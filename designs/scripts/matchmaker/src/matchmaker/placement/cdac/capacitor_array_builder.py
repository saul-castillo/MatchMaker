from collections.abc import Callable

from glayout.backend import Component

from matchmaker.placement.cdac.capacitor_array_intent import (
    CdacCapacitorArrayIntent,
)
from matchmaker.placement.cdac.capacitor_array_plan_compiler import (
    compile_cdac_capacitor_array_plan,
)
from matchmaker.placement.core.placement_result import (
    PlacedReferenceBinding,
    PlacementResult,
)
from matchmaker.placement.core.spacing_policy import (
    calculate_tile_pitch_from_unit_sizes,
)
from matchmaker.primitives.gf180_mim_capacitor_factory import (
    create_gf180_mim_capacitor,
)


def _component_bbox_size(component) -> tuple[float, float]:
    (xmin, ymin), (xmax, ymax) = component.bbox
    return float(xmax - xmin), float(ymax - ymin)


def _orient_reference(reference, orientation: str):
    if orientation == "R0":
        return reference
    if orientation == "MY":
        reference.mirror_y()
        return reference
    if orientation == "MX":
        reference.mirror_x()
        return reference
    if orientation == "R180":
        reference.rotate(180)
        return reference
    raise NotImplementedError(f"Unsupported reference orientation: {orientation!r}")


def build_cdac_capacitor_array(
    intent: CdacCapacitorArrayIntent,
    primitive_factory: Callable = create_gf180_mim_capacitor,
) -> PlacementResult:
    """Build the capacitor-array placement without routing or port adaptation."""

    plan = compile_cdac_capacitor_array_plan(intent)
    unit = primitive_factory(intent.spec.unit_capacitor)
    unit_width, unit_height = _component_bbox_size(unit)
    x_pitch, y_pitch = calculate_tile_pitch_from_unit_sizes(
        unit_widths=[unit_width],
        unit_heights=[unit_height],
        spacing_policy=intent.spacing_policy,
    )

    top = Component(name=plan.cell_name)
    bindings: dict[str, PlacedReferenceBinding] = {}

    for tile in plan.tiles:
        reference = top << unit
        _orient_reference(reference, tile.orientation)
        x = (tile.col - (plan.cols - 1) / 2.0) * x_pitch
        y = ((plan.rows - 1) / 2.0 - tile.row) * y_pitch
        reference.movex(x)
        reference.movey(y)

        bindings[tile.name] = PlacedReferenceBinding(
            instance_name=tile.name,
            cell_name=getattr(unit, "name", intent.spec.unit_capacitor.name),
            reference=reference,
            row=tile.row,
            col=tile.col,
            orientation=tile.orientation,
            role=tile.role,
            group=tile.group,
        )

    return PlacementResult(
        component=top,
        plan=plan,
        bindings=bindings,
    )
