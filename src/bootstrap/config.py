from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "speech-to-speech-backend"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/speech_to_speech"
    storage_root: str = ".data"

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")
