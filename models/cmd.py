from typing import Optional, Literal

from pydantic import BaseModel


class CommandPayload(BaseModel):
    segment_time: Optional[float] = None
    snd_source: Optional[str] = None
    snd_byterate: Optional[int] = None
    vid_stream: Optional[str] = None
    vid_byterate: Optional[int] = None


class StartPayload(CommandPayload):
    segment_time: float = 300.0
    snd_source: str = "pulsesrc01"
    snd_byterate: int = 96
    vid_stream: str = "main"
    vid_byterate: int = 2000


class StopPayload(CommandPayload):
    segment_time: float = 300.0


cmd_type = Literal["start", "stop", "status"]


class CommandMessage(BaseModel):
    task_id: str
    cmd: cmd_type
    payload: Optional[CommandPayload]


class ResponsePayload(BaseModel):
    segment_time: Optional[float] = None
    file_path: Optional[str] = None
    at_started: Optional[str] = None
    at_stopped: Optional[str] = None


class ResponseMessage(BaseModel):
    task_id: str
    msg_status: Literal["success", "error"]
    app_status: Literal["started", "stopped", "error"]
    payload: Optional[ResponsePayload]
