"""empty message

Revision ID: 2c4097eefebf
Revises: 2fcde992fcac
Create Date: 2024-12-15 10:01:15.048319

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c4097eefebf'
down_revision: Union[str, None] = '2fcde992fcac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event', sa.Column('title', sa.String(length=255), nullable=False, comment='Title of the event'))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('event', 'title')
    # ### end Alembic commands ###