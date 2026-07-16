# Core MatchMaker reference library

`core_matchmaker` contains hand-authored GF180/Xschem circuits used as reference structures for MatchMaker development. These cells define concrete hierarchy, device, matching, and routing targets; they are not generated-layout signoff artifacts.

## Cell index

| Cell | Purpose |
| --- | --- |
| `matched_nmos_diffpair_4u` | Matched NMOS differential-pair reference |
| `tg_switch` | Base transmission gate, NMOS 4 µm and PMOS 8 µm |
| `tg_switch_nmos8u_pmos16u` | 2× transmission gate for the 2C bank |
| `tg_switch_nmos16u_pmos32u` | 4× transmission gate for the 4C bank |
| `tg_switch_nmos32u_pmos64u` | 8× transmission gate for the 8C bank |
| `ref_sel_2to1` | VREF/VSS selector built from two transmission gates |
| `ref_sel_2to1_nmos8u_pmos16u` | 2× selector for the 2C bank |
| `ref_sel_2to1_nmos16u_pmos32u` | 4× selector for the 4C bank |
| `ref_sel_2to1_nmos32u_pmos64u` | 8× selector for the 8C bank |
| `cdac_unit_cell` | Legacy capacitor/selector unit cell |
| `7D_cdac_3b_single` | Legacy 3-bit single-ended CDAC |
| `7D_cdac_3b_diff` | Differential wrapper around two 3-bit single-ended CDACs |
| `7d_cdac_4b_single` | 4-bit unit-cell CDAC with one selector per capacitor |
| `7D_cdac_4b_banked` | 4-bit banked CDAC with unscaled shared selectors; retained for comparison |
| [`7D_cdac_4b_banked_scaled_selectors`](7D_cdac_4b_banked_scaled_selectors/README.md) | Current 4-bit review reference with bank-weight-scaled selectors |

## Current CDAC hierarchy

The review reference uses 16 identical minimum-geometry GF180 MIM capacitors:

- one switched unit for B0;
- two switched units for B1;
- four switched units for B2;
- eight switched units for B3;
- one termination unit tied to VSS.

Each bit bank shares one `ref_sel_2to1`-family selector. Selector transistor widths scale with the number of capacitors in the bank. This preserves comparable RC settling while reducing the top-level selector count from sixteen to four.

The associated simulation is in [`tb_matchmaker/tb_7D_cdac_4b_banked_scaled_selectors`](../tb_matchmaker/tb_7D_cdac_4b_banked_scaled_selectors/).

## Status boundary

The reference schematics have been simulated with the GF180 ngspice models. Layout generation, extracted-parasitic simulation, DRC, LVS, PVT corners, mismatch Monte Carlo, and reference-driver loading remain future work unless separately recorded as completed.
