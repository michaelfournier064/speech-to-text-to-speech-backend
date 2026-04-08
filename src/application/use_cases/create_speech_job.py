import logging
from datetime import datetime, timezone
from pathlib import Path
import re

from src.application.ports.repositories.speech_job_repository import SpeechJobRepository
from src.application.ports.services.asr_service import AsrService
from src.application.ports.services.audio_processor import AudioProcessor
from src.application.ports.services.object_storage import ObjectStorage
from src.application.ports.services.transcript_transformer import TranscriptTransformer
from src.application.ports.services.tts_service import TtsService
from src.domain.speech_job.entities import SpeechJob
from src.domain.speech_job.enums import SpeechJobStage, SpeechJobStatus
from src.domain.speech_job.value_objects import ObjectKey, SpeechJobId

logger = logging.getLogger(__name__)


class CreateSpeechJob:
    def __init__(
        self,
        repository: SpeechJobRepository,
        asr: AsrService,
        tts: TtsService,
        storage: ObjectStorage,
        transformer: TranscriptTransformer,
        audio_processor: AudioProcessor,
    ) -> None:
        self._repository = repository
        self._asr = asr
        self._tts = tts
        self._storage = storage
        self._transformer = transformer
        self._audio_processor = audio_processor

    def _build_input_object_key(self, job_id: str, original_filename: str | None) -> str:
        suffix = ".bin"
        if original_filename:
            candidate_suffix = Path(original_filename).suffix.lower()
            if re.fullmatch(r"\.[a-z0-9]{1,10}", candidate_suffix):
                suffix = candidate_suffix

        return f"speech-jobs/{job_id}/input{suffix}"

    def _build_output_object_key(self, input_audio_key: str, voice: str | None) -> str:
        input_path = Path(input_audio_key)
        safe_voice = re.sub(r"[^a-zA-Z0-9_-]+", "_", (voice or "default").strip())
        safe_voice = safe_voice.strip("_") or "default"
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_filename = f"{safe_voice}_output_{timestamp}.wav"
        return input_path.with_name(output_filename).as_posix()

    def execute(self, input_audio_data: bytes, original_filename: str | None = None) -> SpeechJob:
        """Store input audio and persist a queued speech job."""

        if not input_audio_data:
            raise ValueError("Input audio file is empty")

        job_id = SpeechJobId.new()
        input_object_key = self._build_input_object_key(str(job_id), original_filename)
        stored_input_key = self._storage.put_object(input_object_key, input_audio_data)

        job = SpeechJob(
            id=job_id,
            status=SpeechJobStatus.PENDING,
            stage=SpeechJobStage.QUEUED,
            input_audio_key=ObjectKey(stored_input_key),
        )
        queued_job = self._repository.add(job)
        logger.info(
            "speech_job_enqueued job_id=%s input_audio_key=%s",
            queued_job.id,
            queued_job.input_audio_key,
        )
        return queued_job

    def process(self, job_id: str, voice: str | None = None) -> SpeechJob:
        """Process a queued speech job and persist stage transitions."""

        logger.info("speech_job_processing_started job_id=%s voice=%s", job_id, voice)
        job = self._repository.get_by_id(job_id)
        if job is None:
            logger.warning("speech_job_processing_missing_job job_id=%s", job_id)
            raise ValueError(f"Speech job '{job_id}' was not found")

        try:
            job.mark_processing()
            job.mark_staged(SpeechJobStage.FETCHING_INPUT_AUDIO)
            self._repository.update(job)

            input_audio = self._storage.get_object(str(job.input_audio_key))

            job.mark_staged(SpeechJobStage.NORMALIZING_AUDIO)
            self._repository.update(job)
            normalized_audio = self._audio_processor.normalize(input_audio)

            job.mark_staged(SpeechJobStage.TRANSCRIBING_AUDIO)
            self._repository.update(job)
            raw_transcript = self._asr.transcribe(normalized_audio)

            job.mark_staged(SpeechJobStage.TRANSFORMING_TRANSCRIPT)
            self._repository.update(job)
            transcript = self._transformer.transform(raw_transcript)

            job.mark_staged(SpeechJobStage.SYNTHESIZING_AUDIO)
            self._repository.update(job)
            output_audio = self._tts.synthesize(transcript, voice=voice)

            job.mark_staged(SpeechJobStage.STORING_OUTPUT_AUDIO)
            self._repository.update(job)
            output_key = self._build_output_object_key(str(job.input_audio_key), voice)
            stored_key = self._storage.put_object(output_key, output_audio)
            job.mark_completed(transcript=transcript, output_audio_key=ObjectKey(stored_key))
            completed_job = self._repository.update(job)
            logger.info("speech_job_processing_completed job_id=%s", completed_job.id)
            return completed_job
        except Exception as exc:
            job.mark_failed(str(exc))
            failed_job = self._repository.update(job)
            logger.exception("speech_job_processing_failed job_id=%s", failed_job.id)
            return failed_job
