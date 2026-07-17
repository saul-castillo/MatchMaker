import argparse
from inspect import signature
from pathlib import Path

from glayout import gf180

from matchmaker.primitives.gf180_mos_primitive_factory import (
    create_gf180_mos_primitive,
    nmos,
    pmos,
)
from matchmaker.specs.banked_cdac_spec import (
    make_gf180_4bit_banked_cdac_reference_spec,
)


_CARDINAL_DIRECTIONS = frozenset({"N", "S", "E", "W"})
_TERMINAL_ALIASES = {
    "gate": "gate",
    "source": "source",
    "drain": "drain",
    "bulk": "bulk",
    "body": "bulk",
    "substrate": "bulk",
    "well": "bulk",
}


def _ports(component):
    if hasattr(component, "get_ports_list"):
        return tuple(component.get_ports_list())
    ports = component.ports
    if hasattr(ports, "values"):
        return tuple(ports.values())
    return tuple(ports)


def _canonical_terminal(port_name: str) -> str | None:
    parts = port_name.split("_")
    if len(parts) != 2:
        return None
    terminal_name, direction = parts
    if direction.upper() not in _CARDINAL_DIRECTIONS:
        return None
    return _TERMINAL_ALIASES.get(terminal_name.lower())


def _report_device(label: str, component, *, full_ports: bool) -> None:
    ports = sorted(_ports(component), key=lambda port: str(getattr(port, "name", "")))
    canonical = tuple(
        (port, _canonical_terminal(str(getattr(port, "name", ""))))
        for port in ports
        if _canonical_terminal(str(getattr(port, "name", ""))) is not None
    )

    print(f"{label} component name: {component.name}")
    print(f"{label} bbox: {component.bbox}")
    print(f"{label} raw port count: {len(ports)}")
    print(f"{label} canonical external port count: {len(canonical)}")
    for port, terminal in canonical:
        print(
            f"{label} external port: "
            f"terminal={terminal!r} "
            f"name={getattr(port, 'name', None)!r} "
            f"center={tuple(map(float, port.center))} "
            f"orientation={float(port.orientation)} "
            f"width={float(port.width)} "
            f"layer={port.layer!r}"
        )

    if full_ports:
        for port in ports:
            print(
                f"{label} raw port: "
                f"name={getattr(port, 'name', None)!r} "
                f"center={tuple(map(float, port.center))} "
                f"orientation={float(port.orientation)} "
                f"width={float(port.width)} "
                f"layer={port.layer!r}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the installed GF180 NMOS/PMOS primitives used by the "
            "parameterized transmission-gate generator."
        )
    )
    parser.add_argument("--full-ports", action="store_true")
    parser.add_argument("--write-gds-dir", type=Path)
    args = parser.parse_args()

    gf180.activate()
    cdac = make_gf180_4bit_banked_cdac_reference_spec()
    switch = cdac.reset_switch
    if switch is None:
        raise RuntimeError("reference preset does not define a reset switch")

    nmos_component = create_gf180_mos_primitive(switch.nmos)
    pmos_component = create_gf180_mos_primitive(switch.pmos)

    print(f"nmos callable: {nmos.__module__}.{nmos.__name__}")
    print(f"nmos signature: {signature(nmos)}")
    print(f"pmos callable: {pmos.__module__}.{pmos.__name__}")
    print(f"pmos signature: {signature(pmos)}")
    print(
        "requested switch dimensions: "
        f"nmos=(W={switch.nmos.width}, L={switch.nmos.length}), "
        f"pmos=(W={switch.pmos.width}, L={switch.pmos.length})"
    )

    _report_device("nmos", nmos_component, full_ports=args.full_ports)
    _report_device("pmos", pmos_component, full_ports=args.full_ports)

    if args.write_gds_dir is not None:
        args.write_gds_dir.mkdir(parents=True, exist_ok=True)
        nmos_path = args.write_gds_dir / "diagnostic_tg_nmos.gds"
        pmos_path = args.write_gds_dir / "diagnostic_tg_pmos.gds"
        nmos_component.write_gds(nmos_path)
        pmos_component.write_gds(pmos_path)
        print(f"wrote NMOS GDS: {nmos_path}")
        print(f"wrote PMOS GDS: {pmos_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
