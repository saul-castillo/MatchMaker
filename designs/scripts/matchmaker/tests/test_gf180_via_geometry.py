from types import SimpleNamespace
import unittest

from matchmaker.primitives.gf180_via_geometry import Gf180ViaGeometryFactory
from matchmaker.routing.plans.route_plan import ViaPlan
from matchmaker.routing.resources import RoutingLayerTransition


class _FakePdk:
    layers = {
        "met1": (34, 0),
        "met2": (36, 0),
        "met3": (42, 0),
        "met4": (46, 0),
        "met5": (81, 0),
    }

    def get_glayer(self, name):
        return self.layers[name]

    def get_grule(self, name):
        return {"min_width": 0.72}


class _FakeViaBuilder:
    def __init__(self):
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(bbox=((-0.4, -0.5), (0.4, 0.5)))


class Gf180ViaGeometryFactoryTests(unittest.TestCase):
    def test_transition_uses_runtime_layer_map_rules_and_via_bbox(self):
        builder = _FakeViaBuilder()
        factory = Gf180ViaGeometryFactory(
            _FakePdk(),
            via_stack_builder=builder,
        )

        transition = factory.describe_transition(
            source_layer=(36, 0),
            route_generic_layer="met3",
        )

        self.assertEqual(transition.source_layer, (36, 0))
        self.assertEqual(transition.route_layer, (42, 0))
        self.assertEqual(transition.via_size, (0.8, 1.0))
        self.assertEqual(transition.minimum_route_width, 0.72)
        self.assertEqual(builder.calls[0]["glayer1"], "met2")
        self.assertEqual(builder.calls[0]["glayer2"], "met3")

    def test_via_plan_builds_centered_geometry_from_numeric_layers(self):
        builder = _FakeViaBuilder()
        factory = Gf180ViaGeometryFactory(
            _FakePdk(),
            via_stack_builder=builder,
        )
        component = factory(
            ViaPlan(
                center=(3.0, 4.0),
                lower_layer=(36, 0),
                upper_layer=(42, 0),
                via_name="via_stack",
            )
        )
        self.assertEqual(component.bbox, ((-0.4, -0.5), (0.4, 0.5)))
        self.assertEqual(builder.calls[0]["glayer1"], "met2")
        self.assertEqual(builder.calls[0]["glayer2"], "met3")

    def test_unknown_layer_and_via_name_fail_explicitly(self):
        factory = Gf180ViaGeometryFactory(
            _FakePdk(),
            via_stack_builder=_FakeViaBuilder(),
        )
        with self.assertRaises(RuntimeError):
            factory(
                ViaPlan(
                    center=(0.0, 0.0),
                    lower_layer=(999, 0),
                    upper_layer=(42, 0),
                    via_name="via_stack",
                )
            )
        with self.assertRaises(RuntimeError):
            factory(
                ViaPlan(
                    center=(0.0, 0.0),
                    lower_layer=(36, 0),
                    upper_layer=(42, 0),
                    via_name="custom",
                )
            )


class RoutingLayerTransitionTests(unittest.TestCase):
    def test_invalid_transition_resources_are_rejected(self):
        with self.assertRaises(ValueError):
            RoutingLayerTransition(
                source_layer=(36, 0),
                route_layer=(36, 0),
                via_name="via_stack",
                via_size=(0.8, 0.8),
                minimum_route_width=0.5,
            )
        with self.assertRaises(ValueError):
            RoutingLayerTransition(
                source_layer=(36, 0),
                route_layer=(42, 0),
                via_name="via_stack",
                via_size=(0.0, 0.8),
                minimum_route_width=0.5,
            )


if __name__ == "__main__":
    unittest.main()
