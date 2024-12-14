from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from src.models.database_models import User


class UserManager:
    """CRUD-менеджер для работы с моделью User."""

    @staticmethod
    async def get_user(
        session: AsyncSession,
        user_id: UUID
    ) -> User:
        """
        Получение пользователя по его UUID.
        :param session: AsyncSession — асинхронная сессия SQLAlchemy.
        :param user_id: UUID — UUID пользователя.
        :return: User | None — объект пользователя или None, если не найден.
        """
        try:
            result = await session.execute(select(User).filter(User.id == user_id))
            return result.scalars().first()
        except SQLAlchemyError as e:
            raise RuntimeError(f"Ошибка получения пользователя: {str(e)}")

    @staticmethod
    async def create_user(
        session: AsyncSession,
        user_id: UUID,
        username: str = None
    ) -> User:
        """
        Создание нового пользователя.
        :param session: AsyncSession — асинхронная сессия SQLAlchemy.
        :param user_id: str — UUID пользователя.
        :param username: str — Имя пользователя Telegram (опционально).
        :return: User — созданный объект пользователя.
        """
        try:
            new_user = User(id=user_id, username=username)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user
        except SQLAlchemyError as e:
            await session.rollback()
            raise RuntimeError(f"Ошибка создания пользователя: {str(e)}")

    @staticmethod
    async def update_user(
        session: AsyncSession,
        user_id: UUID,
        field: str,
        value
    ) -> User:
        """
        Обновление определенного поля у пользователя.
        :param session: AsyncSession — асинхронная сессия SQLAlchemy.
        :param user_id: str — UUID пользователя.
        :param field: str — Название поля для обновления.
        :param value: значение, которое нужно установить.
        :return: User — объект пользователя с обновленными данными.
        """
        try:
            user = await UserManager.get_user(session, user_id)
            if not user:
                raise ValueError("Пользователь не найден.")

            if not hasattr(user, field):
                raise ValueError(f"Поле '{field}' отсутствует в модели User.")

            setattr(user, field, value)
            await session.commit()
            await session.refresh(user)
            return user
        except SQLAlchemyError as e:
            await session.rollback()
            raise RuntimeError(f"Ошибка обновления пользователя: {str(e)}")
