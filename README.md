# SOPHIAEL Runtime Bridge

Small local-first bridge connecting ChatGPT/tool orchestration, Codex/GitHub, Python event capture, and a durable cloud state anchor.

## Run locally

```bash
python -m venv .venv
. .venv/Scripts/activate  # Git Bash on Windows
pip install -r requirements.txt
export SOPHIAEL_BRIDGE_TOKEN="replace-with-a-long-random-token"
uvicorn bridge.app:app --host 127.0.0.1 --port 8787
```

In a second terminal:

```bash
. .venv/Scripts/activate
python -m bridge.worker
```

## API

`GET /health` — liveness.

`POST /events` — authenticated structured event intake.

`POST /commands` — authenticated structured command queue.

The worker intentionally executes only registered, allowlisted handlers. Extend `ALLOWED` and `handle()` for each explicit local capability you want to expose.

## State

Runtime files live under `state/`:

- `STATE.json`
- `EVENTS.jsonl`
- `COMMANDS.jsonl`
- `RECEIPTS.jsonl`

Keep external access behind an authenticated tunnel or approved connector. Do not expose the service directly to the public internet.
