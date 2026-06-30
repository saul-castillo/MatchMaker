v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 190 10 190 50 {lab=#net1}
N 150 10 190 10 {lab=#net1}
N 250 -10 250 50 {lab=GND}
N 150 -10 250 -10 {lab=GND}
N 310 -30 310 50 {lab=REF}
N 150 -30 310 -30 {lab=REF}
N 150 30 370 30 {lab=OUT}
N 370 30 460 30 {lab=OUT}
N 460 30 460 50 {lab=OUT}
N 390 30 390 50 {lab=OUT}
N -260 -30 -260 50 {lab=SEL}
N -260 -30 -150 -30 {lab=SEL}
N -180 -10 -150 -10 {lab=SELB}
N -180 -10 -180 50 {lab=SELB}
C {libs/core_matchmaker/ref_sel_2to1/ref_sel_2to1.sym} 0 0 0 0 {name=x1}
C {vsource.sym} 190 80 0 0 {name=VDD value=1.8 savecurrent=false}
C {vsource.sym} 310 80 0 0 {name=VREF value=1.8 savecurrent=false}
C {gnd.sym} 250 50 0 0 {name=l1 lab=GND}
C {capa.sym} 390 80 0 0 {name=C1
m=1
value=20f
footprint=1206
device="ceramic capacitor"}
C {res.sym} 460 80 0 0 {name=R1
value=1G
footprint=1206
device=resistor
m=1}
C {gnd.sym} 190 110 0 0 {name=l2 lab=GND}
C {gnd.sym} 310 110 0 0 {name=l3 lab=GND}
C {gnd.sym} 390 110 0 0 {name=l4 lab=GND}
C {gnd.sym} 460 110 0 0 {name=l5 lab=GND}
C {vsource.sym} -180 80 0 0 {name=VSELB value="PULSE(1.8 0 1n 100p 100p 10n 20n)" savecurrent=false}
C {vsource.sym} -260 80 0 0 {name=VSEL value="PULSE(0 1.8 1n 100p 100p 10n 20n)" savecurrent=false}
C {gnd.sym} -180 110 0 0 {name=l6 lab=GND}
C {gnd.sym} -260 110 0 0 {name=l7 lab=GND}
C {code_shown.sym} -250 180 0 0 {name=s1 only_toplevel=false value=
".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical

.control
save all
tran 10p 50n
plot v(sel) 
plot v(selb) 
plot v(out)
plot v(ref)
plot i(VREF) i(VDD)
.endc"}
C {lab_pin.sym} 310 -30 2 0 {name=p2 sig_type=std_logic lab=REF}
C {lab_pin.sym} 460 30 2 0 {name=p3 sig_type=std_logic lab=OUT}
C {lab_pin.sym} -260 -30 0 0 {name=p1 sig_type=std_logic lab=SEL}
C {lab_pin.sym} -180 -10 0 0 {name=p4 sig_type=std_logic lab=SELB}
