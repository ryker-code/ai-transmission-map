from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    anthropic_api_key: str = "placeholder-set-in-env"
    google_api_key: str = "placeholder-set-in-env"
    gemini_api_key: str = "placeholder-set-in-env"
    openai_api_key: str = "placeholder-set-in-env"
    google_cloud_project: str = "placeholder-project"
    bigquery_dataset: str = "aitm"
    next_public_api_url: str = "http://localhost:8000"

    def get_gemini_key(self) -> str:
        """Return GEMINI_API_KEY if set, else fall back to GOOGLE_API_KEY."""
        if "placeholder" not in self.gemini_api_key.lower():
            return self.gemini_api_key
        return self.google_api_key

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
