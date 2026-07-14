from dataclasses import dataclass, field
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

    def as_legacy_mapping(self) -> dict[str, object]:
        return {
            "instance_name": self.owner_instance_name or self.obstacle_id,
            "bbox": self.bbox.as_corners(),
        }


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

    def legacy_obstacles(self) -> tuple[dict[str, object], ...]:
        """Temporary adapter for the current obstacle-aware route planners."""
        return tuple(obstacle.as_legacy_mapping() for obstacle in self.obstacles)
