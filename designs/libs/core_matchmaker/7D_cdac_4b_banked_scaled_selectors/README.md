# 4-bit banked CDAC with scaled selectors

`7D_cdac_4b_banked_scaled_selectors` is the current single-ended CDAC reference for MatchMaker. It prioritizes a clear, reusable hierarchy and a legal GF180 capacitor device over aggressive resolution or area optimization.

## Architecture

The CDAC contains 15 switched unit capacitors and one termination capacitor. All top plates connect to `VOUT`.

| Bank | Weight | Unit capacitors | Selector |
| --- | ---: | ---: | --- |
| B0 | 1C | 1 | base `ref_sel_2to1` |
| B1 | 2C | 2 | `ref_sel_2to1_nmos8u_pmos16u` |
| B2 | 4C | 4 | `ref_sel_2to1_nmos16u_pmos32u` |
| B3 | 8C | 8 | `ref_sel_2to1_nmos32u_pmos64u` |
| termination | 1C | 1 | bottom plate tied directly to VSS |

Each selector contains two transmission gates: one connects its bank bottom plate to VREF and the other connects it to VSS. `Bn=1` selects VREF; `Bn=0` selects VSS. `BnB` is the required complementary control.

A base transmission gate connects `VOUT` to VSS during reset. `RST=1` asserts reset and `RSTB=0` supplies its complement.

## Interface

| Pin | Direction | Description |
| --- | --- | --- |
| `VDD` | input | 1.8 V switch supply in the current testbench |
| `VSS` | input | 0 V reference and reset level |
| `VREF` | input | 1.2 V full-scale reference in the current testbench |
| `B0:B3` | input | active-high code bits, B0 least significant |
| `B0B:B3B` | input | complements of `B0:B3` |
| `RST` | input | active-high output reset |
| `RSTB` | input | complement of `RST` |
| `VOUT` | output | single-ended capacitive DAC output |

Complement-generation logic is external and is not included in the transistor count.

## Devices

### Unit capacitor

All 16 units use the GF180 PDK symbol `cap_mim_2f0fF`:

```text
W=5u
L=5u
m=1
model=cap_mim_2f0fF
```

The 5 µm by 5 µm geometry is the minimum legal MIM top-plate geometry. From the nominal GF180 model area and perimeter terms, one unit is approximately 54.516 fF. Nominal array capacitance is therefore:

| Quantity | Units | Nominal capacitance |
| --- | ---: | ---: |
| B0 bank | 1 | 54.516 fF |
| B1 bank | 2 | 109.032 fF |
| B2 bank | 4 | 218.064 fF |
| B3 bank | 8 | 436.128 fF |
| Switched array | 15 | 817.740 fF |
| VSS termination | 1 | 54.516 fF |
| Total capacitance at `VOUT` | 16 | 872.256 fF |

These values are nominal schematic-model values, not post-layout extracted capacitances.

The capacitor top-plate pin connects to `VOUT`; the bottom-plate pin connects to its bank selector or, for the termination unit, directly to VSS.

### Transmission gates

All MOSFETs use `L=0.28u`, `nf=1`, the GF180 `nfet_03v3`/`pfet_03v3` models, and the following widths:

| Use | NMOS W | PMOS W |
| --- | ---: | ---: |
| reset and B0 | 4 µm | 8 µm |
| B1 | 8 µm | 16 µm |
| B2 | 16 µm | 32 µm |
| B3 | 32 µm | 64 µm |

The complete CDAC contains 18 MOSFET instances: four selectors at four transistors each plus the two-transistor reset gate. The previous selector-per-capacitor topology used 66 MOSFET instances under the same external-complement convention.

## Testbench

Use:

```text
designs/libs/tb_matchmaker/
  tb_7D_cdac_4b_banked_scaled_selectors/
    tb_7D_cdac_4b_banked_scaled_selectors.sch
```

The typical schematic simulation uses:

```text
VDD  = 1.8 V
VREF = 1.2 V
VSS  = 0 V
tran = 50 ps step, 320 ns stop
```

The testbench loads the GF180 typical MOS, MIM device, and typical MIM-corner libraries. It applies all 16 codes, resets between observations, and measures `VOUT` at 15 ns followed by 20 ns increments through 315 ns.

## Typical schematic-simulation result

The following results were obtained from the typical-corner schematic simulation described above. The output is monotonic across all 16 input codes.

