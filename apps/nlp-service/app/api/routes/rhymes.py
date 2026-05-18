from fastapi import APIRouter, Depends, Request

from app.core.logging import get_logger, timed
from app.schemas.requests import RhymeRequest
from app.schemas.responses import RhymeMeta, RhymeResponse
from app.services.rhyme_service import RhymeService

router = APIRouter(prefix="/v1")
logger = get_logger("nlp.rhymes")


def _rhyme_service(request: Request) -> RhymeService:
    return request.app.state.rhyme_service


@router.post("/rhymes")
def post_rhymes(
    payload: RhymeRequest,
    service: RhymeService = Depends(_rhyme_service),
) -> RhymeResponse:
    with timed(
        logger,
        "rhymes.request",
        word=payload.word,
        limit=payload.limit,
        mode=payload.mode,
    ):
        normalized, found, rhymes = service.find_rhymes(
            payload.word,
            payload.limit,
            mode=payload.mode,
            include_metadata=payload.include_metadata,
        )
    return RhymeResponse(
        word=payload.word,
        normalized_word=normalized,
        pronunciations_found=found,
        rhymes=rhymes,
        meta=RhymeMeta(
            limit=payload.limit,
            mode=payload.mode,
            include_near=payload.mode == "near",
        ),
    )
