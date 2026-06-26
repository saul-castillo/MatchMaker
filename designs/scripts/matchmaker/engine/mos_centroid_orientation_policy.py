from dataclasses import dataclass
from typing import Literal

from .plan import Orientation


MosCentroidOrientationPolicyKind = Literal[
    "mirror_top_bottom",
    "alternate_by_row",
    "all_r0",
]


@dataclass(frozen=True)
class MosCentroidOrientationPolicy:
    """
    Controls how MOS tiles are oriented inside a centroid array.

    mirror_top_bottom:
        Top half is mirrored, bottom half is unmirrored.
        This generalizes the original 2-row demo behavior.

    alternate_by_row:
        Even rows are mirrored, odd rows are unmirrored.

    all_r0:
        Every tile is unmirrored.
    """

    kind: MosCentroidOrientationPolicyKind = "mirror_top_bottom"


def get_mos_centroid_orientation_for_tile(
    row: int,
    col: int,
    rows: int,
    cols: int,
    policy: MosCentroidOrientationPolicy,
) -> Orientation:
    """
    Return the orientation for one MOS centroid tile.

    The col/cols arguments are included so future orientation policies can
    depend on both row and column without changing the function signature.
    """
    if policy.kind == "all_r0":
        return "R0"

    if policy.kind == "alternate_by_row":
        return "MY" if row % 2 == 0 else "R0"

    if policy.kind == "mirror_top_bottom":
        if rows == 1:
            return "R0"

        midpoint = rows / 2

        if row < midpoint:
            return "MY"

        return "R0"

    raise NotImplementedError(
        f"Unsupported MOS centroid orientation policy: {policy.kind}"
    )