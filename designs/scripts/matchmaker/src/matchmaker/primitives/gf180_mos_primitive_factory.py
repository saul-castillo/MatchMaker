from inspect import signature

from glayout import gf180

from matchmaker.specs.mos_device_spec import MosDeviceSpec

try:
    from glayout.primitives.fet import nmos, pmos
except Exception:
    from glayout.flow.primitives.fet import nmos, pmos


def _call_with_supported_kwargs(function, candidate_kwargs: dict):
    """
    Call a gLayout primitive while only passing kwargs supported by that
    installed gLayout version.

    This is intentionally defensive because gLayout primitive signatures have
    not been perfectly stable across examples.
    """
    function_signature = signature(function)

    supported_kwargs = {
        key: value
        for key, value in candidate_kwargs.items()
        if key in function_signature.parameters and value is not None
    }

    return function(**supported_kwargs)


def create_gf180_mos_primitive(
    device: MosDeviceSpec,
    dummies: tuple[bool, bool] = (False, False),
):
    """
    Create a GF180 MOS primitive using gLayout.

    The installed gLayout MOS primitives require the PDK object, so this factory
    always provides gf180 as the primitive PDK.

    dummies:
        Tuple of (left_dummy, right_dummy). This is passed through when the
        installed primitive supports dummy-related kwargs.
    """
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
        "with_dummy": dummies,
        "with_dummies": dummies,
        "dummies": dummies,
        "dummy": dummies,
    }

    return _call_with_supported_kwargs(
        function=primitive_function,
        candidate_kwargs=candidate_kwargs,
    )