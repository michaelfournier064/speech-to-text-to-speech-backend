from fastapi import APIRouter

from src.adapters.inbound.api.schemas.responses import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")
