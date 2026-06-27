from matchmaker.placement.core.tile_plan import PlacementPlan
from matchmaker.specs.mos_centroid_array_spec import MosCentroidArraySpec
from matchmaker.specs.mos_device_spec import MosDeviceSpec


MosGroupDeviceMap = dict[str, MosDeviceSpec]


def create_mos_group_device_map_from_centroid_spec(
    spec: MosCentroidArraySpec,
) -> MosGroupDeviceMap:
    """
    Build the default active-device binding for a two-group MOS centroid spec.

    Current convention:
        group A -> spec.device_a
        group B -> spec.device_b
    """
    return {
        spec.device_a.name: spec.device_a,
        spec.device_b.name: spec.device_b,
    }


def get_active_device_for_tile_group(
    group: str,
    device_by_group: MosGroupDeviceMap,
) -> MosDeviceSpec:
    if group not in device_by_group:
        known_groups = ", ".join(sorted(device_by_group))
        raise KeyError(
            f"No MOS device binding found for active group {group!r}. "
            f"Known groups: {known_groups}"
        )

    return device_by_group[group]


def validate_active_tile_groups_have_device_bindings(
    plan: PlacementPlan,
    device_by_group: MosGroupDeviceMap,
) -> None:
    active_groups = {
        tile.group
        for tile in plan.tiles
        if tile.role == "active"
    }

    missing_groups = active_groups - set(device_by_group)

    if missing_groups:
        raise KeyError(
            "Missing MOS device bindings for active groups: "
            + ", ".join(sorted(missing_groups))
        )