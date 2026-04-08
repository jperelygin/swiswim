import pytest
from sqlalchemy import select

from backend.auth.service import login_user, refresh_tokens
from backend.db.models import RefreshToken, User


@pytest.mark.asyncio
async def test_refresh_rotates_token(session, user):
    _, refresh_token = await login_user(
        session=session,
        email=user.email,
        password="TestTest123!",
    )
    new_access, new_refresh = await refresh_tokens(
        session=session,
        raw_refresh_token=refresh_token,
    )

    assert new_access
    assert new_refresh != refresh_token

    user_request = await session.execute(select(User).where(User.email == user.email))
    user_id = user_request.scalar_one().id

    result = await session.execute(select(RefreshToken).where(RefreshToken.user_id == user_id))
    tokens = result.scalars().all()

    assert len(tokens) == 2
    revoked = [t for t in tokens if t.is_revoked]
    active = [t for t in tokens if not t.is_revoked]

    assert len(revoked) == 1
    assert len(active) == 1