from typing import Optional, Literal

from pydantic import BaseModel


class CommandPayload(BaseModel):
    segment_time: Optional[float] = None
    snd_source: Optional[str] = None
    snd_byterate: Optional[int] = None
    vid_stream: Optional[str] = None
    vid_byterate: Optional[int] = None


class CommandMessage(BaseModel):
    task_id: str
    cmd: Literal["start", "stop", "status"]
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
    payload: ResponsePayload
