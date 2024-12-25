from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from src.config.database_config import get_async_session
from src.models.managers.user import UserManager
from src.functionality.user.schemes import UserSchema


class UserService:
    """Сервис для работы с пользователем."""

    @staticmethod
    async def get_or_create_user(user_id: str, username: Optional[str] = None):
        """Получить или создать пользователя."""
        async with get_async_session() as session:
            try:
                user = await UserManager.get_user(session, user_id)
                if not user:
                    user = await UserManager.create_user(session, user_id, username)
                return user
            except SQLAlchemyError as e:
                raise RuntimeError(f"Ошибка работы с БД: {str(e)}")

    @staticmethod
    async def update_user_field(user_id: str, field: str, value):
        """Обновить определенное поле пользователя."""
        async with get_async_session() as session:
            try:
                validated_data = UserSchema(**{field: value})
                return await UserManager.update_user(session, user_id, field, validated_data.dict()[field])
            except ValueError as e:
                raise ValueError(f"Ошибка валидации данных: {e}")
            except SQLAlchemyError as e:
                raise RuntimeError(f"Ошибка работы с БД: {str(e)}")
