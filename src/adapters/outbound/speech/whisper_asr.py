class WhisperAsr:
    def transcribe(self, audio_bytes: bytes) -> str:
        if not audio_bytes:
            return ""
        return f"Transcribed {len(audio_bytes)} bytes of audio"
