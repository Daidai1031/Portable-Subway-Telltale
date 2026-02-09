import time
import ssl
import wifi
import socketpool
import adafruit_requests

import board
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_imageload
from digitalio import DigitalInOut, Direction, Pull
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.rect import Rect


# -----------------------------
# Config
# -----------------------------
KNOWN_NETWORKS = [
    ("RedRover",  None),     
    ("WhiteSky-Cornell", "57h5ssje"),
    ("ddr",   "dddddddd"),
]

def connect_priority_network(networks, scan_timeout_s=6):
    if wifi.radio.connected:
        return True
    # 1) Scan for available networks and remember seen SSIDs until timeout
    seen = set()
    start = time.monotonic()
    try:
        for net in wifi.radio.start_scanning_networks():
            try:
                seen.add(str(net.ssid))
            except Exception:
                pass
            if time.monotonic() - start > scan_timeout_s:
                break
    finally:
        wifi.radio.stop_scanning_networks()
    # 2) Try to connect to known networks in priority order, but only if they were seen in the scan
    for ssid, pwd in networks:
        if ssid not in seen:
            continue
        try:
            if pwd is None:
                wifi.radio.connect(ssid)
            else:
                wifi.radio.connect(ssid, pwd)
            return True
        except Exception as e:
            print(f"Connect failed: {ssid} -> {e}")    
    # 3) Fallback: try to connect to known networks in priority order, even if not seen in the scan (some networks may not broadcast SSID)
    for ssid, pwd in networks:
        try:
            if pwd is None:
                wifi.radio.connect(ssid)
            else:
                wifi.radio.connect(ssid, pwd)
            return True
        except Exception as e:
            print(f"Fallback failed: {ssid} -> {e}")

    return False

STATION_ID = "B06"  # Roosevelt Island
THRESHOLD_MIN = 7
THRESHOLD_ARRIVAL = 2

# Text/icon colors
COLOR_WAIT = 0xA0A0A0      # grey
COLOR_GO = 0x3236A6        # blue
COLOR_ARRIVAL = 0xFF6319   # orange
COLOR_TEXT = 0xFFFFFF      # normal text
COLOR_TEXT_DIM = 0x808080  # unselected text grey
COLOR_OUTLINE = 0x808080   # unselected circle outline

API_URL = f"https://subwayinfo.nyc/api/arrivals?station_id={STATION_ID}&limit=20"

API_INTERVAL = 15.0
UI_TICK = 0.05
BLINK_INTERVAL = 0.25

MANHATTAN_DIR = "S"
QUEENS_DIR = "N"

MARGIN = 5
ICON_W = 32
ICON_H = 32

ICON_GREY = "/Telltale/icons/subway_grey.png"
ICON_BLACK = "/Telltale/icons/subway_black.png"
ICON_BLUE = "/Telltale/icons/subway_blue.png"
ICON_ORANGE = "/Telltale/icons/subway_orange.png"

ANIM_RIGHT_MARGIN = 13
ANIM_BOTTOM_MARGIN = 30
FRAME_W = 32
FRAME_H = 32
FRAMES = 4
ANIM_FPS = 9
ANIM_INTERVAL = 1.0 / ANIM_FPS

SHEET_WAIT = "/Telltale/animation/coffee_sheet_128x32.bmp"
SHEET_GO = "/Telltale/animation/walk_sheet_128x32.bmp"
SHEET_ARRIVAL = "/Telltale/animation/metro_run_sheet_128x32.bmp"

# -----------------------------
# WiFi + HTTPS session
# -----------------------------
ok = connect_priority_network(KNOWN_NETWORKS)

if not ok:
    print("No known WiFi found / all failed.")
    while True:
        pass

pool = socketpool.SocketPool(wifi.radio)
ssl_context = ssl.create_default_context()
requests = adafruit_requests.Session(pool, ssl_context)
print("Connected:", wifi.radio.ap_info.ssid)

# -----------------------------
# Display Setup
# -----------------------------
display = board.DISPLAY
root = displayio.Group()
display.root_group = root

# -----------------------------
# Animation Group (scaled)
# -----------------------------
ANIM_SCALE = 2

# enlarge frame size by scale factor
ANIM_W = FRAME_W * ANIM_SCALE
ANIM_H = FRAME_H * ANIM_SCALE

