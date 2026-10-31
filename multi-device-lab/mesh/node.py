"""Heartbeat agent representing one isolated computer in the mesh."""
import argparse
import json
import os
import platform
import time
import urllib.request
import uuid

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", default="worker")
    args = parser.parse_args()
    name = os.getenv("NODE_NAME", f"{args.role}-{platform.node()}")
    hub = os.getenv("HUB_URL", "http://hub:8788").rstrip("/")
    interval = float(os.getenv("HEARTBEAT_SECONDS", "5"))
    instance = str(uuid.uuid4())
    payload = {
        "name": name,
        "role": args.role,
        "metadata": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "instance_id": instance,
            "capabilities": ["heartbeat", "mesh-discovery"]
        }
    }
    body = json.dumps(payload).encode()
    print(f"{name} ({args.role}) joining {hub}", flush=True)
    while True:
        try:
            req = urllib.request.Request(
                hub + "/heartbeat", data=body,
                headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                print(response.read().decode(), flush=True)
        except Exception as exc:
            print(f"heartbeat failed: {exc}", flush=True)
        time.sleep(interval)

if __name__ == "__main__":
    main()
