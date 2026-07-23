import unittest
from dataclasses import dataclass

from matchmaker.physical.hierarchical_cell_snapshot import (
    CellFamilyAccessContract,
    create_hierarchical_cell_snapshot,
)
from matchmaker.physical.models import TerminalRef
from matchmaker.placement.core.placement_result import (
    PlacedReferenceBinding,
    PlacementResult,
)
from matchmaker.placement.core.tile_plan import PlacementPlan, Tile


@dataclass
class _Port:
    name: str
    center: tuple[float, float]
    orientation: float
    width: float
    layer: tuple[int, int]


class _Reference:
    def __init__(self, ports):
        self._ports = tuple(ports)
        self.bbox = ((-2.0, -1.0), (2.0, 1.0))

    def get_ports_list(self):
        return self._ports


class _Component:
    def __init__(self):
        self.ports = {}

    def add_ports(self, ports, *, prefix):
        for port in ports:
            promoted = _Port(
                name=f"{prefix}{port.name}",
                center=port.center,
                orientation=port.orientation,
                width=port.width,
                layer=port.layer,
            )
            self.ports[promoted.name] = promoted


def _placement(reference) -> PlacementResult:
    component = _Component()
    plan = PlacementPlan(
        cell_name="pair",
        rows=1,
        cols=1,
        tiles=(
            Tile(
                name="R0",
                group="RESISTOR",
                row=0,
                col=0,
                orientation="R0",
            ),
        ),
    )
    return PlacementResult(
        component=component,
        plan=plan,
        bindings={
            "R0": PlacedReferenceBinding(
                instance_name="R0",
                cell_name="resistor",
                reference=reference,
                row=0,
                col=0,
                orientation="R0",
                role="active",
                group="RESISTOR",
            )
        },
    )


def _resistor_classifier(name: str):
    if name == "positive_E":
        return "positive", "E"
    if name == "negative_W":
        return "negative", "W"
    return None


class HierarchicalCellSnapshotTests(unittest.TestCase):
    def test_family_contract_adapts_arbitrary_terminal_grammar(self):
        snapshot = create_hierarchical_cell_snapshot(
            _placement(
                _Reference(
                    (
                        _Port("positive_E", (2.0, 0.0), 0.0, 0.6, (10, 0)),
                        _Port("negative_W", (-2.0, 0.0), 180.0, 0.7, (10, 0)),
                        _Port("internal_marker", (0.0, 0.0), 90.0, 0.2, (99, 0)),
                    )
                )
            ),
            contract=CellFamilyAccessContract(
                family_name="resistor",
                required_terminals=frozenset({"positive", "negative"}),
                classify_port_name=_resistor_classifier,
            ),
        )
        self.assertEqual(
            tuple(snapshot.access_points),
            ("R0__positive_E", "R0__negative_W"),
        )
        self.assertEqual(
            snapshot.access_points_for(TerminalRef("R0", "positive"))[0].layer,
            (10, 0),
        )
        self.assertEqual(snapshot.instance("R0").bbox.width, 4.0)

    def test_missing_required_family_terminal_fails_explicitly(self):
        with self.assertRaises(RuntimeError):
            create_hierarchical_cell_snapshot(
                _placement(
                    _Reference(
                        (
                            _Port(
                                "positive_E",
                                (2.0, 0.0),
                                0.0,
                                0.6,
                                (10, 0),
                            ),
                        )
                    )
                ),
                contract=CellFamilyAccessContract(
                    family_name="resistor",
                    required_terminals=frozenset({"positive", "negative"}),
                    classify_port_name=_resistor_classifier,
                ),
            )


if __name__ == "__main__":
    unittest.main()
