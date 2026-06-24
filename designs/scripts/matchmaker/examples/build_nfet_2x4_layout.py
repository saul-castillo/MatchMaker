from pathlib import Path
import shutil

DESIGNS_ROOT = Path("/foss/designs")

CELL_NAME = "nfet_2x4_centroid"
DESIGN_NAME = CELL_NAME

CELL_DIR = DESIGNS_ROOT / "libs" / "core_analog" / CELL_NAME

GDS_DIR = CELL_DIR / "gds"
NETLIST_DIR = CELL_DIR / "netlist"
REPORT_DIR = CELL_DIR / "reports"
DRC_DIR = REPORT_DIR / "drc"
LVS_DIR = REPORT_DIR / "lvs"

for path in (GDS_DIR, NETLIST_DIR, DRC_DIR, LVS_DIR):
    path.mkdir(parents=True, exist_ok=True)

FINAL_GDS = GDS_DIR / f"{CELL_NAME}.gds"
REF_NETLIST = NETLIST_DIR / f"{CELL_NAME}_ref_flat.spice"
DRC_REPORT = DRC_DIR / f"{CELL_NAME}_drc.lyrdb"
LVS_OUTPUT_DIR = LVS_DIR / f"{CELL_NAME}_lvs_result"

print("Cell directory:", CELL_DIR)
print("Final GDS:", FINAL_GDS)
print("Reference netlist:", REF_NETLIST)
print("DRC report:", DRC_REPORT)
print("LVS output directory:", LVS_OUTPUT_DIR)

#Begin building

import glayout
from glayout import gf180, nmos, rename_ports_by_orientation, straight_route, tapring, via_stack
from glayout.backend import Component, rectangle

gf180.activate()

#----

def snap(x):
    return float(gf180.snap_to_2xgrid(x))


def bbox_size(component):
    (xmin, ymin), (xmax, ymax) = component.bbox
    return float(xmax - xmin), float(ymax - ymin)


def make_unit(dummies):
    return nmos(
        pdk=gf180,
        width=3.0,
        length=None,
        fingers=1,
        multipliers=1,
        with_tie=False,
        with_dummy=dummies,
        with_dnwell=False,
        with_substrate_tap=False,
        dummy_routes=True,
        sd_route_topmet="met2",
        gate_route_topmet="met2",
        sd_route_left=True,
        sd_rmult=1,
        gate_rmult=1,
        interfinger_rmult=1,
    )


def build_port_map(device_refs):
    devices = dict(zip(("A0", "B0", "B1", "A1"), device_refs))
    port_map = {}

    for device_name, ref in devices.items():
        ports = dict(ref.ports.items())
        port_map[device_name] = {}

        for terminal in ("source", "drain", "gate"):
            prefix = f"multiplier_0_{terminal}_"
            matches = {
                name.removeprefix(prefix): port
                for name, port in ports.items()
                if name.startswith(prefix)
            }
            if not matches:
                raise RuntimeError(f"{device_name} has no ports beginning with {prefix!r}")

            port_map[device_name][terminal] = matches

    return devices, port_map


def place_via(top, via_cell, port):
    ref = top << via_cell
    ref.movex(float(port.center[0]))
    ref.movey(float(port.center[1]))
    return ref


def add_path(top, points, glayer, width):
    layer = gf180.get_glayer(glayer)

    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        if x1 != x2 and y1 != y2:
            raise ValueError("Only Manhattan segments are allowed.")

        size = (
            (abs(x2 - x1) + width, width)
            if y1 == y2
            else (width, abs(y2 - y1) + width)
        )

        ref = top << rectangle(size=size, layer=layer, centered=True)
        ref.movex((x1 + x2) / 2)
        ref.movey((y1 + y2) / 2)


def add_named_port(top, name, port, layer=None):
    top.add_port(
        name=name,
        center=tuple(map(float, port.center)),
        width=float(port.width),
        orientation=port.orientation,
        layer=layer or port.layer,
    )


