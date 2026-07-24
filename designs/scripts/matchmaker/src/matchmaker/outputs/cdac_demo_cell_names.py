"""Canonical generated-cell names for the reviewed GF180 CDAC demos.

These names define output-directory, GDS top-cell, extraction, and LVS identities.
Generators and verification targets must import them rather than duplicate literals.
"""

GF180_CDAC_BASE_TRANSMISSION_GATE_DEMO_CELL_NAME = (
    "gf180_cdac_base_transmission_gate_demo"
)
GF180_CDAC_B0_REFERENCE_SELECTOR_DEMO_CELL_NAME = (
    "gf180_cdac_b0_reference_selector_demo"
)

__all__ = [
    "GF180_CDAC_BASE_TRANSMISSION_GATE_DEMO_CELL_NAME",
    "GF180_CDAC_B0_REFERENCE_SELECTOR_DEMO_CELL_NAME",
]
