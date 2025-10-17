import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from clients.nats_client import get_nats_client
from core.config import app_config, nats_config
from models.cmd import StartPayload, StopPayload
from services.send_cmd import ManagerService


@pytest.mark.asyncio
@pytest.mark.integration
class TestRealNATSIntegration:
    """
    Интеграционные тесты с реальным NATS сервером и Rust-приложением.

    ВАЖНО: Для запуска этих тестов необходимо:
    1. Запущенный NATS сервер на localhost:4222
    2. Запущенное Rust-приложение, слушающее на канале "rec.control"

    Запуск: pytest tests/test_real_nats.py -v -m integration
    """

    async def test_start_command_response(self):
        """Тест реального ответа на команду start"""
        async with get_nats_client(
            nats_config.NATS_URL, nats_config.NATS_TIMEOUT
        ) as client:
            service = ManagerService(
                client=client, config=app_config, nats_subject=nats_config.NATS_SUBJECT
            )
            response = await service.start(payload=StartPayload())

            # Проверяем структуру ответа
            assert response.task_id == "task01"
            assert response.msg_status == "success"
            assert response.app_status == "started"

            # Проверяем payload
            assert response.payload is not None
            assert response.payload.segment_time == 300.0
            assert response.payload.file_path is not None
            assert response.payload.file_path.startswith("/mnt/")
            assert response.payload.file_path.endswith(".wav")
            assert response.payload.at_started is not None
            assert len(response.payload.at_started) > 0
            # При старте at_stopped должен быть пустым
            assert (
                response.payload.at_stopped == "" or response.payload.at_stopped is None
            )

            print(f"✓ Start response validated: {response.payload.file_path}")

    async def test_stop_command_response(self):
        """Тест реального ответа на команду stop"""
        async with get_nats_client(
            nats_config.NATS_URL, nats_config.NATS_TIMEOUT
        ) as client:
            service = ManagerService(
                client=client, config=app_config, nats_subject=nats_config.NATS_SUBJECT
            )
            response = await service.stop(payload=StopPayload())

            # Проверяем структуру ответа
            assert response.task_id == "task01"
            assert response.msg_status == "success"
            assert response.app_status == "stopped"

            # Проверяем payload
            assert response.payload is not None
            assert response.payload.segment_time == 300.0
            assert response.payload.file_path is not None
            assert response.payload.file_path.startswith("/mnt/")
            assert response.payload.at_started is not None
            assert response.payload.at_stopped is not None
            assert len(response.payload.at_stopped) > 0

            # Проверяем, что время остановки позже времени старта
            assert response.payload.at_stopped >= response.payload.at_started

            print(
                f"✓ Stop response validated: stopped at {response.payload.at_stopped}"
            )

    async def test_status_command_response(self):
        """Тест реального ответа на команду status"""
        async with get_nats_client(
            nats_config.NATS_URL, nats_config.NATS_TIMEOUT
        ) as client:
            service = ManagerService(
                client=client, config=app_config, nats_subject=nats_config.NATS_SUBJECT
            )
            response = await service.status()

            # Проверяем структуру ответа
            assert response.task_id == "task01"
            assert response.msg_status == "success"
            assert response.app_status in ["started", "stopped"]

            # Проверяем payload
            assert response.payload is not None
            assert response.payload.segment_time == 300.0
            assert response.payload.file_path is not None
            assert response.payload.at_started is not None

            print(f"✓ Status response validated: app_status={response.app_status}")

    async def test_full_cycle_with_real_server(self):
        """Тест полного цикла работы с реальным сервером"""
        async with get_nats_client(
            nats_config.NATS_URL, nats_config.NATS_TIMEOUT
        ) as client:
            service = ManagerService(
                client=client, config=app_config, nats_subject=nats_config.NATS_SUBJECT
            )

            # 1. Запускаем запись
            start_response = await service.start(payload=StartPayload())
            assert start_response.app_status == "started"
            file_path = start_response.payload.file_path
            at_started = start_response.payload.at_started

            print(f"✓ Recording started: {file_path}")

            # 2. Проверяем статус (должна идти запись)
            await asyncio.sleep(0.5)  # Небольшая пауза
            status_response = await service.status()
            assert status_response.app_status in ["started", "stopped"]
            assert status_response.payload.file_path == file_path

            print(f"✓ Status checked: {status_response.app_status}")

            # 3. Останавливаем запись
            await asyncio.sleep(0.5)  # Небольшая пауза
            stop_response = await service.stop(payload=StopPayload())
            assert stop_response.app_status == "stopped"
            assert stop_response.payload.file_path == file_path
            assert stop_response.payload.at_started == at_started
            assert stop_response.payload.at_stopped is not None
            assert len(stop_response.payload.at_stopped) > 0

            print(f"✓ Recording stopped: {stop_response.payload.at_stopped}")

            # 4. Проверяем финальный статус
            await asyncio.sleep(0.5)
            final_status = await service.status()
            # Статус может быть как started (новая запись), так и stopped
            assert final_status.msg_status == "success"

            print(f"✓ Full cycle completed successfully")

    async def test_response_timestamps_format(self):
        """Тест формата временных меток в ответах"""
        async with get_nats_client(
            nats_config.NATS_URL, nats_config.NATS_TIMEOUT
        ) as client:
            service = ManagerService(
                client=client, config=app_config, nats_subject=nats_config.NATS_SUBJECT
            )
            response = await service.start(payload=StartPayload())

            # Проверяем формат ISO 8601
            at_started = response.payload.at_started
            assert at_started is not None
            assert "T" in at_started
            assert "Z" in at_started or "+" in at_started

            # Проверяем, что можно распарсить дату
            from datetime import datetime

            try:
                # Пробуем распарсить как ISO формат
                dt = datetime.fromisoformat(at_started.replace("Z", "+00:00"))
                assert dt.year >= 2025
                print(f"✓ Timestamp format valid: {at_started}")
            except ValueError as e:
                pytest.fail(f"Invalid timestamp format: {at_started}, error: {e}")

    async def test_response_file_path_format(self):
        """Тест формата пути к файлу в ответах"""
        async with get_nats_client(
            nats_config.NATS_URL, nats_config.NATS_TIMEOUT
        ) as client:
            service = ManagerService(
                client=client, config=app_config, nats_subject=nats_config.NATS_SUBJECT
            )
            response = await service.start(payload=StartPayload())

            file_path = response.payload.file_path
            assert file_path is not None
            assert file_path.startswith("/mnt/")
            assert file_path.endswith(".wav")
            assert "rec" in file_path.lower()

            print(f"✓ File path format valid: {file_path}")

    async def test_response_segment_time_consistency(self):
        """Тест согласованности segment_time в ответах"""
        async with get_nats_client(
            nats_config.NATS_URL, nats_config.NATS_TIMEOUT
        ) as client:
            service = ManagerService(
                client=client, config=app_config, nats_subject=nats_config.NATS_SUBJECT
            )

            start_response = await service.start(payload=StartPayload())
            assert start_response.payload.segment_time == 300.0

            await asyncio.sleep(0.5)
            status_response = await service.status()
            assert status_response.payload.segment_time == 300.0

            await asyncio.sleep(0.5)
            stop_response = await service.stop(payload=StopPayload())
            assert stop_response.payload.segment_time == 300.0

            print(f"✓ Segment time consistent across all responses: 300.0")


