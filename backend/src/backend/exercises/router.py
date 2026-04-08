from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.helpers import get_current_user, require_admin
from backend.db.models import SwimmingStyle, User
from backend.db.session import get_session
from backend.exercises.schema import (
    CreateExerciseRequest,
    ExerciseDetail,
    ExerciseListResponse,
)
from backend.exercises.service import create_exercise, get_exercise_by_id, get_exercises


exercises_router = APIRouter(prefix="/exercises", tags=["exercises"])


@exercises_router.get("", response_model=ExerciseListResponse)
async def list_exercises(
    style: Optional[SwimmingStyle] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> ExerciseListResponse:
    exercises, total = await get_exercises(
        session, style=style, search=search, page=page, limit=limit
    )
    return ExerciseListResponse(
        exercises=exercises,  # type: ignore[arg-type]
        total=total,
    )


@exercises_router.post("", status_code=201, response_model=ExerciseDetail)
async def create_exercise_endpoint(
    data: CreateExerciseRequest,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_admin),
) -> ExerciseDetail:
    try:
        exercise = await create_exercise(
            session,
            name=data.name,
            short_name=data.short_name,
            style=data.style,
            distance_meters=data.distance_meters,
            description=data.description,
            content_markdown=data.content_markdown,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Exercise with this name and distance already exists",
        )
    return ExerciseDetail.model_validate(exercise)


@exercises_router.get("/{exercise_id}", response_model=ExerciseDetail)
async def get_exercise(
    exercise_id: UUID,
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> ExerciseDetail:
    exercise = await get_exercise_by_id(session, exercise_id)
    if exercise is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        )
    return ExerciseDetail.model_validate(exercise)