def add_net_label(top, name, port):
    glayer = gf180.layer_to_glayer(port.layer)
    try:
        label_layer = gf180.get_glayer(f"{glayer}_label")
    except Exception:
        label_layer = port.layer

    top.add_label(
        text=name,
        position=tuple(map(float, port.center)),
        layer=label_layer,
    )

#---

unit_left = make_unit((True, False))
unit_right = make_unit((False, True))

w_left, h_left = bbox_size(unit_left)
w_right, h_right = bbox_size(unit_right)

x_pitch = max(w_left, w_right) + 2.0
y_pitch = max(h_left, h_right) + 2.0

top = Component(name=DESIGN_NAME)
device_refs = []
pattern = [["A0", "B0"], ["B1", "A1"]]

for row in range(2):
    for col in range(2):
        unit = unit_left if col == 0 else unit_right
        ref = top << unit

        if row == 0:
            ref = rename_ports_by_orientation(ref.mirror_y())

        x = (col - 0.5) * x_pitch
        y = (0.5 - row) * y_pitch
        ref.movex(x)
        ref.movey(y)
        device_refs.append(ref)

        print(f"{pattern[row][col]} at ({x:.3f}, {y:.3f})")

devices, port_map = build_port_map(device_refs)

print("\nPlaced common-centroid array:")
print("A0  B0")
print("B1  A1")

# Common source/tail net.
top << straight_route(
    pdk=gf180,
    edge1=port_map["A0"]["source"]["E"],
    edge2=port_map["B0"]["source"]["W"],
)

top << straight_route(
    pdk=gf180,
    edge1=port_map["B1"]["source"]["E"],
    edge2=port_map["A1"]["source"]["W"],
)

via23_tail = via_stack(pdk=gf180, glayer1="met2", glayer2="met3", centered=True)

x_top = (
    float(port_map["A0"]["source"]["E"].center[0])
    + float(port_map["B0"]["source"]["W"].center[0])
) / 2
y_top = float(port_map["A0"]["source"]["E"].center[1])

x_bot = (
    float(port_map["B1"]["source"]["E"].center[0])
    + float(port_map["A1"]["source"]["W"].center[0])
) / 2
y_bot = float(port_map["B1"]["source"]["E"].center[1])

via_top = top << via23_tail
via_top.movex(x_top)
via_top.movey(y_top)

via_bot = top << via23_tail
via_bot.movex(x_bot)
via_bot.movey(y_bot)

top << straight_route(
    pdk=gf180,
    edge1=via_top.ports["top_met_S"],
    edge2=via_bot.ports["top_met_N"],
)

print("TAIL connected on met3.")

#---

via23 = via_stack(pdk=gf180, glayer1="met2", glayer2="met3")
via24 = via_stack(pdk=gf180, glayer1="met2", glayer2="met4")

w3 = snap(gf180.get_grule("met3")["min_width"])
w4 = snap(gf180.get_grule("met4")["min_width"])
s3 = snap(gf180.get_grule("met3")["min_separation"])
s4 = snap(gf180.get_grule("met4")["min_separation"])

clearance = max(w3 + s3, w4 + s4)
outer_x = snap(
    max(abs(float(top.xmin)), abs(float(top.xmax)))
    + clearance
    + max(float(via23.xsize), float(via24.xsize)) / 2
)

source_top_y = float(port_map["A0"]["source"]["E"].center[1])
source_bot_y = float(port_map["B1"]["source"]["E"].center[1])
via_half = max(float(via23.ysize), float(via24.ysize)) / 2

y_upper = snap(source_top_y + via_half + clearance)
y_lower = snap(source_bot_y - via_half - clearance)

# DRAIN_A: A0 ↔ A1 on met3.
a0 = port_map["A0"]["drain"]["W"]
a1 = port_map["A1"]["drain"]["E"]

