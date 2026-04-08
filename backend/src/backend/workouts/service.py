import logging
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models import (
    TrainingStep,
    Workout,
    WorkoutStatus,
    WorkoutStep,
    WorkoutStepStatus,
    TrainingTemplate,
)
from backend.workouts.schema import (
    WorkoutCreateResponse,
    WorkoutListItem,
    WorkoutListResponse,
    WorkoutStepItem,
    WorkoutDetail,
    WorkoutUpdateRequest,
    WorkoutSyncRequest,
    WorkoutSyncResponse,
)


async def create_workout(
    session: AsyncSession,
    *,
    user_id: UUID,
    training_id: UUID,
    pool_size_meters: int,
) -> WorkoutCreateResponse:
    
    result = await session.execute(
        select(TrainingTemplate)
        .where(TrainingTemplate.id == training_id, TrainingTemplate.is_active.is_(True))
        .options(
            selectinload(TrainingTemplate.steps)
            .selectinload(TrainingStep.exercise)
        )
    )
    training = result.scalar_one_or_none()
    if training is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training not found or inactive",
        )

    workout = Workout(
        user_id=user_id,
        training_template_id=training.id,
        pool_size_meters=pool_size_meters,
        total_distance_planned=training.total_distance,
    )
    session.add(workout)
    await session.flush()

    for ts in sorted(training.steps, key=lambda s: s.step_number):
        step = WorkoutStep(
            workout_id=workout.id,
            step_number=ts.step_number,
            exercise_id=ts.exercise_id,
            distance_meters=ts.exercise.distance_meters * ts.repetitions,
            notes=ts.notes,
        )
        session.add(step)

    await session.commit()
    await session.refresh(workout)

    return WorkoutCreateResponse(
        workout_id=workout.id,
        user_id=workout.user_id,
        training_id=workout.training_template_id,
        training_version=training.version,
        pool_size_meters=workout.pool_size_meters,
        status=workout.status,
        actual_start_time=workout.actual_start_time,
        actual_end_time=workout.actual_end_time,
        total_distance_planned=workout.total_distance_planned,
        total_distance_completed=workout.total_distance_completed,
        created_at=workout.created_at,
    )


async def get_workouts(
    session: AsyncSession,
    *,
    user_id: UUID,
    workout_status: Optional[WorkoutStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = 1,
    limit: int = 20,
) -> WorkoutListResponse:
    base_filter = Workout.user_id == user_id

    query = (
        select(Workout, TrainingTemplate.name, TrainingTemplate.version)
        .join(TrainingTemplate, Workout.training_template_id == TrainingTemplate.id)
        .where(base_filter)
    )
    count_query = (
        select(func.count())
        .select_from(Workout)
        .where(base_filter)
    )

    if workout_status is not None:
        query = query.where(Workout.status == workout_status)
        count_query = count_query.where(Workout.status == workout_status)

    if date_from is not None:
        query = query.where(Workout.actual_start_time >= date_from)
        count_query = count_query.where(Workout.actual_start_time >= date_from)

    if date_to is not None:
        query = query.where(Workout.actual_start_time <= date_to)
        count_query = count_query.where(Workout.actual_start_time <= date_to)

    total = (await session.execute(count_query)).scalar_one()

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit).order_by(Workout.created_at.desc())

    result = await session.execute(query)
    rows = result.all()

    items = [
        WorkoutListItem(
            workout_id=workout.id,
            training_name=training_name,
            training_version=training_version,
            status=workout.status,
            actual_start_time=workout.actual_start_time,
            actual_end_time=workout.actual_end_time,
            total_distance_completed=workout.total_distance_completed,
            total_duration_seconds=workout.total_duration_seconds,
            created_at=workout.created_at,
        )
        for workout, training_name, training_version in rows
    ]

    return WorkoutListResponse(workouts=items, total=total)


async def get_workout_by_id(
    session: AsyncSession,
    *,
    workout_id: UUID,
    user_id: UUID,
) -> WorkoutDetail:
    result = await session.execute(
        select(Workout)
        .where(Workout.id == workout_id, Workout.user_id == user_id)
        .options(
            selectinload(Workout.steps).selectinload(WorkoutStep.exercise),  # type: ignore[arg-type]
        )
    )
    workout = result.scalar_one_or_none()
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )

    t_result = await session.execute(
        select(TrainingTemplate.name, TrainingTemplate.version)
        .where(TrainingTemplate.id == workout.training_template_id)
    )
    training_row = t_result.one()

    return _build_workout_detail(workout, training_row.name, training_row.version)


