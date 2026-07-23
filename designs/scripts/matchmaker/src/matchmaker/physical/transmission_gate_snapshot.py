from collections import defaultdict

from matchmaker.physical.gf180_mos_access import (
    Gf180MosExternalAccessPolicy,
    classify_gf180_mos_external_port_name,
)
from matchmaker.physical.models import (
    AccessPoint,
    BoundingBox,
    PhysicalDesignSnapshot,
    PlacedInstance,
    RoutingObstacle,
    TerminalRef,
)
from matchmaker.placement.core.placement_result import PlacementResult


_REQUIRED_ROUTABLE_TERMINALS = frozenset({"gate", "source", "drain", "bulk"})


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


def create_transmission_gate_device_snapshot(
    placement: PlacementResult,
    *,
    access_policy: Gf180MosExternalAccessPolicy | None = None,
    separator: str = "__",
) -> PhysicalDesignSnapshot:
    """Adapt a placed NMOS/PMOS pair into typed physical routing state."""

    access_policy = access_policy or Gf180MosExternalAccessPolicy()
    component = placement.component
    placed_instances: dict[str, PlacedInstance] = {}
    access_points: dict[str, AccessPoint] = {}
    terminal_access: dict[TerminalRef, list[str]] = defaultdict(list)
    obstacles: list[RoutingObstacle] = []

    for instance_name, binding in placement.bindings.items():
        prefix = f"{instance_name}{separator}"
        classified_ports: list[tuple[object, str, str]] = []
        observed_terminals: set[str] = set()

        for primitive_port in _reference_ports(binding.reference):
            classification = classify_gf180_mos_external_port_name(
                str(primitive_port.name),
                policy=access_policy,
            )
            if classification is None:
                continue
            terminal_name, direction = classification
            classified_ports.append((primitive_port, terminal_name, direction))
            observed_terminals.add(terminal_name)

        missing = sorted(_REQUIRED_ROUTABLE_TERMINALS - observed_terminals)
        if missing:
            raise RuntimeError(
                f"placed MOS instance {instance_name!r} lacks required external "
                f"terminals: {', '.join(missing)}"
            )

        missing_promoted = [
            primitive_port
            for primitive_port, _, _ in classified_ports
            if f"{prefix}{primitive_port.name}" not in component.ports
        ]
        if missing_promoted:
            component.add_ports(missing_promoted, prefix=prefix)

        instance_access_names: list[str] = []
        for primitive_port, terminal_name, _ in classified_ports:
            access_name = f"{prefix}{primitive_port.name}"
            promoted_port = component.ports[access_name]
            terminal = TerminalRef(instance_name, terminal_name)
            access = AccessPoint(
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
            access_points[access_name] = access
            terminal_access[terminal].append(access_name)
            instance_access_names.append(access_name)

        bbox = BoundingBox.from_corners(binding.reference.bbox)
        placed_instances[instance_name] = PlacedInstance(
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
        instances=placed_instances,
        access_points=access_points,
        terminal_access={
            terminal: tuple(names) for terminal, names in terminal_access.items()
        },
        obstacles=tuple(obstacles),
    )
