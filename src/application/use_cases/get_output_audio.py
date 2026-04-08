from pathlib import Path

from src.application.ports.repositories.speech_job_repository import SpeechJobRepository
from src.application.ports.services.object_storage import ObjectStorage
from src.domain.speech_job.enums import SpeechJobStatus


class OutputAudioNotReadyError(Exception):
    pass


class GetOutputAudio:
    def __init__(self, repository: SpeechJobRepository, storage: ObjectStorage) -> None:
        self._repository = repository
        self._storage = storage

    def execute(self, job_id: str) -> tuple[bytes, str]:
        job = self._repository.get_by_id(job_id)
        if job is None:
            raise ValueError(f"Speech job '{job_id}' was not found")

        if job.status != SpeechJobStatus.COMPLETED or job.output_audio_key is None:
            raise OutputAudioNotReadyError(f"Output audio is not ready for job '{job_id}'")

        output_audio_key = str(job.output_audio_key)
        output_audio = self._storage.get_object(output_audio_key)
        filename = Path(output_audio_key).name or "output.wav"
        return output_audio, filename
