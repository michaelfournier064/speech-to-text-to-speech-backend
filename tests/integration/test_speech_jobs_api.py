from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from src.adapters.inbound.api.routes import speech_jobs
from src.application.use_cases.create_speech_job import CreateSpeechJob
from src.application.use_cases.get_output_audio import GetOutputAudio
from src.application.use_cases.get_speech_job import GetSpeechJob
from src.bootstrap.containers import AppContainer
from src.domain.speech_job.entities import SpeechJob
from src.domain.speech_job.enums import SpeechJobStage, SpeechJobStatus


class InMemorySpeechJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, SpeechJob] = {}

    def add(self, job: SpeechJob) -> SpeechJob:
        self._jobs[str(job.id)] = job
        return job

    def get_by_id(self, job_id: str) -> SpeechJob | None:
        return self._jobs.get(job_id)

    def update(self, job: SpeechJob) -> SpeechJob:
        self._jobs[str(job.id)] = job
        return job


class FakeAsrService:
    def transcribe(self, audio_bytes: bytes) -> str:
        return "raw transcript"


class FakeAudioProcessor:
    def normalize(self, audio_bytes: bytes) -> bytes:
        return b"normalized"


class FakeTranscriptTransformer:
    def transform(self, transcript: str) -> str:
        return "transformed transcript"


class FakeTtsService:
    def synthesize(self, text: str) -> bytes:
        return b"output audio"


class FakeObjectStorage:
    def __init__(self) -> None:
        self._objects: dict[str, bytes] = {"input/file.wav": b"input audio"}

    def get_object(self, key: str) -> bytes:
        if key not in self._objects:
            raise FileNotFoundError(f"Object '{key}' was not found")
        return self._objects[key]

    def put_object(self, key: str, data: bytes) -> str:
        self._objects[key] = data
        return key


class FakeFailingObjectStorage(FakeObjectStorage):
    def put_object(self, key: str, data: bytes) -> str:
        raise RuntimeError("unable to store output")


def _build_app(storage: FakeObjectStorage) -> FastAPI:
    repository = InMemorySpeechJobRepository()
    create_speech_job = CreateSpeechJob(
        repository=repository,
        asr=FakeAsrService(),
        tts=FakeTtsService(),
        storage=storage,
        transformer=FakeTranscriptTransformer(),
        audio_processor=FakeAudioProcessor(),
    )
    container = AppContainer(
        create_speech_job=create_speech_job,
        get_speech_job=GetSpeechJob(repository=repository),
        get_output_audio=GetOutputAudio(repository=repository, storage=storage),
    )

    app = FastAPI()
    app.state.container = container
    v1_router = APIRouter(prefix="/v1")
    v1_router.include_router(speech_jobs.router, prefix="/speech-jobs", tags=["Speech Jobs"])
    app.include_router(v1_router)
    return app


def test_create_job_returns_202_and_completes_when_polled() -> None:
    app = _build_app(FakeObjectStorage())

    with TestClient(app) as client:
        create_response = client.post("/v1/speech-jobs", json={"input_audio_key": "input/file.wav"})
        assert create_response.status_code == 202
        assert create_response.json()["status"] == SpeechJobStatus.PENDING.value
        assert create_response.json()["stage"] == SpeechJobStage.QUEUED.value

        job_id = create_response.json()["id"]
        poll_response = client.get(f"/v1/speech-jobs/{job_id}")
        assert poll_response.status_code == 200
        assert poll_response.json()["status"] == SpeechJobStatus.COMPLETED.value
        assert poll_response.json()["stage"] == SpeechJobStage.COMPLETED.value

        output_response = client.get(f"/v1/speech-jobs/{job_id}/output-audio")
        assert output_response.status_code == 200
        assert output_response.content == b"output audio"


def test_create_job_returns_202_and_fails_when_polled() -> None:
    app = _build_app(FakeFailingObjectStorage())

    with TestClient(app) as client:
        create_response = client.post("/v1/speech-jobs", json={"input_audio_key": "input/file.wav"})
        assert create_response.status_code == 202
        assert create_response.json()["status"] == SpeechJobStatus.PENDING.value
        assert create_response.json()["stage"] == SpeechJobStage.QUEUED.value

        job_id = create_response.json()["id"]
        poll_response = client.get(f"/v1/speech-jobs/{job_id}")
        assert poll_response.status_code == 200
        assert poll_response.json()["status"] == SpeechJobStatus.FAILED.value
        assert poll_response.json()["stage"] == SpeechJobStage.FAILED.value
        assert "unable to store output" in poll_response.json()["error_message"]

        output_response = client.get(f"/v1/speech-jobs/{job_id}/output-audio")
        assert output_response.status_code == 409
