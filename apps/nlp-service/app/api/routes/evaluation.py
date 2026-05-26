from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.core.logging import get_logger, timed
from app.schemas.evaluation import (
    EvaluationReportRequest,
    EvaluationReportResponse,
)
from app.services.evaluation_report_service import EvaluationReportService

router = APIRouter(prefix="/v1")
logger = get_logger("nlp.evaluation")


def _service(request: Request) -> EvaluationReportService:
    return request.app.state.evaluation_report_service


@router.post("/evaluation/regression-report")
def post_regression_report(
    payload: EvaluationReportRequest, request: Request
) -> EvaluationReportResponse:
    if not settings.expose_evaluation_endpoint:
        # Hide the route's existence from clients that shouldn't lean on it.
        raise HTTPException(status_code=404, detail="Not Found")
    service = _service(request)
    with timed(
        logger,
        "evaluation.regression_report",
        kinds=",".join(payload.kinds) if payload.kinds else "all",
        languages=",".join(payload.languages) if payload.languages else "all",
        include_cases=payload.include_cases,
    ):
        return service.generate(
            kinds=payload.kinds,
            languages=payload.languages,
            include_cases=payload.include_cases,
        )
