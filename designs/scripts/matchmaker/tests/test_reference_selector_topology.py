import unittest

from matchmaker.design.reference_selector_naming import (
    VREF_SWITCH_INSTANCE_NAME,
    VSS_SWITCH_INSTANCE_NAME,
)
from matchmaker.physical.models import (
    AccessPoint,
    BoundingBox,
    PhysicalDesignSnapshot,
    PlacedInstance,
    TerminalRef,
)
from matchmaker.physical.transmission_gate_cell_access import (
    TransmissionGateCellAccessPolicy,
    classify_transmission_gate_cell_port_name,
)
from matchmaker.placement.cdac.reference_selector_intent import (
    ReferenceSelectorLayoutIntent,
    ReferenceSelectorLayoutPolicy,
)
from matchmaker.routing.planners.reference_selector_topology_planner import (
    plan_reference_selector_topology,
)
from matchmaker.specs.mos_device_spec import MosDeviceSpec
from matchmaker.specs.transmission_gate_spec import (
    ReferenceSelectorSpec,
    TransmissionGateSpec,
)


class TransmissionGateCellAccessTests(unittest.TestCase):
    def test_control_bar_cardinal_name_is_classified_by_explicit_policy(self):
        self.assertEqual(
            classify_transmission_gate_cell_port_name("control_bar_N"),
            None,
        )
        self.assertEqual(
            classify_transmission_gate_cell_port_name(
                "control_bar_N",
                policy=TransmissionGateCellAccessPolicy(
                    directions=("W", "E", "N", "S")
                ),
            ),
            ("control_bar", "N"),
        )


class ReferenceSelectorTopologyTests(unittest.TestCase):
    def _intent(self, *, route_width=None, child_gap=4.0):
        return ReferenceSelectorLayoutIntent(
            spec=ReferenceSelectorSpec(
                name="selector",
                switch=TransmissionGateSpec(
                    name="switch",
                    nmos=MosDeviceSpec("n", "nfet", 3.3, 0.31),
                    pmos=MosDeviceSpec("p", "pfet", 6.7, 0.31),
                ),
            ),
            policy=ReferenceSelectorLayoutPolicy(
                child_gap=child_gap,
                channel_clearance=2.5,
                channel_spacing=1.0,
                route_width=route_width,
            ),
        )

    def _snapshot(self, *, second_layer=None, right_xmin=4.0):
        layer = (88, 2)
        definitions = (
            (VREF_SWITCH_INSTANCE_NAME, "output", "output_E", (0.0, 0.0), 0.7, layer),
            (VSS_SWITCH_INSTANCE_NAME, "output", "output_W", (right_xmin, 0.0), 0.9, second_layer or layer),
            (VREF_SWITCH_INSTANCE_NAME, "control", "control_W", (-2.0, 1.0), 0.5, layer),
            (VSS_SWITCH_INSTANCE_NAME, "control_bar", "control_bar_E", (right_xmin + 2.0, -2.0), 0.6, layer),
            (VREF_SWITCH_INSTANCE_NAME, "control_bar", "control_bar_E", (-0.5, -1.0), 0.55, layer),
            (VSS_SWITCH_INSTANCE_NAME, "control", "control_W", (right_xmin + 0.5, -2.0), 0.65, layer),
        )
        access_points = {}
        terminal_access = {}
        for instance_name, terminal_name, port_name, center, width, port_layer in definitions:
            terminal = TerminalRef(instance_name, terminal_name)
            access_name = f"{instance_name}__{port_name}"
            access_points[access_name] = AccessPoint(
                name=access_name,
                terminal=terminal,
                primitive_port_name=port_name,
                center=center,
                orientation=0.0,
                width=width,
                layer=port_layer,
            )
            terminal_access[terminal] = (access_name,)

        instances = {
            VREF_SWITCH_INSTANCE_NAME: PlacedInstance(
                instance_name=VREF_SWITCH_INSTANCE_NAME,
                cell_name="vref_tg",
                bbox=BoundingBox(-3.0, -4.0, 0.0, 4.0),
                role="active",
                group="VREF_SWITCH",
                orientation="R0",
                row=0,
                col=0,
            ),
            VSS_SWITCH_INSTANCE_NAME: PlacedInstance(
                instance_name=VSS_SWITCH_INSTANCE_NAME,
                cell_name="vss_tg",
                bbox=BoundingBox(right_xmin, -4.0, right_xmin + 3.0, 4.0),
                role="active",
                group="VSS_SWITCH",
                orientation="R0",
                row=0,
                col=1,
            ),
        }
        return PhysicalDesignSnapshot(
            component=object(),
            instances=instances,
            access_points=access_points,
            terminal_access=terminal_access,
            obstacles=(),
        )

    def test_runtime_geometry_drives_external_selector_channels(self):
        routes = plan_reference_selector_topology(
            intent=self._intent(),
            physical_design=self._snapshot(),
        )
        self.assertEqual(len(routes.common_plan.segments), 1)
        self.assertEqual(len(routes.select_plan.segments), 5)
        self.assertEqual(len(routes.select_bar_plan.segments), 5)
        self.assertEqual(routes.common_plan.segments[0].layer, (88, 2))
        self.assertEqual(routes.common_plan.metrics.resolved_width, 0.7)
        self.assertEqual(routes.select_plan.metrics.resolved_width, 0.5)
        self.assertEqual(routes.select_bar_plan.metrics.resolved_width, 0.55)

        north_horizontal = routes.select_plan.segments[2]
        self.assertEqual(north_horizontal.start[1], 6.75)
        self.assertLess(routes.select_plan.segments[1].start[0], -3.0)
        self.assertGreater(routes.select_plan.segments[3].start[0], 7.0)

        south_horizontal = routes.select_bar_plan.segments[2]
        self.assertEqual(south_horizontal.start[1], -6.775)
        self.assertGreater(south_horizontal.start[0], 0.0)
        self.assertLess(south_horizontal.end[0], 4.0)

    def test_explicit_width_is_policy(self):
        routes = plan_reference_selector_topology(
            intent=self._intent(route_width=1.1),
            physical_design=self._snapshot(),
        )
        self.assertTrue(
            all(plan.metrics.resolved_width == 1.1 for plan in routes.plans)
        )

    def test_layer_mismatch_fails_explicitly(self):
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(),
                physical_design=self._snapshot(second_layer=(99, 0)),
            )

    def test_insufficient_inner_corridor_fails_explicitly(self):
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(),
                physical_design=self._snapshot(right_xmin=1.0),
            )


if __name__ == "__main__":
    unittest.main()
