from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    kora_host: str = "0.0.0.0"
    kora_port: int = 8000
    kora_data_dir: str = "./data"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_chat_model: str = "llama3.2"
    ollama_embed_model: str = "nomic-embed-text"

    chunk_size: int = 800
    chunk_overlap: int = 120
    embed_dim: int = 384

    @property
    def data_path(self) -> Path:
        return Path(self.kora_data_dir).resolve()

    @property
    def db_path(self) -> Path:
        return self.data_path / "kora.db"

    @property
    def upload_path(self) -> Path:
        return self.data_path / "uploads"

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key.strip())


settings = Settings()
