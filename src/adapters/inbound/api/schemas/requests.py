from pydantic import BaseModel, Field


class CreateSpeechJobRequest(BaseModel):
    input_audio_key: str = Field(min_length=1)
    voice: str | None = Field(default=None, min_length=1)
