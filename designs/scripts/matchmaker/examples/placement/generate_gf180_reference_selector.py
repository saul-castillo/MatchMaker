import argparse
import os
from pathlib import Path

from glayout import gf180

from matchmaker.design.reference_selector_naming import (
    VREF_SWITCH_INSTANCE_NAME,
    VSS_SWITCH_INSTANCE_NAME,
)
from matchmaker.generators.reference_selector_generator import (
    generate_reference_selector,
)
from matchmaker.outputs.core_analog_cell_paths import create_core_analog_cell_paths
from matchmaker.placement.cdac.reference_selector_intent import (
    ReferenceSelectorLayoutIntent,
)
from matchmaker.specs.banked_cdac_spec import (
    make_gf180_4bit_banked_cdac_reference_spec,
)
from matchmaker.verification.drc.magic_drc import run_magic_drc
from matchmaker.verification.extraction.magic_extraction import run_magic_extraction
from matchmaker.verification.netlist.shared_net_multiplicity import (
    SharedNetMultiplicityExpectation,
    evaluate_extracted_shared_net_multiplicity,
)


DEFAULT_CELL_NAME = "gf180_cdac_b0_reference_selector_demo"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the B0 VREF/VSS selector from typed intent, run Magic "
            "DRC/extraction, and require five shared signal/control/supply nets "
            "between its balanced R0/R180 transmission-gate children."
        )
    )
    parser.add_argument(
        "--designs-root",
        type=Path,
        default=Path(os.environ.get("DESIGNS_ROOT", "/foss/designs")),
    )
    parser.add_argument("--cell-name", default=DEFAULT_CELL_NAME)
    parser.add_argument("--skip-verification", action="store_true")
    args = parser.parse_args()

    gf180.activate()
    cdac_spec = make_gf180_4bit_banked_cdac_reference_spec()
    bank = cdac_spec.ordered_banks[0]
    intent = ReferenceSelectorLayoutIntent(
        spec=bank.selector,
        cell_name=args.cell_name,
    )
    generated = generate_reference_selector(intent)
    paths = create_core_analog_cell_paths(args.designs_root, args.cell_name)
    generated.component.write_gds(paths.final_gds)

    (xmin, ymin), (xmax, ymax) = generated.component.bbox
    print(f"generated cell: {args.cell_name}")
    print(f"bank: {bank.logical_name}")
    print(
        "requested switch dimensions: "
        f"nmos=(W={bank.selector.switch.nmos.width}, "
        f"L={bank.selector.switch.nmos.length}), "
        f"pmos=(W={bank.selector.switch.pmos.width}, "
        f"L={bank.selector.switch.pmos.length})"
    )
    print(
        "generated bbox: "
        f"({float(xmin)}, {float(ymin)}) to ({float(xmax)}, {float(ymax)})"
    )
    print(f"physical child instances: {len(generated.physical_design.instances)}")
    print(
        "child orientations: "
        + ", ".join(
            f"{name}={instance.orientation}"
            for name, instance in generated.physical_design.instances.items()
        )
    )
    print(f"physical access points: {len(generated.physical_design.access_points)}")
    print(f"routing obstacles: {len(generated.physical_design.obstacles)}")
    print("public ports: " + ", ".join(generated.public_port_names))

    for plan in generated.routes.plans:
        points = [plan.segments[0].start]
        points.extend(segment.end for segment in plan.segments)
        print(f"route {plan.net_name} strategy: {plan.strategy}")
        print(
            f"route {plan.net_name} accesses: "
            + ", ".join(plan.selected_access_point_names)
        )
        print(
            f"route {plan.net_name} points: "
            + " -> ".join(str(point) for point in points)
        )
        print(f"route {plan.net_name} length: {plan.metrics.total_length}")
        print(f"route {plan.net_name} bends: {plan.metrics.bend_count}")
        print(f"route {plan.net_name} vias: {plan.metrics.via_count}")
        print(f"route {plan.net_name} width: {plan.metrics.resolved_width}")
        print(
            f"route {plan.net_name} layers: "
            + ", ".join(
                map(str, dict.fromkeys(segment.layer for segment in plan.segments))
            )
        )
        if plan.vias:
            print(
                f"route {plan.net_name} via centers: "
                + ", ".join(str(via.center) for via in plan.vias)
            )

    print(f"GDS: {paths.final_gds}")
    if args.skip_verification:
        return 0

    drc = run_magic_drc(
        gds_path=paths.final_gds,
        cell_name=args.cell_name,
        report_path=paths.drc_report,
    )
    print(f"DRC passed: {drc.passed}")
    print(f"DRC violations: {drc.violation_count}")
    print(f"DRC report: {drc.report_path}")
    if not drc.passed:
        return 1

    extraction = run_magic_extraction(
        gds_path=paths.final_gds,
        cell_name=args.cell_name,
        output_netlist_path=paths.extracted_netlist,
    )
    paths.extraction_report.write_text(
        f"passed: {extraction.passed}\n"
        f"failure_reason: {extraction.failure_reason}\n"
        f"netlist: {extraction.netlist_path}\n\n"
        + extraction.process.combined_output
        + "\n"
    )
    print(f"extraction passed: {extraction.passed}")
    print(f"extracted netlist: {extraction.netlist_path}")
    print(f"extraction report: {paths.extraction_report}")
    if not extraction.passed:
        print(f"extraction failure: {extraction.failure_reason}")
        return 1

    expected_cells = (
        generated.physical_design.instance(VREF_SWITCH_INSTANCE_NAME).cell_name,
        generated.physical_design.instance(VSS_SWITCH_INSTANCE_NAME).cell_name,
    )
    connectivity = evaluate_extracted_shared_net_multiplicity(
        netlist_path=paths.extracted_netlist,
        top_cell_name=args.cell_name,
        expectation=SharedNetMultiplicityExpectation(
            expected_subcircuit_names=expected_cells,
            expected_match_count=5,
            description=(
                "reference-selector child switches share exactly COMMON, SELECT, "
                "SELECT_BAR, VSS, and VDD"
            ),
        ),
    )
    paths.connectivity_report.write_text(connectivity.render())
    print(f"connectivity passed: {connectivity.passed}")
    print(f"shared selector net count: {len(connectivity.matched_nets)}")
    print("shared selector nets: " + ", ".join(connectivity.matched_nets))
    print(f"connectivity report: {paths.connectivity_report}")
    if connectivity.failure_reason is not None:
        print(f"connectivity failure: {connectivity.failure_reason}")

    pre_lvs_passed = drc.passed and extraction.passed and connectivity.passed
    print(f"pre-LVS checks passed: {pre_lvs_passed}")
    return 0 if pre_lvs_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
