from dataclasses import dataclass, field

from matchmaker.placement.core.spacing_policy import TileSpacingPolicy
from matchmaker.placement.core.tile_plan import PlacementPlan
from matchmaker.placement.mos.mos_dummy_policy import MosDummyPolicy
from matchmaker.placement.mos.mos_group_device_binding import MosGroupDeviceMap
from matchmaker.specs.mos_centroid_array_spec import MosCentroidArraySpec


@dataclass(frozen=True)
class MosCentroidPlacementRequest:
    """
    Complete input package for MOS centroid placement.

    This is the object future spec-to-layout code should produce before handing
    work to the physical placement builder.
    """

    spec: MosCentroidArraySpec
    plan: PlacementPlan
    device_by_group: MosGroupDeviceMap | None = None
    dummy_policy: MosDummyPolicy = field(
        default_factory=lambda: MosDummyPolicy(kind="edge_only")
    )
    spacing_policy: TileSpacingPolicy = field(
        default_factory=lambda: TileSpacingPolicy(kind="bbox_plus_margin")
    )


def validate_mos_centroid_placement_request(
    request: MosCentroidPlacementRequest,
) -> None:
    if request.spec.rows != request.plan.rows or request.spec.cols != request.plan.cols:
        raise ValueError(
            "request spec dimensions do not match placement plan dimensions: "
            f"spec=({request.spec.rows}, {request.spec.cols}), "
            f"plan=({request.plan.rows}, {request.plan.cols})"
        )

    if request.spec.cell_name != request.plan.cell_name:
        raise ValueError(
            "request spec cell_name does not match placement plan cell_name: "
            f"spec={request.spec.cell_name!r}, "
            f"plan={request.plan.cell_name!r}"
        )