from glayout.backend import Component

from matchmaker.placement.core.spacing_policy import (
    TileSpacingPolicy,
    calculate_tile_pitch_from_unit_sizes,
)
from matchmaker.placement.core.tile_plan import PlacementPlan, Tile
from matchmaker.placement.mos.mos_centroid_placement_request import (
    MosCentroidPlacementRequest,
    validate_mos_centroid_placement_request,
)
from matchmaker.placement.mos.mos_dummy_policy import (
    MosDummyPolicy,
    get_mos_primitive_dummy_configuration_for_tile,
)
from matchmaker.placement.mos.mos_group_device_binding import (
    MosGroupDeviceMap,
    create_mos_group_device_map_from_centroid_spec,
    get_active_device_for_tile_group,
    validate_active_tile_groups_have_device_bindings,
)
from matchmaker.primitives.gf180_mos_primitive_factory import (
    create_gf180_mos_primitive,
)
from matchmaker.primitives.gf180_mos_primitive_options import (
    Gf180MosPrimitiveOptions,
)
from matchmaker.specs.mos_centroid_array_spec import MosCentroidArraySpec
from matchmaker.specs.mos_device_spec import MosDeviceSpec


def get_component_bbox_size(component) -> tuple[float, float]:
    """
    Return component bounding-box width and height.
    """
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
    """
    Apply geometric orientation to a MOS reference.

    This is intentionally geometry-only. Port-name normalization belongs in
    the future routing layer, not in the placement-only builder.
    """
    if orientation == "R0":
        return ref

    if orientation == "MY":
        ref.mirror_y()
        return ref

    if orientation == "MX":
        ref.mirror_x()
        return ref

    if orientation == "R180":
        ref.rotate(180)
        return ref

    raise NotImplementedError(f"Unsupported orientation: {orientation}")


def get_mos_device_for_placement_tile(
    tile: Tile,
    device_by_group: MosGroupDeviceMap,
    dummy_reference_device: MosDeviceSpec,
) -> MosDeviceSpec:
    """
    Resolve which MOS device spec should be used for one placement tile.

    Active tiles use the group/device binding.
    Dummy tiles use a reference device so their size matches the array family.
    Empty tiles should be skipped before this function is called.
    """
    if tile.role == "active":
        return get_active_device_for_tile_group(
            group=tile.group,
            device_by_group=device_by_group,
        )

    if tile.role == "dummy":
        return dummy_reference_device

    raise ValueError(
        f"Cannot resolve MOS device for tile {tile.name} "
        f"with role={tile.role!r}"
    )


def get_mos_dummy_configuration_for_placement_tile(
    tile: Tile,
    plan: PlacementPlan,
    dummy_policy: MosDummyPolicy,
) -> tuple[bool, bool]:
    """
    Return the primitive-level dummy configuration for a placement tile.

    Active tiles use the selected MOS dummy policy.
    Dummy tiles are forced to have both primitive dummies enabled.
    Empty tiles should be skipped before this function is called.
    """
    if tile.role == "dummy":
        return (True, True)

    if tile.role == "active":
        return get_mos_primitive_dummy_configuration_for_tile(
            tile=tile,
            plan=plan,
            policy=dummy_policy,
        )

    raise ValueError(
        f"Cannot get MOS dummy configuration for tile {tile.name} "
        f"with role={tile.role!r}"
    )


def create_mos_unit_cache_for_placement_plan(
    spec: MosCentroidArraySpec,
    plan: PlacementPlan,
    dummy_policy: MosDummyPolicy,
    device_by_group: MosGroupDeviceMap,
    primitive_options: Gf180MosPrimitiveOptions,
) -> dict[tuple[str, str, tuple[bool, bool]], Component]:
    """
    Create and cache MOS unit cells needed by the placement plan.

    Cache key:
        (tile_role, cache_group, (left_dummy, right_dummy))

    This prevents regenerating the same MOS primitive for every tile.
    """
    unit_cache: dict[tuple[str, str, tuple[bool, bool]], Component] = {}
    dummy_reference_device = spec.device_a

    for tile in plan.tiles:
        if tile.role == "empty":
            continue

        device = get_mos_device_for_placement_tile(
            tile=tile,
            device_by_group=device_by_group,
            dummy_reference_device=dummy_reference_device,
        )

        dummies = get_mos_dummy_configuration_for_placement_tile(
            tile=tile,
            plan=plan,
            dummy_policy=dummy_policy,
        )

        cache_group = tile.group if tile.role == "active" else "DUMMY"
        cache_key = (tile.role, cache_group, dummies)

        if cache_key in unit_cache:
            continue

        unit = create_gf180_mos_primitive(
            device=device,
            dummies=dummies,
            primitive_options=primitive_options,
        )

        unit_name = (
            f"{spec.cell_name}_{device.kind}"
            f"_{tile.role}"
            f"_group_{cache_group}"
            f"_dummy_l{int(dummies[0])}_r{int(dummies[1])}_unit"
        )

        unit_cache[cache_key] = assign_component_name(unit, unit_name)

    if not unit_cache:
        raise ValueError("Placement plan contains no placeable MOS tiles")

    return unit_cache


