from dataclasses import dataclass, field
from typing import Literal

from matchmaker.primitives.gf180_mos_primitive_options import (
    Gf180MosPrimitiveOptions,
)
from matchmaker.specs.mos_device_spec import MosDeviceSpec


MosCentroidDummyTileStrategy = Literal[
    "none",
    "center_pair",
]


_PATTERN_STRATEGY_ALIASES = {
    "abba": "mirrored_pair",
    "abba_mirrored": "mirrored_pair",
    "mirrored": "mirrored_pair",
    "mirrored_pair": "mirrored_pair",
    "common_centroid": "common_centroid",
    "common centroid": "common_centroid",
    "centroid": "common_centroid",
    "interdigitated": "interdigitated",
    "abab": "interdigitated",
    "custom": "custom_grid",
    "custom_grid": "custom_grid",
    "explicit_grid": "custom_grid",
    "explicit grid": "custom_grid",
}


@dataclass(frozen=True)
class MosCentroidArrayIntent:
    """
    High-level intent for a MOS centroid array.

    This object represents what the caller wants built before the exact
    placement grid is generated.

    The intent may use either:
        1. A named placement strategy, such as "common_centroid",
           "interdigitated", "mirrored_pair", or legacy alias "abba".
        2. An explicit group_grid with pattern_strategy="custom_grid".
    """

    cell_name: str
    device_a: MosDeviceSpec
    device_b: MosDeviceSpec

    rows: int | None = None
    cols: int | None = None

    pattern_strategy: str = "common_centroid"
    dummy_tile_strategy: MosCentroidDummyTileStrategy = "none"

    group_grid: list[list[str]] | None = None

    primitive_options: Gf180MosPrimitiveOptions = field(
        default_factory=Gf180MosPrimitiveOptions
    )


def normalize_mos_centroid_pattern_strategy(pattern_strategy: str) -> str:
    normalized = pattern_strategy.strip().lower().replace("-", "_")

    if normalized not in _PATTERN_STRATEGY_ALIASES:
        known = ", ".join(sorted(_PATTERN_STRATEGY_ALIASES))
        raise ValueError(
            f"Unknown MOS centroid pattern_strategy {pattern_strategy!r}. "
            f"Known strategies/aliases: {known}"
        )

    return _PATTERN_STRATEGY_ALIASES[normalized]


def infer_grid_shape(group_grid: list[list[str]]) -> tuple[int, int]:
    if not group_grid:
        raise ValueError("group_grid must contain at least one row")

    row_lengths = {len(row) for row in group_grid}

    if len(row_lengths) != 1:
        raise ValueError("all rows in group_grid must have the same length")

    return len(group_grid), len(group_grid[0])


def get_resolved_mos_centroid_array_shape(
    intent: MosCentroidArrayIntent,
) -> tuple[int, int]:
    """
    Resolve rows/cols from either explicit rows/cols or group_grid.
    """
    if intent.group_grid is not None:
        grid_rows, grid_cols = infer_grid_shape(intent.group_grid)

        if intent.rows is not None and intent.rows != grid_rows:
            raise ValueError(
                f"intent rows={intent.rows} does not match group_grid rows={grid_rows}"
            )

        if intent.cols is not None and intent.cols != grid_cols:
            raise ValueError(
                f"intent cols={intent.cols} does not match group_grid cols={grid_cols}"
            )

        return grid_rows, grid_cols

    if intent.rows is None or intent.cols is None:
        raise ValueError("rows and cols are required when group_grid is not provided")

    return intent.rows, intent.cols


def validate_mos_centroid_array_intent(
    intent: MosCentroidArrayIntent,
) -> None:
    rows, cols = get_resolved_mos_centroid_array_shape(intent)

    if rows <= 0 or cols <= 0:
        raise ValueError("MOS centroid intent rows and cols must be positive")

    if intent.device_a.kind != intent.device_b.kind:
        raise ValueError(
            "MOS centroid intent requires device_a and device_b to have the same MOS kind"
        )

    pattern_strategy = normalize_mos_centroid_pattern_strategy(intent.pattern_strategy)

    if pattern_strategy == "custom_grid":
        if intent.group_grid is None:
            raise ValueError("custom_grid pattern_strategy requires group_grid")
    else:
        if intent.group_grid is not None:
            raise ValueError(
                "group_grid was provided, so use pattern_strategy='custom_grid'"
            )

    if pattern_strategy in {"common_centroid", "mirrored_pair", "interdigitated"}:
        if cols % 2 != 0:
            raise ValueError(
                f"{pattern_strategy} strategy requires an even number of columns"
            )

    if intent.dummy_tile_strategy == "center_pair" and cols < 4:
        raise ValueError("center_pair dummy strategy requires at least 4 columns")