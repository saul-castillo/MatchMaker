from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from matchmaker.verification.netlist.spice_inspector import (
    SpiceSubcircuit,
    SpiceSubcircuitInstance,
    parse_spice_subcircuits,
)


@dataclass(frozen=True)
class SharedNetConnectivityExpectation:
    """Expected exact set of extracted top-level subcircuit participants."""

    expected_subcircuit_names: tuple[str, ...]
    description: str = "shared-net connectivity"

    def __post_init__(self) -> None:
        if len(self.expected_subcircuit_names) < 2:
            raise ValueError(
                "A shared-net connectivity expectation requires at least two instances"
            )
        if any(not name for name in self.expected_subcircuit_names):
            raise ValueError("expected subcircuit names must be non-empty")


@dataclass(frozen=True)
class SharedNetConnectivityResult:
    passed: bool
    expectation: SharedNetConnectivityExpectation
    matched_net: str | None
    actual_instances: tuple[SpiceSubcircuitInstance, ...]
    candidate_match_count: int
    failure_reason: str | None = None

    def render(self) -> str:
        expected = ", ".join(self.expectation.expected_subcircuit_names)
        lines = [
            f"description: {self.expectation.description}",
            f"passed: {self.passed}",
            f"expected_subcircuits: {expected}",
            f"matched_net: {self.matched_net}",
            f"candidate_match_count: {self.candidate_match_count}",
            f"failure_reason: {self.failure_reason}",
            "actual_instances:",
        ]
        for instance in self.actual_instances:
            lines.append(
                f"  {instance.name}: {instance.subcircuit_name} "
                f"nodes={' '.join(instance.nodes)}"
            )
        return "\n".join(lines) + "\n"


def _participant_counter(
    instances: tuple[SpiceSubcircuitInstance, ...],
) -> Counter[str]:
    return Counter(instance.subcircuit_name for instance in instances)


def evaluate_shared_net_connectivity(
    top: SpiceSubcircuit,
    expectation: SharedNetConnectivityExpectation,
) -> SharedNetConnectivityResult:
    """Require exactly one shared net with exactly the expected participants."""
    expected_counter = Counter(expectation.expected_subcircuit_names)
    shared_nets = top.shared_instance_net_details(minimum_instance_count=2)
    matches = [
        (net_name, instances)
        for net_name, instances in shared_nets.items()
        if _participant_counter(instances) == expected_counter
    ]

    if len(matches) == 1:
        net_name, instances = matches[0]
        return SharedNetConnectivityResult(
            passed=True,
            expectation=expectation,
            matched_net=net_name,
            actual_instances=instances,
            candidate_match_count=1,
        )

    if len(matches) > 1:
        net_name, instances = matches[0]
        return SharedNetConnectivityResult(
            passed=False,
            expectation=expectation,
            matched_net=net_name,
            actual_instances=instances,
            candidate_match_count=len(matches),
            failure_reason=(
                "Multiple extracted nets have the expected participant set; "
                "the connectivity assertion is ambiguous"
            ),
        )

    ranked_candidates = sorted(
        shared_nets.items(),
        key=lambda item: (
            -sum(
                (
                    _participant_counter(item[1])
                    & expected_counter
                ).values()
            ),
            abs(len(item[1]) - len(expectation.expected_subcircuit_names)),
            item[0],
        ),
    )
    closest_net = ranked_candidates[0] if ranked_candidates else (None, ())
    return SharedNetConnectivityResult(
        passed=False,
        expectation=expectation,
        matched_net=closest_net[0],
        actual_instances=closest_net[1],
        candidate_match_count=0,
        failure_reason=(
            "No extracted shared net has exactly the expected subcircuit "
            "participant multiset"
        ),
    )


def evaluate_extracted_shared_net_connectivity(
    netlist_path: Path,
    top_cell_name: str,
    expectation: SharedNetConnectivityExpectation,
) -> SharedNetConnectivityResult:
    path = Path(netlist_path)
    if not path.is_file():
        return SharedNetConnectivityResult(
            passed=False,
            expectation=expectation,
            matched_net=None,
            actual_instances=(),
            candidate_match_count=0,
            failure_reason=f"Extracted netlist does not exist: {path}",
        )

    try:
        subcircuits = parse_spice_subcircuits(path.read_text())
    except Exception as error:
        return SharedNetConnectivityResult(
            passed=False,
            expectation=expectation,
            matched_net=None,
            actual_instances=(),
            candidate_match_count=0,
            failure_reason=f"Could not parse extracted netlist: {error}",
        )

    top = subcircuits.get(top_cell_name)
    if top is None:
        return SharedNetConnectivityResult(
            passed=False,
            expectation=expectation,
            matched_net=None,
            actual_instances=(),
            candidate_match_count=0,
            failure_reason=(
                f"Top subcircuit {top_cell_name!r} was not found in {path}"
            ),
        )

    return evaluate_shared_net_connectivity(top, expectation)
