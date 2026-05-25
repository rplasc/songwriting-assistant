from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.api.routes import analysis, draft_analysis, health, rhymes
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging, get_logger, timed
from app.domain.languages.english import EnglishEngine
from app.domain.languages.spanish import SpanishEngine
from app.repositories.cmudict_repository import CmuDictRepository
from app.repositories.spanish_corpus import SpanishCorpus
from app.services.draft_analysis_service import DraftAnalysisService
from app.services.draft_nlp_service import DraftNlpService
from app.services.language_router import LanguageContext, LanguageRouter
from app.services.pronunciation_service import PronunciationService
from app.services.rhyme_index import RhymeIndex, warm_frequency_cache
from app.services.rhyme_service import RhymeService
from app.services.syllable_service import SyllableService


def _build_english_context(logger) -> LanguageContext:
    with timed(logger, "startup.load_cmudict"):
        repo = CmuDictRepository()
    engine = EnglishEngine()
    with timed(logger, "startup.build_english_index"):
        index = RhymeIndex(repo, engine)
    pron = PronunciationService(repo, engine)
    syl = SyllableService(repo, engine)
    rhymes_service = RhymeService(repo, index, pron, syl, engine)
    logger.info(
        "startup.english_ready",
        extra={"extras": {"dict_words": len(repo), "index_words": index.word_count()}},
    )
    return LanguageContext(
        engine=engine,
        repository=repo,
        index=index,
        pronunciation_service=pron,
        syllable_service=syl,
        rhyme_service=rhymes_service,
    )


def _build_spanish_context(logger) -> LanguageContext:
    with timed(logger, "startup.build_spanish_corpus"):
        repo = SpanishCorpus(top_n=settings.spanish_corpus_size)
    engine = SpanishEngine()
    with timed(logger, "startup.build_spanish_index"):
        index = RhymeIndex(repo, engine)
    pron = PronunciationService(repo, engine)
    syl = SyllableService(repo, engine)
    rhymes_service = RhymeService(repo, index, pron, syl, engine)
    logger.info(
        "startup.spanish_ready",
        extra={"extras": {"corpus_words": len(repo), "index_words": index.word_count()}},
    )
    return LanguageContext(
        engine=engine,
        repository=repo,
        index=index,
        pronunciation_service=pron,
        syllable_service=syl,
        rhyme_service=rhymes_service,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger = get_logger("nlp.startup")
    # Frequencies are read during index build; warm wordfreq's lazy loader
    # for both languages up front so build timings stay comparable across runs.
    with timed(logger, "startup.warm_frequency_cache"):
        warm_frequency_cache()

    en_ctx = _build_english_context(logger)
    es_ctx = _build_spanish_context(logger)

    router = LanguageRouter({"en": en_ctx, "es": es_ctx})
    app.state.language_router = router
    with timed(logger, "startup.build_draft_nlp"):
        nlp_service = DraftNlpService()
    app.state.draft_nlp_service = nlp_service
    app.state.draft_analysis_service = DraftAnalysisService(nlp_service=nlp_service)

    # Legacy single-language attributes preserved so any external callers or
    # tests reaching into ``app.state`` directly continue to work. New code
    # should go through ``app.state.language_router``.
    app.state.repository = en_ctx.repository
    app.state.rhyme_index = en_ctx.index
    app.state.pronunciation_service = en_ctx.pronunciation_service
    app.state.syllable_service = en_ctx.syllable_service
    app.state.rhyme_service = en_ctx.rhyme_service

    logger.info(
        "startup.ready",
        extra={"extras": {"app": settings.app_name, "languages": list(router.supported)}},
    )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
    )
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(rhymes.router)
    app.include_router(analysis.router)
    app.include_router(draft_analysis.router)
    return app


app = create_app()
