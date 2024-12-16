from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
    Date,
    Text,
    Float,
    CheckConstraint,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID

from src.models.mixins import TimestampMixin, IDMixin

Base = declarative_base()


class Category(Base, TimestampMixin, IDMixin):
    __tablename__ = 'category'

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Category name (e.g., Sports, Music, etc.)"
    )
    description: Mapped[str] = mapped_column(
        String(255),
        comment="Description of the category"
    )


class User(Base, TimestampMixin, IDMixin):
    __tablename__ = 'user'

    username: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        comment="Unique username of the user"
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        comment="Role of the user (e.g., admin, player, etc.)"
    )
    first_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="User's first name"
    )
    last_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="User's last name"
    )
    age: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint('age > 0'),
        nullable=True,
        comment="Age of the user (must be greater than 0)"
    )
    experience: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint('experience >= 0'),
        nullable=True,
        comment="Years of experience"
    )


class Team(Base, TimestampMixin, IDMixin):
    __tablename__ = 'team'

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Team's name"
    )
    description: Mapped[str] = mapped_column(
        String(255),
        comment="Short description of the team"
    )
    logo_url: Mapped[str] = mapped_column(
        String(255),
        comment="URL of the team's logo"
    )
    creator_id: Mapped[UUID] = mapped_column(
        ForeignKey('user.id', ondelete="SET NULL"),
        nullable=False,
       comment="ID of the team creator"
    )

    creator: Mapped[User] = relationship("User", backref="creator_team")


class Event(Base, TimestampMixin, IDMixin):
    __tablename__ = 'event'

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Title of the event"
    )
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey('category.id', ondelete="CASCADE"),
        nullable=False,
        comment="ID of the associated category"
    )
    location: Mapped[str] = mapped_column(
        Text,
        comment="Event location"
    )
    people_amount: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint('people_amount >= 0'),
        comment="Number of participants"
    )
    experience: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint('experience >= 0'),
        comment="Experience level required"
    )
    date_time: Mapped[Date] = mapped_column(
        Date,
        nullable=False,
        comment="Date and time of the event"
    )
    organizer_id: Mapped[UUID] = mapped_column(
        ForeignKey('user.id', ondelete="SET NULL"),
        nullable=False,
        comment="ID of the event organizer"
    )
    description: Mapped[str] = mapped_column(
        String(255),
        comment="Event description"
    )

    category: Mapped[Category] = relationship("Category", backref="events")
    organizer: Mapped[User] = relationship("User", backref="organized_events")


class RSVP(Base, TimestampMixin, IDMixin):
    __tablename__ = 'rsvp'

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False,
        comment="ID of the user"
    )
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey('event.id', ondelete="CASCADE"),
        nullable=False,
        comment="ID of the event"
    )
    status: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint("status IN ('accepted', 'declined', 'pending')"),
        comment="RSVP status of the user"
    )
    responded_at: Mapped[Date] = mapped_column(
        Date,
        comment="Date when the user responded"
    )

    user: Mapped[User] = relationship("User", backref="rsvps")
    event: Mapped[Event] = relationship("Event", backref="rsvps")


class Player(Base, TimestampMixin, IDMixin):
    __tablename__ = 'player'

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False,
        comment="ID of the user (player)"
    )
    rsvp_id: Mapped[UUID] = mapped_column(
        ForeignKey('rsvp.id', ondelete="CASCADE"),
        nullable=False,
        comment="RSVP ID for the player"
    )
    team_id: Mapped[UUID] = mapped_column(
        ForeignKey('team.id', ondelete="SET NULL"),
        comment="Team ID that the player belongs to"
    )

    user: Mapped[User] = relationship("User", backref="players")
    rsvp: Mapped[RSVP] = relationship("RSVP", backref="players")
    team: Mapped[Team] = relationship("Team", backref="players")


class Statistic(Base, TimestampMixin, IDMixin):
    __tablename__ = 'statistic'

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('user.id', ondelete="CASCADE"),
        nullable=False,
        comment="ID of the user"
    )
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey('event.id', ondelete="CASCADE"),
        nullable=False,
        comment="ID of the event"
    )
    score: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint('score >= 0'),
        comment="Score achieved by the user"
    )
    rating: Mapped[float] = mapped_column(
        Float,
        CheckConstraint('rating >= 0 AND rating <= 5'),
        comment="Rating for the user (1 to 5)"
    )

    user: Mapped[User] = relationship("User", backref="statistics")
    event: Mapped[Event] = relationship("Event", backref="statistics")
