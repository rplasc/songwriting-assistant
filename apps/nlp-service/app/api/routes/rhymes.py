from collections import Counter

from fastapi import APIRouter, Request

from app.core.logging import get_logger, timed
from app.domain.response_contracts.capability_reason_mapper import (
    rhyme_capabilities,
)
from app.domain.response_contracts.rhyme_evidence_tagger import tag_candidate
from app.schemas.requests import RhymeRequest
from app.schemas.responses import RhymeResponse, RhymeSummary
from app.services.language_router import LanguageRouter

router = APIRouter(prefix="/v1")
logger = get_logger("nlp.rhymes")


def _language_router(request: Request) -> LanguageRouter:
    return request.app.state.language_router


@router.post("/rhymes")
def post_rhymes(payload: RhymeRequest, request: Request) -> RhymeResponse:
    router_ = _language_router(request)
    ctx = router_.get(payload.language)
    with timed(
        logger,
        "rhymes.request",
        word=payload.word,
        limit=payload.limit,
        mode=payload.mode,
        language=payload.language,
        target_type=payload.target_type,
    ):
        lookup = ctx.rhyme_service.find_rhymes(
            payload.word,
            payload.limit,
            mode=payload.mode,
            target_type=payload.target_type,
            include_metadata=payload.include_metadata,
        )
    tagged = [
        tag_candidate(
            c,
            query=payload.word,
            language=payload.language,
            target_type=payload.target_type,
            pronunciations_found=lookup.pronunciations_found,
        )
        for c in lookup.candidates
    ]
    family_counts: Counter[str] = Counter()
    for c in tagged:
        if c.rhyme_family is not None:
            family_counts[c.rhyme_family] += 1
    capabilities = rhyme_capabilities(
        multisyllabic_supported=bool(
            getattr(ctx.engine, "multisyllabic_supported", False)
        )
    )
    return RhymeResponse(
        query=payload.word,
        normalized_query=lookup.normalized,
        language=payload.language,
        target_type=payload.target_type,
        mode=lookup.resolved_mode,
        pronunciations_found=lookup.pronunciations_found,
        summary=RhymeSummary(
            family_counts=dict(family_counts),
            returned=len(tagged),
            requested_limit=payload.limit,
        ),
        rhymes=tagged,
        capabilities=capabilities,
    )