def calculate_pitch_from_unit_cache(
    unit_cache: dict[tuple[str, str, tuple[bool, bool]], Component],
    spacing_policy: TileSpacingPolicy,
) -> tuple[float, float]:
    """
    Calculate placement pitch from cached MOS unit sizes.
    """
    unit_widths = []
    unit_heights = []

    for unit in unit_cache.values():
        width, height = get_component_bbox_size(unit)
        unit_widths.append(width)
        unit_heights.append(height)

    return calculate_tile_pitch_from_unit_sizes(
        unit_widths=unit_widths,
        unit_heights=unit_heights,
        spacing_policy=spacing_policy,
    )


def build_mos_centroid_placement(
    spec: MosCentroidArraySpec,
    plan: PlacementPlan,
    dummy_policy: MosDummyPolicy | None = None,
    spacing_policy: TileSpacingPolicy | None = None,
    device_by_group: MosGroupDeviceMap | None = None,
    primitive_options: Gf180MosPrimitiveOptions | None = None,
) -> Component:
    """
    Build a placement-only MOS common-centroid array from a PlacementPlan.

    Supported tile roles:
        active -> placed using the tile group/device binding
        dummy  -> placed as a MOS dummy tile
        empty  -> skipped

    This builder does not route, label, run DRC/LVS, or normalize ports.
    """
    if spec.device_a.kind != spec.device_b.kind:
        raise ValueError("device_a and device_b must have the same MOS kind for now")

    if spec.rows != plan.rows or spec.cols != plan.cols:
        raise ValueError(
            "spec dimensions do not match placement plan dimensions: "
            f"spec=({spec.rows}, {spec.cols}), "
            f"plan=({plan.rows}, {plan.cols})"
        )

    if dummy_policy is None:
        dummy_policy = MosDummyPolicy(kind="edge_only")

    if spacing_policy is None:
        spacing_policy = TileSpacingPolicy(kind="bbox_plus_margin")

    if primitive_options is None:
        primitive_options = Gf180MosPrimitiveOptions()

    if device_by_group is None:
        device_by_group = create_mos_group_device_map_from_centroid_spec(spec)

    validate_active_tile_groups_have_device_bindings(
        plan=plan,
        device_by_group=device_by_group,
    )

    unit_cache = create_mos_unit_cache_for_placement_plan(
        spec=spec,
        plan=plan,
        dummy_policy=dummy_policy,
        device_by_group=device_by_group,
        primitive_options=primitive_options,
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
    dummy_reference_device = spec.device_a

    for tile in plan.tiles:
        if tile.role == "empty":
            print(
                f"{tile.name} skipped at "
                f"row={tile.row} col={tile.col} role=empty"
            )
            continue

        device = get_mos_device_for_placement_tile(
            tile=tile,
            device_by_group=device_by_group,
            dummy_reference_device=dummy_reference_device,
        )

        dummies = get_mos_dummy_configuration_for_placement_tile(
            tile=tile,
            plan=plan,
            dummy_policy=dummy_policy,
        )

        cache_group = tile.group if tile.role == "active" else "DUMMY"
        cache_key = (tile.role, cache_group, dummies)
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
            f"group={tile.group} "
            f"role={tile.role} "
            f"device={device.name} "
            f"orientation={tile.orientation} "
            f"dummies={dummies}"
        )

    return top


def build_mos_centroid_placement_from_request(
    request: MosCentroidPlacementRequest,
) -> Component:
    """
    Build MOS centroid placement from a complete placement request.
    """
    validate_mos_centroid_placement_request(request)

    return build_mos_centroid_placement(
        spec=request.spec,
        plan=request.plan,
        dummy_policy=request.dummy_policy,
        spacing_policy=request.spacing_policy,
        device_by_group=request.device_by_group,
        primitive_options=request.primitive_options,
    )