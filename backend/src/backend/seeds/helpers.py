from typing import List, Sequence
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from backend.seeds.data.base import Seed


async def seed_base_on_conflict_update(session: AsyncSession,
                                        model: type[DeclarativeBase], 
                                        values: Sequence[Seed], 
                                        index_elems: List[str]) -> None:
    rows = [v.model_dump() for v in values]
    stmt = insert(model).values(rows)

    update_columns = {
        col: getattr(stmt.excluded, col)
        for col in rows[0].keys()
        if col not in index_elems
    }

    stmt = stmt.on_conflict_do_update(
        index_elements=index_elems,
        set_=update_columns
    )

    await session.execute(stmt)
    await session.commit()