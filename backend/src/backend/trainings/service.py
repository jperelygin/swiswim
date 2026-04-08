from uuid import UUID
from typing import Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models import Exercise, TrainingLevel, TrainingStep, TrainingTemplate


async def get_trainings(
    session: AsyncSession,
    *,
    level: Optional[TrainingLevel] = None,
    min_distance: Optional[int] = None,
    max_distance: Optional[int] = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[TrainingTemplate], int]:
    query = select(TrainingTemplate).where(TrainingTemplate.is_active.is_(True))
    count_query = (
        select(func.count())
        .select_from(TrainingTemplate)
        .where(TrainingTemplate.is_active.is_(True))
    )

    if level is not None:
        query = query.where(TrainingTemplate.level == level)
        count_query = count_query.where(TrainingTemplate.level == level)

    if min_distance is not None:
        query = query.where(TrainingTemplate.total_distance >= min_distance)
        count_query = count_query.where(TrainingTemplate.total_distance >= min_distance)

    if max_distance is not None:
        query = query.where(TrainingTemplate.total_distance <= max_distance)
        count_query = count_query.where(TrainingTemplate.total_distance <= max_distance)

    total = (await session.execute(count_query)).scalar_one()

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit).order_by(TrainingTemplate.name)

    result = await session.execute(query)
    trainings = list(result.scalars().all())

    return trainings, total


async def create_training(
    session: AsyncSession,
    *,
    name: str,
    level: TrainingLevel,
    description: Optional[str] = None,
    estimated_duration_minutes: Optional[int] = None,
    steps: list[dict[str, Any]],
) -> TrainingTemplate:
    # Look up exercises to calculate total distance
    exercise_ids = [s["exercise_id"] for s in steps]
    result = await session.execute(
        select(Exercise).where(Exercise.id.in_(exercise_ids))
    )
    exercise_map = {e.id: e for e in result.scalars().all()}

    total_distance = 0
    for s in steps:
        exercise = exercise_map.get(s["exercise_id"])
        if exercise is None:
            raise ValueError(f"Exercise not found: {s['exercise_id']}")
        total_distance += exercise.distance_meters * s.get("repetitions", 1)

    training = TrainingTemplate(
        name=name,
        description=description,
        level=level,
        total_distance=total_distance,
        estimated_duration_minutes=estimated_duration_minutes,
    )
    session.add(training)
    await session.flush()

    for step_data in steps:
        step = TrainingStep(
            training_template_id=training.id,
            exercise_id=step_data["exercise_id"],
            step_number=step_data["step_number"],
            repetitions=step_data.get("repetitions", 1),
            section_type=step_data["section_type"],
            rest_seconds=step_data.get("rest_seconds"),
            notes=step_data.get("notes"),
        )
        session.add(step)

    await session.commit()

    # Re-fetch with relationships loaded
    return await get_training_by_id(session, training.id)  # type: ignore[return-value]


async def get_training_by_id(
    session: AsyncSession,
    training_id: UUID,
) -> Optional[TrainingTemplate]:
    result = await session.execute(
        select(TrainingTemplate)
        .where(TrainingTemplate.id == training_id)
        .options(
            selectinload(TrainingTemplate.steps)
            .selectinload(TrainingStep.exercise)
        )
    )
    return result.scalar_one_or_none()
