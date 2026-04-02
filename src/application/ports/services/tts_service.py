from typing import Protocol


class TtsService(Protocol):
    def synthesize(self, text: str) -> bytes:
        ...
