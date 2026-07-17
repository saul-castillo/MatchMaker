from dataclasses import dataclass

from matchmaker.design.circuit_manifest import (
    CircuitInstance,
    CircuitManifest,
    CircuitNet,
)
from matchmaker.physical.models import TerminalRef
from matchmaker.specs.banked_cdac_spec import BankedCdacSpec


@dataclass(frozen=True)
class CdacNamingPolicy:
    """Stable logical naming policy for generated CDAC hierarchy."""

    capacitor_prefix: str = "C"
    selector_prefix: str = "SEL"
    reset_instance_name: str = "RESET_TG"
    vout_net_name: str = "VOUT"
    vref_net_name: str = "VREF"
    vss_net_name: str = "VSS"
    vdd_net_name: str = "VDD"
    reset_net_name: str = "RST"
    reset_bar_net_name: str = "RSTB"

    def __post_init__(self) -> None:
        values = tuple(self.__dict__.values())
        if any(not value for value in values):
            raise ValueError("CDAC naming-policy values must be non-empty")

    def bank_name(self, bit_index: int) -> str:
        return f"B{bit_index}"

    def bank_bar_name(self, bit_index: int) -> str:
        return f"B{bit_index}B"

    def bank_bottom_net_name(self, bit_index: int) -> str:
        return f"BANK_B{bit_index}"

    def capacitor_instance_name(self, bit_index: int, unit_index: int) -> str:
        return f"{self.capacitor_prefix}_B{bit_index}_{unit_index}"

    def termination_instance_name(self, unit_index: int) -> str:
        return f"{self.capacitor_prefix}_TERM_{unit_index}"

    def selector_instance_name(self, bit_index: int) -> str:
        return f"{self.selector_prefix}_B{bit_index}"


def compile_banked_cdac_manifest(
    spec: BankedCdacSpec,
    naming: CdacNamingPolicy | None = None,
) -> CircuitManifest:
    """Compile typed CDAC hierarchy and connectivity without reading a schematic."""

    naming = naming or CdacNamingPolicy()
    instances: list[CircuitInstance] = []
    net_terminals: dict[str, list[TerminalRef]] = {}
    public_nets: set[str] = {
        naming.vout_net_name,
        naming.vref_net_name,
        naming.vss_net_name,
        naming.vdd_net_name,
    }

    def connect(net_name: str, instance_name: str, terminal_name: str) -> None:
        net_terminals.setdefault(net_name, []).append(
            TerminalRef(instance_name, terminal_name)
        )

    for bank in spec.ordered_banks:
        bank_name = naming.bank_name(bank.bit_index)
        bank_bar_name = naming.bank_bar_name(bank.bit_index)
        bank_bottom_name = naming.bank_bottom_net_name(bank.bit_index)
        selector_name = naming.selector_instance_name(bank.bit_index)
        public_nets.update((bank_name, bank_bar_name))

        for unit_index in range(bank.unit_count):
            capacitor_name = naming.capacitor_instance_name(
                bank.bit_index,
                unit_index,
            )
            instances.append(
                CircuitInstance(
                    instance_name=capacitor_name,
                    instance_kind="mim_capacitor",
                    parameters={
                        "device_spec": spec.unit_capacitor,
                        "bank_bit_index": bank.bit_index,
                        "unit_index": unit_index,
                        "role": "switched",
                    },
                )
            )
            connect(naming.vout_net_name, capacitor_name, "top")
            connect(bank_bottom_name, capacitor_name, "bottom")

        instances.append(
            CircuitInstance(
                instance_name=selector_name,
                instance_kind="reference_selector",
                parameters={
                    "selector_spec": bank.selector,
                    "bank_bit_index": bank.bit_index,
                },
            )
        )
        connect(naming.vref_net_name, selector_name, "high_reference")
        connect(naming.vss_net_name, selector_name, "low_reference")
        connect(naming.vss_net_name, selector_name, "vss")
        connect(naming.vdd_net_name, selector_name, "vdd")
        connect(bank_bottom_name, selector_name, "common")
        connect(bank_name, selector_name, "control")
        connect(bank_bar_name, selector_name, "control_bar")

    for unit_index in range(spec.termination_unit_count):
        capacitor_name = naming.termination_instance_name(unit_index)
        instances.append(
            CircuitInstance(
                instance_name=capacitor_name,
                instance_kind="mim_capacitor",
                parameters={
                    "device_spec": spec.unit_capacitor,
                    "unit_index": unit_index,
                    "role": "termination",
                },
            )
        )
        connect(naming.vout_net_name, capacitor_name, "top")
        connect(naming.vss_net_name, capacitor_name, "bottom")

    if spec.reset_switch is not None:
        reset_name = naming.reset_instance_name
        instances.append(
            CircuitInstance(
                instance_name=reset_name,
                instance_kind="transmission_gate",
                parameters={
                    "switch_spec": spec.reset_switch,
                    "role": "output_reset",
                },
            )
        )
        connect(naming.vout_net_name, reset_name, "input")
        connect(naming.vss_net_name, reset_name, "output")
        connect(naming.vss_net_name, reset_name, "vss")
        connect(naming.vdd_net_name, reset_name, "vdd")
        connect(naming.reset_net_name, reset_name, "control")
        connect(naming.reset_bar_net_name, reset_name, "control_bar")
        public_nets.update((naming.reset_net_name, naming.reset_bar_net_name))

    nets = tuple(
        CircuitNet(
            name=net_name,
            terminals=tuple(terminals),
            public=net_name in public_nets,
        )
        for net_name, terminals in sorted(net_terminals.items())
    )

    return CircuitManifest(
        cell_name=spec.cell_name,
        instances=tuple(instances),
        nets=nets,
        provenance=(
            "compiled from BankedCdacSpec",
            "independent of Xschem schematic hierarchy",
            "stable names generated through CdacNamingPolicy",
        ),
    )
