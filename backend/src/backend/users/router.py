from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.helpers import get_current_user
from backend.db.models import User
from backend.db.session import get_session
from backend.users.schema import UserUpdateRequest, UserProfileResponse, UserUpdateResponse
from backend.users.service import get_user_profile, update_user_profile


users_router = APIRouter(prefix="/users", tags=["users"])

@users_router.get("/me", response_model=UserProfileResponse)
async def get_me(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> UserProfileResponse:
    return await get_user_profile(session=session, user_id=current_user.id)

@users_router.patch("/me", response_model=UserUpdateResponse)
async def update_me(
    data: UserUpdateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> UserUpdateResponse:
    return await update_user_profile(session=session, user_id=current_user.id, data=data)