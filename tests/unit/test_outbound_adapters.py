import subprocess
from pathlib import Path

import pytest

from src.adapters.outbound.audio.ffmpeg_audio_processor import FfmpegAudioProcessor
from src.adapters.outbound.exceptions import AudioProcessingError, AsrTranscriptionError, TtsSynthesisError
from src.adapters.outbound.speech.piper_tts import PiperTts
from src.adapters.outbound.speech.whisper_asr import WhisperAsr


def test_ffmpeg_audio_processor_normalize_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        output_path = Path(command[-1])
        output_path.write_bytes(b"normalized")
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("src.adapters.outbound.audio.ffmpeg_audio_processor.subprocess.run", fake_run)

    processor = FfmpegAudioProcessor(ffmpeg_command="ffmpeg", timeout_seconds=1)
    assert processor.normalize(b"input") == b"normalized"


def test_ffmpeg_audio_processor_timeout_maps_to_audio_processing_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=command, timeout=1)

    monkeypatch.setattr("src.adapters.outbound.audio.ffmpeg_audio_processor.subprocess.run", fake_run)

    processor = FfmpegAudioProcessor(ffmpeg_command="ffmpeg", timeout_seconds=1)
    with pytest.raises(AudioProcessingError, match="timed out"):
        processor.normalize(b"input")


def test_whisper_asr_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        output_prefix = Path(command[command.index("-of") + 1])
        transcript_path = output_prefix.with_suffix(".txt")
        transcript_path.write_text("hello world", encoding="utf-8")
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("src.adapters.outbound.speech.whisper_asr.subprocess.run", fake_run)

    adapter = WhisperAsr(command="whisper-cli", model_path="model.bin", timeout_seconds=1)
    assert adapter.transcribe(b"input") == "hello world"


def test_whisper_asr_called_process_error_maps_to_asr_transcription_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(returncode=1, cmd=command, stderr="bad asr")

    monkeypatch.setattr("src.adapters.outbound.speech.whisper_asr.subprocess.run", fake_run)

    adapter = WhisperAsr(command="whisper-cli", model_path="model.bin", timeout_seconds=1)
    with pytest.raises(AsrTranscriptionError, match="bad asr"):
        adapter.transcribe(b"input")


def test_piper_tts_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        output_path = Path(command[command.index("--output_file") + 1])
        output_path.write_bytes(b"wav-bytes")
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("src.adapters.outbound.speech.piper_tts.subprocess.run", fake_run)

    adapter = PiperTts(command="piper", model_path="voice.onnx", timeout_seconds=1)
    assert adapter.synthesize("hello") == b"wav-bytes"


def test_piper_tts_timeout_maps_to_tts_synthesis_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=command, timeout=1)

    monkeypatch.setattr("src.adapters.outbound.speech.piper_tts.subprocess.run", fake_run)

    adapter = PiperTts(command="piper", model_path="voice.onnx", timeout_seconds=1)
    with pytest.raises(TtsSynthesisError, match="timed out"):
        adapter.synthesize("hello")


def test_piper_tts_uses_selected_voice_model(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_command: list[str] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured_command.extend(command)
        output_path = Path(command[command.index("--output_file") + 1])
        output_path.write_bytes(b"wav-bytes")
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("src.adapters.outbound.speech.piper_tts.subprocess.run", fake_run)

    adapter = PiperTts(
        command="piper",
        model_path="default.onnx",
        config_path="default.json",
        voice_models={"narrator": "narrator.onnx"},
        voice_configs={"narrator": "narrator.json"},
        timeout_seconds=1,
    )

    assert adapter.synthesize("hello", voice="narrator") == b"wav-bytes"
    assert captured_command[captured_command.index("--model") + 1] == "narrator.onnx"
    assert captured_command[captured_command.index("--config") + 1] == "narrator.json"


def test_piper_tts_unknown_voice_raises_error() -> None:
    adapter = PiperTts(command="piper", model_path="voice.onnx", timeout_seconds=1)

    with pytest.raises(TtsSynthesisError, match="Unknown TTS voice"):
        adapter.synthesize("hello", voice="narrator")
