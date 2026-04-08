import pytest
from sqlalchemy import select

from backend.auth.service import login_user, logout
from backend.db.models import RefreshToken, User


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(session, user):
    _, refresh_token = await login_user(
        session=session,
        email=user.email,
        password="TestTest123!"
    )

    await logout(session, raw_refresh_token=refresh_token)

    user_request = await session.execute(select(User).where(User.email == user.email))
    user_id = user_request.scalar_one().id
    result = await session.execute(select(RefreshToken).where(RefreshToken.user_id == user_id))
    tokens = result.scalars().all()
    for t in tokens:
        assert t.is_revoked is True
