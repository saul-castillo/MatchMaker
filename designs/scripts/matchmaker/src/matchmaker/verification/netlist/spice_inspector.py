from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class SpiceSubcircuitInstance:
    name: str
    nodes: tuple[str, ...]
    subcircuit_name: str
    statement: str


@dataclass(frozen=True)
class SpiceSubcircuit:
    name: str
    ports: tuple[str, ...]
    statements: tuple[str, ...]

    @property
    def device_statements(self) -> tuple[str, ...]:
        return tuple(
            statement
            for statement in self.statements
            if statement and statement[0].upper() in {"M", "X", "R", "C", "D", "Q"}
        )

    @property
    def mos_statements(self) -> tuple[str, ...]:
        return tuple(
            statement
            for statement in self.statements
            if statement and statement[0].upper() == "M"
        )

    @property
    def subcircuit_instance_statements(self) -> tuple[str, ...]:
        return tuple(
            statement
            for statement in self.statements
            if statement and statement[0].upper() == "X"
        )

    @property
    def subcircuit_instances(self) -> tuple[SpiceSubcircuitInstance, ...]:
        return tuple(
            parse_spice_subcircuit_instance(statement)
            for statement in self.subcircuit_instance_statements
        )

    def shared_instance_net_details(
        self,
        minimum_instance_count: int = 2,
    ) -> dict[str, tuple[SpiceSubcircuitInstance, ...]]:
        """Map shared nets to the unique top-level X instances that use them."""
        if minimum_instance_count < 2:
            raise ValueError("minimum_instance_count must be at least 2")

        usage: dict[str, list[SpiceSubcircuitInstance]] = defaultdict(list)
        for instance in self.subcircuit_instances:
            for node in dict.fromkeys(instance.nodes):
                usage[node].append(instance)

        return {
            node: tuple(instances)
            for node, instances in usage.items()
            if len(instances) >= minimum_instance_count
        }

    def shared_instance_nets(
        self,
        minimum_instance_count: int = 2,
    ) -> dict[str, tuple[str, ...]]:
        """Map each net used by multiple top-level X instances to instance names."""
        return {
            node: tuple(instance.name for instance in instances)
            for node, instances in self.shared_instance_net_details(
                minimum_instance_count
            ).items()
        }


def parse_spice_subcircuit_instance(statement: str) -> SpiceSubcircuitInstance:
    """Parse a simple SPICE X-instance statement emitted by Magic ext2spice."""
    tokens = statement.split()
    if len(tokens) < 3 or not tokens[0].upper().startswith("X"):
        raise ValueError(f"Malformed subcircuit instance statement: {statement}")

    return SpiceSubcircuitInstance(
        name=tokens[0],
        nodes=tuple(tokens[1:-1]),
        subcircuit_name=tokens[-1],
        statement=statement,
    )


def _logical_spice_statements(text: str) -> tuple[str, ...]:
    statements: list[str] = []

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("*"):
            continue

        if stripped.startswith("+") and statements:
            statements[-1] = statements[-1] + " " + stripped[1:].strip()
        else:
            statements.append(stripped)

    return tuple(statements)


def parse_spice_subcircuits(text: str) -> dict[str, SpiceSubcircuit]:
    """Parse `.subckt` blocks while preserving their logical statements."""
    parsed: dict[str, SpiceSubcircuit] = {}
    current_name: str | None = None
    current_ports: tuple[str, ...] = ()
    current_statements: list[str] = []

    for statement in _logical_spice_statements(text):
        tokens = statement.split()
        if not tokens:
            continue

        directive = tokens[0].lower()
        if directive == ".subckt":
            if len(tokens) < 2:
                raise ValueError(f"Malformed .subckt statement: {statement}")
            if current_name is not None:
                raise ValueError(
                    f"Nested .subckt statement encountered inside {current_name!r}"
                )
            current_name = tokens[1]
            current_ports = tuple(tokens[2:])
            current_statements = []
            continue

        if directive == ".ends":
            if current_name is None:
                continue
            parsed[current_name] = SpiceSubcircuit(
                name=current_name,
                ports=current_ports,
                statements=tuple(current_statements),
            )
            current_name = None
            current_ports = ()
            current_statements = []
            continue

        if current_name is not None:
            current_statements.append(statement)

    if current_name is not None:
        raise ValueError(f"Unterminated .subckt block: {current_name}")

    return parsed
