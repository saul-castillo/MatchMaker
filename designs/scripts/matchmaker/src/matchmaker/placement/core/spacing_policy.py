from dataclasses import dataclass
from typing import Literal


TileSpacingPolicyKind = Literal[
    "bbox_plus_margin",
    "fixed_pitch",
]


@dataclass(frozen=True)
class TileSpacingPolicy:
    """
    Generic tile pitch policy.

    bbox_plus_margin:
        Uses the largest unit-cell bounding box and adds margins.

    fixed_pitch:
        Uses explicit x/y pitch values.
    """

    kind: TileSpacingPolicyKind = "bbox_plus_margin"
    x_margin: float = 2.0
    y_margin: float = 2.0
    x_pitch: float | None = None
    y_pitch: float | None = None


def calculate_tile_pitch_from_unit_sizes(
    unit_widths: list[float],
    unit_heights: list[float],
    spacing_policy: TileSpacingPolicy,
) -> tuple[float, float]:
    if not unit_widths or not unit_heights:
        raise ValueError("unit_widths and unit_heights must not be empty")

    if spacing_policy.kind == "bbox_plus_margin":
        return (
            max(unit_widths) + spacing_policy.x_margin,
            max(unit_heights) + spacing_policy.y_margin,
        )

    if spacing_policy.kind == "fixed_pitch":
        if spacing_policy.x_pitch is None or spacing_policy.y_pitch is None:
            raise ValueError("fixed_pitch requires x_pitch and y_pitch")

        return spacing_policy.x_pitch, spacing_policy.y_pitch

    raise NotImplementedError(f"Unsupported tile spacing policy: {spacing_policy.kind}")