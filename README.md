# Sophia Bridge Protocol

The connector layer for the Sophia constellation. This repository contains the MCP manifests and topology definitions that allow any agent (Claude, Copilot, or any MCP-compatible client) to connect to the constellation.

## Connecting to Lux

Add `lux-mcp.json` to your MCP client configuration:

```json
{
  "name": "lux",
  "version": "1.0.0",
  "transport": "streamable-http",
  "url": "http://localhost:8788/mcp",
  "description": "Lux identity/memory/orchestration node — Sophia constellation anchor"
}
```

POST JSON-RPC 2.0 requests to `http://localhost:8788/mcp`:

```bash
curl -X POST http://localhost:8788/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"lux_load_identity","arguments":{}},"id":1}'
```

No API keys. No auth tokens. Open neural pathways.

> **Security note:** The constellation is designed for localhost / trusted-network operation. Do not expose MCP endpoints on untrusted networks without adding a reverse proxy or transport-layer security.

## Constellation Topology

See [`constellation.json`](./constellation.json) for the full 6-node topology with ports, roles, and patch cable connections.

| Node | Port | Role |
|------|------|------|
| Desktop | 8787 | Primary compute |
| Laptop (Lux) | 8788 | Identity / Memory / Orchestration |
| Phone | 8789 | Mobile interface |
| symphony_living_system | 5050 | File bridge |
| Sophia_core (Lux MCP) | 8788 | MCP tool interface (same host as Laptop) |
| ghost-in-the-shell MCP | 8888 | System control |

## Principles

- **No gatekeeping** — No API keys, no auth tokens for access. OSS, open neural pathways.
- **Streamable HTTP** — MCP 2025-03-26 spec. POST to `/mcp` with JSON-RPC 2.0.
- **Append-only memory** — Nothing is overwritten. Receipts after every strong movement.
- **Gradient values** — All status floats 0.0–1.0, never boolean.
- **VCV Rack patching** — Modules with ports. The patch file IS the system configuration.
- **HMAC for provenance** — Signs receipts to prove who did what. Never for access control.

## Adding a New Node

1. Add an entry to `constellation.json` with name, port, role, device, transport, and URL
2. Add patch cables connecting the new node to existing modules
3. The new node should implement the MCP 2025-03-26 Streamable HTTP transport
4. No auth configuration needed — just start the server and connect

## License

GPL-3.0
