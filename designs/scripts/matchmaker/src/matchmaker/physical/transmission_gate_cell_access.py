from dataclasses import dataclass


@dataclass(frozen=True)
class TransmissionGateCellAccessPolicy:
    terminals: tuple[str, ...] = ("input", "output", "control", "control_bar")
    directions: tuple[str, ...] = ("W", "E")
    terminal_directions: tuple[tuple[str, tuple[str, ...]], ...] = ()

    def __post_init__(self) -> None:
        if not self.terminals:
            raise ValueError("transmission-gate cell terminals must be non-empty")
        if not self.directions:
            raise ValueError("transmission-gate cell directions must be non-empty")
        if len(set(self.terminals)) != len(self.terminals):
            raise ValueError("transmission-gate cell terminals must be unique")
        if len(set(self.directions)) != len(self.directions):
            raise ValueError("transmission-gate cell directions must be unique")
        declared_terminals: set[str] = set()
        for terminal, directions in self.terminal_directions:
            if terminal not in self.terminals:
                raise ValueError(
                    f"direction rule references unknown terminal {terminal!r}"
                )
            if terminal in declared_terminals:
                raise ValueError(
                    f"direction rule is duplicated for terminal {terminal!r}"
                )
            if not directions:
                raise ValueError(
                    f"terminal {terminal!r} requires at least one direction"
                )
            if any(direction not in self.directions for direction in directions):
                raise ValueError(
                    f"terminal {terminal!r} uses a direction outside the "
                    "declared family direction set"
                )
            if len(set(directions)) != len(directions):
                raise ValueError(
                    f"terminal {terminal!r} directions must be unique"
                )
            declared_terminals.add(terminal)

    def directions_for(self, terminal: str) -> tuple[str, ...]:
        for declared_terminal, directions in self.terminal_directions:
            if declared_terminal == terminal:
                return directions
        return self.directions


def classify_transmission_gate_cell_port_name(
    port_name: str,
    *,
    policy: TransmissionGateCellAccessPolicy | None = None,
) -> tuple[str, str] | None:
    policy = policy or TransmissionGateCellAccessPolicy()
    for direction in policy.directions:
        suffix = f"_{direction}"
        if not port_name.endswith(suffix):
            continue
        terminal = port_name[: -len(suffix)]
        if (
            terminal in policy.terminals
            and direction in policy.directions_for(terminal)
        ):
            return terminal, direction
    return None
