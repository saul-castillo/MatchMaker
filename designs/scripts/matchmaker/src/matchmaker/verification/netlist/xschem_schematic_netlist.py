from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from matchmaker.verification.process_runner import ProcessResult, run_process


@dataclass(frozen=True)
class XschemNetlistConfig:
    xschem_bin: str = "xschem"
    rcfile: Path | None = None
    pdk_name: str = "gf180mcuD"
    pdk_root: Path = Path("/foss/pdks")
    environment: Mapping[str, str] | None = None
    timeout_s: float = 120.0


@dataclass(frozen=True)
class XschemNetlistResult:
    passed: bool
    netlist_path: Path
    process: ProcessResult
    failure_reason: str | None = None


def _build_xschem_netlist_argv(
    *,
    xschem_bin: str,
    schematic_path: Path,
    netlist_path: Path,
    rcfile: Path,
) -> tuple[str, ...]:
    return (
        xschem_bin,
        "-q",
        "-x",
        "-n",
        "-s",
        "--rcfile",
        str(rcfile),
        "--tcl",
        "set lvs_netlist 1",
        "--netlist_path",
        str(netlist_path.parent),
        "--netlist_filename",
        netlist_path.name,
        str(schematic_path),
    )


def _build_xschem_environment(
    *,
    designs_root: Path,
    pdk_name: str,
    pdk_root: Path,
    extra_env: Mapping[str, str] | None,
) -> dict[str, str]:
    environment = {
        "DESIGNS": str(designs_root),
        "PDK": pdk_name,
        "PDK_ROOT": str(pdk_root),
    }
    if extra_env is not None:
        environment.update(extra_env)
    return environment


def _contains_subcircuit(netlist_text: str, cell_name: str) -> bool:
    expected = f".subckt {cell_name}".lower()
    return any(
        line.strip().lower().startswith(expected)
        for line in netlist_text.splitlines()
    )


def run_xschem_schematic_netlist(
    *,
    schematic_path: Path,
    schematic_cell_name: str,
    output_netlist_path: Path,
    designs_root: Path,
    config: XschemNetlistConfig | None = None,
) -> XschemNetlistResult:
    """Export one independent Xschem reference schematic as an LVS SPICE netlist."""

    config = config or XschemNetlistConfig()
    schematic_path = schematic_path.resolve()
    output_netlist_path = output_netlist_path.resolve()
    designs_root = designs_root.resolve()
    rcfile = (
        config.rcfile.resolve()
        if config.rcfile is not None
        else designs_root / ".config" / ".xschem" / "xschemrc"
    )

    for required_path, description in (
        (schematic_path, "schematic"),
        (rcfile, "Xschem rcfile"),
    ):
        if not required_path.is_file():
            raise FileNotFoundError(f"{description} file not found: {required_path}")

    output_netlist_path.parent.mkdir(parents=True, exist_ok=True)
    if output_netlist_path.exists():
        output_netlist_path.unlink()

    process = run_process(
        argv=_build_xschem_netlist_argv(
            xschem_bin=config.xschem_bin,
            schematic_path=schematic_path,
            netlist_path=output_netlist_path,
            rcfile=rcfile,
        ),
        cwd=schematic_path.parent,
        timeout_s=config.timeout_s,
        env=_build_xschem_environment(
            designs_root=designs_root,
            pdk_name=config.pdk_name,
            pdk_root=config.pdk_root,
            extra_env=config.environment,
        ),
    )

    if process.returncode != 0:
        return XschemNetlistResult(
            passed=False,
            netlist_path=output_netlist_path,
            process=process,
            failure_reason=f"Xschem exited with status {process.returncode}",
        )
    if not output_netlist_path.is_file():
        return XschemNetlistResult(
            passed=False,
            netlist_path=output_netlist_path,
            process=process,
            failure_reason="Xschem did not create the requested netlist",
        )

    netlist_text = output_netlist_path.read_text(errors="replace")
    if not _contains_subcircuit(netlist_text, schematic_cell_name):
        return XschemNetlistResult(
            passed=False,
            netlist_path=output_netlist_path,
            process=process,
            failure_reason=(
                "generated netlist does not contain expected subcircuit "
                f"{schematic_cell_name!r}"
            ),
        )

    return XschemNetlistResult(
        passed=True,
        netlist_path=output_netlist_path,
        process=process,
    )
