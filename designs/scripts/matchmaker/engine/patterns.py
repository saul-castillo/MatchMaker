def abba_pattern(rows: int, cols: int) -> list[list[str]]:
    """
    Generate an AB/BA common-centroid pattern.

    Example for 2x4:
        A B B A
        B A A B
    """
    if rows <= 0 or cols <= 0:
        raise ValueError("rows and cols must be positive")

    if cols % 2 != 0:
        raise ValueError("ABBA pattern currently expects an even number of columns")

    base = ["A", "B", "B", "A"]

    pattern = []
    for r in range(rows):
        row = []
        while len(row) < cols:
            row.extend(base)

        row = row[:cols]

        if r % 2 == 1:
            row = ["B" if x == "A" else "A" for x in row]

        pattern.append(row)

    return pattern


def print_pattern(pattern: list[list[str]]) -> None:
    for row in pattern:
        print(" ".join(row))

from .plan import PlacementPlan, Tile


def make_abba_plan(cell_name: str, rows: int, cols: int) -> PlacementPlan:
    """
    Build a deterministic ABBA common-centroid placement plan.

    Example for 2x4:
        A B B A
        B A A B
    """
    pattern = abba_pattern(rows, cols)

    counts = {"A": 0, "B": 0}
    tiles = []

    for row_index, row in enumerate(pattern):
        for col_index, group in enumerate(row):
            name = f"{group}{counts[group]}"
            counts[group] += 1

            # Matches the current demo convention:
            # top row is mirrored, bottom row is unmirrored.
            orientation = "MY" if row_index == 0 else "R0"

            tiles.append(
                Tile(
                    name=name,
                    group=group,
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