async def update_workout(
    session: AsyncSession,
    *,
    workout_id: UUID,
    user_id: UUID,
    data: WorkoutUpdateRequest,
) -> WorkoutDetail:
    result = await session.execute(
        select(Workout)
        .where(Workout.id == workout_id, Workout.user_id == user_id)
        .options(
            selectinload(Workout.steps).selectinload(WorkoutStep.exercise),  # type: ignore[arg-type]
        )
    )
    workout = result.scalar_one_or_none()
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )

    if data.status is not None:
        if workout.status != WorkoutStatus.in_progress:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only update status of in_progress workouts",
            )
        if data.status not in (WorkoutStatus.completed, WorkoutStatus.abandoned):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status can only transition to completed or abandoned",
            )
        workout.status = data.status

    if data.pool_size_meters is not None:
        if workout.status != WorkoutStatus.in_progress:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only change pool size for in_progress workouts",
            )
        has_completed = any(
            s.status in (WorkoutStepStatus.completed, WorkoutStepStatus.skipped)
            for s in workout.steps
        )
        if has_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change pool size after steps have been completed",
            )
        workout.pool_size_meters = data.pool_size_meters

    if data.actual_start_time is not None:
        if workout.actual_start_time is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="actual_start_time already set",
            )
        workout.actual_start_time = data.actual_start_time

    if data.actual_end_time is not None:
        if data.status not in (WorkoutStatus.completed, WorkoutStatus.abandoned):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="actual_end_time can only be set when completing or abandoning",
            )
        workout.actual_end_time = data.actual_end_time

    if data.status in (WorkoutStatus.completed, WorkoutStatus.abandoned):
        workout.total_distance_completed = sum(
            s.distance_meters for s in workout.steps
            if s.status == WorkoutStepStatus.completed
        )
        workout.total_duration_seconds = sum(
            s.duration_seconds for s in workout.steps
            if s.duration_seconds is not None
        )

    await session.commit()

    return await get_workout_by_id(
        session, workout_id=workout_id, user_id=user_id,
    )


async def sync_workout(
    session: AsyncSession,
    *,
    workout_id: UUID,
    user_id: UUID,
    data: WorkoutSyncRequest,
) -> WorkoutSyncResponse:
    result = await session.execute(
        select(Workout)
        .where(Workout.id == workout_id, Workout.user_id == user_id)
        .options(selectinload(Workout.steps))
    )
    workout = result.scalar_one_or_none()
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )

    if workout.status == WorkoutStatus.synced:
        logger.info("sync workout_id=%s already synced", workout_id)
        return WorkoutSyncResponse(
            workout_id=workout.id,
            sync_status="synced",
            synced_at=workout.synced_at,  # type: ignore[arg-type]
        )

    workout.status = WorkoutStatus.synced
    workout.actual_start_time = data.actual_start_time
    workout.actual_end_time = data.actual_end_time
    now = datetime.now(timezone.utc)
    workout.synced_at = now

    step_map = {s.step_number: s for s in workout.steps}
    for sync_step in data.steps:
        ws = step_map.get(sync_step.step_number)
        if ws is None:
            continue
        ws.status = sync_step.status
        ws.started_at = sync_step.started_at
        ws.completed_at = sync_step.completed_at
        ws.duration_seconds = sync_step.duration_seconds
        ws.avg_heart_rate = sync_step.avg_heart_rate
        ws.notes = sync_step.notes

    workout.total_distance_completed = sum(
        s.distance_meters for s in workout.steps
        if s.status == WorkoutStepStatus.completed
    )
    workout.total_duration_seconds = sum(
        s.duration_seconds for s in workout.steps
        if s.duration_seconds is not None
    )

    await session.commit()

    logger.info("sync workout_id=%s steps=%d", workout_id, len(data.steps))
    return WorkoutSyncResponse(
        workout_id=workout.id,
        sync_status="synced",
        synced_at=workout.synced_at,  # type: ignore[arg-type]
    )


async def delete_workout(
    session: AsyncSession,
    *,
    workout_id: UUID,
    user_id: UUID,
) -> None:
    result = await session.execute(
        select(Workout)
        .where(Workout.id == workout_id, Workout.user_id == user_id)
    )
    workout = result.scalar_one_or_none()
    if workout is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )

    if workout.status == WorkoutStatus.synced:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete synced workout",
        )

    await session.delete(workout)
    await session.commit()


def _build_workout_detail(
    workout: Workout,
    training_name: str,
    training_version: int,
) -> WorkoutDetail:
    steps = [
        WorkoutStepItem(
            step_number=s.step_number,
            exercise_name=s.exercise.name,
            exercise_short_name=s.exercise.short_name,
            distance_meters=s.distance_meters,
            status=s.status,
            started_at=s.started_at,
            completed_at=s.completed_at,
            duration_seconds=s.duration_seconds,
            avg_heart_rate=s.avg_heart_rate,
            notes=s.notes,
        )
        for s in sorted(workout.steps, key=lambda s: s.step_number)
    ]
    return WorkoutDetail(
        workout_id=workout.id,
        user_id=workout.user_id,
        training_id=workout.training_template_id,
        training_name=training_name,
        training_version=training_version,
        pool_size_meters=workout.pool_size_meters,
        status=workout.status,
        actual_start_time=workout.actual_start_time,
        actual_end_time=workout.actual_end_time,
        total_distance_planned=workout.total_distance_planned,
        total_distance_completed=workout.total_distance_completed,
        total_duration_seconds=workout.total_duration_seconds,
        steps=steps,
        created_at=workout.created_at,
        updated_at=workout.updated_at,
    )
