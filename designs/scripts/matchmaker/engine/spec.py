from dataclasses import dataclass
from typing import Literal


DeviceKind = Literal["nfet", "pfet"]


@dataclass(frozen=True)
class DeviceSpec:
    name: str
    kind: DeviceKind
    width: float
    length: float
    fingers: int = 1
    multipliers: int = 1


@dataclass(frozen=True)
class CentroidArraySpec:
    cell_name: str
    device_a: DeviceSpec
    device_b: DeviceSpec
    rows: int
    cols: int
    pattern: str = "ABBA"
    include_dummies: bool = True
    include_taps: bool = True
    route_gates: bool = True
    route_sources_drains: bool = True
    add_labels: bool = True
