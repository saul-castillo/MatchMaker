from glayout import rename_ports_by_orientation
from glayout.backend import Component

from .spec import CentroidArraySpec
from .plan import PlacementPlan
from .mos_primitive_factory import create_gf180_mos_primitive
from .mos_dummy_placement_policy import (
    MosDummyPlacementPolicy,
    get_mos_dummy_configuration_for_tile,
)
from .mos_centroid_spacing_policy import (
    MosCentroidSpacingPolicy,
    calculate_mos_centroid_tile_pitch,
)


def get_component_bbox_size(component):
    (xmin, ymin), (xmax, ymax) = component.bbox
    return float(xmax - xmin), float(ymax - ymin)


def assign_component_name(component, name: str):
    """
    Give a generated gLayout/gdsfactory component a stable hierarchy name.

    This avoids unnamed-cell warnings when writing GDS.
    """
    try:
        component.name = name
    except Exception:
        if hasattr(component, "rename"):
            component.rename(name)
        else:
            raise

    return component


def orient_mos_reference_for_centroid_tile(ref, orientation: str):
    if orientation == "R0":
        return ref

    if orientation == "MY":
        return rename_ports_by_orientation(ref.mirror_y())

    if orientation == "MX":
        return rename_ports_by_orientation(ref.mirror_x())

    if orientation == "R180":
        return rename_ports_by_orientation(ref.rotate(180))

    raise NotImplementedError(f"Unsupported orientation: {orientation}")


def get_mos_dummy_configuration_for_placement_tile(
    tile,
    plan: PlacementPlan,
    dummy_policy: MosDummyPlacementPolicy,
) -> tuple[bool, bool]:
    """
    Return the primitive-level dummy configuration for a placement tile.

    Active tiles use the selected dummy policy.
    Dummy tiles are forced to have both primitive dummies enabled.
    Empty tiles should be skipped before this function is called.
    """
    if tile.role == "dummy":
        return (True, True)

    if tile.role == "active":
        return get_mos_dummy_configuration_for_tile(
            tile=tile,
            plan=plan,
            policy=dummy_policy,
        )

    raise ValueError(
        f"Cannot get MOS dummy configuration for tile {tile.name} "
        f"with role={tile.role!r}"
    )


def create_mos_unit_cache_for_placement_plan(
    spec: CentroidArraySpec,
    plan: PlacementPlan,
    dummy_policy: MosDummyPlacementPolicy,
) -> dict[tuple[str, tuple[bool, bool]], Component]:
    """
    Create and cache MOS unit cells needed by the placement plan.

    Cache key:
        (tile_role, (left_dummy, right_dummy))

    This prevents regenerating the same primitive for every tile.
    """
    unit_cache = {}

    for tile in plan.tiles:
        if tile.role == "empty":
            continue

        dummies = get_mos_dummy_configuration_for_placement_tile(
            tile=tile,
            plan=plan,
            dummy_policy=dummy_policy,
        )

        cache_key = (tile.role, dummies)

        if cache_key in unit_cache:
            continue

        unit = create_gf180_mos_primitive(
            device=spec.device_a,
            dummies=dummies,
        )

        unit_name = (
            f"{spec.cell_name}_{spec.device_a.kind}"
            f"_{tile.role}"
            f"_dummy_l{int(dummies[0])}_r{int(dummies[1])}_unit"
        )

        unit_cache[cache_key] = assign_component_name(unit, unit_name)

    if not unit_cache:
        raise ValueError("Placement plan contains no placeable MOS tiles")

    return unit_cache


def calculate_pitch_from_unit_cache(
    unit_cache: dict[tuple[str, tuple[bool, bool]], Component],
    spacing_policy: MosCentroidSpacingPolicy,
) -> tuple[float, float]:
    unit_widths = []
    unit_heights = []

    for unit in unit_cache.values():
        width, height = get_component_bbox_size(unit)
        unit_widths.append(width)
        unit_heights.append(height)

    return calculate_mos_centroid_tile_pitch(
        unit_widths=unit_widths,
        unit_heights=unit_heights,
        spacing_policy=spacing_policy,
    )


def build_mos_centroid_placement(
    spec: CentroidArraySpec,
    plan: PlacementPlan,
    dummy_policy: MosDummyPlacementPolicy | None = None,
    spacing_policy: MosCentroidSpacingPolicy | None = None,
) -> Component:
    """
    Build a placement-only MOS common-centroid array from a PlacementPlan.

    This places MOS primitives according to the plan.
    It does not route, add taps, add labels, or run verification.

    Supported tile roles:
        active -> placed as a normal MOS unit using the dummy policy
        dummy  -> placed as a MOS dummy tile
        empty  -> skipped
    """
    if spec.device_a.kind != spec.device_b.kind:
        raise ValueError("device_a and device_b must have the same MOS kind for now.")

    if spec.rows != plan.rows or spec.cols != plan.cols:
        raise ValueError(
            "spec dimensions do not match placement plan dimensions: "
            f"spec=({spec.rows}, {spec.cols}), "
            f"plan=({plan.rows}, {plan.cols})"
        )

    if dummy_policy is None:
        dummy_policy = MosDummyPlacementPolicy(kind="edge_only")

    if spacing_policy is None:
        spacing_policy = MosCentroidSpacingPolicy(kind="bbox_plus_margin")

    unit_cache = create_mos_unit_cache_for_placement_plan(
        spec=spec,
        plan=plan,
        dummy_policy=dummy_policy,
    )

    x_pitch, y_pitch = calculate_pitch_from_unit_cache(
        unit_cache=unit_cache,
        spacing_policy=spacing_policy,
    )

    print(
        f"MOS centroid pitch: "
        f"x_pitch={x_pitch:.3f}, "
        f"y_pitch={y_pitch:.3f}, "
        f"spacing_policy={spacing_policy.kind}"
    )

    top = Component(name=spec.cell_name)

    for tile in plan.tiles:
        if tile.role == "empty":
            print(
                f"{tile.name} skipped at "
                f"row={tile.row} col={tile.col} role=empty"
            )
            continue

        dummies = get_mos_dummy_configuration_for_placement_tile(
            tile=tile,
            plan=plan,
            dummy_policy=dummy_policy,
        )

        cache_key = (tile.role, dummies)
        unit = unit_cache[cache_key]

        ref = top << unit
        ref = orient_mos_reference_for_centroid_tile(ref, tile.orientation)

        x = (tile.col - (plan.cols - 1) / 2) * x_pitch
        y = ((plan.rows - 1) / 2 - tile.row) * y_pitch

        ref.movex(x)
        ref.movey(y)

        print(
            f"{tile.name} placed at "
            f"({x:.3f}, {y:.3f}) "
            f"role={tile.role} "
            f"orientation={tile.orientation} "
            f"dummies={dummies}"
        )

    return top