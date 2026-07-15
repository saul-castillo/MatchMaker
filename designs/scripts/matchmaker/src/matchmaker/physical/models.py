from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


LayerRef = str | tuple[int, int]


@dataclass(frozen=True, order=True)
class TerminalRef:
    """Logical electrical terminal on one placed instance."""

    instance_name: str
    terminal_name: str

    def __post_init__(self) -> None:
        if not self.instance_name:
            raise ValueError("instance_name must be non-empty")
        if not self.terminal_name:
            raise ValueError("terminal_name must be non-empty")


@dataclass(frozen=True)
class BoundingBox:
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    def __post_init__(self) -> None:
        if self.xmax < self.xmin:
            raise ValueError("xmax must be greater than or equal to xmin")
        if self.ymax < self.ymin:
            raise ValueError("ymax must be greater than or equal to ymin")

    @classmethod
    def from_corners(cls, corners) -> "BoundingBox":
        (xmin, ymin), (xmax, ymax) = corners
        return cls(float(xmin), float(ymin), float(xmax), float(ymax))

    def as_corners(self) -> tuple[tuple[float, float], tuple[float, float]]:
        return ((self.xmin, self.ymin), (self.xmax, self.ymax))

    @property
    def width(self) -> float:
        return self.xmax - self.xmin

    @property
    def height(self) -> float:
        return self.ymax - self.ymin


@dataclass(frozen=True)
class AccessPoint:
    """One physical contact option for a logical terminal."""

    name: str
    terminal: TerminalRef
    primitive_port_name: str
    center: tuple[float, float]
    orientation: float
    width: float
    layer: LayerRef

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("access-point name must be non-empty")
        if not self.primitive_port_name:
            raise ValueError("primitive_port_name must be non-empty")
        if self.width <= 0:
            raise ValueError("access-point width must be positive")


@dataclass(frozen=True)
class PlacedInstance:
    """Stable physical record for one placed tile or primitive instance."""

    instance_name: str
    cell_name: str
    bbox: BoundingBox
    role: str
    group: str
    orientation: str
    row: int
    col: int
    access_point_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.instance_name:
            raise ValueError("instance_name must be non-empty")
        if not self.cell_name:
            raise ValueError("cell_name must be non-empty")


@dataclass(frozen=True)
class RoutingObstacle:
    obstacle_id: str
    bbox: BoundingBox
    owner_instance_name: str | None = None
    kind: str = "instance"

    def __post_init__(self) -> None:
        if not self.obstacle_id:
            raise ValueError("obstacle_id must be non-empty")
        if not self.kind:
            raise ValueError("obstacle kind must be non-empty")

    @property
    def display_name(self) -> str:
        return self.owner_instance_name or self.obstacle_id


@dataclass(frozen=True)
class PhysicalDesignSnapshot:
    """Read-only physical state consumed by routing and verification planners."""

    component: object
    instances: Mapping[str, PlacedInstance]
    access_points: Mapping[str, AccessPoint]
    terminal_access: Mapping[TerminalRef, tuple[str, ...]]
    obstacles: tuple[RoutingObstacle, ...]
    keepouts: tuple[RoutingObstacle, ...] = ()
    committed_routes: tuple[object, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        instances = dict(self.instances)
        access_points = dict(self.access_points)
        terminal_access = {
            terminal: tuple(names)
            for terminal, names in self.terminal_access.items()
        }

        for key, instance in instances.items():
            if key != instance.instance_name:
                raise ValueError(
                    "instance mapping key does not match PlacedInstance.instance_name: "
                    f"{key!r} != {instance.instance_name!r}"
                )
        for key, access_point in access_points.items():
            if key != access_point.name:
                raise ValueError(
                    "access-point mapping key does not match AccessPoint.name: "
                    f"{key!r} != {access_point.name!r}"
                )
        for terminal, names in terminal_access.items():
            for name in names:
                access_point = access_points.get(name)
                if access_point is None:
                    raise ValueError(
                        f"terminal_access references unknown access point {name!r}"
                    )
                if access_point.terminal != terminal:
                    raise ValueError(
                        f"access point {name!r} belongs to a different terminal"
                    )

        object.__setattr__(self, "instances", MappingProxyType(instances))
        object.__setattr__(self, "access_points", MappingProxyType(access_points))
        object.__setattr__(self, "terminal_access", MappingProxyType(terminal_access))
        object.__setattr__(self, "obstacles", tuple(self.obstacles))
        object.__setattr__(self, "keepouts", tuple(self.keepouts))
        object.__setattr__(self, "committed_routes", tuple(self.committed_routes))

    def instance(self, instance_name: str) -> PlacedInstance:
        try:
            return self.instances[instance_name]
        except KeyError as error:
            raise KeyError(f"Unknown placed instance: {instance_name}") from error

    def access_point(self, access_point_name: str) -> AccessPoint:
        try:
            return self.access_points[access_point_name]
        except KeyError as error:
            raise KeyError(f"Unknown physical access point: {access_point_name}") from error

    def access_points_for(self, terminal: TerminalRef) -> tuple[AccessPoint, ...]:
        names = self.terminal_access.get(terminal, ())
        return tuple(self.access_points[name] for name in names)
