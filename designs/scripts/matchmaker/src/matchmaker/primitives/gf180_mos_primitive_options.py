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