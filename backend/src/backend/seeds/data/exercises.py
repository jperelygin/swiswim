from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.seeds.data.base import Seed
from backend.seeds.helpers import seed_base_on_conflict_update
from backend.db.models import Exercise, SwimmingStyle


class ExerciseSeed(Seed):
    name: str
    short_name: str
    style: SwimmingStyle
    distance_meters: int
    description: Optional[str] = None
    content_markdown: Optional[str] = None


# --- Freestyle ---
FREE_50 = ExerciseSeed(name="Freestyle 50", short_name="Free 50", style=SwimmingStyle.freestyle, distance_meters=50)
FREE_100 = ExerciseSeed(name="Freestyle 100", short_name="Free 100", style=SwimmingStyle.freestyle, distance_meters=100)
FREE_200 = ExerciseSeed(name="Freestyle 200", short_name="Free 200", style=SwimmingStyle.freestyle, distance_meters=200)
FREE_400 = ExerciseSeed(name="Freestyle 400", short_name="Free 400", style=SwimmingStyle.freestyle, distance_meters=400)

# --- Backstroke ---
BACK_50 = ExerciseSeed(name="Backstroke 50", short_name="Back 50", style=SwimmingStyle.backstroke, distance_meters=50)
BACK_100 = ExerciseSeed(name="Backstroke 100", short_name="Back 100", style=SwimmingStyle.backstroke, distance_meters=100)
BACK_200 = ExerciseSeed(name="Backstroke 200", short_name="Back 200", style=SwimmingStyle.backstroke, distance_meters=200)

# --- Breaststroke ---
BREAST_50 = ExerciseSeed(name="Breaststroke 50", short_name="Breast 50", style=SwimmingStyle.breaststroke, distance_meters=50)
BREAST_100 = ExerciseSeed(name="Breaststroke 100", short_name="Breast 100", style=SwimmingStyle.breaststroke, distance_meters=100)
BREAST_200 = ExerciseSeed(name="Breaststroke 200", short_name="Breast 200", style=SwimmingStyle.breaststroke, distance_meters=200)

# --- Butterfly ---
FLY_50 = ExerciseSeed(name="Butterfly 50", short_name="Fly 50", style=SwimmingStyle.butterfly, distance_meters=50)
FLY_100 = ExerciseSeed(name="Butterfly 100", short_name="Fly 100", style=SwimmingStyle.butterfly, distance_meters=100)

# --- Individual Medley ---
IM_100 = ExerciseSeed(name="IM 100", short_name="IM 100", style=SwimmingStyle.mixed, distance_meters=100, description="25 fly + 25 back + 25 breast + 25 free")
IM_200 = ExerciseSeed(name="IM 200", short_name="IM 200", style=SwimmingStyle.mixed, distance_meters=200, description="50 fly + 50 back + 50 breast + 50 free")

# --- Kick ---
KICK_50 = ExerciseSeed(name="Kick 50", short_name="Kick 50", style=SwimmingStyle.mixed, distance_meters=50, description="Kick with board, any style")
KICK_100 = ExerciseSeed(name="Kick 100", short_name="Kick 100", style=SwimmingStyle.mixed, distance_meters=100, description="Kick with board, any style")

# --- Pull ---
PULL_200 = ExerciseSeed(name="Pull 200 Free", short_name="Pull 200 Free", style=SwimmingStyle.freestyle, distance_meters=200, description="Freestyle with pull buoy, focus on upper body")
PULL_400 = ExerciseSeed(name="Pull 400 Free", short_name="Pull 400 Free", style=SwimmingStyle.freestyle, distance_meters=400, description="Freestyle with pull buoy, steady pace")

# --- Drills ---
CATCHUP_100 = ExerciseSeed(name="Catch-up Drill 100", short_name="Catch-up 100", style=SwimmingStyle.freestyle, distance_meters=100, description="Freestyle catch-up drill: one arm stays extended until the other finishes the stroke")
FNGRTIP_100 = ExerciseSeed(name="Fingertip Drag 100", short_name="Fngrtip Drag 100", style=SwimmingStyle.freestyle, distance_meters=100, description="Drag fingertips along water surface during recovery phase")


EXERCISES: list[ExerciseSeed] = [
    FREE_50, FREE_100, FREE_200, FREE_400,
    BACK_50, BACK_100, BACK_200,
    BREAST_50, BREAST_100, BREAST_200,
    FLY_50, FLY_100,
    IM_100, IM_200,
    KICK_50, KICK_100,
    PULL_200, PULL_400,
    CATCHUP_100, FNGRTIP_100,
]


async def seed_exercises(session: AsyncSession) -> None:
    await seed_base_on_conflict_update(
        session=session,
        model=Exercise,
        values=EXERCISES,
        index_elems=["name", "distance_meters"]
    )
