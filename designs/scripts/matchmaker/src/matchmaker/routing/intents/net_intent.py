from dataclasses import dataclass, field
from typing import Literal

from matchmaker.physical.models import LayerRef, TerminalRef


RouteStrategyPreference = Literal["auto", "straight", "manhattan", "dogleg"]


@dataclass(frozen=True)
class NetConstraintProfile:
    """Typed hard constraints and soft-cost weights for one logical net.

    ``width_class`` carries semantic intent for later PDK rule resolution. The
    current two-terminal planner uses ``width`` when provided and otherwise
    resolves to the minimum width of the selected physical access points.
    """

    width_class: str = "signal"
    width: float | None = None
    avoid_obstacles: bool = True
    obstacle_clearance: float = 1.0
    allowed_layers: tuple[LayerRef, ...] = ()
    forbidden_layers: tuple[LayerRef, ...] = ()
    max_length: float | None = None
    max_bends: int | None = None
    length_weight: float = 1.0
    bend_penalty: float = 0.25
    via_penalty: float = 1.0
    priority: int = 0

    def __post_init__(self) -> None:
        if not self.width_class:
            raise ValueError("width_class must be non-empty")
        if self.width is not None and self.width <= 0:
            raise ValueError("width must be positive when provided")
        if self.obstacle_clearance < 0:
            raise ValueError("obstacle_clearance must be non-negative")
        if self.max_length is not None and self.max_length <= 0:
            raise ValueError("max_length must be positive when provided")
        if self.max_bends is not None and self.max_bends < 0:
            raise ValueError("max_bends must be non-negative when provided")
        if self.length_weight < 0:
            raise ValueError("length_weight must be non-negative")
        if self.bend_penalty < 0:
            raise ValueError("bend_penalty must be non-negative")
        if self.via_penalty < 0:
            raise ValueError("via_penalty must be non-negative")

        allowed = tuple(self.allowed_layers)
        forbidden = tuple(self.forbidden_layers)
        overlap = set(allowed) & set(forbidden)
        if overlap:
            raise ValueError(
                "allowed_layers and forbidden_layers overlap: "
                + ", ".join(map(str, sorted(overlap, key=str)))
            )
        object.__setattr__(self, "allowed_layers", allowed)
        object.__setattr__(self, "forbidden_layers", forbidden)


@dataclass(frozen=True)
class NetIntent:
    """Logical connectivity request independent of concrete physical ports."""

    name: str
    terminals: tuple[TerminalRef, ...]
    constraints: NetConstraintProfile = field(default_factory=NetConstraintProfile)
    strategy_preference: RouteStrategyPreference = "auto"

    def __post_init__(self) -> None:
        terminals = tuple(self.terminals)
        if not self.name:
            raise ValueError("net name must be non-empty")
        if len(terminals) < 2:
            raise ValueError("a net requires at least two logical terminals")
        if len(set(terminals)) != len(terminals):
            raise ValueError("logical net terminals must be unique")
        object.__setattr__(self, "terminals", terminals)


@dataclass(frozen=True)
class RouteGroupConstraintProfile:
    """Constraints that relate two or more nets.

    Planning for these constraints is intentionally deferred; the typed model is
    introduced now so matching, symmetry, and separation do not become ad-hoc
    per-net flags later.
    """

    minimum_separation: float | None = None
    matched_length_tolerance: float | None = None
    symmetry_axis: tuple[Literal["x", "y"], float] | None = None
    equal_bend_count: bool = False
    equal_via_count: bool = False
    shield_net_name: str | None = None

    def __post_init__(self) -> None:
        if self.minimum_separation is not None and self.minimum_separation < 0:
            raise ValueError("minimum_separation must be non-negative")
        if (
            self.matched_length_tolerance is not None
            and self.matched_length_tolerance < 0
        ):
            raise ValueError("matched_length_tolerance must be non-negative")
        if self.symmetry_axis is not None:
            axis, coordinate = self.symmetry_axis
            if axis not in {"x", "y"}:
                raise ValueError("symmetry axis must be 'x' or 'y'")
            object.__setattr__(self, "symmetry_axis", (axis, float(coordinate)))
        if self.shield_net_name is not None and not self.shield_net_name:
            raise ValueError("shield_net_name must be non-empty when provided")


@dataclass(frozen=True)
class RouteGroupIntent:
    name: str
    nets: tuple[NetIntent, ...]
    constraints: RouteGroupConstraintProfile = field(
        default_factory=RouteGroupConstraintProfile
    )

    def __post_init__(self) -> None:
        nets = tuple(self.nets)
        if not self.name:
            raise ValueError("route-group name must be non-empty")
        if len(nets) < 2:
            raise ValueError("a route group requires at least two nets")
        names = [net.name for net in nets]
        if len(set(names)) != len(names):
            raise ValueError("route-group net names must be unique")
        object.__setattr__(self, "nets", nets)
