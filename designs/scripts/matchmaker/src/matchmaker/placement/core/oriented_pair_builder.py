from dataclasses import dataclass
from typing import Literal

from matchmaker.placement.core.placement_result import (
    PlacedReferenceBinding,
    PlacementResult,
)
from matchmaker.placement.core.reference_orientation import orient_reference
from matchmaker.placement.core.tile_plan import (
    Orientation,
    PlacementPlan,
    Tile,
    TileRole,
)


PairAxis = Literal["horizontal", "vertical"]
PairSide = Literal["low", "high"]


@dataclass(frozen=True)
class OrientedPairMember:
    """One reusable child binding in an oriented two-member assembly."""

    instance_name: str
    cell_name: str
    component: object
    group: str
    orientation: Orientation = "R0"
    role: TileRole = "active"

    def __post_init__(self) -> None:
        if not self.instance_name:
            raise ValueError("pair member instance_name must be non-empty")
        if not self.cell_name:
            raise ValueError("pair member cell_name must be non-empty")
        if not self.group:
            raise ValueError("pair member group must be non-empty")
        if not self.role:
            raise ValueError("pair member role must be non-empty")


@dataclass(frozen=True)
class OrientedPairPlacementPolicy:
    """Geometry policy for any two generated child-cell families.

    ``first_side`` names the first member's side along ``axis``. ``low`` means
    west for a horizontal pair and south for a vertical pair; ``high`` means
    east or north respectively. Orthogonal centers are aligned after applying
    each member's orientation, and all spacing comes from runtime envelopes.
    """

    axis: PairAxis = "horizontal"
    gap: float = 0.0
    first_side: PairSide = "low"

    def __post_init__(self) -> None:
        if self.axis not in {"horizontal", "vertical"}:
            raise ValueError("pair axis must be horizontal or vertical")
        if self.first_side not in {"low", "high"}:
            raise ValueError("pair first_side must be low or high")
        if self.gap < 0:
            raise ValueError("pair gap must be non-negative")


def _bbox_edges(reference) -> tuple[float, float, float, float]:
    (xmin, ymin), (xmax, ymax) = reference.bbox
    return float(xmin), float(ymin), float(xmax), float(ymax)


def _center_on_axis(reference, *, axis: Literal["x", "y"]) -> None:
    xmin, ymin, xmax, ymax = _bbox_edges(reference)
    if axis == "x":
        reference.movex(-((xmin + xmax) / 2.0))
    else:
        reference.movey(-((ymin + ymax) / 2.0))


def _grid_location(
    *,
    axis: PairAxis,
    side: PairSide,
) -> tuple[int, int]:
    if axis == "horizontal":
        return 0, 0 if side == "low" else 1
    return (1 if side == "low" else 0), 0


def build_oriented_pair_placement(
    *,
    cell_name: str,
    first: OrientedPairMember,
    second: OrientedPairMember,
    policy: OrientedPairPlacementPolicy,
) -> PlacementResult:
    """Place any two generated cells from transformed runtime envelopes."""

    from glayout.backend import Component

    if not cell_name:
        raise ValueError("pair placement cell_name must be non-empty")
    if first.instance_name == second.instance_name:
        raise ValueError("pair member instance names must be distinct")

    top = Component(name=cell_name)
    first_reference = top << first.component
    second_reference = top << second.component
    orient_reference(first_reference, first.orientation)
    orient_reference(second_reference, second.orientation)

    half_gap = policy.gap / 2.0
    if policy.axis == "horizontal":
        _center_on_axis(first_reference, axis="y")
        _center_on_axis(second_reference, axis="y")
        first_xmin, _, first_xmax, _ = _bbox_edges(first_reference)
        second_xmin, _, second_xmax, _ = _bbox_edges(second_reference)
        if policy.first_side == "low":
            first_reference.movex(-half_gap - first_xmax)
            second_reference.movex(half_gap - second_xmin)
        else:
            first_reference.movex(half_gap - first_xmin)
            second_reference.movex(-half_gap - second_xmax)
        rows, cols = 1, 2
    else:
        _center_on_axis(first_reference, axis="x")
        _center_on_axis(second_reference, axis="x")
        _, first_ymin, _, first_ymax = _bbox_edges(first_reference)
        _, second_ymin, _, second_ymax = _bbox_edges(second_reference)
        if policy.first_side == "low":
            first_reference.movey(-half_gap - first_ymax)
            second_reference.movey(half_gap - second_ymin)
        else:
            first_reference.movey(half_gap - first_ymin)
            second_reference.movey(-half_gap - second_ymax)
        rows, cols = 2, 1

    first_row, first_col = _grid_location(
        axis=policy.axis,
        side=policy.first_side,
    )
    second_side: PairSide = "high" if policy.first_side == "low" else "low"
    second_row, second_col = _grid_location(
        axis=policy.axis,
        side=second_side,
    )
    plan = PlacementPlan(
        cell_name=cell_name,
        rows=rows,
        cols=cols,
        tiles=(
            Tile(
                name=first.instance_name,
                group=first.group,
                row=first_row,
                col=first_col,
                orientation=first.orientation,
                role=first.role,
            ),
            Tile(
                name=second.instance_name,
                group=second.group,
                row=second_row,
                col=second_col,
                orientation=second.orientation,
                role=second.role,
            ),
        ),
    )
    bindings = {
        first.instance_name: PlacedReferenceBinding(
            instance_name=first.instance_name,
            cell_name=first.cell_name,
            reference=first_reference,
            row=first_row,
            col=first_col,
            orientation=first.orientation,
            role=first.role,
            group=first.group,
        ),
        second.instance_name: PlacedReferenceBinding(
            instance_name=second.instance_name,
            cell_name=second.cell_name,
            reference=second_reference,
            row=second_row,
            col=second_col,
            orientation=second.orientation,
            role=second.role,
            group=second.group,
        ),
    }
    return PlacementResult(component=top, plan=plan, bindings=bindings)
