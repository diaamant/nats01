"""Service layer for sending commands to the recording application"""

import logging

from clients.nats_client import get_nats_client
from models.cmd import CommandMessage, CommandPayload, ResponseMessage
from core.config import nats_config, app_config

logger = logging.getLogger(__name__)


async def send_cmd_start(
    task_id: str = None,
    segment_time: float = 300.0,
    snd_source: str = "pulsesrc01",
    snd_byterate: int = 96,
    vid_stream: str = "main",
    vid_byterate: int = 2000,
) -> ResponseMessage:
    """
    Отправка команды start для начала записи.

    Args:
        task_id: ID задачи (по умолчанию из конфига)
        segment_time: Время сегмента в секундах
        snd_source: Источник звука
        snd_byterate: Битрейт аудио
        vid_stream: Видео поток
        vid_byterate: Битрейт видео

    Returns:
        ResponseMessage: Ответ от сервера
    """
    task_id = task_id or app_config.task_id

    cmd = CommandMessage(
        task_id=task_id,
        cmd="start",
        payload=CommandPayload(
            segment_time=segment_time,
            snd_source=snd_source,
            snd_byterate=snd_byterate,
            vid_stream=vid_stream,
            vid_byterate=vid_byterate,
        ),
    )

    async with get_nats_client(nats_config.url, nats_config.timeout) as client:
        try:
            response = await client.send_command(nats_config.subject, cmd)
            logger.info(f"Start command sent: {response.payload.file_path}")
            return response
        except Exception as e:
            logger.error(f"Error sending start command: {e}")
            raise


async def send_cmd_stop(
    task_id: str = None, segment_time: float = 300.0
) -> ResponseMessage:
    """
    Отправка команды stop для остановки записи.

    Args:
        task_id: ID задачи (по умолчанию из конфига)
        segment_time: Время сегмента в секундах

    Returns:
        ResponseMessage: Ответ от сервера
    """
    task_id = task_id or app_config.task_id

    cmd = CommandMessage(
        task_id=task_id, cmd="stop", payload=CommandPayload(segment_time=segment_time)
    )

    async with get_nats_client(nats_config.url, nats_config.timeout) as client:
        try:
            response = await client.send_command(nats_config.subject, cmd)
            logger.info(f"Stop command sent: stopped at {response.payload.at_stopped}")
            return response
        except Exception as e:
            logger.error(f"Error sending stop command: {e}")
            raise


async def send_cmd_status(task_id: str = None) -> ResponseMessage:
    """
    Отправка команды status для проверки статуса записи.

    Args:
        task_id: ID задачи (по умолчанию из конфига)

    Returns:
        ResponseMessage: Ответ от сервера
    """
    task_id = task_id or app_config.task_id

    cmd = CommandMessage(task_id=task_id, cmd="status", payload=None)

    async with get_nats_client(nats_config.url, nats_config.timeout) as client:
        try:
            response = await client.send_command(nats_config.subject, cmd)
            logger.info(f"Status: {response.app_status}")
            return response
        except Exception as e:
            logger.error(f"Error sending status command: {e}")
            raise
