from typing import Protocol

from src.domain.speech_job.entities import SpeechJob


class SpeechJobRepository(Protocol):
    def add(self, job: SpeechJob) -> SpeechJob:
        ...

    def get_by_id(self, job_id: str) -> SpeechJob | None:
        ...

    def update(self, job: SpeechJob) -> SpeechJob:
        ...
