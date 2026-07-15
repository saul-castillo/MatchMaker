"""Public verification entry points for generated MatchMaker cells."""

from matchmaker.verification.generated_cell_verifier import (
    GeneratedCellVerificationResult,
    verify_generated_cell,
)

__all__ = [
    "GeneratedCellVerificationResult",
    "verify_generated_cell",
]
