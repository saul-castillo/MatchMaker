from matchmaker.physical.models import (
    AccessPoint,
    PhysicalDesignSnapshot,
    TerminalRef,
)


_CARDINAL_ORIENTATIONS = frozenset({0, 90, 180, 270})


def normalized_cardinal_orientation(
    orientation: float,
    *,
    context: str,
) -> int:
    """Normalize one Manhattan orientation without depending on a router."""

    normalized = int(round(float(orientation))) % 360
    if normalized not in _CARDINAL_ORIENTATIONS:
        raise ValueError(f"{context} is not Manhattan: {orientation}")
    return normalized


def unique_access_facing(
    snapshot: PhysicalDesignSnapshot,
    *,
    terminal: TerminalRef,
    orientation: int,
    context: str = "physical access",
) -> AccessPoint:
    """Return the sole terminal access facing one cardinal direction."""

    requested = normalized_cardinal_orientation(
        orientation,
        context=f"requested {context} orientation",
    )
    matches = tuple(
        access
        for access in snapshot.access_points_for(terminal)
        if normalized_cardinal_orientation(
            access.orientation,
            context=f"physical access {access.name!r}",
        )
        == requested
    )
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one {context} for {terminal.instance_name}."
            f"{terminal.terminal_name} facing {requested} degrees; "
            f"found {len(matches)}"
        )
    return matches[0]
