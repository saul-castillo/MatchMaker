# Routing and Verification Foundation

This milestone adds the first deterministic point-to-point routing path plus headless Magic DRC, Magic extraction, and Netgen LVS adapters.

## Routing flow

```text
placement component + placement plan
→ stable promoted tile ports + tile bounding boxes
→ PointToPointRouteIntent
→ geometric route-family plan
→ obstacle check for straight candidates
→ gLayout route-family execution
→ routed GDS
```

A placed MOS tile port is promoted as `<tile_name>__<primitive_port_name>`, for example `A0__gate_E` or `B1__drain_N`.

For `strategy="auto"`, the pure geometric planner initially selects:

```text
parallel + inline                   → straight
perpendicular                      → L
parallel + same-facing, non-inline → C
parallel + opposite-facing         → smart-route fallback
```

Before executing a straight route, MatchMaker now intersects its centerline against the recorded bounding boxes of all non-endpoint tiles. A blocked same-facing route is converted to a C-route detour. A blocked opposite-facing inline route fails safely with the blocker names until a general channel detour is implemented. Obstacle checks can be disabled explicitly with `avoid_obstacles=False`, but they are enabled by default.

The routing slice remains point-to-point only. It does not yet solve general channel assignment, multi-terminal topology, balanced differential routing, shielding, or CDAC bus routing.

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
→ detects devices blocking the direct A-gate route
→ selects a detour
→ writes GDS
→ runs GF180 Magic DRC
→ extracts layout SPICE
→ writes structured reports
```

The command prints both the executed route strategy and the names of devices that blocked the original straight candidate. Use `--skip-verification` to generate only the GDS.

## Verify any generated cell

```bash
python scripts/matchmaker/examples/verification/verify_generated_cell.py CELL_NAME
```

Use `--drc-only` to skip extraction. A successful result means the requested pre-LVS stages completed; it does not claim schematic connectivity is correct.

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

`run_magic_extraction(...)` removes stale output first, reads the requested GDS cell, runs `extract all`, writes an ngspice-compatible LVS netlist, and returns a structured failure reason when any stage is incomplete. Extraction scratch files are kept in the cell netlist directory rather than beside the GDS.

Inspect the extracted top-level hierarchy with:

```bash
python scripts/matchmaker/examples/verification/inspect_extracted_netlist.py CELL_NAME
```

The inspector prints top-level device statements and a shared-net summary. That summary exposed the first straight-route defect: the route node appeared on four device instances instead of only the two intended A instances.

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

Missing executables and process timeouts are returned as structured failures rather than uncaught subprocess exceptions.

## Tests

```bash
cd /foss/designs
source scripts/matchmaker/env/setup.sh
python -m unittest discover -s scripts/matchmaker/tests -v
```

A GitHub Actions workflow also runs the pure unit tests and Python compilation for MatchMaker changes.

The next routing milestone is to integration-test the C detour in the `/foss` container, verify DRC, and confirm from the extracted shared-net summary that the routed node appears on exactly the two intended A instances. After that, add a general dogleg/channel planner for opposite-facing ports and then multi-terminal and symmetry-constrained nets.
