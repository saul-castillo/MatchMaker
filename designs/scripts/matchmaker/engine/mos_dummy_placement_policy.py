from dataclasses import dataclass
from typing import Literal

from .plan import PlacementPlan, Tile


MosDummyPolicyKind = Literal["edge_only", "none", "all"]


@dataclass(frozen=True)
class MosDummyPlacementPolicy:
    """
    Controls dummy placement for MOS centroid arrays.
    """

    kind: MosDummyPolicyKind = "edge_only"


def get_mos_dummy_configuration_for_tile(
    tile: Tile,
    plan: PlacementPlan,
    policy: MosDummyPlacementPolicy,
) -> tuple[bool, bool]:
    """
    Return (left_dummy, right_dummy) for one MOS tile.
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