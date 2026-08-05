#!/usr/bin/env python3
"""GPU-scale TPSI-1 runner. Requires PyTorch 2.x; uses CUDA when available."""

from __future__ import annotations

import argparse
import json
import time

try:
    import torch
    import torch.nn.functional as F
except ImportError as exc:
    raise SystemExit("Install PyTorch 2.x for the GPU runner: https://pytorch.org/get-started/") from exc


def signatures(states):
    distances = torch.cdist(states, states)
    indices = torch.triu_indices(states.shape[1], states.shape[1], offset=1, device=states.device)
    values = distances[:, indices[0], indices[1]]
    values = values / values.mean(dim=1, keepdim=True).clamp_min(1e-8)
    return values.sort(dim=1).values


def score(left, right):
    rmse = (signatures(left) - signatures(right)).square().mean(dim=1).sqrt()
    return 1.0 / (1.0 + rmse)


def run(batch=4096, nodes=48, dims=8, noise=0.015, quantum=0.01, seed=369, device="auto"):
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(seed)
    if device == "cuda":
        torch.cuda.manual_seed_all(seed)
    dev = torch.device(device)
    base = torch.randn(batch, nodes, dims, device=dev) * 0.28
    centers = torch.zeros(3, dims, device=dev)
    centers[0, 0], centers[0, 1] = 3.0, -1.5
    centers[1, 1], centers[1, 2 % dims] = 3.0, -1.5
    centers[2, 2 % dims], centers[2, 0] = 3.0, -1.5
    base = base + centers[torch.arange(nodes, device=dev) % 3][None, :, :]

    node_order = torch.rand(batch, nodes, device=dev).argsort(dim=1)
    transformed = base.gather(1, node_order[:, :, None].expand(-1, -1, dims))
    axis_order = torch.randperm(dims, device=dev)
    signs = torch.where(torch.rand(dims, device=dev) > 0.5, 1.0, -1.0)
    transformed = transformed[:, :, axis_order] * signs
    scale = torch.empty(batch, 1, 1, device=dev).uniform_(0.6, 1.8)
    shift = torch.empty(batch, 1, dims, device=dev).uniform_(-4.0, 4.0)
    transformed = transformed * scale + shift + torch.randn_like(transformed) * noise
    if quantum > 0:
        transformed = torch.round(transformed / quantum) * quantum
    corrupted = transformed.clone()
    corrupted[:, 0::2, 0] = corrupted[:, 0::2, 0] * 3.5 + 2.0
    corrupted[:, 1::2, 1] = corrupted[:, 1::2, 1] * 0.2 - 1.0

    if dev.type == "cuda":
        torch.cuda.synchronize()
    started = time.perf_counter()
    positive = score(base, transformed)
    negative = score(base, corrupted)
    flat_base = base.flatten(1) - base.flatten(1).mean(dim=1, keepdim=True)
    flat_transformed = transformed.flatten(1) - transformed.flatten(1).mean(dim=1, keepdim=True)
    payload = (F.cosine_similarity(flat_base, flat_transformed, dim=1) + 1.0) / 2.0
    if dev.type == "cuda":
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - started
    pos, neg, raw = positive.mean().item(), negative.mean().item(), payload.mean().item()
    return {
        "benchmark": "TPSI-1-GPU",
        "device": str(dev),
        "config": {"batch": batch, "nodes": nodes, "dims": dims, "noise": noise, "quantum": quantum, "seed": seed},
        "scores": {"equivalent_invariant": pos, "corrupted_invariant": neg, "equivalent_payload": raw,
                   "integrity_gap": pos - neg, "representation_gain": pos - raw},
        "performance": {"seconds": elapsed, "states_per_second": batch * 3 / elapsed},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=4096)
    parser.add_argument("--nodes", type=int, default=48)
    parser.add_argument("--dims", type=int, default=8)
    parser.add_argument("--noise", type=float, default=0.015)
    parser.add_argument("--quantum", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=369)
    parser.add_argument("--device", default="auto")
    print(json.dumps(run(**vars(parser.parse_args())), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
