from dataclasses import dataclass, field
from typing import Literal

from matchmaker.primitives.gf180_mos_primitive_options import (
    Gf180MosPrimitiveOptions,
)
from matchmaker.specs.transmission_gate_spec import TransmissionGateSpec


HorizontalSide = Literal["W", "E"]
CardinalDirection = Literal["N", "S", "E", "W"]


@dataclass(frozen=True)
class TransmissionGateLayoutPolicy:
    """Physical policy for a complementary transmission-gate cell.

    The policy contains no layer numbers or primitive dimensions. Device
    separation and route width are resolved from the generated geometry and
    selected ports unless explicitly overridden here.
    """

    device_gap: float = 2.0
    nmos_side: Literal["left", "right"] = "left"
    input_device_terminal: Literal["source", "drain"] = "source"
    output_device_terminal: Literal["source", "drain"] = "drain"
    inner_nmos_direction: HorizontalSide = "E"
    inner_pmos_direction: HorizontalSide = "W"
    external_directions: tuple[HorizontalSide, ...] = ("W", "E")
    control_directions: tuple[CardinalDirection, ...] = ("W", "E")
    route_width: float | None = None
    alignment_tolerance: float = 1e-6

    def __post_init__(self) -> None:
        if self.device_gap < 0:
            raise ValueError("transmission-gate device_gap must be non-negative")
        if self.input_device_terminal == self.output_device_terminal:
            raise ValueError("input and output device terminals must be distinct")
        if self.inner_nmos_direction == self.inner_pmos_direction:
            raise ValueError("inner NMOS and PMOS directions must face each other")
        if not self.external_directions:
            raise ValueError("at least one external signal access direction is required")
        if not self.control_directions:
            raise ValueError("at least one control access direction is required")
        if len(set(self.external_directions)) != len(self.external_directions):
            raise ValueError("external signal access directions must be unique")
        if len(set(self.control_directions)) != len(self.control_directions):
            raise ValueError("control access directions must be unique")
        if self.route_width is not None and self.route_width <= 0:
            raise ValueError("explicit transmission-gate route width must be positive")
        if self.alignment_tolerance < 0:
            raise ValueError("alignment_tolerance must be non-negative")


@dataclass(frozen=True)
class TransmissionGateLayoutIntent:
    """Typed request for one generated transmission-gate layout cell."""

    spec: TransmissionGateSpec
    cell_name: str | None = None
    policy: TransmissionGateLayoutPolicy = field(
        default_factory=TransmissionGateLayoutPolicy
    )
    nmos_primitive_options: Gf180MosPrimitiveOptions = field(
        default_factory=Gf180MosPrimitiveOptions
    )
    pmos_primitive_options: Gf180MosPrimitiveOptions = field(
        default_factory=Gf180MosPrimitiveOptions
    )

    def __post_init__(self) -> None:
        if self.cell_name is not None and not self.cell_name:
            raise ValueError("transmission-gate cell_name must be non-empty")

    @property
    def resolved_cell_name(self) -> str:
        return self.cell_name or self.spec.name
