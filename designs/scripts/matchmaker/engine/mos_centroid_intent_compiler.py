from .spec import CentroidArraySpec
from .mos_centroid_array_intent import (
    MosCentroidArrayIntent,
    validate_mos_centroid_array_intent,
)
from .mos_centroid_orientation_policy import MosCentroidOrientationPolicy
from .mos_dummy_placement_policy import MosDummyPlacementPolicy
from .mos_centroid_spacing_policy import MosCentroidSpacingPolicy
from .mos_centroid_grid_compiler import (
    compile_mos_centroid_grid_to_placement_request,
)
from .mos_centroid_placement_request import MosCentroidPlacementRequest


def make_abba_group_grid(
    rows: int,
    cols: int,
) -> list[list[str]]:
    """
    Build a simple A/B ABBA-style matched grid.

    Example, rows=2, cols=4:
        A B B A
        B A A B
    """
    if cols % 2 != 0:
        raise ValueError("ABBA group grid requires an even number of columns")

    half_pattern = ["A", "B"] * (cols // 2)
    mirrored_half_pattern = list(reversed(half_pattern))

    row_a = mirrored_half_pattern
    row_b = half_pattern

    grid = []

    for row_index in range(rows):
        if row_index % 2 == 0:
            grid.append(row_a.copy())
        else:
            grid.append(row_b.copy())

    return grid


def apply_center_pair_dummy_tiles(
    group_grid: list[list[str]],
) -> list[list[str]]:
    """
    Replace the center two columns with dummy tiles.

    Example:
        A B B A
        B A A B

    becomes:
        A D D A
        B D D B
    """
    rows = len(group_grid)
    cols = len(group_grid[0])

    if cols < 4:
        raise ValueError("center_pair dummy strategy requires at least 4 columns")

    left_center = cols // 2 - 1
    right_center = cols // 2

    new_grid = [row.copy() for row in group_grid]

    for row_index in range(rows):
        new_grid[row_index][left_center] = "D"
        new_grid[row_index][right_center] = "D"

    return new_grid


def compile_mos_centroid_intent_to_grid(
    intent: MosCentroidArrayIntent,
) -> list[list[str]]:
    """
    Compile high-level MOS centroid intent into the internal placement grid.
    """
    validate_mos_centroid_array_intent(intent)

    if intent.pattern_style == "abba":
        group_grid = make_abba_group_grid(
            rows=intent.rows,
            cols=intent.cols,
        )
    else:
        raise NotImplementedError(
            "custom pattern_style should use the existing explicit grid compiler for now"
        )

    if intent.dummy_tile_strategy == "center_pair":
        group_grid = apply_center_pair_dummy_tiles(group_grid)

    return group_grid


def compile_mos_centroid_intent_to_placement_request(
    intent: MosCentroidArrayIntent,
    orientation_policy: MosCentroidOrientationPolicy | None = None,
    dummy_policy: MosDummyPlacementPolicy | None = None,
    spacing_policy: MosCentroidSpacingPolicy | None = None,
) -> MosCentroidPlacementRequest:
    """
    Compile high-level MOS centroid intent into a physical placement request.
    """
    group_grid = compile_mos_centroid_intent_to_grid(intent)

    spec = CentroidArraySpec(
        cell_name=intent.cell_name,
        device_a=intent.device_a,
        device_b=intent.device_b,
        rows=intent.rows,
        cols=intent.cols,
        pattern=intent.pattern_style,
    )

    return compile_mos_centroid_grid_to_placement_request(
        spec=spec,
        group_grid=group_grid,
        orientation_policy=orientation_policy,
        dummy_policy=dummy_policy,
        spacing_policy=spacing_policy,
    )