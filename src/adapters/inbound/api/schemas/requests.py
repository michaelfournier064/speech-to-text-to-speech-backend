from pydantic import BaseModel, Field


class CreateSpeechJobRequest(BaseModel):
    input_audio_key: str = Field(min_length=1)
