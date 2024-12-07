import os

from typing import Optional
from dotenv import load_dotenv

from pydantic import BaseModel, ConfigDict


class Settings(BaseModel):
    model_config = ConfigDict(
        alias_generator=str.upper
    )

    API_VERSION: int = 1

    API_KEY: str

    # Database settings
    # DB_HOST: str | None
    # DB_PORT: str | None
    # DB_DRIVER_NAME: str | None
    # DB_DATABASE_NAME: str | None
    # DB_USERNAME: str | None
    # DB_PASSWORD: str | None
    #
    # @property
    # def get_db_creds(self):
    #     return {
    #         "drivername": self.DB_DRIVER_NAME,
    #         "username": self.DB_USERNAME,
    #         "host": self.DB_HOST,
    #         "port": self.DB_PORT,
    #         "database": self.DB_DATABASE_NAME,
    #         "password": self.DB_PASSWORD,
    #     }


class SettingsProvider:
    __settings: Optional[Settings] = None

    @classmethod
    def get(cls, dotenv_path: str = './contrib/docker/.env') -> Settings:
        if cls.__settings is None:
            cls.__settings = cls.__load_settings(dotenv_path)
        return cls.__settings

    @staticmethod
    def __load_settings(dotenv_path: str = './contrib/docker/.env') -> Settings:
        load_dotenv(dotenv_path=dotenv_path, override=True)
        return Settings.model_validate(os.environ)
