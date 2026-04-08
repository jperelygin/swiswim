from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import User, UserRole, Workout, WorkoutStatus
from backend.users.schema import UserProfileResponse, UserUpdateRequest, UserUpdateResponse


async def get_user_profile(
        session: AsyncSession,
        *,
        user_id: UUID
) -> UserProfileResponse:
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return UserProfileResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_admin=user.role == UserRole.admin,
        preferred_pool_size=user.preferred_pool_size,
        created_at=user.created_at
    )

async def update_user_profile(
        session: AsyncSession,
        *,
        user_id: UUID,
        data: UserUpdateRequest
) -> UserUpdateResponse:
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.preferred_pool_size is not None:
        user.preferred_pool_size = data.preferred_pool_size

    await session.commit()
    await session.refresh(user)

    return UserUpdateResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        preferred_pool_size=user.preferred_pool_size
    )