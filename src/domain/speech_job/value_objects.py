from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SpeechJobId:
    value: UUID

    @staticmethod
    def new() -> "SpeechJobId":
        return SpeechJobId(value=uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ObjectKey:
    value: str

    def __str__(self) -> str:
        return self.value
