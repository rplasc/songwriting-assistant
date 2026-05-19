from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NLP_", env_file=".env", extra="ignore")

    app_name: str = "songwriting-nlp-service"
    log_level: str = "INFO"

    default_rhyme_limit: int = 10
    max_rhyme_limit: int = 25
    max_line_length: int = 500

    # Phase 3 — Spanish track.
    # Top-N most-frequent words from wordfreq's "es" data feed the rhyme index.
    # ~80k matches the order of magnitude of the English CMU corpus after the
    # frequency-floor filter; tune lower for faster startup.
    spanish_corpus_size: int = 80_000


settings = Settings()
