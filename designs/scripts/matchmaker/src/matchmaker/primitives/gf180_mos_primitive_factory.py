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


def _call_with_supported_kwargs(function, candidate_kwargs: dict):
    """
    Call a gLayout primitive while only passing kwargs supported by that
    installed gLayout version.
    """
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
    """
    Create a GF180 MOS primitive using gLayout.

    Explicit parameter sources:
        device:
            MOS dimensions and grouping identity.

        dummies:
            Primitive-level left/right dummy configuration decided by placement.

        primitive_options:
            Optional GF180/gLayout primitive-generation controls.

    Note:
        The factory passes only kwargs supported by the installed gLayout
        primitive function.
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

        # Different gLayout versions have used different dummy kwarg names.
        "with_dummy": primitive_options.with_dummy
        if primitive_options.with_dummy is not None
        else dummies,
        "with_dummies": dummies,
        "dummies": dummies,
        "dummy": dummies,

        "with_substrate_tap": primitive_options.with_substrate_tap,
        "with_tie": primitive_options.with_tie,
        "with_dnwell": primitive_options.with_dnwell,
        "with_guardring": primitive_options.with_guardring,

        "sd_route_topmet": primitive_options.sd_route_topmet,
        "gate_route_topmet": primitive_options.gate_route_topmet,
        "interfinger_routing": primitive_options.interfinger_routing,

        "tie_layers": primitive_options.tie_layers,
        "substrate_tap_layers": primitive_options.substrate_tap_layers,
    }

    candidate_kwargs.update(dict(primitive_options.extra_kwargs))

    return _call_with_supported_kwargs(
        function=primitive_function,
        candidate_kwargs=candidate_kwargs,
    )