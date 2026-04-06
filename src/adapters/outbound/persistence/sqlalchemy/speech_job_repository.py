from uuid import UUID

from src.adapters.outbound.persistence.sqlalchemy.models import SpeechJobModel
from src.adapters.outbound.persistence.sqlalchemy.session import InMemorySession
from src.domain.speech_job.entities import SpeechJob
from src.domain.speech_job.enums import SpeechJobStage, SpeechJobStatus
from src.domain.speech_job.value_objects import ObjectKey, SpeechJobId


class SqlAlchemySpeechJobRepository:
    def __init__(self, session: InMemorySession) -> None:
        self._session = session

    def add(self, job: SpeechJob) -> SpeechJob:
        model = self._to_model(job)
        self._session.speech_jobs[model.id] = model
        return self._to_domain(model)

    def get_by_id(self, job_id: str) -> SpeechJob | None:
        model = self._session.speech_jobs.get(job_id)
        return self._to_domain(model) if model else None

    def update(self, job: SpeechJob) -> SpeechJob:
        model = self._to_model(job)
        self._session.speech_jobs[model.id] = model
        return self._to_domain(model)

    @staticmethod
    def _to_model(job: SpeechJob) -> SpeechJobModel:
        return SpeechJobModel(
            id=str(job.id),
            status=job.status.value,
            stage=job.stage.value,
            input_audio_key=str(job.input_audio_key),
            output_audio_key=str(job.output_audio_key) if job.output_audio_key else None,
            transcript=job.transcript,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    @staticmethod
    def _to_domain(model: SpeechJobModel) -> SpeechJob:
        return SpeechJob(
            id=SpeechJobId(value=UUID(model.id)),
            status=SpeechJobStatus(model.status),
            stage=SpeechJobStage(model.stage),
            input_audio_key=ObjectKey(model.input_audio_key),
            output_audio_key=ObjectKey(model.output_audio_key) if model.output_audio_key else None,
            transcript=model.transcript,
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
