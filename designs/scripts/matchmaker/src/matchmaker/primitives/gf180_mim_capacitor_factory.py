from inspect import signature

from glayout import gf180

from matchmaker.specs.capacitor_device_spec import MimCapacitorSpec

try:
    from glayout.primitives.mimcap import mimcap
except Exception:
    from glayout.flow.primitives.mimcap import mimcap


def _call_with_supported_kwargs(function, candidate_kwargs: dict):
    function_signature = signature(function)
    supported_kwargs = {
        key: value
        for key, value in candidate_kwargs.items()
        if key in function_signature.parameters and value is not None
    }
    return function(**supported_kwargs)


def _assign_component_name(component, name: str):
    try:
        component.name = name
    except Exception:
        if hasattr(component, "rename"):
            component.rename(name)
        else:
            raise
    return component


def create_gf180_mim_capacitor(spec: MimCapacitorSpec):
    """Create one GF180 gLayout MIM capacitor from a typed device spec.

    The adapter owns the installed-gLayout API mapping. It does not choose the
    capacitor dimensions, array position, spacing, or logical connectivity.
    """

    component = _call_with_supported_kwargs(
        function=mimcap,
        candidate_kwargs={
            "pdk": gf180,
            "size": (float(spec.width), float(spec.length)),
        },
    )
    return _assign_component_name(component, spec.name)
