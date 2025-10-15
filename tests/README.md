# Тесты для NATS01

## Структура тестов

### `test_commands.py`
Модульные тесты для проверки:
- **TestCommandModels**: создание и сериализация команд (start, stop, status)
- **TestResponseModels**: парсинг ответов от Rust-приложения
- **TestNATSCommunication**: взаимодействие с NATS (с моками)
- **TestCommandValidation**: валидация входных данных

### `test_integration.py`
Интеграционные тесты для проверки:
- Полного цикла работы (start → status → stop)
- Работы с несколькими задачами
- Обработки ошибок
- Различных параметров команд

### `test_real_nats.py`
Интеграционные тесты с реальным NATS и Rust-приложением:
- **TestRealNATSIntegration**: проверка реальных ответов от Rust-приложения
- **TestRealNATSErrorHandling**: проверка обработки ошибочных сценариев

⚠️ **Требования для запуска**: запущенный NATS сервер и Rust-приложение

## Запуск тестов

### Установка зависимостей
```bash
pip install pytest pytest-asyncio nats-py pydantic
```

### Запуск всех тестов
```bash
pytest tests/
```

### Запуск с подробным выводом
```bash
pytest tests/ -v
```

### Запуск конкретного файла
```bash
pytest tests/test_commands.py -v
```

### Запуск конкретного теста
```bash
pytest tests/test_commands.py::TestCommandModels::test_start_command_creation -v
```

### Запуск интеграционных тестов с реальным NATS
```bash
source .venv/bin/activate
pytest tests/test_real_nats.py -v -m integration
```

### Запуск только unit-тестов (без реального NATS)
```bash
source .venv/bin/activate
pytest tests/test_commands.py tests/test_integration.py -v
```

### Запуск с покрытием кода
```bash
source .venv/bin/activate
pytest tests/ -v
```

## Покрытие тестами

### Unit-тесты (test_commands.py, test_integration.py)
- ✅ Создание команд start, stop, status
- ✅ Сериализацию команд в JSON
- ✅ Парсинг ответов от сервера
- ✅ Валидацию типов команд и статусов
- ✅ Полный цикл работы с записью
- ✅ Обработку ошибок
- ✅ Работу с несколькими задачами

### Интеграционные тесты (test_real_nats.py)
- ✅ Проверку реальных ответов от Rust-приложения
- ✅ Валидацию структуры ответов (task_id, msg_status, app_status, payload)
- ✅ Проверку формата временных меток (ISO 8601)
- ✅ Проверку формата путей к файлам
- ✅ Согласованность данных между командами
- ✅ Полный цикл: start → status → stop с реальным сервером
- ✅ Обработку граничных случаев (повторный start, stop без start)

## Примечания

- **Unit-тесты** (`test_commands.py`, `test_integration.py`) используют моки для NATS, поэтому не требуют запущенного NATS-сервера
- **Интеграционные тесты** (`test_real_nats.py`) требуют:
  - Запущенный NATS сервер на `localhost:4222`
  - Запущенное Rust-приложение, слушающее канал `rec.control`
- Все асинхронные тесты помечены декоратором `@pytest.mark.asyncio`
- Интеграционные тесты помечены маркером `@pytest.mark.integration`

## Структура тестов

```
tests/
├── __init__.py
├── test_commands.py       # Unit-тесты моделей и сериализации (15 тестов)
├── test_integration.py    # Интеграционные тесты с моками (5 тестов)
├── test_real_nats.py      # Тесты с реальным NATS и Rust (10 тестов)
└── README.md              # Документация
```
