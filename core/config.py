import json
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = Path(__file__).parent.parent / ".env"
print(f"env_path - {env_path}")


class NATSConfig(BaseSettings):
    """NATS connection configuration using Pydantic"""

    model_config = SettingsConfigDict(env_file=env_path, extra="ignore")

    # NATS_URL: str = Field("nats://localhost:4222", validation_alias="NATS_URL")
    # NATS_TIMEOUT: int = Field(2, validation_alias="NATS_TIMEOUT")
    # NATS_SUBJECT: str = Field("rec.control", validation_alias="NATS_SUBJECT")

    NATS_URL: str = "nats://localhost:4222"
    NATS_TIMEOUT: int = 2
    NATS_SUBJECT: str = "rec.control"


class AppConfig(BaseSettings):
    """Application configuration using Pydantic"""

    model_config = SettingsConfigDict(env_file=env_path, extra="ignore")

    DEBUG: bool = True
    TASK_ID: str = "task01"
    LOG_LEVEL: str = "INFO"


# Singleton instances
app_config = AppConfig()
nats_config = NATSConfig()

if app_config.DEBUG:
    if env_path.exists():
        print("Environment variables loaded from %s", env_path)
        print(
            "Application settings initialized: %s",
            json.dumps(nats_config.model_dump(), indent=2, default=str),
        )
