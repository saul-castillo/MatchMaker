import argparse
from collections import Counter
from inspect import signature
from pathlib import Path

from glayout import gf180

from matchmaker.physical.gf180_mos_access import (
    classify_gf180_mos_external_port_name,
)
from matchmaker.primitives.gf180_mos_primitive_factory import (
    create_gf180_mos_primitive,
    nmos,
    pmos,
)
from matchmaker.primitives.gf180_mos_primitive_options import (
    make_gf180_bulk_tied_mos_options,
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


def _report_port(prefix: str, port, *, terminal: str | None = None) -> None:
    terminal_text = "" if terminal is None else f"terminal={terminal!r} "
    print(
        f"{prefix}: "
        f"{terminal_text}"
        f"name={getattr(port, 'name', None)!r} "
        f"center={tuple(map(float, port.center))} "
        f"orientation={float(port.orientation)} "
        f"width={float(port.width)} "
        f"layer={port.layer!r}"
    )


def _is_cardinal_tie_top_metal_candidate(port_name: str) -> bool:
    parts = port_name.split("_")
    return (
        len(parts) == 5
        and parts[0].lower() == "tie"
        and parts[1].upper() in {"N", "E", "S", "W"}
        and parts[2].lower() == "top"
        and parts[3].lower() == "met"
        and parts[4].upper() in {"N", "E", "S", "W"}
    )


def _report_device(label: str, component, *, full_ports: bool) -> None:
    ports = sorted(_ports(component), key=lambda port: str(getattr(port, "name", "")))
    canonical = []
    simple_unclassified = []
    cardinal_tie_candidates = []
    for port in ports:
        port_name = str(getattr(port, "name", ""))
        if _is_cardinal_tie_top_metal_candidate(port_name):
            cardinal_tie_candidates.append(port_name)
        classification = classify_gf180_mos_external_port_name(port_name)
        if classification is not None:
            canonical.append((port, classification[0]))
        elif len(port_name.split("_")) == 2:
            simple_unclassified.append(port)

    print(f"{label} component name: {component.name}")
    print(f"{label} bbox: {component.bbox}")
    print(f"{label} raw port count: {len(ports)}")
    terminal_counts = Counter(terminal for _, terminal in canonical)
    print(f"{label} routable external port count: {len(canonical)}")
    print(
        f"{label} routable terminal counts: "
        + ", ".join(
            f"{terminal}={terminal_counts[terminal]}"
            for terminal in sorted(terminal_counts)
        )
    )
    for port, terminal in canonical:
        _report_port(f"{label} external port", port, terminal=terminal)

    print(
        f"{label} cardinal tie top-metal candidates: "
        + ", ".join(cardinal_tie_candidates)
    )

    print(f"{label} simple unclassified port count: {len(simple_unclassified)}")
    for port in simple_unclassified:
        _report_port(f"{label} simple unclassified port", port)

    if full_ports:
        for port in ports:
            _report_port(f"{label} raw port", port)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the installed GF180 NMOS/PMOS primitives used by the "
            "parameterized transmission-gate generator. Simple unclassified "
            "ports are reported separately to identify supply/tie candidates."
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

    primitive_options = make_gf180_bulk_tied_mos_options()
    nmos_component = create_gf180_mos_primitive(
        switch.nmos,
        primitive_options=primitive_options,
    )
    pmos_component = create_gf180_mos_primitive(
        switch.pmos,
        primitive_options=primitive_options,
    )

    print(f"nmos callable: {nmos.__module__}.{nmos.__name__}")
    print(f"nmos signature: {signature(nmos)}")
    print(f"pmos callable: {pmos.__module__}.{pmos.__name__}")
    print(f"pmos signature: {signature(pmos)}")
    print(f"explicit primitive options: {primitive_options}")
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
