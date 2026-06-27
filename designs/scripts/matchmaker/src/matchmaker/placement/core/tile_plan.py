from dataclasses import dataclass
from typing import Literal


Orientation = Literal["R0", "MX", "MY", "R180"]
TileRole = Literal["active", "dummy", "empty"]


@dataclass(frozen=True)
class Tile:
    """
    One physical slot in a placement plan.

    This is generic placement IR. It is not MOS-specific.
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
    Generic placement plan.

    This object describes spatial intent after higher-level compiler has
    resolved the layout into rows, columns, groups, roles, and orientations.
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
                f"{tile.name:8s} "
                f"group={tile.group:4s} "
                f"role={tile.role:6s} "
                f"row={tile.row} "
                f"col={tile.col} "
                f"orientation={tile.orientation}"
            )

        return "\n".join(lines)