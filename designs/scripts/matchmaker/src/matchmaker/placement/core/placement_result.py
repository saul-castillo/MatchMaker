from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from matchmaker.placement.core.tile_plan import Orientation, PlacementPlan


@dataclass(frozen=True)
class PlacedReferenceBinding:
    """Stable logical identity and physical reference for one placed instance."""

    instance_name: str
    cell_name: str
    reference: object
    row: int
    col: int
    orientation: Orientation
    role: str
    group: str

    def __post_init__(self) -> None:
        if not self.instance_name:
            raise ValueError("placed binding instance_name must be non-empty")
        if not self.cell_name:
            raise ValueError("placed binding cell_name must be non-empty")
        if self.reference is None:
            raise ValueError("placed binding reference must not be None")
        if self.row < 0 or self.col < 0:
            raise ValueError("placed binding row and col must be non-negative")
        if not self.role:
            raise ValueError("placed binding role must be non-empty")
        if not self.group:
            raise ValueError("placed binding group must be non-empty")


@dataclass(frozen=True)
class PlacementResult:
    """Component plus deterministic placement plan and logical reference bindings."""

    component: object
    plan: PlacementPlan
    bindings: Mapping[str, PlacedReferenceBinding]

    def __post_init__(self) -> None:
        if self.component is None:
            raise ValueError("placement result component must not be None")
        bindings = dict(self.bindings)
        for key, binding in bindings.items():
            if key != binding.instance_name:
                raise ValueError(
                    "placement binding key does not match instance_name: "
                    f"{key!r} != {binding.instance_name!r}"
                )
        object.__setattr__(self, "bindings", MappingProxyType(bindings))

    def binding(self, instance_name: str) -> PlacedReferenceBinding:
        try:
            return self.bindings[instance_name]
        except KeyError as error:
            raise KeyError(f"Unknown placed reference binding: {instance_name}") from error
