from src.application.ports.repositories.speech_job_repository import SpeechJobRepository
from src.application.ports.services.asr_service import AsrService
from src.application.ports.services.audio_processor import AudioProcessor
from src.application.ports.services.object_storage import ObjectStorage
from src.application.ports.services.transcript_transformer import TranscriptTransformer
from src.application.ports.services.tts_service import TtsService
from src.domain.speech_job.entities import SpeechJob
from src.domain.speech_job.enums import SpeechJobStatus
from src.domain.speech_job.value_objects import ObjectKey, SpeechJobId


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

    def execute(self, input_audio_key: str) -> SpeechJob:
        job = SpeechJob(
            id=SpeechJobId.new(),
            status=SpeechJobStatus.PENDING,
            input_audio_key=ObjectKey(input_audio_key),
        )
        self._repository.add(job)

        try:
            job.mark_processing()
            self._repository.update(job)

            input_audio = self._storage.get_object(input_audio_key)
            normalized_audio = self._audio_processor.normalize(input_audio)
            raw_transcript = self._asr.transcribe(normalized_audio)
            transcript = self._transformer.transform(raw_transcript)
            output_audio = self._tts.synthesize(transcript)

            output_key = f"speech-jobs/{job.id}.wav"
            stored_key = self._storage.put_object(output_key, output_audio)
            job.mark_completed(transcript=transcript, output_audio_key=ObjectKey(stored_key))
            return self._repository.update(job)
        except Exception as exc:
            job.mark_failed(str(exc))
            self._repository.update(job)
            raise
