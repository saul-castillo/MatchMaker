from dataclasses import dataclass
from pathlib import Path
import re

from matchmaker.verification.process_runner import ProcessResult, run_process


_DRC_COUNT_PATTERN = re.compile(
    r"(?:MATCHMAKER_DRC_COUNT=|Total DRC errors found:\s*)(\d+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class MagicDrcConfig:
    magic_bin: str = "magic"
    tech_name: str | None = None
    startup_file: Path | None = None
    timeout_s: float = 300.0


@dataclass(frozen=True)
class MagicDrcResult:
    passed: bool
    violation_count: int | None
    report_path: Path
    process: ProcessResult


def _magic_drc_tcl(gds_path: Path, cell_name: str, tech_name: str | None) -> str:
    commands = []
    if tech_name is not None:
        commands.append(f"tech load {tech_name}")

    commands.extend(
        [
            f"gds read {gds_path}",
            f"load {cell_name}",
            "select top cell",
            "drc catchup",
            # Magic prints the numeric result to stdout; it does not return the
            # count as the Tcl command value.
            "drc count total",
            'puts "MATCHMAKER_DRC_COMPLETED=1"',
            "quit -noprompt",
        ]
    )
    return "\n".join(commands) + "\n"


def _parse_drc_count(output: str) -> int | None:
    matches = _DRC_COUNT_PATTERN.findall(output)
    if not matches:
        return None
    return int(matches[-1])


def _magic_loaded_target_cell(output: str, cell_name: str) -> bool:
    if f'Reading "{cell_name}".' not in output:
        return False

    fatal_fragments = (
        "Don't know how to read GDS-II",
        f"Cell {cell_name} couldn't be read",
        'Using technology "minimum"',
    )
    return not any(fragment in output for fragment in fatal_fragments)


def run_magic_drc(
    gds_path: Path,
    cell_name: str,
    report_path: Path,
    config: MagicDrcConfig | None = None,
) -> MagicDrcResult:
    config = config or MagicDrcConfig()
    gds_path = gds_path.resolve()
    report_path = report_path.resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)

    if not gds_path.is_file():
        raise FileNotFoundError(f"GDS file not found: {gds_path}")

    argv = [config.magic_bin, "-dnull", "-noconsole"]
    if config.startup_file is not None:
        argv.extend(["-r", str(config.startup_file.resolve())])

    process = run_process(
        argv=argv,
        cwd=gds_path.parent,
        timeout_s=config.timeout_s,
        input_text=_magic_drc_tcl(
            gds_path=gds_path,
            cell_name=cell_name,
            tech_name=config.tech_name,
        ),
    )
    report_path.write_text(process.combined_output + "\n")

    violation_count = _parse_drc_count(process.combined_output)
    passed = (
        process.returncode == 0
        and violation_count == 0
        and _magic_loaded_target_cell(process.combined_output, cell_name)
    )

    return MagicDrcResult(
        passed=passed,
        violation_count=violation_count,
        report_path=report_path,
        process=process,
    )
