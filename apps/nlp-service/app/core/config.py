from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NLP_", env_file=".env", extra="ignore")

    app_name: str = "songwriting-nlp-service"
    log_level: str = "INFO"

    default_rhyme_limit: int = 10
    max_rhyme_limit: int = 25
    max_line_length: int = 500

    # Top-N most-frequent words from wordfreq's "es" data feed the rhyme index.
    # Raised from 80k to 150k to surface more rare/poetic/regional vocabulary.
    # Trade-off: ~2-5% longer startup time.
    spanish_corpus_size: int = 150_000

    # Phase 5.5 M3: gate the /v1/evaluation/regression-report endpoint.
    # When False the route returns 404 so external clients can't depend
    # on it. The CLI keeps working regardless.
    expose_evaluation_endpoint: bool = True

    # Redis-backed response cache for /v1/analyze-draft and
    # /v1/analyze-draft-compare. Off by default so local dev and CI don't
    # require Redis; flip on per environment via NLP_CACHE_ENABLED=true.
    # Bump cache_key_prefix to invalidate everything after analysis changes.
    cache_enabled: bool = False
    cache_redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600
    cache_key_prefix: str = "nlp:v2"


settings = Settings()
