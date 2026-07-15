from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from matchmaker.verification.magic_support import (
    build_magic_argv,
    build_magic_environment,
    magic_loaded_target_cell,
)
from matchmaker.verification.process_runner import ProcessResult, run_process


@dataclass(frozen=True)
class MagicExtractionConfig:
    magic_bin: str = "magic"
    tech_name: str | None = None
    startup_file: Path | None = None
    pdk_name: str | None = "gf180mcuD"
    pdk_root: Path | None = Path("/foss/pdks")
    environment: Mapping[str, str] | None = None
    timeout_s: float = 300.0


@dataclass(frozen=True)
class MagicExtractionResult:
    passed: bool
    netlist_path: Path
    process: ProcessResult
    failure_reason: str | None = None


def _tcl_path(path: Path) -> str:
    return "{" + str(path) + "}"


def _magic_extract_tcl(
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
            f"gds read {_tcl_path(gds_path)}",
            f"load {cell_name}",
            "select top cell",
            "extract all",
            "ext2spice lvs",
            f"ext2spice -o {_tcl_path(output_netlist_path)} -f ngspice",
            'puts "MATCHMAKER_EXTRACTION_COMPLETED=1"',
            "quit -noprompt",
        ]
    )
    return "\n".join(commands) + "\n"


def _extraction_failure_reason(
    process: ProcessResult,
    output_netlist_path: Path,
    cell_name: str,
) -> str | None:
    output = process.combined_output

    if process.returncode != 0:
        return f"Magic exited with return code {process.returncode}"
    if not magic_loaded_target_cell(output, cell_name):
        return f"Magic did not successfully load target cell {cell_name!r}"
    if "MATCHMAKER_EXTRACTION_COMPLETED=1" not in output:
        return "Magic did not emit the extraction completion marker"
    if not output_netlist_path.is_file():
        return f"Magic did not create layout netlist: {output_netlist_path}"
    if output_netlist_path.stat().st_size == 0:
        return f"Magic created an empty layout netlist: {output_netlist_path}"
    return None


def run_magic_extraction(
    gds_path: Path,
    cell_name: str,
    output_netlist_path: Path,
    config: MagicExtractionConfig | None = None,
) -> MagicExtractionResult:
    """Extract one GDS top cell to an ngspice-compatible LVS netlist."""
    config = config or MagicExtractionConfig()
    gds_path = gds_path.resolve()
    output_netlist_path = output_netlist_path.resolve()

    if not gds_path.is_file():
        raise FileNotFoundError(f"GDS file not found: {gds_path}")

    output_netlist_path.parent.mkdir(parents=True, exist_ok=True)
    if output_netlist_path.exists():
        output_netlist_path.unlink()

    process = run_process(
        argv=build_magic_argv(
            magic_bin=config.magic_bin,
            startup_file=config.startup_file,
        ),
        cwd=output_netlist_path.parent,
        timeout_s=config.timeout_s,
        input_text=_magic_extract_tcl(
            gds_path=gds_path,
            cell_name=cell_name,
            output_netlist_path=output_netlist_path,
            tech_name=config.tech_name,
        ),
        env=build_magic_environment(
            pdk_name=config.pdk_name,
            pdk_root=config.pdk_root,
            extra_env=config.environment,
        ),
    )

    failure_reason = _extraction_failure_reason(
        process=process,
        output_netlist_path=output_netlist_path,
        cell_name=cell_name,
    )
    return MagicExtractionResult(
        passed=failure_reason is None,
        netlist_path=output_netlist_path,
        process=process,
        failure_reason=failure_reason,
    )
