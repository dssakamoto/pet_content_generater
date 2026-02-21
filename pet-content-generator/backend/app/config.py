from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    image_generator: str = "mock"
    output_dir: Path = Path("/app/app/outputs")

    # API keys (all optional — set only what you use)
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    stability_api_key: str | None = None

    model_config = {"env_file": ".env"}


settings = Settings()
settings.output_dir.mkdir(parents=True, exist_ok=True)
