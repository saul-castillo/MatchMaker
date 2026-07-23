from matchmaker.physical.hierarchical_cell_snapshot import (
    CellFamilyAccessContract,
    create_hierarchical_cell_snapshot,
)
from matchmaker.physical.models import PhysicalDesignSnapshot
from matchmaker.physical.transmission_gate_cell_access import (
    TransmissionGateCellAccessPolicy,
    classify_transmission_gate_cell_port_name,
)
from matchmaker.placement.core.placement_result import PlacementResult


_REQUIRED_TERMINALS = frozenset(
    {"input", "output", "control", "control_bar", "vss", "vdd"}
)
_SELECTOR_CHILD_ACCESS_POLICY = TransmissionGateCellAccessPolicy(
    terminals=("input", "output", "control", "control_bar", "vss", "vdd"),
    directions=("W", "E", "N", "S"),
    terminal_directions=(
        ("input", ("W", "E")),
        ("output", ("W", "E")),
        ("control", ("W",)),
        ("control_bar", ("E",)),
        ("vss", ("N", "S")),
        ("vdd", ("N", "S")),
    ),
)


def create_reference_selector_child_snapshot(
    placement: PlacementResult,
    *,
    access_policy: TransmissionGateCellAccessPolicy | None = None,
    separator: str = "__",
) -> PhysicalDesignSnapshot:
    """Adapt selector children through the reusable generated-cell boundary."""

    access_policy = access_policy or _SELECTOR_CHILD_ACCESS_POLICY
    return create_hierarchical_cell_snapshot(
        placement,
        contract=CellFamilyAccessContract(
            family_name="transmission-gate",
            required_terminals=_REQUIRED_TERMINALS,
            classify_port_name=lambda name: (
                classify_transmission_gate_cell_port_name(
                    name,
                    policy=access_policy,
                )
            ),
        ),
        separator=separator,
    )
