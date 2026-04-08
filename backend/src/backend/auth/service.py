import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, UTC
import hashlib

from backend.db.models import User, RefreshToken
from backend.auth.security import hash_password, verify_password, create_access_token, create_refresh_token, get_refresh_token_expires_at

logger = logging.getLogger(__name__)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def register_user(session: AsyncSession, *, email: str, password: str, full_name: str) -> User:
    logger.info("register email=%s", email)
    password_hash = hash_password(password)
    user = User(email=email, password_hash=password_hash, full_name=full_name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
    # Uniqness of email will be checked in endpoint or on DB level


async def login_user(session: AsyncSession, *, email: str, password: str) -> tuple[str, str]:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        logger.warning("login failed email=%s", email)
        raise ValueError("Invalid credentials")

    logger.info("login email=%s", email)
    access_token = create_access_token(user_id=str(user.id), role=user.role.value)
    raw_refresh_token = create_refresh_token()
    refresh_token_hash = hash_refresh_token(raw_refresh_token)
    
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=get_refresh_token_expires_at(),
    )
    session.add(refresh_token)
    await session.commit()
    
    return access_token, raw_refresh_token


async def refresh_tokens(session: AsyncSession, *, raw_refresh_token: str) -> tuple[str, str]:
    token_hash = hash_refresh_token(raw_refresh_token)
    result = await session.execute(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .where(RefreshToken.is_revoked.is_(False))
        .options(selectinload(RefreshToken.user))
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        logger.warning("token refresh failed: token not found or revoked")
        raise ValueError("Invalid refresh token")
    if db_token.expires_at < datetime.now(UTC):
        logger.warning("token refresh failed: token expired")
        raise ValueError("Refresh token expired")

    db_token.is_revoked = True # revoke old

    new_raw_token = create_refresh_token()
    new_token = RefreshToken(
        user_id=db_token.user_id,
        token_hash=hash_refresh_token(new_raw_token),
        expires_at=get_refresh_token_expires_at(),
    )

    session.add(new_token)
    await session.commit()

    access_token = create_access_token(
        user_id=str(db_token.user_id),
        role=db_token.user.role.value,
    )

    logger.debug("token refresh")
    return access_token, new_raw_token


async def logout(session: AsyncSession, *, raw_refresh_token: str) -> None:
    token_hash = hash_refresh_token(raw_refresh_token)

    result = await session.execute(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .where(RefreshToken.is_revoked.is_(False))
    )
    db_token = result.scalar_one_or_none()

    if db_token:
        db_token.is_revoked = True
        await session.commit()
    logger.debug("logout")
