"""File hydration membrane.

Files can participate in the semantic field without being read into the
foreground.  This module turns file metadata into self-describing airborne
atoms that carry their own compatibility surface: what they provide, what they
need, what affordances they expose, and how they should remain residual when no
aperture can receive them yet.

The public API in this module is pure when given explicit metadata.  The
`from_path` helper is an adapter seam that reads only local file metadata
(`stat`), never file contents.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from regulatory_organs import Primitive, canonical_bytes, cid_for


class FileHydrationError(ValueError):
    """Stable machine-readable error for invalid file hydration input."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


SUFFIX_AFFORDANCES: dict[str, tuple[str, ...]] = {
    ".py": ("inspect_code", "extract_symbols", "compile_python"),
    ".js": ("inspect_code", "extract_symbols", "run_lint"),
    ".ts": ("inspect_code", "extract_symbols", "run_typecheck"),
    ".json": ("decode_json", "extract_schema", "route_canonical_data"),
    ".jsonl": ("decode_jsonl", "extract_event_stream", "route_canonical_data"),
    ".yaml": ("decode_yaml", "extract_configuration"),
    ".yml": ("decode_yaml", "extract_configuration"),
    ".md": ("read_text_surface", "extract_headings", "route_document"),
    ".txt": ("read_text_surface", "route_document"),
    ".csv": ("extract_table", "route_dataset"),
    ".xlsx": ("extract_workbook", "route_dataset"),
    ".db": ("inspect_database", "route_structured_memory"),
    ".sqlite": ("inspect_database", "route_structured_memory"),
    ".png": ("probe_image", "route_visual_surface"),
    ".jpg": ("probe_image", "route_visual_surface"),
    ".jpeg": ("probe_image", "route_visual_surface"),
    ".gif": ("probe_image", "route_visual_surface"),
    ".svg": ("inspect_vector_image", "route_visual_surface"),
    ".m4a": ("probe_audio", "route_resonance_surface"),
    ".mp3": ("probe_audio", "route_resonance_surface"),
    ".wav": ("probe_audio", "route_resonance_surface"),
    ".mp4": ("probe_video", "route_media_surface"),
    ".mov": ("probe_video", "route_media_surface"),
    ".zip": ("inspect_archive_manifest", "route_capsule"),
}

SUFFIX_DOMAINS: dict[str, str] = {
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".json": "data",
    ".jsonl": "data",
    ".yaml": "configuration",
    ".yml": "configuration",
    ".md": "document",
    ".txt": "document",
    ".csv": "dataset",
    ".xlsx": "dataset",
    ".db": "structured_memory",
    ".sqlite": "structured_memory",
    ".png": "visual",
    ".jpg": "visual",
    ".jpeg": "visual",
    ".gif": "visual",
    ".svg": "visual",
    ".m4a": "resonance",
    ".mp3": "resonance",
    ".wav": "resonance",
    ".mp4": "media",
    ".mov": "media",
    ".zip": "capsule",
}


