v {xschem version=3.4.7 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N -160 -0 -140 -0 {lab=CTRL}
N 130 -0 160 0 {lab=CTRLB}
N -170 -0 -160 0 {lab=CTRL}
N -100 -0 -60 0 {lab=VSS}
N 60 -0 90 -0 {lab=VDD}
N -100 -60 -100 -30 {lab=IN}
N 90 -60 90 -30 {lab=IN}
N -100 -60 90 -60 {lab=IN}
N -100 -60 -0 -60 {lab=IN}
N -0 -90 -0 -60 {lab=IN}
N -100 30 -100 50 {lab=OUT}
N -100 50 90 50 {lab=OUT}
N 90 30 90 50 {lab=OUT}
N -0 50 0 80 {lab=OUT}
C {symbols/nfet_03v3.sym} -120 0 0 0 {name=M1
L=0.28u
W=4u
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
C {symbols/pfet_03v3.sym} 110 0 2 0 {name=M2
L=0.28u
W=8u
nf=1
m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X
}
C {iopin.sym} 0 -90 0 0 {name=IN lab=IN}
C {iopin.sym} 0 80 0 0 {name=OUT lab=OUT}
C {iopin.sym} -60 0 0 0 {name=VSS lab=VSS}
C {iopin.sym} 60 0 2 0 {name=VDD lab=VDD}
C {ipin.sym} -170 0 0 0 {name=CTRL lab=CTRL}
C {ipin.sym} 160 0 2 0 {name=CTRLB lab=CTRLB}
