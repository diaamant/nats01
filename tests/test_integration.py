import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.cmd import CommandMessage, CommandPayload, ResponseMessage


class TestIntegrationScenarios:
    """Интеграционные тесты для сценариев работы"""

    @pytest.mark.asyncio
    async def test_full_recording_cycle(self):
        """Тест полного цикла: start -> status -> stop"""

        # 1. Команда START
        start_cmd = CommandMessage(
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

        start_json = start_cmd.model_dump_json()
        assert "start" in start_json

        # Симуляция ответа на START
        start_response_data = {
            "task_id": "task01",
            "msg_status": "success",
            "app_status": "started",
            "payload": {
                "file_path": "/mnt/rec001.wav",
                "at_started": "2025-10-15T08:55:00Z",
            },
        }
        start_response = ResponseMessage(**start_response_data)
        assert start_response.app_status == "started"
        assert start_response.payload.file_path == "/mnt/rec001.wav"

        # 2. Команда STATUS
        status_cmd = CommandMessage(task_id="task01", cmd="status", payload=None)

        status_json = status_cmd.model_dump_json()
        assert "status" in status_json

        # Симуляция ответа на STATUS
        status_response_data = {
            "task_id": "task01",
            "msg_status": "success",
            "app_status": "started",
            "payload": {
                "segment_time": 300.0,
                "file_path": "/mnt/rec001.wav",
                "at_started": "2025-10-15T08:55:00Z",
            },
        }
        status_response = ResponseMessage(**status_response_data)
        assert status_response.app_status == "started"

        # 3. Команда STOP
        stop_cmd = CommandMessage(
            task_id="task01", cmd="stop", payload=CommandPayload(segment_time=300.0)
        )

        stop_json = stop_cmd.model_dump_json()
        assert "stop" in stop_json

        # Симуляция ответа на STOP
        stop_response_data = {
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
        stop_response = ResponseMessage(**stop_response_data)
        assert stop_response.app_status == "stopped"
        assert stop_response.payload.at_stopped == "2025-10-15T09:00:00Z"

    @pytest.mark.asyncio
    async def test_multiple_tasks(self):
        """Тест работы с несколькими задачами"""

        tasks = ["task01", "task02", "task03"]

        for task_id in tasks:
            cmd = CommandMessage(
                task_id=task_id,
                cmd="start",
                payload=CommandPayload(
                    segment_time=300.0, snd_source="pulsesrc01", snd_byterate=96
                ),
            )

            json_data = cmd.model_dump_json()
            assert task_id in json_data

            # Симуляция ответа
            response_data = {
                "task_id": task_id,
                "msg_status": "success",
                "app_status": "started",
                "payload": {
                    "file_path": f"/mnt/rec_{task_id}.wav",
                    "at_started": "2025-10-15T08:55:00Z",
                },
            }
            response = ResponseMessage(**response_data)
            assert response.task_id == task_id
            assert response.payload.file_path == f"/mnt/rec_{task_id}.wav"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Тест обработки ошибок"""

        # Команда, которая вызовет ошибку
        cmd = CommandMessage(
            task_id="task_error",
            cmd="start",
            payload=CommandPayload(
                segment_time=300.0, snd_source="invalid_source", snd_byterate=96
            ),
        )

        # Симуляция ответа с ошибкой
        error_response_data = {
            "task_id": "task_error",
            "msg_status": "error",
            "app_status": "error",
            "payload": {},
        }

        error_response = ResponseMessage(**error_response_data)
        assert error_response.msg_status == "error"
        assert error_response.app_status == "error"

    @pytest.mark.asyncio
    async def test_status_before_start(self):
        """Тест запроса статуса до запуска записи"""

        status_cmd = CommandMessage(task_id="task_new", cmd="status", payload=None)

        # Симуляция ответа - задача не запущена
        response_data = {
            "task_id": "task_new",
            "msg_status": "success",
            "app_status": "stopped",
            "payload": {},
        }

        response = ResponseMessage(**response_data)
        assert response.app_status == "stopped"

    @pytest.mark.asyncio
    async def test_different_segment_times(self):
        """Тест с разными значениями segment_time"""

        segment_times = [60.0, 300.0, 600.0, 1800.0]

        for segment_time in segment_times:
            cmd = CommandMessage(
                task_id="task01",
                cmd="start",
                payload=CommandPayload(
                    segment_time=segment_time, snd_source="pulsesrc01", snd_byterate=96
                ),
            )

            assert cmd.payload.segment_time == segment_time

            json_data = json.loads(cmd.model_dump_json())
            assert json_data["payload"]["segment_time"] == segment_time
