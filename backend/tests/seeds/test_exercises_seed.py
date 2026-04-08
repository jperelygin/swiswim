import pytest
from sqlalchemy import select

from backend.db.models import Exercise
from backend.seeds.data.exercises import seed_exercises, EXERCISES


@pytest.mark.asyncio
async def test_seed_exercises_idempotent(engine, session):
    await seed_exercises(session)
    result = await session.execute(select(Exercise))
    rows_first = result.scalars().all()

    assert len(rows_first) >= len(EXERCISES), f"Seed data not fully inserted."
    first_count = len(rows_first)

    await seed_exercises(session)

    result = await session.execute(select(Exercise))
    rows_second = result.scalars().all()

    assert len(rows_second) == first_count, f"Seeding not idempotent, added more rows with same Seed data"


@pytest.mark.asyncio
async def test_seed_exercises_updates_fields(session):
    await seed_exercises(session)
    exercise = (
        await session.execute(
            select(Exercise).where(Exercise.name == "Freestyle 100")
        )
    ).scalar_one()

    assert exercise.short_name == "Free 100"