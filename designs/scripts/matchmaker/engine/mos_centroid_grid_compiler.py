from .spec import CentroidArraySpec
from .custom_centroid_pattern_planner import make_custom_centroid_plan
from .mos_centroid_orientation_policy import MosCentroidOrientationPolicy
from .mos_dummy_placement_policy import MosDummyPlacementPolicy
from .mos_centroid_spacing_policy import MosCentroidSpacingPolicy
from .mos_group_device_binding import (
    MosGroupDeviceMap,
    create_mos_group_device_map_from_centroid_spec,
)
from .mos_centroid_placement_request import (
    MosCentroidPlacementRequest,
    validate_mos_centroid_placement_request,
)


def compile_mos_centroid_grid_to_placement_request(
    spec: CentroidArraySpec,
    group_grid: list[list[str]],
    orientation_policy: MosCentroidOrientationPolicy | None = None,
    dummy_policy: MosDummyPlacementPolicy | None = None,
    spacing_policy: MosCentroidSpacingPolicy | None = None,
    device_by_group: MosGroupDeviceMap | None = None,
) -> MosCentroidPlacementRequest:
    """
    Compile an explicit MOS centroid grid into a placement request.

    This is the preferred frontend for the placement engine.

    Input:
        spec:
            Describes the cell and available MOS devices.

        group_grid:
            Explicit tile grid.
            Example:
                [
                    ["A", "B", "D", "D", "B", "A"],
                    ["B", "A", "D", "D", "A", "B"],
                ]

            Current conventions:
                A/B/C/... -> active device groups
                D         -> dummy tile
                .         -> empty slot

        orientation_policy:
            Controls tile mirroring/orientation.

        dummy_policy:
            Controls primitive-level dummy usage for active tiles.

        spacing_policy:
            Controls tile pitch.

        device_by_group:
            Maps active group symbols to DeviceSpec objects.
            If omitted, defaults to:
                spec.device_a.name -> spec.device_a
                spec.device_b.name -> spec.device_b

    Output:
        MosCentroidPlacementRequest
    """
    if dummy_policy is None:
        dummy_policy = MosDummyPlacementPolicy(kind="edge_only")

    if spacing_policy is None:
        spacing_policy = MosCentroidSpacingPolicy(kind="bbox_plus_margin")

    if device_by_group is None:
        device_by_group = create_mos_group_device_map_from_centroid_spec(spec)

    plan = make_custom_centroid_plan(
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