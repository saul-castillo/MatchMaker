v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -980 -80 -980 -60 {lab=#net1}
N -980 -80 -610 -80 {lab=#net1}
N -1050 -100 -610 -100 {lab=GND}
N -1050 -100 -1050 0 {lab=GND}
N -1120 -120 -1120 -60 {lab=#net2}
N -1120 -120 -610 -120 {lab=#net2}
N 150 -120 190 -120 {lab=VOUT}
N -330 320 -330 450 {lab=B3}
N -440 540 -440 670 {lab=B2}
N -680 980 -680 1110 {lab=B0}
N -640 610 -640 1020 {lab=#net3}
N -180 120 -180 140 {lab=#net4}
N -180 120 -150 120 {lab=#net4}
N -220 100 -220 230 {lab=RST}
N -220 100 -150 100 {lab=RST}
N -410 -80 -150 -80 {lab=#net1}
N -410 -60 -150 -60 {lab=B0}
N -410 -40 -150 -40 {lab=#net3}
N -430 -20 -150 -20 {lab=B1}
N -430 -0 -150 -0 {lab=#net5}
N -610 -120 -150 -120 {lab=#net2}
N -610 -100 -150 -100 {lab=GND}
N -610 -80 -410 -80 {lab=#net1}
N -630 -60 -410 -60 {lab=B0}
N -630 -40 -410 -40 {lab=#net3}
N -550 650 -550 890 {lab=B1}
N -290 80 -290 360 {lab=#net6}
N -290 80 -150 80 {lab=#net6}
N -330 60 -150 60 {lab=B3}
N -330 60 -330 320 {lab=B3}
N -400 40 -400 580 {lab=#net7}
N -400 40 -150 40 {lab=#net7}
N -440 20 -150 20 {lab=B2}
N -440 20 -440 540 {lab=B2}
N -550 -20 -550 650 {lab=B1}
N -550 -20 -430 -20 {lab=B1}
N -510 0 -430 0 {lab=#net5}
N -510 0 -510 800 {lab=#net5}
N -640 -40 -640 610 {lab=#net3}
N -640 -40 -630 -40 {lab=#net3}
N -680 -60 -680 980 {lab=B0}
N -680 -60 -630 -60 {lab=B0}
C {vsource.sym} -980 -30 0 0 {name=VREF value=1.2 savecurrent=false}
C {gnd.sym} -1120 0 0 0 {name=l1 lab=GND}
C {gnd.sym} -1050 0 0 0 {name=l2 lab=GND}
C {lab_pin.sym} 190 -120 2 0 {name=p1 sig_type=std_logic lab=VOUT}
C {vsource.sym} -400 610 0 0 {name=VB2B value="PWL(0 1.8 87n 1.8 87.1n 0 97n 0 97.1n 1.8 107n 1.8 107.1n 0 117n 0 117.1n 1.8 127n 1.8 127.1n 0 137n 0 137.1n 1.8 147n 1.8 147.1n 0 157n 0 157.1n 1.8 247n 1.8 247.1n 0 257n 0 257.1n 1.8 267n 1.8 267.1n 0 277n 0 277.1n 1.8 287n 1.8 287.1n 0 297n 0 297.1n 1.8 307n 1.8 307.1n 0 317n 0 317.1n 1.8)" savecurrent=false}
C {vsource.sym} -440 700 0 0 {name=VB2 value="PWL(0 0 87n 0 87.1n 1.8 97n 1.8 97.1n 0 107n 0 107.1n 1.8 117n 1.8 117.1n 0 127n 0 127.1n 1.8 137n 1.8 137.1n 0 147n 0 147.1n 1.8 157n 1.8 157.1n 0 247n 0 247.1n 1.8 257n 1.8 257.1n 0 267n 0 267.1n 1.8 277n 1.8 277.1n 0 287n 0 287.1n 1.8 297n 1.8 297.1n 0 307n 0 307.1n 1.8 317n 1.8 317.1n 0)" savecurrent=false}
C {vsource.sym} -1120 -30 0 0 {name=VDD value=1.8 savecurrent=false}
C {gnd.sym} -330 510 0 0 {name=l5 lab=GND}
C {gnd.sym} -980 0 0 0 {name=l6 lab=GND}
C {gnd.sym} -290 420 0 0 {name=l7 lab=GND}
C {vsource.sym} -510 830 0 0 {name=VB1B value="PWL(0 1.8 47n 1.8 47.1n 0 57n 0 57.1n 1.8 67n 1.8 67.1n 0 77n 0 77.1n 1.8 127n 1.8 127.1n 0 137n 0 137.1n 1.8 147n 1.8 147.1n 0 157n 0 157.1n 1.8 207n 1.8 207.1n 0 217n 0 217.1n 1.8 227n 1.8 227.1n 0 237n 0 237.1n 1.8 287n 1.8 287.1n 0 297n 0 297.1n 1.8 307n 1.8 307.1n 0 317n 0 317.1n 1.8)" savecurrent=false}
C {vsource.sym} -550 920 0 0 {name=VB1 value="PWL(0 0 47n 0 47.1n 1.8 57n 1.8 57.1n 0 67n 0 67.1n 1.8 77n 1.8 77.1n 0 127n 0 127.1n 1.8 137n 1.8 137.1n 0 147n 0 147.1n 1.8 157n 1.8 157.1n 0 207n 0 207.1n 1.8 217n 1.8 217.1n 0 227n 0 227.1n 1.8 237n 1.8 237.1n 0 287n 0 287.1n 1.8 297n 1.8 297.1n 0 307n 0 307.1n 1.8 317n 1.8 317.1n 0)" savecurrent=false}
C {gnd.sym} -440 730 0 0 {name=l8 lab=GND}
C {gnd.sym} -400 640 0 0 {name=l9 lab=GND}
C {vsource.sym} -640 1050 0 0 {name=VB0B value="PWL(0 1.8 27n 1.8 27.1n 0 37n 0 37.1n 1.8 67n 1.8 67.1n 0 77n 0 77.1n 1.8 107n 1.8 107.1n 0 117n 0 117.1n 1.8 147n 1.8 147.1n 0 157n 0 157.1n 1.8 187n 1.8 187.1n 0 197n 0 197.1n 1.8 227n 1.8 227.1n 0 237n 0 237.1n 1.8 267n 1.8 267.1n 0 277n 0 277.1n 1.8 307n 1.8 307.1n 0 317n 0 317.1n 1.8)" savecurrent=false}
C {vsource.sym} -680 1140 0 0 {name=VB0 value="PWL(0 0 27n 0 27.1n 1.8 37n 1.8 37.1n 0 67n 0 67.1n 1.8 77n 1.8 77.1n 0 107n 0 107.1n 1.8 117n 1.8 117.1n 0 147n 0 147.1n 1.8 157n 1.8 157.1n 0 187n 0 187.1n 1.8 197n 1.8 197.1n 0 227n 0 227.1n 1.8 237n 1.8 237.1n 0 267n 0 267.1n 1.8 277n 1.8 277.1n 0 307n 0 307.1n 1.8 317n 1.8 317.1n 0)" savecurrent=false}
C {gnd.sym} -680 1170 0 0 {name=l10 lab=GND}
C {gnd.sym} -640 1080 0 0 {name=l11 lab=GND}
C {code_shown.sym} 300 -410 0 0 {name=s1 only_toplevel=false value=
".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice cap_mim
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice mimcap_typical

.control
save all
tran 50p 320n

meas tran v0  find v(vout) at=15n
meas tran v1  find v(vout) at=35n
meas tran v2  find v(vout) at=55n
meas tran v3  find v(vout) at=75n
meas tran v4  find v(vout) at=95n
meas tran v5  find v(vout) at=115n
meas tran v6  find v(vout) at=135n
meas tran v7  find v(vout) at=155n
meas tran v8  find v(vout) at=175n
meas tran v9  find v(vout) at=195n
meas tran v10 find v(vout) at=215n
meas tran v11 find v(vout) at=235n
meas tran v12 find v(vout) at=255n
meas tran v13 find v(vout) at=275n
meas tran v14 find v(vout) at=295n
meas tran v15 find v(vout) at=315n

print v0 v1 v2 v3 v4 v5 v6 v7
print v8 v9 v10 v11 v12 v13 v14 v15
plot v(vout) v(rst)
.endc"}
C {lab_pin.sym} -440 20 0 0 {name=p2 sig_type=std_logic lab=B2}
C {lab_pin.sym} -680 -60 0 0 {name=p4 sig_type=std_logic lab=B0}
C {vsource.sym} -290 390 0 0 {name=VB3B value="PWL(0 1.8 167n 1.8 167.1n 0 177n 0 177.1n 1.8 187n 1.8 187.1n 0 197n 0 197.1n 1.8 207n 1.8 207.1n 0 217n 0 217.1n 1.8 227n 1.8 227.1n 0 237n 0 237.1n 1.8 247n 1.8 247.1n 0 257n 0 257.1n 1.8 267n 1.8 267.1n 0 277n 0 277.1n 1.8 287n 1.8 287.1n 0 297n 0 297.1n 1.8 307n 1.8 307.1n 0 317n 0 317.1n 1.8)" savecurrent=false}
C {vsource.sym} -330 480 0 0 {name=VB3 value="PWL(0 0 167n 0 167.1n 1.8 177n 1.8 177.1n 0 187n 0 187.1n 1.8 197n 1.8 197.1n 0 207n 0 207.1n 1.8 217n 1.8 217.1n 0 227n 0 227.1n 1.8 237n 1.8 237.1n 0 247n 0 247.1n 1.8 257n 1.8 257.1n 0 267n 0 267.1n 1.8 277n 1.8 277.1n 0 287n 0 287.1n 1.8 297n 1.8 297.1n 0 307n 0 307.1n 1.8 317n 1.8 317.1n 0)" savecurrent=false}
C {gnd.sym} -220 290 0 0 {name=l3 lab=GND}
C {gnd.sym} -180 200 0 0 {name=l12 lab=GND}
C {lab_pin.sym} -330 60 0 0 {name=B3 sig_type=std_logic lab=B3}
C {vsource.sym} -180 170 0 0 {name=VRSTB value="PULSE(0 1.8 5n 100p 100p 14n 20n)" savecurrent=false}
C {vsource.sym} -220 260 0 0 {name=VRST value="PULSE(1.8 0 5n 100p 100p 14n 20n)" savecurrent=false}
C {gnd.sym} -550 950 0 0 {name=l4 lab=GND}
C {gnd.sym} -510 860 0 0 {name=l13 lab=GND}
C {lab_pin.sym} -220 100 0 0 {name=p5 sig_type=std_logic lab=RST}
C {lab_pin.sym} -550 -20 0 0 {name=p3 sig_type=std_logic lab=B1}
C {libs/core_matchmaker/7D_cdac_4b_banked/7D_cdac_4b_banked.sym} 0 0 0 0 {name=x1}