@pytest.mark.asyncio
@pytest.mark.integration
class TestRealNATSErrorHandling:
    """Тесты обработки ошибок с реальным сервером"""

    async def test_multiple_start_commands(self):
        """Тест отправки нескольких команд start подряд"""
        async with get_nats_client(
            nats_config.NATS_URL, nats_config.NATS_TIMEOUT
        ) as client:
            service = ManagerService(
                client=client, config=app_config, nats_subject=nats_config.NATS_SUBJECT
            )

            response1 = await service.start(payload=StartPayload())
            assert response1.msg_status == "success"

            await asyncio.sleep(0.5)

            # Вторая команда start - поведение зависит от реализации Rust
            response2 = await service.start(payload=StartPayload())
            # Может быть success (перезапуск) или error (уже запущено)
            assert response2.msg_status in ["success", "error"]

            print(f"✓ Multiple start handling: {response2.msg_status}")

    async def test_stop_without_start(self):
        """Тест команды stop без предварительного start"""
        async with get_nats_client(
            nats_config.NATS_URL, nats_config.NATS_TIMEOUT
        ) as client:
            service = ManagerService(
                client=client, config=app_config, nats_subject=nats_config.NATS_SUBJECT
            )

            # Сначала убедимся, что запись остановлена
            await service.stop(payload=StopPayload())
            await asyncio.sleep(0.5)

            # Пытаемся остановить снова
            response = await service.stop(payload=StopPayload())
            # Может вернуть success (уже остановлено) или error
            assert response.msg_status in ["success", "error"]

            print(f"✓ Stop without start handling: {response.msg_status}")
