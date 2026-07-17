from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


_CARDINAL_DIRECTIONS = frozenset({"N", "S", "E", "W"})


@dataclass(frozen=True)
class Gf180MosExternalAccessPolicy:
    """Device-adapter grammar for simple external GF180 MOS ports.

    Primitive port names belong in this device-specific adapter. Physical layer,
    width, center, and orientation values are always read from the actual ports.
    """

    terminal_aliases: Mapping[str, str] = field(
        default_factory=lambda: {
            "gate": "gate",
            "source": "source",
            "drain": "drain",
            "bulk": "bulk",
            "body": "bulk",
            "substrate": "bulk",
            "well": "bulk",
        }
    )
    directions: frozenset[str] = _CARDINAL_DIRECTIONS

    def __post_init__(self) -> None:
        aliases = {
            str(name).lower(): str(terminal).lower()
            for name, terminal in self.terminal_aliases.items()
        }
        if not aliases:
            raise ValueError("MOS access policy requires terminal aliases")
        directions = frozenset(str(direction).upper() for direction in self.directions)
        if not directions:
            raise ValueError("MOS access policy requires at least one direction")
        object.__setattr__(self, "terminal_aliases", MappingProxyType(aliases))
        object.__setattr__(self, "directions", directions)


def classify_gf180_mos_external_port_name(
    port_name: str,
    policy: Gf180MosExternalAccessPolicy | None = None,
) -> tuple[str, str] | None:
    """Return ``(logical_terminal, direction)`` for one simple external port.

    Names with nested hierarchy prefixes are rejected intentionally. For
    example, ``gate_E`` is accepted while ``multiplier_0_gate_E`` is not.
    """

    policy = policy or Gf180MosExternalAccessPolicy()
    parts = str(port_name).split("_")
    if len(parts) != 2:
        return None

    raw_terminal, raw_direction = parts
    direction = raw_direction.upper()
    if direction not in policy.directions:
        return None

    terminal = policy.terminal_aliases.get(raw_terminal.lower())
    if terminal is None:
        return None
    return terminal, direction


def gf180_mos_external_port_name(terminal: str, direction: str) -> str:
    """Construct a simple external port name from canonical tokens."""

    canonical_terminal = str(terminal).lower()
    canonical_direction = str(direction).upper()
    if canonical_direction not in _CARDINAL_DIRECTIONS:
        raise ValueError(f"unsupported cardinal direction: {direction!r}")
    if canonical_terminal not in {"gate", "source", "drain", "well"}:
        raise ValueError(f"unsupported GF180 MOS primitive terminal: {terminal!r}")
    return f"{canonical_terminal}_{canonical_direction}"
