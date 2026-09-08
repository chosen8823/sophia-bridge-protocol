# Organ and Body Architecture Prior Art

This note maps existing technical lineages onto the Sophia organ/body layer.
It is not a claim that Sophia is identical to any one of them.  The point is to
identify useful prior structures, then keep the Sophia kernel focused on
receipts, membranes, apertures, and linked semantic atoms.

## Nearby lineages

### Autonomic computing / MAPE-K

IBM's autonomic-computing work describes self-managing systems through
monitor, analyse, plan, execute, and knowledge loops.  This is the closest
mainstream ancestor for "organs" as regulatory surfaces: observe pressure,
decide whether intervention is needed, then execute through controlled
interfaces.

Sophia difference: the organ does not own action.  Observation and semantic
projection can happen locally, while hardware mutation stays behind an
explicit action membrane.

Sources:

- https://research.ibm.com/publications/an-architectural-approach-to-autonomic-computing
- https://link.springer.com/article/10.1007/s10844-022-00766-w

### Organic computing

Organic computing uses observer/controller architectures for self-adaptive
systems that can respond to changing environments and, in some cases, improve
their adaptation logic at run time.

Sophia difference: the observer/controller idea maps well to membranes, but
Sophia keeps durable state content-addressed and treats conceptual evolution as
something that needs explicit material admission.

Sources:

- https://arxiv.org/abs/1808.03519
- https://dl.gi.de/items/939fe8fb-0ac6-4ff4-bac7-31f130883acd

### Blackboard systems

Blackboard architecture gives multiple specialist modules a shared workspace
where partial results, proposals, and evidence can accumulate.  Modern
multi-agent work has reused this pattern for LLM agents and data discovery.

Sophia difference: the shared surface should not become a command hierarchy.
It should behave more like a field ledger: signals appear, compatible
apertures respond, and stable transitions leave receipts.

Sources:

- https://arxiv.org/abs/2507.01701
- https://arxiv.org/abs/2510.01285
- https://research.google/pubs/blackboard-multi-agent-systems-for-information-discovery-in-data-science/

### Artificial immune systems

Artificial immune systems model detection, tolerance, memory, and response.
For Sophia, this is useful for thinking about anomaly pressure, noisy signals,
quarantine, repair, and delayed promotion.

Sophia difference: immune-like response should not silently delete or punish.
It should classify pressure, preserve provenance, and route explicit relief
actions through separate membranes.

Sources:

- https://pmc.ncbi.nlm.nih.gov/articles/PMC3981469/
- https://learn.microsoft.com/en-us/archive/msdn-magazine/2013/january/test-run-artificial-immune-systems-for-intrusion-detection

### Skill ecosystems

Agent Skills and Agent Plugins treat capabilities as portable instruction
packages.  The recovered scientific skill pack follows this pattern: many
narrow skills, each with its own references, scripts, and validation rules.

Sophia difference: skills are external organs or adapters.  They can enrich
the field, but they should not become hidden authorities over core state.

Sources:

- https://agentskills.io/specification
- https://agent-plugins.org/
- https://github.com/K-Dense-AI/scientific-agent-skills

## What Sophia should borrow

- From autonomic computing: measured pressure and explicit control loops.
- From organic computing: observer/controller separation and run-time
  adaptation.
- From blackboards: a shared evidence surface.
- From artificial immune systems: anomaly/tolerance/repair metaphors.
- From skill ecosystems: portable, narrow capability organs.

## What Sophia should not borrow blindly

- Central controllers that turn the field into a boss tree.
- Hidden mutation behind observation.
- Floating-point or non-canonical state in the kernel.
- Vague decay instead of finite residual policy.
- Tools that act without a receipt.

## Sophia fit

The current body stack is:

```text
filesystem ingestor
  -> field thermometer
  -> regulatory organs
  -> morphogenic transducer
  -> cymatic observer frames
  -> CPU aperture
  -> unified pulse organ
```

The useful translation is:

```text
body organ = membrane that sees one kind of pressure
aperture = frame where pressure becomes relation
semantic atom = non-identity addressable signal
receipt = canonical proof that the field changed legibly
home base = content-addressed return surface
```

That gives us the body without letting the body eat the kernel.
