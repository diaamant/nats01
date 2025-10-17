import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.cmd import (
    CommandMessage,
    CommandPayload,
    ResponseMessage,
    ResponsePayload,
    StartPayload,
    StopPayload,
)
from services.send_cmd import ManagerService
from core.config import AppConfig


class TestCommandModels:
    """Тесты для Pydantic моделей команд"""

    def test_start_command_creation(self):
        """Тест создания команды start"""
        cmd = CommandMessage(
            task_id="task01",
            cmd="start",
            payload=CommandPayload(
                segment_time=300.0,
                snd_source="pulsesrc01",
                snd_byterate=96,
                vid_stream="main",
                vid_byterate=2000,
            ),
        )

        assert cmd.task_id == "task01"
        assert cmd.cmd == "start"
        assert cmd.payload.segment_time == 300.0
        assert cmd.payload.snd_source == "pulsesrc01"
        assert cmd.payload.snd_byterate == 96
        assert cmd.payload.vid_stream == "main"
        assert cmd.payload.vid_byterate == 2000

    def test_stop_command_creation(self):
        """Тест создания команды stop"""
        cmd = CommandMessage(
            task_id="task01", cmd="stop", payload=CommandPayload(segment_time=300.0)
        )

        assert cmd.task_id == "task01"
        assert cmd.cmd == "stop"
        assert cmd.payload.segment_time == 300.0

    def test_status_command_creation(self):
        """Тест создания команды status"""
        cmd = CommandMessage(task_id="task01", cmd="status", payload=None)

        assert cmd.task_id == "task01"
        assert cmd.cmd == "status"
        assert cmd.payload is None

    def test_start_command_serialization(self):
        """Тест сериализации команды start в JSON"""
        cmd = CommandMessage(
            task_id="task01",
            cmd="start",
            payload=CommandPayload(
                segment_time=300.0,
                snd_source="pulsesrc01",
                snd_byterate=96,
                vid_stream="main",
                vid_byterate=2000,
            ),
        )

        json_str = cmd.model_dump_json()
        data = json.loads(json_str)

        assert data["task_id"] == "task01"
        assert data["cmd"] == "start"
        assert data["payload"]["segment_time"] == 300.0
        assert data["payload"]["snd_source"] == "pulsesrc01"

    def test_stop_command_serialization(self):
        """Тест сериализации команды stop в JSON"""
        cmd = CommandMessage(
            task_id="task01", cmd="stop", payload=CommandPayload(segment_time=300.0)
        )

        json_str = cmd.model_dump_json()
        data = json.loads(json_str)

        assert data["task_id"] == "task01"
        assert data["cmd"] == "stop"
        assert data["payload"]["segment_time"] == 300.0

    def test_status_command_serialization(self):
        """Тест сериализации команды status в JSON"""
        cmd = CommandMessage(task_id="task01", cmd="status", payload=None)

        json_str = cmd.model_dump_json()
        data = json.loads(json_str)

        assert data["task_id"] == "task01"
        assert data["cmd"] == "status"
        assert data["payload"] is None


class TestResponseModels:
    """Тесты для Pydantic моделей ответов"""

    def test_start_response_parsing(self):
        """Тест парсинга ответа на команду start"""
        response_data = {
            "task_id": "task01",
            "msg_status": "success",
            "app_status": "started",
            "payload": {
                "file_path": "/mnt/rec001.wav",
                "at_started": "2025-10-15T08:55:00Z",
            },
        }

        response = ResponseMessage(**response_data)

        assert response.task_id == "task01"
        assert response.msg_status == "success"
        assert response.app_status == "started"
        assert response.payload.file_path == "/mnt/rec001.wav"
        assert response.payload.at_started == "2025-10-15T08:55:00Z"

    def test_stop_response_parsing(self):
        """Тест парсинга ответа на команду stop"""
        response_data = {
            "task_id": "task01",
            "msg_status": "success",
            "app_status": "stopped",
            "payload": {
                "segment_time": 300.0,
                "file_path": "/mnt/rec001.wav",
                "at_started": "2025-10-15T08:55:00Z",
                "at_stopped": "2025-10-15T09:00:00Z",
            },
        }

        response = ResponseMessage(**response_data)

        assert response.task_id == "task01"
        assert response.msg_status == "success"
        assert response.app_status == "stopped"
        assert response.payload.segment_time == 300.0
        assert response.payload.file_path == "/mnt/rec001.wav"
        assert response.payload.at_started == "2025-10-15T08:55:00Z"
        assert response.payload.at_stopped == "2025-10-15T09:00:00Z"

    def test_error_response_parsing(self):
        """Тест парсинга ответа с ошибкой"""
        response_data = {
            "task_id": "task01",
            "msg_status": "error",
            "app_status": "error",
            "payload": {},
        }

        response = ResponseMessage(**response_data)

        assert response.task_id == "task01"
        assert response.msg_status == "error"
        assert response.app_status == "error"


