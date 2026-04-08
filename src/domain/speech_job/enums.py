from enum import Enum


class SpeechJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SpeechJobStage(str, Enum):
    QUEUED = "queued"
    FETCHING_INPUT_AUDIO = "fetching_input_audio"
    NORMALIZING_AUDIO = "normalizing_audio"
    TRANSCRIBING_AUDIO = "transcribing_audio"
    TRANSFORMING_TRANSCRIPT = "transforming_transcript"
    SYNTHESIZING_AUDIO = "synthesizing_audio"
    STORING_OUTPUT_AUDIO = "storing_output_audio"
    COMPLETED = "completed"
    FAILED = "failed"
