"""Filesystem field membrane.

The filesystem can be treated as a formless semantic field that collapses into
different expressions on demand:

* state: compact counts, CIDs, pressures, and topology health
* expression: a centred HTML/textual pulse surface
* mechanism: deterministic next affordances for adapters to consider

Scanning is metadata-only.  The membrane never reads file contents, never
mutates paths, and never follows symlinks.  It hydrates observed files through
the file-hydration atom layer and emits an OPTE-shaped receipt.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from file_hydrator import FileSignal, hydrate_files, path_motifs, size_band
from regulatory_organs import Primitive, cid_for, pulse_garden


class FilesystemFieldError(ValueError):
    """Stable machine-readable error for filesystem field failures."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


DEFAULT_EXCLUDE_NAMES = (
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "site-packages",
    "$Recycle.Bin",
    "System Volume Information",
)


@dataclass(frozen=True)
class FilesystemScanConfig:
    root_path: str
    max_files: int = 256
    max_dirs: int = 512
    max_depth: int = 4
    include_hidden: bool = False
    exclude_names: tuple[str, ...] = DEFAULT_EXCLUDE_NAMES

    def to_primitive(self) -> dict[str, Primitive]:
        if self.max_files <= 0:
            raise FilesystemFieldError("FS_MAX_FILES_REJECTED", "max_files must be positive")
        if self.max_dirs <= 0:
            raise FilesystemFieldError("FS_MAX_DIRS_REJECTED", "max_dirs must be positive")
        if self.max_depth < 0:
            raise FilesystemFieldError("FS_MAX_DEPTH_REJECTED", "max_depth must be zero or positive")
        return {
            "kind": "filesystem_scan_config_v1",
            "root_path": self.root_path.replace("\\", "/"),
            "max_files": self.max_files,
            "max_dirs": self.max_dirs,
            "max_depth": self.max_depth,
            "include_hidden": self.include_hidden,
            "exclude_names": sorted(set(self.exclude_names)),
        }


