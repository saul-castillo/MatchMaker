from dataclasses import dataclass, field
from typing import Literal

from matchmaker.design.circuit_manifest import CircuitManifest
from matchmaker.placement.core.orientation_policy import OrientationPolicy
from matchmaker.specs.banked_cdac_spec import BankedCdacSpec


ResidualPairPolicy = Literal["reject", "pair_compatible"]
SymmetryPolicy = Literal["inversion"]


@dataclass(frozen=True)
class CdacCapacitorArrayIntent:
    """Placement request for the unit-capacitor subset of a banked CDAC."""

    spec: BankedCdacSpec
    manifest: CircuitManifest
    cell_name: str | None = None
    rows: int | None = None
    cols: int | None = None
    symmetry_policy: SymmetryPolicy = "inversion"
    residual_pair_policy: ResidualPairPolicy = "pair_compatible"
    orientation_policy: OrientationPolicy = field(
        default_factory=lambda: OrientationPolicy(kind="all_r0")
    )

    def __post_init__(self) -> None:
        if self.manifest.cell_name != self.spec.cell_name:
            raise ValueError(
                "CDAC capacitor intent manifest/spec cell names must match"
            )
        if self.cell_name is not None and not self.cell_name:
            raise ValueError("CDAC capacitor-array cell_name must be non-empty")
        if self.rows is not None and self.rows <= 0:
            raise ValueError("CDAC capacitor-array rows must be positive")
        if self.cols is not None and self.cols <= 0:
            raise ValueError("CDAC capacitor-array cols must be positive")

    @property
    def resolved_cell_name(self) -> str:
        return self.cell_name or f"{self.spec.cell_name}_capacitor_array"
