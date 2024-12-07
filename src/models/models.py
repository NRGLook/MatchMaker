from sqlalchemy import (
    Column, String, Integer, ForeignKey, Date, Text, Float, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255))


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50))
    first_name = Column(String(255))
    last_name = Column(String(255))
    age = Column(Integer, CheckConstraint('age > 0'))
    experience = Column(Integer, CheckConstraint('experience >= 0'))
    created_at = Column(Date, nullable=False)


class Team(Base):
    __tablename__ = 'team'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255))
    logo_url = Column(String(255))


class Event(Base):
    __tablename__ = 'event'

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey('category.id', ondelete="CASCADE"), nullable=False)
    location = Column(Text)  # SQLAlchemy не поддерживает GEOGRAPHY напрямую
    people_amount = Column(Integer, CheckConstraint('people_amount >= 0'))
    experience = Column(Integer, CheckConstraint('experience >= 0'))
    date_time = Column(Date, nullable=False)
    organizer_id = Column(Integer, ForeignKey('user.id', ondelete="SET NULL"), nullable=False)
    description = Column(String(255))

    category = relationship("Category")
    organizer = relationship("User")


class RSVP(Base):
    __tablename__ = 'rsvp'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"), nullable=False)
    status = Column(String(50), CheckConstraint("status IN ('accepted', 'declined', 'pending')"))
    responded_at = Column(Date)

    user = relationship("User")
    event = relationship("Event")


class Player(Base):
    __tablename__ = 'player'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    rsvp_id = Column(Integer, ForeignKey('rsvp.id', ondelete="CASCADE"), nullable=False)
    team_id = Column(Integer, ForeignKey('team.id', ondelete="SET NULL"))

    user = relationship("User")
    rsvp = relationship("RSVP")
    team = relationship("Team")


class Statistic(Base):
    __tablename__ = 'statistic'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey('event.id', ondelete="CASCADE"), nullable=False)
    score = Column(Integer, CheckConstraint('score >= 0'))
    rating = Column(Float, CheckConstraint('rating >= 0 AND rating <= 5'))
    updated_at = Column(Date, nullable=False)

    user = relationship("User")
    event = relationship("Event")
