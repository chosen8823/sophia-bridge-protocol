"""Small local coordination hub for the multi-device mesh lab."""
import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", "/data/mesh.db")

def connect():
    db = sqlite3.connect(DB_PATH)
    db.execute("""CREATE TABLE IF NOT EXISTS nodes (
        name TEXT PRIMARY KEY, role TEXT NOT NULL, host TEXT NOT NULL,
        last_seen TEXT NOT NULL, metadata TEXT NOT NULL
    )""")
    return db

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, payload):
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self.reply(200, {"ok": True, "service": "sophia-mesh-hub"})
        if self.path == "/nodes":
            with connect() as db:
                rows = db.execute(
                    "SELECT name, role, host, last_seen, metadata FROM nodes ORDER BY name"
                ).fetchall()
            nodes = [
                {"name": r[0], "role": r[1], "host": r[2], "last_seen": r[3],
                 "metadata": json.loads(r[4])}
                for r in rows
            ]
            return self.reply(200, {"count": len(nodes), "nodes": nodes})
        return self.reply(404, {"error": "not found", "routes": ["/health", "/nodes"]})

    def do_POST(self):
        if self.path != "/heartbeat":
            return self.reply(404, {"error": "not found"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(size))
            name, role = data["name"], data["role"]
            host = self.client_address[0]
            now = datetime.now(timezone.utc).isoformat()
            with connect() as db:
                db.execute(
                    """INSERT INTO nodes(name, role, host, last_seen, metadata)
                       VALUES(?, ?, ?, ?, ?)
                       ON CONFLICT(name) DO UPDATE SET role=excluded.role,
                       host=excluded.host, last_seen=excluded.last_seen,
                       metadata=excluded.metadata""",
                    (name, role, host, now, json.dumps(data.get("metadata", {})))
                )
            return self.reply(200, {"accepted": True, "name": name, "last_seen": now})
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            return self.reply(400, {"error": str(exc)})

    def log_message(self, fmt, *args):
        print("hub:", fmt % args, flush=True)

if __name__ == "__main__":
    host = os.getenv("HUB_HOST", "0.0.0.0")
    port = int(os.getenv("HUB_PORT", "8788"))
    connect().close()
    print(f"mesh hub listening on {host}:{port}", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
