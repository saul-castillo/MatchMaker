from dataclasses import dataclass
from pathlib import Path
from typing import Literal


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
            layout_cell_name="gf180_cdac_transmission_gate_demo",
            schematic_cell_name="7D_tg_switch",
            schematic_path=(
                library_root / "7D_tg_switch" / "7D_tg_switch.sch"
            ),
        ),
        CdacLeafLvsTarget(
            name="reference_selector",
            layout_cell_name="gf180_cdac_b0_reference_selector_demo",
            schematic_cell_name="7D_ref_sel_2to1",
            schematic_path=(
                library_root / "7D_ref_sel_2to1" / "7D_ref_sel_2to1.sch"
            ),
        ),
    )
