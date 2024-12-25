from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select

from src.models.database_models import Event, User
from src.functionality.event.schemes import EventCreateSchema, EventUpdateSchema
from uuid import UUID


class EventManager:
    @staticmethod
    async def create_event(session: AsyncSession, event_data: EventCreateSchema) -> Event:
        """Creates a new event."""
        new_event = Event(**event_data.model_dump())
        session.add(new_event)
        try:
            await session.commit()
            await session.refresh(new_event)
            return new_event
        except SQLAlchemyError as e:
            await session.rollback()
            raise e

    @staticmethod
    async def get_event_by_id(session: AsyncSession, event_id: UUID) -> Event | None:
        """Get event by ID."""
        result = await session.execute(select(Event).where(Event.id == event_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_event(session: AsyncSession, event_id: UUID, event_data: EventUpdateSchema) -> Event | None:
        """Update event by ID."""
        event = await EventManager.get_event_by_id(session, event_id)
        if not event:
            return None

        for key, value in event_data.dict(exclude_unset=True).items():
            setattr(event, key, value)
        try:
            await session.commit()
            await session.refresh(event)
            return event
        except SQLAlchemyError as e:
            await session.rollback()
            raise e

    @staticmethod
    async def delete_event(session: AsyncSession, event_id: UUID) -> bool:
        """Delete event by ID."""
        event = await EventManager.get_event_by_id(session, event_id)
        if not event:
            return False
        await session.delete(event)
        try:
            await session.commit()
            return True
        except SQLAlchemyError as e:
            await session.rollback()
            raise e
