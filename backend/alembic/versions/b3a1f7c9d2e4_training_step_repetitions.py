"""training_step_repetitions

Revision ID: b3a1f7c9d2e4
Revises: 78f69734f852
Create Date: 2026-02-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b3a1f7c9d2e4'
down_revision: Union[str, None] = '78f69734f852'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create section_type enum
    section_type_enum = sa.Enum('warmup', 'main', 'cooldown', name='section_type')
    section_type_enum.create(op.get_bind(), checkfirst=True)

    # Add new columns to training_steps
    op.add_column('training_steps', sa.Column('repetitions', sa.Integer(), server_default='1', nullable=False))
    op.add_column('training_steps', sa.Column('section_type', sa.Enum('warmup', 'main', 'cooldown', name='section_type'), nullable=False, server_default='main'))
    op.add_column('training_steps', sa.Column('rest_seconds', sa.Integer(), nullable=True))

    # Remove the server default on section_type (it was only for migration of existing rows)
    op.alter_column('training_steps', 'section_type', server_default=None)

    # Drop distance_meters from training_steps
    op.drop_column('training_steps', 'distance_meters')


def downgrade() -> None:
    op.add_column('training_steps', sa.Column('distance_meters', sa.Integer(), nullable=False, server_default='0'))
    op.alter_column('training_steps', 'distance_meters', server_default=None)
    op.drop_column('training_steps', 'rest_seconds')
    op.drop_column('training_steps', 'section_type')
    op.drop_column('training_steps', 'repetitions')

    sa.Enum('warmup', 'main', 'cooldown', name='section_type').drop(op.get_bind(), checkfirst=True)
