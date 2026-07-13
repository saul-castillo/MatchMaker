from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CoreAnalogCellPaths:
    """
    Generated artifact paths for one core_analog cell.
    """

    cell_name: str
    cell_dir: Path
    gds_dir: Path
    netlist_dir: Path
    drc_report_dir: Path
    extraction_report_dir: Path
    lvs_report_dir: Path
    final_gds: Path
    extracted_netlist: Path
    drc_report: Path
    extraction_report: Path
    lvs_report: Path


def create_core_analog_cell_paths(
    designs_root: Path,
    cell_name: str,
) -> CoreAnalogCellPaths:
    """
    Create the standard generated-cell directory structure under:

        designs/libs/core_analog/<cell_name>/
    """
    cell_dir = designs_root / "libs" / "core_analog" / cell_name
    gds_dir = cell_dir / "gds"
    netlist_dir = cell_dir / "netlist"
    drc_report_dir = cell_dir / "reports" / "drc"
    extraction_report_dir = cell_dir / "reports" / "extraction"
    lvs_report_dir = cell_dir / "reports" / "lvs"

    for path in [
        gds_dir,
        netlist_dir,
        drc_report_dir,
        extraction_report_dir,
        lvs_report_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)

    return CoreAnalogCellPaths(
        cell_name=cell_name,
        cell_dir=cell_dir,
        gds_dir=gds_dir,
        netlist_dir=netlist_dir,
        drc_report_dir=drc_report_dir,
        extraction_report_dir=extraction_report_dir,
        lvs_report_dir=lvs_report_dir,
        final_gds=gds_dir / f"{cell_name}.gds",
        extracted_netlist=netlist_dir / f"{cell_name}.spice",
        drc_report=drc_report_dir / f"{cell_name}_drc.rpt",
        extraction_report=extraction_report_dir / f"{cell_name}_extraction.rpt",
        lvs_report=lvs_report_dir / f"{cell_name}_lvs.rpt",
    )
