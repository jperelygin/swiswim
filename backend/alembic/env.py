from typing import List, Dict, Any, cast, Union, Tuple
import os

from sqlalchemy import engine_from_config, pool
from alembic import context
from alembic.operations import ops
from alembic.runtime.migration import MigrationContext
from alembic.operations.ops import MigrationScript

from backend.db.base import Base
from backend.db.models import *


config = context.config

if not config.get_main_option("sqlalchemy.url"):
    database_url = os.getenv("ALEMBIC_DATABASE_URL")
    if not database_url:
        raise RuntimeError("ALEMBIC_DATABASE_URL variable is not set!")
    config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def process_revision_directives(context: MigrationContext, 
                                revision: Union[str, Tuple[str, ...]], 
                                directives: List[MigrationScript]) -> None:
    def _filter_duplicates(ops_list: List[ops.CreateIndexOp]) -> None:
        index_map = {}
        non_index_ops = []

        for op in ops_list:
            if isinstance(op, ops.CreateIndexOp):
                key = (op.table_name, tuple(sorted(op.columns)))
                if key in index_map:
                    existing_op = index_map[key]
                    if isinstance(op.index_name, str) and op.index_name.startswith('ix_'):
                        continue
                    else:
                        index_map[key] = op
                else:
                    index_map[key] = op
            else:
                non_index_ops.append(op)
        ops_list[:] = non_index_ops + list(index_map.values())

    if not directives:
        return
    migration_script = directives[0]
    _filter_duplicates(migration_script.upgrade_ops.ops)
    _filter_duplicates(migration_script.downgrade_ops.ops)

    

def run_migrations_online() -> None:
    conf = config.get_section(config.config_ini_section)
    if not isinstance(conf, dict):
        raise RuntimeError
    
    conf = cast(Dict[str, Any], conf)
    connectable = engine_from_config(
        conf,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            process_revision_directives=process_revision_directives
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()