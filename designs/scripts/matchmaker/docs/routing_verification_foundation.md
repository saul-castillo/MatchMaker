# Routing and Verification Foundation

This milestone adds the first deterministic routing path and headless DRC/LVS adapters.

## Routing flow

```text
placement component + placement plan
→ promote tile ports into stable names
→ PointToPointRouteIntent
→ PointToPointRoutePlan
→ gLayout route-family execution
→ routed component
```

A placed MOS tile port is promoted as:

```text
<tile_name>__<primitive_port_name>
```

For example:

```text
A0__gate_E
B1__drain_N
```

The planner is intentionally independent of gLayout. For `strategy="auto"`, it selects a route family from port orientation and alignment:

```text
parallel + inline                   → straight
perpendicular                      → L
parallel + same-facing, non-inline → C
parallel + opposite-facing         → smart-route fallback
```

Run the first routing demo inside the Chipathon container:

```bash
cd /foss/designs
source scripts/matchmaker/env/setup.sh
python scripts/matchmaker/examples/routing/route_two_centroid_gates.py
```

The current routing slice is point-to-point only. It does not yet solve multi-terminal net topology, obstacle avoidance, balanced differential routing, shield insertion, or CDAC bus routing.

## DRC flow

`run_magic_drc(...)` launches Magic headlessly, reads the generated GDS, runs `drc catchup`, emits a tagged total violation count, stores the complete tool output, and returns a structured `MagicDrcResult`.

Use the standard output paths already created by `create_core_analog_cell_paths(...)`:

```python
result = run_magic_drc(
    gds_path=paths.final_gds,
    cell_name=cell_name,
    report_path=paths.drc_report,
)
```

A DRC run passes only when Magic exits successfully and the parsed violation count is exactly zero. A missing count marker is treated as an unsuccessful verification result rather than a clean design.

## LVS flow

`run_magic_netgen_lvs(...)` performs two explicit stages:

```text
GDS
→ Magic extraction for LVS
→ layout SPICE netlist
→ Netgen batch comparison against schematic SPICE
→ structured pass/fail result + report
```

For GF180 in the Chipathon container, configure the Netgen setup file explicitly:

```python
config = MagicNetgenLvsConfig(
    netgen_setup_file=Path(
        "/foss/pdks/gf180mcuD/libs.tech/netgen/gf180mcuD_setup.tcl"
    )
)
```

The LVS parser currently accepts only an unqualified unique circuit match. Mismatch, property-error, and port-error outcomes fail.

## Tests

The routing planner and verification-output parsers are covered by standard-library `unittest` tests:

```bash
cd /foss/designs
source scripts/matchmaker/env/setup.sh
python -m unittest discover \
    -s scripts/matchmaker/tests \
    -p 'test_*.py' \
    -v
```

The next routing milestone should be a multi-terminal net planner that builds a route tree from logical nets, followed by obstacle/channel constraints and symmetry-aware differential routing. DRC/LVS feedback should consume the structured result objects instead of invoking tools directly.
