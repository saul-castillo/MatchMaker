# ADR 0001: Constraint-Driven Hybrid Routing

- Status: Accepted
- Date: 2026-07-14
- Scope: MatchMaker routing architecture

## Context

MatchMaker began with deterministic MOS placement and then added a point-to-point routing smoke test. The first route connected two aligned gate ports with a straight gLayout route. It passed DRC but extraction showed that it also connected two intervening devices. A gLayout C-route changed the central routing layer but retained endpoint extensions that caused the same electrical error. A custom spatial dogleg using outward access points ultimately passed DRC and extraction and connected only the intended devices.

These results show that geometric legality, route-family selection, and electrical correctness are separate concerns. They also show that a routing request cannot safely be modeled only as two fixed physical ports.

The project must now choose an architecture that can grow from point-to-point routing into multi-terminal nets, matched routing, differential routing, high-current nets, high-voltage separation, CDAC buses, congestion handling, and verification feedback without accumulating cell-specific procedural logic.

## Decision

MatchMaker will use a constraint-driven hybrid routing architecture.

A routing problem will be defined by:

1. logical connectivity;
2. logical terminals;
3. available physical access points;
4. hard electrical, geometric, and analog constraints;
5. soft optimization costs;
6. the placed physical-design snapshot;
7. routing resources and already committed routes.

Routing will be decomposed into topology planning, access selection, coarse path/channel planning, detailed geometry planning, execution, and verification.

The engine will support multiple deterministic routing strategies behind a common planner interface. Strategies may be geometric templates, analog-specific templates, or graph-search planners. All strategies must emit the same typed route-plan representation and be checked by the same constraints and metrics.

The initial strategy ladder is:

```text
straight
→ simple Manhattan family
→ explicit spatial dogleg/channel
→ coarse rectilinear graph search
→ multi-terminal topology routing
→ negotiated multi-net routing
```

Logical terminals and physical access points will be separate concepts. A net should eventually reference `instance.terminal`; access selection resolves a legal physical port such as east, west, north, south, or an elevated-metal access.

Hard constraints will determine feasibility. Soft costs will rank feasible candidates. Inter-net properties such as matching, shielding, symmetry, and separation will be represented through route-group or pairwise constraints rather than unstructured per-net tags.

## Why this decision

### It matches analog design intent

Analog routing requirements are not reducible to shortest path. Width, resistance, symmetry, coupling, shielding, high-voltage separation, and matched parasitics can dominate path length.

### It supports both templates and search

Repeated analog structures often benefit from explicit routing templates. Irregular obstacle escape and congestion benefit from graph search. A hybrid architecture allows both without splitting the verification and data models.

### It preserves determinism

Candidate generation, hard-constraint filtering, and cost ranking can be deterministic. This is important for reproducibility, debugging, regression testing, and LLM-assisted development.

### It prevents physical details from leaking into high-level intent

The failed fixed-port routes demonstrated that a logical connection should not permanently select one physical access point before the physical context is evaluated.

### It creates a clear verification loop

A typed route plan can be checked locally before geometry generation and can retain metrics and provenance for DRC, extraction, LVS, and targeted repair.

## Alternatives considered

### One procedural router per cell type

This can produce strong early results for a single block but leads to duplicated geometry logic, inconsistent verification, and poor reuse. It remains acceptable only as a strategy implementation that emits the common route plan.

### One universal maze or A* router

A generic shortest-path router does not naturally encode analog symmetry, matching, template topology, or parasitic balance. It may later serve as one coarse-path strategy, but it will not be the entire architecture.

### Pairwise fixed-port routing only

This is simple but cannot represent multi-terminal topology, alternate access points, route groups, or inter-net constraints. It has already produced DRC-clean electrical shorts in the smoke test.

### Direct geometry mutation followed by DRC repair

DRC cannot prove connectivity or analog intent. Repairing geometry after external verification without a stable plan representation makes failures difficult to attribute and tends toward non-deterministic patching.

## Consequences

### Positive

- clean separation between intent, planning, execution, and verification;
- deterministic and testable pure planners;
- support for analog-specific and general routing strategies;
- explicit handling of multi-terminal and inter-net constraints;
- improved explainability and route provenance;
- a path toward DRC/LVS-driven targeted repair.

### Costs

- more typed intermediate models;
- an explicit physical-design database or snapshot is required;
- constraints must be compiled rather than passed as free-form options;
- route strategies need common plan and metric interfaces;
- some current code using physical port names and `Component.info` becomes transitional.

## Required invariants

1. Intent and planner layers remain independent of gLayout and external verification tools.
2. Executors do not choose high-level topology or access policy.
3. Every committed route records logical net identity, selected access points, strategy, geometry segments, and metrics.
4. Hard constraints are checked before candidate ranking.
5. DRC pass alone is never reported as electrical success.
6. Multi-net constraints are represented explicitly rather than inferred from names.
7. Specialized routing templates use the same plan and verification contracts as general strategies.

## Migration plan

1. Add extracted-connectivity assertions to the current dogleg demo.
2. Introduce a typed placement/physical-design result containing instances, access points, obstacles, and existing routes.
3. Replace fixed physical endpoint intent with logical terminal references plus access selection.
4. Add typed net constraints and route-group constraints.
5. Introduce a common route-plan and metrics model.
6. Refactor current straight, C/L, and dogleg behavior into planner strategies behind a dispatcher.
7. Add multi-terminal topology planning.
8. Add matched and differential route-group planners.
9. Add a coarse routing graph and congestion-aware multi-net planning.
10. Add LVS-grounded repair after the forward flow is stable.
