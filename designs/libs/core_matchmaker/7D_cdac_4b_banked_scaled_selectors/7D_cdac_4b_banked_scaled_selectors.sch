v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 170 -160 230 -160 {lab=#net1}
N 170 70 230 70 {lab=#net2}
N 230 70 360 70 {lab=#net2}
N 170 260 230 260 {lab=#net3}
N 230 260 360 260 {lab=#net3}
N 430 260 490 260 {lab=#net3}
N 490 260 620 260 {lab=#net3}
N 360 260 430 260 {lab=#net3}
N 170 490 230 490 {lab=#net4}
N 230 490 360 490 {lab=#net4}
N 430 490 490 490 {lab=#net4}
N 490 490 620 490 {lab=#net4}
N 360 490 430 490 {lab=#net4}
N 690 490 750 490 {lab=#net4}
N 750 490 880 490 {lab=#net4}
N 950 490 1010 490 {lab=#net4}
N 1010 490 1140 490 {lab=#net4}
N 880 490 950 490 {lab=#net4}
N 620 490 690 490 {lab=#net4}
N 40 260 170 260 {lab=#net3}
N 40 490 170 490 {lab=#net4}
N 40 70 170 70 {lab=#net2}
N 40 -160 170 -160 {lab=#net1}
N 40 -220 60 -220 {lab=VREF}
N 60 -220 60 10 {lab=VREF}
N 40 10 60 10 {lab=VREF}
N 60 10 60 200 {lab=VREF}
N 40 200 60 200 {lab=VREF}
N 60 200 60 430 {lab=VREF}
N 40 430 60 430 {lab=VREF}
N 60 -300 60 -220 {lab=VREF}
N -20 -300 60 -300 {lab=VREF}
N -20 -320 80 -320 {lab=VSS}
N 80 -320 80 450 {lab=VSS}
N 40 450 80 450 {lab=VSS}
N 40 220 80 220 {lab=VSS}
N 40 30 80 30 {lab=VSS}
N 40 -200 80 -200 {lab=VSS}
N -20 -340 100 -340 {lab=VDD}
N 100 -340 100 470 {lab=VDD}
N 40 470 100 470 {lab=VDD}
N 40 240 100 240 {lab=VDD}
N 40 50 100 50 {lab=VDD}
N 40 -180 100 -180 {lab=VDD}
N 230 550 1140 550 {lab=VOUT}
N 230 320 620 320 {lab=VOUT}
N 620 320 1180 320 {lab=VOUT}
N 1180 320 1180 550 {lab=VOUT}
N 1140 550 1220 550 {lab=VOUT}
N 230 130 1180 130 {lab=VOUT}
N 1180 130 1180 320 {lab=VOUT}
N 230 -100 1180 -100 {lab=VOUT}
N 1180 -100 1180 130 {lab=VOUT}
N 80 -320 1180 -320 {lab=VSS}
N 1180 -320 1180 -180 {lab=VSS}
N 1180 -120 1180 -100 {lab=VOUT}
N 80 450 80 540 {lab=VSS}
N 40 540 80 540 {lab=VSS}
N 40 600 1180 600 {lab=VOUT}
N 1180 550 1180 600 {lab=VOUT}
N 100 470 100 580 {lab=VDD}
N 40 580 100 580 {lab=VDD}
N 80 540 80 560 {lab=VSS}
N 40 560 80 560 {lab=VSS}
C {libs/core_matchmaker/7D_tg_switch/7D_tg_switch.sym} -110 570 0 0 {name=x1}
C {libs/core_matchmaker/7D_ref_sel_2to1/7D_ref_sel_2to1.sym} -110 -190 0 0 {name=x2}
C {symbols/cap_mim_2f0fF.sym} 230 -130 0 0 {name=C1
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {symbols/cap_mim_2f0fF.sym} 230 100 0 0 {name=C2
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {symbols/cap_mim_2f0fF.sym} 360 100 0 0 {name=C3
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {symbols/cap_mim_2f0fF.sym} 230 290 0 0 {name=C4
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {symbols/cap_mim_2f0fF.sym} 360 290 0 0 {name=C5
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {symbols/cap_mim_2f0fF.sym} 480 290 0 0 {name=C6
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {symbols/cap_mim_2f0fF.sym} 620 290 0 0 {name=C7
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {symbols/cap_mim_2f0fF.sym} 230 520 0 0 {name=C8
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {symbols/cap_mim_2f0fF.sym} 360 520 0 0 {name=C9
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {symbols/cap_mim_2f0fF.sym} 490 520 0 0 {name=C10
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {symbols/cap_mim_2f0fF.sym} 620 520 0 0 {name=C11
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {symbols/cap_mim_2f0fF.sym} 750 520 0 0 {name=C12
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {symbols/cap_mim_2f0fF.sym} 880 520 0 0 {name=C13
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {symbols/cap_mim_2f0fF.sym} 1010 520 0 0 {name=C14
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {symbols/cap_mim_2f0fF.sym} 1140 520 0 0 {name=C15
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {ipin.sym} -260 -220 0 0 {name=B0 lab=B0}
C {ipin.sym} -260 -200 0 0 {name=B0B lab=B0B}
C {ipin.sym} -260 10 0 0 {name=B1 lab=B1}
C {ipin.sym} -260 30 0 0 {name=B1B lab=B1B}
C {ipin.sym} -260 200 0 0 {name=B2 lab=B2}
C {ipin.sym} -260 220 0 0 {name=B3 lab=B2B}
C {ipin.sym} -260 430 0 0 {name=B4 lab=B3}
C {ipin.sym} -260 450 0 0 {name=B5 lab=B3B}
C {ipin.sym} -20 -300 0 0 {name=VREF lab=VREF}
C {ipin.sym} -20 -320 0 0 {name=VSS lab=VSS}
C {ipin.sym} -20 -340 0 0 {name=VDD lab=VDD}
C {opin.sym} 1220 550 0 0 {name=VOUT lab=VOUT}
C {symbols/cap_mim_2f0fF.sym} 1180 -150 0 0 {name=C16
W=5u
L=5u
model=cap_mim_2f0fF
spiceprefix=X
m=1}
C {ipin.sym} -260 540 0 0 {name=RST lab=RST}
C {ipin.sym} -260 560 0 0 {name=RSTB lab=RSTB}
C {libs/core_matchmaker/7D_ref_sel_2to1_nmos16u_pmos32u/7D_ref_sel_2to1_nmos16u_pmos32u.sym} -110 230 0 0 {name=x3}
C {libs/core_matchmaker/7D_ref_sel_2to1_nmos32u_pmos64u/7D_ref_sel_2to1_nmos32u_pmos64u.sym} -110 460 0 0 {name=x4}
C {libs/core_matchmaker/7D_ref_sel_2to1_nmos8u_pmos16u/7D_ref_sel_2to1_nmos8u_pmos16u.sym} -110 40 0 0 {name=x5}
