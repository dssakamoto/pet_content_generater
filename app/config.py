"""アプリケーション設定管理モジュール"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション設定クラス"""

    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "llama3.2"
    max_retries: int = 3
    code_exec_timeout: int = 30
    debug_mode: bool = False

    model_config = {"env_file": ".env"}


settings = Settings()
