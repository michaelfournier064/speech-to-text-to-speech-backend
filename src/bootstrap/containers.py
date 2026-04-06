from dataclasses import dataclass

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


def build_container(settings: Settings | None = None) -> AppContainer:
    app_settings = settings or Settings()

    session_factory = SqlAlchemySessionFactory(app_settings.database_url)
    session_factory.create_tables()

    repository = SqlAlchemySpeechJobRepository(session_factory)
    storage = LocalObjectStorage(root_dir=app_settings.storage_root)
    asr = WhisperAsr()
    tts = PiperTts()
    transformer = BasicTranscriptTransformer()
    audio_processor = FfmpegAudioProcessor()

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
