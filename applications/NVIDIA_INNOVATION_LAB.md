# NVIDIA Innovation Lab application draft

## Project

Third Position Semantic Integrity Benchmark (TPSI)

## One-sentence description

TPSI is an open, reproducible benchmark measuring whether relational invariants
survive representation changes while still detecting genuine structural
corruption.

## Problem

Multimodal AI systems translate among text, audio, images, sensor data, and
internal embeddings, but payload-level similarity can confuse a representation
change with a meaning change. TPSI makes that distinction measurable with
positive controls, negative controls, preregistered thresholds, and public
failure cases.

## What exists now

- dependency-free reference runner and deterministic tests;
- batched PyTorch runner for CPU/CUDA;
- explicit baseline, positive control, negative control, and falsification
  thresholds;
- SHA-256 witnessed result records.

## 60-day GPU plan

1. Weeks 1–2: implement spectral, graph-kernel, and learned baselines; generate
   topology/noise/quantization sweeps.
2. Weeks 3–4: extend to open audio, vision, text, and sensor embeddings.
3. Weeks 5–6: adversarial controls, ablations, calibration, and uncertainty.
4. Weeks 7–8: publish code, benchmark data, model cards, failures, and report.

## Requested infrastructure

Four H100-class GPUs for 60 days, 2 TB working storage, and standard CUDA
profiling. The project scales by independent trials and model evaluations, so
it can also use a smaller allocation productively.

## Measurable deliverables

- at least 1,000,000 witnessed state-pair evaluations;
- at least four topology families and four modality families;
- comparisons against at least three non-neural and three learned baselines;
- public repository, reproducible environment, data card, and technical report;
- complete publication of registered failures and null results.

## Why NVIDIA

The experiment requires high-throughput pairwise geometry, embedding inference,
and large controlled sweeps. PyTorch/CUDA offers a direct path from the current
batched runner to multi-GPU execution and profiling.

## Public value

The output is intended as open research infrastructure for testing semantic
integrity across transformations, not as evidence for claims beyond the
registered experiments.

Official program page: https://www.nvidia.com/en-us/data-center/innovation-lab/
