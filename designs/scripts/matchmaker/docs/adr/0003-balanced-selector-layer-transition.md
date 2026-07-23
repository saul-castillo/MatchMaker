# ADR 0003: Balanced selector controls use an explicit layer transition

Status: Accepted

## Context

The physically accepted B0 selector used two identical R0 transmission-gate
children. Its safe control accesses forced `SELECT` around both child envelopes,
while `SELECT_BAR` fit in the central gap. The measured lengths were 116.445 µm
and 20.485 µm. Adding met2 VSS/VDD rails preserved zero DRC violations but
produced a visually rejected nested layout and only four of five expected shared
child nets.

The asymmetry is structural. With both children in R0, the safe NMOS and PMOS
gate escapes place one complementary-control pair at the selector exterior and
the other pair in the child gap. Rotating one identical child by 180 degrees
makes the two control pairs rotationally symmetric, but a single-layer planar
solution then conflicts with the central COMMON route and supply crossings.

## Decision

Place the generated children as an `R0/R180` pair and route both complementary
controls on one explicitly resolved upper metal layer.

```text
identical generated TG cells
-> VREF_TG R0 + VSS_TG R180
-> transformed-orientation access selection
-> short met2 escape stubs
-> two matched met2/met3 via stacks per control
-> symmetric north/south met3 half-perimeters
```

`COMMON` remains in the central gap on met2. VSS uses the transformed physical
north ties and physical-east low-reference input on met2. VDD uses the facing
physical east/west PMOS body ties on their measured met1 layer, with a compact
central strap and south escape.

The generated control access supplies the numeric source layer, while policy
selects only generic `met3`. The GF180 adapter derives the numeric route layer,
minimum width, and via envelope from the activated PDK. The planner receives the
result as a typed `RoutingLayerTransition`. The executor receives a via-geometry
factory and only materializes the already resolved `RoutePlan`.

## Invariants

1. Both child instances reference geometrically identical generated TG cells.
2. Placement transforms references before deriving centers and spacing.
3. Routing selects transformed physical orientation, never cardinal name suffix
   alone.
4. `SELECT` and `SELECT_BAR` contain the same number of vias and have equal total
   planned length within policy tolerance.
5. Every via center terminates a segment on both connected layers.
6. The child gap must contain the runtime via envelope.
7. Different nets may cross only on different routing layers; same-layer route
   rectangles may not touch.
8. PDK layer numbers, minimum widths, and via dimensions remain adapter-owned.
9. DRC, extraction, exact five-net connectivity, visual inspection, and Netgen
   LVS remain independent acceptance gates.

## Consequences

Positive:

- complementary-control parasitics are balanced by construction;
- the full-width SELECT loop and nested SELECT/VSS perimeter are removed;
- the VDD experiment moves from the failed met2 south ties to measured facing
  met1 ties;
- rotated child ports remain stable because names identify logical exports while
  runtime orientation identifies physical direction;
- via geometry is now an injected execution resource rather than planner policy.

Costs and limitations:

- each control gains two met2/met3 vias;
- control routing now consumes met3, which the future CDAC macro planner must
  coordinate with capacitor top-plate routing;
- only the GF180 centered via-stack execution path is implemented;
- the topology is not physically accepted until the Chipathon `/foss` run passes
  every verification gate.
