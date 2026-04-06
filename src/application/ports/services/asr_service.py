from typing import Protocol


class AsrService(Protocol):
    def transcribe(self, audio_bytes: bytes) -> str:
        ...
