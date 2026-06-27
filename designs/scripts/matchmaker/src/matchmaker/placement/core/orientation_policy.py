from dataclasses import dataclass
from typing import Literal

from .tile_plan import Orientation


OrientationPolicyKind = Literal[
    "mirror_top_bottom",
    "alternate_by_row",
    "all_r0",
]


@dataclass(frozen=True)
class OrientationPolicy:
    """
    Generic tile-orientation policy.

    This is generic enough to live in placement.core, but device-specific
    compilers may decide which policy is appropriate.
    """

    kind: OrientationPolicyKind = "mirror_top_bottom"


def get_orientation_for_tile(
    row: int,
    col: int,
    rows: int,
    cols: int,
    policy: OrientationPolicy,
) -> Orientation:
    if policy.kind == "all_r0":
        return "R0"

    if policy.kind == "alternate_by_row":
        return "MY" if row % 2 == 0 else "R0"

    if policy.kind == "mirror_top_bottom":
        if rows == 1:
            return "R0"

        if row < rows / 2:
            return "MY"

        return "R0"

    raise NotImplementedError(f"Unsupported orientation policy: {policy.kind}")