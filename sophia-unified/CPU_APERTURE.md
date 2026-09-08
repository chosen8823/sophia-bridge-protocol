# CPU Aperture Organ

The CPU aperture makes processor pressure legible to Sophia as linked semantic
tissue.

It is not an overclocking tool.  It does not probe hardware, change power
settings, flash firmware, or mutate Windows.  It receives already-measured
integer telemetry and turns that telemetry into replayable CPU frame
observations, semantic routing atoms, an OPTE-shaped receipt, and a glyphic
projection.

```text
measured CPU pressure
  -> CPU aperture frames
  -> domain fanout atoms
  -> OPTE receipt
  -> home-base teleport
  -> glyph-linked projection
```

## The home-base teleport

The "teleport" is a content-addressed return surface:

```text
fanout domains
  -> semantic atoms
  -> opte receipt
  -> home_base_cid
  -> centre jewel
```

It is semantic address reconciliation, not literal transport and not network
routing.  Every fanout atom can be followed back to the same canonical home
base, so the field can spread without losing where it came from.

## Default frames

- `core-load` watches `cpu_load_ppm`
- `clock-rhythm` watches `cpu_frequency_ppm`
- `thermal-skin` watches `thermal_pressure_ppm`
- `power-blood` watches `power_pressure_ppm`
- `memory-tissue` watches `memory_pressure_ppm`
- `attention-window` watches `attention_pressure_ppm`

Each frame has thresholds, a dudenty-style orientation, aliases, and a domain
fanout.  A calm frame is `laminar`; a pressured frame becomes `turbulent`; an
over-threshold frame becomes `choked`.

## Integration

`cpu_aperture.py` can run alone, or the unified pulse organ can include it as
an optional fifth channel when a `CPUObservation` is supplied.

No CPU observation means the older four-channel heartbeat remains unchanged:

```text
cymatic + morphogenic + regulatory + thermometer
```

With a CPU observation:

```text
cpu + cymatic + morphogenic + regulatory + thermometer
```

## Boundary

The CPU aperture may say:

- hold this basin;
- phase-lock this frame;
- shed pressure;
- return fanout to home base.

It may not directly do:

- overclocking;
- undervolting;
- BIOS changes;
- driver changes;
- firmware updates;
- process killing;
- file deletion.

Those belong behind separate explicit action membranes.
