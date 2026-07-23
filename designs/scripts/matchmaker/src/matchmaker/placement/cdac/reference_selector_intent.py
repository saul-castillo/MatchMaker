from dataclasses import dataclass, field

from matchmaker.placement.cdac.transmission_gate_intent import (
    TransmissionGateLayoutPolicy,
)
from matchmaker.placement.core.oriented_pair_builder import PairAxis, PairSide
from matchmaker.placement.core.tile_plan import Orientation
from matchmaker.specs.transmission_gate_spec import ReferenceSelectorSpec


@dataclass(frozen=True)
class ReferenceSelectorLayoutPolicy:
    """Physical policy for a two-transmission-gate VREF/VSS selector.

    Child sizes, access coordinates, layers, and default route widths are
    resolved from generated transmission-gate cells at runtime. The policy
    supplies an oriented-pair composition policy, corridor clearance, optional
    widths, and semantic upper routing-layer names. The generic pair builder and
    corridor planners own geometry construction.
    """

    child_gap: float = 4.0
    channel_clearance: float = 2.0
    route_width: float | None = None
    supply_route_width: float | None = None
    child_axis: PairAxis = "vertical"
    vref_child_side: PairSide = "high"
    vref_child_orientation: Orientation = "R0"
    vss_child_orientation: Orientation = "R180"
    upper_route_glayer: str = "met3"
    alignment_tolerance: float = 1e-6

    def __post_init__(self) -> None:
        if self.child_gap < 0:
            raise ValueError("reference-selector child_gap must be non-negative")
        if self.channel_clearance < 0:
            raise ValueError(
                "reference-selector channel_clearance must be non-negative"
            )
        if self.route_width is not None and self.route_width <= 0:
            raise ValueError("reference-selector route_width must be positive")
        if self.supply_route_width is not None and self.supply_route_width <= 0:
            raise ValueError(
                "reference-selector supply_route_width must be positive"
            )
        if self.child_axis not in {"horizontal", "vertical"}:
            raise ValueError("unsupported selector child axis")
        if self.vref_child_side not in {"low", "high"}:
            raise ValueError("unsupported VREF child side")
        supported_orientations = {"R0", "MX", "MY", "R180"}
        if self.vref_child_orientation not in supported_orientations:
            raise ValueError("unsupported VREF child orientation")
        if self.vss_child_orientation not in supported_orientations:
            raise ValueError("unsupported VSS child orientation")
        if not self.upper_route_glayer:
            raise ValueError("upper_route_glayer must be non-empty")
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
        default_factory=lambda: TransmissionGateLayoutPolicy(
            nmos_side="left",
            input_device_terminal="drain",
            output_device_terminal="source",
        )
    )
    vss_switch_policy: TransmissionGateLayoutPolicy = field(
        default_factory=lambda: TransmissionGateLayoutPolicy(
            nmos_side="left",
            input_device_terminal="drain",
            output_device_terminal="source",
        )
    )

    def __post_init__(self) -> None:
        if self.cell_name is not None and not self.cell_name:
            raise ValueError("reference-selector cell_name must be non-empty")

    @property
    def resolved_cell_name(self) -> str:
        return self.cell_name or self.spec.name
