from backend.seeds.manager import SeedManager

from backend.seeds.data.exercises import seed_exercises
from backend.seeds.data.trainings import seed_trainings


seed_manager = SeedManager()

seed_manager.register("exercises", seed_exercises)
seed_manager.register("trainings", seed_trainings, depends_on=["exercises"])