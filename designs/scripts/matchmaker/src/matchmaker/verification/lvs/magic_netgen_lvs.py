from dataclasses import dataclass
from pathlib import Path

from matchmaker.verification.process_runner import ProcessResult, run_process


@dataclass(frozen=True)
class MagicNetgenLvsConfig:
    netgen_setup_file: Path
    magic_bin: str = "magic"
    netgen_bin: str = "netgen"
    magic_tech_name: str | None = None
    magic_startup_file: Path | None = None
    extraction_timeout_s: float = 300.0
    lvs_timeout_s: float = 300.0


@dataclass(frozen=True)
class MagicNetgenLvsResult:
    passed: bool
    layout_netlist_path: Path
    report_path: Path
    extraction_process: ProcessResult
    lvs_process: ProcessResult | None


def _magic_extract_lvs_tcl(
    gds_path: Path,
    cell_name: str,
    output_netlist_path: Path,
    tech_name: str | None,
) -> str:
    commands = []
    if tech_name is not None:
        commands.append(f"tech load {tech_name}")

    commands.extend(
        [
            f"gds read {gds_path}",
            f"load {cell_name}",
            "select top cell",
            "extract all",
            "ext2spice lvs",
            f"ext2spice -o {output_netlist_path} -f ngspice",
            "quit -noprompt",
        ]
    )
    return "\n".join(commands) + "\n"


def _netgen_output_passed(output: str) -> bool:
    return (
        "Circuits match uniquely." in output
        and "Property errors were found." not in output
        and "Netlists do not match." not in output
        and "Circuits match uniquely with port errors." not in output
    )


def run_magic_netgen_lvs(
    gds_path: Path,
    schematic_netlist_path: Path,
    cell_name: str,
    layout_netlist_path: Path,
    report_path: Path,
    config: MagicNetgenLvsConfig,
) -> MagicNetgenLvsResult:
    gds_path = gds_path.resolve()
    schematic_netlist_path = schematic_netlist_path.resolve()
    layout_netlist_path = layout_netlist_path.resolve()
    report_path = report_path.resolve()
    setup_file = config.netgen_setup_file.resolve()

    for required_path, description in [
        (gds_path, "GDS"),
        (schematic_netlist_path, "schematic netlist"),
        (setup_file, "Netgen setup"),
    ]:
        if not required_path.is_file():
            raise FileNotFoundError(f"{description} file not found: {required_path}")

    layout_netlist_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    magic_argv = [config.magic_bin, "-dnull", "-noconsole"]
    if config.magic_startup_file is not None:
        magic_argv.extend(["-r", str(config.magic_startup_file.resolve())])

    extraction_process = run_process(
        argv=magic_argv,
        cwd=gds_path.parent,
        timeout_s=config.extraction_timeout_s,
        input_text=_magic_extract_lvs_tcl(
            gds_path=gds_path,
            cell_name=cell_name,
            output_netlist_path=layout_netlist_path,
            tech_name=config.magic_tech_name,
        ),
    )

    if extraction_process.returncode != 0 or not layout_netlist_path.is_file():
        report_path.write_text(
            "LAYOUT EXTRACTION FAILED\n\n" + extraction_process.combined_output + "\n"
        )
        return MagicNetgenLvsResult(
            passed=False,
            layout_netlist_path=layout_netlist_path,
            report_path=report_path,
            extraction_process=extraction_process,
            lvs_process=None,
        )

    lvs_process = run_process(
        argv=[
            config.netgen_bin,
            "-batch",
            "lvs",
            f"{schematic_netlist_path} {cell_name}",
            f"{layout_netlist_path} {cell_name}",
            str(setup_file),
        ],
        cwd=report_path.parent,
        timeout_s=config.lvs_timeout_s,
    )

    report_path.write_text(lvs_process.combined_output + "\n")
    passed = lvs_process.returncode == 0 and _netgen_output_passed(
        lvs_process.combined_output
    )

    return MagicNetgenLvsResult(
        passed=passed,
        layout_netlist_path=layout_netlist_path,
        report_path=report_path,
        extraction_process=extraction_process,
        lvs_process=lvs_process,
    )
