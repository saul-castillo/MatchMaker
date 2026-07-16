v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 150 -90 190 -90 {lab=VSS}
N 170 -90 170 70 {lab=VSS}
N 150 70 170 70 {lab=VSS}
N 150 50 170 50 {lab=VSS}
N 150 -110 170 -110 {lab=VREF}
N 170 -110 190 -110 {lab=VREF}
N 150 -70 190 -70 {lab=VDD}
N 190 -70 190 90 {lab=VDD}
N 150 90 190 90 {lab=VDD}
N 210 -50 210 110 {lab=OUT}
N 150 -50 210 -50 {lab=OUT}
N 150 110 210 110 {lab=OUT}
N -170 -110 -170 70 {lab=SEL}
N -170 70 -150 70 {lab=SEL}
N -190 50 -150 50 {lab=SELB}
N -190 -90 -190 50 {lab=SELB}
N -190 -90 -150 -90 {lab=SELB}
N -190 -110 -150 -110 {lab=SEL}
C {iopin.sym} 190 -110 0 0 {name=p1 lab=VREF}
C {iopin.sym} 190 -90 0 0 {name=p2 lab=VSS}
C {iopin.sym} 190 -70 0 0 {name=p3 lab=VDD}
C {iopin.sym} 210 110 0 0 {name=p4 lab=OUT}
C {ipin.sym} -190 -110 0 0 {name=p5 lab=SEL}
C {ipin.sym} -190 -90 0 0 {name=p6 lab=SELB}
C {libs/core_matchmaker/7D_tg_switch/7D_tg_switch.sym} 0 -80 0 0 {name=x1}
C {libs/core_matchmaker/7D_tg_switch/7D_tg_switch.sym} 0 80 0 0 {name=x2}
