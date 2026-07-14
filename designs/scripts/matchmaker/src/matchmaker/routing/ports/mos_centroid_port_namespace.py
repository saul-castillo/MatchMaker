from matchmaker.physical.mos_centroid_snapshot import (
    create_mos_centroid_physical_design_snapshot,
)
from matchmaker.placement.core.tile_plan import PlacementPlan


def expose_mos_centroid_tile_ports(
    component,
    plan: PlacementPlan,
    separator: str = "__",
):
    """Compatibility wrapper that promotes ports and records routing metadata.

    New code should call ``create_mos_centroid_physical_design_snapshot`` and
    retain the returned snapshot. This wrapper remains for existing examples and
    callers that only expect the component back.
    """
    snapshot = create_mos_centroid_physical_design_snapshot(
        component=component,
        plan=plan,
        separator=separator,
    )
    return snapshot.component
