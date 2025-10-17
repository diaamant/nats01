"""Service layer for sending commands to the recording application"""

import logging
from typing import Optional
from nats.errors import ConnectionClosedError, TimeoutError as NatsTimeoutError

from clients.nats_client import NatsClient
from core.config import AppConfig
from models.cmd import (
    CommandMessage,
    CommandPayload,
    ResponseMessage,
    StartPayload,
    StopPayload,
    cmd_type,
)

logger = logging.getLogger(__name__)


class ManagerService:
    """Manages sending commands to the recording application via NATS."""

    def __init__(self, client: NatsClient, config: AppConfig, nats_subject: str):
        self._client = client
        self._config = config
        self._subject = nats_subject

    async def _send_command(
        self,
        command_name: cmd_type,
        task_id: Optional[str] = None,
        payload: Optional[CommandPayload] = None,
    ) -> ResponseMessage:
        """
        Private helper to construct, send a command, and handle errors centrally.
        """
        effective_task_id = task_id or self._config.TASK_ID
        if not effective_task_id:
            raise ValueError("Task ID must be provided or set in the config.")

        cmd = CommandMessage(
            task_id=effective_task_id,
            cmd=command_name,
            payload=payload,
        )

        try:
            logger.debug(
                f"Sending command '{command_name}' for task '{effective_task_id}'..."
            )
            response = await self._client.send_command(self._subject, cmd)
            logger.debug(f"Received response for '{command_name}': {response}")
            return response

        # Перехватываем конкретную ошибку подключения от NATS-клиента
        except ConnectionClosedError as e:
            msg = f"Connection error on command '{command_name}': {e}"
            logger.error(msg)
            return ResponseMessage(
                task_id=effective_task_id,
                msg_status="error",
                app_status="error",
                payload=None,
            )

        # Перехватываем ошибку тайм-аута от NATS-клиента
        except NatsTimeoutError as e:
            msg = f"Timeout on command '{command_name}': The handler did not respond in time."
            logger.error(msg)
            return ResponseMessage(
                task_id=effective_task_id,
                msg_status="error",
                app_status="error",
                payload=None,
            )

        # Перехватываем любые другие неожиданные ошибки
        except Exception as e:
            msg = f"Unexpected error on command '{command_name}': {e}"
            logger.error(msg, exc_info=True)
            return ResponseMessage(
                task_id=effective_task_id,
                msg_status="success",
                app_status="error",
                payload=None,
            )

    async def start(
        self,
        payload: StartPayload,
        task_id: Optional[str] = None,
    ) -> ResponseMessage:
        """Sends the 'start' command to begin recording."""
        response = await self._send_command(
            command_name="start",
            task_id=task_id,
            payload=CommandPayload(**payload.model_dump()),
        )
        logger.info(
            f"Start command successful for task '{response.task_id}': recording to {response.payload.file_path}"
        )
        return response

    async def stop(
        self,
        payload: StopPayload,
        task_id: Optional[str] = None,
    ) -> ResponseMessage:
        """Sends the 'stop' command to stop recording."""
        response = await self._send_command(
            command_name="stop",
            task_id=task_id,
            payload=CommandPayload(**payload.model_dump()),
        )
        logger.info(
            f"Stop command successful for task '{response.task_id}': stopped at {response.payload.at_stopped}"
        )
        return response

    async def status(self, task_id: Optional[str] = None) -> ResponseMessage:
        """Sends the 'status' command to check the recording status."""
        response = await self._send_command(
            command_name="status", task_id=task_id, payload=None
        )
        logger.info(f"Status for task '{response.task_id}': {response.app_status}")
        return response
