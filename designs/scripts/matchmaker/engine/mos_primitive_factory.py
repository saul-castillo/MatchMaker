from inspect import signature

from glayout import gf180, nmos, pmos

from .spec import DeviceSpec


def _call_gf180_mos_primitive_with_supported_kwargs(primitive_function, kwargs):
    """
    Call a gLayout primitive while only passing keyword arguments that the
    primitive actually supports.

    This avoids NFET/PFET signature mismatch problems such as:
        pmos() got an unexpected keyword argument 'with_dnwell'
    """
    primitive_signature = signature(primitive_function)
    accepted_parameters = primitive_signature.parameters

    if any(
        parameter.kind == parameter.VAR_KEYWORD
        for parameter in accepted_parameters.values()
    ):
        return primitive_function(**kwargs)

    filtered_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key in accepted_parameters
    }

    return primitive_function(**filtered_kwargs)


def create_gf180_mos_primitive(
    device: DeviceSpec,
    dummies: tuple[bool, bool],
):
    """
    Create a single GF180 MOS primitive from a MatchMaker DeviceSpec.

    Parameters
    ----------
    device:
        MatchMaker MOS device specification.
    dummies:
        Tuple of booleans: (left_dummy, right_dummy).
    """
    common_kwargs = dict(
        pdk=gf180,
        width=device.width,
        length=device.length,
        fingers=device.fingers,
        multipliers=device.multipliers,
        with_tie=False,
        with_dummy=dummies,
        with_substrate_tap=False,
        dummy_routes=True,
        sd_route_topmet="met2",
        gate_route_topmet="met2",
        sd_route_left=True,
        sd_rmult=1,
        gate_rmult=1,
        interfinger_rmult=1,
    )

    if device.kind == "nfet":
        nfet_kwargs = {
            **common_kwargs,
            "with_dnwell": False,
        }

        return _call_gf180_mos_primitive_with_supported_kwargs(
            primitive_function=nmos,
            kwargs=nfet_kwargs,
        )

    if device.kind == "pfet":
        return _call_gf180_mos_primitive_with_supported_kwargs(
            primitive_function=pmos,
            kwargs=common_kwargs,
        )

    raise NotImplementedError(f"Unsupported MOS device kind: {device.kind}")