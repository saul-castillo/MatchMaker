from dataclasses import dataclass

from matchmaker.physical.models import LayerRef


@dataclass(frozen=True)
class RoutingLayerTransition:
    """Execution resources for escaping one net onto another routing layer."""

    source_layer: LayerRef
    route_layer: LayerRef
    via_name: str
    via_size: tuple[float, float]
    minimum_route_width: float

    def __post_init__(self) -> None:
        if self.source_layer == self.route_layer:
            raise ValueError("routing transition layers must be different")
        if not self.via_name:
            raise ValueError("routing transition via_name must be non-empty")
        if len(self.via_size) != 2 or any(size <= 0 for size in self.via_size):
            raise ValueError("routing transition via_size must be positive")
        if self.minimum_route_width <= 0:
            raise ValueError("minimum_route_width must be positive")
