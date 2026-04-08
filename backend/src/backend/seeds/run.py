from backend.db.session import SessionLocal
from backend.seeds.registry import seed_manager


async def run_seeds() -> None:
    async with SessionLocal() as session:
        await seed_manager.run(session)


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_seeds())