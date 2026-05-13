from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import analysis, health, rhymes
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging, get_logger, timed
from app.repositories.cmudict_repository import CmuDictRepository
from app.services.pronunciation_service import PronunciationService
from app.services.ranking_service import warm_frequency_cache
from app.services.rhyme_index import RhymeIndex
from app.services.rhyme_service import RhymeService
from app.services.syllable_service import SyllableService


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger = get_logger("nlp.startup")
    with timed(logger, "startup.load_dictionary"):
        repository = CmuDictRepository()
    with timed(logger, "startup.build_rhyme_index"):
        index = RhymeIndex(repository)
    with timed(logger, "startup.warm_frequency_cache"):
        warm_frequency_cache()

    pronunciation = PronunciationService(repository)
    syllables = SyllableService(repository)
    rhymes_service = RhymeService(repository, index, pronunciation, syllables)

    app.state.repository = repository
    app.state.rhyme_index = index
    app.state.pronunciation_service = pronunciation
    app.state.syllable_service = syllables
    app.state.rhyme_service = rhymes_service

    logger.info(
        "startup.ready",
        extra={"extras": {"app": settings.app_name, "words": len(repository)}},
    )
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(rhymes.router)
    app.include_router(analysis.router)
    return app


app = create_app()