| Code | VOUT (V) |
| ---: | ---: |
| 0 | -0.00226233 |
| 1 | 0.07184134 |
| 2 | 0.1459538 |
| 3 | 0.2200729 |
| 4 | 0.2941975 |
| 5 | 0.3683265 |
| 6 | 0.4424591 |
| 7 | 0.5165943 |
| 8 | 0.5907316 |
| 9 | 0.6648701 |
| 10 | 0.7390093 |
| 11 | 0.8131486 |
| 12 | 0.8872875 |
| 13 | 0.9614255 |
| 14 | 1.035562 |
| 15 | 1.109696 |

### Endpoint transfer characteristics

The ideal 4-bit transfer uses `VREF/16 = 75 mV` per LSB and has an ideal code-15 output of `15/16 × VREF = 1.125 V`. Endpoint correction uses the measured code-0 and code-15 values; consequently, endpoint INL is zero by definition.

| Metric | Result |
| --- | ---: |
| Zero-code offset | -2.26233 mV |
| Code-15 output | 1.109696 V |
| Measured endpoint span, code 0 to code 15 | 1.11195833 V |
| Endpoint LSB | 74.130555 mV |
| Ideal LSB for 1.2 V/16 | 75 mV |
| Endpoint gain error, based on transfer span | -1.159260% |
| Code-15 absolute error relative to 1.125 V | -15.304 mV (-1.360356%) |
| Minimum code step | 74.10367 mV |
| Maximum code step | 74.13930 mV |
| Maximum absolute DNL | 0.000363 LSB |
| Maximum absolute INL | 0.000863 LSB |

DNL and INL use the endpoint LSB and an endpoint-corrected line between codes 0 and 15:

```text
LSBendpoint = (VOUT[15] - VOUT[0]) / 15
DNL[k]      = (VOUT[k] - VOUT[k-1]) / LSBendpoint - 1
INL[k]      = (VOUT[k] - (VOUT[0] + k*LSBendpoint)) / LSBendpoint
```

| Code | VOUT (V) | Step (mV) | DNL (LSB) | INL (LSB) |
| ---: | ---: | ---: | ---: | ---: |
| 0 | -0.00226233 | — | — | 0.000000 |
| 1 | 0.07184134 | 74.10367 | -0.000363 | -0.000363 |
| 2 | 0.14595380 | 74.11246 | -0.000244 | -0.000607 |
| 3 | 0.22007290 | 74.11910 | -0.000155 | -0.000761 |
| 4 | 0.29419750 | 74.12460 | -0.000080 | -0.000842 |
| 5 | 0.36832650 | 74.12900 | -0.000021 | -0.000863 |
| 6 | 0.44245910 | 74.13260 | 0.000028 | -0.000835 |
| 7 | 0.51659430 | 74.13520 | 0.000063 | -0.000772 |
| 8 | 0.59073160 | 74.13730 | 0.000091 | -0.000681 |
| 9 | 0.66487010 | 74.13850 | 0.000107 | -0.000574 |
| 10 | 0.73900930 | 74.13920 | 0.000117 | -0.000458 |
| 11 | 0.81314860 | 74.13930 | 0.000118 | -0.000340 |
| 12 | 0.88728750 | 74.13890 | 0.000113 | -0.000227 |
| 13 | 0.96142550 | 74.13800 | 0.000100 | -0.000127 |
| 14 | 1.03556200 | 74.13650 | 0.000080 | -0.000046 |
| 15 | 1.10969600 | 74.13400 | 0.000046 | 0.000000 |

The reported linearity values are calculated from the printed ngspice samples and inherit their displayed precision. They describe nominal schematic behavior only; capacitor mismatch and extracted parasitics are not represented.

## Interpretation and limitations

The typical schematic simulation is monotonic and shows repeatable reset and settling with the scaled selectors. Relative to the earlier 20 fF ideal-capacitor model, the larger physical MIM capacitance reduces the voltage disturbance produced by a given amount of switch charge injection. It also increases capacitive load, switching energy, reference-current demand, and the settling burden on the switches and any future reference driver.

This result does not establish silicon accuracy. All capacitor instances currently use identical nominal models; no extracted interconnect parasitics, capacitor mismatch, reference-source impedance, PVT sweep, Monte Carlo analysis, DRC, or LVS result is included. These remain required before physical signoff.

For the current review deadline this topology and sizing are frozen. Future area optimization may reduce selector widths only after worst-case settling is measured at process, voltage, and temperature corners.
