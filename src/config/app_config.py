from src.config.settings import SettingsProvider


settings = SettingsProvider.get()

api_version = settings.API_VERSION
