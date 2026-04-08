from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from backend.db.models import (
    Exercise,
    SectionType,
    TrainingLevel,
    TrainingStep,
    TrainingTemplate,
)
from backend.seeds.data.base import Seed
from backend.seeds.data.exercises import (
    ExerciseSeed,
    FREE_50, FREE_100, FREE_200, FREE_400,
    BACK_100, BACK_200,
    BREAST_100, BREAST_200,
    FLY_100,
    IM_200,
    KICK_50, KICK_100,
    PULL_200, PULL_400,
    CATCHUP_100, FNGRTIP_100,
)


class TrainingStepSeed(Seed):
    exercise: ExerciseSeed
    repetitions: int = 1
    section_type: SectionType
    rest_seconds: Optional[int] = None
    notes: Optional[str] = None


class TrainingSeed(Seed):
    name: str
    level: TrainingLevel
    description: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    steps: list[TrainingStepSeed]


TRAININGS: list[TrainingSeed] = [
    # --- Beginner ---
    TrainingSeed(
        name="Beginner Endurance",
        level=TrainingLevel.beginner,
        description="Build base endurance with easy freestyle and mixed strokes",
        estimated_duration_minutes=40,
        steps=[
            TrainingStepSeed(exercise=FREE_200, section_type=SectionType.warmup, notes="Take it easy, focus on breathing"),
            TrainingStepSeed(exercise=KICK_100, section_type=SectionType.main, rest_seconds=30, notes="Use kickboard, any style"),
            TrainingStepSeed(exercise=FREE_100, repetitions=4, section_type=SectionType.main, rest_seconds=20, notes="Keep steady pace"),
            TrainingStepSeed(exercise=BACK_200, section_type=SectionType.main),
            TrainingStepSeed(exercise=PULL_200, section_type=SectionType.main, notes="Use pull buoy"),
            TrainingStepSeed(exercise=BREAST_200, section_type=SectionType.main),
            TrainingStepSeed(exercise=FREE_200, section_type=SectionType.cooldown, notes="Easy swimming, relax"),
        ],
    ),
    TrainingSeed(
        name="Beginner Technique",
        level=TrainingLevel.beginner,
        description="Focus on stroke technique with drills and short distances",
        estimated_duration_minutes=35,
        steps=[
            TrainingStepSeed(exercise=FREE_200, section_type=SectionType.warmup, notes="Easy warm-up"),
            TrainingStepSeed(exercise=CATCHUP_100, section_type=SectionType.main, rest_seconds=30, notes="Focus on full arm extension"),
            TrainingStepSeed(exercise=FNGRTIP_100, section_type=SectionType.main, rest_seconds=30, notes="High elbows during recovery"),
            TrainingStepSeed(exercise=FREE_200, section_type=SectionType.main, notes="Apply drill techniques"),
            TrainingStepSeed(exercise=KICK_100, repetitions=2, section_type=SectionType.main, rest_seconds=15, notes="Focus on steady kick from hips"),
            TrainingStepSeed(exercise=BACK_100, section_type=SectionType.main, notes="Long strokes, rotate shoulders"),
            TrainingStepSeed(exercise=BREAST_100, section_type=SectionType.main, notes="Glide after each stroke"),
            TrainingStepSeed(exercise=FREE_100, section_type=SectionType.cooldown),
        ],
    ),

    # --- Intermediate ---
    TrainingSeed(
        name="Intermediate Mixed",
        level=TrainingLevel.intermediate,
        description="All four strokes with moderate intensity",
        estimated_duration_minutes=55,
        steps=[
            TrainingStepSeed(exercise=FREE_100, repetitions=4, section_type=SectionType.warmup, rest_seconds=10, notes="100 each stroke"),
            TrainingStepSeed(exercise=KICK_100, repetitions=2, section_type=SectionType.main, rest_seconds=15, notes="Alternate freestyle and backstroke kick"),
            TrainingStepSeed(exercise=IM_200, section_type=SectionType.main, rest_seconds=30, notes="50 of each stroke"),
            TrainingStepSeed(exercise=FREE_400, section_type=SectionType.main, notes="Moderate pace, bilateral breathing"),
            TrainingStepSeed(exercise=BACK_200, section_type=SectionType.main),
            TrainingStepSeed(exercise=PULL_400, section_type=SectionType.main, notes="Steady pace with pull buoy"),
            TrainingStepSeed(exercise=FREE_200, section_type=SectionType.cooldown),
        ],
    ),
    TrainingSeed(
        name="Intermediate Speed",
        level=TrainingLevel.intermediate,
        description="Build speed with interval sets and sprints",
        estimated_duration_minutes=50,
        steps=[
            TrainingStepSeed(exercise=FREE_100, repetitions=4, section_type=SectionType.warmup, rest_seconds=10),
            TrainingStepSeed(exercise=KICK_50, repetitions=4, section_type=SectionType.main, rest_seconds=15, notes="Build speed each 50"),
            TrainingStepSeed(exercise=FREE_50, repetitions=8, section_type=SectionType.main, rest_seconds=15, notes="Aim for consistent splits"),
            TrainingStepSeed(exercise=BACK_200, section_type=SectionType.main, notes="Active recovery"),
            TrainingStepSeed(exercise=FREE_50, repetitions=4, section_type=SectionType.main, rest_seconds=30, notes="Maximum effort"),
            TrainingStepSeed(exercise=PULL_200, section_type=SectionType.main, notes="Easy pull, recover"),
            TrainingStepSeed(exercise=FREE_200, section_type=SectionType.cooldown),
        ],
    ),

    # --- Advanced ---
    TrainingSeed(
        name="Advanced Endurance",
        level=TrainingLevel.advanced,
        description="High-volume endurance set with sustained effort",
        estimated_duration_minutes=70,
        steps=[
            TrainingStepSeed(exercise=FREE_100, repetitions=4, section_type=SectionType.warmup, rest_seconds=10),
            TrainingStepSeed(exercise=KICK_100, repetitions=2, section_type=SectionType.main, rest_seconds=15, notes="Strong kick, build pace"),
            TrainingStepSeed(exercise=FREE_400, section_type=SectionType.main, rest_seconds=30, notes="Threshold pace"),
            TrainingStepSeed(exercise=IM_200, section_type=SectionType.main, rest_seconds=30),
            TrainingStepSeed(exercise=FREE_100, repetitions=4, section_type=SectionType.main, rest_seconds=20, notes="Descend 1-4"),
            TrainingStepSeed(exercise=FLY_100, section_type=SectionType.main, rest_seconds=30, notes="Focus on rhythm"),
            TrainingStepSeed(exercise=PULL_400, section_type=SectionType.main, notes="Steady effort"),
            TrainingStepSeed(exercise=FREE_50, repetitions=8, section_type=SectionType.main, rest_seconds=15, notes="Hold pace"),
            TrainingStepSeed(exercise=FREE_200, section_type=SectionType.cooldown),
        ],
    ),
    TrainingSeed(
        name="Advanced Sprint",
        level=TrainingLevel.advanced,
        description="Race-pace sprints with active recovery",
        estimated_duration_minutes=60,
        steps=[
            TrainingStepSeed(exercise=FREE_100, repetitions=4, section_type=SectionType.warmup, rest_seconds=10),
            TrainingStepSeed(exercise=KICK_50, repetitions=4, section_type=SectionType.main, rest_seconds=15, notes="Fast kick, build each set"),
            TrainingStepSeed(exercise=FREE_50, repetitions=4, section_type=SectionType.main, rest_seconds=60, notes="All-out effort, full recovery"),
            TrainingStepSeed(exercise=BACK_200, section_type=SectionType.main, notes="Active recovery"),
            TrainingStepSeed(exercise=FLY_100, section_type=SectionType.main, rest_seconds=30, notes="Strong, fast tempo"),
            TrainingStepSeed(exercise=FREE_50, repetitions=8, section_type=SectionType.main, rest_seconds=15, notes="Race pace"),
            TrainingStepSeed(exercise=IM_200, section_type=SectionType.main, rest_seconds=30, notes="Push each stroke"),
            TrainingStepSeed(exercise=PULL_200, section_type=SectionType.main, notes="Easy recovery pull"),
            TrainingStepSeed(exercise=FREE_200, section_type=SectionType.cooldown),
        ],
    ),
]


