from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.helpers import get_current_user
from backend.db.models import User, WorkoutStatus
from backend.db.session import get_session
from backend.workouts.schema import (
    WorkoutCreateRequest,
    WorkoutCreateResponse,
    WorkoutDetail,
    WorkoutListResponse,
    WorkoutSyncRequest,
    WorkoutSyncResponse,
    WorkoutUpdateRequest,
)
from backend.workouts.service import (
    create_workout,
    delete_workout,
    get_workout_by_id,
    get_workouts,
    sync_workout,
    update_workout,
)


workouts_router = APIRouter(prefix="/workouts", tags=["workouts"])


@workouts_router.post("", status_code=201, response_model=WorkoutCreateResponse)
async def create_workout_endpoint(
    data: WorkoutCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> WorkoutCreateResponse:
    return await create_workout(
        session,
        user_id=current_user.id,
        training_id=data.training_id,
        pool_size_meters=data.pool_size_meters,
    )


@workouts_router.get("", response_model=WorkoutListResponse)
async def list_workouts(
    workout_status: Optional[WorkoutStatus] = Query(default=None, alias="status"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> WorkoutListResponse:
    return await get_workouts(
        session,
        user_id=current_user.id,
        workout_status=workout_status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )


@workouts_router.get("/{workout_id}", response_model=WorkoutDetail)
async def get_workout_endpoint(
    workout_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> WorkoutDetail:
    return await get_workout_by_id(
        session,
        workout_id=workout_id,
        user_id=current_user.id,
    )


@workouts_router.patch("/{workout_id}", response_model=WorkoutDetail)
async def update_workout_endpoint(
    workout_id: UUID,
    data: WorkoutUpdateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> WorkoutDetail:
    return await update_workout(
        session,
        workout_id=workout_id,
        user_id=current_user.id,
        data=data,
    )


@workouts_router.post("/{workout_id}/sync", response_model=WorkoutSyncResponse)
async def sync_workout_endpoint(
    workout_id: UUID,
    data: WorkoutSyncRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> WorkoutSyncResponse:
    return await sync_workout(
        session,
        workout_id=workout_id,
        user_id=current_user.id,
        data=data,
    )


@workouts_router.delete("/{workout_id}", status_code=204)
async def delete_workout_endpoint(
    workout_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    await delete_workout(
        session,
        workout_id=workout_id,
        user_id=current_user.id,
    )
