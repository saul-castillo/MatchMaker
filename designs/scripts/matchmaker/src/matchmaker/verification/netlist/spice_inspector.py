from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class SpiceSubcircuitInstance:
    name: str
    nodes: tuple[str, ...]
    subcircuit_name: str
    statement: str

    def port_bindings(
        self,
        subcircuit: "SpiceSubcircuit",
    ) -> tuple[tuple[str, str], ...]:
        """Bind this instance's nodes to its referenced subcircuit interface."""

        if self.subcircuit_name != subcircuit.name:
            raise ValueError(
                f"instance {self.name!r} references {self.subcircuit_name!r}, "
                f"not {subcircuit.name!r}"
            )
        if len(self.nodes) != len(subcircuit.ports):
            raise ValueError(
                f"instance {self.name!r} has {len(self.nodes)} nodes but "
                f"subcircuit {subcircuit.name!r} declares "
                f"{len(subcircuit.ports)} ports"
            )
        return tuple(zip(subcircuit.ports, self.nodes))


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


def render_subcircuit_instance_interfaces(
    subcircuits: dict[str, SpiceSubcircuit],
    *,
    top_cell_name: str,
    included_subcircuit_names: tuple[str, ...] = (),
) -> str:
    """Render terminal-to-net bindings for selected top-level child families."""

    top = subcircuits.get(top_cell_name)
    if top is None:
        raise ValueError(f"top subcircuit {top_cell_name!r} was not found")
    included = frozenset(included_subcircuit_names)
    instances = tuple(
        instance
        for instance in top.subcircuit_instances
        if not included or instance.subcircuit_name in included
    )
    lines = [f"top: {top_cell_name}", "child interfaces:"]
    for instance in instances:
        child = subcircuits.get(instance.subcircuit_name)
        if child is None:
            lines.append(
                f"  {instance.name}: {instance.subcircuit_name} "
                "(definition unavailable)"
            )
            continue
        try:
            bindings = instance.port_bindings(child)
        except ValueError as error:
            lines.append(f"  {instance.name}: {error}")
            continue
        lines.append(f"  {instance.name}: {instance.subcircuit_name}")
        for port_name, node_name in bindings:
            lines.append(f"    {port_name} -> {node_name}")
    return "\n".join(lines) + "\n"
