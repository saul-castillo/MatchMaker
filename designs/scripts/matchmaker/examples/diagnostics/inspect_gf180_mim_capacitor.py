import argparse
from collections import Counter
from inspect import signature
from pathlib import Path

from glayout import gf180

from matchmaker.physical.cdac_capacitor_snapshot import (
    classify_gf180_mim_external_port_name,
)
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


def _print_port(port, canonical_terminal=None) -> None:
    prefix = (
        f"external[{canonical_terminal}]"
        if canonical_terminal is not None
        else "port"
    )
    print(
        f"{prefix}: "
        f"name={getattr(port, 'name', None)!r} "
        f"center={tuple(map(float, port.center))} "
        f"orientation={float(port.orientation)} "
        f"width={float(port.width)} "
        f"layer={port.layer!r}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the installed gLayout/GF180 MIM primitive and report the "
            "canonical external accesses used by MatchMaker."
        )
    )
    parser.add_argument("--write-gds", type=Path)
    parser.add_argument(
        "--show-all-ports",
        action="store_true",
        help="also print nested primitive implementation exports",
    )
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
    classified = tuple(
        (port, classify_gf180_mim_external_port_name(str(port.name)))
        for port in ports
    )
    external = tuple(
        (port, terminal)
        for port, terminal in classified
        if terminal is not None
    )
    ignored = tuple(port for port, terminal in classified if terminal is None)
    counts = Counter(terminal for _, terminal in external)

    print(f"raw port count: {len(ports)}")
    print(f"canonical external access count: {len(external)}")
    print(f"ignored nested/noncanonical export count: {len(ignored)}")
    print(f"canonical terminal counts: {dict(sorted(counts.items()))}")
    for port, terminal in external:
        _print_port(port, terminal)

    if args.show_all_ports:
        for port in ignored:
            _print_port(port)

    if args.write_gds is not None:
        args.write_gds.parent.mkdir(parents=True, exist_ok=True)
        component.write_gds(args.write_gds)
        print(f"wrote GDS: {args.write_gds}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
