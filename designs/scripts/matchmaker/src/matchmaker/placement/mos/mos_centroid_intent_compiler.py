from matchmaker.placement.core.orientation_policy import OrientationPolicy
from matchmaker.placement.core.spacing_policy import TileSpacingPolicy
from matchmaker.placement.mos.mos_centroid_array_intent import (
    MosCentroidArrayIntent,
    get_resolved_mos_centroid_array_shape,
    normalize_mos_centroid_pattern_strategy,
    validate_mos_centroid_array_intent,
)
from matchmaker.placement.mos.mos_centroid_grid_compiler import (
    compile_mos_centroid_grid_to_placement_request,
)
from matchmaker.placement.mos.mos_centroid_placement_request import (
    MosCentroidPlacementRequest,
)
from matchmaker.placement.mos.mos_dummy_policy import MosDummyPolicy
from matchmaker.specs.mos_centroid_array_spec import MosCentroidArraySpec


def make_interdigitated_group_grid(
    rows: int,
    cols: int,
) -> list[list[str]]:
    """
    Build alternating A/B rows.

    Example, rows=2, cols=6:
        A B A B A B
        B A B A B A
    """
    if cols % 2 != 0:
        raise ValueError("interdigitated group grid requires an even number of columns")

    row_a = ["A" if col % 2 == 0 else "B" for col in range(cols)]
    row_b = ["B" if col % 2 == 0 else "A" for col in range(cols)]

    return [
        row_a.copy() if row_index % 2 == 0 else row_b.copy()
        for row_index in range(rows)
    ]


def make_mirrored_pair_group_grid(
    rows: int,
    cols: int,
) -> list[list[str]]:
    """
    Build a mirrored pair pattern.

    Example, rows=2, cols=4:
        A B B A
        B A A B
    """
    if cols % 2 != 0:
        raise ValueError("mirrored_pair group grid requires an even number of columns")

    left_half = ["A" if col % 2 == 0 else "B" for col in range(cols // 2)]
    row_a = left_half + list(reversed(left_half))
    row_b = [
        "B" if entry == "A" else "A"
        for entry in row_a
    ]

    return [
        row_a.copy() if row_index % 2 == 0 else row_b.copy()
        for row_index in range(rows)
    ]


def make_common_centroid_group_grid(
    rows: int,
    cols: int,
) -> list[list[str]]:
    """
    Current two-group common-centroid default.

    For now this aliases to mirrored_pair. Keeping the function separate gives
    us a cleaner place to improve the common-centroid planner later.
    """
    return make_mirrored_pair_group_grid(rows=rows, cols=cols)


def apply_center_pair_dummy_tiles(
    group_grid: list[list[str]],
) -> list[list[str]]:
    """
    Replace the center two columns with dummy tiles.
    """
    if not group_grid:
        raise ValueError("group_grid must not be empty")

    cols = len(group_grid[0])

    if cols < 4:
        raise ValueError("center_pair dummy strategy requires at least 4 columns")

    left_center = cols // 2 - 1
    right_center = cols // 2

    new_grid = [row.copy() for row in group_grid]

    for row in new_grid:
        row[left_center] = "D"
        row[right_center] = "D"

    return new_grid


def compile_mos_centroid_intent_to_grid(
    intent: MosCentroidArrayIntent,
) -> list[list[str]]:
    """
    Compile high-level MOS centroid intent into the internal placement grid.
    """
    validate_mos_centroid_array_intent(intent)

    rows, cols = get_resolved_mos_centroid_array_shape(intent)
    pattern_strategy = normalize_mos_centroid_pattern_strategy(intent.pattern_strategy)

    if pattern_strategy == "custom_grid":
        if intent.group_grid is None:
            raise ValueError("custom_grid strategy requires group_grid")
        group_grid = [row.copy() for row in intent.group_grid]

    elif pattern_strategy == "interdigitated":
        group_grid = make_interdigitated_group_grid(rows=rows, cols=cols)

    elif pattern_strategy == "mirrored_pair":
        group_grid = make_mirrored_pair_group_grid(rows=rows, cols=cols)

    elif pattern_strategy == "common_centroid":
        group_grid = make_common_centroid_group_grid(rows=rows, cols=cols)

    else:
        raise NotImplementedError(
            f"Unsupported normalized pattern strategy: {pattern_strategy}"
        )

    if intent.dummy_tile_strategy == "center_pair":
        group_grid = apply_center_pair_dummy_tiles(group_grid)

    return group_grid


def compile_mos_centroid_intent_to_placement_request(
    intent: MosCentroidArrayIntent,
    orientation_policy: OrientationPolicy | None = None,
    dummy_policy: MosDummyPolicy | None = None,
    spacing_policy: TileSpacingPolicy | None = None,
) -> MosCentroidPlacementRequest:
    """
    Compile high-level MOS centroid intent into a physical placement request.
    """
    rows, cols = get_resolved_mos_centroid_array_shape(intent)
    group_grid = compile_mos_centroid_intent_to_grid(intent)
    pattern_strategy = normalize_mos_centroid_pattern_strategy(intent.pattern_strategy)

    spec = MosCentroidArraySpec(
        cell_name=intent.cell_name,
        device_a=intent.device_a,
        device_b=intent.device_b,
        rows=rows,
        cols=cols,
        pattern=pattern_strategy,
    )

    return compile_mos_centroid_grid_to_placement_request(
        spec=spec,
        group_grid=group_grid,
        orientation_policy=orientation_policy,
        dummy_policy=dummy_policy,
        spacing_policy=spacing_policy,
        primitive_options=intent.primitive_options,
    )