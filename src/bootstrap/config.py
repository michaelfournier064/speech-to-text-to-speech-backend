from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "speech-to-speech-backend"
    app_env: str = "development"
    storage_root: str = ".data"

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")
