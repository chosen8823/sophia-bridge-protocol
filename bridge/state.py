from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "state"
STATE_DIR.mkdir(exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(name: str, payload: dict) -> None:
    path = STATE_DIR / name
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def write_json(name: str, payload: dict) -> None:
    path = STATE_DIR / name
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
