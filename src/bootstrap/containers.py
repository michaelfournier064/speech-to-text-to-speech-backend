from dataclasses import dataclass
import json

from src.adapters.outbound.audio.ffmpeg_audio_processor import FfmpegAudioProcessor
from src.adapters.outbound.persistence.sqlalchemy.session import SqlAlchemySessionFactory
from src.adapters.outbound.persistence.sqlalchemy.speech_job_repository import (
    SqlAlchemySpeechJobRepository,
)
from src.adapters.outbound.speech.piper_tts import PiperTts
from src.adapters.outbound.speech.whisper_asr import WhisperAsr
from src.adapters.outbound.storage.local_object_storage import LocalObjectStorage
from src.adapters.outbound.transcript.basic_transcript_transformer import (
    BasicTranscriptTransformer,
)
from src.application.use_cases.create_speech_job import CreateSpeechJob
from src.application.use_cases.get_output_audio import GetOutputAudio
from src.application.use_cases.get_speech_job import GetSpeechJob
from src.bootstrap.config import Settings


@dataclass
class AppContainer:
    create_speech_job: CreateSpeechJob
    get_speech_job: GetSpeechJob
    get_output_audio: GetOutputAudio


def _parse_string_map(raw_json: str | None, setting_name: str) -> dict[str, str]:
    if not raw_json:
        return {}

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Setting '{setting_name}' must be valid JSON") from exc

    if not isinstance(parsed, dict):
        raise ValueError(f"Setting '{setting_name}' must be a JSON object")

    for key, value in parsed.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError(f"Setting '{setting_name}' must map string keys to string values")

    return parsed


def _parse_nullable_string_map(raw_json: str | None, setting_name: str) -> dict[str, str | None]:
    if not raw_json:
        return {}

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Setting '{setting_name}' must be valid JSON") from exc

    if not isinstance(parsed, dict):
        raise ValueError(f"Setting '{setting_name}' must be a JSON object")

    for key, value in parsed.items():
        if not isinstance(key, str) or (value is not None and not isinstance(value, str)):
            raise ValueError(
                f"Setting '{setting_name}' must map string keys to string or null values"
            )

    return parsed


def build_container(settings: Settings | None = None) -> AppContainer:
    app_settings = settings or Settings()
    voice_models = _parse_string_map(app_settings.tts_voice_models_json, "APP_TTS_VOICE_MODELS_JSON")
    voice_configs = _parse_nullable_string_map(
        app_settings.tts_voice_configs_json,
        "APP_TTS_VOICE_CONFIGS_JSON",
    )

    session_factory = SqlAlchemySessionFactory(app_settings.database_url)
    session_factory.create_tables()

    repository = SqlAlchemySpeechJobRepository(session_factory)
    storage = LocalObjectStorage(root_dir=app_settings.storage_root)
    asr = WhisperAsr(
        command=app_settings.asr_command,
        model_path=app_settings.asr_model_path,
        language=app_settings.asr_language,
        timeout_seconds=app_settings.asr_timeout_seconds,
    )
    tts = PiperTts(
        command=app_settings.tts_command,
        model_path=app_settings.tts_model_path,
        config_path=app_settings.tts_config_path,
        voice_models=voice_models,
        voice_configs=voice_configs,
        timeout_seconds=app_settings.tts_timeout_seconds,
    )
    transformer = BasicTranscriptTransformer()
    audio_processor = FfmpegAudioProcessor(
        ffmpeg_command=app_settings.ffmpeg_command,
        timeout_seconds=app_settings.ffmpeg_timeout_seconds,
    )

    create_speech_job = CreateSpeechJob(
        repository=repository,
        asr=asr,
        tts=tts,
        storage=storage,
        transformer=transformer,
        audio_processor=audio_processor,
    )
    get_speech_job = GetSpeechJob(repository=repository)
    get_output_audio = GetOutputAudio(repository=repository, storage=storage)

    return AppContainer(
        create_speech_job=create_speech_job,
        get_speech_job=get_speech_job,
        get_output_audio=get_output_audio,
    )
