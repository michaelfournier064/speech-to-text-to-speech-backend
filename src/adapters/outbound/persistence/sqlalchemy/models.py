from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.outbound.persistence.sqlalchemy.base import Base


class SpeechJobModel(Base):
    __tablename__ = "speech_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    input_audio_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    output_audio_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
