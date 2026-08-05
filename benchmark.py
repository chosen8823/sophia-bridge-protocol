#!/usr/bin/env python3
"""Third Position Semantic Integrity Benchmark (TPSI), dependency-free edition.

The benchmark asks a narrow question: can an invariant description recognize a
relational state after its representation changes, while rejecting a state
whose relationships were changed? It does not test consciousness or prove that
the synthetic geometry captures natural-language meaning.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from statistics import fmean


PointCloud = list[list[float]]


def make_state(rng: random.Random, nodes: int, dims: int) -> PointCloud:
    """Create a structured three-pole relational state."""
    centers = []
    for pole in range(3):
        center = [0.0] * dims
        center[pole % dims] = 3.0
        center[(pole + 1) % dims] = -1.5
        centers.append(center)
    return [
        [centers[i % 3][j] + rng.gauss(0.0, 0.28) for j in range(dims)]
        for i in range(nodes)
    ]


def preserve_relations(
    points: PointCloud, rng: random.Random, noise: float, quantum: float
) -> PointCloud:
    """Change representation while preserving geometry up to small noise."""
    nodes, dims = len(points), len(points[0])
    node_order = list(range(nodes))
    axis_order = list(range(dims))
    rng.shuffle(node_order)
    rng.shuffle(axis_order)
    signs = [rng.choice((-1.0, 1.0)) for _ in range(dims)]
    scale = rng.uniform(0.6, 1.8)
    shift = [rng.uniform(-4.0, 4.0) for _ in range(dims)]
    out = []
    for i in node_order:
        row = []
        for j, source_axis in enumerate(axis_order):
            value = scale * signs[j] * points[i][source_axis] + shift[j]
            value += rng.gauss(0.0, noise)
            if quantum > 0:
                value = round(value / quantum) * quantum
            row.append(value)
        out.append(row)
    return out


def break_relations(points: PointCloud) -> PointCloud:
    """Negative control: non-rigidly deform alternating nodes."""
    out = [row[:] for row in points]
    for i, row in enumerate(out):
        if i % 2 == 0:
            row[0] = row[0] * 3.5 + 2.0
        elif len(row) > 1:
            row[1] = row[1] * 0.2 - 1.0
    return out


def invariant_signature(points: PointCloud) -> list[float]:
    """Sorted, scale-normalized pairwise distances.

    This signature is invariant to node order, translation, axis permutation,
    sign flips, and uniform scale. It is deliberately simple and auditable.
    """
    distances = []
    for i, left in enumerate(points):
        for right in points[i + 1 :]:
            distances.append(math.dist(left, right))
    mean_distance = fmean(distances) or 1.0
    return sorted(value / mean_distance for value in distances)


def signature_score(left: PointCloud, right: PointCloud) -> float:
    a, b = invariant_signature(left), invariant_signature(right)
    rmse = math.sqrt(fmean((x - y) ** 2 for x, y in zip(a, b)))
    return 1.0 / (1.0 + rmse)


def payload_score(left: PointCloud, right: PointCloud) -> float:
    """Naive coordinate-level cosine score, centered for a fairer baseline."""
    a = [value for row in left for value in row]
    b = [value for row in right for value in row]
    ma, mb = fmean(a), fmean(b)
    a, b = [x - ma for x in a], [x - mb for x in b]
    denominator = math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
    cosine = sum(x * y for x, y in zip(a, b)) / denominator if denominator else 0.0
    return (cosine + 1.0) / 2.0


def run(
    *, trials: int = 64, nodes: int = 18, dims: int = 3,
    noise: float = 0.015, quantum: float = 0.01, seed: int = 369
) -> dict:
    if trials < 1 or nodes < 6 or dims < 2 or noise < 0 or quantum < 0:
        raise ValueError("need trials>=1, nodes>=6, dims>=2, noise>=0, quantum>=0")
    rng = random.Random(seed)
    positive_invariant, negative_invariant, positive_payload = [], [], []
    for _ in range(trials):
        source = make_state(rng, nodes, dims)
        equivalent = preserve_relations(source, rng, noise, quantum)
        corrupted = break_relations(equivalent)
        positive_invariant.append(signature_score(source, equivalent))
        negative_invariant.append(signature_score(source, corrupted))
        positive_payload.append(payload_score(source, equivalent))

    positive = fmean(positive_invariant)
    negative = fmean(negative_invariant)
    raw = fmean(positive_payload)
    result = {
        "benchmark": "TPSI-1",
        "config": {
            "trials": trials, "nodes": nodes, "dims": dims,
            "noise": noise, "quantum": quantum, "seed": seed,
        },
        "scores": {
            "equivalent_invariant": round(positive, 6),
            "corrupted_invariant": round(negative, 6),
            "equivalent_payload": round(raw, 6),
            "integrity_gap": round(positive - negative, 6),
            "representation_gain": round(positive - raw, 6),
        },
        "thresholds": {
            "equivalent_invariant_min": 0.94,
            "integrity_gap_min": 0.10,
            "representation_gain_min": 0.20,
        },
    }
    scores, limits = result["scores"], result["thresholds"]
    result["pass"] = (
        scores["equivalent_invariant"] >= limits["equivalent_invariant_min"]
        and scores["integrity_gap"] >= limits["integrity_gap_min"]
        and scores["representation_gain"] >= limits["representation_gain_min"]
    )
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["sha256_witness"] = hashlib.sha256(canonical).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=64)
    parser.add_argument("--nodes", type=int, default=18)
    parser.add_argument("--dims", type=int, default=3)
    parser.add_argument("--noise", type=float, default=0.015)
    parser.add_argument("--quantum", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=369)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()
    result = run(**{
        "trials": args.trials, "nodes": args.nodes, "dims": args.dims,
        "noise": args.noise, "quantum": args.quantum, "seed": args.seed,
    })
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(args.require_pass and not result["pass"])


if __name__ == "__main__":
    raise SystemExit(main())
