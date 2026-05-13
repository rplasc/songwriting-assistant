from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NLP_", env_file=".env", extra="ignore")

    app_name: str = "songwriting-nlp-service"
    log_level: str = "INFO"

    default_rhyme_limit: int = 10
    max_rhyme_limit: int = 25
    max_line_length: int = 500


settings = Settings()
