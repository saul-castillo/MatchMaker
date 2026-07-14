from dataclasses import dataclass
from pathlib import Path

from matchmaker.outputs.core_analog_cell_paths import (
    CoreAnalogCellPaths,
    create_core_analog_cell_paths,
)
from matchmaker.verification.drc.magic_drc import (
    MagicDrcConfig,
    MagicDrcResult,
    run_magic_drc,
)
from matchmaker.verification.extraction.magic_extraction import (
    MagicExtractionConfig,
    MagicExtractionResult,
    run_magic_extraction,
)
from matchmaker.verification.netlist.connectivity_assertions import (
    SharedNetConnectivityExpectation,
    SharedNetConnectivityResult,
    evaluate_extracted_shared_net_connectivity,
)


@dataclass(frozen=True)
class GeneratedCellVerificationResult:
    """Pre-LVS verification result for DRC, extraction, and connectivity."""

    passed: bool
    paths: CoreAnalogCellPaths
    drc: MagicDrcResult
    extraction: MagicExtractionResult | None
    connectivity: SharedNetConnectivityResult | None


def verify_generated_cell(
    designs_root: Path,
    cell_name: str,
    drc_config: MagicDrcConfig | None = None,
    extraction_config: MagicExtractionConfig | None = None,
    run_extraction: bool = True,
    connectivity_expectation: SharedNetConnectivityExpectation | None = None,
) -> GeneratedCellVerificationResult:
    """Run standard pre-LVS checks for one generated core_analog cell."""
    if connectivity_expectation is not None and not run_extraction:
        raise ValueError(
            "connectivity_expectation requires run_extraction=True"
        )

    paths = create_core_analog_cell_paths(
        designs_root=Path(designs_root),
        cell_name=cell_name,
    )

    drc_result = run_magic_drc(
        gds_path=paths.final_gds,
        cell_name=cell_name,
        report_path=paths.drc_report,
        config=drc_config,
    )

    extraction_result = None
    connectivity_result = None
    if run_extraction:
        extraction_result = run_magic_extraction(
            gds_path=paths.final_gds,
            cell_name=cell_name,
            output_netlist_path=paths.extracted_netlist,
            config=extraction_config,
        )
        report_header = (
            f"passed: {extraction_result.passed}\n"
            f"failure_reason: {extraction_result.failure_reason}\n"
            f"netlist: {extraction_result.netlist_path}\n\n"
        )
        paths.extraction_report.write_text(
            report_header + extraction_result.process.combined_output + "\n"
        )

        if connectivity_expectation is not None and extraction_result.passed:
            connectivity_result = evaluate_extracted_shared_net_connectivity(
                netlist_path=paths.extracted_netlist,
                top_cell_name=cell_name,
                expectation=connectivity_expectation,
            )
            paths.connectivity_report.write_text(connectivity_result.render())

    passed = drc_result.passed and (
        extraction_result is None or extraction_result.passed
    )
    if connectivity_expectation is not None:
        passed = passed and (
            connectivity_result is not None and connectivity_result.passed
        )

    return GeneratedCellVerificationResult(
        passed=passed,
        paths=paths,
        drc=drc_result,
        extraction=extraction_result,
        connectivity=connectivity_result,
    )
