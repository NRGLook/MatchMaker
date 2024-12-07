from sqlalchemy import (
    DateTime,
)
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime


class IDMixin:
    """Mixin to add unique identifier PK with UUID."""
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


# Mixin for adding timestamp fields
class TimestampMixin:
    """Mixin to add timestamp fields: created_at and updated_at with UTC time."""
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow,
                                                 onupdate=datetime.utcnow)