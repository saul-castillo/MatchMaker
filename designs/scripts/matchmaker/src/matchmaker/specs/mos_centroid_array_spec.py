from dataclasses import dataclass

from .mos_device_spec import MosDeviceSpec


@dataclass(frozen=True)
class MosCentroidArraySpec:
    """
    Concrete MOS centroid array specification.

    This is lower-level than intent. It describes the resolved cell name,
    device groups, and array dimensions used by placement.
    """

    cell_name: str
    device_a: MosDeviceSpec
    device_b: MosDeviceSpec
    rows: int
    cols: int
    pattern: str = "custom"

    def __post_init__(self) -> None:
        if not self.cell_name:
            raise ValueError("MOS centroid array cell_name must be non-empty")

        if self.rows <= 0 or self.cols <= 0:
            raise ValueError("MOS centroid array rows and cols must be positive")

        if self.device_a.kind != self.device_b.kind:
            raise ValueError(
                "MOS centroid array requires device_a and device_b to have the same kind"
            )