from __future__ import annotations

import os
import secrets
import uuid
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .state import append_jsonl, now_iso, write_json

app = FastAPI(title="SOPHIAEL Runtime Bridge")
TOKEN = os.getenv("SOPHIAEL_BRIDGE_TOKEN", "")

class Event(BaseModel):
    source: str
    kind: str
    data: dict = Field(default_factory=dict)

class Command(BaseModel):
    action: str
    args: dict = Field(default_factory=dict)
    target: str = "local"


def require_token(auth: str | None) -> None:
    expected = f"Bearer {TOKEN}" if TOKEN else ""
    if not expected or not auth or not secrets.compare_digest(auth, expected):
        raise HTTPException(status_code=401, detail="unauthorized")

@app.get("/health")
def health():
    return {"ok": True, "time": now_iso()}

@app.post("/events")
def receive_event(event: Event, authorization: str | None = Header(default=None)):
    require_token(authorization)
    envelope = {"id": str(uuid.uuid4()), "ts": now_iso(), **event.model_dump()}
    append_jsonl("EVENTS.jsonl", envelope)
    write_json("STATE.json", {"last_event": envelope})
    return envelope

@app.post("/commands")
def enqueue_command(command: Command, authorization: str | None = Header(default=None)):
    require_token(authorization)
    envelope = {"id": str(uuid.uuid4()), "ts": now_iso(), "status": "queued", **command.model_dump()}
    append_jsonl("COMMANDS.jsonl", envelope)
    return envelope
