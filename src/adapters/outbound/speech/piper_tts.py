import subprocess
import tempfile
from pathlib import Path

from src.adapters.outbound.exceptions import TtsSynthesisError


class PiperTts:
    def __init__(
        self,
        command: str = "piper",
        model_path: str = "models/en_US-lessac-medium.onnx",
        config_path: str | None = None,
        voice_models: dict[str, str] | None = None,
        voice_configs: dict[str, str | None] | None = None,
        timeout_seconds: int = 60,
    ) -> None:
        self._command = command
        self._model_path = model_path
        self._config_path = config_path
        self._voice_models = voice_models or {}
        self._voice_configs = voice_configs or {}
        self._timeout_seconds = timeout_seconds

    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        input_text = text.strip()
        if not input_text:
            raise TtsSynthesisError("Cannot synthesize empty text")

        model_path = self._model_path
        config_path = self._config_path
        if voice is not None:
            if voice not in self._voice_models:
                available = ", ".join(sorted(self._voice_models.keys()))
                detail = f" Available voices: {available}" if available else ""
                raise TtsSynthesisError(f"Unknown TTS voice '{voice}'.{detail}")
            model_path = self._voice_models[voice]
            config_path = self._voice_configs.get(voice, config_path)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.wav"

            command = [
                self._command,
                "--model",
                model_path,
                "--output_file",
                str(output_path),
            ]
            if config_path:
                command.extend(["--config", config_path])

            try:
                subprocess.run(
                    command,
                    input=input_text,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=self._timeout_seconds,
                )
            except FileNotFoundError as exc:
                raise TtsSynthesisError(
                    f"TTS command '{self._command}' was not found"
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise TtsSynthesisError(
                    f"TTS synthesis timed out after {self._timeout_seconds}s"
                ) from exc
            except subprocess.CalledProcessError as exc:
                stderr = (exc.stderr or "").strip()
                message = stderr or "TTS synthesis command failed"
                raise TtsSynthesisError(message) from exc

            if not output_path.exists():
                raise TtsSynthesisError("TTS command produced no audio output")
            output_audio = output_path.read_bytes()
            if not output_audio:
                raise TtsSynthesisError("TTS command produced empty audio")
            return output_audio
