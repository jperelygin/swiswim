import pytest
from uuid import uuid4

from backend.db.models import SwimmingStyle, TrainingLevel, SectionType
from backend.exercises.service import create_exercise
from backend.trainings.service import get_trainings, create_training, get_training_by_id


@pytest.mark.asyncio
async def test_create_training_calculates_total_distance(session):
    ex = await create_exercise(
        session,
        name=f"T-Rex {uuid4().hex[:6]}",
        short_name=f"Trex{uuid4().hex[:3]}",
        style=SwimmingStyle.freestyle,
        distance_meters=100,
    )
    training = await create_training(
        session,
        name=f"Svc Training {uuid4().hex[:6]}",
        level=TrainingLevel.beginner,
        steps=[
            {"exercise_id": ex.id, "step_number": 1, "repetitions": 3, "section_type": SectionType.main},
            {"exercise_id": ex.id, "step_number": 2, "repetitions": 1, "section_type": SectionType.cooldown},
        ],
    )
    assert training.total_distance == 400


@pytest.mark.asyncio
async def test_create_training_nonexistent_exercise_raises(session):
    with pytest.raises(ValueError, match="Exercise not found"):
        await create_training(
            session,
            name=f"Bad Training {uuid4().hex[:6]}",
            level=TrainingLevel.beginner,
            steps=[
                {"exercise_id": uuid4(), "step_number": 1, "repetitions": 1, "section_type": SectionType.main},
            ],
        )


@pytest.mark.asyncio
async def test_get_training_by_id_nonexistent(session):
    result = await get_training_by_id(session, uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_trainings_filter_by_level(session):
    ex = await create_exercise(
        session,
        name=f"Lvl Ex {uuid4().hex[:6]}",
        short_name=f"LE{uuid4().hex[:3]}",
        style=SwimmingStyle.freestyle,
        distance_meters=50,
    )
    await create_training(
        session,
        name=f"Adv Training {uuid4().hex[:6]}",
        level=TrainingLevel.advanced,
        steps=[{"exercise_id": ex.id, "step_number": 1, "repetitions": 1, "section_type": SectionType.main}],
    )

    trainings, total = await get_trainings(session, level=TrainingLevel.advanced)
    assert total >= 1
    assert all(t.level == TrainingLevel.advanced for t in trainings)


@pytest.mark.asyncio
async def test_get_trainings_filter_by_distance(session):
    ex = await create_exercise(
        session,
        name=f"Dist Ex {uuid4().hex[:6]}",
        short_name=f"DE{uuid4().hex[:3]}",
        style=SwimmingStyle.freestyle,
        distance_meters=500,
    )
    await create_training(
        session,
        name=f"Long Training {uuid4().hex[:6]}",
        level=TrainingLevel.intermediate,
        steps=[{"exercise_id": ex.id, "step_number": 1, "repetitions": 2, "section_type": SectionType.main}],
    )

    trainings, total = await get_trainings(session, min_distance=900)
    assert total >= 1
    assert all(t.total_distance >= 900 for t in trainings)

    trainings2, total2 = await get_trainings(session, max_distance=100)
    assert all(t.total_distance <= 100 for t in trainings2)


@pytest.mark.asyncio
async def test_get_trainings_only_active(session):
    # get_trainings should only return is_active=True templates.
    ex = await create_exercise(
        session,
        name=f"Act Ex {uuid4().hex[:6]}",
        short_name=f"AE{uuid4().hex[:3]}",
        style=SwimmingStyle.freestyle,
        distance_meters=50,
    )
    training = await create_training(
        session,
        name=f"Act Training {uuid4().hex[:6]}",
        level=TrainingLevel.beginner,
        steps=[{"exercise_id": ex.id, "step_number": 1, "repetitions": 1, "section_type": SectionType.main}],
    )
    # Deactivate
    training.is_active = False
    await session.commit()

    trainings, _ = await get_trainings(session)
    ids = [t.id for t in trainings]
    assert training.id not in ids
