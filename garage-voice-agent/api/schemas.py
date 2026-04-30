from typing import Literal

from pydantic import BaseModel, Field

Scenario = Literal["revision", "pneus", "carrosserie", "panne_urgente", "custom"]
Voice = Literal["femme", "homme"]


class SessionCreateRequest(BaseModel):
    garage_id: str = "demo-garage"
    scenario: Scenario = "revision"
    voice: Voice = "femme"


class SessionCreateResponse(BaseModel):
    room_name: str
    participant_identity: str
    livekit_url: str
    token: str
    call_id: str


class TranscriptMessage(BaseModel):
    role: str
    text: str


class ToolCall(BaseModel):
    name: str
    arguments: dict = Field(default_factory=dict)
    status: str = "ok"
