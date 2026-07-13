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


@dataclass(frozen=True)
class GeneratedCellVerificationResult:
    passed: bool
    paths: CoreAnalogCellPaths
    drc: MagicDrcResult
    extraction: MagicExtractionResult | None


def verify_generated_cell(
    designs_root: Path,
    cell_name: str,
    drc_config: MagicDrcConfig | None = None,
    extraction_config: MagicExtractionConfig | None = None,
    run_extraction: bool = True,
) -> GeneratedCellVerificationResult:
    """Run standard DRC and optional extraction for one generated core_analog cell."""
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

    passed = drc_result.passed and (
        extraction_result is None or extraction_result.passed
    )
    return GeneratedCellVerificationResult(
        passed=passed,
        paths=paths,
        drc=drc_result,
        extraction=extraction_result,
    )
