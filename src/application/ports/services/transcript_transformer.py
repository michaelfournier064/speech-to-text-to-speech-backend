from typing import Protocol


class TranscriptTransformer(Protocol):
    def transform(self, transcript: str) -> str:
        ...
