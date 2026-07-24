from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from matchmaker.outputs.cdac_demo_cell_names import (
    GF180_CDAC_B0_REFERENCE_SELECTOR_DEMO_CELL_NAME,
    GF180_CDAC_BASE_TRANSMISSION_GATE_DEMO_CELL_NAME,
)


CdacLeafTargetName = Literal["transmission_gate", "reference_selector"]


@dataclass(frozen=True)
class CdacLeafLvsTarget:
    name: CdacLeafTargetName
    layout_cell_name: str
    schematic_cell_name: str
    schematic_path: Path

    @property
    def reference_netlist_filename(self) -> str:
        return f"{self.schematic_cell_name}_lvs_reference.spice"


def make_gf180_cdac_leaf_lvs_targets(
    designs_root: Path,
) -> tuple[CdacLeafLvsTarget, ...]:
    """Return the reviewed base-TG and B0 selector LVS target preset."""

    library_root = designs_root / "libs" / "core_matchmaker"
    return (
        CdacLeafLvsTarget(
            name="transmission_gate",
            layout_cell_name=(
                GF180_CDAC_BASE_TRANSMISSION_GATE_DEMO_CELL_NAME
            ),
            schematic_cell_name="7D_tg_switch",
            schematic_path=(
                library_root / "7D_tg_switch" / "7D_tg_switch.sch"
            ),
        ),
        CdacLeafLvsTarget(
            name="reference_selector",
            layout_cell_name=(
                GF180_CDAC_B0_REFERENCE_SELECTOR_DEMO_CELL_NAME
            ),
            schematic_cell_name="7D_ref_sel_2to1",
            schematic_path=(
                library_root / "7D_ref_sel_2to1" / "7D_ref_sel_2to1.sch"
            ),
        ),
    )