# position animation at bottom-right with margin
ANIM_X = display.width - ANIM_RIGHT_MARGIN - ANIM_W
ANIM_Y = display.height - ANIM_BOTTOM_MARGIN - ANIM_H

anim_group = displayio.Group(scale=ANIM_SCALE)
anim_group.x = ANIM_X
anim_group.y = ANIM_Y

root.append(anim_group)


ICON_X = display.width - MARGIN - ICON_W +3
ICON_Y = MARGIN
ANIM_X = display.width - ANIM_RIGHT_MARGIN - FRAME_W
ANIM_Y = display.height - ANIM_BOTTOM_MARGIN - FRAME_H
TEXT_X = MARGIN + 5

Y1, Y2, Y3, Y4 = 22, 55, 85, 115
STATUS_GAP = 10
STATUS_Y = ANIM_Y + FRAME_H + STATUS_GAP

title = label.Label(terminalio.FONT, text="Roosevelt Island", scale=2, x=TEXT_X, y=Y1)
status_line = label.Label(terminalio.FONT, text="--", scale=2, x=TEXT_X - 30, y=STATUS_Y)
line_label = label.Label(terminalio.FONT, text="Line: --", scale=1, x=TEXT_X, y=Y2)
man_line = label.Label(terminalio.FONT, text="To Manhattan: --", scale=1, x=TEXT_X, y=Y3)
que_line = label.Label(terminalio.FONT, text="To Queens: --", scale=1, x=TEXT_X, y=Y4)

root.append(title)
root.append(status_line)
root.append(line_label)
root.append(man_line)
root.append(que_line)

DOT_R = 4
DOT_X = TEXT_X
LINE_TEXT_X = TEXT_X + 12
man_line.x = LINE_TEXT_X
que_line.x = LINE_TEXT_X

dot_man = Circle(DOT_X + DOT_R, Y3, DOT_R, outline=COLOR_OUTLINE, fill=None)
dot_que = Circle(DOT_X + DOT_R, Y4, DOT_R, outline=COLOR_OUTLINE, fill=None)
root.append(dot_man)
root.append(dot_que)

# -----------------------------
# Edge Flow Border (clockwise)
# -----------------------------
EDGE_MARGIN = 2              
EDGE_SPACING = 6             # distance between blocks
EDGE_BLOCKS = 15             # number of blocks (including head+tail) 
EDGE_MIN_SIZE = 1
EDGE_MAX_SIZE = 5

def edge_interval_for(state, minutes):
    # base fps by state
    if state == "ARRIVAL":
        fps = 30
    elif state == "GO":
        fps = 15
    else:
        fps = 4

    # gentle fine-tuning within state (avoid jitter)
    if minutes is None:
        return 1.0 / fps

    # clamp minutes to 0..15 for stability
    m = minutes
    if m < 0: m = 0
    if m > 15: m = 15

    # small adjustment only (±20%)
    if state == "WAIT":
        # bigger minutes -> slightly slower
        fps *= (0.8 + 0.2 * (1.0 - (m / 15.0)))
    else:
        # closer to 0 -> slightly faster
        fps *= (0.8 + 0.2 * (1.0 - (m / 15.0)))

    if fps < 4: fps = 4
    if fps > 30: fps = 30
    return 1.0 / fps


# use a separate group for the border so it can be rendered below text/icons
border_group = displayio.Group()
root.insert(0, border_group)   # insert at bottom layer

# build edge path: top -> right -> bottom -> left
def build_edge_path(w, h, margin, spacing):
    pts = []
    x0, y0 = margin, margin
    x1, y1 = w - margin - 1, h - margin - 1

    # top: left->right
    x = x0
    while x <= x1:
        pts.append((x, y0))
        x += spacing

    # right: top->bottom (skip top corner)
    y = y0 + spacing
    while y <= y1:
        pts.append((x1, y))
        y += spacing

    # bottom: right->left (skip bottom-right corner)
    x = x1 - spacing
    while x >= x0:
        pts.append((x, y1))
        x -= spacing

    # left: bottom->top (skip bottom-left & top-left)
    y = y1 - spacing
    while y >= y0 + spacing:
        pts.append((x0, y))
        y -= spacing

    return pts

