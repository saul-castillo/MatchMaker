from glayout.backend import Component

from matchmaker.design.reference_selector_naming import (
    VREF_SWITCH_INSTANCE_NAME,
    VSS_SWITCH_INSTANCE_NAME,
)
from matchmaker.generators.transmission_gate_generator import GeneratedTransmissionGate
from matchmaker.placement.cdac.reference_selector_intent import (
    ReferenceSelectorLayoutIntent,
)
from matchmaker.placement.core.placement_result import (
    PlacedReferenceBinding,
    PlacementResult,
)
from matchmaker.placement.core.reference_orientation import orient_reference
from matchmaker.placement.core.tile_plan import PlacementPlan, Tile


def _bbox_edges(component) -> tuple[float, float, float, float]:
    (xmin, ymin), (xmax, ymax) = component.bbox
    return float(xmin), float(ymin), float(xmax), float(ymax)


def _center_y(reference) -> None:
    _, ymin, _, ymax = _bbox_edges(reference)
    reference.movey(-((ymin + ymax) / 2.0))


def build_reference_selector_child_placement(
    *,
    intent: ReferenceSelectorLayoutIntent,
    vref_switch: GeneratedTransmissionGate,
    vss_switch: GeneratedTransmissionGate,
) -> PlacementResult:
    """Place two generated transmission gates from runtime envelopes.

    The VREF switch is left of the VSS switch. Child orientations come from the
    typed selector policy, and transformed runtime envelopes drive centering and
    horizontal spacing.
    """

    top = Component(name=intent.resolved_cell_name)
    vref_reference = top << vref_switch.component
    vss_reference = top << vss_switch.component

    orient_reference(vref_reference, intent.policy.vref_child_orientation)
    orient_reference(vss_reference, intent.policy.vss_child_orientation)
    _center_y(vref_reference)
    _center_y(vss_reference)

    _, _, vref_xmax, _ = _bbox_edges(vref_reference)
    vss_xmin, _, _, _ = _bbox_edges(vss_reference)
    half_gap = intent.policy.child_gap / 2.0
    vref_reference.movex(-half_gap - vref_xmax)
    vss_reference.movex(half_gap - vss_xmin)

    plan = PlacementPlan(
        cell_name=intent.resolved_cell_name,
        rows=1,
        cols=2,
        tiles=(
            Tile(
                name=VREF_SWITCH_INSTANCE_NAME,
                group="VREF_SWITCH",
                row=0,
                col=0,
                orientation=intent.policy.vref_child_orientation,
                role="active",
            ),
            Tile(
                name=VSS_SWITCH_INSTANCE_NAME,
                group="VSS_SWITCH",
                row=0,
                col=1,
                orientation=intent.policy.vss_child_orientation,
                role="active",
            ),
        ),
    )
    bindings = {
        VREF_SWITCH_INSTANCE_NAME: PlacedReferenceBinding(
            instance_name=VREF_SWITCH_INSTANCE_NAME,
            cell_name=str(vref_switch.component.name),
            reference=vref_reference,
            row=0,
            col=0,
            orientation=intent.policy.vref_child_orientation,
            role="active",
            group="VREF_SWITCH",
        ),
        VSS_SWITCH_INSTANCE_NAME: PlacedReferenceBinding(
            instance_name=VSS_SWITCH_INSTANCE_NAME,
            cell_name=str(vss_switch.component.name),
            reference=vss_reference,
            row=0,
            col=1,
            orientation=intent.policy.vss_child_orientation,
            role="active",
            group="VSS_SWITCH",
        ),
    }
    return PlacementResult(component=top, plan=plan, bindings=bindings)
