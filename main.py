"""Main entry point for the NATS client application"""

import asyncio
import logging
import sys
from typing import List

from clients.nats_client import get_nats_client
from core.config import app_config, nats_config
from models.cmd import StartPayload, StopPayload, ResponseMessage
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

        # ----------------------------------------------------------------------
        # Пример использования с Пользовательскими параметрами
        # ----------------------------------------------------------------------
        try:
            # 1. Определяем кастомные параметры старта записи
            custom_start_params = StartPayload(
                segment_time=600.0,  # Записывать сегменты по 10 минут
                snd_source="microphone_array",  # Кастомный источник звука
                snd_byterate=128,  # Более высокая частота звука
                vid_byterate=3000,  # Высокий битрейт видео
                vid_stream="high_res",  # Кастомный видеопоток
            )

            # 2. Отправляем команду "старт" с кастомными параметрами и кастомным task_id
            logger.info(
                "Sending 'start' command with custom parameters for task 'custom_rec'"
            )
            start_response = await recording_service.start(
                payload=custom_start_params, task_id="custom_rec"
            )
            logger.info(f"Start Response: {start_response}")

            # 3. Проверяем статус для кастомной задачи
            logger.info("Sending 'status' command for task 'custom_rec'")
            status_response = await recording_service.status(task_id="custom_rec")
            logger.info(f"Status Response: {status_response}")

            # 4. Отправляем команду "стоп" для кастомной задачи
            logger.info("Sending 'stop' command for task 'custom_rec'")
            stop_response = await recording_service.stop(
                payload=StopPayload(), task_id="custom_rec"
            )
            logger.info(f"Stop Response: {stop_response}")

        except Exception as e:
            logger.critical(f"An operation failed in the main workflow: {e}")
        # ----------------------------------------------------------------------

    logger.info("All commands completed successfully")


def main():
    """Main entry point"""
    setup_logging()

    asyncio.run(main_async())


if __name__ == "__main__":
    main()
