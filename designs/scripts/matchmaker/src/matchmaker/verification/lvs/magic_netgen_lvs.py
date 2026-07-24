from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from matchmaker.verification.extraction.magic_extraction import (
    MagicExtractionConfig,
    run_magic_extraction,
)
from matchmaker.verification.magic_support import (
    build_magic_environment,
    resolve_netgen_setup_file,
)
from matchmaker.verification.process_runner import ProcessResult, run_process


@dataclass(frozen=True)
class MagicNetgenLvsConfig:
    netgen_setup_file: Path | None = None
    magic_bin: str = "magic"
    netgen_bin: str = "netgen"
    magic_tech_name: str | None = None
    magic_startup_file: Path | None = None
    pdk_name: str = "gf180mcuD"
    pdk_root: Path = Path("/foss/pdks")
    environment: Mapping[str, str] | None = None
    extraction_timeout_s: float = 300.0
    lvs_timeout_s: float = 300.0


@dataclass(frozen=True)
class MagicNetgenLvsResult:
    passed: bool
    layout_netlist_path: Path
    report_path: Path
    extraction_process: ProcessResult
    lvs_process: ProcessResult | None
    failure_reason: str | None = None


def _netgen_output_passed(output: str) -> bool:
    return (
        "Circuits match uniquely." in output
        and "Property errors were found." not in output
        and "Netlists do not match." not in output
        and "Circuits match uniquely with port errors." not in output
    )


def _build_netgen_lvs_argv(
    *,
    netgen_bin: str,
    schematic_netlist_path: Path,
    schematic_cell_name: str,
    layout_netlist_path: Path,
    layout_cell_name: str,
    setup_file: Path,
) -> tuple[str, ...]:
    return (
        netgen_bin,
        "-batch",
        "lvs",
        f"{schematic_netlist_path} {schematic_cell_name}",
        f"{layout_netlist_path} {layout_cell_name}",
        str(setup_file),
    )


def run_magic_netgen_lvs(
    gds_path: Path,
    schematic_netlist_path: Path,
    cell_name: str,
    layout_netlist_path: Path,
    report_path: Path,
    config: MagicNetgenLvsConfig | None = None,
    *,
    schematic_cell_name: str | None = None,
) -> MagicNetgenLvsResult:
    """Extract a layout and compare it against a schematic netlist with Netgen.

    ``cell_name`` is the generated layout top cell. ``schematic_cell_name`` may
    differ because independent hand-authored references use stable review-library
    names rather than generated artifact names.
    """

    config = config or MagicNetgenLvsConfig()
    gds_path = gds_path.resolve()
    schematic_netlist_path = schematic_netlist_path.resolve()
    layout_netlist_path = layout_netlist_path.resolve()
    report_path = report_path.resolve()
    schematic_cell_name = schematic_cell_name or cell_name

    for required_path, description in [
        (gds_path, "GDS"),
        (schematic_netlist_path, "schematic netlist"),
    ]:
        if not required_path.is_file():
            raise FileNotFoundError(f"{description} file not found: {required_path}")

    setup_file = resolve_netgen_setup_file(
        explicit_path=config.netgen_setup_file,
        pdk_name=config.pdk_name,
        pdk_root=config.pdk_root,
    )

    layout_netlist_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    extraction = run_magic_extraction(
        gds_path=gds_path,
        cell_name=cell_name,
        output_netlist_path=layout_netlist_path,
        config=MagicExtractionConfig(
            magic_bin=config.magic_bin,
            tech_name=config.magic_tech_name,
            startup_file=config.magic_startup_file,
            pdk_name=config.pdk_name,
            pdk_root=config.pdk_root,
            environment=config.environment,
            timeout_s=config.extraction_timeout_s,
        ),
    )

    if not extraction.passed:
        failure_reason = extraction.failure_reason or "layout extraction failed"
        report_path.write_text(
            "LAYOUT EXTRACTION FAILED\n"
            f"Reason: {failure_reason}\n\n"
            + extraction.process.combined_output
            + "\n"
        )
        return MagicNetgenLvsResult(
            passed=False,
            layout_netlist_path=layout_netlist_path,
            report_path=report_path,
            extraction_process=extraction.process,
            lvs_process=None,
            failure_reason=failure_reason,
        )

    lvs_process = run_process(
        argv=_build_netgen_lvs_argv(
            netgen_bin=config.netgen_bin,
            schematic_netlist_path=schematic_netlist_path,
            schematic_cell_name=schematic_cell_name,
            layout_netlist_path=layout_netlist_path,
            layout_cell_name=cell_name,
            setup_file=setup_file,
        ),
        cwd=report_path.parent,
        timeout_s=config.lvs_timeout_s,
        env=build_magic_environment(
            pdk_name=config.pdk_name,
            pdk_root=config.pdk_root,
            extra_env=config.environment,
        ),
    )

    passed = lvs_process.returncode == 0 and _netgen_output_passed(
        lvs_process.combined_output
    )
    failure_reason = (
        None
        if passed
        else "Netgen did not report an unqualified unique match"
    )

    report_path.write_text(
        "LVS TARGETS\n"
        "===========\n"
        f"schematic: {schematic_netlist_path} {schematic_cell_name}\n"
        f"layout: {layout_netlist_path} {cell_name}\n\n"
        "MAGIC EXTRACTION OUTPUT\n"
        "=======================\n"
        + extraction.process.combined_output
        + "\n\nNETGEN LVS OUTPUT\n"
        "=================\n"
        + lvs_process.combined_output
        + "\n"
    )

    return MagicNetgenLvsResult(
        passed=passed,
        layout_netlist_path=layout_netlist_path,
        report_path=report_path,
        extraction_process=extraction.process,
        lvs_process=lvs_process,
        failure_reason=failure_reason,
    )
