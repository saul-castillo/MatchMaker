import argparse
import os
from pathlib import Path

from glayout import gf180

from matchmaker.outputs.core_analog_cell_paths import create_core_analog_cell_paths
from matchmaker.placement.mos.mos_centroid_array_intent import MosCentroidArrayIntent
from matchmaker.placement.mos.mos_centroid_intent_compiler import (
    compile_mos_centroid_intent_to_placement_request,
)
from matchmaker.placement.mos.mos_centroid_placement_builder import (
    build_mos_centroid_placement_from_request,
)
from matchmaker.routing.intents.point_to_point_route_intent import (
    PointToPointRouteIntent,
    RouteEndpoint,
)
from matchmaker.routing.ports.mos_centroid_port_namespace import (
    expose_mos_centroid_tile_ports,
)
from matchmaker.routing.routers.glayout_point_to_point_router import (
    route_point_to_point_intent,
)
from matchmaker.specs.mos_device_spec import MosDeviceSpec
from matchmaker.verification.generated_cell_verifier import verify_generated_cell


CELL_NAME = "nfet_centroid_gate_route_demo"


def build_routed_demo():
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

    intent = MosCentroidArrayIntent(
        cell_name=CELL_NAME,
        device_a=nfet_a,
        device_b=nfet_b,
        rows=2,
        cols=4,
        pattern_strategy="common centroid",
    )
    request = compile_mos_centroid_intent_to_placement_request(intent)
    top = build_mos_centroid_placement_from_request(request)
    expose_mos_centroid_tile_ports(top, request.plan)

    route_intent = PointToPointRouteIntent(
        net_name="A_gate_pair",
        source=RouteEndpoint(instance_name="A0", port_name="gate_E"),
        target=RouteEndpoint(instance_name="A1", port_name="gate_E"),
        avoid_obstacles=True,
        obstacle_clearance=1.0,
    )
    executed = route_point_to_point_intent(
        component=top,
        pdk=gf180,
        intent=route_intent,
    )
    return top, executed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate, route, DRC, and extract the centroid routing demo."
    )
    parser.add_argument(
        "--designs-root",
        type=Path,
        default=Path(os.environ.get("DESIGNS_ROOT", "/foss/designs")),
    )
    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Write the GDS without running DRC or extraction.",
    )
    args = parser.parse_args()

    top, executed = build_routed_demo()
    paths = create_core_analog_cell_paths(args.designs_root, CELL_NAME)
    top.write_gds(str(paths.final_gds))

    print(f"route strategy: {executed.plan.strategy}")
    print(f"straight-route blockers: {executed.blockers or '(none)'}")
    print(f"actual source access: {executed.plan.source_top_port_name}")
    print(f"actual target access: {executed.plan.target_top_port_name}")
    print(f"detour direction: {executed.detour_direction or '(none)'}")
    print(f"detour channel coordinate: {executed.detour_channel_coordinate}")
    print(f"GDS: {paths.final_gds}")

    if args.skip_verification:
        return 0

    verification = verify_generated_cell(
        designs_root=args.designs_root,
        cell_name=CELL_NAME,
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

    print(f"pre-LVS checks passed: {verification.passed}")
    return 0 if verification.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
