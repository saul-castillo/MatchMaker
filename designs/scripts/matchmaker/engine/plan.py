from dataclasses import dataclass
from typing import Literal


Orientation = Literal["R0", "MX", "MY", "R180"]
TileRole = Literal["active", "dummy", "empty"]


@dataclass(frozen=True)
class Tile:
    """
    One physical slot in a placement plan.
    """

    name: str
    group: str
    row: int
    col: int
    orientation: Orientation
    role: TileRole = "active"


@dataclass(frozen=True)
class PlacementPlan:
    """
    Pure-Python placement plan.

    This is intentionally independent of gLayout. It describes what should be
    placed, where it belongs in the array, how each tile should be oriented,
    and whether each tile is active, dummy, or empty.
    """

    cell_name: str
    rows: int
    cols: int
    tiles: tuple[Tile, ...]

    def pretty_pattern(self) -> str:
        grid = [["" for _ in range(self.cols)] for _ in range(self.rows)]

        for tile in self.tiles:
            if tile.role == "empty":
                marker = "."
            elif tile.role == "dummy":
                marker = "D"
            else:
                marker = tile.group

            grid[tile.row][tile.col] = marker

        return "\n".join(" ".join(row) for row in grid)

    def describe_tiles(self) -> str:
        lines = []

        for tile in self.tiles:
            lines.append(
                f"{tile.name:4s} "
                f"group={tile.group:2s} "
                f"role={tile.role:6s} "
                f"row={tile.row} "
                f"col={tile.col} "
                f"orientation={tile.orientation}"
            )

        return "\n".join(lines)