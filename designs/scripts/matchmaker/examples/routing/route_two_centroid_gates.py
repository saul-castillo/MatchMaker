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


DESIGNS_ROOT = Path("/foss/designs")
CELL_NAME = "nfet_centroid_gate_route_demo"


gf180.activate()

nfet_a = MosDeviceSpec(name="A", kind="nfet", width=3.0, length=None, fingers=1)
nfet_b = MosDeviceSpec(name="B", kind="nfet", width=3.0, length=None, fingers=1)

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
)
executed = route_point_to_point_intent(
    component=top,
    pdk=gf180,
    intent=route_intent,
)

paths = create_core_analog_cell_paths(DESIGNS_ROOT, CELL_NAME)
top.write_gds(str(paths.final_gds))

print(f"route strategy: {executed.plan.strategy}")
print(f"wrote: {paths.final_gds}")
