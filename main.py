"""Main entry point for the NATS client application"""

import asyncio
import logging
import sys

from core.config import app_config
from services.send_cmd import send_cmd_start, send_cmd_stop, send_cmd_status


def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=getattr(logging, app_config.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


async def main_async():
    """Async main function to run commands"""
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting command execution...")

        # Start recording
        start_response = await send_cmd_start()
        print(f"✓ Start: {start_response.payload.file_path}")

        # Stop recording
        stop_response = await send_cmd_stop()
        print(f"✓ Stop: {stop_response.payload.at_stopped}")

        # Check status
        status_response = await send_cmd_status()
        print(f"✓ Status: {status_response.app_status}")

        logger.info("All commands completed successfully")

    except Exception as e:
        logger.error(f"Error during command execution: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point"""
    setup_logging()
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
