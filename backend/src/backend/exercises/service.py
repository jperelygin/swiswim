from uuid import UUID
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Exercise, SwimmingStyle


async def get_exercises(
    session: AsyncSession,
    *,
    style: Optional[SwimmingStyle] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Exercise], int]:
    query = select(Exercise)
    count_query = select(func.count()).select_from(Exercise)

    if style is not None:
        query = query.where(Exercise.style == style)
        count_query = count_query.where(Exercise.style == style)

    if search is not None:
        query = query.where(Exercise.name.ilike(f"%{search}%"))
        count_query = count_query.where(Exercise.name.ilike(f"%{search}%"))

    total = (await session.execute(count_query)).scalar_one()

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit).order_by(Exercise.name)

    result = await session.execute(query)
    exercises = list(result.scalars().all())

    return exercises, total


async def create_exercise(
    session: AsyncSession,
    *,
    name: str,
    short_name: str,
    style: SwimmingStyle,
    distance_meters: int,
    description: Optional[str] = None,
    content_markdown: Optional[str] = None,
) -> Exercise:
    exercise = Exercise(
        name=name,
        short_name=short_name,
        style=style,
        distance_meters=distance_meters,
        description=description,
        content_markdown=content_markdown,
    )
    session.add(exercise)
    await session.commit()
    await session.refresh(exercise)
    return exercise


async def get_exercise_by_id(
    session: AsyncSession,
    exercise_id: UUID,
) -> Optional[Exercise]:
    result = await session.execute(
        select(Exercise).where(Exercise.id == exercise_id)
    )
    return result.scalar_one_or_none()
