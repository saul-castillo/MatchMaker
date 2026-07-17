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
from matchmaker.placement.core.tile_plan import PlacementPlan, Tile


def _bbox_edges(component) -> tuple[float, float, float, float]:
    (xmin, ymin), (xmax, ymax) = component.bbox
    return float(xmin), float(ymin), float(xmax), float(ymax)


def _center_y(reference, component) -> None:
    _, ymin, _, ymax = _bbox_edges(component)
    reference.movey(-((ymin + ymax) / 2.0))


def build_reference_selector_child_placement(
    *,
    intent: ReferenceSelectorLayoutIntent,
    vref_switch: GeneratedTransmissionGate,
    vss_switch: GeneratedTransmissionGate,
) -> PlacementResult:
    """Place two generated transmission gates from runtime envelopes.

    The VREF switch is left of the VSS switch. Their y centers are aligned so
    the inner output accesses can form a direct common node. Horizontal spacing
    comes only from child bboxes and the typed selector policy.
    """

    top = Component(name=intent.resolved_cell_name)
    vref_reference = top << vref_switch.component
    vss_reference = top << vss_switch.component

    _center_y(vref_reference, vref_switch.component)
    _center_y(vss_reference, vss_switch.component)

    _, _, vref_xmax, _ = _bbox_edges(vref_switch.component)
    vss_xmin, _, _, _ = _bbox_edges(vss_switch.component)
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
                orientation="R0",
                role="active",
            ),
            Tile(
                name=VSS_SWITCH_INSTANCE_NAME,
                group="VSS_SWITCH",
                row=0,
                col=1,
                orientation="R0",
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
            orientation="R0",
            role="active",
            group="VREF_SWITCH",
        ),
        VSS_SWITCH_INSTANCE_NAME: PlacedReferenceBinding(
            instance_name=VSS_SWITCH_INSTANCE_NAME,
            cell_name=str(vss_switch.component.name),
            reference=vss_reference,
            row=0,
            col=1,
            orientation="R0",
            role="active",
            group="VSS_SWITCH",
        ),
    }
    return PlacementResult(component=top, plan=plan, bindings=bindings)
