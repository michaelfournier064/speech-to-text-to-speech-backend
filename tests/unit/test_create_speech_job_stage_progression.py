from src.application.use_cases.create_speech_job import CreateSpeechJob
from src.domain.speech_job.entities import SpeechJob
from src.domain.speech_job.enums import SpeechJobStage, SpeechJobStatus
import re


class RecordingSpeechJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, SpeechJob] = {}
        self.history: list[tuple[SpeechJobStatus, SpeechJobStage]] = []

    def add(self, job: SpeechJob) -> SpeechJob:
        self._jobs[str(job.id)] = job
        self.history.append((job.status, job.stage))
        return job

    def get_by_id(self, job_id: str) -> SpeechJob | None:
        return self._jobs.get(job_id)

    def update(self, job: SpeechJob) -> SpeechJob:
        self._jobs[str(job.id)] = job
        self.history.append((job.status, job.stage))
        return job


class FakeAsrService:
    def transcribe(self, audio_bytes: bytes) -> str:
        return "raw transcript"


class FakeAudioProcessor:
    def normalize(self, audio_bytes: bytes) -> bytes:
        return b"normalized"


class FakeObjectStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def get_object(self, key: str) -> bytes:
        return self.objects[key]

    def put_object(self, key: str, data: bytes) -> str:
        self.objects[key] = data
        return key


class FakeFailingObjectStorage(FakeObjectStorage):
    def put_object(self, key: str, data: bytes) -> str:
        if "/input." in key:
            return super().put_object(key, data)
        raise RuntimeError("unable to store output")


class FakeTranscriptTransformer:
    def transform(self, transcript: str) -> str:
        return "transformed transcript"


class FakeTtsService:
    def __init__(self) -> None:
        self.last_voice: str | None = None

    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        self.last_voice = voice
        return b"audio"


def test_create_speech_job_starts_queued() -> None:
    repository = RecordingSpeechJobRepository()
    use_case = CreateSpeechJob(
        repository=repository,
        asr=FakeAsrService(),
        tts=FakeTtsService(),
        storage=FakeObjectStorage(),
        transformer=FakeTranscriptTransformer(),
        audio_processor=FakeAudioProcessor(),
    )

    job = use_case.execute(b"input", original_filename="input.wav")

    assert job.status is SpeechJobStatus.PENDING
    assert job.stage is SpeechJobStage.QUEUED
    assert repository.history == [
        (SpeechJobStatus.PENDING, SpeechJobStage.QUEUED),
    ]


def test_create_speech_job_tracks_stage_progression_on_success() -> None:
    repository = RecordingSpeechJobRepository()
    use_case = CreateSpeechJob(
        repository=repository,
        asr=FakeAsrService(),
        tts=FakeTtsService(),
        storage=FakeObjectStorage(),
        transformer=FakeTranscriptTransformer(),
        audio_processor=FakeAudioProcessor(),
    )

    queued_job = use_case.execute(b"input", original_filename="input.wav")
    job = use_case.process(str(queued_job.id))

    assert job.status is SpeechJobStatus.COMPLETED
    assert job.stage is SpeechJobStage.COMPLETED

    assert repository.history == [
        (SpeechJobStatus.PENDING, SpeechJobStage.QUEUED),
        (SpeechJobStatus.PROCESSING, SpeechJobStage.FETCHING_INPUT_AUDIO),
        (SpeechJobStatus.PROCESSING, SpeechJobStage.NORMALIZING_AUDIO),
        (SpeechJobStatus.PROCESSING, SpeechJobStage.TRANSCRIBING_AUDIO),
        (SpeechJobStatus.PROCESSING, SpeechJobStage.TRANSFORMING_TRANSCRIPT),
        (SpeechJobStatus.PROCESSING, SpeechJobStage.SYNTHESIZING_AUDIO),
        (SpeechJobStatus.PROCESSING, SpeechJobStage.STORING_OUTPUT_AUDIO),
        (SpeechJobStatus.COMPLETED, SpeechJobStage.COMPLETED),
    ]


def test_create_speech_job_tracks_failed_stage_on_error() -> None:
    repository = RecordingSpeechJobRepository()
    use_case = CreateSpeechJob(
        repository=repository,
        asr=FakeAsrService(),
        tts=FakeTtsService(),
        storage=FakeFailingObjectStorage(),
        transformer=FakeTranscriptTransformer(),
        audio_processor=FakeAudioProcessor(),
    )

    queued_job = use_case.execute(b"input", original_filename="input.wav")
    failed_job = use_case.process(str(queued_job.id))

    final_status, final_stage = repository.history[-1]
    assert final_status is SpeechJobStatus.FAILED
    assert final_stage is SpeechJobStage.FAILED
    assert failed_job.error_message == "unable to store output"


def test_create_speech_job_passes_requested_voice_to_tts() -> None:
    repository = RecordingSpeechJobRepository()
    tts = FakeTtsService()
    use_case = CreateSpeechJob(
        repository=repository,
        asr=FakeAsrService(),
        tts=tts,
        storage=FakeObjectStorage(),
        transformer=FakeTranscriptTransformer(),
        audio_processor=FakeAudioProcessor(),
    )

    queued_job = use_case.execute(b"input", original_filename="input.wav")
    use_case.process(str(queued_job.id), voice="narrator")

    assert tts.last_voice == "narrator"


def test_create_speech_job_names_output_with_voice_and_datetime() -> None:
    repository = RecordingSpeechJobRepository()
    tts = FakeTtsService()
    storage = FakeObjectStorage()
    use_case = CreateSpeechJob(
        repository=repository,
        asr=FakeAsrService(),
        tts=tts,
        storage=storage,
        transformer=FakeTranscriptTransformer(),
        audio_processor=FakeAudioProcessor(),
    )

    queued_job = use_case.execute(b"input", original_filename="input.m4a")
    use_case.process(str(queued_job.id), voice="amy")

    output_keys = [key for key in storage.objects.keys() if key.endswith(".wav")]
    assert output_keys
    expected_prefix = f"speech-jobs/{queued_job.id}/amy_output_"
    assert output_keys[0].startswith(expected_prefix)
    assert re.fullmatch(r"speech-jobs/.+/amy_output_\d{8}T\d{6}Z\.wav", output_keys[0])
