# ADR 0004: Composite cells use family contracts and reusable corridor plans

Status: Accepted

## Context

The first B0 reference-selector planners directly encoded a sequence of
selector-specific corridors. They established useful typed boundaries, but each
physical correction expanded one block planner: central control trunks,
perimeter controls, supply rails, rotated access selection, and explicit layer
transitions all accumulated in the same module.

The balanced horizontal `R0/R180` attempt demonstrated the limit of that model.
It made `SELECT` and `SELECT_BAR` numerically equal at 71.085 µm, yet retained
large met3 half-perimeters, a 98.54 µm VSS tree, a four-device row, and only four
of five expected extracted shared nets. A selector-only rewrite would not help
MatchMaker compose future resistor, current-source, differential-pair,
transmission-gate, capacitor, or other device families.

## Decision

Composite-cell generation is split into reusable family, placement, routing,
and block-binding layers.

```text
device or generated-cell family
  -> CellFamilyAccessContract
  -> generic hierarchical PhysicalDesignSnapshot

generated child components
  -> OrientedPairPlacementPolicy
  -> runtime-envelope PlacementResult

NetIntent + selected transformed accesses + runtime corridor
  -> side bus / gap bridge / transitioned trunk tree
  -> ordinary RoutePlan

block-specific logical roles
  -> thin binding over those reusable primitives
```

### Family contract

Each device or generated-cell family owns its port-name grammar and required
logical terminal set. The generic hierarchical snapshot builder knows neither
GF180 names nor block roles. It records transformed centers, orientations,
widths, layers, and envelopes from runtime references.

Family adapters may narrow access capability per logical terminal. For the
transmission-gate family, signal routes expose only proven exterior W/E ports,
the NMOS control exposes west, the PMOS complement exposes east, and body ties
expose vertical N/S ports for stacked composition. A port's existence does not
prove that extending it through the composite interior is safe.

### Pair composition

The oriented-pair builder accepts any two generated child components plus:

- assembly axis;
- which side receives the first child;
- child orientations;
- runtime-envelope gap.

It aligns orthogonal centers, applies transforms before measuring envelopes,
and returns stable `PlacementResult` bindings. It contains no selector names or
device-family grammar.

### Corridor routing

The reusable corridor planner provides three execution-independent templates:

- exterior side bus for two outward-facing terminals;
- gap bridge for two terminals facing a shared inter-child or central corridor;
- transitioned rectilinear trunk for two or more terminals that must cross
  lower-layer routes.

Every template consumes `NetIntent`, `AccessPoint`, runtime envelopes, and typed
layer-transition resources. It emits `RoutePlan`; the executor remains
mechanical. Regression fixtures use resistor-, capacitor-, and
transistor-style terminal identities to prevent selector-name dependencies.

### Block binding

The reference selector is the first client. Its policy chooses a vertical
`VREF_TG=R0` / `VSS_TG=R180` pair and binds:

```text
COMMON     -> transitioned west-side trunk
SELECT     -> west side bus
SELECT_BAR -> east side bus
VSS        -> transitioned east-side multi-terminal trunk
VDD        -> vertical inter-child gap bridge
```

Those logical names and matching requirements stay in the selector planner.
The generic modules do not import them.

The policy names only semantic generic routing layers. The GF180 adapter alone
resolves numeric layers, minimum widths, and via envelopes.

## Invariants

1. A family-specific port token is interpreted only by its family adapter.
2. Generic placement and corridor planners cannot inspect block or terminal
   names to choose geometry.
3. Reference transforms precede all envelope and access measurements.
4. Family contracts expose only demonstrated terminal/direction capabilities.
5. Block planners bind logical roles and constraints; they do not draw
   primitive-specific coordinates.
6. Concrete numeric layers and via geometry remain PDK-adapter owned.
7. Every plan is checked for same-layer cross-net overlap before execution.
8. Matched route groups must pass explicit length and bend invariants.
9. Branched routes are reported as segments, never serialized as a fictitious
   ordered polyline.
10. DRC, extraction, terminal-level connectivity evidence, visual inspection,
    and independent LVS remain separate acceptance gates.

## Consequences

Positive:

- new cell families can reuse pair composition and corridor planning without
  copying selector code;
- the selector planner becomes smaller and easier to replace;
- safe access direction is part of a composite family interface;
- multi-terminal upper-layer trees are available beyond CDAC selectors;
- extraction reports identify child-interface terminal-to-net bindings rather
  than relying only on a shared-net count.

Costs and limitations:

- the current generic tree template uses a caller-selected trunk rather than
  obstacle-aware candidate search;
- only pair composition is implemented; larger arbitrary assemblies still need
  a general array/floorplan compiler;
- centered GF180 via stacks are the only executed transition family;
- reusable external-pin escape synthesis is still separate from internal
  composite routing;
- the vertical B0 binding remains physically unvalidated until its `/foss`
  DRC, extraction, five-net connectivity, visual, and Netgen LVS gates pass.
