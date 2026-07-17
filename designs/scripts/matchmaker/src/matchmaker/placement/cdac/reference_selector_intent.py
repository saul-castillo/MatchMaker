from dataclasses import dataclass, field

from matchmaker.placement.cdac.transmission_gate_intent import (
    TransmissionGateLayoutPolicy,
)
from matchmaker.specs.transmission_gate_spec import ReferenceSelectorSpec


@dataclass(frozen=True)
class ReferenceSelectorLayoutPolicy:
    """Physical policy for a two-transmission-gate VREF/VSS selector.

    The policy defines spacing and routing-channel clearance only. Child sizes,
    access coordinates, layers, and default route widths are resolved from the
    generated transmission-gate cells at runtime.
    """

    child_gap: float = 4.0
    channel_clearance: float = 2.0
    channel_spacing: float = 1.0
    route_width: float | None = None
    alignment_tolerance: float = 1e-6

    def __post_init__(self) -> None:
        if self.child_gap < 0:
            raise ValueError("reference-selector child_gap must be non-negative")
        if self.channel_clearance < 0:
            raise ValueError(
                "reference-selector channel_clearance must be non-negative"
            )
        if self.channel_spacing <= 0:
            raise ValueError("reference-selector channel_spacing must be positive")
        if self.route_width is not None and self.route_width <= 0:
            raise ValueError("reference-selector route_width must be positive")
        if self.alignment_tolerance < 0:
            raise ValueError("alignment_tolerance must be non-negative")


@dataclass(frozen=True)
class ReferenceSelectorLayoutIntent:
    """Typed request for a generated VREF/VSS reference selector."""

    spec: ReferenceSelectorSpec
    cell_name: str | None = None
    policy: ReferenceSelectorLayoutPolicy = field(
        default_factory=ReferenceSelectorLayoutPolicy
    )
    vref_switch_policy: TransmissionGateLayoutPolicy = field(
        default_factory=lambda: TransmissionGateLayoutPolicy(nmos_side="left")
    )
    vss_switch_policy: TransmissionGateLayoutPolicy = field(
        default_factory=lambda: TransmissionGateLayoutPolicy(nmos_side="left")
    )

    def __post_init__(self) -> None:
        if self.cell_name is not None and not self.cell_name:
            raise ValueError("reference-selector cell_name must be non-empty")

    @property
    def resolved_cell_name(self) -> str:
        return self.cell_name or self.spec.name
