from dataclasses import dataclass
from typing import Literal

from matchmaker.placement.core.tile_plan import PlacementPlan, Tile


MosDummyPolicyKind = Literal[
    "none",
    "edge_only",
    "all",
]


@dataclass(frozen=True)
class MosDummyPolicy:
    """
    MOS primitive-level dummy policy.

    This controls dummy devices attached to MOS primitive cells. This is
    different from dummy placement tiles in the grid.
    """

    kind: MosDummyPolicyKind = "edge_only"


def get_mos_primitive_dummy_configuration_for_tile(
    tile: Tile,
    plan: PlacementPlan,
    policy: MosDummyPolicy,
) -> tuple[bool, bool]:
    """
    Return (left_dummy, right_dummy) for one active MOS tile.
    """
    if policy.kind == "none":
        return (False, False)

    if policy.kind == "all":
        return (True, True)

    if policy.kind == "edge_only":
        is_left_edge = tile.col == 0
        is_right_edge = tile.col == plan.cols - 1
        return (is_left_edge, is_right_edge)

    raise NotImplementedError(f"Unsupported MOS dummy policy: {policy.kind}")