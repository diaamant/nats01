"""Configuration management for the application"""

import os
from dataclasses import dataclass


@dataclass
class NATSConfig:
    """NATS connection configuration"""

    url: str = os.getenv("NATS_URL", "nats://localhost:4222")
    timeout: int = int(os.getenv("NATS_TIMEOUT", "2"))
    subject: str = os.getenv("NATS_SUBJECT", "rec.control")


@dataclass
class AppConfig:
    """Application configuration"""

    task_id: str = os.getenv("TASK_ID", "task01")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


# Singleton instances
nats_config = NATSConfig()
app_config = AppConfig()
