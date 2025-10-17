"""Main entry point for the NATS client application"""

import asyncio
import logging
import sys

from clients.nats_client import get_nats_client
from core.config import app_config, nats_config
from models.cmd import StartPayload, StopPayload
from services.send_cmd import ManagerService


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

    async with get_nats_client(nats_config.url, nats_config.timeout) as nats_client:
        # Сервис создается один раз и переиспользуется
        recording_service = ManagerService(
            client=nats_client,
            config=app_config,
            nats_subject=nats_config.subject,
        )

        # Теперь можно вызывать методы сервиса
        try:
            # 1. Проверяем статус
            await recording_service.status()

            # 2. Начинаем запись с кастомными параметрами
            start_params = StartPayload(vid_byterate=2500, segment_time=60)
            await recording_service.start(payload=start_params)

            # 3. Останавливаем запись
            await recording_service.stop(payload=StopPayload())

        except Exception as e:
            logger.critical(f"An operation failed in the main workflow: {e}")

    logger.info("All commands completed successfully")


def main():
    """Main entry point"""
    setup_logging()
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
