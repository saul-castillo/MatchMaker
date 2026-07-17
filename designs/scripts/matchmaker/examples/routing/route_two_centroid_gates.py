import argparse
import os
from pathlib import Path

from glayout import gf180

from matchmaker.outputs.core_analog_cell_paths import create_core_analog_cell_paths
from matchmaker.physical.models import TerminalRef
from matchmaker.physical.mos_centroid_snapshot import (
    create_mos_centroid_physical_design_snapshot,
)
from matchmaker.placement.mos.mos_centroid_array_intent import MosCentroidArrayIntent
from matchmaker.placement.mos.mos_centroid_intent_compiler import (
    compile_mos_centroid_intent_to_placement_request,
)
from matchmaker.placement.mos.mos_centroid_placement_builder import (
    build_mos_centroid_placement_from_request,
)
from matchmaker.routing.intents.net_intent import NetConstraintProfile, NetIntent
from matchmaker.routing.planners.two_terminal_net_planner import (
    plan_two_terminal_net_with_report,
)
from matchmaker.routing.routers.route_plan_executor import execute_route_plan
from matchmaker.specs.mos_device_spec import MosDeviceSpec
from matchmaker.verification.generated_cell_verifier import verify_generated_cell
from matchmaker.verification.netlist.connectivity_assertions import (
    SharedNetConnectivityExpectation,
)


DEFAULT_CELL_NAME = "nfet_centroid_gate_route_demo"
DEFAULT_SOURCE_INSTANCE = "A0"
DEFAULT_TARGET_INSTANCE = "A1"


def build_routed_demo(
    *,
    cell_name: str = DEFAULT_CELL_NAME,
    source_instance: str = DEFAULT_SOURCE_INSTANCE,
    target_instance: str = DEFAULT_TARGET_INSTANCE,
    strategy_preference: str = "auto",
):
    gf180.activate()

    nfet_a = MosDeviceSpec(
        name="A",
        kind="nfet",
        width=3.0,
        length=None,
        fingers=1,
    )
    nfet_b = MosDeviceSpec(
        name="B",
        kind="nfet",
        width=3.0,
        length=None,
        fingers=1,
    )

    placement_intent = MosCentroidArrayIntent(
        cell_name=cell_name,
        device_a=nfet_a,
        device_b=nfet_b,
        rows=2,
        cols=4,
        pattern_strategy="common centroid",
    )
    request = compile_mos_centroid_intent_to_placement_request(placement_intent)
    top = build_mos_centroid_placement_from_request(request)
    physical_design = create_mos_centroid_physical_design_snapshot(
        component=top,
        plan=request.plan,
    )

    net_intent = NetIntent(
        name=f"{source_instance}_{target_instance}_gate_pair",
        terminals=(
            TerminalRef(source_instance, "gate"),
            TerminalRef(target_instance, "gate"),
        ),
        constraints=NetConstraintProfile(
            width_class="signal",
            avoid_obstacles=True,
            obstacle_clearance=1.0,
        ),
        strategy_preference=strategy_preference,
    )
    planning = plan_two_terminal_net_with_report(
        intent=net_intent,
        physical_design=physical_design,
    )
    executed = execute_route_plan(component=top, plan=planning.plan)
    return top, physical_design, net_intent, planning, executed


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate, logically route, DRC, extract, and connectivity-check "
            "one pair of centroid-array MOS gates."
        )
    )
    parser.add_argument(
        "--designs-root",
        type=Path,
        default=Path(os.environ.get("DESIGNS_ROOT", "/foss/designs")),
    )
    parser.add_argument("--cell-name", default=DEFAULT_CELL_NAME)
    parser.add_argument("--source-instance", default=DEFAULT_SOURCE_INSTANCE)
    parser.add_argument("--target-instance", default=DEFAULT_TARGET_INSTANCE)
    parser.add_argument(
        "--strategy",
        choices=("auto", "straight", "manhattan", "dogleg"),
        default="auto",
    )
    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Write the GDS without running DRC, extraction, or connectivity checks.",
    )
    args = parser.parse_args()

    top, physical_design, net_intent, planning, executed = build_routed_demo(
        cell_name=args.cell_name,
        source_instance=args.source_instance,
        target_instance=args.target_instance,
        strategy_preference=args.strategy,
    )
    route_plan = executed.plan
    paths = create_core_analog_cell_paths(args.designs_root, args.cell_name)
    top.write_gds(str(paths.final_gds))

    print(
        "logical terminals: "
        + ", ".join(
            f"{terminal.instance_name}.{terminal.terminal_name}"
            for terminal in net_intent.terminals
        )
    )
    print(f"route strategy: {route_plan.strategy}")
    print(f"direct-route blockers: {route_plan.blockers or '(none)'}")
    print(f"actual source access: {route_plan.selected_access_point_names[0]}")
    print(f"actual target access: {route_plan.selected_access_point_names[1]}")
    print(f"channel direction: {route_plan.channel_direction or '(none)'}")
    print(f"channel coordinate: {route_plan.channel_coordinate}")
    print(
        "route points: "
        + " -> ".join(
            str(segment.start) for segment in route_plan.segments
        )
        + f" -> {route_plan.segments[-1].end}"
    )
    print(f"route length: {route_plan.metrics.total_length}")
    print(f"route bends: {route_plan.metrics.bend_count}")
    print(f"route width: {route_plan.metrics.resolved_width}")
    print(f"route estimated cost: {route_plan.metrics.estimated_cost}")
    print(f"feasible route candidates: {len(planning.dispatch.candidates)}")
    print(f"rejected route candidates: {len(planning.dispatch.rejections)}")
    print(f"physical instances: {len(physical_design.instances)}")
    print(f"physical access points: {len(physical_design.access_points)}")
    print(f"GDS: {paths.final_gds}")

    if args.skip_verification:
        return 0

    endpoint_cell_names = (
        physical_design.instance(args.source_instance).cell_name,
        physical_design.instance(args.target_instance).cell_name,
    )
    verification = verify_generated_cell(
        designs_root=args.designs_root,
        cell_name=args.cell_name,
        connectivity_expectation=SharedNetConnectivityExpectation(
            expected_subcircuit_names=endpoint_cell_names,
            description=(
                f"{args.source_instance}.gate connected only to "
                f"{args.target_instance}.gate"
            ),
        ),
    )
    print(f"DRC passed: {verification.drc.passed}")
    print(f"DRC violations: {verification.drc.violation_count}")
    print(f"DRC report: {verification.paths.drc_report}")

    extraction = verification.extraction
    if extraction is not None:
        print(f"extraction passed: {extraction.passed}")
        print(f"extracted netlist: {extraction.netlist_path}")
        print(f"extraction report: {verification.paths.extraction_report}")
        if extraction.failure_reason is not None:
            print(f"extraction failure: {extraction.failure_reason}")

    connectivity = verification.connectivity
    if connectivity is not None:
        print(f"connectivity passed: {connectivity.passed}")
        print(f"connectivity net: {connectivity.matched_net}")
        print(
            "connectivity instances: "
            + ", ".join(
                instance.name for instance in connectivity.actual_instances
            )
        )
        print(f"connectivity report: {verification.paths.connectivity_report}")
        if connectivity.failure_reason is not None:
            print(f"connectivity failure: {connectivity.failure_reason}")

    print(f"pre-LVS checks passed: {verification.passed}")
    return 0 if verification.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
