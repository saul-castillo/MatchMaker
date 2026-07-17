from dataclasses import dataclass

from matchmaker.specs.mos_device_spec import MosDeviceSpec


@dataclass(frozen=True)
class TransmissionGateSpec:
    """Complementary MOS transmission-gate device specification."""

    name: str
    nmos: MosDeviceSpec
    pmos: MosDeviceSpec

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("transmission-gate name must be non-empty")
        if self.nmos.kind != "nfet":
            raise ValueError("transmission-gate nmos must be an nfet")
        if self.pmos.kind != "pfet":
            raise ValueError("transmission-gate pmos must be a pfet")
        if (
            self.nmos.length is not None
            and self.pmos.length is not None
            and self.nmos.length != self.pmos.length
        ):
            raise ValueError("transmission-gate NMOS and PMOS lengths must match")

    @property
    def transistor_count(self) -> int:
        return self.nmos.multipliers + self.pmos.multipliers


@dataclass(frozen=True)
class ReferenceSelectorSpec:
    """Two-input VREF/VSS selector built from two transmission gates."""

    name: str
    switch: TransmissionGateSpec

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("reference-selector name must be non-empty")

    @property
    def transistor_count(self) -> int:
        return 2 * self.switch.transistor_count
