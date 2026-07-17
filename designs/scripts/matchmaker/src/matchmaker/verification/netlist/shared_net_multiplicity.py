from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from matchmaker.verification.netlist.spice_inspector import (
    SpiceSubcircuit,
    SpiceSubcircuitInstance,
    parse_spice_subcircuits,
)


@dataclass(frozen=True)
class SharedNetMultiplicityExpectation:
    """Expected number of distinct shared nets for one participant multiset."""

    expected_subcircuit_names: tuple[str, ...]
    expected_match_count: int
    description: str = "shared-net multiplicity"

    def __post_init__(self) -> None:
        if len(self.expected_subcircuit_names) < 2:
            raise ValueError("shared-net multiplicity requires at least two instances")
        if any(not name for name in self.expected_subcircuit_names):
            raise ValueError("expected subcircuit names must be non-empty")
        if self.expected_match_count <= 0:
            raise ValueError("expected_match_count must be positive")


@dataclass(frozen=True)
class SharedNetMultiplicityResult:
    passed: bool
    expectation: SharedNetMultiplicityExpectation
    matched_nets: tuple[str, ...]
    matched_instances: tuple[tuple[SpiceSubcircuitInstance, ...], ...]
    failure_reason: str | None = None

    def render(self) -> str:
        lines = [
            f"description: {self.expectation.description}",
            f"passed: {self.passed}",
            "expected_subcircuits: "
            + ", ".join(self.expectation.expected_subcircuit_names),
            f"expected_match_count: {self.expectation.expected_match_count}",
            f"actual_match_count: {len(self.matched_nets)}",
            f"failure_reason: {self.failure_reason}",
            "matched_nets:",
        ]
        for net_name, instances in zip(self.matched_nets, self.matched_instances):
            lines.append(f"  {net_name}:")
            for instance in instances:
                lines.append(
                    f"    {instance.name}: {instance.subcircuit_name} "
                    f"nodes={' '.join(instance.nodes)}"
                )
        return "\n".join(lines) + "\n"


def _participant_counter(
    instances: tuple[SpiceSubcircuitInstance, ...],
) -> Counter[str]:
    return Counter(instance.subcircuit_name for instance in instances)


def evaluate_shared_net_multiplicity(
    top: SpiceSubcircuit,
    expectation: SharedNetMultiplicityExpectation,
) -> SharedNetMultiplicityResult:
    """Require an exact count of shared nets with the expected participants."""
    expected_counter = Counter(expectation.expected_subcircuit_names)
    matches = tuple(
        sorted(
            (
                (net_name, instances)
                for net_name, instances in top.shared_instance_net_details(
                    minimum_instance_count=2
                ).items()
                if _participant_counter(instances) == expected_counter
            ),
            key=lambda item: item[0],
        )
    )
    passed = len(matches) == expectation.expected_match_count
    return SharedNetMultiplicityResult(
        passed=passed,
        expectation=expectation,
        matched_nets=tuple(net_name for net_name, _ in matches),
        matched_instances=tuple(instances for _, instances in matches),
        failure_reason=None
        if passed
        else (
            "Expected exactly "
            f"{expectation.expected_match_count} shared nets with participant "
            f"multiset {dict(expected_counter)}, found {len(matches)}"
        ),
    )


def evaluate_extracted_shared_net_multiplicity(
    netlist_path: Path,
    top_cell_name: str,
    expectation: SharedNetMultiplicityExpectation,
) -> SharedNetMultiplicityResult:
    path = Path(netlist_path)
    if not path.is_file():
        return SharedNetMultiplicityResult(
            passed=False,
            expectation=expectation,
            matched_nets=(),
            matched_instances=(),
            failure_reason=f"Extracted netlist does not exist: {path}",
        )

    try:
        subcircuits = parse_spice_subcircuits(path.read_text())
    except Exception as error:
        return SharedNetMultiplicityResult(
            passed=False,
            expectation=expectation,
            matched_nets=(),
            matched_instances=(),
            failure_reason=f"Could not parse extracted netlist: {error}",
        )

    top = subcircuits.get(top_cell_name)
    if top is None:
        return SharedNetMultiplicityResult(
            passed=False,
            expectation=expectation,
            matched_nets=(),
            matched_instances=(),
            failure_reason=(
                f"Top subcircuit {top_cell_name!r} was not found in {path}"
            ),
        )
    return evaluate_shared_net_multiplicity(top, expectation)
