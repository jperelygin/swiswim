import pytest
import pytest_asyncio
import asyncio
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi.testclient import TestClient
import psycopg

from backend.db.session import DATABASE_URL as MAIN_DB_URL, get_session
from backend.limiter import limiter
from backend.main import app
from tests.db import TEST_DB_URL, TEST_DB_NAME
from alembic import command
from alembic.config import Config




@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Clear in-memory rate limit counters before each test."""
    storage = limiter._storage
    for attr in ("storage", "expirations", "events", "_events"):
        bucket = getattr(storage, attr, None)
        if isinstance(bucket, dict):
            bucket.clear()


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def engine():

    with psycopg.connect(MAIN_DB_URL.replace("+psycopg", "")) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            print(f"\nCreating test database {TEST_DB_NAME}")
            cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
            cur.execute(f"CREATE DATABASE {TEST_DB_NAME}")
            print(f"Test database {TEST_DB_NAME} created")

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    command.upgrade(alembic_cfg, "head")

    engine = create_async_engine(TEST_DB_URL, echo=False)
    
    yield engine

    await engine.dispose()
    with psycopg.connect(MAIN_DB_URL.replace("+psycopg", "")) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            print("\nDropping test database")
            cur.execute(f"DROP DATABASE {TEST_DB_NAME} WITH (FORCE)")
            print("Test database dropped")


@pytest_asyncio.fixture
async def session(engine):
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def admin_token(client):
    """Register a user, promote to admin via DB, return access token."""
    from uuid import uuid4

    email = f"admin_{uuid4().hex[:8]}@example.com"
    client.post("/api/auth/register", json={
        "email": email,
        "password": "StrongPass123!",
        "full_name": "Admin User",
    })

    # Promote to admin directly in DB via psycopg
    conninfo = TEST_DB_URL.replace("+psycopg", "")
    with psycopg.connect(conninfo) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET role = 'admin' WHERE email = %s", (email,)
            )

    # Re-login to get a token with admin role in JWT
    resp = client.post("/api/auth/login", json={
        "email": email,
        "password": "StrongPass123!",
    })
    return resp.json()["access_token"]


@pytest.fixture
def client(engine):
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    test_session_factory = async_sessionmaker(
        test_engine, expire_on_commit=False,
    )

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    test_engine.sync_engine.dispose()