from dataclasses import dataclass


@dataclass(frozen=True)
class TransmissionGateCellAccessPolicy:
    terminals: tuple[str, ...] = ("input", "output", "control", "control_bar")
    directions: tuple[str, ...] = ("W", "E")

    def __post_init__(self) -> None:
        if not self.terminals:
            raise ValueError("transmission-gate cell terminals must be non-empty")
        if not self.directions:
            raise ValueError("transmission-gate cell directions must be non-empty")


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
        if terminal in policy.terminals:
            return terminal, direction
    return None
