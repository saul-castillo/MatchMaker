v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 220 70 280 70 {lab=GND}
N 220 50 400 50 {lab=OUTP}
N 400 -60 400 50 {lab=OUTP}
N 220 30 310 30 {lab=OUTN}
N 310 -60 310 30 {lab=OUTN}
N -60 -150 -60 -120 {lab=INP}
N -110 -150 -60 -150 {lab=INP}
N -110 -150 -110 50 {lab=INP}
N -110 50 -80 50 {lab=INP}
N -130 30 -80 30 {lab=INN}
N -130 -140 -130 30 {lab=INN}
N -130 -140 70 -140 {lab=INN}
N 70 -140 70 -120 {lab=INN}
N 220 90 250 90 {lab=TAIL}
N 280 70 430 70 {lab=GND}
N 250 90 470 90 {lab=TAIL}
N 500 20 500 90 {lab=GND}
C {libs/core_matchmaker/nmos_diff_pair/matched_nmos_diffpair_4u.sym} 70 60 0 0 {name=x1}
C {vsource.sym} 190 -90 0 0 {name=VDD value=3.3 savecurrent=false}
C {vdd.sym} 190 -120 0 0 {name=l2 lab=VDD}
C {vsource.sym} 70 -90 0 0 {name=VINN value=1.65 savecurrent=false}
C {vsource.sym} -60 -90 0 0 {name=VINP value=1.65 savecurrent=false}
C {res.sym} 310 -90 0 0 {name=RLOADN
value=68k
footprint=1206
device=resistor
m=1}
C {res.sym} 400 -90 0 0 {name=RLOADP
value=68k
footprint=1206
device=resistor
m=1}
C {vdd.sym} 310 -120 0 0 {name=l7 lab=VDD}
C {vdd.sym} 400 -120 0 0 {name=l8 lab=VDD}
C {gnd.sym} -60 -60 0 0 {name=l1 lab=GND}
C {gnd.sym} 70 -60 0 0 {name=l3 lab=GND}
C {gnd.sym} 190 -60 0 0 {name=l4 lab=GND}
C {gnd.sym} 430 70 3 0 {name=l5 lab=GND}
C {lab_pin.sym} 310 10 0 0 {name=p1 sig_type=std_logic lab=OUTN}
C {lab_pin.sym} 400 10 0 0 {name=p2 sig_type=std_logic lab=OUTP}
C {lab_pin.sym} -130 30 0 0 {name=p3 sig_type=std_logic lab=INN}
C {lab_pin.sym} -110 50 0 0 {name=p4 sig_type=std_logic lab=INP}
C {symbols/nfet_03v3.sym} 500 110 3 0 {name=MTAIL
L=0.28u
W=0.22u
nf=1
m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0
model=nfet_03v3
spiceprefix=X
}
C {gnd.sym} 500 20 2 0 {name=l6 lab=GND}
C {vsource.sym} 500 160 0 0 {name=VBIAS value=1.4 savecurrent=false}
C {gnd.sym} 530 90 3 0 {name=l9 lab=GND}
C {lab_pin.sym} 290 90 3 0 {name=p5 sig_type=std_logic lab=TAIL}
C {gnd.sym} 500 190 0 0 {name=l10 lab=GND}
C {code_shown.sym} -880 -140 0 0 {name=s2 only_toplevel=false value=
".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical

.control
save all
op
print v(outp) v(outn) v(tail) v(inp) v(inn)
print -i(VDD)
.endc"}
C {code_shown.sym} -870 -370 0 0 {name=s1 only_toplevel=false value=
".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical

.control
save all
dc VBIAS 0.3 1.5 0.01
plot i(VDD)
plot v(outp)
plot v(outn)
.endc"}
C {code_shown.sym} -880 80 0 0 {name=s3 only_toplevel=false value=
".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical

.control
save all
dc VINP 1.2 2.1 0.005
plot v(outp) v(outn)
.endc"}
C {code_shown.sym} -890 270 0 0 {name=s4 only_toplevel=false value=
".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical

.control
save all
dc VINP 1.2 2.1 0.005
plot (3.3-v(outp))/68k (3.3-v(outn))/68k
plot -i(VDD)
.endc"}
C {code_shown.sym} -890 480 0 0 {name=s5 only_toplevel=false value=
".include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical

.control
save all
dc VINP 1.2 2.1 0.005
plot v(tail)
.endc"}
