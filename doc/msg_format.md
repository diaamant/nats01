структуры сообщений и пояснения, оформленные в Markdown:

---

# 📡 Протокол обмена сообщениями: `Gemeni.md`

## 📤 Команды (GUI → Rust через NATS)

### Общая структура команды

```json
{
  "task_id": "string",
  "cmd": "start|stop|status",
  "payload": {
    // параметры команды, зависят от типа
  }
}
```

### Команда `start`

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

### Команда `stop`

```json
{
  "task_id": "task01",
  "cmd": "stop",
  "payload": {
    "segment_time": 300.0
  }
}
```

### Команда `status`

```json
{
  "task_id": "task01",
  "cmd": "status"
}
```

---

## 📥 Ответы (Rust → GUI через NATS)

### Общая структура ответа

```json
{
  "task_id": "string",
  "msg_status": "success|error",
  "app_status": "started|stopped|error",
  "payload": {
    // параметры результата
  }
}
```

### Ответ на `start`

```json
{
  "task_id": "task01",
  "msg_status": "success",
  "app_status": "started",
  "payload": {
    "file_path": "/mnt/rec001.wav",
    "at_started": "2025-10-15T08:55:00Z"
  }
}
```

### Ответ на `stop`

```json
{
  "task_id": "task01",
  "msg_status": "success",
  "app_status": "stopped",
  "payload": {
    "segment_time": 300.0,
    "file_path": "/mnt/rec001.wav",
    "at_started": "2025-10-15T08:55:00Z",
    "at_stopped": "2025-10-15T09:00:00Z"
  }
}
```

### Ответ на `status` (запись идёт)

```json
{
  "task_id": "task01",
  "msg_status": "success",
  "app_status": "started",
  "payload": {
    "segment_time": 300.0,
    "file_path": "/mnt/rec001.wav",
    "at_started": "2025-10-15T08:55:00Z",
    "at_stopped": ""
  }
}
```

### Ответ на `status` (запись завершена)

```json
{
  "task_id": "task01",
  "msg_status": "success",
  "app_status": "stopped",
  "payload": {
    "segment_time": 300.0,
    "file_path": "/mnt/rec001.wav",
    "at_started": "2025-10-15T08:55:00Z",
    "at_stopped": "2025-10-15T09:00:00Z"
  }
}
```

---

## 🧠 Пояснения

- `task_id`: уникальный идентификатор запроса.
- `cmd`: команда управления — `"start"`, `"stop"`, `"status"`.
- `msg_status`: результат обработки сообщения — `"success"` или `"error"`.
- `app_status`: состояние записи — `"started"`, `"stopped"`, `"error"`.
- `payload`: параметры команды или результата, включая таймстемпы и путь к файлу.

---

