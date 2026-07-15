from dataclasses import dataclass, field
from typing import Literal, Mapping


RouteStrategy = Literal["auto", "straight", "l", "c", "smart"]


@dataclass(frozen=True)
class RouteEndpoint:
    """Reference to one physical access point on a placed instance."""

    instance_name: str
    port_name: str

    def __post_init__(self) -> None:
        if not self.instance_name:
            raise ValueError("instance_name must be non-empty")
        if not self.port_name:
            raise ValueError("port_name must be non-empty")

    def top_port_name(self, separator: str = "__") -> str:
        return f"{self.instance_name}{separator}{self.port_name}"


@dataclass(frozen=True)
class PointToPointRouteIntent:
    """Transitional intent for one two-terminal physical connection.

    The obstacle-aware router may replace the requested access points with
    equivalent outward access points before executing a spatial dogleg. Future
    net intent will name logical terminals directly and perform access selection
    as a separate planning stage.
    """

    net_name: str
    source: RouteEndpoint
    target: RouteEndpoint
    strategy: RouteStrategy = "auto"
    route_kwargs: Mapping[str, object] = field(default_factory=dict)
    avoid_obstacles: bool = True
    obstacle_clearance: float = 1.0

    def __post_init__(self) -> None:
        if not self.net_name:
            raise ValueError("net_name must be non-empty")
        if self.source == self.target:
            raise ValueError("source and target endpoints must be different")
        if self.obstacle_clearance < 0:
            raise ValueError("obstacle_clearance must be non-negative")
