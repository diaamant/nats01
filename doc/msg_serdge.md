Интеграция структур сообщений в **Rust** с помощью `serde` и в **Python** с помощью `pydantic`, чтобы обеспечить надёжную сериализацию/десериализацию JSON при обмене через NATS.

---

## 🦀 Rust: `serde`-структуры

Добавь в `Cargo.toml`:

```toml
[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
```

### 🔹 Команда (GUI → Rust)

```rust
use serde::Deserialize;

#[derive(Debug, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum CommandType {
    Start,
    Stop,
    Status,
}

#[derive(Debug, Deserialize)]
pub struct CommandPayload {
    pub segment_time: Option<f64>,
    pub snd_source: Option<String>,
    pub snd_byterate: Option<u32>,
    pub vid_stream: Option<String>,
    pub vid_byterate: Option<u32>,
}

#[derive(Debug, Deserialize)]
pub struct CommandMessage {
    pub task_id: String,
    pub cmd: CommandType,
    pub payload: Option<CommandPayload>,
}
```

### 🔹 Ответ (Rust → GUI)

```rust
use serde::Serialize;

#[derive(Debug, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum MsgStatus {
    Success,
    Error,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum AppStatus {
    Started,
    Stopped,
    Error,
}

#[derive(Debug, Serialize)]
pub struct ResponsePayload {
    pub segment_time: Option<f64>,
    pub file_path: Option<String>,
    pub at_started: Option<String>,
    pub at_stopped: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct ResponseMessage {
    pub task_id: String,
    pub msg_status: MsgStatus,
    pub app_status: AppStatus,
    pub payload: ResponsePayload,
}
```

---

## 🐍 Python: `pydantic`-модели

Установи:

```bash
pip install pydantic
```

### 🔹 Команда (GUI → Rust)

```python
from pydantic import BaseModel
from typing import Optional, Literal

class CommandPayload(BaseModel):
    segment_time: Optional[float]
    snd_source: Optional[str]
    snd_byterate: Optional[int]
    vid_stream: Optional[str]
    vid_byterate: Optional[int]

class CommandMessage(BaseModel):
    task_id: str
    cmd: Literal["start", "stop", "status"]
    payload: Optional[CommandPayload]
```

### 🔹 Ответ (Rust → GUI)

```python
class ResponsePayload(BaseModel):
    segment_time: Optional[float]
    file_path: Optional[str]
    at_started: Optional[str]
    at_stopped: Optional[str]

class ResponseMessage(BaseModel):
    task_id: str
    msg_status: Literal["success", "error"]
    app_status: Literal["started", "stopped", "error"]
    payload: ResponsePayload
```

---

## 🧪 Пример использования

### Rust: десериализация команды

```rust
let json = r#"{"task_id":"task01","cmd":"start","payload":{"segment_time":300.0}}"#;
let cmd: CommandMessage = serde_json::from_str(json)?;
```

### Python: сериализация ответа

```python
resp = ResponseMessage(
    task_id="task01",
    msg_status="success",
    app_status="started",
    payload=ResponsePayload(
        file_path="/mnt/rec001.wav",
        at_started="2025-10-15T08:55:00Z"
    )
)
json_str = resp.json()
```

---

обернуть это в NATS-клиент на Rust и Python для обмена сообщениями