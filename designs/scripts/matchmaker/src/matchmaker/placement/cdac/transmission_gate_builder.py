from math import isclose

from glayout.backend import Component

from matchmaker.design.transmission_gate_naming import (
    NMOS_INSTANCE_NAME,
    PMOS_INSTANCE_NAME,
)
from matchmaker.physical.gf180_mos_access import gf180_mos_external_port_name
from matchmaker.placement.cdac.transmission_gate_intent import (
    TransmissionGateLayoutIntent,
)
from matchmaker.placement.core.placement_result import (
    PlacedReferenceBinding,
    PlacementResult,
)
from matchmaker.placement.core.tile_plan import PlacementPlan, Tile
from matchmaker.primitives.gf180_mos_primitive_factory import (
    create_gf180_mos_primitive,
)


def _assign_component_name(component, name: str):
    rename = getattr(component, "rename", None)
    if callable(rename):
        rename(name)
    else:
        component.name = name
    return component


def _bbox_edges(component) -> tuple[float, float, float, float]:
    (xmin, ymin), (xmax, ymax) = component.bbox
    return float(xmin), float(ymin), float(xmax), float(ymax)


def _reference_port(reference, port_name: str):
    ports = reference.ports
    try:
        return ports[port_name]
    except (KeyError, TypeError) as error:
        raise RuntimeError(
            f"placed MOS reference does not expose required port {port_name!r}"
        ) from error


def _alignment_delta(
    *,
    nmos_reference,
    pmos_reference,
    terminal: str,
    nmos_direction: str,
    pmos_direction: str,
) -> float:
    nmos_port = _reference_port(
        nmos_reference,
        gf180_mos_external_port_name(terminal, nmos_direction),
    )
    pmos_port = _reference_port(
        pmos_reference,
        gf180_mos_external_port_name(terminal, pmos_direction),
    )
    return float(nmos_port.center[1]) - float(pmos_port.center[1])


def build_transmission_gate_device_placement(
    intent: TransmissionGateLayoutIntent,
) -> PlacementResult:
    """Place one NMOS/PMOS pair with source and drain accesses aligned.

    This stage does not route the parallel signal terminals or assign supply
    semantics. It derives all offsets from generated bounding boxes and ports.
    """

    nmos = _assign_component_name(
        create_gf180_mos_primitive(
            intent.spec.nmos,
            primitive_options=intent.nmos_primitive_options,
        ),
        f"{intent.resolved_cell_name}_nmos",
    )
    pmos = _assign_component_name(
        create_gf180_mos_primitive(
            intent.spec.pmos,
            primitive_options=intent.pmos_primitive_options,
        ),
        f"{intent.resolved_cell_name}_pmos",
    )

    top = Component(name=intent.resolved_cell_name)
    nmos_reference = top << nmos
    pmos_reference = top << pmos

    nmos_xmin, _, nmos_xmax, _ = _bbox_edges(nmos)
    pmos_xmin, _, pmos_xmax, _ = _bbox_edges(pmos)
    half_gap = intent.policy.device_gap / 2.0

    if intent.policy.nmos_side == "left":
        nmos_reference.movex(-half_gap - nmos_xmax)
        pmos_reference.movex(half_gap - pmos_xmin)
        nmos_col, pmos_col = 0, 1
    else:
        pmos_reference.movex(-half_gap - pmos_xmax)
        nmos_reference.movex(half_gap - nmos_xmin)
        pmos_col, nmos_col = 0, 1

    input_delta = _alignment_delta(
        nmos_reference=nmos_reference,
        pmos_reference=pmos_reference,
        terminal=intent.policy.input_device_terminal,
        nmos_direction=intent.policy.inner_nmos_direction,
        pmos_direction=intent.policy.inner_pmos_direction,
    )
    output_delta = _alignment_delta(
        nmos_reference=nmos_reference,
        pmos_reference=pmos_reference,
        terminal=intent.policy.output_device_terminal,
        nmos_direction=intent.policy.inner_nmos_direction,
        pmos_direction=intent.policy.inner_pmos_direction,
    )
    if not isclose(
        input_delta,
        output_delta,
        abs_tol=intent.policy.alignment_tolerance,
    ):
        raise RuntimeError(
            "NMOS/PMOS source and drain accesses cannot be aligned by one "
            f"translation: input_delta={input_delta}, output_delta={output_delta}"
        )
    pmos_reference.movey((input_delta + output_delta) / 2.0)

    plan = PlacementPlan(
        cell_name=intent.resolved_cell_name,
        rows=1,
        cols=2,
        tiles=(
            Tile(
                name=NMOS_INSTANCE_NAME,
                group="NMOS",
                row=0,
                col=nmos_col,
                orientation="R0",
                role="active",
            ),
            Tile(
                name=PMOS_INSTANCE_NAME,
                group="PMOS",
                row=0,
                col=pmos_col,
                orientation="R0",
                role="active",
            ),
        ),
    )
    bindings = {
        NMOS_INSTANCE_NAME: PlacedReferenceBinding(
            instance_name=NMOS_INSTANCE_NAME,
            cell_name=str(nmos.name),
            reference=nmos_reference,
            row=0,
            col=nmos_col,
            orientation="R0",
            role="active",
            group="NMOS",
        ),
        PMOS_INSTANCE_NAME: PlacedReferenceBinding(
            instance_name=PMOS_INSTANCE_NAME,
            cell_name=str(pmos.name),
            reference=pmos_reference,
            row=0,
            col=pmos_col,
            orientation="R0",
            role="active",
            group="PMOS",
        ),
    }
    return PlacementResult(component=top, plan=plan, bindings=bindings)
