import unittest

from matchmaker.physical.gf180_mos_access import (
    classify_gf180_mos_external_port_name,
    gf180_mos_bulk_tie_port_name,
)
from matchmaker.physical.models import (
    AccessPoint,
    BoundingBox,
    PhysicalDesignSnapshot,
    PlacedInstance,
    TerminalRef,
)
from matchmaker.placement.cdac.transmission_gate_intent import (
    TransmissionGateLayoutIntent,
    TransmissionGateLayoutPolicy,
)
from matchmaker.routing.planners.transmission_gate_topology_planner import (
    plan_transmission_gate_signal_topology,
)
from matchmaker.specs.mos_device_spec import MosDeviceSpec
from matchmaker.specs.transmission_gate_spec import TransmissionGateSpec


class Gf180MosExternalAccessTests(unittest.TestCase):
    def test_simple_external_names_are_classified(self):
        self.assertEqual(
            classify_gf180_mos_external_port_name("gate_E"),
            ("gate", "E"),
        )
        self.assertIsNone(classify_gf180_mos_external_port_name("well_N"))

    def test_only_cardinal_top_metal_tie_exports_are_bulk_accesses(self):
        self.assertEqual(
            classify_gf180_mos_external_port_name("tie_N_top_met_N"),
            ("bulk", "N"),
        )
        self.assertIsNone(
            classify_gf180_mos_external_port_name("tie_N_top_met_E")
        )
        self.assertIsNone(
            classify_gf180_mos_external_port_name("guardring_N_top_met_N")
        )
        self.assertEqual(
            gf180_mos_bulk_tie_port_name("s"),
            "tie_S_top_met_S",
        )

    def test_nested_names_are_rejected(self):
        self.assertIsNone(
            classify_gf180_mos_external_port_name("multiplier_0_gate_E")
        )


class TransmissionGateTopologyTests(unittest.TestCase):
    def _intent(self, *, route_width=None):
        return TransmissionGateLayoutIntent(
            spec=TransmissionGateSpec(
                name="test_tg",
                nmos=MosDeviceSpec("test_nmos", "nfet", 3.7, 0.31),
                pmos=MosDeviceSpec("test_pmos", "pfet", 7.1, 0.31),
            ),
            policy=TransmissionGateLayoutPolicy(route_width=route_width),
        )

    def test_default_intent_requires_primitive_bulk_ties(self):
        intent = self._intent()
        self.assertIs(intent.nmos_primitive_options.with_tie, True)
        self.assertIs(intent.pmos_primitive_options.with_tie, True)
        self.assertEqual(
            intent.policy.supply_directions,
            ("N", "E", "S", "W"),
        )

    def _snapshot(self, *, output_y=4.0):
        layer = (77, 4)
        access_points = {}
        terminal_access = {}
        definitions = (
            ("NMOS", "source", "source_E", (2.0, 1.0), 0.7),
            ("PMOS", "source", "source_W", (8.0, 1.0), 0.9),
            ("NMOS", "drain", "drain_E", (2.0, output_y), 0.8),
            ("PMOS", "drain", "drain_W", (8.0, 4.0), 1.0),
        )
        for instance_name, terminal_name, primitive_name, center, width in definitions:
            terminal = TerminalRef(instance_name, terminal_name)
            access_name = f"{instance_name}__{primitive_name}"
            access_points[access_name] = AccessPoint(
                name=access_name,
                terminal=terminal,
                primitive_port_name=primitive_name,
                center=center,
                orientation=0.0,
                width=width,
                layer=layer,
            )
            terminal_access[terminal] = (access_name,)

        instances = {
            name: PlacedInstance(
                instance_name=name,
                cell_name=f"{name.lower()}_cell",
                bbox=BoundingBox(0.0, 0.0, 1.0, 1.0),
                role="active",
                group=name,
                orientation="R0",
                row=0,
                col=index,
            )
            for index, name in enumerate(("NMOS", "PMOS"))
        }
        return PhysicalDesignSnapshot(
            component=object(),
            instances=instances,
            access_points=access_points,
            terminal_access=terminal_access,
            obstacles=(),
        )

    def test_planner_uses_runtime_layer_width_and_coordinates(self):
        bundle = plan_transmission_gate_signal_topology(
            intent=self._intent(),
            physical_design=self._snapshot(),
        )

        self.assertEqual(bundle.input_plan.segments[0].layer, (77, 4))
        self.assertEqual(bundle.input_plan.metrics.resolved_width, 0.7)
        self.assertEqual(bundle.output_plan.metrics.resolved_width, 0.8)
        self.assertEqual(bundle.input_plan.metrics.total_length, 6.0)
        self.assertEqual(bundle.output_plan.metrics.total_length, 6.0)
        self.assertEqual(bundle.input_plan.metrics.bend_count, 0)

    def test_explicit_route_width_is_policy_not_hidden_algorithm_value(self):
        bundle = plan_transmission_gate_signal_topology(
            intent=self._intent(route_width=1.25),
            physical_design=self._snapshot(),
        )
        self.assertEqual(bundle.input_plan.metrics.resolved_width, 1.25)
        self.assertEqual(bundle.output_plan.metrics.resolved_width, 1.25)

    def test_misaligned_parallel_terminal_fails_explicitly(self):
        with self.assertRaises(RuntimeError):
            plan_transmission_gate_signal_topology(
                intent=self._intent(),
                physical_design=self._snapshot(output_y=3.5),
            )


if __name__ == "__main__":
    unittest.main()
