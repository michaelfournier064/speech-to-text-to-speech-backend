class BasicTranscriptTransformer:
    def transform(self, transcript: str) -> str:
        return " ".join(transcript.strip().split())
