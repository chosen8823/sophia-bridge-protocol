# Sophia Filesystem Ingestion Daemon

`bridge/ingestor.py` implements the carrier membrane:

```text
CONTACT -> HOLD -> INTERPRET -> WRAP -> RETURN
```

It watches or scans `inbox/`, computes the raw file SHA-256, classifies the
carrier, emits a canonical JSONL event into `state/EVENTS.jsonl`, and can
optionally move the carrier into `archive/`.

Important kernel choices:

- event identity is content-addressed, not UUID-based;
- replay uses local ledger epochs, not wall-clock timestamps;
- canonical events reject floats and raw bytes;
- payload content is not copied into the event;
- archival is opt-in;
- continuous daemon mode is available, but `--once` is the preferred test path.

Example:

```powershell
cd C:\Users\chose\sophia-unified
C:\Python313\python.exe bridge\ingestor.py --once
```

Focused verification:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
C:\Python313\python.exe -m pytest tests\test_filesystem_ingestor.py -q
```
