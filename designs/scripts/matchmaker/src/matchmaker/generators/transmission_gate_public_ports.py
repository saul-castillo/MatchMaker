from matchmaker.design.transmission_gate_naming import (
    NMOS_INSTANCE_NAME,
    PMOS_INSTANCE_NAME,
)
from matchmaker.generators.transmission_gate_generator import GeneratedTransmissionGate
from matchmaker.physical.gf180_mos_access import gf180_mos_external_port_name


def _copy_component_port(component, *, new_name: str, source_name: str) -> None:
    if new_name in component.ports:
        return
    source_port = component.ports[source_name]
    try:
        component.add_port(name=new_name, port=source_port)
    except TypeError:
        component.add_port(
            name=new_name,
            center=tuple(map(float, source_port.center)),
            width=float(source_port.width),
            orientation=float(source_port.orientation),
            layer=source_port.layer,
        )


def ensure_transmission_gate_control_ports(
    generated: GeneratedTransmissionGate,
    *,
    directions: tuple[str, ...],
) -> tuple[str, ...]:
    """Expose requested NMOS/PMOS gate accesses on a generated TG cell.

    Primitive port grammar remains behind the MOS access adapter. Coordinates,
    layers, widths, and orientations are copied from runtime promoted ports.
    """

    if not directions:
        raise ValueError("at least one control direction is required")

    names: list[str] = []
    for direction in directions:
        for logical_name, instance_name in (
            ("control", NMOS_INSTANCE_NAME),
            ("control_bar", PMOS_INSTANCE_NAME),
        ):
            public_name = f"{logical_name}_{direction}"
            source_name = (
                f"{instance_name}__"
                f"{gf180_mos_external_port_name('gate', direction)}"
            )
            _copy_component_port(
                generated.component,
                new_name=public_name,
                source_name=source_name,
            )
            names.append(public_name)
    return tuple(names)
