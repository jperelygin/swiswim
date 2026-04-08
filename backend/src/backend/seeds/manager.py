from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from collections.abc import Awaitable, Callable


SeedFn = Callable[..., Awaitable[None]]

class SeedManager:
    def __init__(self) -> None:
        self._seeds: dict = {} # type: ignore

    def register(self, name: str, fn: SeedFn, *, depends_on: Optional[list[str]] = None) -> None:
        if name in self._seeds:
            raise ValueError(f"Seed '{name}' already registered!")
        self._seeds[name] = {
            "fn": fn,
            "depends_on": depends_on or []
        }

    async def run(self, session: AsyncSession) -> None:
        for name in self._resolve_order():
            await self._seeds[name]["fn"](session)

    def _resolve_order(self) -> list[str]:
        visited: set[str] = set()
        visiting: set[str] = set()
        order: list[str] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            if name in visiting:
                raise RuntimeError(f"Cyclic dependency in seed: {name}")
            if name not in self._seeds:
                raise RuntimeError(f"Seed '{name}' not registered!")
            visiting.add(name)
            for dep in self._seeds[name]["depends_on"]:
                visit(dep)
            visiting.remove(name)
            visited.add(name)
            order.append(name)
        
        for name in self._seeds:
            visit(name)

        return order