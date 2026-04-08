import pytest
from backend.auth.service import login_user


@pytest.mark.asyncio
async def test_login_success(session, user):
    access_token, refresh_token = await login_user(
        session=session,
        email=user.email,
        password="TestTest123!",
    )
    assert isinstance(access_token, str)
    assert isinstance(refresh_token, str)
    assert len(refresh_token) > 30

@pytest.mark.asyncio
async def test_login_invalid_password(session, user):
    with pytest.raises(ValueError):
        await login_user(
            session=session,
            email=user.email,
            password="wrongpassword"
        )