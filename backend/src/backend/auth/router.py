from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.helpers import get_current_user
from backend.auth.schema import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from backend.auth.service import login_user, logout, refresh_tokens, register_user
from backend.db.models import User
from backend.db.session import get_session
from backend.limiter import limiter
from backend.config import settings


auth_router = APIRouter(prefix="/auth", tags=["auth"])
AUTH_RATE_LIMIT = settings.auth_rate_limit


@auth_router.post("/register", status_code=201, response_model=RegisterResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def register(request: Request, data: RegisterRequest, session: AsyncSession = Depends(get_session)) -> RegisterResponse:
    try:
        user = await register_user(
            session,
            email=data.email,
            password=data.password,
            full_name=data.full_name,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    access_token, refresh_token = await login_user(
        session, email=data.email, password=data.password
    )

    return RegisterResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        access_token=access_token,
        refresh_token=refresh_token,
    )


@auth_router.post("/login", response_model=TokenResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def login(request: Request, data: LoginRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    try:
        access_token, refresh_token = await login_user(
            session, email=data.email, password=data.password
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@auth_router.post("/refresh", response_model=TokenResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def refresh(request: Request, data: RefreshRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    try:
        access_token, refresh_token = await refresh_tokens(
            session, raw_refresh_token=data.refresh_token
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@auth_router.post("/logout", status_code=204)
async def logout_endpoint(data: LogoutRequest,
                          session: AsyncSession = Depends(get_session),
                          _current_user: User = Depends(get_current_user)) -> Response:
    await logout(session, raw_refresh_token=data.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
