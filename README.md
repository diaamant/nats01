# NATS01 - NATS Client для управления сторонним приложением

Python-клиент для взаимодействия с Rust-приложением через NATS.

## Описание

Проект предоставляет асинхронный клиент для отправки команд управления через NATS message broker. Поддерживает команды `start`, `stop`, `status`.


## Ключевые особенности

### Best Practices
- **Separation of Concerns** - разделение на clients, models, services
- **DRY** - переиспользование NATS соединения
- **Error Handling** - обработка ошибок подключения и таймаутов
- **Logging** - структурированное логирование
- **Configuration** - через переменные окружения
- **Type Hints** - полная типизация
- **Async/Await** - асинхронная работа с NATS
- **Context Managers** - автоматическое управление ресурсами
- **Testing** - 30+ тестов (unit, integration, real)

### Возможности NATSClient
- Переиспользование соединения
- Контекстный менеджер для автоматического закрытия
- Обработка ошибок (timeout, connection closed)
- Логирование всех операций
- Валидация ответов через Pydantic

## Установка

### Требования
- Python >= 3.12
- NATS сервер (для интеграционных тестов и работы)
- Rust-приложение (для работы с реальным сервером)

### Установка зависимостей

```bash
# Создание виртуального окружения
uv venv

# Активация
source .venv/bin/activate

# Установка зависимостей
uv pip install nats-py pydantic pytest pytest-asyncio
```

### Установка сервера NUTS

```bash
# Debian, Ubuntu
sudo apt install nats-server

sudo systemctl status nats-server.service
```

## Архитектура проекта

```
nats01/
├── clients/                    # NATS клиент
│   ├── __init__.py
│   └── nats_client.py         # NATSClient с переиспользованием соединения
├── core/                       # Ядро приложения
│   ├── __init__.py
│   └── config.py              # Конфигурация приложения
├── models/                     # Pydantic модели
│   └── cmd.py                 # CommandMessage, ResponseMessage
├── services/                   # Бизнес-логика
│   └── send_cmd.py            # ManagerService для управления командами
├── tests/                      # Тесты
│   ├── test_commands.py       # Unit-тесты моделей (15 тестов)
│   ├── test_integration.py    # Интеграционные тесты с моками (5 тестов)
│   ├── test_real_nats.py      # Тесты с реальным NATS (9 тестов)
│   └── README.md              # Документация по тестам
├── doc/                        # Документация
│   └── msg_format.md          # Формат сообщений
├── main.py                     # Точка входа
├── pyproject.toml             # Конфигурация проекта
└── README.md                  # Этот файл
```

## Использование

### Базовое использование

```python
import asyncio
from clients.nats_client import get_nats_client
from core.config import app_config, nats_config
from models.cmd import StartPayload, StopPayload
from services.send_cmd import ManagerService


async def main():
    async with get_nats_client(nats_config.NATS_URL, nats_config.NATS_TIMEOUT) as nats_client:
        # Создаем сервис
        service = ManagerService(
            client=nats_client,
            config=app_config,
            nats_subject=nats_config.NATS_SUBJECT,
        )

        # Запуск записи с кастомными параметрами
        start_params = StartPayload(vid_byterate=2500, segment_time=60)
        response = await service.start(payload=start_params)
        print(f"Started: {response.payload.file_path}")

        # Проверка статуса
        status = await service.status()
        print(f"Status: {status.app_status}")

        # Остановка записи
        stop_response = await service.stop(payload=StopPayload())
        print(f"Stopped at: {stop_response.payload.at_stopped}")


asyncio.run(main())
```

### Запуск из командной строки

```bash
# Активация окружения
source .venv/bin/activate

# Запуск
python main.py
```


### Пользовательские параметры

```python

async def main_async():
    """Async main function to run commands"""
    logger = logging.getLogger(__name__)

    async with get_nats_client(nats_config.NATS_URL, nats_config.NATS_TIMEOUT) as nats_client:
        # Сервис создается один раз и переиспользуется
        recording_service = ManagerService(
            client=nats_client,
            config=app_config,
            nats_subject=nats_config.NATS_SUBJECT,
        )

        try:
            # 1. Определяем кастомные параметры старта записи
            custom_start_params = StartPayload(
                segment_time=600.0,  # Записывать сегменты по 10 минут
                snd_source="microphone_array",  # Кастомный источник звука
                snd_byterate=128,  # Более высокая частота звука
                vid_byterate=3000,  # Высокий битрейт видео
                vid_stream="high_res"  # Кастомный видеопоток
            )

            # 2. Отправляем команду "старт" с кастомными параметрами и кастомным task_id
            logger.info("Sending 'start' command with custom parameters for task 'custom_rec'")
            start_response = await recording_service.start(
                payload=custom_start_params,
                task_id="custom_rec"
            )
            logger.info(f"Start Response: {start_response}")

            # 3. Проверяем статус для кастомной задачи
            logger.info("Sending 'status' command for task 'custom_rec'")
            status_response = await recording_service.status(task_id="custom_rec")
            logger.info(f"Status Response: {status_response}")

            # 4. Отправляем команду "стоп" для кастомной задачи
            logger.info("Sending 'stop' command for task 'custom_rec'")
            stop_response = await recording_service.stop(
                payload=StopPayload(),
                task_id="custom_rec"
            )
            logger.info(f"Stop Response: {stop_response}")

        except Exception as e:
            logger.critical(f"An operation failed in the main workflow: {e}")
```


