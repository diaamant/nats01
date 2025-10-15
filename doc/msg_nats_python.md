Вот минимальные реализации NATS-клиентов на **Rust** и **Python**, которые используют твои структуры сообщений для обмена через NATS в режиме Request/Reply.


---

## 🐍 Python: GUI-клиент (NiceGUI или FastAPI)

### 📦 Установка

```bash
pip install nats-py pydantic
```

### 🧩 `client.py`

```python
import asyncio
import json
from nats.aio.client import Client as NATS
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

async def send_command():
    nc = NATS()
    await nc.connect("nats://localhost:4222")

    cmd = CommandMessage(
        task_id="task01",
        cmd="status",
        payload=None
    )

    response = await nc.request("rec.control", cmd.json().encode(), timeout=2)
    data = json.loads(response.data.decode())
    reply = ResponseMessage(**data)
    print("Ответ от Rust:", reply)

    await nc.close()

if __name__ == "__main__":
    asyncio.run(send_command())
```

---

## 🧠 Рекомендации

- Тема NATS: `"rec.control"` — можно изменить на `"recording.cmd"` или `"app.control"`.
- Можно добавить логирование, таймауты, JetStream для хранения.
- Rust-сервис можно запускать как systemd-сервис на RK3308B.

Хочешь, я помогу обернуть это в Docker или systemd unit-файл для автозапуска на ARM?