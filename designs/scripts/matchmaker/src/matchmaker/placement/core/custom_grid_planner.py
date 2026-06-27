from .orientation_policy import (
    OrientationPolicy,
    get_orientation_for_tile,
)
from .tile_plan import PlacementPlan, Tile, TileRole


def validate_group_grid(group_grid: list[list[str]]) -> tuple[int, int]:
    """
    Validate a user/compiler-provided group grid.
    """
    if not group_grid:
        raise ValueError("group_grid must contain at least one row")

    row_lengths = {len(row) for row in group_grid}

    if len(row_lengths) != 1:
        raise ValueError("all rows in group_grid must have the same length")

    rows = len(group_grid)
    cols = len(group_grid[0])

    if rows <= 0 or cols <= 0:
        raise ValueError("group_grid must have positive dimensions")

    for row in group_grid:
        for entry in row:
            if not isinstance(entry, str) or not entry:
                raise ValueError("each grid entry must be a non-empty string")

    return rows, cols


def get_tile_role_from_grid_entry(entry: str) -> TileRole:
    """
    Interpret a grid entry as a generic tile role.

    Current convention:
        A, B, C, ... -> active group
        D            -> dummy tile
        .            -> empty slot
    """
    if entry == ".":
        return "empty"

    if entry == "D":
        return "dummy"

    return "active"


def make_placement_plan_from_group_grid(
    cell_name: str,
    group_grid: list[list[str]],
    orientation_policy: OrientationPolicy | None = None,
) -> PlacementPlan:
    """
    Build a generic PlacementPlan from an explicit group grid.
    """
    if orientation_policy is None:
        orientation_policy = OrientationPolicy(kind="mirror_top_bottom")

    rows, cols = validate_group_grid(group_grid)

    counts: dict[str, int] = {}
    tiles = []

    for row_index, row in enumerate(group_grid):
        for col_index, entry in enumerate(row):
            role = get_tile_role_from_grid_entry(entry)

            if role == "empty":
                group = "."
            elif role == "dummy":
                group = "D"
            else:
                group = entry

            group_count = counts.get(group, 0)
            name = f"{group}{group_count}" if group != "." else f"EMPTY{group_count}"
            counts[group] = group_count + 1

            orientation = get_orientation_for_tile(
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
                    role=role,
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