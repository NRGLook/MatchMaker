import pytest
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import date
from src.models.database_models import (
    Category, User, Team, Event, RSVP, Player, Statistic, Feedback
)

def create_mock_category(session):
    category = Category(
        name="Sports",
        description="Sports related activities"
    )
    session.add(category)
    session.commit()
    return category

def create_mock_user(session):
    user = User(
        username="test_user",
        role="player",
        first_name="John",
        last_name="Doe",
        age=25,
        experience=3
    )
    session.add(user)
    session.commit()
    return user

def create_mock_team(session, creator):
    team = Team(
        name="Test Team",
        description="A mock team",
        logo_url="http://example.com/logo.png",
        creator_id=creator.id
    )
    session.add(team)
    session.commit()
    return team

def create_mock_event(session, category, organizer):
    event = Event(
        title="Mock Event",
        category_id=category.id,
        location="Mock Location",
        people_amount=10,
        experience=1,
        date_time=date.today(),
        organizer_id=organizer.id,
        description="A mock event for testing."
    )
    session.add(event)
    session.commit()
    return event

def create_mock_rsvp(session, user, event):
    rsvp = RSVP(
        user_id=user.id,
        event_id=event.id,
        status="accepted",
        responded_at=date.today()
    )
    session.add(rsvp)
    session.commit()
    return rsvp

def create_mock_statistic(session, user, event):
    stat = Statistic(
        user_id=user.id,
        event_id=event.id,
        score=100,
        rating=4.5
    )
    session.add(stat)
    session.commit()
    return stat

def create_mock_feedback(session, user):
    feedback = Feedback(
        user_id=user.id,
        text="Great event!"
    )
    session.add(feedback)
    session.commit()
    return feedback

@pytest.mark.parametrize("model_class", [Category, User, Team, Event, RSVP, Player, Statistic, Feedback])
def test_model_table_exists(session: Session, model_class):
    # Проверка существования таблиц
    assert session.bind.has_table(model_class.__tablename__), f"Table {model_class.__tablename__} does not exist."

def test_category_constraints(session: Session):
    # Проверка ограничений Category
    category = Category(name=None)  # name cannot be None
    session.add(category)
    with pytest.raises(IntegrityError):
        session.commit()

def test_user_constraints(session: Session):
    # Проверка ограничений User
    user = User(username="test_user", age=-1)  # Invalid age
    session.add(user)
    with pytest.raises(IntegrityError):
        session.commit()

def test_team_creation(session: Session):
    # Создание команды с реальными связями
    creator = create_mock_user(session)
    team = create_mock_team(session, creator)

    assert team.creator_id == creator.id
    assert team.creator.username == "test_user"

def test_event_relationships(session: Session):
    # Проверка отношений Event
    category = create_mock_category(session)
    organizer = create_mock_user(session)
    event = create_mock_event(session, category, organizer)

    assert event.category_id == category.id
    assert event.organizer_id == organizer.id

def test_rsvp_relationships(session: Session):
    # Проверка отношений RSVP
    user = create_mock_user(session)
    category = create_mock_category(session)
    event = create_mock_event(session, category, user)
    rsvp = create_mock_rsvp(session, user, event)

    assert rsvp.user_id == user.id
    assert rsvp.event_id == event.id

def test_statistic_constraints(session: Session):
    # Проверка ограничений Statistic
    user = create_mock_user(session)
    category = create_mock_category(session)
    event = create_mock_event(session, category, user)
    stat = Statistic(user_id=user.id, event_id=event.id, score=-10)  # Invalid score
    session.add(stat)
    with pytest.raises(IntegrityError):
        session.commit()

def test_feedback_relationships(session: Session):
    # Проверка отношений Feedback
    user = create_mock_user(session)
    feedback = create_mock_feedback(session, user)

    assert feedback.user_id == user.id
    assert feedback.text == "Great event!"

def test_player_relationships(session: Session):
    # Проверка отношений Player
    user = create_mock_user(session)
    category = create_mock_category(session)
    event = create_mock_event(session, category, user)
    rsvp = create_mock_rsvp(session, user, event)
    team = create_mock_team(session, user)
    player = Player(user_id=user.id, rsvp_id=rsvp.id, team_id=team.id)
    session.add(player)
    session.commit()

    assert player.user_id == user.id
    assert player.rsvp_id == rsvp.id
    assert player.team_id == team.id

def test_category_duplicate_name(session: Session):
    # Проверка ограничения уникальности имени категории
    category1 = create_mock_category(session)
    category2 = Category(name=category1.name, description="Duplicate name")
    session.add(category2)
    with pytest.raises(IntegrityError):
        session.commit()

def test_event_people_amount_constraint(session: Session):
    # Проверка ограничения на количество участников события
    category = create_mock_category(session)
    organizer = create_mock_user(session)
    event = Event(
        title="Invalid Event",
        category_id=category.id,
        location="Mock Location",
        people_amount=-5,  # Неверное количество участников
        experience=1,
        date_time=date.today(),
        organizer_id=organizer.id,
        description="Event with invalid people amount."
    )
    session.add(event)
    with pytest.raises(IntegrityError):
        session.commit()

def test_rsvp_status_constraint(session: Session):
    # Проверка ограничения на статус RSVP
    user = create_mock_user(session)
    category = create_mock_category(session)
    event = create_mock_event(session, category, user)
    invalid_rsvp = RSVP(
        user_id=user.id,
        event_id=event.id,
        status="invalid_status",  # Некорректный статус
        responded_at=date.today()
    )
    session.add(invalid_rsvp)
    with pytest.raises(DataError):
        session.commit()

def test_statistic_rating_constraint(session: Session):
    # Проверка ограничения на рейтинг Statistic
    user = create_mock_user(session)
    category = create_mock_category(session)
    event = create_mock_event(session, category, user)
    invalid_stat = Statistic(
        user_id=user.id,
        event_id=event.id,
        score=50,
        rating=6.0  # Рейтинг выше допустимого диапазона
    )
    session.add(invalid_stat)
    with pytest.raises(IntegrityError):
        session.commit()

def test_feedback_null_text_constraint(session: Session):
    # Проверка ограничения на обязательность текста в Feedback
    user = create_mock_user(session)
    invalid_feedback = Feedback(
        user_id=user.id,
        text=None  # Текст не должен быть null
    )
    session.add(invalid_feedback)
    with pytest.raises(IntegrityError):
        session.commit()

def test_team_duplicate_name(session: Session):
    # Проверка уникальности названия команды
    creator = create_mock_user(session)
    team1 = create_mock_team(session, creator)
    team2 = Team(
        name=team1.name,  # Дублируем название
        description="Duplicate team name",
        logo_url="http://example.com/logo2.png",
        creator_id=creator.id
    )
    session.add(team2)
    with pytest.raises(IntegrityError):
        session.commit()
