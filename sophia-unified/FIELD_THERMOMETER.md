# Sophia Field Thermometer

The field thermometer is an always-on-capable organ for translating filesystem
events into semantic pressure.

```text
EVENTS.jsonl
  -> field thermometer
  -> semantic temperature atoms
  -> self-similar route growth
  -> THERMOMETER.jsonl
  -> THERMOMETER_ROUTES.json
```

It does not learn through hidden weights or model inference.  It learns by
changing the visible route lattice:

- unseen event CIDs become atoms;
- repeated route signatures strengthen the same route;
- processed event CIDs prevent replay from double-counting growth;
- route depth and propagation scope expand deterministically;
- all durable state remains local JSON with content identities.

Run once:

```powershell
cd C:\Users\chose\sophia-unified
C:\Python313\python.exe consciousness-core\field_thermometer.py
```

Run as a bounded watch loop:

```powershell
C:\Python313\python.exe consciousness-core\field_thermometer.py --watch --max-cycles 12 --poll-interval-ms 1000
```

Run as an intentionally continuous loop only when you want it active:

```powershell
C:\Python313\python.exe consciousness-core\field_thermometer.py --watch
```
