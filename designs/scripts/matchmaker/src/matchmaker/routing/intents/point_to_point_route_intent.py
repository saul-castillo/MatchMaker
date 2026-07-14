from dataclasses import dataclass, field
from typing import Literal, Mapping


RouteStrategy = Literal["auto", "straight", "l", "c", "smart"]


@dataclass(frozen=True)
class RouteEndpoint:
    """Stable reference to one promoted placement port."""

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
    """Net intent for one two-terminal physical connection.

    When obstacle avoidance is enabled, cardinal MOS terminal ports may be
    exchanged for equivalent cardinal access points on the same terminal. For
    example, a blocked ``gate_E`` request may execute through ``gate_N``.
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