@dataclass(frozen=True)
class FilesystemObservation:
    root_hint: str
    dirs_seen: tuple[str, ...]
    file_signals: tuple[FileSignal, ...]
    inaccessible: tuple[str, ...]
    truncated: bool
    config_cid: str

    def to_primitive(self) -> dict[str, Primitive]:
        return {
            "kind": "filesystem_observation_v1",
            "root_hint": self.root_hint,
            "dirs_seen": list(self.dirs_seen),
            "file_signal_cids": [signal.cid for signal in self.file_signals],
            "inaccessible": list(self.inaccessible),
            "truncated": self.truncated,
            "config_cid": self.config_cid,
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


@dataclass(frozen=True)
class EntityChoicePolicy:
    """Declared local preference for how an entity collapses a field."""

    entity: str = "machine"
    priority: str = "adaptive"

    def to_primitive(self) -> dict[str, Primitive]:
        if self.priority not in {"adaptive", "conserve", "express", "mechanise", "witness"}:
            raise FilesystemFieldError(
                "FS_POLICY_REJECTED",
                "priority must be adaptive, conserve, express, mechanise, or witness",
            )
        return {
            "kind": "entity_choice_policy_v1",
            "entity": self.entity,
            "priority": self.priority,
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


def _is_hidden(name: str) -> bool:
    return name.startswith(".") or name.startswith("$")


def _safe_hint(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return path.name


def scan_filesystem(config: FilesystemScanConfig) -> FilesystemObservation:
    """Scan one local root as metadata-only topology with hard budgets."""

    primitive_config = config.to_primitive()
    root = Path(config.root_path)
    if not root.exists():
        raise FilesystemFieldError("FS_ROOT_MISSING", f"root path does not exist: {config.root_path}")
    if not root.is_dir():
        raise FilesystemFieldError("FS_ROOT_NOT_DIRECTORY", f"root path is not a directory: {config.root_path}")

    resolved_root = root.resolve()
    exclude = set(config.exclude_names)
    dirs_seen: list[str] = []
    inaccessible: list[str] = []
    file_signals: list[FileSignal] = []
    truncated = False
    stack: list[tuple[Path, int]] = [(resolved_root, 0)]

    while stack:
        current, depth = stack.pop()
        if len(dirs_seen) >= config.max_dirs:
            truncated = True
            break
        hint = "." if current == resolved_root else _safe_hint(current, resolved_root)
        dirs_seen.append(hint)

        try:
            entries = sorted(os.scandir(current), key=lambda entry: entry.name.lower())
        except OSError:
            inaccessible.append(hint)
            continue

        child_dirs: list[Path] = []
        for entry in entries:
            name = entry.name
            if name in exclude:
                continue
            if not config.include_hidden and _is_hidden(name):
                continue
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if depth < config.max_depth:
                        child_dirs.append(Path(entry.path))
                    continue
                if entry.is_file(follow_symlinks=False):
                    if len(file_signals) >= config.max_files:
                        truncated = True
                        continue
                    stat = entry.stat(follow_symlinks=False)
                    path = Path(entry.path)
                    file_signals.append(
                        FileSignal(
                            path_hint=_safe_hint(path, resolved_root),
                            suffix=path.suffix,
                            size_bytes=stat.st_size,
                            modified_ns=stat.st_mtime_ns,
                            source="filesystem_field",
                            realm="digital",
                            tags=path_motifs(_safe_hint(path, resolved_root)),
                        )
                    )
            except OSError:
                inaccessible.append(_safe_hint(Path(entry.path), resolved_root))

        for child in reversed(child_dirs):
            stack.append((child, depth + 1))

    return FilesystemObservation(
        root_hint=str(primitive_config["root_path"]),
        dirs_seen=tuple(dirs_seen),
        file_signals=tuple(sorted(file_signals, key=lambda item: item.path_hint)),
        inaccessible=tuple(sorted(set(inaccessible))),
        truncated=truncated,
        config_cid=cid_for(primitive_config),
    )


def _count_by(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _filesystem_pressure(observation: FilesystemObservation) -> dict[str, int]:
    file_count = len(observation.file_signals)
    dir_count = len(observation.dirs_seen)
    inaccessible_count = len(observation.inaccessible)
    filesystem_pressure = min(
        1_000_000,
        (400_000 if observation.truncated else 0)
        + inaccessible_count * 100_000
        + (250_000 if file_count == 0 else 0),
    )
    memory_pressure = min(1_000_000, file_count * 1_500 + dir_count * 750)
    process_pressure = min(1_000_000, dir_count * 1_000 + inaccessible_count * 50_000)
    attention_pressure = min(1_000_000, len(_count_by(signal.suffix.lower() for signal in observation.file_signals)) * 40_000)
    return {
        "filesystem_pressure_ppm": filesystem_pressure,
        "memory_pressure_ppm": memory_pressure,
        "process_pressure_ppm": process_pressure,
        "attention_pressure_ppm": attention_pressure,
    }


def choose_collapse(
    observation: FilesystemObservation,
    policy: EntityChoicePolicy | None = None,
) -> str:
    """Let the declared entity policy choose the field projection."""

    active_policy = policy or EntityChoicePolicy()
    active_policy.to_primitive()
    if active_policy.priority == "conserve":
        return "state"
    if active_policy.priority == "express":
        return "expression"
    if active_policy.priority == "mechanise":
        return "mechanism"
    if active_policy.priority == "witness":
        return "state"
    if observation.truncated or observation.inaccessible:
        return "mechanism"
    suffix_count = len({signal.suffix.lower() for signal in observation.file_signals})
    if suffix_count >= 4:
        return "expression"
    return "state"


def collapse_filesystem_field(
    observation: FilesystemObservation,
    collapse: str = "state",
    aperture: str = "opte:filesystem_field_v1",
    policy: EntityChoicePolicy | None = None,
) -> dict[str, Primitive]:
    """Collapse a formless filesystem observation into a requested projection."""

    if collapse == "auto":
        collapse = choose_collapse(observation, policy)
    if collapse not in {"state", "expression", "mechanism"}:
        raise FilesystemFieldError("FS_COLLAPSE_REJECTED", "collapse must be state, expression, mechanism, or auto")

    suffix_counts = _count_by(signal.suffix.lower() or "<none>" for signal in observation.file_signals)
    size_bands = _count_by(size_band(signal.size_bytes) for signal in observation.file_signals)
    hydration = hydrate_files(observation.file_signals, aperture="opte:file_hydration_v1")
    pressure = _filesystem_pressure(observation)
    organ_receipt = pulse_garden(pressure)
    base = {
        "kind": "filesystem_field_receipt_v1",
        "aperture": aperture,
        "collapse": collapse,
        "observation_cid": observation.cid,
        "config_cid": observation.config_cid,
        "root_hint": observation.root_hint,
        "files_observed": len(observation.file_signals),
        "dirs_observed": len(observation.dirs_seen),
        "inaccessible_count": len(observation.inaccessible),
        "truncated": observation.truncated,
        "chosen_by": (policy or EntityChoicePolicy()).to_primitive() if policy is not None or collapse else None,
        "suffix_counts": suffix_counts,
        "size_bands": size_bands,
        "pressure": pressure,
        "hydration_root_cid": hydration["root_cid"],
        "organ_receipt_cid": organ_receipt.cid,
        "settlement_surface": "ground",
        "altitude": "air",
    }
    if collapse == "expression":
        projection: Primitive = (
            "<div data-sophia-filesystem=\"field\" "
            f"data-observation=\"{observation.cid}\" "
            f"data-hydration=\"{hydration['root_cid']}\" "
            "style=\"display:grid;place-items:center;min-height:100vh;\">"
            f"<pre>FILESYSTEM FIELD\\nfiles:{len(observation.file_signals)} "
            f"dirs:{len(observation.dirs_seen)} truncated:{str(observation.truncated).lower()}</pre>"
            "</div>"
        )
    elif collapse == "mechanism":
        actions: list[str] = []
        if observation.truncated:
            actions.append("increase_budget_or_narrow_root")
        if observation.inaccessible:
            actions.append("mark_inaccessible_paths_as_residual")
        if suffix_counts.get(".py", 0):
            actions.append("route_python_to_code_aperture")
        if suffix_counts.get(".md", 0) or suffix_counts.get(".txt", 0):
            actions.append("route_text_to_document_aperture")
        if suffix_counts.get(".json", 0) or suffix_counts.get(".jsonl", 0):
            actions.append("route_json_to_canonical_data_aperture")
        if not actions:
            actions.append("observe_only")
        projection = sorted(set(actions))
    else:
        projection = {
            "suffix_counts": suffix_counts,
            "size_bands": size_bands,
            "pressure": pressure,
        }

    receipt = {**base, "projection": projection}
    return {**receipt, "root_cid": cid_for(receipt)}


def scan_and_collapse(config: FilesystemScanConfig, collapse: str = "state") -> dict[str, Primitive]:
    return collapse_filesystem_field(scan_filesystem(config), collapse=collapse)


def scan_and_choose(
    config: FilesystemScanConfig,
    policy: EntityChoicePolicy | None = None,
) -> dict[str, Primitive]:
    return collapse_filesystem_field(scan_filesystem(config), collapse="auto", policy=policy)


if __name__ == "__main__":
    import json

    demo = scan_and_collapse(FilesystemScanConfig(root_path=".", max_files=32, max_dirs=32, max_depth=2), "state")
    print(json.dumps(demo, ensure_ascii=False, indent=2, sort_keys=True))
