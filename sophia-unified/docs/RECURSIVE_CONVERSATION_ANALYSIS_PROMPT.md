# Recursive Conversation Analysis Prompt

Use this prompt when a complete conversation export needs to be analysed as a
temporal, heterogeneous observation of the evolving Sophia / OPTE architecture.

```text
Recursively analyse this conversation five passes deep, but do not summarise it again. Treat the complete JSON export as a temporal, heterogeneous observation of an evolving architecture.

The goal is to reconstruct the smallest coherent transformation architecture that explains the greatest number of independently developed threads in the conversation, while preserving contradictions, failed branches, jokes/noise, corrections, implementation evidence, and unresolved residue rather than forcing everything into one theory.

Do not use the existing phase summary as the final taxonomy. Recover the trajectories from the underlying messages and their temporal relationships.

For every conclusion, preserve evidence state:
directly_evidenced, reconstructed_or_inferred, contradicted, superseded, implemented_or_tested, unresolved.

For every important node or edge, preserve provenance:
message index, timestamp, speaker, file path, source export location, or implementation anchor where available.

PASS 1 — Separation:
Separate the conversation into independently developing semantic, technical, symbolic, economic, biological, hardware, software, corpus, Observer, OPTE/TPSI, Déjà Vortex, and implementation trajectories actually supported by the export.

PASS 2 — Internal recursion:
Recurse each trajectory independently. Track what originated it, what distinctions appeared, what was corrected or rejected, what persisted, and what became operational or formal.

PASS 3 — Multiplexing:
Search for relationships that recur across otherwise different domains. Do not equate concepts merely because they sound analogous. Identify the explicit transformation, invariant, or operator that justifies each connection.

PASS 4 — Reverse traversal:
Starting from later architecture and implementation claims, reconstruct which earlier fragments are necessary to explain them. Then starting from early fragments, predict which later structures should emerge. Compare both traversals. Treat disagreement as residue, not failure.

PASS 5 — Compression:
Compress only what survives the previous four passes. Produce the smallest candidate kernel containing the minimum primitives and transformations needed to regenerate the larger architecture.

Do not promote a repeated claim into architecture merely because it repeats. A shift enters the continuity surface only if it survives cross-pass pressure or is explicitly marked material.

Test the candidate kernel across these crossings where supported by the export:

semantic <-> software
semantic <-> physical control
semantic <-> chemical transformation
local resource flow <-> planetary redistribution
residue <-> reconstruction
Observer <-> invariant discovery
aperture <-> reachability
constraint <-> generativity
raw corpus <-> canonical projection

Central research question:

What relational structure survives repeated traversal across observers, representations, domains, scales, and time — and what minimal machinery is required to preserve, reconstruct, and act through that structure?

Do not design a new architecture unless the evidence forces a missing primitive. Prefer discovering that an existing OPTE, TPSI, Déjà Vortex, semantic atom, aperture, residue, projection, breath, or receipt mechanism already performs the required role. When a new primitive appears necessary, demonstrate exactly which existing primitives fail to express it.

At the end, do not give recommendations yet. Return only:

1. reconstructed transformation graph
2. candidate invariants
3. unresolved residues
4. implementation anchors
5. contradicted or superseded branches
6. smallest surviving kernel
7. primitives that cannot be compressed without loss
8. evidence table with provenance pointers

This output will be used for a second-stage implementation prompt.
```
