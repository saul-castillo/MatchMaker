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
from matchmaker.routing.resources import RoutingLayerTransition
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
    signal_layer = (88, 2)
    lower_supply_layer = (77, 1)
    control_route_layer = (99, 3)

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

    def _transition(
        self,
        *,
        source_layer=None,
        via_size=(0.8, 0.8),
        minimum_route_width=0.4,
    ):
        return RoutingLayerTransition(
            source_layer=source_layer or self.signal_layer,
            route_layer=self.control_route_layer,
            via_name="via_stack",
            via_size=via_size,
            minimum_route_width=minimum_route_width,
        )

    def _snapshot(
        self,
        *,
        second_output_layer=None,
        right_xmin=4.0,
        vref_select_bar_x=-0.5,
        vdd_layer=None,
        select_right_y=2.0,
    ):
        signal = self.signal_layer
        lower = vdd_layer or self.lower_supply_layer
        definitions = (
            (
                VREF_SWITCH_INSTANCE_NAME,
                "input",
                "input_W",
                (-3.5, 1.5),
                180.0,
                0.4,
                signal,
            ),
            (
                VREF_SWITCH_INSTANCE_NAME,
                "output",
                "output_E",
                (-0.5, 1.0),
                0.0,
                0.7,
                signal,
            ),
            (
                VSS_SWITCH_INSTANCE_NAME,
                "output",
                "output_E",
                (right_xmin + 0.5, -1.0),
                180.0,
                0.9,
                second_output_layer or signal,
            ),
            (
                VSS_SWITCH_INSTANCE_NAME,
                "input",
                "input_W",
                (right_xmin + 3.5, -1.5),
                0.0,
                0.4,
                signal,
            ),
            (
                VREF_SWITCH_INSTANCE_NAME,
                "control",
                "control_W",
                (-2.0, -1.0),
                180.0,
                0.5,
                signal,
            ),
            (
                VSS_SWITCH_INSTANCE_NAME,
                "control_bar",
                "control_bar_E",
                (right_xmin + 0.5, select_right_y),
                180.0,
                0.6,
                signal,
            ),
            (
                VREF_SWITCH_INSTANCE_NAME,
                "control_bar",
                "control_bar_E",
                (vref_select_bar_x, -2.0),
                0.0,
                0.6,
                signal,
            ),
            (
                VSS_SWITCH_INSTANCE_NAME,
                "control",
                "control_W",
                (right_xmin + 2.0, 1.0),
                0.0,
                0.5,
                signal,
            ),
            (
                VREF_SWITCH_INSTANCE_NAME,
                "vss",
                "vss_N",
                (-2.0, 3.0),
                90.0,
                1.6,
                signal,
            ),
            (
                VSS_SWITCH_INSTANCE_NAME,
                "vss",
                "vss_S",
                (right_xmin + 2.0, 2.5),
                90.0,
                1.8,
                signal,
            ),
            (
                VREF_SWITCH_INSTANCE_NAME,
                "vdd",
                "vdd_E",
                (-0.5, -0.5),
                0.0,
                7.0,
                lower,
            ),
            (
                VSS_SWITCH_INSTANCE_NAME,
                "vdd",
                "vdd_E",
                (right_xmin + 0.5, 0.5),
                180.0,
                8.0,
                lower,
            ),
        )
        access_points = {}
        terminal_access: dict[TerminalRef, tuple[str, ...]] = {}
        for (
            instance_name,
            terminal_name,
            port_name,
            center,
            orientation,
            width,
            layer,
        ) in definitions:
            terminal = TerminalRef(instance_name, terminal_name)
            access_name = f"{instance_name}__{port_name}"
            access_points[access_name] = AccessPoint(
                name=access_name,
                terminal=terminal,
                primitive_port_name=port_name,
                center=center,
                orientation=orientation,
                width=width,
                layer=layer,
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
                bbox=BoundingBox(
                    right_xmin,
                    -4.0,
                    right_xmin + 3.0,
                    4.0,
                ),
                role="active",
                group="VSS_SWITCH",
                orientation="R180",
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

    def _plan(self, **snapshot_kwargs):
        return plan_reference_selector_topology(
            intent=self._intent(),
            physical_design=self._snapshot(**snapshot_kwargs),
            control_transition=self._transition(),
        )

    def test_default_policy_uses_rotationally_symmetric_child_pair(self):
        policy = self._intent().policy
        self.assertEqual(policy.vref_child_orientation, "R0")
        self.assertEqual(policy.vss_child_orientation, "R180")
        self.assertEqual(policy.control_route_glayer, "met3")

    def test_invalid_child_orientation_fails_at_policy_boundary(self):
        with self.assertRaises(ValueError):
            ReferenceSelectorLayoutPolicy(vss_child_orientation="R90")

    def test_empty_control_route_layer_fails_at_policy_boundary(self):
        with self.assertRaises(ValueError):
            ReferenceSelectorLayoutPolicy(control_route_glayer="")

    def test_transformed_geometry_drives_balanced_multilayer_topology(self):
        routes = self._plan()

        self.assertEqual(len(routes.common_plan.segments), 3)
        self.assertEqual(len(routes.select_plan.segments), 5)
        self.assertEqual(len(routes.select_bar_plan.segments), 5)
        self.assertEqual(len(routes.vss_plan.segments), 5)
        self.assertEqual(len(routes.vdd_plan.segments), 4)

        self.assertEqual(
            routes.common_plan.selected_access_point_names,
            (
                f"{VREF_SWITCH_INSTANCE_NAME}__output_E",
                f"{VSS_SWITCH_INSTANCE_NAME}__output_E",
            ),
        )
        self.assertEqual(
            routes.select_plan.selected_access_point_names,
            (
                f"{VREF_SWITCH_INSTANCE_NAME}__control_W",
                f"{VSS_SWITCH_INSTANCE_NAME}__control_bar_E",
            ),
        )
        self.assertEqual(
            routes.select_bar_plan.selected_access_point_names,
            (
                f"{VREF_SWITCH_INSTANCE_NAME}__control_bar_E",
                f"{VSS_SWITCH_INSTANCE_NAME}__control_W",
            ),
        )
        self.assertEqual(routes.select_plan.metrics.via_count, 2)
        self.assertEqual(routes.select_bar_plan.metrics.via_count, 2)
        self.assertEqual(
            routes.select_plan.metrics.total_length,
            routes.select_bar_plan.metrics.total_length,
        )
        self.assertEqual(routes.select_plan.metrics.total_length, 26.8)
        self.assertEqual(
            {segment.layer for segment in routes.select_plan.segments},
            {self.signal_layer, self.control_route_layer},
        )
        self.assertEqual(
            routes.select_plan.strategy,
            "reference_selector_balanced_north_control",
        )
        self.assertEqual(
            routes.select_bar_plan.strategy,
            "reference_selector_balanced_south_control",
        )

        self.assertEqual(
            routes.vss_plan.selected_access_point_names,
            (
                f"{VREF_SWITCH_INSTANCE_NAME}__vss_N",
                f"{VSS_SWITCH_INSTANCE_NAME}__vss_S",
                f"{VSS_SWITCH_INSTANCE_NAME}__input_W",
            ),
        )
        self.assertEqual(routes.vss_plan.metrics.resolved_width, 0.4)
        self.assertEqual(routes.vss_plan.metrics.via_count, 0)

        self.assertEqual(
            routes.vdd_plan.selected_access_point_names,
            (
                f"{VREF_SWITCH_INSTANCE_NAME}__vdd_E",
                f"{VSS_SWITCH_INSTANCE_NAME}__vdd_E",
            ),
        )
        self.assertEqual(routes.vdd_plan.segments[0].layer, self.lower_supply_layer)
        self.assertEqual(routes.vdd_plan.metrics.resolved_width, 0.4)
        self.assertEqual(
            routes.vdd_plan.strategy,
            "reference_selector_central_lower_metal_vdd",
        )

    def test_central_geometry_tracks_runtime_child_bboxes(self):
        routes = self._plan(right_xmin=8.0)
        common_trunk = routes.common_plan.segments[1]
        self.assertEqual(common_trunk.start[0], 4.0)
        self.assertEqual(common_trunk.end[0], 4.0)
        self.assertEqual(routes.select_plan.vias[1].center[0], 4.0)
        self.assertEqual(routes.select_bar_plan.vias[0].center[0], 4.0)

    def test_explicit_width_is_policy(self):
        routes = plan_reference_selector_topology(
            intent=self._intent(route_width=0.8),
            physical_design=self._snapshot(),
            control_transition=self._transition(),
        )
        self.assertTrue(
            all(plan.metrics.resolved_width == 0.8 for plan in routes.plans)
        )

    def test_explicit_supply_width_does_not_change_signal_routes(self):
        routes = plan_reference_selector_topology(
            intent=self._intent(supply_route_width=0.8),
            physical_design=self._snapshot(),
            control_transition=self._transition(),
        )
        self.assertEqual(routes.common_plan.metrics.resolved_width, 0.7)
        self.assertEqual(routes.select_plan.metrics.resolved_width, 0.5)
        self.assertEqual(routes.vss_plan.metrics.resolved_width, 0.8)
        self.assertEqual(routes.vdd_plan.metrics.resolved_width, 0.8)

    def test_vss_lane_must_fit_between_child_and_control_channel(self):
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(route_width=3.0),
                physical_design=self._snapshot(),
                control_transition=self._transition(),
            )

    def test_common_layer_mismatch_fails_explicitly(self):
        with self.assertRaises(RuntimeError):
            self._plan(second_output_layer=(100, 0))

    def test_control_transition_source_layer_must_match_accesses(self):
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(),
                physical_design=self._snapshot(),
                control_transition=self._transition(source_layer=(100, 0)),
            )

    def test_upper_layer_minimum_width_does_not_widen_source_stubs(self):
        routes = plan_reference_selector_topology(
            intent=self._intent(),
            physical_design=self._snapshot(),
            control_transition=self._transition(minimum_route_width=0.9),
        )
        self.assertEqual(routes.select_plan.segments[0].width, 0.5)
        self.assertEqual(routes.select_plan.segments[-1].width, 0.5)
        self.assertTrue(
            all(
                segment.width == 0.9
                for segment in routes.select_plan.segments[1:-1]
            )
        )

    def test_central_via_envelope_must_clear_common(self):
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(),
                physical_design=self._snapshot(),
                control_transition=self._transition(via_size=(0.8, 1.4)),
            )

    def test_overlapping_children_fail_explicitly(self):
        with self.assertRaises(RuntimeError):
            self._plan(right_xmin=-0.5)

    def test_child_gap_must_contain_control_via(self):
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(),
                physical_design=self._snapshot(right_xmin=0.5),
                control_transition=self._transition(via_size=(0.8, 0.8)),
            )

    def test_transformed_control_order_must_support_balanced_topology(self):
        with self.assertRaises(RuntimeError):
            self._plan(vref_select_bar_x=2.5)
        with self.assertRaises(RuntimeError):
            self._plan(select_right_y=-3.0)

    def test_vdd_ties_must_be_on_lower_layer(self):
        with self.assertRaises(RuntimeError):
            self._plan(vdd_layer=self.signal_layer)


if __name__ == "__main__":
    unittest.main()
