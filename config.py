from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    db_url: str

    openai_api_key: str
    openai_model: str
    openai_model_dates: str

    google_search_api_key: str
    google_search_engine_id: str
    google_search_engine_url: str = "https://www.googleapis.com/customsearch/v1"
    google_search_number_of_retries: int

    news_range_in_days: int
    ny_classification_score_threshold: int


def load_settings():
    try:
        return Settings()
    except ValidationError as e:
        exit(str(e))


settings = load_settings()
