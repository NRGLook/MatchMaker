"""First version of models

Revision ID: adc34179983e
Revises: 
Create Date: 2024-12-07 15:04:27.256676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'adc34179983e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('category',
    sa.Column('name', sa.String(length=255), nullable=False, comment='Category name (e.g., Sports, Music, etc.)'),
    sa.Column('description', sa.String(length=255), nullable=False, comment='Description of the category'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('team',
    sa.Column('name', sa.String(length=255), nullable=False, comment="Team's name"),
    sa.Column('description', sa.String(length=255), nullable=False, comment='Short description of the team'),
    sa.Column('logo_url', sa.String(length=255), nullable=False, comment="URL of the team's logo"),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('username', sa.String(length=255), nullable=False, comment='Unique username of the user'),
    sa.Column('role', sa.String(length=50), nullable=False, comment='Role of the user (e.g., admin, player, etc.)'),
    sa.Column('first_name', sa.String(length=255), nullable=False, comment="User's first name"),
    sa.Column('last_name', sa.String(length=255), nullable=False, comment="User's last name"),
    sa.Column('age', sa.Integer(), nullable=False, comment='Age of the user (must be greater than 0)'),
    sa.Column('experience', sa.Integer(), nullable=False, comment='Years of experience'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('event',
    sa.Column('category_id', sa.UUID(), nullable=False, comment='ID of the associated category'),
    sa.Column('location', sa.Text(), nullable=False, comment='Event location'),
    sa.Column('people_amount', sa.Integer(), nullable=False, comment='Number of participants'),
    sa.Column('experience', sa.Integer(), nullable=False, comment='Experience level required'),
    sa.Column('date_time', sa.Date(), nullable=False, comment='Date and time of the event'),
    sa.Column('organizer_id', sa.UUID(), nullable=False, comment='ID of the event organizer'),
    sa.Column('description', sa.String(length=255), nullable=False, comment='Event description'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['category.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['organizer_id'], ['user.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('rsvp',
    sa.Column('user_id', sa.UUID(), nullable=False, comment='ID of the user'),
    sa.Column('event_id', sa.UUID(), nullable=False, comment='ID of the event'),
    sa.Column('status', sa.String(length=50), nullable=False, comment='RSVP status of the user'),
    sa.Column('responded_at', sa.Date(), nullable=False, comment='Date when the user responded'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('statistic',
    sa.Column('user_id', sa.UUID(), nullable=False, comment='ID of the user'),
    sa.Column('event_id', sa.UUID(), nullable=False, comment='ID of the event'),
    sa.Column('score', sa.Integer(), nullable=False, comment='Score achieved by the user'),
    sa.Column('rating', sa.Float(), nullable=False, comment='Rating for the user (1 to 5)'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['event_id'], ['event.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('player',
    sa.Column('user_id', sa.UUID(), nullable=False, comment='ID of the user (player)'),
    sa.Column('rsvp_id', sa.UUID(), nullable=False, comment='RSVP ID for the player'),
    sa.Column('team_id', sa.UUID(), nullable=False, comment='Team ID that the player belongs to'),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['rsvp_id'], ['rsvp.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('player')
    op.drop_table('statistic')
    op.drop_table('rsvp')
    op.drop_table('event')
    op.drop_table('user')
    op.drop_table('team')
    op.drop_table('category')
    # ### end Alembic commands ###
