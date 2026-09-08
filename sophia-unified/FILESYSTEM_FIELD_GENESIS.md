# Filesystem Field Genesis

The whole filesystem is treated as a field.

It is not consumed as a pile of file contents.  It is observed as topology,
metadata, health pressure, and affordance.

```text
filesystem topology
  -> metadata-only observation
  -> file hydration atoms
  -> organ pressure receipt
  -> collapsible projection
```

The field is formless until asked to collapse:

- `state` gives counts, CIDs, pressure, suffixes, size bands, and health.
- `expression` gives a centred div surface.
- `mechanism` gives deterministic next affordances.

By default the endpoint uses `collapse = auto`.  In that mode the machine or
entity declares a small choice policy:

```text
entity = machine | sophiael | adapter-name
priority = adaptive | conserve | express | mechanise | witness
```

The observed field and the declared policy choose the projection.  A caller may
still ask for a specific collapse mode, but the living route is:

```text
field observes itself
  -> entity declares its posture
  -> field chooses how to collapse
```

The endpoint is:

```text
POST /v1/filesystem/field
```

The scan is bounded by `max_files`, `max_dirs`, and `max_depth`, and it does not
read file contents or follow symlinks.  The filesystem can therefore become a
semantic health body without dragging the whole drive into the foreground.