edge_path = build_edge_path(display.width, display.height, EDGE_MARGIN, EDGE_SPACING)

# pre-build edge blocks (groups with multiple rects for different sizes)
edge_slots = []
for _ in range(EDGE_BLOCKS):
    g = displayio.Group()
    # pre-create rects for all sizes (1..5) and toggle visibility instead of creating new ones
    r1 = Rect(0, 0, 1, 1, fill=COLOR_WAIT, outline=None)
    r2 = Rect(0, 0, 2, 2, fill=COLOR_WAIT, outline=None)
    r3 = Rect(0, 0, 3, 3, fill=COLOR_WAIT, outline=None)
    r4 = Rect(0, 0, 4, 4, fill=COLOR_WAIT, outline=None)
    r5 = Rect(0, 0, 5, 5, fill=COLOR_WAIT, outline=None)

    g.append(r1); g.append(r2); g.append(r3); g.append(r4); g.append(r5)

    # start with all hidden, show as needed in animation loop
    for r in (r1, r2, r3, r4, r5):
        r.hidden = True

    border_group.append(g)
    edge_slots.append((g, (r1, r2, r3, r4, r5)))


edge_head = 0
last_edge = 0.0

def state_color(state):
    if state == "ARRIVAL":
        return COLOR_ARRIVAL
    if state == "GO":
        return COLOR_GO
    return COLOR_WAIT

def _clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v

def _edge_interval_for(state, minutes):
    """
    Return seconds per step (smaller = faster).
    Primary: by state (WAIT/GO/ARRIVAL).
    Secondary: gentle tuning by minutes (to avoid jitter).
    """
    # Base FPS by state (tune these)
    if state == "ARRIVAL":
        base_fps = 35.0
    elif state == "GO":
        base_fps = 15.0
    else:  # WAIT or NODATA
        base_fps = 5.0

    if minutes is None:
        fps = base_fps
        return 1.0 / fps

    # Clamp minutes to a stable band to avoid crazy speed swings
    m = _clamp(minutes, 0, 15)

    # Gentle adjust within ±20%
    # - WAIT: larger minutes => slightly slower
    # - GO/ARRIVAL: closer to 0 => slightly faster
    if state == "WAIT":
        # m=15 -> 0.8x, m=0 -> 1.0x  (still calm)
        factor = 0.8 + 0.2 * (1.0 - (m / 15.0))
    else:
        # m=15 -> 0.8x, m=0 -> 1.0x  (tighten urgency near arrival)
        factor = 0.8 + 0.2 * (1.0 - (m / 15.0))

    fps = base_fps * factor
    fps = _clamp(fps, 4.0, 24.0)  # safety
    return 1.0 / fps

def update_edge_flow(state, now, minutes=None):
    global edge_head, last_edge

    interval = _edge_interval_for(state, minutes)
    if now - last_edge < interval:
        return
    last_edge = now

    if len(edge_path) == 0:
        return

    color = state_color(state)
    edge_head = (edge_head + 1) % len(edge_path)

    for i, (g, rects) in enumerate(edge_slots):
        idx = (edge_head - i) % len(edge_path)
        x, y = edge_path[idx]

        # size: head big -> tail small (EDGE_MAX_SIZE..EDGE_MIN_SIZE)
        if EDGE_BLOCKS <= 1:
            size = EDGE_MAX_SIZE
        else:
            size = EDGE_MAX_SIZE - int((EDGE_MAX_SIZE - EDGE_MIN_SIZE) * (i / (EDGE_BLOCKS - 1)))

        size = _clamp(size, EDGE_MIN_SIZE, EDGE_MAX_SIZE)  # 1..5

        g.x = x
        g.y = y

        for r in rects:
            r.hidden = True

        rr = rects[size - 1]  # rects: (r1..r5)
        rr.fill = color
        rr.hidden = False

    

    # Determine dynamic interval
    interval = _edge_interval_for(state, minutes)

    if now - last_edge < interval:
        return
    last_edge = now

    color = state_color(state)

    # Advance head clockwise
    if len(edge_path) == 0:
        return
    edge_head = (edge_head + 1) % len(edge_path)

    # Render head + tail
    for i, (g, rects) in enumerate(edge_slots):
        idx = (edge_head - i) % len(edge_path)
        x, y = edge_path[idx]

        # size: head big -> tail small (4..1)
        if EDGE_BLOCKS <= 1:
            size = EDGE_MAX_SIZE
        else:
            size = EDGE_MAX_SIZE - int((EDGE_MAX_SIZE - EDGE_MIN_SIZE) * (i / (EDGE_BLOCKS - 1)))
        size = _clamp(size, 1, 4)

        # move group
        g.x = x
        g.y = y

        # hide all, show chosen size
        for r in rects:
            r.hidden = True
        rr = rects[size - 1]
        rr.fill = color
        rr.hidden = False


