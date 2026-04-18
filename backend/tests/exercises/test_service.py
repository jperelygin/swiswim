import pytest
from uuid import uuid4

from backend.db.models import SwimmingStyle
from backend.exercises.service import get_exercises, create_exercise, get_exercise_by_id


@pytest.mark.asyncio
async def test_create_exercise_and_retrieve(session):
    ex = await create_exercise(
        session,
        name=f"Svc Ex {uuid4().hex[:6]}",
        short_name=f"SE{uuid4().hex[:3]}",
        style=SwimmingStyle.freestyle,
        distance_meters=200,
        description="Test desc",
        content_markdown="# Content",
    )
    assert ex.id is not None
    assert ex.distance_meters == 200
    assert ex.style == SwimmingStyle.freestyle

    fetched = await get_exercise_by_id(session, ex.id)
    assert fetched is not None
    assert fetched.id == ex.id
    assert fetched.content_markdown == "# Content"


@pytest.mark.asyncio
async def test_get_exercise_by_id_nonexistent(session):
    result = await get_exercise_by_id(session, uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_exercises_empty(session):
    # Filter by a search term that won't match
    exercises, total = await get_exercises(session, search="zzz_no_match_zzz")
    assert exercises == []
    assert total == 0


@pytest.mark.asyncio
async def test_get_exercises_filter_by_style(session):
    await create_exercise(
        session,
        name=f"Back {uuid4().hex[:6]}",
        short_name=f"B{uuid4().hex[:4]}",
        style=SwimmingStyle.backstroke,
        distance_meters=50,
    )
    await create_exercise(
        session,
        name=f"Free {uuid4().hex[:6]}",
        short_name=f"F{uuid4().hex[:4]}",
        style=SwimmingStyle.freestyle,
        distance_meters=50,
    )

    exercises, _ = await get_exercises(session, style=SwimmingStyle.backstroke)
    assert all(e.style == SwimmingStyle.backstroke for e in exercises)


@pytest.mark.asyncio
async def test_get_exercises_pagination(session):
    for i in range(3):
        await create_exercise(
            session,
            name=f"Page Ex {uuid4().hex[:6]}",
            short_name=f"P{uuid4().hex[:4]}",
            style=SwimmingStyle.freestyle,
            distance_meters=25,
        )

    page1, total = await get_exercises(session, page=1, limit=2)
    assert len(page1) <= 2
    assert total >= 3


@pytest.mark.asyncio
async def test_create_exercise_duplicate_raises(session):
    name = f"Duplicate {uuid4().hex[:6]}"
    await create_exercise(
        session,
        name=name,
        short_name=f"D{uuid4().hex[:4]}",
        style=SwimmingStyle.freestyle,
        distance_meters=100,
    )
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        await create_exercise(
            session,
            name=name,
            short_name=f"D{uuid4().hex[:4]}",
            style=SwimmingStyle.freestyle,
            distance_meters=100,  # same name + distance triggers unique constraint
        )
