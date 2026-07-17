from inspect import signature

from glayout import gf180

from matchmaker.primitives.gf180_mos_primitive_options import (
    Gf180MosPrimitiveOptions,
)
from matchmaker.specs.mos_device_spec import MosDeviceSpec

try:
    from glayout.primitives.fet import nmos, pmos
except Exception:
    from glayout.flow.primitives.fet import nmos, pmos


_DUMMY_KWARG_ALIASES = (
    "with_dummy",
    "with_dummies",
    "dummies",
    "dummy",
)
_DNWELL_KWARG_ALIASES = (
    "with_dnwell",
    "dnwell",
)


def _first_supported_alias(function, aliases: tuple[str, ...]) -> str | None:
    parameters = signature(function).parameters
    return next((name for name in aliases if name in parameters), None)


def _call_with_supported_kwargs(function, candidate_kwargs: dict):
    """Call one installed gLayout primitive with supported explicit kwargs only."""
    function_signature = signature(function)
    supported_kwargs = {
        key: value
        for key, value in candidate_kwargs.items()
        if key in function_signature.parameters and value is not None
    }

    ignored_kwargs = {
        key: value
        for key, value in candidate_kwargs.items()
        if key not in function_signature.parameters and value is not None
    }
    if ignored_kwargs:
        ignored_names = ", ".join(sorted(ignored_kwargs))
        print(
            f"GF180 MOS primitive factory ignored unsupported kwargs: {ignored_names}"
        )

    return function(**supported_kwargs)


def create_gf180_mos_primitive(
    device: MosDeviceSpec,
    dummies: tuple[bool, bool] = (False, False),
    primitive_options: Gf180MosPrimitiveOptions | None = None,
):
    """Create one GF180 MOS primitive from typed device and adapter options.

    Alias selection is resolved against the installed primitive signature before
    invocation. Reusable placement code therefore supplies one semantic dummy or
    deep-n-well choice without probing multiple historical keyword spellings.
    """
    if primitive_options is None:
        primitive_options = Gf180MosPrimitiveOptions()

    if device.kind == "nfet":
        primitive_function = nmos
    elif device.kind == "pfet":
        primitive_function = pmos
    else:
        raise ValueError(f"Unsupported GF180 MOS device kind: {device.kind}")

    candidate_kwargs = {
        "pdk": gf180,
        "width": device.width,
        "length": device.length,
        "fingers": device.fingers,
        "multipliers": device.multipliers,
        "with_substrate_tap": primitive_options.with_substrate_tap,
        "with_tie": primitive_options.with_tie,
        "with_guardring": primitive_options.with_guardring,
        "sd_route_topmet": primitive_options.sd_route_topmet,
        "gate_route_topmet": primitive_options.gate_route_topmet,
        "interfinger_routing": primitive_options.interfinger_routing,
        "tie_layers": primitive_options.tie_layers,
        "substrate_tap_layers": primitive_options.substrate_tap_layers,
    }

    dummy_keyword = _first_supported_alias(
        primitive_function,
        _DUMMY_KWARG_ALIASES,
    )
    if dummy_keyword is not None:
        candidate_kwargs[dummy_keyword] = (
            primitive_options.with_dummy
            if primitive_options.with_dummy is not None
            else dummies
        )

    dnwell_keyword = _first_supported_alias(
        primitive_function,
        _DNWELL_KWARG_ALIASES,
    )
    if dnwell_keyword is not None:
        candidate_kwargs[dnwell_keyword] = primitive_options.with_dnwell

    candidate_kwargs.update(dict(primitive_options.extra_kwargs))
    return _call_with_supported_kwargs(
        function=primitive_function,
        candidate_kwargs=candidate_kwargs,
    )
