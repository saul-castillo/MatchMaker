v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -50 40 -30 40 {lab=VOUT}
N -30 40 -30 450 {lab=VOUT}
N -30 450 810 450 {lab=VOUT}
N 350 160 370 160 {lab=VOUT}
N 370 160 370 450 {lab=VOUT}
N 370 40 370 160 {lab=VOUT}
N 350 40 370 40 {lab=VOUT}
N 770 40 790 40 {lab=VOUT}
N 790 40 790 450 {lab=VOUT}
N 770 160 790 160 {lab=VOUT}
N 770 280 790 280 {lab=VOUT}
N 770 400 790 400 {lab=VOUT}
N -50 -40 -30 -40 {lab=VREF}
N 390 -90 390 -40 {lab=VREF}
N 350 -40 390 -40 {lab=VREF}
N 390 -40 390 80 {lab=VREF}
N 350 80 390 80 {lab=VREF}
N -30 -40 -10 -40 {lab=VREF}
N -10 -90 -10 -40 {lab=VREF}
N -10 -90 390 -90 {lab=VREF}
N 390 -90 810 -90 {lab=VREF}
N 810 -90 810 -40 {lab=VREF}
N 770 -40 810 -40 {lab=VREF}
N 810 -40 810 320 {lab=VREF}
N 770 320 810 320 {lab=VREF}
N 770 200 810 200 {lab=VREF}
N 770 80 810 80 {lab=VREF}
N -60 -90 -10 -90 {lab=VREF}
N -60 -110 410 -110 {lab=VSS}
N 410 -110 410 -20 {lab=VSS}
N 350 -20 410 -20 {lab=VSS}
N -50 -20 10 -20 {lab=VSS}
N 10 -110 10 -20 {lab=VSS}
N 410 -20 410 100 {lab=VSS}
N 350 100 410 100 {lab=VSS}
N 770 -20 830 -20 {lab=VSS}
N 830 -20 830 340 {lab=VSS}
N 770 340 830 340 {lab=VSS}
N 770 220 830 220 {lab=VSS}
N 770 100 830 100 {lab=VSS}
N -50 0 -0 -0 {lab=VDD}
N -0 -130 -0 0 {lab=VDD}
N -60 -130 -0 -130 {lab=VDD}
N -0 -130 400 -130 {lab=VDD}
N 400 -130 400 -0 {lab=VDD}
N 350 0 400 0 {lab=VDD}
N 400 -0 400 120 {lab=VDD}
N 350 120 400 120 {lab=VDD}
N 400 -130 820 -130 {lab=VDD}
N 770 0 820 0 {lab=VDD}
N 820 -0 820 360 {lab=VDD}
N 770 360 820 360 {lab=VDD}
N 770 240 820 240 {lab=VDD}
N 770 120 820 120 {lab=VDD}
N 30 -20 50 -20 {lab=B1B}
N 30 -20 30 240 {lab=B1B}
N 30 100 50 100 {lab=B1B}
N 20 -40 50 -40 {lab=B1}
N 20 -40 20 240 {lab=B1}
N 20 80 50 80 {lab=B1}
N 450 -20 470 -20 {lab=B2B}
N 450 -20 450 380 {lab=B2B}
N 450 100 470 100 {lab=B2B}
N 450 220 470 220 {lab=B2B}
N 450 340 470 340 {lab=B2B}
N 440 -40 470 -40 {lab=B2}
N 440 -40 440 380 {lab=B2}
N 440 320 470 320 {lab=B2}
N 440 200 470 200 {lab=B2}
N 440 80 470 80 {lab=B2}
N 820 -130 820 -0 {lab=VDD}
N 830 -110 830 -20 {lab=VSS}
N 800 -110 830 -110 {lab=VSS}
N 410 -110 800 -110 {lab=VSS}
C {libs/core_matchmaker/7D_cdac_unit_cell/7D_cdac_unit_cell.sym} -200 0 0 0 {name=x1}
C {libs/core_matchmaker/7D_cdac_unit_cell/7D_cdac_unit_cell.sym} 200 0 0 0 {name=x2}
C {libs/core_matchmaker/7D_cdac_unit_cell/7D_cdac_unit_cell.sym} 200 120 0 0 {name=x3}
C {libs/core_matchmaker/7D_cdac_unit_cell/7D_cdac_unit_cell.sym} 620 0 0 0 {name=x4}
C {libs/core_matchmaker/7D_cdac_unit_cell/7D_cdac_unit_cell.sym} 620 120 0 0 {name=x5}
C {libs/core_matchmaker/7D_cdac_unit_cell/7D_cdac_unit_cell.sym} 620 240 0 0 {name=x6}
C {libs/core_matchmaker/7D_cdac_unit_cell/7D_cdac_unit_cell.sym} 620 360 0 0 {name=x7}
C {iopin.sym} 810 450 0 0 {name=VOUT lab=VOUT}
C {ipin.sym} -60 -90 0 0 {name=VREF lab=VREF}
C {ipin.sym} -60 -110 0 0 {name=VSS lab=VSS}
C {ipin.sym} -60 -130 0 0 {name=VDD lab=VDD}
C {ipin.sym} -350 -20 0 0 {name=B0B lab=B0B}
C {ipin.sym} -350 -40 0 0 {name=B0 lab=B0}
C {ipin.sym} 20 240 3 0 {name=B1 lab=B1}
C {ipin.sym} 30 240 2 0 {name=B1B lab=B1B}
C {ipin.sym} 450 380 3 0 {name=B2B lab=B2B}
C {ipin.sym} 440 380 0 0 {name=B3 lab=B2}
