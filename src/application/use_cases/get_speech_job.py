from src.application.ports.repositories.speech_job_repository import SpeechJobRepository
from src.domain.speech_job.entities import SpeechJob


class SpeechJobNotFoundError(Exception):
    pass


class GetSpeechJob:
    def __init__(self, repository: SpeechJobRepository) -> None:
        self._repository = repository

    def execute(self, job_id: str) -> SpeechJob:
        job = self._repository.get_by_id(job_id)
        if job is None:
            raise SpeechJobNotFoundError(f"Speech job '{job_id}' was not found")
        return job
