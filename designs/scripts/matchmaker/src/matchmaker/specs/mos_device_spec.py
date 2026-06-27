from dataclasses import dataclass
from typing import Literal


MosDeviceKind = Literal["nfet", "pfet"]


@dataclass(frozen=True)
class MosDeviceSpec:
    """
    Technology-facing MOS device description used by MatchMaker.

    This is intentionally MOS-specific. Capacitors, resistors, and other
    primitive families should get their own spec objects later.
    """

    name: str
    kind: MosDeviceKind
    width: float
    length: float | None = None
    fingers: int = 1
    multipliers: int = 1

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("MOS device name must be non-empty")

        if self.width <= 0:
            raise ValueError("MOS device width must be positive")

        if self.length is not None and self.length <= 0:
            raise ValueError("MOS device length must be positive when provided")

        if self.fingers <= 0:
            raise ValueError("MOS device fingers must be positive")

        if self.multipliers <= 0:
            raise ValueError("MOS device multipliers must be positive")