from fastapi import FastAPI, APIRouter
from internal.app.api.routes import health
from internal.app.api.routes.v1 import sessions, speech_to_speech

app = FastAPI(title="Speech-to-text-backend", version="1.0.0")

# Health is not versioned
app.include_router(health.router, prefix="/health", tags=["Health"])

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
v1_router.include_router(speech_to_speech.router, prefix="/speech-to-speech", tags=["Speech-to-Speech"])

app.include_router(v1_router)
