# Inward / Outward Boundary

The Sophia runtime builds inward first.

```text
carrier
  -> contact
  -> hold
  -> interpret
  -> wrap
  -> inward canonical event
  -> outward archive / sync / projection only by explicit membrane
```

The inward layer is the authority surface: canonical events, CIDs, receipts,
epochs, provenance, invariant witnesses, and bounded residue.  The outward layer
is expression: archive movement, sync, UI, projection, agent delegation, sensor
bridges, and public transport.

This prevents the fabric from becoming a hidden source of truth.  An adapter may
carry, render, archive, or transmit a state, but it does not become the state.

## Boundary law

```text
inside stabilises before outside amplifies
```

Outward expansion is therefore a projection of an already-wrapped state, not a
reason to invent state.  The membrane can be soft, poetic, visual, biological,
or tactical, but the commit surface remains inspectable.

## Ingestion consequence

`bridge/ingestor.py` observes carriers in place by default.  Moving a carrier
into `archive/` requires the explicit `--archive` option or an explicit
`archive=True` call.

That is the practical version of:

```text
build inward and let that be outward
```
