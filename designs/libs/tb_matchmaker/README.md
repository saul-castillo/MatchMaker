# MatchMaker testbench library

`tb_matchmaker` contains top-level Xschem/ngspice verification setups for cells in `core_matchmaker`.

| Testbench | Device under test |
| --- | --- |
| `tb_matched_nmos_diffpair_4u` | `matched_nmos_diffpair_4u` |
| `tb_tg_switch` | base `tg_switch` |
| `tb_ref_sel_2to1` | base `ref_sel_2to1` |
| `tb_cdac_unit_cell` | legacy `cdac_unit_cell` |
| `tb_7D_cdac_3b_single` | `7D_cdac_3b_single` |
| `tb_7D_cdac_3b_diff` | `7D_cdac_3b_diff` |
| `tb_7D_cdac_4b_single` | selector-per-capacitor `7d_cdac_4b_single` |
| `tb_7D_cdac_4b_banked_scaled_selectors` | current banked/scaled 4-bit CDAC |

Simulation output files such as `.raw`, `.log`, and generated netlists are intentionally excluded from version control. Record reproducible conditions and reviewed numerical results in the corresponding core-cell README.
