from collections import defaultdict
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from matchmaker.physical.models import (
    AccessPoint,
    BoundingBox,
    PhysicalDesignSnapshot,
    PlacedInstance,
    RoutingObstacle,
    TerminalRef,
)
from matchmaker.placement.core.placement_result import PlacementResult


@dataclass(frozen=True)
class Gf180MimExternalAccessPolicy:
    """Installed-gLayout port grammar for public GF180 MIM accesses.

    This policy is the only place that interprets primitive port-name tokens.
    Layer numbers, widths, centers, and orientations are always read from the
    actual placed ports at runtime.
    """

    electrode_aliases: Mapping[str, str] = field(
        default_factory=lambda: {"top": "top", "bottom": "bottom"}
    )
    conductor_token: str = "met"
    directions: tuple[str, ...] = ("N", "E", "S", "W")

    def __post_init__(self) -> None:
        aliases = {
            str(source).lower(): str(target).lower()
            for source, target in self.electrode_aliases.items()
        }
        if not aliases:
            raise ValueError("MIM access policy requires at least one electrode alias")
        if any(not source or not target for source, target in aliases.items()):
            raise ValueError("MIM electrode aliases must be non-empty")
        conductor = self.conductor_token.strip().lower()
        if not conductor:
            raise ValueError("MIM conductor token must be non-empty")
        directions = tuple(str(direction).upper() for direction in self.directions)
        if not directions or any(direction not in {"N", "E", "S", "W"} for direction in directions):
            raise ValueError("MIM access directions must be cardinal")
        if len(set(directions)) != len(directions):
            raise ValueError("MIM access directions must be unique")

        object.__setattr__(self, "electrode_aliases", MappingProxyType(aliases))
        object.__setattr__(self, "conductor_token", conductor)
        object.__setattr__(self, "directions", directions)

    def classify(self, port_name: str) -> str | None:
        """Return a canonical terminal for one exact external access name.

        The installed primitive exposes public names such as ``top_met_E`` and
        ``bottom_met_N`` plus many nested names such as
        ``array_row0_col0_top_met_E``. Exact three-token matching retains only
        the public access family and rejects nested implementation exports.
        """

        parts = str(port_name).split("_")
        if len(parts) != 3:
            return None
        electrode_token, conductor_token, direction = parts
        if conductor_token.lower() != self.conductor_token:
            return None
        if direction.upper() not in self.directions:
            return None
        return self.electrode_aliases.get(electrode_token.lower())


DEFAULT_GF180_MIM_EXTERNAL_ACCESS_POLICY = Gf180MimExternalAccessPolicy()


def classify_gf180_mim_external_port_name(
    port_name: str,
    policy: Gf180MimExternalAccessPolicy = DEFAULT_GF180_MIM_EXTERNAL_ACCESS_POLICY,
) -> str | None:
    return policy.classify(port_name)


def _normalize_layer(layer):
    if isinstance(layer, (tuple, list)) and len(layer) == 2:
        return (int(layer[0]), int(layer[1]))
    return str(layer)


def _ports(reference) -> tuple:
    if hasattr(reference, "get_ports_list"):
        return tuple(reference.get_ports_list())
    ports = getattr(reference, "ports", None)
    if ports is None:
        raise TypeError("Placed capacitor reference does not expose ports")
    if hasattr(ports, "values"):
        return tuple(ports.values())
    return tuple(ports)


def create_cdac_capacitor_array_physical_design_snapshot(
    placement_result: PlacementResult,
    *,
    access_policy: Gf180MimExternalAccessPolicy = DEFAULT_GF180_MIM_EXTERNAL_ACCESS_POLICY,
    separator: str = "__",
) -> PhysicalDesignSnapshot:
    """Promote canonical capacitor accesses and capture typed physical state.

    Stable instance/reference bindings come directly from ``PlacementResult``;
    reference ordering is never used to recover logical identity.
    """

    if not separator:
        raise ValueError("access-name separator must be non-empty")

    component = placement_result.component
    placed_instances: dict[str, PlacedInstance] = {}
    access_points: dict[str, AccessPoint] = {}
    terminal_access_names: dict[TerminalRef, list[str]] = defaultdict(list)
    obstacles: list[RoutingObstacle] = []

    for tile in placement_result.plan.tiles:
        binding = placement_result.binding(tile.name)
        if (
            binding.row != tile.row
            or binding.col != tile.col
            or binding.orientation != tile.orientation
            or binding.group != tile.group
            or binding.role != tile.role
        ):
            raise ValueError(
                f"Placement binding does not match capacitor tile metadata: {tile.name!r}"
            )

        routable_ports: list[tuple[object, str]] = []
        for primitive_port in sorted(
            _ports(binding.reference),
            key=lambda port: str(getattr(port, "name", "")),
        ):
            canonical_terminal = access_policy.classify(str(primitive_port.name))
            if canonical_terminal is not None:
                routable_ports.append((primitive_port, canonical_terminal))

        if not routable_ports:
            raise RuntimeError(
                "Placed MIM capacitor exposes no supported external accesses: "
                f"instance={binding.instance_name!r}, cell={binding.cell_name!r}"
            )

        prefix = f"{binding.instance_name}{separator}"
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
                instance_name=binding.instance_name,
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

        bbox = BoundingBox.from_corners(binding.reference.bbox)
        placed_instances[binding.instance_name] = PlacedInstance(
            instance_name=binding.instance_name,
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
                obstacle_id=f"instance:{binding.instance_name}",
                owner_instance_name=binding.instance_name,
                bbox=bbox,
                kind="mim_capacitor",
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
