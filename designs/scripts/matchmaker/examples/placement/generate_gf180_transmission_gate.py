import argparse
import os
from pathlib import Path

from glayout import gf180

from matchmaker.generators.transmission_gate_generator import (
    generate_transmission_gate,
)
from matchmaker.outputs.core_analog_cell_paths import create_core_analog_cell_paths
from matchmaker.placement.cdac.transmission_gate_intent import (
    TransmissionGateLayoutIntent,
)
from matchmaker.specs.banked_cdac_spec import (
    make_gf180_4bit_banked_cdac_reference_spec,
)
from matchmaker.verification.drc.magic_drc import run_magic_drc


DEFAULT_CELL_NAME = "gf180_cdac_base_transmission_gate_demo"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the base CDAC transmission gate from typed intent and run "
            "GF180 Magic DRC. Bulk/supply port assignment remains a later gate."
        )
    )
    parser.add_argument(
        "--designs-root",
        type=Path,
        default=Path(os.environ.get("DESIGNS_ROOT", "/foss/designs")),
    )
    parser.add_argument("--cell-name", default=DEFAULT_CELL_NAME)
    parser.add_argument("--skip-drc", action="store_true")
    args = parser.parse_args()

    gf180.activate()
    cdac_spec = make_gf180_4bit_banked_cdac_reference_spec()
    switch = cdac_spec.reset_switch
    if switch is None:
        raise RuntimeError("reviewed CDAC preset does not define a reset switch")

    intent = TransmissionGateLayoutIntent(
        spec=switch,
        cell_name=args.cell_name,
    )
    generated = generate_transmission_gate(intent)
    paths = create_core_analog_cell_paths(args.designs_root, args.cell_name)
    generated.component.write_gds(paths.final_gds)

    (xmin, ymin), (xmax, ymax) = generated.component.bbox
    print(f"generated cell: {args.cell_name}")
    print(
        "requested switch dimensions: "
        f"nmos=(W={switch.nmos.width}, L={switch.nmos.length}), "
        f"pmos=(W={switch.pmos.width}, L={switch.pmos.length})"
    )
    print(
        "generated bbox: "
        f"({float(xmin)}, {float(ymin)}) to ({float(xmax)}, {float(ymax)})"
    )
    print(f"physical instances: {len(generated.physical_design.instances)}")
    print(f"physical access points: {len(generated.physical_design.access_points)}")
    print(f"routing obstacles: {len(generated.physical_design.obstacles)}")
    print("public ports: " + ", ".join(generated.public_port_names))

    for plan in generated.routes.plans:
        print(f"route {plan.net_name} strategy: {plan.strategy}")
        print(
            f"route {plan.net_name} accesses: "
            + ", ".join(plan.selected_access_point_names)
        )
        print(
            f"route {plan.net_name} points: "
            f"{plan.segments[0].start} -> {plan.segments[-1].end}"
        )
        print(f"route {plan.net_name} length: {plan.metrics.total_length}")
        print(f"route {plan.net_name} width: {plan.metrics.resolved_width}")
        print(f"route {plan.net_name} layer: {plan.segments[0].layer}")

    print(f"GDS: {paths.final_gds}")
    if args.skip_drc:
        return 0

    drc = run_magic_drc(
        gds_path=paths.final_gds,
        cell_name=args.cell_name,
        report_path=paths.drc_report,
    )
    print(f"DRC passed: {drc.passed}")
    print(f"DRC violations: {drc.violation_count}")
    print(f"DRC report: {drc.report_path}")
    return 0 if drc.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
