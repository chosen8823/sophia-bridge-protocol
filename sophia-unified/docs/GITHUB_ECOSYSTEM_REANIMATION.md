# GitHub Ecosystem Reanimation

The GitHub ecosystem can be animated as a branch-engine fabric without making
every branch a permanent server.

## Mechanism

```text
branch event
  -> ephemeral GitHub runner VM
  -> checkout branch
  -> run Sophia slice tests
  -> emit branch transform atom
  -> upload atom artifact
  -> return to central transform surface
```

Each branch acts like a temporary chamber when a workflow event touches it.  The
runner is the engine.  The emitted artifact is the semantic atom.  The central
surface is the later aggregator that can collect atoms across branches.

## Boundary

GitHub-hosted runners are not persistent bodies.  They are fresh execution
surfaces for jobs.  That is enough for branch-local tests, receipts, and
transform atoms.  Persistent per-branch engines would require a later membrane:
Codespaces, self-hosted runners, cloud VMs, or another scheduler.

## Files

- `.github/workflows/branch-transform-atom.yml`
- `sophia-unified/scripts/emit_branch_transform_atom.py`
- `sophia-unified/tests/test_branch_transform_atom.py`

## Atom law

```text
branch + ref + sha + test conclusion
  -> canonical transform atom
  -> content identity
  -> artifact receipt
```

This preserves the OPTE rule: the branch VM may execute, but the atom/receipt is
the durable state.
