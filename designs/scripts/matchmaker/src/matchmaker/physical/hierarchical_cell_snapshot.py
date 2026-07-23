from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from matchmaker.physical.models import (
    AccessPoint,
    BoundingBox,
    PhysicalDesignSnapshot,
    PlacedInstance,
    RoutingObstacle,
    TerminalRef,
)
from matchmaker.placement.core.placement_result import PlacementResult


CellPortClassification = tuple[str, str]
CellPortClassifier = Callable[[str], CellPortClassification | None]


@dataclass(frozen=True)
class CellFamilyAccessContract:
    """Logical interface adapter for one reusable generated-cell family.

    The classifier owns that family's port-name grammar. Snapshot construction
    remains generic and always takes physical center, orientation, width, layer,
    and transformed envelope data from the placed references at runtime.
    """

    family_name: str
    required_terminals: frozenset[str]
    classify_port_name: CellPortClassifier

    def __post_init__(self) -> None:
        if not self.family_name:
            raise ValueError("cell-family name must be non-empty")
        required = frozenset(str(name) for name in self.required_terminals)
        if not required or any(not name for name in required):
            raise ValueError("cell family requires non-empty terminal names")
        if not callable(self.classify_port_name):
            raise ValueError("cell family requires a callable port classifier")
        object.__setattr__(self, "required_terminals", required)


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


def create_hierarchical_cell_snapshot(
    placement: PlacementResult,
    *,
    contract: CellFamilyAccessContract,
    separator: str = "__",
) -> PhysicalDesignSnapshot:
    """Adapt placed children of any declared cell family into routing state."""

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
            classification = contract.classify_port_name(str(child_port.name))
            if classification is None:
                continue
            terminal_name, direction = classification
            classified_ports.append((child_port, terminal_name, direction))
            observed.add(terminal_name)

        missing = sorted(contract.required_terminals - observed)
        if missing:
            raise RuntimeError(
                f"placed {contract.family_name} cell {instance_name!r} lacks "
                f"required terminals: {', '.join(missing)}"
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