place_via(top, via23, a0)
place_via(top, via23, a1)

ax0, ay0 = map(float, a0.center)
ax1, ay1 = map(float, a1.center)

add_path(
    top,
    [(ax0, ay0), (-outer_x, ay0), (-outer_x, y_lower), (ax1, y_lower), (ax1, ay1)],
    "met3",
    w3,
)

# DRAIN_B: B0 ↔ B1 on met4.
b0 = port_map["B0"]["drain"]["E"]
b1 = port_map["B1"]["drain"]["W"]

place_via(top, via24, b0)
place_via(top, via24, b1)

bx0, by0 = map(float, b0.center)
bx1, by1 = map(float, b1.center)

add_path(
    top,
    [(bx0, by0), (outer_x, by0), (outer_x, y_upper), (bx1, y_upper), (bx1, by1)],
    "met4",
    w4,
)

print("DRAIN_A connected on met3.")
print("DRAIN_B connected on met4.")

#---

via23_gate = via_stack(pdk=gf180, glayer1="met2", glayer2="met3")
via24_gate = via_stack(pdk=gf180, glayer1="met2", glayer2="met4")

clearance = max(w3 + s3, w4 + s4)
via_half = max(float(via23_gate.ysize), float(via24_gate.ysize)) / 2

gate_x = snap(max(abs(float(top.xmin)), abs(float(top.xmax))) + clearance + via_half)
gate_y_top = snap(float(top.ymax) + clearance + via_half)
gate_y_bot = snap(float(top.ymin) - clearance - via_half)

# GATE_A: A0 ↔ A1 on met3.
a0g = port_map["A0"]["gate"]["W"]
a1g = port_map["A1"]["gate"]["E"]

place_via(top, via23_gate, a0g)
place_via(top, via23_gate, a1g)

a0x, a0y = map(float, a0g.center)
a1x, a1y = map(float, a1g.center)

add_path(
    top,
    [
        (a0x, a0y),
        (a0x, gate_y_top),
        (-gate_x, gate_y_top),
        (-gate_x, gate_y_bot),
        (a1x, gate_y_bot),
        (a1x, a1y),
    ],
    "met3",
    w3,
)

# GATE_B: B0 ↔ B1 on met4.
b0g = port_map["B0"]["gate"]["E"]
b1g = port_map["B1"]["gate"]["W"]

place_via(top, via24_gate, b0g)
place_via(top, via24_gate, b1g)

b0x, b0y = map(float, b0g.center)
b1x, b1y = map(float, b1g.center)

add_path(
    top,
    [
        (b0x, b0y),
        (b0x, gate_y_top),
        (gate_x, gate_y_top),
        (gate_x, gate_y_bot),
        (b1x, gate_y_bot),
        (b1x, b1y),
    ],
    "met4",
    w4,
)

print("GATE_A connected on met3.")
print("GATE_B connected on met4.")

#---

(xmin, ymin), (xmax, ymax) = top.bbox
xmin, ymin, xmax, ymax = map(float, (xmin, ymin, xmax, ymax))

margin = snap(
    max(
        gf180.util_max_metal_seperation(),
        gf180.get_grule("active_diff", "active_tap")["min_separation"],
    )
    + gf180.get_grule("p+s/d", "active_tap")["min_enclosure"]
)

bulk_ring = tapring(
    pdk=gf180,
    enclosed_rectangle=(xmax - xmin + 2 * margin, ymax - ymin + 2 * margin),
    sdlayer="p+s/d",
    horizontal_glayer="met2",
    vertical_glayer="met1",
)

bulk_ref = top << bulk_ring
bulk_ref.movex((xmin + xmax) / 2)
bulk_ref.movey((ymin + ymax) / 2)
top.add_ports(bulk_ref.get_ports_list(), prefix="bulk_")

