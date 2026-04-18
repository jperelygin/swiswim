import pytest
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select

from backend.db.models import (
    SwimmingStyle, TrainingLevel, SectionType,
    WorkoutStatus, WorkoutStepStatus, WorkoutStep,
)
from backend.exercises.service import create_exercise
from backend.trainings.service import create_training
from backend.workouts.service import (
    create_workout,
    get_workout_by_id,
    update_workout,
    sync_workout,
    delete_workout,
)
from backend.workouts.schema import WorkoutUpdateRequest, WorkoutSyncRequest, SyncStepItem
from backend.auth.service import register_user


async def _make_user(session):
    email = f"svc_{uuid4().hex[:8]}@example.com"
    return await register_user(session, email=email, password="Pass123!", full_name="Svc User")


async def _make_training(session):
    ex = await create_exercise(
        session,
        name=f"WS Ex {uuid4().hex[:6]}",
        short_name=f"WS{uuid4().hex[:3]}",
        style=SwimmingStyle.freestyle,
        distance_meters=100,
    )
    return await create_training(
        session,
        name=f"WS Training {uuid4().hex[:6]}",
        level=TrainingLevel.beginner,
        steps=[
            {"exercise_id": ex.id, "step_number": 1, "repetitions": 2, "section_type": SectionType.warmup},
            {"exercise_id": ex.id, "step_number": 2, "repetitions": 1, "section_type": SectionType.main},
        ],
    )


@pytest.mark.asyncio
async def test_create_workout_sets_planned_distance(session):
    user = await _make_user(session)
    training = await _make_training(session)

    result = await create_workout(session, user_id=user.id, training_id=training.id, pool_size_meters=25)
    assert result.total_distance_planned == training.total_distance
    assert result.total_distance_completed == 0
    assert result.status == WorkoutStatus.in_progress


@pytest.mark.asyncio
async def test_create_workout_nonexistent_training_raises(session):
    user = await _make_user(session)
    with pytest.raises(HTTPException) as exc_info:
        await create_workout(session, user_id=user.id, training_id=uuid4(), pool_size_meters=25)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_workout_inactive_training_raises(session):
    user = await _make_user(session)
    training = await _make_training(session)
    training.is_active = False
    await session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await create_workout(session, user_id=user.id, training_id=training.id, pool_size_meters=25)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_workout_wrong_user_raises(session):
    user1 = await _make_user(session)
    user2 = await _make_user(session)
    training = await _make_training(session)

    wo = await create_workout(session, user_id=user1.id, training_id=training.id, pool_size_meters=25)
    with pytest.raises(HTTPException) as exc_info:
        await get_workout_by_id(session, workout_id=wo.workout_id, user_id=user2.id)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_workout_complete(session):
    user = await _make_user(session)
    training = await _make_training(session)
    wo = await create_workout(session, user_id=user.id, training_id=training.id, pool_size_meters=25)

    result = await update_workout(
        session,
        workout_id=wo.workout_id,
        user_id=user.id,
        data=WorkoutUpdateRequest(status=WorkoutStatus.completed),
    )
    assert result.status == WorkoutStatus.completed


@pytest.mark.asyncio
async def test_update_completed_workout_status_raises(session):
    user = await _make_user(session)
    training = await _make_training(session)
    wo = await create_workout(session, user_id=user.id, training_id=training.id, pool_size_meters=25)

    await update_workout(
        session, workout_id=wo.workout_id, user_id=user.id,
        data=WorkoutUpdateRequest(status=WorkoutStatus.completed),
    )
    with pytest.raises(HTTPException) as exc_info:
        await update_workout(
            session, workout_id=wo.workout_id, user_id=user.id,
            data=WorkoutUpdateRequest(status=WorkoutStatus.abandoned),
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_update_pool_size_after_step_completed_raises(session):
    user = await _make_user(session)
    training = await _make_training(session)
    wo = await create_workout(session, user_id=user.id, training_id=training.id, pool_size_meters=25)

    # Mark a step as completed
    result = await session.execute(
        select(WorkoutStep).where(WorkoutStep.workout_id == wo.workout_id)
    )
    step = result.scalars().first()
    assert step is not None
    step.status = WorkoutStepStatus.completed
    await session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await update_workout(
            session, workout_id=wo.workout_id, user_id=user.id,
            data=WorkoutUpdateRequest(pool_size_meters=50),
        )
    assert exc_info.value.status_code == 400
    assert "steps have been completed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_end_time_without_status_change_raises(session):
    user = await _make_user(session)
    training = await _make_training(session)
    wo = await create_workout(session, user_id=user.id, training_id=training.id, pool_size_meters=25)

    with pytest.raises(HTTPException) as exc_info:
        await update_workout(
            session, workout_id=wo.workout_id, user_id=user.id,
            data=WorkoutUpdateRequest(actual_end_time=datetime.now(timezone.utc)),
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_delete_synced_workout_raises(session):
    user = await _make_user(session)
    training = await _make_training(session)
    wo = await create_workout(session, user_id=user.id, training_id=training.id, pool_size_meters=25)

    await sync_workout(
        session,
        workout_id=wo.workout_id,
        user_id=user.id,
        data=WorkoutSyncRequest(
            status=WorkoutStatus.completed,
            steps=[
                SyncStepItem(step_number=1, status=WorkoutStepStatus.completed),
                SyncStepItem(step_number=2, status=WorkoutStepStatus.completed),
            ],
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        await delete_workout(session, workout_id=wo.workout_id, user_id=user.id)
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_delete_nonexistent_workout_raises(session):
    user = await _make_user(session)
    with pytest.raises(HTTPException) as exc_info:
        await delete_workout(session, workout_id=uuid4(), user_id=user.id)
    assert exc_info.value.status_code == 404
