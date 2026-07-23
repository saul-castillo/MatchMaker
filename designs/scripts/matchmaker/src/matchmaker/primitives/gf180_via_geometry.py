from collections.abc import Callable

from matchmaker.physical.models import LayerRef
from matchmaker.routing.plans.route_plan import ViaPlan
from matchmaker.routing.resources import RoutingLayerTransition


def _normalize_layer(layer) -> LayerRef:
    if isinstance(layer, (tuple, list)) and len(layer) == 2:
        return int(layer[0]), int(layer[1])
    return str(layer)


def _load_via_stack_builder():
    try:
        from glayout.primitives.via_gen import via_stack
    except ModuleNotFoundError:
        from glayout.flow.primitives.via_gen import via_stack
    return via_stack


def _bbox_size(component) -> tuple[float, float]:
    (xmin, ymin), (xmax, ymax) = component.bbox
    return float(xmax) - float(xmin), float(ymax) - float(ymin)


class Gf180ViaGeometryFactory:
    """Resolve GF180 routing layers and build centered gLayout via stacks."""

    _ROUTING_LAYER_NAMES = ("met1", "met2", "met3", "met4", "met5")

    def __init__(self, pdk, *, via_stack_builder: Callable | None = None):
        self._pdk = pdk
        self._via_stack_builder = via_stack_builder or _load_via_stack_builder()

    def layer_ref(self, generic_layer_name: str) -> LayerRef:
        return _normalize_layer(self._pdk.get_glayer(generic_layer_name))

    def _generic_layer_name(self, layer: LayerRef) -> str:
        normalized = _normalize_layer(layer)
        for name in self._ROUTING_LAYER_NAMES:
            if self.layer_ref(name) == normalized:
                return name
        raise RuntimeError(f"GF180 routing layer is not recognized: {layer!r}")

    def _build_between(self, first_layer: LayerRef, second_layer: LayerRef):
        return self._via_stack_builder(
            pdk=self._pdk,
            glayer1=self._generic_layer_name(first_layer),
            glayer2=self._generic_layer_name(second_layer),
            centered=True,
        )

    def describe_transition(
        self,
        *,
        source_layer: LayerRef,
        route_generic_layer: str,
    ) -> RoutingLayerTransition:
        route_layer = self.layer_ref(route_generic_layer)
        prototype = self._build_between(source_layer, route_layer)
        minimum_width = float(
            self._pdk.get_grule(route_generic_layer)["min_width"]
        )
        return RoutingLayerTransition(
            source_layer=_normalize_layer(source_layer),
            route_layer=route_layer,
            via_name="via_stack",
            via_size=_bbox_size(prototype),
            minimum_route_width=minimum_width,
        )

    def __call__(self, via: ViaPlan):
        if via.via_name != "via_stack":
            raise RuntimeError(f"unsupported GF180 via geometry: {via.via_name!r}")
        return self._build_between(via.lower_layer, via.upper_layer)
