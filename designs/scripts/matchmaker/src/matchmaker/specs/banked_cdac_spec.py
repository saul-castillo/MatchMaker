from dataclasses import dataclass

from matchmaker.specs.capacitor_device_spec import MimCapacitorSpec
from matchmaker.specs.mos_device_spec import MosDeviceSpec
from matchmaker.specs.transmission_gate_spec import (
    ReferenceSelectorSpec,
    TransmissionGateSpec,
)


@dataclass(frozen=True)
class CdacBankSpec:
    """One switched capacitor bank and its shared reference selector."""

    bit_index: int
    unit_count: int
    selector: ReferenceSelectorSpec

    def __post_init__(self) -> None:
        if self.bit_index < 0:
            raise ValueError("CDAC bank bit_index must be non-negative")
        if self.unit_count <= 0:
            raise ValueError("CDAC bank unit_count must be positive")

    @property
    def logical_name(self) -> str:
        return f"B{self.bit_index}"


@dataclass(frozen=True)
class BankedCdacSpec:
    """Typed hierarchy specification for a single-ended banked CDAC.

    The spec is the generator source of truth. Xschem schematics are independent
    LVS references and are never parsed to construct this object.
    """

    cell_name: str
    unit_capacitor: MimCapacitorSpec
    banks: tuple[CdacBankSpec, ...]
    termination_unit_count: int
    reset_switch: TransmissionGateSpec | None = None

    def __post_init__(self) -> None:
        banks = tuple(self.banks)
        if not self.cell_name:
            raise ValueError("CDAC cell_name must be non-empty")
        if not banks:
            raise ValueError("a banked CDAC requires at least one bank")
        bit_indices = tuple(bank.bit_index for bank in banks)
        if len(set(bit_indices)) != len(bit_indices):
            raise ValueError("CDAC bank bit indices must be unique")
        if self.termination_unit_count < 0:
            raise ValueError("termination_unit_count must be non-negative")
        object.__setattr__(self, "banks", banks)

    @property
    def ordered_banks(self) -> tuple[CdacBankSpec, ...]:
        return tuple(sorted(self.banks, key=lambda bank: bank.bit_index))

    @property
    def resolution_bits(self) -> int:
        return len(self.banks)

    @property
    def switched_unit_count(self) -> int:
        return sum(bank.unit_count for bank in self.banks)

    @property
    def total_unit_count(self) -> int:
        return self.switched_unit_count + self.termination_unit_count

    @property
    def transistor_count(self) -> int:
        selector_devices = sum(bank.selector.transistor_count for bank in self.banks)
        reset_devices = 0 if self.reset_switch is None else self.reset_switch.transistor_count
        return selector_devices + reset_devices


def make_scaled_binary_banked_cdac_spec(
    *,
    cell_name: str,
    bits: int,
    unit_capacitor: MimCapacitorSpec,
    base_nmos_width: float,
    base_pmos_width: float,
    mos_length: float,
    termination_unit_count: int = 1,
    include_reset_switch: bool = True,
) -> BankedCdacSpec:
    """Construct a binary banked CDAC with selector width scaled by bank units.

    This compiler is parameterized; it contains no fixed bit count, capacitor
    geometry, transistor dimensions, or placement coordinates.
    """

    if bits <= 0:
        raise ValueError("bits must be positive")
    if base_nmos_width <= 0 or base_pmos_width <= 0:
        raise ValueError("base transmission-gate widths must be positive")
    if mos_length <= 0:
        raise ValueError("mos_length must be positive")

    banks: list[CdacBankSpec] = []
    for bit_index in range(bits):
        unit_count = 1 << bit_index
        nmos = MosDeviceSpec(
            name=f"B{bit_index}_selector_nmos",
            kind="nfet",
            width=base_nmos_width * unit_count,
            length=mos_length,
        )
        pmos = MosDeviceSpec(
            name=f"B{bit_index}_selector_pmos",
            kind="pfet",
            width=base_pmos_width * unit_count,
            length=mos_length,
        )
        switch = TransmissionGateSpec(
            name=f"B{bit_index}_selector_switch",
            nmos=nmos,
            pmos=pmos,
        )
        banks.append(
            CdacBankSpec(
                bit_index=bit_index,
                unit_count=unit_count,
                selector=ReferenceSelectorSpec(
                    name=f"B{bit_index}_reference_selector",
                    switch=switch,
                ),
            )
        )

    reset_switch = None
    if include_reset_switch:
        reset_switch = TransmissionGateSpec(
            name="reset_switch",
            nmos=MosDeviceSpec(
                name="reset_nmos",
                kind="nfet",
                width=base_nmos_width,
                length=mos_length,
            ),
            pmos=MosDeviceSpec(
                name="reset_pmos",
                kind="pfet",
                width=base_pmos_width,
                length=mos_length,
            ),
        )

    return BankedCdacSpec(
        cell_name=cell_name,
        unit_capacitor=unit_capacitor,
        banks=tuple(banks),
        termination_unit_count=termination_unit_count,
        reset_switch=reset_switch,
    )


def make_gf180_4bit_banked_cdac_reference_spec(
    cell_name: str = "cdac_4b_banked_scaled_selectors_layout",
) -> BankedCdacSpec:
    """Named preset matching the reviewed nominal GF180 reference hierarchy.

    These concrete values are isolated configuration data. Generation algorithms
    must not depend on this preset being four bits or using these dimensions.
    """

    return make_scaled_binary_banked_cdac_spec(
        cell_name=cell_name,
        bits=4,
        unit_capacitor=MimCapacitorSpec(
            name="unit_mim_capacitor",
            width=5.0,
            length=5.0,
            model="cap_mim_2f0fF",
        ),
        base_nmos_width=4.0,
        base_pmos_width=8.0,
        mos_length=0.28,
        termination_unit_count=1,
        include_reset_switch=True,
    )
