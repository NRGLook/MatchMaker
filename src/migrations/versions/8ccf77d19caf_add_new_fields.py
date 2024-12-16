"""add new fields

Revision ID: 8ccf77d19caf
Revises: 2c4097eefebf
Create Date: 2024-12-16 12:06:14.132292

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ccf77d19caf'
down_revision: Union[str, None] = '2c4097eefebf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('team', sa.Column('creator_id', sa.UUID(), nullable=False, comment='ID of the team creator'))
    op.create_foreign_key(None, 'team', 'user', ['creator_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'team', type_='foreignkey')
    op.drop_column('team', 'creator_id')
    # ### end Alembic commands ###
