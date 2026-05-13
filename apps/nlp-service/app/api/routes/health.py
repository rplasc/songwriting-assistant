from fastapi import APIRouter

from app.schemas.responses import HealthResponse

router = APIRouter()


@router.get("/healthz", response_model=HealthResponse)
def healthz() -> HealthResponse:
    return HealthResponse(status="ok")
