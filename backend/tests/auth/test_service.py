import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4

from sqlalchemy import update

from backend.auth.security import hash_password, verify_password, create_access_token
from backend.auth.service import register_user, login_user, refresh_tokens, logout, hash_refresh_token
from backend.db.models import RefreshToken, User


@pytest.mark.asyncio
async def test_register_duplicate_email_raises(session):
    email = f"dup_{uuid4().hex[:8]}@example.com"
    await register_user(session, email=email, password="Pass123!", full_name="A")
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        await register_user(session, email=email, password="Pass123!", full_name="B")

@pytest.mark.asyncio
async def test_login_nonexistent_email_raises(session):
    with pytest.raises(ValueError, match="Invalid credentials"):
        await login_user(session, email="nobody@example.com", password="whatever")

@pytest.mark.asyncio
async def test_login_empty_password_raises(session, user):
    with pytest.raises(ValueError, match="Invalid credentials"):
        await login_user(session, email=user.email, password="")

@pytest.mark.asyncio
async def test_refresh_with_bogus_token_raises(session):
    with pytest.raises(ValueError, match="Invalid refresh token"):
        await refresh_tokens(session, raw_refresh_token="totally-wrong-token")

@pytest.mark.asyncio
async def test_refresh_with_revoked_token_raises(session, user):
    _, raw_rt = await login_user(session, email=user.email, password="TestTest123!")
    # First refresh succeeds and revokes original
    await refresh_tokens(session, raw_refresh_token=raw_rt)
    # Second refresh with same token not succedds
    with pytest.raises(ValueError, match="Invalid refresh token"):
        await refresh_tokens(session, raw_refresh_token=raw_rt)

@pytest.mark.asyncio
async def test_refresh_with_expired_token_raises(session, user):
    _, raw_rt = await login_user(session, email=user.email, password="TestTest123!")
    # Force-expire the token in DB
    token_hash = hash_refresh_token(raw_rt)
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .values(expires_at=datetime.now(UTC) - timedelta(hours=1))
    )
    await session.commit()

    with pytest.raises(ValueError, match="Refresh token expired"):
        await refresh_tokens(session, raw_refresh_token=raw_rt)

@pytest.mark.asyncio
async def test_logout_with_already_revoked_token_is_noop(session, user):
    _, raw_rt = await login_user(session, email=user.email, password="TestTest123!")
    await logout(session, raw_refresh_token=raw_rt)
    # Second logout should not raise
    await logout(session, raw_refresh_token=raw_rt)

@pytest.mark.asyncio
async def test_logout_with_bogus_token_is_noop(session):
    # Should not raise; just does nothing
    await logout(session, raw_refresh_token="nonexistent-token")

def test_verify_password_wrong():
    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False

def test_verify_password_correct():
    hashed = hash_password("correct")
    assert verify_password("correct", hashed) is True

def test_hash_password_produces_different_hashes():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2  # bcrypt salts differ

def test_access_token_contains_expected_claims():
    from jose import jwt
    from backend.config import settings

    token = create_access_token(user_id="abc-123", role="user")
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["sub"] == "abc-123"
    assert payload["role"] == "user"
    assert payload["type"] == "access"
    assert "exp" in payload
