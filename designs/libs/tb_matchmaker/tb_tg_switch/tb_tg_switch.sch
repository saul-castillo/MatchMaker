v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 190 0 190 60 {lab=#net1}
N 150 -0 190 0 {lab=#net1}
N 150 -20 250 -20 {lab=GND}
N 250 -20 250 60 {lab=GND}
N 150 -40 310 -40 {lab=IN}
N 310 -40 310 60 {lab=IN}
N -290 -40 -290 60 {lab=#net2}
N -290 -40 -150 -40 {lab=#net2}
N -210 -20 -150 -20 {lab=#net3}
N -210 -20 -210 60 {lab=#net3}
N 150 20 390 20 {lab=OUT}
N 390 20 390 60 {lab=OUT}
N 390 20 460 20 {lab=OUT}
N 460 20 460 60 {lab=OUT}
C {libs/core_matchmaker/tg_switch/tg_switch.sym} 0 -10 0 0 {name=x1}
C {vsource.sym} 190 90 0 0 {name=VDD value=1.8 savecurrent=false}
C {gnd.sym} 190 120 0 0 {name=l1 lab=GND}
C {gnd.sym} 250 60 0 0 {name=l2 lab=GND}
C {vsource.sym} 310 90 0 0 {name=VIN value=0.9 savecurrent=false}
C {gnd.sym} 310 120 0 0 {name=l3 lab=GND}
C {vsource.sym} -290 90 0 0 {name=VCTRL value=1.8 savecurrent=false}
C {vsource.sym} -210 90 0 0 {name=VCTRLB value=0 savecurrent=false}
C {gnd.sym} -210 120 0 0 {name=l4 lab=GND}
C {gnd.sym} -290 120 0 0 {name=l5 lab=GND}
C {capa.sym} 390 90 0 0 {name=CLOAD
m=1
value=20f
footprint=1206
device="ceramic capacitor"}
C {res.sym} 460 90 0 0 {name=RLEAK
value=100k
footprint=1206
device=resistor
m=1}
C {gnd.sym} 390 120 0 0 {name=l6 lab=GND}
C {gnd.sym} 460 120 0 0 {name=l7 lab=GND}
C {code_shown.sym} -310 200 0 0 {name=s1 only_toplevel=false value=
".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical

.control
save all
dc VIN 0 1.8 0.01
plot v(in) v(out)
.endc"}
C {lab_pin.sym} 310 -40 2 0 {name=p1 sig_type=std_logic lab=IN}
C {lab_pin.sym} 460 20 2 0 {name=p2 sig_type=std_logic lab=OUT}
