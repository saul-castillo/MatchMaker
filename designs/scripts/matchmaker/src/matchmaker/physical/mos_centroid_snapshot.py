from collections import defaultdict

from matchmaker.physical.models import (
    AccessPoint,
    BoundingBox,
    PhysicalDesignSnapshot,
    PlacedInstance,
    RoutingObstacle,
    TerminalRef,
)
from matchmaker.placement.core.tile_plan import PlacementPlan


def _get_component_references(component) -> list:
    references = getattr(component, "references", None)
    if references is not None:
        return list(references)

    instances = getattr(component, "insts", None)
    if instances is not None:
        if hasattr(instances, "values"):
            return list(instances.values())
        return list(instances)

    raise TypeError("Component does not expose references or instances")


def _reference_cell_name(reference) -> str:
    for attribute in ("cell", "parent", "ref_cell"):
        referenced_cell = getattr(reference, attribute, None)
        name = getattr(referenced_cell, "name", None)
        if name:
            return str(name)

    name = getattr(reference, "name", None)
    if name:
        return str(name)

    raise TypeError("Placed reference does not expose a referenced-cell name")


def _normalize_layer(layer):
    if isinstance(layer, (tuple, list)) and len(layer) == 2:
        return (int(layer[0]), int(layer[1]))
    return str(layer)


def _terminal_name_from_primitive_port(port_name: str) -> str:
    if "_" not in port_name:
        return port_name
    terminal_name, suffix = port_name.rsplit("_", 1)
    if suffix.upper() in {"N", "S", "E", "W"}:
        return terminal_name
    return port_name


def create_mos_centroid_physical_design_snapshot(
    component,
    plan: PlacementPlan,
    separator: str = "__",
) -> PhysicalDesignSnapshot:
    """Promote tile ports and capture stable placed-instance/access metadata.

    The reference-order binding is a transitional adapter for the current MOS
    placement builder. Future builders should return this mapping directly.
    """
    placeable_tiles = [tile for tile in plan.tiles if tile.role != "empty"]
    references = _get_component_references(component)

    if len(references) != len(placeable_tiles):
        raise ValueError(
            "MOS centroid component/reference count does not match the placement plan: "
            f"references={len(references)}, tiles={len(placeable_tiles)}"
        )

    placed_instances: dict[str, PlacedInstance] = {}
    access_points: dict[str, AccessPoint] = {}
    terminal_access_names: dict[TerminalRef, list[str]] = defaultdict(list)
    obstacles: list[RoutingObstacle] = []

    for tile, reference in zip(placeable_tiles, references):
        prefix = f"{tile.name}{separator}"
        reference_ports = list(reference.get_ports_list())
        missing_ports = [
            port
            for port in reference_ports
            if f"{prefix}{port.name}" not in component.ports
        ]
        if missing_ports:
            component.add_ports(missing_ports, prefix=prefix)

        instance_access_names: list[str] = []
        for primitive_port in reference_ports:
            access_name = f"{prefix}{primitive_port.name}"
            promoted_port = component.ports[access_name]
            terminal = TerminalRef(
                instance_name=tile.name,
                terminal_name=_terminal_name_from_primitive_port(
                    str(primitive_port.name)
                ),
            )
            access_point = AccessPoint(
                name=access_name,
                terminal=terminal,
                primitive_port_name=str(primitive_port.name),
                center=(
                    float(promoted_port.center[0]),
                    float(promoted_port.center[1]),
                ),
                orientation=float(promoted_port.orientation),
                width=float(promoted_port.width),
                layer=_normalize_layer(promoted_port.layer),
            )
            access_points[access_name] = access_point
            terminal_access_names[terminal].append(access_name)
            instance_access_names.append(access_name)

        bbox = BoundingBox.from_corners(reference.bbox)
        placed_instances[tile.name] = PlacedInstance(
            instance_name=tile.name,
            cell_name=_reference_cell_name(reference),
            bbox=bbox,
            role=tile.role,
            group=tile.group,
            orientation=tile.orientation,
            row=tile.row,
            col=tile.col,
            access_point_names=tuple(instance_access_names),
        )
        obstacles.append(
            RoutingObstacle(
                obstacle_id=f"instance:{tile.name}",
                owner_instance_name=tile.name,
                bbox=bbox,
            )
        )

    terminal_access = {
        terminal: tuple(names)
        for terminal, names in terminal_access_names.items()
    }
    snapshot = PhysicalDesignSnapshot(
        component=component,
        instances=placed_instances,
        access_points=access_points,
        terminal_access=terminal_access,
        obstacles=tuple(obstacles),
    )

    # Transitional metadata for legacy callers. New routing code should consume
    # the snapshot directly instead of reading Component.info.
    component.info["matchmaker_port_separator"] = separator
    component.info["matchmaker_routing_instances"] = tuple(placed_instances)
    component.info["matchmaker_routing_obstacles"] = snapshot.legacy_obstacles()
    component.info["matchmaker_physical_snapshot_version"] = 1
    return snapshot
