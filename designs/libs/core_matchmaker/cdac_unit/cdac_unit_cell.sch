v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 160 -20 260 -20 {lab=BOT}
C {libs/core_matchmaker/ref_sel_2to1/ref_sel_2to1.sym} 10 -50 0 0 {name=x1}
C {iopin.sym} 320 -20 0 0 {name=TOP lab=TOP}
C {iopin.sym} 160 -80 0 0 {name=VREF lab=VREF}
C {iopin.sym} 160 -60 0 0 {name=VSS lab=VSS}
C {iopin.sym} 160 -40 0 0 {name=VDD lab=VDD}
C {ipin.sym} -140 -80 0 0 {name=SEL lab=SEL}
C {ipin.sym} -140 -60 0 0 {name=SELB lab=SELB}
C {iopin.sym} 210 -20 1 0 {name=TOP1 lab=BOT}
C {symbols/cap_mim_2f0fF.sym} 290 -20 1 0 {name=C1
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
