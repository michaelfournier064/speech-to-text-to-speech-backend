from datetime import datetime

from pydantic import BaseModel

from src.domain.speech_job.enums import SpeechJobStage, SpeechJobStatus


class SpeechJobResponse(BaseModel):
    id: str
    status: SpeechJobStatus
    stage: SpeechJobStage
    input_audio_key: str
    output_audio_key: str | None
    transcript: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str
