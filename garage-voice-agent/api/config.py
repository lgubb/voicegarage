from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_env_files() -> None:
    load_dotenv(PROJECT_ROOT.parent / ".envrc")
    load_dotenv(PROJECT_ROOT / ".env")


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore", populate_by_name=True)

    livekit_url: str | None = Field(default=None, alias="LIVEKIT_URL")
    livekit_api_key: str | None = Field(default=None, alias="LIVEKIT_API_KEY")
    livekit_api_secret: str | None = Field(default=None, alias="LIVEKIT_API_SECRET")
    agent_name: str = Field(default="garage-voice-agent", alias="AGENT_NAME")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
    )

    demo_mode: bool = Field(default=True, alias="DEMO_MODE")
    local_call_store_path: Path = Field(default=PROJECT_ROOT / "data" / "calls.json", alias="LOCAL_CALL_STORE_PATH")

    @field_validator("local_call_store_path", mode="before")
    @classmethod
    def resolve_local_path(cls, value: str | Path) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return PROJECT_ROOT / path

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_api_settings() -> ApiSettings:
    _load_env_files()
    return ApiSettings()