dummy_connections = {
    "A0": ("multiplier_0_dummy_L_gsdcon_top_met_W", "W_top_met_W"),
    "B1": ("multiplier_0_dummy_L_gsdcon_top_met_W", "W_top_met_W"),
    "B0": ("multiplier_0_dummy_R_gsdcon_top_met_W", "E_top_met_E"),
    "A1": ("multiplier_0_dummy_R_gsdcon_top_met_W", "E_top_met_E"),
}

for name, (dummy_port, ring_port) in dummy_connections.items():
    top << straight_route(
        pdk=gf180,
        edge1=devices[name].ports[dummy_port],
        edge2=bulk_ref.ports[ring_port],
        glayer2="met1",
    )

print("Bulk ring added and dummy gates tied to BULK.")

#---

interface_ports = {
    "GATE_A": port_map["A0"]["gate"]["W"],
    "GATE_B": port_map["B0"]["gate"]["E"],
    "DRAIN_A": port_map["A0"]["drain"]["W"],
    "DRAIN_B": port_map["B0"]["drain"]["E"],
    "TAIL": via_top.ports["top_met_N"],
    "BULK": bulk_ref.ports["W_top_met_W"],
}

for name, port in interface_ports.items():
    add_named_port(top, name, port)
    add_net_label(top, name, port)

print("Top-level ports:")
for name in interface_ports:
    p = top.ports[name]
    print(f"{name:8s} center={tuple(map(float, p.center))} layer={p.layer}")

#---

top.write_gds(str(FINAL_GDS))
print(f"Wrote GDS: {FINAL_GDS}")

#---

drc_ok = gf180.drc(top, str(DRC_REPORT))
print("DRC:", drc_ok)
if drc_ok:
    print("DRC: PASS")
else:
    print("DRC: FAIL")
    print(f"DRC report written to: {DRC_REPORT}")

#---

REF_NETLIST.write_text(f"""
* Reference schematic for 2x2 AB/BA NFET differential-pair input core

.subckt {DESIGN_NAME} GATE_A GATE_B DRAIN_A DRAIN_B TAIL BULK

* Active matched devices
XA0 DRAIN_A GATE_A TAIL BULK nfet_03v3 w=3u l=0.28u
XA1 DRAIN_A GATE_A TAIL BULK nfet_03v3 w=3u l=0.28u
XB0 DRAIN_B GATE_B TAIL BULK nfet_03v3 w=3u l=0.28u
XB1 DRAIN_B GATE_B TAIL BULK nfet_03v3 w=3u l=0.28u

* Perimeter dummy devices tied to bulk
XDA0 BULK BULK BULK BULK nfet_03v3 w=3u l=0.28u
XDA1 BULK BULK BULK BULK nfet_03v3 w=3u l=0.28u
XDB0 BULK BULK BULK BULK nfet_03v3 w=3u l=0.28u
XDB1 BULK BULK BULK BULK nfet_03v3 w=3u l=0.28u

.ends {DESIGN_NAME}
""".lstrip())

lvs_result = gf180.lvs_netgen(
    layout=str(FINAL_GDS),
    design_name=DESIGN_NAME,
    netlist=str(REF_NETLIST),
    output_file_path=str(LVS_OUTPUT_DIR),
    copy_intermediate_files=True,
    show_scripts=False,
)

print(lvs_result)

reports = sorted(LVS_OUTPUT_DIR.rglob("*_lvs.rpt"))
if not reports:
    raise FileNotFoundError(f"No LVS report found under {LVS_OUTPUT_DIR}")

report_text = reports[-1].read_text(errors="ignore")
lvs_ok = (
    "Netlists match uniquely" in report_text
    or "Final result: Circuits match uniquely" in report_text
)

print("LVS report:", reports[-1])
print("LVS match:", lvs_ok)
if lvs_ok:
    print("LVS: PASS")
else:
    print("LVS: FAIL")
    print(f"LVS report written to: {LVS_OUTPUT_DIR}")

#---