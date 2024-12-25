from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date


class EventBaseSchema(BaseModel):
    category_id: UUID
    location: str
    people_amount: int
    experience: int
    date_time: date
    organizer_id: UUID
    description: str


class EventCreateSchema(EventBaseSchema):
    pass


class EventUpdateSchema(BaseModel):
    category_id: UUID | None = None
    location: str | None = None
    people_amount: int | None = None
    experience: int | None = None
    date_time: date | None = None
    organizer_id: UUID | None = None
    description: str | None = None
