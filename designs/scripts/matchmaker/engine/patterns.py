from .plan import PlacementPlan, Tile
from .mos_centroid_orientation_policy import (
    MosCentroidOrientationPolicy,
    get_mos_centroid_orientation_for_tile,
)


def abba_pattern(rows: int, cols: int) -> list[list[str]]:
    """
    Generate an AB/BA common-centroid pattern.

    Example for 2x4:
        A B B A
        B A A B

    Example for 4x4:
        A B B A
        B A A B
        A B B A
        B A A B
    """
    if rows <= 0 or cols <= 0:
        raise ValueError("rows and cols must be positive")

    if cols % 4 != 0:
        raise ValueError("ABBA pattern currently expects columns to be a multiple of 4")

    even_row_base = ["A", "B", "B", "A"]
    odd_row_base = ["B", "A", "A", "B"]

    pattern = []

    for row_index in range(rows):
        base = even_row_base if row_index % 2 == 0 else odd_row_base

        row = []
        while len(row) < cols:
            row.extend(base)

        pattern.append(row[:cols])

    return pattern


def print_pattern(pattern: list[list[str]]) -> None:
    for row in pattern:
        print(" ".join(row))


def make_abba_plan(
    cell_name: str,
    rows: int,
    cols: int,
    orientation_policy: MosCentroidOrientationPolicy | None = None,
) -> PlacementPlan:
    """
    Build a deterministic ABBA common-centroid placement plan.
    """
    if orientation_policy is None:
        orientation_policy = MosCentroidOrientationPolicy(kind="mirror_top_bottom")

    pattern = abba_pattern(rows, cols)

    counts = {"A": 0, "B": 0}
    tiles = []

    for row_index, row in enumerate(pattern):
        for col_index, group in enumerate(row):
            name = f"{group}{counts[group]}"
            counts[group] += 1

            orientation = get_mos_centroid_orientation_for_tile(
                row=row_index,
                col=col_index,
                rows=rows,
                cols=cols,
                policy=orientation_policy,
            )

            tiles.append(
                Tile(
                    name=name,
                    group=group,
                    role="active",
                    row=row_index,
                    col=col_index,
                    orientation=orientation,
                )
            )

    return PlacementPlan(
        cell_name=cell_name,
        rows=rows,
        cols=cols,
        tiles=tuple(tiles),
    )