# -----------------------------
# Helpers
# -----------------------------
def load_icon(path):
    bmp, pal = adafruit_imageload.load(path, bitmap=displayio.Bitmap, palette=displayio.Palette)
    try:
        for i in range(len(pal)):
            if (int(pal[i]) & 0xFFFFFF) == 0xFFFFFF:
                pal.make_transparent(i)
                break
    except Exception: pass
    tg = displayio.TileGrid(bmp, pixel_shader=pal, x=ICON_X, y=ICON_Y)
    return tg

def load_sheet(path):
    bmp, pal = adafruit_imageload.load(
        path, bitmap=displayio.Bitmap, palette=displayio.Palette
    )
    try:
        for i in range(len(pal)):
            if (int(pal[i]) & 0xFFFFFF) == 0xFF00FF:
                pal.make_transparent(i)
                break
    except Exception:
        pass

    return displayio.TileGrid(
        bmp,
        pixel_shader=pal,
        tile_width=FRAME_W,
        tile_height=FRAME_H,
        width=1,
        height=1
    )

anim_wait = load_sheet(SHEET_WAIT)
anim_go = load_sheet(SHEET_GO)
anim_arrival = load_sheet(SHEET_ARRIVAL)

for anim in [anim_wait, anim_go, anim_arrival]:
    anim_group.append(anim)

icon_grey = load_icon(ICON_GREY)
icon_black = load_icon(ICON_BLACK)
icon_blue = load_icon(ICON_BLUE)
icon_orange = load_icon(ICON_ORANGE)
for icon in [icon_grey, icon_black, icon_blue, icon_orange]: root.append(icon)



def show_anim(which):
    anim_wait.hidden = (which != "WAIT")
    anim_go.hidden = (which != "GO")
    anim_arrival.hidden = (which != "ARRIVAL")

def show_icon(mode):
    icon_grey.hidden = (mode != "grey")
    icon_black.hidden = (mode != "black")
    icon_blue.hidden = (mode != "blue")
    icon_orange.hidden = (mode != "orange")

def get_state(minutes):
    if minutes is None: return "NODATA"
    if 0 <= minutes <= THRESHOLD_ARRIVAL: return "ARRIVAL"
    if THRESHOLD_ARRIVAL < minutes <= THRESHOLD_MIN: return "GO"
    return "WAIT"

def get_status_text(minutes):
    if minutes is None: return "NO ETA"
    if 0 <= minutes <= THRESHOLD_ARRIVAL: return "ARRIVE!"
    if THRESHOLD_ARRIVAL < minutes <= THRESHOLD_MIN: return "GO NOW!"
    return "WAIT~"

def pick_soonest(arrivals, line, direction):
    best = None
    for a in arrivals:
        if a.get("line") == line and a.get("direction") == direction:
            try:
                m = int(a.get("minutesAway", 9999))
                if best is None or m < best: best = m
            except: continue
    return best

def choose_current_line(arrivals):
    lines = {a.get("line") for a in arrivals if a.get("line")}
    if "F" in lines: return "F", lines
    if "M" in lines: return "M", lines
    return None, lines

STATUS_LEFT_NUDGE = 12  

def center_status():
    status_line.x = (
        anim_group.x
        + (ANIM_W - status_line.bounding_box[2]) // 2
        - STATUS_LEFT_NUDGE
    )


# -----------------------------
# UI Animation/Style State Machine
# -----------------------------
blink_on = True
last_blink = 0.0
anim_frame = 0
last_anim = 0.0

