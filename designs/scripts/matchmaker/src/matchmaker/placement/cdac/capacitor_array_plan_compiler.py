from collections import defaultdict, deque
from dataclasses import dataclass
from math import inf

from matchmaker.placement.cdac.capacitor_array_intent import (
    CdacCapacitorArrayIntent,
)
from matchmaker.placement.core.orientation_policy import get_orientation_for_tile
from matchmaker.placement.core.tile_plan import PlacementPlan, Tile


Coordinate = tuple[int, int]


@dataclass(frozen=True)
class _PairAssignment:
    first_group: str
    second_group: str


@dataclass(frozen=True)
class _CapacitorRecord:
    instance_name: str
    group: str
    compatibility_key: tuple[object, ...]
    unit_index: int


def infer_near_square_grid_shape(total_units: int) -> tuple[int, int]:
    """Infer a deterministic factorization with minimum aspect-ratio error."""

    if total_units <= 0:
        raise ValueError("total_units must be positive")

    best: tuple[float, int, int] | None = None
    for rows in range(1, total_units + 1):
        if total_units % rows:
            continue
        cols = total_units // rows
        if rows > cols:
            continue
        candidate = (abs(cols - rows), rows, cols)
        if best is None or candidate < best:
            best = candidate

    if best is None:
        raise RuntimeError("unable to factor capacitor-array unit count")
    return best[1], best[2]


def resolve_cdac_capacitor_grid_shape(
    intent: CdacCapacitorArrayIntent,
    total_units: int,
) -> tuple[int, int]:
    rows = intent.rows
    cols = intent.cols

    if rows is None and cols is None:
        return infer_near_square_grid_shape(total_units)
    if rows is None:
        if total_units % cols:
            raise ValueError("total capacitor units are not divisible by cols")
        rows = total_units // cols
    elif cols is None:
        if total_units % rows:
            raise ValueError("total capacitor units are not divisible by rows")
        cols = total_units // rows

    if rows * cols != total_units:
        raise ValueError(
            "capacitor-array grid area must equal the manifest capacitor count"
        )
    return rows, cols


def _inversion_orbits(rows: int, cols: int) -> tuple[tuple[Coordinate, ...], ...]:
    center_row = (rows - 1) / 2.0
    center_col = (cols - 1) / 2.0
    visited: set[Coordinate] = set()
    orbits: list[tuple[Coordinate, ...]] = []

    for row in range(rows):
        for col in range(cols):
            coordinate = (row, col)
            if coordinate in visited:
                continue
            mirror = (rows - 1 - row, cols - 1 - col)
            orbit = tuple(sorted({coordinate, mirror}))
            visited.update(orbit)
            orbits.append(orbit)

    def orbit_key(orbit: tuple[Coordinate, ...]) -> tuple[float, Coordinate]:
        radius = min(
            (row - center_row) ** 2 + (col - center_col) ** 2
            for row, col in orbit
        )
        return (radius, orbit[0])

    return tuple(sorted(orbits, key=orbit_key))


def _capacitor_records(intent: CdacCapacitorArrayIntent) -> tuple[_CapacitorRecord, ...]:
    records: list[_CapacitorRecord] = []
    for instance in intent.manifest.instances:
        if instance.instance_kind != "mim_capacitor":
            continue
        role = instance.parameters.get("role")
        device_spec = instance.parameters.get("device_spec")
        compatibility_key = getattr(device_spec, "compatibility_key", None)
        if compatibility_key is None:
            raise ValueError(
                f"capacitor instance {instance.instance_name!r} has no compatible device spec"
            )

        if role == "termination":
            group = "TERM"
        elif role == "switched":
            bit_index = instance.parameters.get("bank_bit_index")
            if not isinstance(bit_index, int):
                raise ValueError(
                    f"switched capacitor {instance.instance_name!r} lacks bank_bit_index"
                )
            group = f"B{bit_index}"
        else:
            raise ValueError(
                f"capacitor instance {instance.instance_name!r} has unknown role {role!r}"
            )

        unit_index = instance.parameters.get("unit_index")
        if not isinstance(unit_index, int) or unit_index < 0:
            raise ValueError(
                f"capacitor instance {instance.instance_name!r} has invalid unit_index"
            )
        records.append(
            _CapacitorRecord(
                instance_name=instance.instance_name,
                group=group,
                compatibility_key=tuple(compatibility_key),
                unit_index=unit_index,
            )
        )

    if not records:
        raise ValueError("CDAC manifest contains no MIM capacitor instances")
    return tuple(sorted(records, key=lambda item: (item.group, item.unit_index, item.instance_name)))


def _choose_center_group(
    remaining_counts: dict[str, int],
) -> str:
    odd_groups = sorted(group for group, count in remaining_counts.items() if count % 2)
    if len(odd_groups) != 1:
        raise ValueError(
            "an odd-sized inversion array requires exactly one odd-count capacitor group"
        )
    return odd_groups[0]


