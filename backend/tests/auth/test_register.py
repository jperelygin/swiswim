import pytest
from sqlalchemy import select
from backend.db.models import User
from backend.auth.service import register_user


@pytest.mark.asyncio
async def test_register_user_creates_user(session):
    email = "new@example.com"
    password = "password123"
    user = await register_user(
        session=session,
        email=email,
        password=password,
        full_name="New User",
    )
    result = await session.execute(
        select(User).where(User.email == email)
    )
    db_user = result.scalar_one()

    assert db_user.id == user.id
    assert db_user.password_hash != password
    assert db_user.email == email