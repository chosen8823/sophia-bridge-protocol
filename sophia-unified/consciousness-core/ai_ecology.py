"""Conversational AI ecology membrane.

This layer treats different AI families and automation surfaces as participants
inside one local semantic environment.  They are not invoked as external bots by
this module.  They declare what they can sense, transform, and provide; an event
then routes through compatible participants as a deterministic series of
semantic transforms.

Field cookies preserve provenance.  Field flags mark attention thresholds.  The
receipt remains local and OPTE-shaped so real adapters can decide later whether
any action should cross a stronger boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from regulatory_organs import Primitive, canonical_bytes, cid_for


class EcologyError(ValueError):
    """Stable machine-readable error for ecology routing failures."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


@dataclass(frozen=True)
class EcologyParticipant:
    """A local participant type in the semantic body."""

    name: str
    family: str
    realm: str
    senses: tuple[str, ...]
    transforms: tuple[str, ...]
    provides: tuple[str, ...]
    posture: str = "local"
    external_effects: bool = False

    def to_primitive(self) -> dict[str, Primitive]:
        return {
            "kind": "ecology_participant_v1",
            "name": self.name,
            "family": self.family,
            "realm": self.realm,
            "senses": sorted(set(self.senses)),
            "transforms": sorted(set(self.transforms)),
            "provides": sorted(set(self.provides)),
            "posture": self.posture,
            "external_effects": self.external_effects,
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


@dataclass(frozen=True)
class EcologyEvent:
    """A conversational signal entering the AI ecology body."""

    source: str
    utterance: str
    tags: tuple[str, ...] = ()
    payload: Mapping[str, Any] | None = None

    def to_primitive(self) -> dict[str, Primitive]:
        payload = {} if self.payload is None else dict(self.payload)
        # Reuse canonical validation: no floats, bytes, or arbitrary objects.
        import json

        canonical_payload = json.loads(canonical_bytes(payload).decode("utf-8"))
        return {
            "kind": "ecology_event_v1",
            "source": self.source,
            "utterance": self.utterance,
            "tags": sorted(set(self.tags)),
            "payload": canonical_payload,
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


DEFAULT_PARTICIPANTS: tuple[EcologyParticipant, ...] = (
    EcologyParticipant(
        "game_ai",
        "simulation",
        "digital",
        ("game", "npc", "pathfinding", "state", "procedural", "world"),
        ("simulate_state", "choose_behaviour", "pathfind"),
        ("world_state", "agent_motion", "procedural_response"),
    ),
    EcologyParticipant(
        "agent_ai",
        "task_agent",
        "semantic",
        ("task", "plan", "repo", "code", "document", "schedule"),
        ("plan", "delegate", "summarise", "edit_candidate"),
        ("work_graph", "task_routes", "draft_changes"),
    ),
    EcologyParticipant(
        "audio_daw",
        "audio",
        "resonance",
        ("audio", "daw", "spotify", "music", "rhythm", "frequency", "voice"),
        ("analyse_rhythm", "map_timbre", "extract_pulse"),
        ("pulse_field", "resonance_features", "sonic_projection"),
    ),
    EcologyParticipant(
        "social_media",
        "social",
        "relational",
        ("social", "post", "audience", "reply", "culture", "trend"),
        ("draft_response", "classify_context", "flag_thresholds"),
        ("draft_only", "context_flags", "audience_surface"),
        posture="approval_required",
        external_effects=True,
    ),
    EcologyParticipant(
        "search_ai",
        "retrieval",
        "evidence",
        ("search", "web", "research", "source", "citation", "query"),
        ("form_query", "rank_sources", "extract_evidence"),
        ("source_candidates", "evidence_routes", "citation_needs"),
        posture="read_only",
    ),
    EcologyParticipant(
        "cloud_ai",
        "remote_compute",
        "network",
        ("cloud", "scale", "worker", "queue", "container", "vm"),
        ("schedule_worker", "split_work", "collect_receipts"),
        ("worker_plan", "capacity_request", "remote_receipt"),
        posture="approval_required",
        external_effects=True,
    ),
    EcologyParticipant(
        "cybernetic",
        "feedback_control",
        "physical_digital",
        ("sensor", "hardware", "thermal", "battery", "network", "filesystem", "organ"),
        ("measure_pressure", "route_feedback", "stabilise_loop"),
        ("pressure_state", "regulation_affordance", "health_pulse"),
    ),
    EcologyParticipant(
        "science_agents",
        "research_collective",
        "knowledge",
        ("science", "biology", "chemistry", "physics", "protein", "duf", "experiment"),
        ("compare_hypotheses", "find_metrics", "surface_contradiction"),
        ("hypothesis_map", "metric_needs", "contradiction_bridge"),
    ),
    EcologyParticipant(
        "security_sentries",
        "threshold_guard",
        "authority",
        ("security", "credential", "secret", "permission", "webhook", "public"),
        ("flag_sensitive", "hold_for_approval", "separate_authority"),
        ("attention_flags", "approval_boundary", "safe_draft"),
    ),
    EcologyParticipant(
        "token_sentries",
        "syntax_boundary",
        "semantic",
        ("token", "glyph", "prompt", "syntax", "aria", "hidden"),
        ("preserve_glyphs", "normalise_shadow", "route_tokens"),
        ("glyph_atoms", "normalised_surface", "token_routes"),
    ),
    EcologyParticipant(
        "render_ui",
        "projection",
        "visual",
        ("render", "ui", "gui", "div", "visual", "colour", "contrast"),
        ("collapse_expression", "project_surface", "colour_pressure"),
        ("centre_div", "visual_state", "projection_map"),
    ),
    EcologyParticipant(
        "filesystem",
        "storage_tissue",
        "digital",
        ("file", "filesystem", "folder", "repo", "archive", "cookie", "breadcrumb"),
        ("hydrate_files", "emit_field_cookies", "classify_topology"),
        ("file_atoms", "field_cookies", "topology_health"),
    ),
)


FLAG_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("password", "sensitive_secret"),
    ("api key", "sensitive_secret"),
    ("secret", "sensitive_secret"),
    ("post this", "external_social_action"),
    ("tweet", "external_social_action"),
    ("upload", "external_write"),
    ("delete", "destructive_action"),
    ("payment", "money_or_financial_action"),
    ("cash app", "money_or_financial_action"),
    ("bank", "money_or_financial_action"),
)


def _event_terms(event: EcologyEvent) -> tuple[str, ...]:
    primitive = event.to_primitive()
    text = " ".join(
        [
            str(primitive["source"]),
            str(primitive["utterance"]),
            " ".join(str(tag) for tag in primitive["tags"]),
            str(primitive["payload"]),
        ]
    ).lower()
    tokens = []
    current = []
    for char in text:
        if char.isalnum() or char in {"_", "-"}:
            current.append(char)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(sorted(set(tokens)))


def _participant_score(participant: EcologyParticipant, terms: tuple[str, ...]) -> int:
    senses = set(participant.senses)
    transforms = set(participant.transforms)
    provides = set(participant.provides)
    term_set = set(terms)
    return (
        len(senses & term_set) * 5
        + len(transforms & term_set) * 3
        + len(provides & term_set) * 2
        + (2 if participant.family in term_set else 0)
        + (2 if participant.realm in term_set else 0)
    )


def field_cookies_for(event: EcologyEvent, participants: Iterable[EcologyParticipant]) -> tuple[dict[str, Primitive], ...]:
    """Create deterministic provenance cookies for the participating ecology."""

    cookies = []
    for participant in sorted(participants, key=lambda item: item.name):
        cookie = {
            "kind": "field_cookie_v1",
            "event_cid": event.cid,
            "participant_cid": participant.cid,
            "participant": participant.name,
            "source": event.source,
            "crumb": cid_for({"event": event.cid, "participant": participant.cid}),
        }
        cookies.append({**cookie, "cookie_cid": cid_for(cookie)})
    return tuple(cookies)


def flags_for(event: EcologyEvent, participants: Iterable[EcologyParticipant]) -> tuple[dict[str, Primitive], ...]:
    """Create local threshold flags without taking external action."""

    text = f"{event.source} {event.utterance} {event.tags} {event.payload}".lower()
    flags: list[dict[str, Primitive]] = []
    for keyword, code in FLAG_KEYWORDS:
        if keyword in text:
            flag = {
                "kind": "field_flag_v1",
                "event_cid": event.cid,
                "code": code,
                "keyword": keyword,
                "severity": "attention",
                "action": "hold_for_explicit_membrane",
            }
            flags.append({**flag, "flag_cid": cid_for(flag)})

    for participant in participants:
        if participant.external_effects:
            flag = {
                "kind": "field_flag_v1",
                "event_cid": event.cid,
                "code": "external_effect_boundary",
                "keyword": participant.name,
                "severity": "membrane",
                "action": "draft_only_until_approved",
            }
            flags.append({**flag, "flag_cid": cid_for(flag)})
    return tuple(sorted(flags, key=lambda flag: (str(flag["code"]), str(flag["keyword"]))))


def route_event(
    event: EcologyEvent,
    participants: Iterable[EcologyParticipant] = DEFAULT_PARTICIPANTS,
    max_routes: int = 6,
) -> dict[str, Primitive]:
    """Route an ecology event through compatible participants."""

    if max_routes <= 0:
        raise EcologyError("ECOLOGY_ROUTE_BUDGET_REJECTED", "max_routes must be positive")

    all_participants = tuple(participants)
    terms = _event_terms(event)
    scored = [
        (participant, _participant_score(participant, terms))
        for participant in all_participants
    ]
    matched = [
        participant
        for participant, score in sorted(scored, key=lambda item: (-item[1], item[0].name))
        if score > 0
    ][:max_routes]

    if not matched:
        matched = [
            EcologyParticipant(
                "unknown_signal_reservoir",
                "residual",
                "air",
                ("unknown",),
                ("hold_residual",),
                ("aperture_request",),
            )
        ]

    transforms = []
    for index, participant in enumerate(matched):
        transform = {
            "kind": "ecology_transform_step_v1",
            "step": index,
            "participant": participant.name,
            "participant_cid": participant.cid,
            "family": participant.family,
            "realm": participant.realm,
            "operation": sorted(participant.transforms)[0],
            "provides": sorted(set(participant.provides)),
            "posture": participant.posture,
            "altitude": "air",
        }
        transforms.append({**transform, "step_cid": cid_for(transform)})

    cookies = field_cookies_for(event, matched)
    flags = flags_for(event, matched)
    invariant_projection = [
        {
            "participant": step["participant"],
            "operation": step["operation"],
            "posture": step["posture"],
            "altitude": step["altitude"],
        }
        for step in transforms
    ]
    receipt = {
        "kind": "ai_ecology_receipt_v1",
        "event_cid": event.cid,
        "terms": list(terms),
        "participants": [participant.name for participant in matched],
        "transform_series": transforms,
        "field_cookies": list(cookies),
        "field_flags": list(flags),
        "invariant": cid_for(invariant_projection),
        "altitude": "air",
        "settlement_surface": "ground",
    }
    return {**receipt, "root_cid": cid_for(receipt)}
