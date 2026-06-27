from dataclasses import dataclass
from typing import Literal

from matchmaker.specs.mos_device_spec import MosDeviceSpec


MosCentroidPatternStyle = Literal[
    "abba",
    "custom",
]

MosCentroidDummyTileStrategy = Literal[
    "none",
    "center_pair",
]


@dataclass(frozen=True)
class MosCentroidArrayIntent:
    """
    High-level intent for a MOS centroid array.

    This object represents what the caller wants built before the exact
    placement grid is generated.
    """

    cell_name: str
    device_a: MosDeviceSpec
    device_b: MosDeviceSpec
    rows: int
    cols: int
    pattern_style: MosCentroidPatternStyle = "abba"
    dummy_tile_strategy: MosCentroidDummyTileStrategy = "none"


def validate_mos_centroid_array_intent(
    intent: MosCentroidArrayIntent,
) -> None:
    if intent.rows <= 0 or intent.cols <= 0:
        raise ValueError("MOS centroid intent rows and cols must be positive")

    if intent.device_a.kind != intent.device_b.kind:
        raise ValueError(
            "MOS centroid intent requires device_a and device_b to have the same MOS kind"
        )

    if intent.pattern_style == "abba" and intent.cols % 2 != 0:
        raise ValueError("ABBA pattern requires an even number of columns")

    if intent.dummy_tile_strategy == "center_pair" and intent.cols < 4:
        raise ValueError("center_pair dummy strategy requires at least 4 columns")