v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
P 4 1 -400 70 {}
N -620 30 -620 100 {lab=TAIL}
N -90 30 -90 100 {lab=TAIL}
N -620 100 -90 100 {lab=TAIL}
N -90 100 80 100 {lab=TAIL}
N 80 30 80 100 {lab=TAIL}
N 620 30 620 100 {lab=TAIL}
N 90 100 620 100 {lab=TAIL}
N 80 100 90 100 {lab=TAIL}
N -620 -0 -530 0 {lab=VSS}
N -810 -0 -710 -0 {lab=VSS}
N -710 -0 -710 60 {lab=VSS}
N -710 60 -520 60 {lab=VSS}
N -520 0 -520 60 {lab=VSS}
N -530 0 -520 0 {lab=VSS}
N -520 60 -0 60 {lab=VSS}
N -0 -0 -0 60 {lab=VSS}
N -90 -0 -0 -0 {lab=VSS}
N -260 -0 -180 0 {lab=VSS}
N -180 0 -180 60 {lab=VSS}
N -440 -0 -340 -0 {lab=VSS}
N -340 -0 -340 60 {lab=VSS}
N 530 0 530 60 {lab=VSS}
N 440 -0 530 -0 {lab=VSS}
N 80 -0 180 0 {lab=VSS}
N 180 -0 180 60 {lab=VSS}
N 260 -0 360 -0 {lab=VSS}
N 360 -0 360 60 {lab=VSS}
N 620 -0 700 0 {lab=VSS}
N 700 0 700 60 {lab=VSS}
N -830 60 -710 60 {lab=VSS}
N -440 30 -440 100 {lab=TAIL}
N -260 30 -260 100 {lab=TAIL}
N 260 30 260 100 {lab=TAIL}
N 440 30 440 100 {lab=TAIL}
N 620 100 770 100 {lab=TAIL}
N 770 30 770 100 {lab=TAIL}
N -670 100 -620 100 {lab=TAIL}
N -690 -0 -660 -0 {lab=INP}
N -690 -60 -690 -0 {lab=INP}
N -900 -60 -690 -60 {lab=INP}
N -690 -60 -400 -60 {lab=INP}
N -400 -60 -160 -60 {lab=INP}
N -160 -60 -160 -0 {lab=INP}
N -160 0 -130 -0 {lab=INP}
N -160 -60 10 -60 {lab=INP}
N 10 -60 10 0 {lab=INP}
N 10 0 40 0 {lab=INP}
N 10 -60 300 -60 {lab=INP}
N 300 -60 550 -60 {lab=INP}
N 550 -60 550 -0 {lab=INP}
N 550 0 580 0 {lab=INP}
N 520 60 700 60 {lab=VSS}
N 0 60 520 60 {lab=VSS}
N -860 -100 -500 -100 {lab=INN}
N -500 -100 -500 0 {lab=INN}
N -500 0 -480 -0 {lab=INN}
N -500 -100 -330 -100 {lab=INN}
N -330 -100 -330 -0 {lab=INN}
N -330 -0 -300 -0 {lab=INN}
N -330 -100 100 -100 {lab=INN}
N 100 -100 190 -100 {lab=INN}
N 190 -100 190 -0 {lab=INN}
N 190 -0 220 -0 {lab=INN}
N 190 -100 370 -100 {lab=INN}
N 370 -100 370 -0 {lab=INN}
N 370 -0 400 0 {lab=INN}
N -620 -140 -620 -30 {lab=xxx}
N -620 -140 -390 -140 {lab=xxx}
N -390 -140 -90 -140 {lab=xxx}
N -90 -140 -90 -30 {lab=xxx}
N -90 -140 80 -140 {lab=xxx}
N 80 -140 80 -30 {lab=xxx}
N 80 -140 620 -140 {lab=xxx}
N 620 -140 620 -30 {lab=xxx}
N 620 -140 710 -140 {lab=xxx}
N -440 -180 700 -180 {lab=OUTN}
N -440 -180 -440 -30 {lab=OUTN}
N -260 -180 -260 -30 {lab=OUTN}
N 440 -180 440 -30 {lab=OUTN}
N 260 -180 260 -30 {lab=OUTN}
N 730 0 730 100 {lab=TAIL}
N 770 100 860 100 {lab=TAIL}
N 860 10 860 90 {lab=TAIL}
N 860 90 860 100 {lab=TAIL}
N 860 0 860 10 {lab=TAIL}
N 770 -0 860 0 {lab=TAIL}
N 860 -60 860 0 {lab=TAIL}
N 770 -60 860 -60 {lab=TAIL}
N 770 -60 770 -30 {lab=TAIL}
N -710 -40 -710 -0 {lab=VSS}
N -810 -40 -710 -40 {lab=VSS}
N -810 -40 -810 -30 {lab=VSS}
N -810 30 -810 60 {lab=VSS}
N -880 -40 -810 -40 {lab=VSS}
N -880 -40 -880 -0 {lab=VSS}
N -880 -0 -850 -0 {lab=VSS}
C {symbols/nfet_03v3.sym} 60 0 0 0 {name=M_INP2
L=0.6u
W=1u
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
C {symbols/nfet_03v3.sym} -110 0 0 0 {name=M_INP1
L=0.6u
W=1u
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
C {symbols/nfet_03v3.sym} -280 0 0 0 {name=M_INN1
L=0.6u
W=1u
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
C {symbols/nfet_03v3.sym} -460 0 0 0 {name=M_INN0
L=0.6u
W=1u
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
C {symbols/nfet_03v3.sym} -640 0 0 0 {name=M_INP0
L=0.6u
W=1u
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
C {symbols/nfet_03v3.sym} -830 0 0 0 {name=DMY_L
L=0.6u
W=1u
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
C {symbols/nfet_03v3.sym} 240 0 0 0 {name=M_INN2
L=0.6u
W=1u
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
C {symbols/nfet_03v3.sym} 420 0 0 0 {name=M_INN3
L=0.6u
W=1u
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
C {symbols/nfet_03v3.sym} 600 0 0 0 {name=M_INP3
L=0.6u
W=1u
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
C {symbols/nfet_03v3.sym} 750 0 0 0 {name=DMY_R
L=0.6u
W=1u
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
C {iopin.sym} -670 100 2 0 {name=TAIL lab=TAIL}
C {iopin.sym} -830 60 2 0 {name=VSS lab=VSS}
C {ipin.sym} -860 -100 0 0 {name=INN lab=INN}
C {ipin.sym} -900 -60 0 0 {name=INP lab=INP}
C {opin.sym} 700 -180 0 0 {name=OUTN lab=OUTN}
C {opin.sym} 710 -140 0 0 {name=OUTP lab=OUTP}
