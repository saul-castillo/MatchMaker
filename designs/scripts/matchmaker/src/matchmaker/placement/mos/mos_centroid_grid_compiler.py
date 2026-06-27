from matchmaker.placement.core.custom_grid_planner import (
    make_placement_plan_from_group_grid,
)
from matchmaker.placement.core.orientation_policy import OrientationPolicy
from matchmaker.placement.core.spacing_policy import TileSpacingPolicy
from matchmaker.placement.mos.mos_centroid_placement_request import (
    MosCentroidPlacementRequest,
    validate_mos_centroid_placement_request,
)
from matchmaker.placement.mos.mos_dummy_policy import MosDummyPolicy
from matchmaker.placement.mos.mos_group_device_binding import (
    MosGroupDeviceMap,
    create_mos_group_device_map_from_centroid_spec,
)
from matchmaker.specs.mos_centroid_array_spec import MosCentroidArraySpec


def compile_mos_centroid_grid_to_placement_request(
    spec: MosCentroidArraySpec,
    group_grid: list[list[str]],
    orientation_policy: OrientationPolicy | None = None,
    dummy_policy: MosDummyPolicy | None = None,
    spacing_policy: TileSpacingPolicy | None = None,
    device_by_group: MosGroupDeviceMap | None = None,
) -> MosCentroidPlacementRequest:
    """
    Compile an explicit MOS centroid grid into a placement request.

    The grid is placement IR. Most future high-level flows should generate this
    grid from intent rather than requiring users to write it manually.
    """
    if dummy_policy is None:
        dummy_policy = MosDummyPolicy(kind="edge_only")

    if spacing_policy is None:
        spacing_policy = TileSpacingPolicy(kind="bbox_plus_margin")

    if device_by_group is None:
        device_by_group = create_mos_group_device_map_from_centroid_spec(spec)

    plan = make_placement_plan_from_group_grid(
        cell_name=spec.cell_name,
        group_grid=group_grid,
        orientation_policy=orientation_policy,
    )

    request = MosCentroidPlacementRequest(
        spec=spec,
        plan=plan,
        device_by_group=device_by_group,
        dummy_policy=dummy_policy,
        spacing_policy=spacing_policy,
    )

    validate_mos_centroid_placement_request(request)

    return request