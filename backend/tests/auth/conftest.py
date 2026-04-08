from uuid import uuid4
import pytest_asyncio
from backend.auth.service import register_user


@pytest_asyncio.fixture
async def user(session):
    return await register_user(
        session,
        email=f"test_{uuid4().hex[:8]}@example.com",
        password="TestTest123!",
        full_name="John Doe"
    )
