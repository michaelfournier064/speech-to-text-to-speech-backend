from fastapi import APIRouter, FastAPI

from src.adapters.inbound.api.routes import health, speech_jobs
from src.bootstrap.containers import build_container

app = FastAPI(title="Speech-to-speech-backend", version="1.0.0")
app.state.container = build_container()

app.include_router(health.router, prefix="/health", tags=["Health"])

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(speech_jobs.router, prefix="/speech-jobs", tags=["Speech Jobs"])

app.include_router(v1_router)
