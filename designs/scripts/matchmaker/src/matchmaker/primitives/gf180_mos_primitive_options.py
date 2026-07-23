from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class Gf180MosPrimitiveOptions:
    """
    Explicit options for GF180 MOS primitive generation.

    These fields are intentionally optional because gLayout primitive signatures
    may differ across versions. The primitive factory will pass only parameters
    supported by the installed gLayout function.

    Dummies are handled separately by the placement builder because they depend
    on tile position and dummy policy.
    """

    with_substrate_tap: bool | None = None
    with_tie: bool | None = None
    with_dnwell: bool | None = None
    with_guardring: bool | None = None
    with_dummy: bool | tuple[bool, bool] | None = None

    sd_route_topmet: str | None = None
    gate_route_topmet: str | None = None
    interfinger_routing: bool | None = None

    tie_layers: tuple[str, str] | None = None
    substrate_tap_layers: tuple[str, str] | None = None

    extra_kwargs: Mapping[str, Any] = field(default_factory=dict)


_COMPACT_BULK_TIED_PROFILE = {
    "with_substrate_tap": False,
    "with_tie": True,
    "with_dnwell": False,
    "with_guardring": False,
    "with_dummy": (False, False),
}


def make_gf180_compact_bulk_tied_mos_options() -> Gf180MosPrimitiveOptions:
    """Return the explicit compact MOS profile used by generated TG children.

    The profile retains conductive body ties while disabling geometry that can
    enlarge the primitive envelope or create an inherited substrate connection.
    No safety-critical field is left to an installed gLayout default.
    """

    return Gf180MosPrimitiveOptions(**_COMPACT_BULK_TIED_PROFILE)


def require_gf180_compact_bulk_tied_mos_options(
    options: Gf180MosPrimitiveOptions,
    *,
    context: str,
) -> None:
    """Reject inherited or expansive profiles before any geometry is generated."""

    mismatches = []
    for field_name, expected in _COMPACT_BULK_TIED_PROFILE.items():
        actual = getattr(options, field_name)
        if actual != expected:
            inherited = " (inherits primitive default)" if actual is None else ""
            mismatches.append(
                f"{field_name}={actual!r}{inherited}; expected {expected!r}"
            )
    if mismatches:
        raise ValueError(
            f"{context} must use the explicit compact GF180 MOS profile: "
            + "; ".join(mismatches)
        )


def render_gf180_mos_primitive_profile(
    options: Gf180MosPrimitiveOptions,
) -> str:
    """Render the safety-critical primitive profile for diagnostics."""

    def state(value: object) -> str:
        if value is True:
            return "on"
        if value is False or value == (False, False):
            return "off"
        return "inherited" if value is None else repr(value)

    return ", ".join(
        (
            f"ties={state(options.with_tie)}",
            f"substrate_taps={state(options.with_substrate_tap)}",
            f"deep_wells={state(options.with_dnwell)}",
            f"guard_rings={state(options.with_guardring)}",
            f"dummies={state(options.with_dummy)}",
        )
    )


def make_gf180_bulk_tied_mos_options() -> Gf180MosPrimitiveOptions:
    """Compatibility name for the explicit compact bulk-tied profile."""

    return make_gf180_compact_bulk_tied_mos_options()
