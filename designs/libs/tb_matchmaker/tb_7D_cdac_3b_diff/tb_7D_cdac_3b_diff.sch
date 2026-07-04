v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -520 -40 -520 -20 {lab=#net1}
N -520 -40 -150 -40 {lab=#net1}
N -590 -60 -150 -60 {lab=GND}
N -590 -60 -590 40 {lab=GND}
N -660 -80 -660 -20 {lab=#net2}
N -660 -80 -150 -80 {lab=#net2}
N 190 -60 190 -30 {lab=VOUTN}
N 150 -80 190 -80 {lab=VOUTP}
N -180 80 -180 100 {lab=#net3}
N -180 80 -150 80 {lab=#net3}
N -220 60 -150 60 {lab=B2}
N -220 60 -220 190 {lab=B2}
N -330 210 -330 340 {lab=B1}
N -440 370 -440 500 {lab=B0}
N -290 40 -290 250 {lab=#net4}
N -290 40 -150 40 {lab=#net4}
N -330 20 -150 20 {lab=B1}
N -330 20 -330 210 {lab=B1}
N -400 -0 -400 410 {lab=#net5}
N -400 -0 -150 -0 {lab=#net5}
N -440 -20 -150 -20 {lab=B0}
N -440 -20 -440 370 {lab=B0}
N 150 -60 190 -60 {lab=VOUTN}
N 190 -80 280 -80 {lab=VOUTP}
N 280 -80 280 -30 {lab=VOUTP}
C {vsource.sym} -520 10 0 0 {name=VREF value=1.2 savecurrent=false}
C {gnd.sym} -660 40 0 0 {name=l1 lab=GND}
C {gnd.sym} -590 40 0 0 {name=l2 lab=GND}
C {res.sym} 190 0 0 0 {name=RLEAKN
value=10G
footprint=1206
device=resistor
m=1}
C {vsource.sym} 190 60 0 0 {name=VCM value=1.2 savecurrent=false}
C {gnd.sym} 190 90 0 0 {name=l4 lab=GND}
C {lab_pin.sym} 160 -80 1 0 {name=p1 sig_type=std_logic lab=VOUTP}
C {vsource.sym} -180 130 0 0 {name=VB2B value="PULSE(1.8 0 80n 100p 100p 80n 160n" savecurrent=false}
C {vsource.sym} -220 220 0 0 {name=VB2 value="PULSE(0 1.8 80n 100p 100p 80n 160n)" savecurrent=false}
C {vsource.sym} -660 10 0 0 {name=VDD value=1.8 savecurrent=false}
C {gnd.sym} -220 250 0 0 {name=l5 lab=GND}
C {gnd.sym} -520 40 0 0 {name=l6 lab=GND}
C {gnd.sym} -180 160 0 0 {name=l7 lab=GND}
C {vsource.sym} -290 280 0 0 {name=VB1B value="PULSE(1.8 0 40n 100p 100p 40n 80n" savecurrent=false}
C {vsource.sym} -330 370 0 0 {name=VB1 value="PULSE(0 1.8 40n 100p 100p 40n 80n)" savecurrent=false}
C {gnd.sym} -330 400 0 0 {name=l8 lab=GND}
C {gnd.sym} -290 310 0 0 {name=l9 lab=GND}
C {vsource.sym} -400 440 0 0 {name=VB0B value="PULSE(1.8 0 20n 100p 100p 20n 40n" savecurrent=false}
C {vsource.sym} -440 530 0 0 {name=VB0 value="PULSE(0 1.8 20n 100p 100p 20n 40n)" savecurrent=false}
C {gnd.sym} -440 560 0 0 {name=l10 lab=GND}
C {gnd.sym} -400 470 0 0 {name=l11 lab=GND}
C {code_shown.sym} 90 160 0 0 {name=s1 only_toplevel=false value=
".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical

.control
save all
tran 50p 180n
plot v(voutp)-v(voutn)
.endc"}
C {lab_pin.sym} -220 60 0 0 {name=p2 sig_type=std_logic lab=B2}
C {lab_pin.sym} -330 20 0 0 {name=p3 sig_type=std_logic lab=B1}
C {lab_pin.sym} -440 220 0 0 {name=p4 sig_type=std_logic lab=B0}
C {libs/core_matchmaker/7d_cdac_3b_diff/7D_cdac_3b_diff.sym} 0 0 0 0 {name=x1}
C {lab_pin.sym} 160 -60 3 0 {name=p5 sig_type=std_logic lab=VOUTN}
C {res.sym} 280 0 0 0 {name=RLEAKP
value=10G
footprint=1206
device=resistor
m=1}
C {vsource.sym} 280 60 0 0 {name=VCM1 value=1.2 savecurrent=false}
C {gnd.sym} 280 90 0 0 {name=l3 lab=GND}
