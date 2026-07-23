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

    def test_supply_ports_are_classified_only_when_requested(self):
        self.assertIsNone(classify_transmission_gate_cell_port_name("vss_N"))
        policy = TransmissionGateCellAccessPolicy(
            terminals=(
                "input",
                "output",
                "control",
                "control_bar",
                "vss",
                "vdd",
            ),
            directions=("W", "E", "N", "S"),
        )
        self.assertEqual(
            classify_transmission_gate_cell_port_name("vss_N", policy=policy),
            ("vss", "N"),
        )
        self.assertEqual(
            classify_transmission_gate_cell_port_name("vdd_S", policy=policy),
            ("vdd", "S"),
        )


class ReferenceSelectorTopologyTests(unittest.TestCase):
    def _intent(self, *, route_width=None, supply_route_width=None):
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
                child_gap=4.0,
                channel_clearance=2.5,
                route_width=route_width,
                supply_route_width=supply_route_width,
            ),
        )

    def _snapshot(
        self,
        *,
        second_layer=None,
        right_xmin=4.0,
        vref_select_bar_x=-0.5,
    ):
        layer = (88, 2)
        definitions = (
            (VREF_SWITCH_INSTANCE_NAME, "output", "output_E", (0.0, 0.0), 0.7, layer),
            (VSS_SWITCH_INSTANCE_NAME, "output", "output_W", (right_xmin, 0.0), 0.9, second_layer or layer),
            (VSS_SWITCH_INSTANCE_NAME, "input", "input_E", (right_xmin + 2.0, 1.5), 0.4, layer),
            (VREF_SWITCH_INSTANCE_NAME, "control", "control_W", (-2.0, 1.0), 0.5, layer),
            (VSS_SWITCH_INSTANCE_NAME, "control_bar", "control_bar_E", (right_xmin + 2.0, -2.0), 0.6, layer),
            (VREF_SWITCH_INSTANCE_NAME, "control_bar", "control_bar_E", (vref_select_bar_x, -1.0), 0.55, layer),
            (VSS_SWITCH_INSTANCE_NAME, "control", "control_W", (right_xmin + 0.5, -2.0), 0.65, layer),
            (VREF_SWITCH_INSTANCE_NAME, "vss", "vss_N", (-2.0, 3.0), 1.6, layer),
            (VSS_SWITCH_INSTANCE_NAME, "vss", "vss_N", (right_xmin + 1.0, 3.0), 1.8, layer),
            (VREF_SWITCH_INSTANCE_NAME, "vdd", "vdd_S", (-1.0, -3.0), 1.4, layer),
            (VSS_SWITCH_INSTANCE_NAME, "vdd", "vdd_S", (right_xmin + 1.0, -3.0), 1.6, layer),
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

    def test_runtime_geometry_drives_north_perimeter_and_central_trunk(self):
        routes = plan_reference_selector_topology(
            intent=self._intent(),
            physical_design=self._snapshot(),
        )
        self.assertEqual(len(routes.common_plan.segments), 1)
        self.assertEqual(len(routes.select_plan.segments), 5)
        self.assertEqual(len(routes.select_bar_plan.segments), 3)
        self.assertEqual(len(routes.vss_plan.segments), 5)
        self.assertEqual(len(routes.vdd_plan.segments), 3)
        self.assertEqual(routes.common_plan.segments[0].layer, (88, 2))
        self.assertEqual(routes.common_plan.metrics.resolved_width, 0.7)
        self.assertEqual(routes.select_plan.metrics.resolved_width, 0.5)
        self.assertEqual(routes.select_bar_plan.metrics.resolved_width, 0.55)
        self.assertEqual(routes.vss_plan.metrics.resolved_width, 0.4)
        self.assertEqual(routes.vdd_plan.metrics.resolved_width, 0.4)

        north_horizontal = routes.select_plan.segments[2]
        self.assertEqual(north_horizontal.start[1], 6.75)
        self.assertLess(north_horizontal.start[0], -3.0)
        self.assertGreater(north_horizontal.end[0], 7.0)

        self.assertEqual(
            routes.select_bar_plan.selected_access_point_names,
            (
                f"{VREF_SWITCH_INSTANCE_NAME}__control_bar_E",
                f"{VSS_SWITCH_INSTANCE_NAME}__control_W",
            ),
        )
        central_trunk = routes.select_bar_plan.segments[1]
        self.assertEqual(central_trunk.orientation, "vertical")
        self.assertEqual(central_trunk.start, (2.0, -1.0))
        self.assertEqual(central_trunk.end, (2.0, -2.0))
        self.assertGreater(
            central_trunk.start[0]
            - routes.select_bar_plan.metrics.resolved_width / 2.0,
            0.0,
        )
        self.assertLess(
            central_trunk.start[0]
            + routes.select_bar_plan.metrics.resolved_width / 2.0,
            4.0,
        )
        self.assertEqual(routes.select_bar_plan.metrics.bend_count, 2)
        self.assertEqual(routes.select_bar_plan.metrics.total_length, 6.0)
        self.assertEqual(
            routes.select_bar_plan.strategy,
            "reference_selector_central_gap_control",
        )

        self.assertEqual(
            routes.vss_plan.selected_access_point_names,
            (
                f"{VREF_SWITCH_INSTANCE_NAME}__vss_N",
                f"{VSS_SWITCH_INSTANCE_NAME}__vss_N",
                f"{VSS_SWITCH_INSTANCE_NAME}__input_E",
            ),
        )
        vss_rail = routes.vss_plan.segments[2]
        self.assertEqual(vss_rail.orientation, "horizontal")
        self.assertEqual(vss_rail.start, (-2.0, 5.25))
        self.assertEqual(vss_rail.end, (8.25, 5.25))
        self.assertEqual(routes.vss_plan.metrics.via_count, 0)

        self.assertEqual(
            routes.vdd_plan.selected_access_point_names,
            (
                f"{VREF_SWITCH_INSTANCE_NAME}__vdd_S",
                f"{VSS_SWITCH_INSTANCE_NAME}__vdd_S",
            ),
        )
        vdd_rail = routes.vdd_plan.segments[1]
        self.assertEqual(vdd_rail.orientation, "horizontal")
        self.assertEqual(vdd_rail.start, (-1.0, -6.7))
        self.assertEqual(vdd_rail.end, (5.0, -6.7))
        self.assertEqual(routes.vdd_plan.metrics.via_count, 0)

    def test_central_trunk_x_is_derived_from_runtime_child_bboxes(self):
        routes = plan_reference_selector_topology(
            intent=self._intent(),
            physical_design=self._snapshot(right_xmin=8.0),
        )
        central_trunk = routes.select_bar_plan.segments[1]
        self.assertEqual(central_trunk.start[0], 4.0)
        self.assertEqual(central_trunk.end[0], 4.0)

    def test_explicit_width_is_policy(self):
        routes = plan_reference_selector_topology(
            intent=self._intent(route_width=1.1),
            physical_design=self._snapshot(),
        )
        self.assertTrue(
            all(plan.metrics.resolved_width == 1.1 for plan in routes.plans)
        )

    def test_explicit_supply_width_does_not_change_signal_routes(self):
        routes = plan_reference_selector_topology(
            intent=self._intent(supply_route_width=0.8),
            physical_design=self._snapshot(),
        )
        self.assertEqual(routes.common_plan.metrics.resolved_width, 0.7)
        self.assertEqual(routes.vss_plan.metrics.resolved_width, 0.8)
        self.assertEqual(routes.vdd_plan.metrics.resolved_width, 0.8)

    def test_vss_lane_must_fit_between_child_and_select_perimeter(self):
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(route_width=2.5),
                physical_design=self._snapshot(),
            )

    def test_layer_mismatch_fails_explicitly(self):
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(),
                physical_design=self._snapshot(second_layer=(99, 0)),
            )

    def test_overlapping_children_fail_explicitly(self):
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(),
                physical_design=self._snapshot(right_xmin=-0.5),
            )

    def test_child_gap_must_contain_central_trunk_width(self):
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(),
                physical_design=self._snapshot(right_xmin=0.5),
            )

    def test_inner_accesses_must_face_central_trunk(self):
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(),
                physical_design=self._snapshot(vref_select_bar_x=2.5),
            )


if __name__ == "__main__":
    unittest.main()
