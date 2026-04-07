from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "speech-to-speech-backend"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/speech_to_speech"
    storage_root: str = ".data"
    ffmpeg_command: str = "ffmpeg"
    ffmpeg_timeout_seconds: int = 30
    asr_command: str = "whisper-cli"
    asr_model_path: str = "models/ggml-base.en.bin"
    asr_language: str = "en"
    asr_timeout_seconds: int = 120
    tts_command: str = "piper"
    tts_model_path: str = "models/en_US-lessac-medium.onnx"
    tts_config_path: str | None = None
    tts_voice_models_json: str | None = None
    tts_voice_configs_json: str | None = None
    tts_timeout_seconds: int = 60

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")
