from collections.abc import Mapping, Sequence
import logging
from time import perf_counter
from typing import Any

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.adapters.inbound.api.routes import health, speech_jobs
from src.bootstrap.config import Settings
from src.bootstrap.containers import build_container

logger = logging.getLogger("speech_to_text_to_speech.request")


def configure_logging() -> None:
	root_logger = logging.getLogger()
	if not root_logger.handlers:
		logging.basicConfig(
			level=logging.INFO,
			format="%(asctime)s %(levelname)s %(name)s %(message)s",
		)


def configure_request_logging(app: FastAPI) -> None:
	@app.middleware("http")
	async def log_requests(request: Request, call_next: Any) -> Any:
		start_time = perf_counter()
		client_host = request.client.host if request.client else "unknown"

		try:
			response = await call_next(request)
		except Exception:
			duration_ms = (perf_counter() - start_time) * 1000
			logging.getLogger("uvicorn.error").exception(
				"request_failed method=%s path=%s client=%s duration_ms=%.2f",
				request.method,
				request.url.path,
				client_host,
				duration_ms,
			)
			raise

		duration_ms = (perf_counter() - start_time) * 1000
		logger.info(
			"request method=%s path=%s status=%s client=%s duration_ms=%.2f",
			request.method,
			request.url.path,
			response.status_code,
			client_host,
			duration_ms,
		)
		return response


def configure_cors(app: FastAPI, origins: list[str]) -> None:
	app.add_middleware(
		CORSMiddleware,
		allow_origins=origins,
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)


def _sanitize_validation_value(value: Any) -> Any:
	if isinstance(value, BaseException):
		return str(value)
	if isinstance(value, bytes):
		return f"<{len(value)} bytes>"
	if isinstance(value, str) and len(value) > 512:
		return value[:512] + "...<truncated>"
	if isinstance(value, Mapping):
		return {key: _sanitize_validation_value(item) for key, item in value.items()}
	if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
		return [_sanitize_validation_value(item) for item in value]
	if value is None or isinstance(value, (bool, int, float, str)):
		return value
	return str(value)


def configure_exception_handlers(app: FastAPI) -> None:
	@app.exception_handler(RequestValidationError)
	async def validation_exception_handler(
		request: Request,
		exc: RequestValidationError,
	) -> JSONResponse:
		_ = request
		detail = _sanitize_validation_value(exc.errors())
		return JSONResponse(status_code=422, content={"detail": detail})

settings = Settings()

app = FastAPI(title="Speech-to-speech-backend", version="1.0.0")
configure_logging()
configure_cors(app, settings.get_cors_origins())
app.state.container = build_container(settings)
configure_exception_handlers(app)
configure_request_logging(app)

app.include_router(health.router, prefix="/health", tags=["Health"])

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(speech_jobs.router, prefix="/speech-jobs", tags=["Speech Jobs"])

app.include_router(v1_router)
