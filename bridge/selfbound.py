from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

POLICY_PATH = Path(__file__).resolve().parents[1] / "runtime" / "selfbound.toml"


@dataclass(frozen=True)
class Scope:
    name: str
    channels: frozenset[str]
    capabilities: frozenset[str]
    transports: frozenset[str]


class PolicyError(RuntimeError):
    pass


def _subset(child: set[str], parent: set[str], field: str, scope: str) -> None:
    extra = child - parent
    if extra:
        raise PolicyError(f"{scope}.{field} exceeds parent authority: {sorted(extra)}")


def load_policy(path: Path = POLICY_PATH) -> dict:
    with path.open("rb") as f:
        data = tomllib.load(f)

    root = data["root"]
    root_caps = set(root.get("capabilities", []))
    root_channels = set(root.get("channels", []))
    root_transports = set(root.get("transports", []))

    for name, raw in data.get("scopes", {}).items():
        if raw.get("parent") != "root":
            raise PolicyError(f"unsupported parent for scope {name}")
        _subset(set(raw.get("capabilities", [])), root_caps, "capabilities", name)
        _subset(set(raw.get("channels", [])), root_channels, "channels", name)
        _subset(set(raw.get("transports", [])), root_transports, "transports", name)
    return data


def scope(name: str, data: dict | None = None) -> Scope:
    data = data or load_policy()
    raw = data["root"] if name == "root" else data["scopes"][name]
    return Scope(
        name=name,
        channels=frozenset(raw.get("channels", [])),
        capabilities=frozenset(raw.get("capabilities", [])),
        transports=frozenset(raw.get("transports", [])),
    )


def permits(scope_name: str, capability: str, data: dict | None = None) -> bool:
    return capability in scope(scope_name, data).capabilities
