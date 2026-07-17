v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 150 10 250 10 {lab=#net1}
N 250 10 250 50 {lab=#net1}
N 370 -30 370 50 {lab=#net2}
N 150 -30 370 -30 {lab=#net2}
N 150 -10 310 -10 {lab=GND}
N 310 -10 310 50 {lab=GND}
N -280 -30 -280 50 {lab=SEL}
N -280 -30 -150 -30 {lab=SEL}
N -200 -10 -150 -10 {lab=SELB}
N -200 -10 -200 50 {lab=SELB}
N 150 50 180 50 {lab=TOP}
N 180 50 180 80 {lab=TOP}
C {res.sym} 180 110 0 0 {name=RTOP
value=1G
footprint=1206
device=resistor
m=1}
C {vsource.sym} 250 80 0 0 {name=VDD value=1.8 savecurrent=false}
C {gnd.sym} 310 50 0 0 {name=l2 lab=GND}
C {vsource.sym} 370 80 0 0 {name=VREF value=1.2 savecurrent=false}
C {gnd.sym} 250 110 0 0 {name=l3 lab=GND}
C {gnd.sym} 370 110 0 0 {name=l4 lab=GND}
C {vsource.sym} -200 80 0 0 {name=VSELB value="PULSE(1.8 0 1n 100p 100p 10n 20n)" savecurrent=false}
C {vsource.sym} -280 80 0 0 {name=VSEL value="PULSE(0 1.8 1n 100p 100p 10n 20n" savecurrent=false}
C {gnd.sym} -200 110 0 0 {name=l5 lab=GND}
C {gnd.sym} -280 110 0 0 {name=l6 lab=GND}
C {code_shown.sym} -300 190 0 0 {name=s1 only_toplevel=false value=
".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical

.control
save all
tran 10p 50n
plot v(sel) v(selb) v(bot)
.endc"}
C {lab_pin.sym} 180 80 2 0 {name=p1 sig_type=std_logic lab=TOP}
C {libs/core_matchmaker/7D_cdac_unit_cell/7D_cdac_unit_cell.sym} 0 10 0 0 {name=x1}
C {gnd.sym} 180 140 0 0 {name=l1 lab=GND}
C {lab_pin.sym} 150 30 2 0 {name=p2 sig_type=std_logic lab=BOT}
C {lab_pin.sym} -280 -30 0 0 {name=p3 sig_type=std_logic lab=SEL}
C {lab_pin.sym} -200 -10 0 0 {name=p4 sig_type=std_logic lab=SELB}
