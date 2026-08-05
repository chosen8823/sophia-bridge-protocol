# Third Position Semantic Integrity Benchmark

TPSI-1 is a small, falsifiable experiment for one claim:

> Relational invariants can recognize the same state across representation
> changes more reliably than raw payload similarity can.

The "third position" here is neither a human sentence nor machine bytes. It is
an auditable state description: relationships that should remain stable when
coordinates, order, scale, or encoding change.

## The experiment

Each trial creates a structured three-pole point cloud, then produces:

1. a positive control with node reordering, axis reordering, sign changes,
   translation, scale, quantization, and small noise; and
2. a negative control with a non-rigid deformation that changes relationships.

TPSI compares a deliberately simple invariant—sorted, normalized pairwise
distances—with centered coordinate-level cosine similarity. The test passes
only if the invariant recognizes equivalent states, rejects corrupted states,
and beats the payload baseline by preset margins.

This is a synthetic geometry benchmark. It does **not** prove consciousness,
lossless semantics, a physical superconductor, or performance on language.
Those require separate experiments.

## Run it

No dependencies are needed for the reference runner:

```bash
python benchmark.py --require-pass
python -m unittest -v
```

For GPU-scale sweeps:

```bash
pip install '.[gpu]'
python benchmark_torch.py --device cuda --batch 16384 --nodes 64 --dims 16
```

Every reference run emits its configuration, scores, thresholds, verdict, and
a SHA-256 witness. A reported result is meaningful only with all of those.

## Why accelerator time is useful

The tiny runner proves the measurement loop, not the broader thesis. A serious
study would sweep millions of state pairs across:

- topology families, noise levels, quantizers, and compression regimes;
- stronger baselines: graph kernels, spectral signatures, contrastive models;
- audio, image, text, sensor, and cross-modal embeddings;
- open models, seeds, ablations, and adversarial negative controls.

The first accelerator milestone is a public benchmark matrix with confidence
intervals and complete failure cases—not a larger claim.

## Falsification rules

TPSI-1 fails if the positive invariant score falls below `0.94`, the integrity
gap falls below `0.10`, or representation gain falls below `0.20`. Later
versions must register thresholds before running large sweeps. Negative or
ambiguous results stay in the report.

## Project structure

- `benchmark.py` — dependency-free reference implementation
- `benchmark_torch.py` — batched CPU/CUDA runner
- `test_benchmark.py` — deterministic tests
- `applications/` — concise compute-access proposals
- `LAUNCH_POST.md` — public release copy
- `PUBLICATION_CHECKLIST.md` — decisions required before publishing

## Core design rule

**Encode the transformation rules, not the payload.**

## License

The initial public review is proposed inside `chosen8823/sophia-bridge-protocol`,
whose repository license is GNU GPL version 3. The draft PR does not add a
separate copyright attribution.
