import pytest
from backend.seeds.manager import SeedManager


@pytest.mark.asyncio
async def test_seed_manager_order():
    calls = []
    async def seed_a(session):
        calls.append("a")
    async def seed_b(session):
        calls.append("b")
    async def seed_c(session):
        calls.append("c")

    manager = SeedManager()
    manager.register("c", seed_c, depends_on=["b"])
    manager.register("b", seed_b, depends_on=["a"])
    manager.register("a", seed_a)

    await manager.run(session=None)
    assert calls == ['a', 'b', 'c']


@pytest.mark.asyncio
async def test_seed_runs_once():
    calls = []
    async def seed_a(session):
        calls.append("a")
    async def seed_b(session):
        calls.append("b")
    async def seed_c(session):
        calls.append("c")

    manager = SeedManager()
    manager.register("c", seed_c, depends_on=["a"])
    manager.register("b", seed_b, depends_on=["a"])
    manager.register("a", seed_a)

    await manager.run(session=None)
    assert calls.count('a') == 1


@pytest.mark.asyncio
async def test_error_with_cycle_depends():
    calls = []
    async def seed_a(session):
        calls.append("a")
    async def seed_b(session):
        calls.append("b")

    manager = SeedManager()
    manager.register("a", seed_a, depends_on=["b"])
    manager.register("b", seed_b, depends_on=["a"])

    with pytest.raises(expected_exception=RuntimeError):
        await manager.run(session=None)


@pytest.mark.asyncio
async def test_register_seed_twice():
    calls = []
    async def seed_a(session):
        calls.append("a")
    manager = SeedManager()
    manager.register("a", seed_a)

    with pytest.raises(expected_exception=ValueError):
        manager.register("a", seed_a)