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


_CARDINAL_DIRECTIONS = frozenset({"N", "S", "E", "W"})
_MOS_TERMINAL_ALIASES = {
    "gate": "gate",
    "source": "source",
    "drain": "drain",
    "bulk": "bulk",
    "body": "bulk",
    "substrate": "bulk",
    "well": "bulk",
}


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


def _routable_mos_terminal_name(port_name: str) -> str | None:
    """Return the canonical terminal for one public cardinal MOS port.

    gLayout MOS primitives may expose thousands of internal hierarchy ports.
    Routing snapshots retain only simple external terminal accesses such as
    ``gate_E``, ``source_N``, ``drain_S``, and ``bulk_W``. Nested names such as
    ``multiplier_0_gate_E`` are internal implementation details and are ignored.
    """
    parts = port_name.split("_")
    if len(parts) != 2:
        return None

    terminal_name, direction = parts
    if direction.upper() not in _CARDINAL_DIRECTIONS:
        return None

    return _MOS_TERMINAL_ALIASES.get(terminal_name.lower())


def create_mos_centroid_physical_design_snapshot(
    component,
    plan: PlacementPlan,
    separator: str = "__",
) -> PhysicalDesignSnapshot:
    """Promote routable tile ports and capture typed physical metadata.

    Reference-order binding is temporary because the existing MOS placement
    builder returns only a component. Future placement builders should return
    stable instance bindings directly.
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
        routable_ports: list[tuple[object, str]] = []
        for primitive_port in reference.get_ports_list():
            canonical_terminal = _routable_mos_terminal_name(str(primitive_port.name))
            if canonical_terminal is not None:
                routable_ports.append((primitive_port, canonical_terminal))

        if not routable_ports:
            raise RuntimeError(
                "Placed MOS reference exposes no supported external terminal ports: "
                f"tile={tile.name!r}, cell={_reference_cell_name(reference)!r}"
            )

        missing_ports = [
            primitive_port
            for primitive_port, _ in routable_ports
            if f"{prefix}{primitive_port.name}" not in component.ports
        ]
        if missing_ports:
            component.add_ports(missing_ports, prefix=prefix)

        instance_access_names: list[str] = []
        for primitive_port, canonical_terminal in routable_ports:
            access_name = f"{prefix}{primitive_port.name}"
            promoted_port = component.ports[access_name]
            terminal = TerminalRef(
                instance_name=tile.name,
                terminal_name=canonical_terminal,
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

    return PhysicalDesignSnapshot(
        component=component,
        instances=placed_instances,
        access_points=access_points,
        terminal_access={
            terminal: tuple(names)
            for terminal, names in terminal_access_names.items()
        },
        obstacles=tuple(obstacles),
    )
