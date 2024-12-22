from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from src.models.rsvp import RSVP
from src.models.event import Event
from src.models.user import User


class RSVPCRUD:
    """CRUD class for managing RSVP records."""

    @staticmethod
    def create_rsvp(session: Session, user_id: UUID, event_id: UUID, status: str, responded_at: date) -> RSVP:
        """Create a new RSVP record."""
        try:
            rsvp = RSVP(
                user_id=user_id,
                event_id=event_id,
                status=status,
                responded_at=responded_at
            )
            session.add(rsvp)
            session.commit()
            session.refresh(rsvp)
            return rsvp
        except SQLAlchemyError as e:
            session.rollback()
            raise RuntimeError(f"Error creating RSVP: {e}")

    @staticmethod
    def get_rsvp(session: Session, rsvp_id: UUID) -> RSVP | None:
        """Retrieve an RSVP by its ID."""
        try:
            return session.query(RSVP).filter_by(id=rsvp_id).first()
        except SQLAlchemyError as e:
            raise RuntimeError(f"Error retrieving RSVP: {e}")

    @staticmethod
    def get_rsvps_by_user(session: Session, user_id: UUID) -> list[RSVP]:
        """Retrieve all RSVPs for a specific user."""
        try:
            return session.query(RSVP).filter_by(user_id=user_id).all()
        except SQLAlchemyError as e:
            raise RuntimeError(f"Error retrieving RSVPs for user: {e}")

    @staticmethod
    def get_rsvps_by_event(session: Session, event_id: UUID) -> list[RSVP]:
        """Retrieve all RSVPs for a specific event."""
        try:
            return session.query(RSVP).filter_by(event_id=event_id).all()
        except SQLAlchemyError as e:
            raise RuntimeError(f"Error retrieving RSVPs for event: {e}")

    @staticmethod
    def update_rsvp(session: Session, rsvp_id: UUID, status: str = None, responded_at: date = None) -> RSVP:
        """Update an RSVP by its ID."""
        try:
            rsvp = session.query(RSVP).filter_by(id=rsvp_id).first()
            if not rsvp:
                raise ValueError("RSVP with the specified ID was not found.")

            if status:
                rsvp.status = status
            if responded_at:
                rsvp.responded_at = responded_at

            session.commit()
            session.refresh(rsvp)
            return rsvp
        except SQLAlchemyError as e:
            session.rollback()
            raise RuntimeError(f"Error updating RSVP: {e}")

    @staticmethod
    def delete_rsvp(session: Session, rsvp_id: UUID) -> None:
        """Delete an RSVP by its ID."""
        try:
            rsvp = session.query(RSVP).filter_by(id=rsvp_id).first()
            if not rsvp:
                raise ValueError("RSVP with the specified ID was not found.")

            session.delete(rsvp)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise RuntimeError(f"Error deleting RSVP: {e}")
