import subprocess
import tempfile
from pathlib import Path

from src.adapters.outbound.exceptions import AudioProcessingError


class FfmpegAudioProcessor:
    def __init__(self, ffmpeg_command: str = "ffmpeg", timeout_seconds: int = 30) -> None:
        self._ffmpeg_command = ffmpeg_command
        self._timeout_seconds = timeout_seconds

    def normalize(self, audio_bytes: bytes) -> bytes:
        if not audio_bytes:
            raise AudioProcessingError("Cannot normalize empty audio payload")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "input.wav"
            output_path = temp_path / "output.wav"
            input_path.write_bytes(audio_bytes)

            command = [
                self._ffmpeg_command,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(input_path),
                "-ac",
                "1",
                "-ar",
                "16000",
                "-f",
                "wav",
                str(output_path),
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
                raise AudioProcessingError(
                    f"Audio processor command '{self._ffmpeg_command}' was not found"
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise AudioProcessingError(
                    f"Audio normalization timed out after {self._timeout_seconds}s"
                ) from exc
            except subprocess.CalledProcessError as exc:
                stderr = (exc.stderr or "").strip()
                message = stderr or "Audio normalization command failed"
                raise AudioProcessingError(message) from exc

            if not output_path.exists():
                raise AudioProcessingError("Audio normalization produced no output")

            return output_path.read_bytes()
