from matchmaker.design.reference_selector_naming import (
    VREF_SWITCH_INSTANCE_NAME,
    VSS_SWITCH_INSTANCE_NAME,
)
from matchmaker.generators.transmission_gate_generator import GeneratedTransmissionGate
from matchmaker.placement.cdac.reference_selector_intent import (
    ReferenceSelectorLayoutIntent,
)
from matchmaker.placement.core.placement_result import (
    PlacementResult,
)
from matchmaker.placement.core.oriented_pair_builder import (
    OrientedPairMember,
    OrientedPairPlacementPolicy,
    build_oriented_pair_placement,
)


def build_reference_selector_child_placement(
    *,
    intent: ReferenceSelectorLayoutIntent,
    vref_switch: GeneratedTransmissionGate,
    vss_switch: GeneratedTransmissionGate,
) -> PlacementResult:
    """Bind selector roles to the reusable oriented-pair composition."""

    return build_oriented_pair_placement(
        cell_name=intent.resolved_cell_name,
        first=OrientedPairMember(
            instance_name=VREF_SWITCH_INSTANCE_NAME,
            cell_name=str(vref_switch.component.name),
            component=vref_switch.component,
            orientation=intent.policy.vref_child_orientation,
            role="active",
            group="VREF_SWITCH",
        ),
        second=OrientedPairMember(
            instance_name=VSS_SWITCH_INSTANCE_NAME,
            cell_name=str(vss_switch.component.name),
            component=vss_switch.component,
            orientation=intent.policy.vss_child_orientation,
            role="active",
            group="VSS_SWITCH",
        ),
        policy=OrientedPairPlacementPolicy(
            axis=intent.policy.child_axis,
            gap=intent.policy.child_gap,
            first_side=intent.policy.vref_child_side,
        ),
    )
