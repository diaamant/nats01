"""NATS client with connection management and error handling"""

import json
import logging
from typing import Optional
from contextlib import asynccontextmanager

from nats.aio.client import Client as NATS
from nats.errors import (
    TimeoutError as NATSTimeoutError,
    ConnectionClosedError,
    NoRespondersError,
)

from models.cmd import CommandMessage, ResponseMessage

logger = logging.getLogger(__name__)


class NatsClient:
    """
    NATS client для управления подключением и отправки команд.

    Best practices:
    - Переиспользование соединения
    - Обработка ошибок
    - Логирование
    - Контекстный менеджер для автоматического закрытия
    """

    def __init__(self, nats_url: str = "nats://localhost:4222", timeout: int = 2):
        """
        Инициализация NATS клиента.

        Args:
            nats_url: URL NATS сервера
            timeout: Таймаут запросов в секундах
        """
        self.nats_url = nats_url
        self.timeout = timeout
        self._nc: Optional[NATS] = None
        self._connected = False

    async def connect(self) -> None:
        """Установка соединения с NATS сервером"""
        if self._connected and self._nc:
            logger.debug("Already connected to NATS")
            return

        try:
            self._nc = NATS()
            await self._nc.connect(self.nats_url)
            self._connected = True
            logger.info(f"Connected to NATS: {self.nats_url}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
            raise ConnectionError(f"Could not connect to NATS server: {e}") from e

    async def disconnect(self) -> None:
        """Закрытие соединения с NATS сервером"""
        if self._nc and self._connected:
            try:
                await self._nc.close()
                self._connected = False
                logger.info("Disconnected from NATS")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")

    @property
    def is_connected(self) -> bool:
        """Проверка статуса подключения"""
        return self._connected and self._nc is not None

    async def send_command(
        self, subject: str, command: CommandMessage
    ) -> ResponseMessage:
        """
        Отправка команды через NATS и получение ответа.

        Args:
            subject: NATS subject (канал)
            command: Команда для отправки

        Returns:
            ResponseMessage: Ответ от сервера

        Raises:
            ConnectionError: Если нет подключения к NATS
            TimeoutError: Если превышен таймаут ожидания ответа
            ValueError: Если получен некорректный ответ
            NoRespondersError: Если нет доступных обработчиков для запроса
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to NATS server")

        try:
            # Сериализация команды
            payload = command.model_dump_json().encode()
            logger.debug(f"Sending command: {command.cmd} to {subject}")

            # Отправка запроса и ожидание ответа
            response = await self._nc.request(subject, payload, timeout=self.timeout)

            # Десериализация ответа
            data = json.loads(response.data.decode())
            reply = ResponseMessage(**data)

            logger.info(
                f"Command {command.cmd} completed: "
                f"status={reply.msg_status}, app_status={reply.app_status}"
            )
            return reply

        except NoRespondersError as e:
            logger.error(
                f"No responders available for command {command.cmd} on subject {subject}. "
                "Make sure the application handler is running."
            )
            raise ConnectionError(
                f"No responders available for request on {subject}. "
                "The application handler may not be running."
            ) from e

        except NATSTimeoutError as e:
            logger.error(f"NATS request timeout for command {command.cmd}")
            raise TimeoutError(
                f"Request timeout after {self.timeout}s for {subject}"
            ) from e

        except ConnectionClosedError as e:
            logger.error(f"NATS connection closed during request")
            self._connected = False
            raise ConnectionError("NATS connection was closed") from e

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise ValueError(f"Could not parse response: {e}") from e

        except Exception as e:
            logger.error(f"Unexpected error during command execution: {e}")
            raise

    async def __aenter__(self):
        """Контекстный менеджер: вход"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер: выход"""
        await self.disconnect()


@asynccontextmanager
async def get_nats_client(nats_url: str = "nats://localhost:4222", timeout: int = 2):
    """
    Контекстный менеджер для получения NATS клиента.

    Usage:
        async with get_nats_client() as client:
            response = await client.send_command(subject, command)

    Args:
        nats_url: URL NATS сервера
        timeout: Таймаут запросов

    Yields:
        NATSClient: Подключенный клиент
    """
    client = NatsClient(nats_url=nats_url, timeout=timeout)
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()