### Работа с несколькими задачами

```python
async def start_multiple_tasks() -> List[ResponseMessage]:
    """
    Параллельно отправляет команду 'start' для нескольких задач, 
    используя asyncio.gather.
    """
    logger = logging.getLogger(__name__)

    # 1. Получаем NATS-клиент через контекстный менеджер
    async with get_nats_client(nats_config.NATS_URL, nats_config.NATS_TIMEOUT) as client:
        # 2. Инициализируем сервис
        service = ManagerService(
            client=client,
            config=app_config,
            nats_subject=nats_config.NATS_SUBJECT,
        )

        # Список ID задач
        tasks = ["rec_task_A", "rec_task_B", "rec_task_C"]
        logger.info(f"Preparing to start {len(tasks)} tasks concurrently: {tasks}")

        # Параметры по умолчанию, или можно использовать разные для каждой задачи
        default_payload = StartPayload(segment_time=120.0, vid_byterate=2500)

        # 3. Создаем список асинхронных вызовов
        commands = [
            service.start(payload=default_payload, task_id=task_id)
            for task_id in tasks
        ]

        # 4. Параллельно запускаем все команды и ожидаем результаты
        responses = await asyncio.gather(*commands, return_exceptions=True)

        logger.info("--- Results Summary ---")
        for task_id, response in zip(tasks, responses):
            if isinstance(response, ResponseMessage):
                logger.info(
                    f"Task {task_id}: SUCCESS. Status: {response.app_status}, "
                    f"Msg: {response.msg_status}"
                )
            else:
                logger.error(
                    f"Task {task_id}: FAILED. Exception: {response.__class__.__name__}, "
                    f"Message: {response}"
                )
        logger.info("-----------------------")

        return responses
```

## Конфигурация

Настройка через переменные окружения:

```bash
# NATS конфигурация
export NATS_URL="nats://localhost:4222"
export NATS_TIMEOUT="2"
export NATS_SUBJECT="rec.control"

# Приложение
export TASK_ID="task01"
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
```

Или через `core/config.py`:

```python
from core.config import nats_config, app_config

# Изменение конфигурации
nats_config.NATS_URL = "nats://remote-server:4222"
app_config.LOG_LEVEL = "DEBUG"
```

## Формат сообщений

### Команды (Python → Rust)

#### Start
```json
{
  "task_id": "task01",
  "cmd": "start",
  "payload": {
    "segment_time": 300.0,
    "snd_source": "pulsesrc01",
    "snd_byterate": 96,
    "vid_stream": "main",
    "vid_byterate": 2000
  }
}
```

#### Stop
```json
{
  "task_id": "task01",
  "cmd": "stop",
  "payload": {
    "segment_time": 300.0
  }
}
```

#### Status
```json
{
  "task_id": "task01",
  "cmd": "status",
  "payload": null
}
```

### Ответы (Rust → Python)

```json
{
  "task_id": "task01",
  "msg_status": "success",
  "app_status": "started",
  "payload": {
    "segment_time": 300.0,
    "file_path": "/mnt/rec001.wav",
    "at_started": "2025-10-15T08:55:00Z",
    "at_stopped": "2025-10-15T09:00:00Z"
  }
}
```

Подробнее: [`doc/msg_format.md`](doc/msg_format.md)

## Тестирование

### Запуск всех тестов

```bash
source .venv/bin/activate
pytest tests/ -v
```

### Запуск unit-тестов (без NATS сервера)

```bash
pytest tests/test_commands.py tests/test_integration.py -v
```

### Запуск интеграционных тестов (требуется NATS + Rust)

```bash
pytest tests/test_real_nats.py -v -m integration
```

### Покрытие тестами

- **15 тестов** моделей и сериализации
- **5 тестов** интеграционных сценариев
- **9 тестов** с реальным NATS сервером
- Валидация типов команд и ответов
- Обработка ошибок
- Полный цикл: start → status → stop

Подробнее: [`tests/README.md`](tests/README.md)


## Разработка

### Требования к коду
- Type hints для всех функций
- Docstrings (Google style)
- Логирование важных операций
- Обработка ошибок
- Тесты для нового функционала

## Документация

- [`doc/msg_format.md`](doc/msg_format.md) - Формат сообщений
- [`tests/README.md`](tests/README.md) - Документация по тестам
- [`clients/nats_client.py`](clients/nats_client.py) - API NATSClient

## Известные проблемы

### Python 3.13 Threading Warning
```
Exception ignored in: <function _DeleteDummyThreadOnDel.__del__>
TypeError: 'NoneType' object does not support the context manager protocol
```
Это известная проблема Python 3.13 с asyncio/threading при завершении программы. Не влияет на функциональность.

## Лицензия
MIT

## Авторы
Ihar ([GitHub](https://github.com/diaamantkia)) 

## Контакты
diaamantkia@gmail.com

## Вклад
Приветствуются pull requests. Для изменений сначала откройте issue для обсуждения.


