# Routing and Verification Foundation

This milestone adds the first deterministic point-to-point routing path plus headless Magic DRC, Magic extraction, and Netgen LVS adapters.

## Routing flow

```text
placement component + placement plan
→ stable promoted tile ports
→ PointToPointRouteIntent
→ PointToPointRoutePlan
→ gLayout route-family execution
→ routed GDS
```

A placed MOS tile port is promoted as `<tile_name>__<primitive_port_name>`, for example `A0__gate_E` or `B1__drain_N`.

For `strategy="auto"`, the pure planner currently selects:

```text
parallel + inline                   → straight
perpendicular                      → L
parallel + same-facing, non-inline → C
parallel + opposite-facing         → smart-route fallback
```

The current routing slice is point-to-point only. It does not yet solve obstacle avoidance, multi-terminal topology, balanced differential routing, shielding, or CDAC bus routing.

## One-command demo

Inside the Chipathon container:

```bash
cd /foss/designs
source scripts/matchmaker/env/setup.sh
python scripts/matchmaker/examples/routing/route_two_centroid_gates.py
```

That single command now:

```text
generates placement
→ routes A0 gate to A1 gate
→ writes GDS
→ runs GF180 Magic DRC
→ extracts layout SPICE
→ writes structured reports
```

Use `--skip-verification` to generate only the GDS.

## Verify any generated cell

```bash
python scripts/matchmaker/examples/verification/verify_generated_cell.py CELL_NAME
```

Use `--drc-only` to skip extraction.

Standard artifacts are written under:

```text
libs/core_analog/<cell>/gds/
libs/core_analog/<cell>/netlist/
libs/core_analog/<cell>/reports/drc/
libs/core_analog/<cell>/reports/extraction/
libs/core_analog/<cell>/reports/lvs/
```

The verification adapters explicitly provide `PDK=gf180mcuD` and `PDK_ROOT=/foss/pdks` to subprocesses, so Jupyter kernels and terminal shells do not need separate manual environment fixes.

## DRC criteria

`run_magic_drc(...)` passes only when:

- Magic exits successfully;
- the requested GDS top cell was actually read;
- the completion marker is present; and
- Magic reports exactly zero DRC errors.

The parser accepts Magic's native `Total DRC errors found: N` output.

## Extraction criteria

`run_magic_extraction(...)` removes stale output first, reads the requested GDS cell, runs `extract all`, writes an ngspice-compatible LVS netlist, and returns a structured failure reason when any stage is incomplete.

## LVS flow

```text
GDS
→ Magic extraction
→ layout SPICE
→ Netgen comparison against schematic SPICE
→ structured result + combined report
```

Run LVS with:

```bash
python scripts/matchmaker/examples/verification/run_lvs.py CELL_NAME path/to/schematic.spice
```

The GF180 Netgen setup file is resolved automatically from either the direct `/foss/pdks/gf180mcuD` layout or the CIEL versioned PDK tree. An explicit setup file remains optional through `MagicNetgenLvsConfig`.

The LVS parser accepts only an unqualified unique circuit match. Mismatch, property-error, and port-error outcomes fail.

## Tests

```bash
cd /foss/designs
source scripts/matchmaker/env/setup.sh
python -m unittest discover -s scripts/matchmaker/tests -v
```

The next routing milestone is connectivity-driven obstacle avoidance: extract the current centroid route, establish which device gates share the routed node, then reject straight candidates that cross non-endpoint device access geometry.
