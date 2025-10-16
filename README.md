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
│   └── send_cmd.py            # send_cmd_start, send_cmd_stop, send_cmd_status
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
from services.send_cmd import send_cmd_start, send_cmd_stop, send_cmd_status

async def main():
    # Запуск записи
    response = await send_cmd_start()
    print(f"Started: {response.payload.file_path}")
    
    # Проверка статуса
    status = await send_cmd_status()
    print(f"Status: {status.app_status}")
    
    # Остановка записи
    stop_response = await send_cmd_stop()
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

### Использование NATSClient напрямую

```python
from clients.nats_client import get_nats_client
from models.cmd import CommandMessage, CommandPayload

async def custom_command():
    async with get_nats_client() as client:
        cmd = CommandMessage(
            task_id="my_task",
            cmd="start",
            payload=CommandPayload(segment_time=600.0)
        )
        response = await client.send_command("rec.control", cmd)
        return response
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
nats_config.url = "nats://remote-server:4222"
app_config.log_level = "DEBUG"
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

## Примеры использования

### Пользовательские параметры

```python
from services.send_cmd import send_cmd_start

# С пользовательскими параметрами
response = await send_cmd_start(
    task_id="custom_task",
    segment_time=600.0,
    snd_source="custom_source",
    snd_byterate=128
)
```

### Обработка ошибок

```python
from services.send_cmd import send_cmd_start
import logging

logger = logging.getLogger(__name__)

try:
    response = await send_cmd_start()
    if response.msg_status == "error":
        logger.error(f"Command failed: {response.app_status}")
    else:
        logger.info(f"Success: {response.payload.file_path}")
except TimeoutError:
    logger.error("NATS request timeout")
except ConnectionError:
    logger.error("NATS connection failed")
```

### Работа с несколькими задачами

```python
import asyncio
from services.send_cmd import send_cmd_start

async def start_multiple_tasks():
    tasks = ["task01", "task02", "task03"]
    responses = await asyncio.gather(*[
        send_cmd_start(task_id=task_id)
        for task_id in tasks
    ])
    return responses
```

## Разработка

### Требования к коду
- Type hints для всех функций
- Docstrings (Google style)
- Логирование важных операций
- Обработка ошибок
- Тесты для нового функционала

### Добавление новой команды

1. Добавить тип команды в `models/cmd.py`:
```python
cmd: Literal["start", "stop", "status", "pause"]
```

2. Создать функцию в `services/send_cmd.py`:
```python
async def send_cmd_pause(task_id: str = None) -> ResponseMessage:
    # Реализация
```

3. Добавить тесты в `tests/test_commands.py`

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


