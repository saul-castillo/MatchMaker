from types import SimpleNamespace
import unittest

from matchmaker.routing.planners.orthogonal_access_detour import (
    choose_orthogonal_access_detour,
)


class OrthogonalAccessDetourTests(unittest.TestCase):
    def setUp(self):
        self.requested_source = SimpleNamespace(center=(0.0, 0.0), orientation=0.0)
        self.requested_target = SimpleNamespace(center=(10.0, 0.0), orientation=0.0)
        self.ports = {
            "A0__gate_N": SimpleNamespace(center=(0.0, 2.0), orientation=90.0),
            "A1__gate_N": SimpleNamespace(center=(10.0, 2.0), orientation=90.0),
            "A0__gate_S": SimpleNamespace(center=(0.0, -2.0), orientation=270.0),
            "A1__gate_S": SimpleNamespace(center=(10.0, -2.0), orientation=270.0),
        }
        self.obstacles = (
            {
                "instance_name": "B0",
                "bbox": ((3.0, -1.0), (5.0, 4.0)),
            },
            {
                "instance_name": "B1",
                "bbox": ((5.0, -1.0), (7.0, 4.0)),
            },
            {
                "instance_name": "LOWER_ROW",
                "bbox": ((3.0, -8.0), (7.0, -4.0)),
            },
        )

    def test_chooses_shorter_north_access_detour(self):
        detour = choose_orthogonal_access_detour(
            ports=self.ports,
            source_instance_name="A0",
            source_port_name="gate_E",
            target_instance_name="A1",
            target_port_name="gate_E",
            source_port=self.requested_source,
            target_port=self.requested_target,
            obstacles=self.obstacles,
            clearance=1.0,
        )

        self.assertEqual(detour.source_top_port_name, "A0__gate_N")
        self.assertEqual(detour.target_top_port_name, "A1__gate_N")
        self.assertEqual(detour.direction, "N")
        self.assertGreaterEqual(detour.extension, 3.0)

    def test_missing_equivalent_cardinal_ports_fails_safe(self):
        with self.assertRaises(RuntimeError):
            choose_orthogonal_access_detour(
                ports={},
                source_instance_name="A0",
                source_port_name="gate_E",
                target_instance_name="A1",
                target_port_name="gate_E",
                source_port=self.requested_source,
                target_port=self.requested_target,
                obstacles=self.obstacles,
            )

    def test_endpoint_obstacles_are_ignored(self):
        detour = choose_orthogonal_access_detour(
            ports=self.ports,
            source_instance_name="A0",
            source_port_name="gate_E",
            target_instance_name="A1",
            target_port_name="gate_E",
            source_port=self.requested_source,
            target_port=self.requested_target,
            obstacles=self.obstacles
            + (
                {
                    "instance_name": "A0",
                    "bbox": ((-1.0, -3.0), (1.0, 3.0)),
                },
                {
                    "instance_name": "A1",
                    "bbox": ((9.0, -3.0), (11.0, 3.0)),
                },
            ),
        )
        self.assertEqual(detour.direction, "N")


if __name__ == "__main__":
    unittest.main()
