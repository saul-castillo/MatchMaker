import argparse
from inspect import signature
from pathlib import Path

from glayout import gf180

from matchmaker.primitives.gf180_mim_capacitor_factory import (
    create_gf180_mim_capacitor,
    mimcap,
)
from matchmaker.specs.banked_cdac_spec import (
    make_gf180_4bit_banked_cdac_reference_spec,
)


def _ports(component):
    if hasattr(component, "get_ports_list"):
        return tuple(component.get_ports_list())
    ports = component.ports
    if hasattr(ports, "values"):
        return tuple(ports.values())
    return tuple(ports)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the installed gLayout/GF180 MIM primitive before MatchMaker "
            "defines canonical capacitor access points."
        )
    )
    parser.add_argument("--write-gds", type=Path)
    args = parser.parse_args()

    gf180.activate()
    spec = make_gf180_4bit_banked_cdac_reference_spec().unit_capacitor
    component = create_gf180_mim_capacitor(spec)

    print(f"mimcap callable: {mimcap.__module__}.{mimcap.__name__}")
    print(f"mimcap signature: {signature(mimcap)}")
    print(f"requested size: ({spec.width}, {spec.length})")
    print(f"component name: {component.name}")
    print(f"component bbox: {component.bbox}")

    ports = sorted(_ports(component), key=lambda port: str(getattr(port, "name", "")))
    print(f"port count: {len(ports)}")
    for port in ports:
        print(
            "port: "
            f"name={getattr(port, 'name', None)!r} "
            f"center={tuple(map(float, port.center))} "
            f"orientation={float(port.orientation)} "
            f"width={float(port.width)} "
            f"layer={port.layer!r}"
        )

    if args.write_gds is not None:
        args.write_gds.parent.mkdir(parents=True, exist_ok=True)
        component.write_gds(args.write_gds)
        print(f"wrote GDS: {args.write_gds}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