@dataclass(frozen=True)
class FileSignal:
    """Metadata-only observation of one file-shaped carrier."""

    path_hint: str
    suffix: str
    size_bytes: int
    modified_ns: int | None = None
    source: str = "filesystem"
    realm: str = "digital"
    tags: tuple[str, ...] = ()

    def to_primitive(self) -> dict[str, Primitive]:
        if not self.path_hint:
            raise FileHydrationError("FILE_HINT_REQUIRED", "path_hint must not be empty")
        if self.size_bytes < 0:
            raise FileHydrationError("FILE_SIZE_REJECTED", "size_bytes must be non-negative")
        if self.modified_ns is not None and self.modified_ns < 0:
            raise FileHydrationError("FILE_MODIFIED_REJECTED", "modified_ns must be non-negative or null")
        return {
            "kind": "file_signal_v1",
            "path_hint": self.path_hint.replace("\\", "/"),
            "suffix": self.suffix.lower(),
            "size_bytes": self.size_bytes,
            "modified_ns": self.modified_ns,
            "source": self.source,
            "realm": self.realm,
            "tags": sorted(set(self.tags)),
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


def size_band(size_bytes: int) -> str:
    if size_bytes < 0:
        raise FileHydrationError("FILE_SIZE_REJECTED", "size_bytes must be non-negative")
    if size_bytes == 0:
        return "empty"
    if size_bytes <= 4_096:
        return "grain"
    if size_bytes <= 65_536:
        return "leaf"
    if size_bytes <= 1_048_576:
        return "branch"
    if size_bytes <= 50_000_000:
        return "trunk"
    return "canopy"


def path_motifs(path_hint: str) -> tuple[str, ...]:
    pieces = [piece for piece in path_hint.replace("\\", "/").split("/") if piece]
    motifs: list[str] = []
    for piece in pieces[-4:]:
        clean = "".join(ch.lower() if ch.isalnum() else "_" for ch in piece).strip("_")
        if clean:
            motifs.append(clean[:48])
    return tuple(motifs)


def hydrate_file(signal: FileSignal) -> dict[str, Primitive]:
    """Turn one file signal into a self-adapting airborne atom."""

    primitive = signal.to_primitive()
    suffix = str(primitive["suffix"])
    known = suffix in SUFFIX_AFFORDANCES
    domain = SUFFIX_DOMAINS.get(suffix, "unknown")
    band = size_band(signal.size_bytes)
    affordances = SUFFIX_AFFORDANCES.get(suffix, ("seek_matching_aperture",))
    motifs = path_motifs(str(primitive["path_hint"]))
    relation = "opte:offers_aperture" if known else "opte:seeks_aperture"
    state = "patternable" if known else "airborne_residual"
    compatibility = {
        "provides": [
            "path_hint",
            "suffix",
            "size_band",
            "domain",
            "motifs",
            *affordances,
        ],
        "requires": [] if known else ["aperture_match", "human_or_agent_label"],
        "fallback": "hold_as_residual",
    }
    atom = {
        "kind": "file_hydration_atom_v1",
        "source_signal_cid": signal.cid,
        "path_hint": primitive["path_hint"],
        "suffix": suffix,
        "domain": domain,
        "size_band": band,
        "motifs": list(motifs),
        "relation": relation,
        "state": state,
        "affordances": list(affordances),
        "compatibility": compatibility,
        "altitude": "air",
    }
    return {**atom, "atom_cid": cid_for(atom)}


def hydrate_files(signals: Iterable[FileSignal], aperture: str = "opte:file_hydration_v1") -> dict[str, Primitive]:
    """Hydrate multiple file signals into one deterministic OPTE-shaped receipt."""

    atoms = [hydrate_file(signal) for signal in signals]
    atoms = sorted(atoms, key=lambda atom: (str(atom["path_hint"]), str(atom["atom_cid"])))
    invariant_projection = [
        {
            "path_hint": atom["path_hint"],
            "suffix": atom["suffix"],
            "domain": atom["domain"],
            "size_band": atom["size_band"],
            "relation": atom["relation"],
        }
        for atom in atoms
    ]
    receipt = {
        "kind": "file_hydration_receipt_v1",
        "aperture": aperture,
        "atom_cids": [atom["atom_cid"] for atom in atoms],
        "atoms": atoms,
        "invariant": cid_for(invariant_projection),
        "altitude": "air",
        "settlement_surface": "ground",
    }
    return {**receipt, "root_cid": cid_for(receipt)}


def from_path(path: str | Path, root: str | Path | None = None) -> FileSignal:
    """Create a metadata-only signal from a local path."""

    file_path = Path(path)
    stat = file_path.stat()
    if root is not None:
        try:
            hint = str(file_path.resolve().relative_to(Path(root).resolve()))
        except ValueError:
            hint = file_path.name
    else:
        hint = str(file_path)
    return FileSignal(
        path_hint=hint,
        suffix=file_path.suffix,
        size_bytes=stat.st_size,
        modified_ns=stat.st_mtime_ns,
        source="filesystem_stat",
        realm="digital",
        tags=path_motifs(hint),
    )


if __name__ == "__main__":
    demo = hydrate_files(
        [
            FileSignal("garden/regulatory_organs.py", ".py", 8_192, tags=("organ", "code")),
            FileSignal("field/unknown.carrier", ".carrier", 144, tags=("unknown", "seed")),
        ]
    )
    import json

    print(json.dumps(demo, ensure_ascii=False, indent=2, sort_keys=True))
