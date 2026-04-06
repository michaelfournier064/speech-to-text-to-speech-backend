from dataclasses import dataclass
from datetime import datetime


@dataclass
class SpeechJobModel:
    id: str
    status: str
    input_audio_key: str
    output_audio_key: str | None
    transcript: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
