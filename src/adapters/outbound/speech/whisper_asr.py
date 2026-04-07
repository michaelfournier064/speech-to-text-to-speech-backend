import subprocess
import tempfile
from pathlib import Path

from src.adapters.outbound.exceptions import AsrTranscriptionError


class WhisperAsr:
    def __init__(
        self,
        command: str = "whisper-cli",
        model_path: str = "models/ggml-base.en.bin",
        language: str = "en",
        timeout_seconds: int = 120,
    ) -> None:
        self._command = command
        self._model_path = model_path
        self._language = language
        self._timeout_seconds = timeout_seconds

    def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            raise AsrTranscriptionError("Cannot transcribe empty audio payload")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "input.wav"
            output_prefix = temp_path / "transcript"
            transcript_path = temp_path / "transcript.txt"
            input_path.write_bytes(audio_bytes)

            command = [
                self._command,
                "-m",
                self._model_path,
                "-f",
                str(input_path),
                "-l",
                self._language,
                "-otxt",
                "-of",
                str(output_prefix),
            ]

            try:
                subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=self._timeout_seconds,
                )
            except FileNotFoundError as exc:
                raise AsrTranscriptionError(
                    f"ASR command '{self._command}' was not found"
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise AsrTranscriptionError(
                    f"ASR transcription timed out after {self._timeout_seconds}s"
                ) from exc
            except subprocess.CalledProcessError as exc:
                stderr = (exc.stderr or "").strip()
                message = stderr or "ASR transcription command failed"
                raise AsrTranscriptionError(message) from exc

            if not transcript_path.exists():
                raise AsrTranscriptionError("ASR command produced no transcript output")

            transcript = transcript_path.read_text(encoding="utf-8").strip()
            if not transcript:
                raise AsrTranscriptionError("ASR command produced an empty transcript")
            return transcript
