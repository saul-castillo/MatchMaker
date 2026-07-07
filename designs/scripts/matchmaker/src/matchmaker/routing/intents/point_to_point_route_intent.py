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
    """Net intent for one two-terminal physical connection."""

    net_name: str
    source: RouteEndpoint
    target: RouteEndpoint
    strategy: RouteStrategy = "auto"
    route_kwargs: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.net_name:
            raise ValueError("net_name must be non-empty")
        if self.source == self.target:
            raise ValueError("source and target endpoints must be different")
