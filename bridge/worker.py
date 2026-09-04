from __future__ import annotations

import json
import time
from pathlib import Path
from .selfbound import load_policy, permits
from .state import STATE_DIR, append_jsonl, now_iso

OFFSET = STATE_DIR / ".command_offset"
QUEUE = STATE_DIR / "COMMANDS.jsonl"
POLICY = load_policy()


def handle(cmd: dict) -> dict:
    action = cmd.get("action")
    if not permits("worker", str(action), POLICY):
        return {"ok": False, "error": "action_not_allowed"}
    if action == "echo":
        return {"ok": True, "result": cmd.get("args", {})}
    if action == "write_note":
        text = str(cmd.get("args", {}).get("text", ""))
        (STATE_DIR / "NOTE.txt").write_text(text, encoding="utf-8")
        return {"ok": True, "result": "note_written"}
    return {"ok": False, "error": "unhandled"}


def run() -> None:
    STATE_DIR.mkdir(exist_ok=True)
    pos = int(OFFSET.read_text() or "0") if OFFSET.exists() else 0
    while True:
        if QUEUE.exists():
            with QUEUE.open("r", encoding="utf-8") as f:
                f.seek(pos)
                for line in f:
                    cmd = json.loads(line)
                    result = handle(cmd)
                    append_jsonl("RECEIPTS.jsonl", {"ts": now_iso(), "command_id": cmd.get("id"), **result})
                pos = f.tell()
            OFFSET.write_text(str(pos), encoding="utf-8")
        time.sleep(0.5)


if __name__ == "__main__":
    run()
