import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response

from src.adapters.inbound.api.deps import get_container
from src.adapters.inbound.api.schemas.requests import CreateSpeechJobRequest
from src.adapters.inbound.api.schemas.responses import SpeechJobResponse
from src.application.use_cases.get_output_audio import OutputAudioNotReadyError
from src.application.use_cases.get_speech_job import SpeechJobNotFoundError
from src.bootstrap.containers import AppContainer
from src.domain.speech_job.entities import SpeechJob

router = APIRouter()
logger = logging.getLogger(__name__)


def _to_response(job: SpeechJob) -> SpeechJobResponse:
    return SpeechJobResponse(
        id=str(job.id),
        status=job.status,
        stage=job.stage,
        input_audio_key=str(job.input_audio_key),
        output_audio_key=str(job.output_audio_key) if job.output_audio_key else None,
        transcript=job.transcript,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("", response_model=SpeechJobResponse, status_code=202)
def create_speech_job(
    payload: CreateSpeechJobRequest,
    background_tasks: BackgroundTasks,
    container: AppContainer = Depends(get_container),
) -> SpeechJobResponse:
    try:
        job = container.create_speech_job.execute(payload.input_audio_key)
        background_tasks.add_task(container.create_speech_job.process, str(job.id), payload.voice)
        logger.info("speech_job_processing_scheduled job_id=%s voice=%s", job.id, payload.voice)
        return _to_response(job)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{job_id}", response_model=SpeechJobResponse)
def get_speech_job(
    job_id: str,
    container: AppContainer = Depends(get_container),
) -> SpeechJobResponse:
    try:
        job = container.get_speech_job.execute(job_id)
        return _to_response(job)
    except SpeechJobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{job_id}/output-audio")
def get_output_audio(
    job_id: str,
    container: AppContainer = Depends(get_container),
) -> Response:
    try:
        audio_bytes = container.get_output_audio.execute(job_id)
        return Response(content=audio_bytes, media_type="audio/wav")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OutputAudioNotReadyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
