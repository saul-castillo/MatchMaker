v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -170 40 -150 40 {lab=VDD}
N -170 -200 -170 40 {lab=VDD}
N -300 -180 -150 -180 {lab=VSS}
N -190 -180 -190 60 {lab=VSS}
N -190 60 -150 60 {lab=VSS}
N -210 80 -150 80 {lab=VREF}
N -210 -160 -210 80 {lab=VREF}
N -300 -160 -210 -160 {lab=VREF}
N -210 -160 -150 -160 {lab=VREF}
N -300 -140 -150 -140 {lab=B0}
N -230 -140 -230 120 {lab=B0}
N -230 120 -150 120 {lab=B0}
N -380 -120 -150 -120 {lab=B0B}
N -380 -140 -300 -140 {lab=B0}
N -250 -120 -250 100 {lab=B0B}
N -250 100 -150 100 {lab=B0B}
N -380 -100 -150 -100 {lab=B1}
N -270 -100 -270 160 {lab=B1}
N -270 160 -160 160 {lab=B1}
N -160 160 -150 160 {lab=B1}
N -290 140 -150 140 {lab=B1B}
N -290 -80 -290 140 {lab=B1B}
N -290 -80 -150 -80 {lab=B1B}
N -380 -80 -290 -80 {lab=B1B}
N -380 -60 -150 -60 {lab=B2}
N -310 -60 -310 200 {lab=B2}
N -310 200 -150 200 {lab=B2}
N -330 180 -150 180 {lab=xxx}
N -330 -40 -330 180 {lab=xxx}
N -330 -40 -150 -40 {lab=xxx}
N -380 -40 -330 -40 {lab=xxx}
N -300 -200 -150 -200 {lab=VDD}
C {libs/core_matchmaker/7D_cdac_3b_single/7D_cdac_3b_single.sym} 0 -120 0 0 {name=x1}
C {libs/core_matchmaker/7D_cdac_3b_single/7D_cdac_3b_single.sym} 0 120 0 0 {name=x2}
C {iopin.sym} 150 -200 0 0 {name=VOUTP lab=VOUTP}
C {iopin.sym} 150 40 0 0 {name=VOUTN lab=VOUTN}
C {ipin.sym} -300 -200 0 0 {name=VDD lab=VDD}
C {ipin.sym} -300 -180 0 0 {name=VSS lab=VSS}
C {ipin.sym} -300 -160 0 0 {name=VREF lab=VREF}
C {ipin.sym} -380 -140 0 0 {name=B0 lab=B0}
C {ipin.sym} -380 -120 0 0 {name=B0B lab=B0B}
C {ipin.sym} -380 -100 0 0 {name=B1 lab=B1}
C {ipin.sym} -380 -80 0 0 {name=B1B lab=B1B}
C {ipin.sym} -380 -60 0 0 {name=B2 lab=B2}
C {ipin.sym} -380 -40 0 0 {name=B2B lab=B2B}
