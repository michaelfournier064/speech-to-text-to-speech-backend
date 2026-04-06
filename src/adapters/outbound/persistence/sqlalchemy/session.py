from src.adapters.outbound.persistence.sqlalchemy.models import SpeechJobModel


class InMemorySession:
    def __init__(self) -> None:
        self.speech_jobs: dict[str, SpeechJobModel] = {}
