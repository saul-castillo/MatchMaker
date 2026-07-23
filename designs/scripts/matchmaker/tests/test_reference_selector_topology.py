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

    def test_terminal_direction_rules_filter_unsafe_family_accesses(self):
        policy = TransmissionGateCellAccessPolicy(
            terminals=("input", "control", "control_bar", "vss"),
            directions=("W", "E", "N", "S"),
            terminal_directions=(
                ("input", ("W", "E")),
                ("control", ("W",)),
                ("control_bar", ("E",)),
                ("vss", ("N", "S")),
            ),
        )
        self.assertEqual(
            classify_transmission_gate_cell_port_name("control_W", policy=policy),
            ("control", "W"),
        )
        self.assertIsNone(
            classify_transmission_gate_cell_port_name("control_E", policy=policy)
        )
        self.assertIsNone(
            classify_transmission_gate_cell_port_name("vss_E", policy=policy)
        )

    def test_terminal_direction_rules_reject_unknown_terminals(self):
        with self.assertRaises(ValueError):
            TransmissionGateCellAccessPolicy(
                terminals=("input",),
                directions=("W", "E"),
                terminal_directions=(("output", ("E",)),),
            )


class ReferenceSelectorTopologyTests(unittest.TestCase):
    signal_layer = (88, 2)
    upper_layer = (99, 3)

    def _intent(
        self,
        *,
        route_width=None,
        supply_route_width=None,
        child_axis="vertical",
        vref_child_side="high",
    ):
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
                channel_clearance=2.0,
                route_width=route_width,
                supply_route_width=supply_route_width,
                child_axis=child_axis,
                vref_child_side=vref_child_side,
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
            route_layer=self.upper_layer,
            via_name="via_stack",
            via_size=via_size,
            minimum_route_width=minimum_route_width,
        )

    def _snapshot(
        self,
        *,
        vref_ymin=2.0,
        vss_ymax=-2.0,
        select_bar_x=4.0,
        second_output_layer=None,
        second_vdd_layer=None,
    ):
        signal = self.signal_layer
        definitions = (
            (
                VREF_SWITCH_INSTANCE_NAME,
                "input",
                "input_E",
                (5.0, 9.0),
                0.0,
                0.5,
                signal,
            ),
            (
                VSS_SWITCH_INSTANCE_NAME,
                "input",
                "input_W",
                (5.0, -9.0),
                0.0,
                0.5,
                signal,
            ),
            (
                VREF_SWITCH_INSTANCE_NAME,
                "output",
                "output_W",
                (-5.0, vref_ymin + 1.0),
                180.0,
                0.5,
                signal,
            ),
            (
                VSS_SWITCH_INSTANCE_NAME,
                "output",
                "output_E",
                (-5.0, vss_ymax - 1.0),
                180.0,
                0.5,
                second_output_layer or signal,
            ),
            (
                VREF_SWITCH_INSTANCE_NAME,
                "control",
                "control_W",
                (-4.0, 6.0),
                180.0,
                0.5,
                signal,
            ),
            (
                VSS_SWITCH_INSTANCE_NAME,
                "control_bar",
                "control_bar_E",
                (-4.0, -6.0),
                180.0,
                0.5,
                signal,
            ),
            (
                VREF_SWITCH_INSTANCE_NAME,
                "control_bar",
                "control_bar_E",
                (select_bar_x, 6.0),
                0.0,
                0.5,
                signal,
            ),
            (
                VSS_SWITCH_INSTANCE_NAME,
                "control",
                "control_W",
                (4.0, -6.0),
                0.0,
                0.5,
                signal,
            ),
            (
                VREF_SWITCH_INSTANCE_NAME,
                "vss",
                "vss_S",
                (-3.0, vref_ymin + 0.5),
                270.0,
                1.6,
                signal,
            ),
            (
                VSS_SWITCH_INSTANCE_NAME,
                "vss",
                "vss_S",
                (3.0, vss_ymax - 0.5),
                90.0,
                1.8,
                signal,
            ),
            (
                VREF_SWITCH_INSTANCE_NAME,
                "vdd",
                "vdd_S",
                (3.0, vref_ymin + 0.5),
                270.0,
                3.2,
                signal,
            ),
            (
                VSS_SWITCH_INSTANCE_NAME,
                "vdd",
                "vdd_S",
                (-3.0, vss_ymax - 0.5),
                90.0,
                3.4,
                second_vdd_layer or signal,
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
                bbox=BoundingBox(-5.0, vref_ymin, 5.0, 12.0),
                role="active",
                group="VREF_SWITCH",
                orientation="R0",
                row=0,
                col=0,
            ),
            VSS_SWITCH_INSTANCE_NAME: PlacedInstance(
                instance_name=VSS_SWITCH_INSTANCE_NAME,
                cell_name="vss_tg",
                bbox=BoundingBox(-5.0, -12.0, 5.0, vss_ymax),
                role="active",
                group="VSS_SWITCH",
                orientation="R180",
                row=1,
                col=0,
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
            upper_route_transition=self._transition(),
        )

    def test_default_policy_uses_generic_vertical_oriented_pair(self):
        policy = self._intent().policy
        self.assertEqual(policy.child_axis, "vertical")
        self.assertEqual(policy.vref_child_side, "high")
        self.assertEqual(policy.vref_child_orientation, "R0")
        self.assertEqual(policy.vss_child_orientation, "R180")
        self.assertEqual(policy.upper_route_glayer, "met3")
        self.assertEqual(
            self._intent().vref_switch_policy.input_device_terminal,
            "drain",
        )
        self.assertEqual(
            self._intent().vref_switch_policy.output_device_terminal,
            "source",
        )

    def test_invalid_child_orientation_fails_at_policy_boundary(self):
        with self.assertRaises(ValueError):
            ReferenceSelectorLayoutPolicy(vss_child_orientation="R90")

    def test_empty_upper_route_layer_fails_at_policy_boundary(self):
        with self.assertRaises(ValueError):
            ReferenceSelectorLayoutPolicy(upper_route_glayer="")

    def test_compact_topology_uses_reusable_corridor_plans(self):
        routes = self._plan()

        self.assertEqual(
            routes.common_plan.strategy,
            "transitioned_vertical_trunk_tree",
        )
        self.assertEqual(routes.select_plan.strategy, "external_west_side_bus")
        self.assertEqual(
            routes.select_bar_plan.strategy,
            "external_east_side_bus",
        )
        self.assertEqual(
            routes.vss_plan.strategy,
            "transitioned_vertical_trunk_tree",
        )
        self.assertEqual(routes.vdd_plan.strategy, "vertical_gap_bridge")

        self.assertEqual(routes.common_plan.metrics.via_count, 2)
        self.assertEqual(routes.select_plan.metrics.via_count, 0)
        self.assertEqual(routes.select_bar_plan.metrics.via_count, 0)
        self.assertEqual(routes.vss_plan.metrics.via_count, 3)
        self.assertEqual(routes.vdd_plan.metrics.via_count, 0)
        self.assertEqual(
            routes.select_plan.metrics.total_length,
            routes.select_bar_plan.metrics.total_length,
        )
        self.assertEqual(routes.select_plan.metrics.total_length, 18.5)
        self.assertEqual(routes.select_plan.metrics.bend_count, 2)
        self.assertEqual(routes.select_bar_plan.metrics.bend_count, 2)

        self.assertEqual(
            routes.common_plan.selected_access_point_names,
            (
                f"{VREF_SWITCH_INSTANCE_NAME}__output_W",
                f"{VSS_SWITCH_INSTANCE_NAME}__output_E",
            ),
        )
        self.assertEqual(
            routes.vss_plan.selected_access_point_names,
            (
                f"{VREF_SWITCH_INSTANCE_NAME}__vss_S",
                f"{VSS_SWITCH_INSTANCE_NAME}__vss_S",
                f"{VSS_SWITCH_INSTANCE_NAME}__input_W",
            ),
        )
        self.assertEqual(
            {segment.layer for segment in routes.common_plan.segments},
            {self.signal_layer, self.upper_layer},
        )
        self.assertEqual(
            {segment.layer for segment in routes.vss_plan.segments},
            {self.signal_layer, self.upper_layer},
        )
        self.assertEqual(
            {segment.layer for segment in routes.vdd_plan.segments},
            {self.signal_layer},
        )

    def test_runtime_child_envelopes_drive_gap_and_side_channels(self):
        routes = self._plan(vref_ymin=4.0, vss_ymax=-4.0)
        vdd_horizontal = tuple(
            segment
            for segment in routes.vdd_plan.segments
            if segment.orientation == "horizontal"
        )
        self.assertEqual(len(vdd_horizontal), 1)
        self.assertEqual(vdd_horizontal[0].start[1], 0.0)
        self.assertEqual(routes.select_plan.segments[1].start[0], -7.25)
        self.assertEqual(routes.select_bar_plan.segments[1].start[0], 7.25)

    def test_explicit_widths_are_semantic_policy(self):
        routes = plan_reference_selector_topology(
            intent=self._intent(route_width=0.7, supply_route_width=0.9),
            physical_design=self._snapshot(),
            upper_route_transition=self._transition(),
        )
        self.assertEqual(routes.common_plan.metrics.resolved_width, 0.7)
        self.assertEqual(routes.select_plan.metrics.resolved_width, 0.7)
        self.assertEqual(routes.vss_plan.metrics.resolved_width, 0.9)
        self.assertEqual(routes.vdd_plan.metrics.resolved_width, 0.9)

    def test_unsupported_pair_orientation_fails_explicitly(self):
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(child_axis="horizontal"),
                physical_design=self._snapshot(),
                upper_route_transition=self._transition(),
            )
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(vref_child_side="low"),
                physical_design=self._snapshot(),
                upper_route_transition=self._transition(),
            )

    def test_overlapping_or_reversed_children_fail_explicitly(self):
        with self.assertRaises(RuntimeError):
            self._plan(vref_ymin=-1.0, vss_ymax=1.0)

    def test_common_transition_must_match_access_layer(self):
        with self.assertRaises(RuntimeError):
            self._plan(second_output_layer=(100, 0))
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(),
                physical_design=self._snapshot(),
                upper_route_transition=self._transition(source_layer=(100, 0)),
            )

    def test_gap_must_clear_supply_vias_from_vdd_route(self):
        with self.assertRaises(RuntimeError):
            plan_reference_selector_topology(
                intent=self._intent(),
                physical_design=self._snapshot(),
                upper_route_transition=self._transition(via_size=(0.8, 3.0)),
            )

    def test_control_asymmetry_fails_before_geometry_execution(self):
        with self.assertRaises(RuntimeError):
            self._plan(select_bar_x=3.0)

    def test_vdd_gap_accesses_must_share_layer(self):
        with self.assertRaises(RuntimeError):
            self._plan(second_vdd_layer=(100, 0))


if __name__ == "__main__":
    unittest.main()
