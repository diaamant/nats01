import logging
import sys

from core.config import app_config


def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=getattr(logging, app_config.LOG_LEVEL),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


# Configure logging
logger = logging.getLogger(__name__)
