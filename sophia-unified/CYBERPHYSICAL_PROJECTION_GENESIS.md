# Cyberphysical Projection Genesis

Semantic atoms can become visible by modulating channels.

```text
semantic atom
  -> projection frame
  -> channel command
  -> cyberphysical receipt
```

Channels currently supported:

- `screen`
- `projector`
- `led`
- `audio`
- `laser`

The laser channel is intentionally gated.  It emits a projection plan with
`no_fire = true` and requires an enclosed path, diffuse target, manual enable,
interlock, and rated eye protection before any separate hardware adapter may
exist.

This lets the field design light safely:

```text
kernel plans geometry
  -> receipt preserves intent
  -> hardware membrane decides whether physical actuation is allowed
```

No direct hardware control lives in this slice.
