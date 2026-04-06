class PiperTts:
    def synthesize(self, text: str) -> bytes:
        return text.encode("utf-8")
