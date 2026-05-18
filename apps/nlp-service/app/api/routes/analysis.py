from fastapi import APIRouter, Depends, Request

from app.core.logging import get_logger, timed
from app.domain.tokenization import tokenize_line
from app.schemas.requests import LineAnalysisRequest
from app.schemas.responses import LastWord, LineAnalysisResponse, TokenAnalysis
from app.services.syllable_service import SyllableService

router = APIRouter(prefix="/v1")
logger = get_logger("nlp.analysis")


def _syllable_service(request: Request) -> SyllableService:
    return request.app.state.syllable_service


def _source(found: bool) -> str:
    return "dictionary" if found else "heuristic"


@router.post("/analyze-line")
def post_analyze_line(
    payload: LineAnalysisRequest,
    service: SyllableService = Depends(_syllable_service),
) -> LineAnalysisResponse:
    with timed(logger, "analyze_line.request", length=len(payload.line)):
        tokens = tokenize_line(payload.line)
        total, per_token = service.count_tokens(tokens)

    token_payloads = [
        TokenAnalysis(
            text=tok.text,
            normalized=tok.normalized,
            syllables=count,
            pronunciation_found=found,
            source=_source(found),
        )
        for tok, count, found in per_token
    ]

    last_word: LastWord | None = None
    if per_token:
        tok, count, found = per_token[-1]
        last_word = LastWord(
            text=tok.text,
            normalized=tok.normalized,
            pronunciation_found=found,
            syllables=count,
            source=_source(found),
        )

    normalized_line = " ".join(t.normalized for t in tokens)
    return LineAnalysisResponse(
        line=payload.line,
        normalized_line=normalized_line,
        total_syllables=total,
        tokens=token_payloads,
        last_word=last_word,
    )
