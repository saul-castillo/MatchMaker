"""SPICE netlist inspection, connectivity, and schematic-export helpers."""

from matchmaker.verification.netlist.connectivity_assertions import (
    SharedNetConnectivityExpectation,
    SharedNetConnectivityResult,
    evaluate_extracted_shared_net_connectivity,
    evaluate_shared_net_connectivity,
)
from matchmaker.verification.netlist.spice_inspector import (
    SpiceSubcircuit,
    SpiceSubcircuitInstance,
    parse_spice_subcircuits,
)
from matchmaker.verification.netlist.xschem_schematic_netlist import (
    XschemNetlistConfig,
    XschemNetlistResult,
    run_xschem_schematic_netlist,
)

__all__ = [
    "SharedNetConnectivityExpectation",
    "SharedNetConnectivityResult",
    "SpiceSubcircuit",
    "SpiceSubcircuitInstance",
    "XschemNetlistConfig",
    "XschemNetlistResult",
    "evaluate_extracted_shared_net_connectivity",
    "evaluate_shared_net_connectivity",
    "parse_spice_subcircuits",
    "run_xschem_schematic_netlist",
]