async def seed_trainings(session: AsyncSession) -> None:
    # Build exercise lookup: (name, distance) -> id
    result = await session.execute(select(Exercise.id, Exercise.name, Exercise.distance_meters))
    exercise_map: dict[tuple[str, int], UUID] = {
        (row.name, row.distance_meters): row.id for row in result.all()
    }

    for t in TRAININGS:
        total_distance = sum(
            s.exercise.distance_meters * s.repetitions for s in t.steps
        )

        # Upsert training template
        stmt = insert(TrainingTemplate).values(
            name=t.name,
            version=1,
            level=t.level,
            description=t.description,
            estimated_duration_minutes=t.estimated_duration_minutes,
            total_distance=total_distance,
            is_active=True,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="unique_name-version",
            set_={
                "description": stmt.excluded.description,
                "level": stmt.excluded.level,
                "estimated_duration_minutes": stmt.excluded.estimated_duration_minutes,
                "total_distance": stmt.excluded.total_distance,
                "is_active": stmt.excluded.is_active,
            },
        )
        await session.execute(stmt)

        # Get the training template id
        tt_result = await session.execute(
            select(TrainingTemplate.id).where(
                TrainingTemplate.name == t.name,
                TrainingTemplate.version == 1,
            )
        )
        training_id = tt_result.scalar_one()

        # Delete existing steps and re-insert (idempotency)
        await session.execute(
            TrainingStep.__table__.delete().where(
                TrainingStep.training_template_id == training_id
            )
        )

        for step_num, s in enumerate(t.steps, start=1):
            ex = s.exercise
            exercise_id = exercise_map.get((ex.name, ex.distance_meters))
            if exercise_id is None:
                raise RuntimeError(
                    f"Exercise not found: ({ex.name}, {ex.distance_meters}m). "
                    f"Make sure exercises are seeded first."
                )
            step = TrainingStep(
                training_template_id=training_id,
                exercise_id=exercise_id,
                step_number=step_num,
                repetitions=s.repetitions,
                section_type=s.section_type,
                rest_seconds=s.rest_seconds,
                notes=s.notes,
            )
            session.add(step)

    await session.commit()