class TestNATSCommunication:
    """Тесты для взаимодействия с NATS через ManagerService"""

    @pytest.mark.asyncio
    async def test_send_start_command(self):
        """Тест отправки команды start через NATS"""
        mock_response = ResponseMessage(
            task_id="task01",
            msg_status="success",
            app_status="started",
            payload=ResponsePayload(
                file_path="/mnt/rec001.wav",
                at_started="2025-10-15T08:55:00Z",
            ),
        )

        mock_client = AsyncMock()
        mock_client.send_command.return_value = mock_response

        mock_config = AppConfig(TASK_ID="task01", LOG_LEVEL="INFO")
        service = ManagerService(
            client=mock_client, config=mock_config, nats_subject="rec.control"
        )

        response = await service.start(payload=StartPayload())

        assert response.task_id == "task01"
        assert response.app_status == "started"
        assert response.payload.file_path == "/mnt/rec001.wav"
        mock_client.send_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_stop_command(self):
        """Тест отправки команды stop через NATS"""
        mock_response = ResponseMessage(
            task_id="task01",
            msg_status="success",
            app_status="stopped",
            payload=ResponsePayload(
                segment_time=300.0,
                file_path="/mnt/rec001.wav",
                at_started="2025-10-15T08:55:00Z",
                at_stopped="2025-10-15T09:00:00Z",
            ),
        )

        mock_client = AsyncMock()
        mock_client.send_command.return_value = mock_response

        mock_config = AppConfig(TASK_ID="task01", LOG_LEVEL="INFO")
        service = ManagerService(
            client=mock_client, config=mock_config, nats_subject="rec.control"
        )

        response = await service.stop(payload=StopPayload())

        assert response.task_id == "task01"
        assert response.app_status == "stopped"
        assert response.payload.at_stopped == "2025-10-15T09:00:00Z"
        mock_client.send_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_status_command(self):
        """Тест отправки команды status через NATS"""
        mock_response = ResponseMessage(
            task_id="task01",
            msg_status="success",
            app_status="started",
            payload=ResponsePayload(
                segment_time=300.0,
                file_path="/mnt/rec001.wav",
                at_started="2025-10-15T08:55:00Z",
            ),
        )

        mock_client = AsyncMock()
        mock_client.send_command.return_value = mock_response

        mock_config = AppConfig(TASK_ID="task01", LOG_LEVEL="INFO")
        service = ManagerService(
            client=mock_client, config=mock_config, nats_subject="rec.control"
        )

        response = await service.status()

        assert response.task_id == "task01"
        assert response.app_status == "started"
        assert response.payload.file_path == "/mnt/rec001.wav"
        mock_client.send_command.assert_called_once()


class TestCommandValidation:
    """Тесты для валидации команд"""

    def test_invalid_command_type(self):
        """Тест валидации неверного типа команды"""
        with pytest.raises(Exception):
            CommandMessage(
                task_id="task01",
                cmd="invalid_command",  # Недопустимая команда
                payload=None,
            )

    def test_invalid_msg_status(self):
        """Тест валидации неверного статуса сообщения"""
        with pytest.raises(Exception):
            ResponseMessage(
                task_id="task01",
                msg_status="invalid_status",  # Недопустимый статус
                app_status="started",
                payload=ResponsePayload(),
            )

    def test_invalid_app_status(self):
        """Тест валидации неверного статуса приложения"""
        with pytest.raises(Exception):
            ResponseMessage(
                task_id="task01",
                msg_status="success",
                app_status="invalid_status",  # Недопустимый статус
                payload=ResponsePayload(),
            )
