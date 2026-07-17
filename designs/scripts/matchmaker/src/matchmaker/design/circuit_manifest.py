from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from matchmaker.physical.models import TerminalRef


@dataclass(frozen=True)
class CircuitInstance:
    """One logical hierarchy instance before physical placement."""

    instance_name: str
    instance_kind: str
    parameters: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.instance_name:
            raise ValueError("circuit instance_name must be non-empty")
        if not self.instance_kind:
            raise ValueError("circuit instance_kind must be non-empty")
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))


@dataclass(frozen=True)
class CircuitNet:
    """One logical electrical net over hierarchy terminals."""

    name: str
    terminals: tuple[TerminalRef, ...]
    public: bool = False

    def __post_init__(self) -> None:
        terminals = tuple(self.terminals)
        if not self.name:
            raise ValueError("circuit net name must be non-empty")
        if not terminals:
            raise ValueError("circuit net requires at least one terminal")
        if len(set(terminals)) != len(terminals):
            raise ValueError(f"circuit net {self.name!r} contains duplicate terminals")
        object.__setattr__(self, "terminals", terminals)


@dataclass(frozen=True)
class CircuitManifest:
    """Read-only logical hierarchy and connectivity generated from typed intent."""

    cell_name: str
    instances: tuple[CircuitInstance, ...]
    nets: tuple[CircuitNet, ...]
    provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        instances = tuple(self.instances)
        nets = tuple(self.nets)
        if not self.cell_name:
            raise ValueError("circuit manifest cell_name must be non-empty")
        if not instances:
            raise ValueError("circuit manifest requires at least one instance")

        instance_names = tuple(instance.instance_name for instance in instances)
        if len(set(instance_names)) != len(instance_names):
            raise ValueError("circuit manifest instance names must be unique")

        net_names = tuple(net.name for net in nets)
        if len(set(net_names)) != len(net_names):
            raise ValueError("circuit manifest net names must be unique")

        known_instances = set(instance_names)
        assigned_terminals: dict[TerminalRef, str] = {}
        for net in nets:
            for terminal in net.terminals:
                if terminal.instance_name not in known_instances:
                    raise ValueError(
                        f"net {net.name!r} references unknown instance "
                        f"{terminal.instance_name!r}"
                    )
                prior_net = assigned_terminals.get(terminal)
                if prior_net is not None:
                    raise ValueError(
                        f"terminal {terminal!r} is assigned to both "
                        f"{prior_net!r} and {net.name!r}"
                    )
                assigned_terminals[terminal] = net.name

        object.__setattr__(self, "instances", instances)
        object.__setattr__(self, "nets", nets)
        object.__setattr__(self, "provenance", tuple(self.provenance))

    def instance(self, instance_name: str) -> CircuitInstance:
        for instance in self.instances:
            if instance.instance_name == instance_name:
                return instance
        raise KeyError(f"Unknown circuit instance: {instance_name}")

    def net(self, net_name: str) -> CircuitNet:
        for net in self.nets:
            if net.name == net_name:
                return net
        raise KeyError(f"Unknown circuit net: {net_name}")

    @property
    def public_net_names(self) -> tuple[str, ...]:
        return tuple(net.name for net in self.nets if net.public)
