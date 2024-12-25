from uuid import UUID


def convert_telegram_id_to_uuid(telegram_id: int) -> UUID:
    """Convert Telegram ID to UUID."""
    return UUID(int=telegram_id, version=4)