def _pair_odd_residual_groups(
    *,
    odd_groups: list[str],
    compatibility_by_group: dict[str, tuple[object, ...]],
    residual_pair_policy: str,
) -> list[_PairAssignment]:
    if not odd_groups:
        return []
    if residual_pair_policy == "reject":
        raise ValueError(
            "odd capacitor-group counts cannot satisfy per-group inversion symmetry"
        )
    if len(odd_groups) % 2:
        raise ValueError("odd residual capacitor groups must occur in compatible pairs")

    assignments: list[_PairAssignment] = []
    unmatched = list(sorted(odd_groups))
    while unmatched:
        first = unmatched.pop(0)
        first_key = compatibility_by_group[first]
        match_index = next(
            (
                index
                for index, candidate in enumerate(unmatched)
                if compatibility_by_group[candidate] == first_key
            ),
            None,
        )
        if match_index is None:
            raise ValueError(
                f"no physically compatible odd residual group can pair with {first!r}"
            )
        second = unmatched.pop(match_index)
        assignments.append(_PairAssignment(first, second))
    return assignments


def _fair_homogeneous_pair_sequence(pair_quota: dict[str, int]) -> list[_PairAssignment]:
    total_pairs = sum(pair_quota.values())
    if total_pairs == 0:
        return []

    placed = {group: 0 for group in pair_quota}
    sequence: list[_PairAssignment] = []
    for step in range(total_pairs):
        best_group = None
        best_lag = -inf
        for group in sorted(pair_quota):
            if placed[group] >= pair_quota[group]:
                continue
            target = (step + 1) * pair_quota[group] / total_pairs
            lag = target - placed[group]
            if lag > best_lag:
                best_group = group
                best_lag = lag
        if best_group is None:
            raise RuntimeError("failed to allocate homogeneous capacitor pairs")
        placed[best_group] += 1
        sequence.append(_PairAssignment(best_group, best_group))
    return sequence


def compile_cdac_capacitor_array_plan(
    intent: CdacCapacitorArrayIntent,
) -> PlacementPlan:
    """Compile capacitor hierarchy into a deterministic inversion-symmetric grid."""

    if intent.symmetry_policy != "inversion":
        raise NotImplementedError(
            f"Unsupported CDAC capacitor symmetry policy: {intent.symmetry_policy!r}"
        )

    records = _capacitor_records(intent)
    rows, cols = resolve_cdac_capacitor_grid_shape(intent, len(records))
    orbits = list(_inversion_orbits(rows, cols))
    singleton_orbits = [orbit for orbit in orbits if len(orbit) == 1]
    pair_orbits = [orbit for orbit in orbits if len(orbit) == 2]
    if len(singleton_orbits) > 1:
        raise RuntimeError("180-degree inversion can contain at most one center slot")

    records_by_group: dict[str, deque[_CapacitorRecord]] = defaultdict(deque)
    compatibility_by_group: dict[str, tuple[object, ...]] = {}
    for record in records:
        records_by_group[record.group].append(record)
        prior_key = compatibility_by_group.setdefault(
            record.group,
            record.compatibility_key,
        )
        if prior_key != record.compatibility_key:
            raise ValueError(
                f"capacitor group {record.group!r} mixes incompatible unit devices"
            )

    remaining_counts = {
        group: len(group_records)
        for group, group_records in records_by_group.items()
    }
    coordinate_to_record: dict[Coordinate, _CapacitorRecord] = {}

    if singleton_orbits:
        center_group = _choose_center_group(remaining_counts)
        center_record = records_by_group[center_group].popleft()
        remaining_counts[center_group] -= 1
        coordinate_to_record[singleton_orbits[0][0]] = center_record

    odd_groups = sorted(
        group for group, count in remaining_counts.items() if count % 2
    )
    mixed_assignments = _pair_odd_residual_groups(
        odd_groups=odd_groups,
        compatibility_by_group=compatibility_by_group,
        residual_pair_policy=intent.residual_pair_policy,
    )
    for assignment in mixed_assignments:
        remaining_counts[assignment.first_group] -= 1
        remaining_counts[assignment.second_group] -= 1

    pair_quota = {
        group: count // 2
        for group, count in remaining_counts.items()
        if count
    }
    assignments = mixed_assignments + _fair_homogeneous_pair_sequence(pair_quota)
    if len(assignments) != len(pair_orbits):
        raise RuntimeError(
            "capacitor pair assignments do not match inversion-pair slot count"
        )

    for orbit, assignment in zip(pair_orbits, assignments):
        first_record = records_by_group[assignment.first_group].popleft()
        second_record = records_by_group[assignment.second_group].popleft()
        coordinate_to_record[orbit[0]] = first_record
        coordinate_to_record[orbit[1]] = second_record

    unplaced = [
        record.instance_name
        for group_records in records_by_group.values()
        for record in group_records
    ]
    if unplaced:
        raise RuntimeError(f"unplaced capacitor instances remain: {unplaced}")

    tiles: list[Tile] = []
    for row in range(rows):
        for col in range(cols):
            record = coordinate_to_record.get((row, col))
            if record is None:
                raise RuntimeError(f"capacitor grid slot {(row, col)} was not assigned")
            tiles.append(
                Tile(
                    name=record.instance_name,
                    group=record.group,
                    row=row,
                    col=col,
                    orientation=get_orientation_for_tile(
                        row=row,
                        col=col,
                        rows=rows,
                        cols=cols,
                        policy=intent.orientation_policy,
                    ),
                    role="active",
                )
            )

    return PlacementPlan(
        cell_name=intent.resolved_cell_name,
        rows=rows,
        cols=cols,
        tiles=tuple(tiles),
    )
