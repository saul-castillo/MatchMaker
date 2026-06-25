from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CoreAnalogCellPaths:
    """
    Standard output paths for a generated analog cell.

    Convention:
        /foss/designs/libs/core_analog/<cell_name>/
            gds/
            netlist/
            reports/drc/
            reports/lvs/
    """

    cell_name: str
    cell_dir: Path
    gds_dir: Path
    netlist_dir: Path
    reports_dir: Path
    drc_reports_dir: Path
    lvs_reports_dir: Path
    final_gds: Path
    reference_netlist: Path
    drc_report: Path
    lvs_output_dir: Path


def create_core_analog_cell_paths(
    designs_root: Path,
    cell_name: str,
    create_directories: bool = True,
) -> CoreAnalogCellPaths:
    cell_dir = designs_root / "libs" / "core_analog" / cell_name

    gds_dir = cell_dir / "gds"
    netlist_dir = cell_dir / "netlist"
    reports_dir = cell_dir / "reports"
    drc_reports_dir = reports_dir / "drc"
    lvs_reports_dir = reports_dir / "lvs"

    if create_directories:
        for directory in (
            gds_dir,
            netlist_dir,
            drc_reports_dir,
            lvs_reports_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    return CoreAnalogCellPaths(
        cell_name=cell_name,
        cell_dir=cell_dir,
        gds_dir=gds_dir,
        netlist_dir=netlist_dir,
        reports_dir=reports_dir,
        drc_reports_dir=drc_reports_dir,
        lvs_reports_dir=lvs_reports_dir,
        final_gds=gds_dir / f"{cell_name}.gds",
        reference_netlist=netlist_dir / f"{cell_name}_ref_flat.spice",
        drc_report=drc_reports_dir / f"{cell_name}_drc.lyrdb",
        lvs_output_dir=lvs_reports_dir / f"{cell_name}_lvs_result",
    )