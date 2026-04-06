from typing import Protocol


class AudioProcessor(Protocol):
    def normalize(self, audio_bytes: bytes) -> bytes:
        ...
