# Sophia Multi-Device Mesh Lab

A safe, local-first prototype for reconstructing the old multi-device layout.

## What this is

Docker Compose starts five isolated Linux containers that behave like separate computers:

- `hub`: coordination and node registry
- `workstation`: user/workstation identity
- `cloud_agent`: remote-compute identity
- `audio_node`: audio-processing identity (heartbeat only in this first pass)
- `memory_node`: memory/index identity

They share a private Docker bridge network and discover the hub by its service name, `hub`. Only the hub's read-only status endpoint is published to the host, bound to `127.0.0.1`. No node ports are exposed. The network is marked internal, so this prototype has no outbound internet access and no cloud credentials.

These are containers, not full virtual machines, and the roles are emulated—not copies of the historical computers. GitHub stores the reproducible setup; it does not host the running machines.

## Run it

Requires Docker Desktop (or Docker Engine) with the Compose plugin.

```sh
cd multi-device-lab
docker compose up --build -d
docker compose ps
```

Inspect the mesh:

```sh
curl http://127.0.0.1:8788/health
curl http://127.0.0.1:8788/nodes
```

Stop it:

```sh
docker compose down
```

The SQLite registry is stored in the named `mesh_state` volume and survives container restarts. To erase the prototype's registry too, use `docker compose down -v`.

## Network and safety model

The containers can reach each other on `sophia_mesh`; the host can reach the hub on localhost. No SSH daemon, privileged container, host filesystem mount, API key, or external port-forward is configured. Do not put secrets in this repository. Add real provider integrations only after deciding which node may access the internet and which data may cross that boundary.

## Next reconstruction step

Replace the role placeholders with the actual historical services one at a time: first the bridge/API, then memory, then browser or agent workers, and finally audio/MIDI. Keep each service's address, port, protocol, and evidence status documented. This lets us test the architecture without pretending that the original machine configuration has already been recovered.
