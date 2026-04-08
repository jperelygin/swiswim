from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.helpers import get_current_user, require_admin
from backend.db.models import TrainingLevel, User
from backend.db.session import get_session
from backend.trainings.schema import (
    CreateTrainingRequest,
    TrainingDetail,
    TrainingListResponse,
    TrainingStepItem,
)
from backend.trainings.service import create_training, get_training_by_id, get_trainings


trainings_router = APIRouter(prefix="/trainings", tags=["trainings"])


@trainings_router.get("", response_model=TrainingListResponse)
async def list_trainings(
    level: Optional[TrainingLevel] = None,
    min_distance: Optional[int] = None,
    max_distance: Optional[int] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> TrainingListResponse:
    trainings, total = await get_trainings(
        session, level=level, min_distance=min_distance,
        max_distance=max_distance, page=page, limit=limit,
    )
    return TrainingListResponse(
        trainings=trainings,  # type: ignore[arg-type]
        total=total,
    )


@trainings_router.post("", status_code=201, response_model=TrainingDetail)
async def create_training_endpoint(
    data: CreateTrainingRequest,
    session: AsyncSession = Depends(get_session),
    _admin: User = Depends(require_admin),
) -> TrainingDetail:
    steps_data = [s.model_dump() for s in data.steps]
    try:
        training = await create_training(
            session,
            name=data.name,
            description=data.description,
            level=data.level,
            estimated_duration_minutes=data.estimated_duration_minutes,
            steps=steps_data,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Training with this name and version already exists",
        )
    return _build_training_detail(training)


@trainings_router.get("/{training_id}", response_model=TrainingDetail)
async def get_training(
    training_id: UUID,
    session: AsyncSession = Depends(get_session),
    _current_user: User = Depends(get_current_user),
) -> TrainingDetail:
    training = await get_training_by_id(session, training_id)
    if training is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training not found",
        )
    return _build_training_detail(training)


def _build_training_detail(training: object) -> TrainingDetail:
    from backend.db.models import TrainingTemplate
    t: TrainingTemplate = training  # type: ignore[assignment]
    steps = [
        TrainingStepItem(
            step_number=step.step_number,
            exercise_id=step.exercise_id,
            exercise_name=step.exercise.name,
            exercise_short_name=step.exercise.short_name,
            repetitions=step.repetitions,
            section_type=step.section_type,
            rest_seconds=step.rest_seconds,
            distance_meters=step.exercise.distance_meters * step.repetitions,
            notes=step.notes,
        )
        for step in sorted(t.steps, key=lambda s: s.step_number)
    ]
    return TrainingDetail(
        id=t.id,
        name=t.name,
        description=t.description,
        level=t.level,
        total_distance=t.total_distance,
        estimated_duration_minutes=t.estimated_duration_minutes,
        version=t.version,
        is_active=t.is_active,
        steps=steps,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )
