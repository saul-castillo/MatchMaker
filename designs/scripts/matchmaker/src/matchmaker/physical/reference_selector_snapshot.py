from collections import defaultdict

from matchmaker.physical.models import (
    AccessPoint,
    BoundingBox,
    PhysicalDesignSnapshot,
    PlacedInstance,
    RoutingObstacle,
    TerminalRef,
)
from matchmaker.physical.transmission_gate_cell_access import (
    TransmissionGateCellAccessPolicy,
    classify_transmission_gate_cell_port_name,
)
from matchmaker.placement.core.placement_result import PlacementResult


_REQUIRED_TERMINALS = frozenset(
    {"input", "output", "control", "control_bar", "vss", "vdd"}
)
_SELECTOR_CHILD_ACCESS_POLICY = TransmissionGateCellAccessPolicy(
    terminals=("input", "output", "control", "control_bar", "vss", "vdd"),
    directions=("W", "E", "N", "S"),
)


def _normalize_layer(layer):
    if isinstance(layer, (tuple, list)) and len(layer) == 2:
        return int(layer[0]), int(layer[1])
    return str(layer)


def _reference_ports(reference) -> tuple:
    if hasattr(reference, "get_ports_list"):
        return tuple(reference.get_ports_list())
    ports = reference.ports
    if hasattr(ports, "values"):
        return tuple(ports.values())
    return tuple(ports)


def create_reference_selector_child_snapshot(
    placement: PlacementResult,
    *,
    access_policy: TransmissionGateCellAccessPolicy | None = None,
    separator: str = "__",
) -> PhysicalDesignSnapshot:
    """Adapt two placed generated transmission-gate cells into routing state."""

    access_policy = access_policy or _SELECTOR_CHILD_ACCESS_POLICY
    component = placement.component
    instances: dict[str, PlacedInstance] = {}
    access_points: dict[str, AccessPoint] = {}
    terminal_access: dict[TerminalRef, list[str]] = defaultdict(list)
    obstacles: list[RoutingObstacle] = []

    for instance_name, binding in placement.bindings.items():
        prefix = f"{instance_name}{separator}"
        classified_ports: list[tuple[object, str, str]] = []
        observed: set[str] = set()

        for child_port in _reference_ports(binding.reference):
            classification = classify_transmission_gate_cell_port_name(
                str(child_port.name),
                policy=access_policy,
            )
            if classification is None:
                continue
            terminal_name, direction = classification
            classified_ports.append((child_port, terminal_name, direction))
            observed.add(terminal_name)

        missing = sorted(_REQUIRED_TERMINALS - observed)
        if missing:
            raise RuntimeError(
                f"placed transmission gate {instance_name!r} lacks required "
                f"terminals: {', '.join(missing)}"
            )

        missing_promoted = [
            child_port
            for child_port, _, _ in classified_ports
            if f"{prefix}{child_port.name}" not in component.ports
        ]
        if missing_promoted:
            component.add_ports(missing_promoted, prefix=prefix)

        instance_access_names: list[str] = []
        for child_port, terminal_name, _ in classified_ports:
            access_name = f"{prefix}{child_port.name}"
            promoted = component.ports[access_name]
            terminal = TerminalRef(instance_name, terminal_name)
            access = AccessPoint(
                name=access_name,
                terminal=terminal,
                primitive_port_name=str(child_port.name),
                center=(float(promoted.center[0]), float(promoted.center[1])),
                orientation=float(promoted.orientation),
                width=float(promoted.width),
                layer=_normalize_layer(promoted.layer),
            )
            access_points[access_name] = access
            terminal_access[terminal].append(access_name)
            instance_access_names.append(access_name)

        bbox = BoundingBox.from_corners(binding.reference.bbox)
        instances[instance_name] = PlacedInstance(
            instance_name=instance_name,
            cell_name=binding.cell_name,
            bbox=bbox,
            role=binding.role,
            group=binding.group,
            orientation=binding.orientation,
            row=binding.row,
            col=binding.col,
            access_point_names=tuple(instance_access_names),
        )
        obstacles.append(
            RoutingObstacle(
                obstacle_id=f"instance:{instance_name}",
                owner_instance_name=instance_name,
                bbox=bbox,
            )
        )

    return PhysicalDesignSnapshot(
        component=component,
        instances=instances,
        access_points=access_points,
        terminal_access={
            terminal: tuple(names) for terminal, names in terminal_access.items()
        },
        obstacles=tuple(obstacles),
    )
