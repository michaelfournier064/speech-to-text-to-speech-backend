from dataclasses import dataclass, field
from datetime import datetime, UTC

from src.domain.speech_job.enums import SpeechJobStage, SpeechJobStatus
from src.domain.speech_job.value_objects import ObjectKey, SpeechJobId


@dataclass
class SpeechJob:
    id: SpeechJobId
    status: SpeechJobStatus
    stage: SpeechJobStage
    input_audio_key: ObjectKey
    output_audio_key: ObjectKey | None = None
    transcript: str | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def mark_processing(self) -> None:
        self.status = SpeechJobStatus.PROCESSING
        self.updated_at = datetime.now(UTC)

    def mark_staged(self, stage: SpeechJobStage) -> None:
        self.stage = stage
        self.updated_at = datetime.now(UTC)

    def mark_completed(self, transcript: str, output_audio_key: ObjectKey) -> None:
        self.status = SpeechJobStatus.COMPLETED
        self.stage = SpeechJobStage.COMPLETED
        self.transcript = transcript
        self.output_audio_key = output_audio_key
        self.error_message = None
        self.updated_at = datetime.now(UTC)

    def mark_failed(self, error_message: str) -> None:
        self.status = SpeechJobStatus.FAILED
        self.stage = SpeechJobStage.FAILED
        self.error_message = error_message
        self.updated_at = datetime.now(UTC)
