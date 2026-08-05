# Google TPU Research Cloud proposal draft

## Title

Measuring relational integrity across multimodal representation changes

## Abstract

We propose an open benchmark for distinguishing representation changes from
relationship changes. The reference experiment generates structured states,
applies meaning-preserving transformations and topology-breaking negative
controls, and compares raw payload similarity with invariant state
descriptions. TPU access would support large preregistered sweeps across open
multimodal embeddings, topology families, quantization levels, and adversarial
controls. Code, configurations, witnessed outputs, failures, and a technical
report will be released publicly.

## Research questions

1. Which invariant families best separate equivalent states from corrupted
   states under noise, compression, and quantization?
2. Do learned relational encoders generalize to transformations withheld from
   training?
3. Does integrity measured inside one modality predict cross-modal retrieval
   or reconstruction quality?
4. Where do invariant descriptions erase distinctions that humans judge
   meaningful?

## TPU work plan

- Port the batched reference to JAX with deterministic seeds and parity tests.
- Run factorial sweeps across modality, model, transform, corruption, and seed.
- Train compact relational encoders and compare them with graph/spectral
  baselines.
- Publish calibration curves, confidence intervals, ablations, and counterexamples.

## Compute estimate

Initial request: 8 TPU v5e chips for 8 weeks, approximately 10,000 chip-hours.
The plan is elastic; a smaller award would first fund the synthetic and
embedding-only sweeps.

## Open-science commitment

We will publish source code, environment locks, experiment manifests, aggregate
results, representative witnessed outputs, and a report or public blog post.
No claim will exceed the registered scope of the benchmark.

Official program page: https://sites.research.google/trc/
