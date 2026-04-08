class AdapterError(Exception):
    """Base exception for outbound adapter failures."""


class AudioProcessingError(AdapterError):
    """Raised when audio normalization fails."""


class AsrTranscriptionError(AdapterError):
    """Raised when ASR transcription fails."""


class TtsSynthesisError(AdapterError):
    """Raised when TTS synthesis fails."""
