from glayout import rename_ports_by_orientation
from glayout.backend import Component

from .spec import CentroidArraySpec
from .plan import PlacementPlan
from .mos_primitive_factory import create_gf180_mos_primitive


def get_component_bbox_size(component):
    (xmin, ymin), (xmax, ymax) = component.bbox
    return float(xmax - xmin), float(ymax - ymin)


def orient_mos_reference_for_centroid_tile(ref, orientation: str):
    if orientation == "R0":
        return ref

    if orientation == "MY":
        return rename_ports_by_orientation(ref.mirror_y())

    raise NotImplementedError(f"Unsupported orientation: {orientation}")


def build_mos_centroid_placement(
    spec: CentroidArraySpec,
    plan: PlacementPlan,
) -> Component:
    """
    Build a placement-only MOS common-centroid array from a PlacementPlan.

    This places MOS primitives according to the plan.
    It does not route, add taps, add labels, or run verification.
    """
    if spec.device_a.kind != spec.device_b.kind:
        raise ValueError("device_a and device_b must have the same MOS kind for now.")

    left_edge_unit = create_gf180_mos_primitive(
        device=spec.device_a,
        dummies=(True, False),
    )

    right_edge_unit = create_gf180_mos_primitive(
        device=spec.device_a,
        dummies=(False, True),
    )

    w_left, h_left = get_component_bbox_size(left_edge_unit)
    w_right, h_right = get_component_bbox_size(right_edge_unit)

    x_pitch = max(w_left, w_right) + 2.0
    y_pitch = max(h_left, h_right) + 2.0

    top = Component(name=spec.cell_name)

    for tile in plan.tiles:
        unit = left_edge_unit if tile.col == 0 else right_edge_unit

        ref = top << unit
        ref = orient_mos_reference_for_centroid_tile(ref, tile.orientation)

        x = (tile.col - (plan.cols - 1) / 2) * x_pitch
        y = ((plan.rows - 1) / 2 - tile.row) * y_pitch

        ref.movex(x)
        ref.movey(y)

        print(
            f"{tile.name} placed at "
            f"({x:.3f}, {y:.3f}) "
            f"orientation={tile.orientation}"
        )

    return top