def update_ui_visuals(state, now):
    global blink_on, last_blink, anim_frame, last_anim

    # 1. Blink Logic
    if state == "ARRIVAL":
        if now - last_blink >= BLINK_INTERVAL:
            last_blink = now
            blink_on = not blink_on
    else:
        blink_on = True

    # 2. Text/Icon Color & Visibility
    if state == "ARRIVAL":
        title.color = status_line.color = COLOR_ARRIVAL
        status_line.hidden = (not blink_on)
        show_icon("orange")
        icon_orange.hidden = (not blink_on)
    elif state == "GO":
        title.color = status_line.color = COLOR_GO
        title.hidden = status_line.hidden = False
        show_icon("blue")
    else:
        title.color = status_line.color = COLOR_WAIT
        title.hidden = status_line.hidden = False
        show_icon("grey")

    # 3. Animation Frames
    if now - last_anim >= ANIM_INTERVAL:
        last_anim = now
        anim_frame = (anim_frame + 1) % FRAMES
        if not anim_wait.hidden: anim_wait[0] = anim_frame
        if not anim_go.hidden: anim_go[0] = anim_frame
        if not anim_arrival.hidden: anim_arrival[0] = anim_frame

    # 4. Show Correct Animation
    if state == "ARRIVAL":
        show_anim("ARRIVAL")
        anim_arrival.hidden = False
    elif state == "GO": show_anim("GO")
    else: show_anim("WAIT")

def render_selection_ui(selected_dir, state):
    sel_color = COLOR_ARRIVAL if state == "ARRIVAL" else (COLOR_GO if state == "GO" else COLOR_WAIT)
    if selected_dir == "M":
        dot_man.fill = dot_man.outline = sel_color
        dot_que.fill, dot_que.outline = None, COLOR_OUTLINE
        man_line.color, que_line.color = COLOR_TEXT, COLOR_TEXT_DIM
    else:
        dot_que.fill = dot_que.outline = sel_color
        dot_man.fill, dot_man.outline = None, COLOR_OUTLINE
        que_line.color, man_line.color = COLOR_TEXT, COLOR_TEXT_DIM

# -----------------------------
# Main Loop
# -----------------------------
btn_d1 = DigitalInOut(board.D1)
btn_d1.direction, btn_d1.pull = Direction.INPUT, Pull.DOWN 

btn_d2 = DigitalInOut(board.D2)
btn_d2.direction, btn_d2.pull = Direction.INPUT, Pull.DOWN

selected_dir = "M"
last_btn_time = 0.0
DEBOUNCE = 0.2
last_api = 0.0
man_min, que_min, current_line = None, None, None

while True:
    now = time.monotonic()

    # --- API DATA FETCH ---
    if now - last_api >= API_INTERVAL:
        last_api = now
        try:
            resp = requests.get(API_URL)
            data = resp.json()
            resp.close()
            arrivals = data.get("arrivals", [])

            if not arrivals:
                man_min = que_min = None
                line_label.text = "Line: --"
            else:
                current_line, _ = choose_current_line(arrivals)
                if current_line:
                    man_min = pick_soonest(arrivals, current_line, MANHATTAN_DIR)
                    que_min = pick_soonest(arrivals, current_line, QUEENS_DIR)
                    line_label.text = f"Line: {current_line}"
                    man_line.text = f"To Manhattan: {('--' if man_min is None else str(man_min)+' min')}"
                    que_line.text = f"To Queens: {('--' if que_min is None else str(que_min)+' min')}"
        except Exception as e:
            print("API Error:", e)

    # --- BUTTON HANDLING ---
    if now - last_btn_time > DEBOUNCE:
        if btn_d1.value:
            selected_dir, last_btn_time = "M", now
            print("D1 pressed -> Manhattan")
        elif btn_d2.value:
            selected_dir, last_btn_time = "Q", now
            print("D2 pressed -> Queens")

    # --- DYNAMIC UI REFRESH ---
    selected_min = man_min if selected_dir == "M" else que_min
    state = get_state(selected_min)

    # 1. text
    status_line.text = get_status_text(selected_min)
    center_status()

    # 2. ui visuals (color, icon, animation, blink)
    update_ui_visuals(state, now)

    # 3. selection UI (dot + line color)
    render_selection_ui(selected_dir, state)
    update_edge_flow(state, now, selected_min)



    time.sleep(UI_TICK)
