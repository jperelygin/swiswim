import pytest
from uuid import uuid4

from fastapi import HTTPException

from backend.auth.service import register_user
from backend.users.service import get_user_profile, update_user_profile
from backend.users.schema import UserUpdateRequest


async def _make_user(session):
    return await register_user(
        session,
        email=f"usvc_{uuid4().hex[:8]}@example.com",
        password="Pass123!",
        full_name="Service User",
    )


@pytest.mark.asyncio
async def test_get_profile(session):
    user = await _make_user(session)
    profile = await get_user_profile(session, user_id=user.id)
    assert profile.email == user.email
    assert profile.full_name == "Service User"
    assert profile.is_admin is False
    assert profile.preferred_pool_size == 25  # server default


@pytest.mark.asyncio
async def test_get_profile_nonexistent_raises(session):
    with pytest.raises(HTTPException) as exc_info:
        await get_user_profile(session, user_id=uuid4())
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_full_name(session):
    user = await _make_user(session)
    result = await update_user_profile(
        session, user_id=user.id, data=UserUpdateRequest(full_name="New Name"),
    )
    assert result.full_name == "New Name"


@pytest.mark.asyncio
async def test_update_pool_size(session):
    user = await _make_user(session)
    result = await update_user_profile(
        session, user_id=user.id, data=UserUpdateRequest(preferred_pool_size=50),
    )
    assert result.preferred_pool_size == 50


@pytest.mark.asyncio
async def test_update_nonexistent_user_raises(session):
    with pytest.raises(HTTPException) as exc_info:
        await update_user_profile(
            session, user_id=uuid4(), data=UserUpdateRequest(full_name="Ghost"),
        )
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_no_fields_is_noop(session):
    user = await _make_user(session)
    result = await update_user_profile(
        session, user_id=user.id, data=UserUpdateRequest(),
    )
    assert result.full_name == "Service User"
    assert result.preferred_pool_size == 25
