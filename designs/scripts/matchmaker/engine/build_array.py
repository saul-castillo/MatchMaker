from pathlib import Path

from .spec import CentroidArraySpec
from .patterns import abba_pattern


def build_centroid_array(spec: CentroidArraySpec, output_dir: str | Path):
    """
    First engine stub.
    """
    if spec.pattern != "ABBA":
        raise NotImplementedError("Only ABBA pattern is currently supported")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pattern = abba_pattern(spec.rows, spec.cols)

    return {
        "cell_name": spec.cell_name,
        "output_dir": output_dir,
        "pattern": pattern,
    }