#!/usr/bin/env python3
"""The World Today - Friday 20 November 2026 in one image.

Draws a 1024x1024 newspaper front page summing up the day's world news
and encodes it as a PNG with a hand-rolled encoder. Standard library only,
no network, fully deterministic: two runs produce byte-identical output.

The hero photograph is a media-generated illustration of Kyiv at predawn
(assets: hero.png, decoded below with a small PNG reader) composited into
the front page; every word on the page is drawn here with a 5x7 bitmap
font so the text stays sharp and legible.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---- palette ---------------------------------------------------------------
PAPER = (247, 243, 232)
INK = (18, 18, 18)
NAVY = (20, 33, 61)
NAVY2 = (28, 46, 84)
RED = (185, 28, 28)
RED2 = (200, 40, 40)
GOLD = (201, 162, 39)
WHITE = (255, 255, 255)
SKY = (168, 205, 232)
GREY = (120, 120, 118)
LGREY = (228, 226, 218)
DARK = (40, 40, 40)
YELLOW = (250, 204, 21)
GREEN = (34, 120, 60)
TEAL = (14, 116, 144)
ORANGE = (234, 88, 12)
BROWN = (120, 72, 20)
SKIN1 = (232, 190, 150)
SKIN2 = (205, 160, 120)

# ---- canvas ----------------------------------------------------------------
px = bytearray(W * H * 3)


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i], px[i + 1], px[i + 2] = c


def fill_rect(x, y, w, h, c):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            px[i], px[i + 1], px[i + 2] = c


def rect(x, y, w, h, c, t=1):
    fill_rect(x, y, w, t, c)
    fill_rect(x, y + h - t, w, t, c)
    fill_rect(x, y, t, h, c)
    fill_rect(x + w - t, y, t, h, c)


def hline(x, y, w, c, t=1):
    fill_rect(x, y, w, t, c)


def vline(x, y, h, c, t=1):
    fill_rect(x, y, t, h, c)


def line(x0, y0, x1, y1, c, t=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        for a in range(t):
            for b in range(t):
                set_px(x0 + a, y0 + b, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c, filled=True):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
            if filled:
                if d <= r * r:
                    set_px(xx, yy, c)
            else:
                if r * r - 2 * r <= d <= r * r:
                    set_px(xx, yy, c)


# ---- PNG encode / decode (stdlib only) -------------------------------------
def encode_png(w, h, rgb):
    def chunk(typ, data):
        out = struct.pack(">I", len(data)) + typ + data
        out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def decode_png(path):
    """Decode an 8-bit non-interlaced RGB/RGBA PNG. Returns (w, h, rgb)."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file")
    pos = 8
    w = h = None
    bit_depth = color_type = interlace = None
    idat = bytearray()
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, bit_depth, color_type, _cm, _fm, interlace = struct.unpack(
                ">IIBBBBB", body)
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
        pos += 12 + ln
    if bit_depth != 8 or interlace != 0 or color_type not in (2, 6):
        raise ValueError("unsupported PNG variant")
    bpp = 3 if color_type == 2 else 4
    stride = w * bpp
    raw = zlib.decompress(bytes(idat))
    out = bytearray(w * h * 3)
    prev = bytearray(stride)
    off = 0
    for y in range(h):
        ftype = raw[off]
        off += 1
        row = bytearray(raw[off:off + stride])
        off += stride
        for i in range(stride):
            a = row[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ftype == 0:
                pass
            elif ftype == 1:
                row[i] = (row[i] + a) & 0xFF
            elif ftype == 2:
                row[i] = (row[i] + b) & 0xFF
            elif ftype == 3:
                row[i] = (row[i] + (a + b) // 2) & 0xFF
            elif ftype == 4:
                row[i] = (row[i] + _paeth(a, b, c)) & 0xFF
            else:
                raise ValueError("bad filter type")
        prev = row
        if bpp == 3:
            out[y * w * 3:(y + 1) * w * 3] = row
        else:
            for x in range(w):
                o = (y * w + x) * 3
                s = x * 4
                out[o], out[o + 1], out[o + 2] = row[s], row[s + 1], row[s + 2]
    return w, h, out


def blit_scaled(src_w, src_h, src, dx, dy, dw, dh):
    """Nearest-neighbour blit of an RGB image into the canvas rect."""
    for yy in range(dh):
        sy = min(src_h - 1, yy * src_h // dh)
        for xx in range(dw):
            sx = min(src_w - 1, xx * src_w // dw)
            si = (sy * src_w + sx) * 3
            set_px(dx + xx, dy + yy, (src[si], src[si + 1], src[si + 2]))


# ---- 5x7 bitmap font -------------------------------------------------------
# Each glyph: 7 rows of 5 bits. Written from the classic public-domain
# 5x7 pattern set; only capitals, digits and common punctuation are needed
# because the whole page is set in capitals.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "•": ("00000", "00000", "01100", "01100", "01100", "00000", "00000"),
}


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, scale, c, bold=False):
    for ch in s:
        g = FONT.get(ch, FONT[" "])
        for r in range(7):
            row = g[r]
            for col in range(5):
                if row[col] == "1":
                    fill_rect(x + col * scale, y + r * scale, scale, scale, c)
                    if bold:
                        fill_rect(x + col * scale + 1, y + r * scale,
                                  scale, scale, c)
        x += 6 * scale
    return x


def wrap_text(s, max_w, scale):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    lines = []
    for para in s.split("\n"):
        words = para.split(" ")
        cur = ""
        for wd in words:
            trial = wd if not cur else cur + " " + wd
            if text_w(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
    return lines


# ---- page content ----------------------------------------------------------
# All stories below were first reported on Friday 20 November 2026
# (Reuters, AP, Al Jazeera, IRIB and wire reports of that morning).
HERO_KICKER = "UKRAINE WAR"
HERO_HEAD1 = "MISSILES STRIKE"
HERO_HEAD2 = "KYIV OVERNIGHT"
HERO_DECK = (
    "RUSSIAN BALLISTIC MISSILES HIT THE CAPITAL BEFORE DAWN. A FIRE BROKE "
    "OUT IN A NORTHERN DISTRICT AFTER DEBRIS STRUCK A BUILDING, THE MAYOR SAID."
)

TILES = [
    ("MIDDLE EAST", RED,
     "HOUTHIS CLAIM FOUR SAUDI STRIKES",
     "FOUR TARGETS CLAIMED, INCLUDING RIYADH AIRPORT AND A FINANCE HUB."),
    ("ENERGY", ORANGE,
     "IRAN: MINES HIT THREE TANKERS",
     "THREE TANKERS CAUGHT FIRE AFTER HITTING MINES, TEHRAN SAYS."),
    ("EUROPE", TEAL,
     "DRONES SHUT GENOA AIRPORT",
     "FLIGHTS HALTED FOR FOUR HOURS AFTER UNIDENTIFIED DRONES WERE SPOTTED."),
    ("MARKETS", GREEN,
     "ANTHROPIC SOARS ON NASDAQ DEBUT",
     "SHARES OF THE AI FIRM JUMP 17% ON DAY ONE, CLOSING NEAR $97."),
    ("UNITED STATES", NAVY2,
     "TRUMP PARDONS PETE ROSE",
     "THE LATE HITS KING IS PARDONED FOR TAX CRIMES BY THE PRESIDENT."),
    ("ISRAEL", BROWN,
     "EISENKOT TAPPED TO FORM GOVERNMENT",
     "HERZOG PICKS THE EX-ARMY CHIEF OVER NETANYAHU TO BUILD A COALITION."),
]

TICKER = (
    "INDIA EVACUATES 80,000 AS STORM NEARS  •  FIJI DECLARES DROUGHT "
    "DISASTER  •  SEOUL COURT CLEARS EX-PM HAN  •  CALIFORNIA TARGETS NVIDIA "
    "OVER CHINA CHIPS"
)

FOOTER = ("SOURCES: REUTERS - AP - AL JAZEERA - IRIB - FRIDAY 20 NOVEMBER 2026")


# ---- drawing ---------------------------------------------------------------
def draw_hero_fallback(x, y, w, h):
    """Code-drawn Kyiv skyline, used only if hero.png cannot be read."""
    fill_rect(x, y, w, h, (24, 38, 66))
    for i in range(h):
        shade = int(24 + (i / h) * 30)
        hline(x, y + i, w, (shade, shade + 14, shade + 40))
    for bx, bw, bh in ((0, 90, 120), (100, 60, 170), (170, 110, 100),
                       (290, 70, 190), (370, 120, 130), (500, 80, 200),
                       (590, 100, 140), (700, 70, 180), (780, 120, 110),
                       (900, 68, 160)):
        fill_rect(x + bx, y + h - bh - 60, bw, bh, (16, 22, 40))
    for fx in (140, 330, 620, 830):
        circle(x + fx, y + h - 200, 26, ORANGE)
        circle(x + fx, y + h - 200, 14, YELLOW)
    fill_rect(x, y + h - 60, w, 60, (30, 60, 95))


def draw_tile(x, y, w, h, kicker, accent, head, body):
    fill_rect(x, y, w, h, WHITE)
    rect(x, y, w, h, LGREY, 1)
    fill_rect(x, y, w, 4, accent)
    draw_text(x + 12, y + 14, kicker, 2, RED, bold=True)
    hl = wrap_text(head, w - 24, 2)
    yy = y + 36
    for ln in hl[:2]:
        draw_text(x + 12, yy, ln, 2, INK, bold=True)
        yy += 16
    bl = wrap_text(body, w - 24, 2)
    yy += 4
    for ln in bl[:3]:
        draw_text(x + 12, yy, ln, 2, DARK)
        yy += 16


def draw_page():
    fill_rect(0, 0, W, H, PAPER)
    # thin frame
    rect(10, 10, W - 20, H - 20, INK, 2)

    # ---- masthead ------------------------------------------------------
    hline(28, 30, 968, INK, 2)
    mast = "THE WORLD TODAY"
    draw_text(28 + (968 - text_w(mast, 8)) // 2, 42, mast, 8, INK)
    hline(28, 106, 968, INK, 2)
    hline(28, 110, 968, INK, 1)
    tag = "ONE DAY'S NEWS IN ONE IMAGE"
    draw_text(28 + (968 - text_w(tag, 2)) // 2, 118, tag, 2, GREY)

    # ---- date band -----------------------------------------------------
    fill_rect(28, 136, 968, 38, RED)
    draw_text(44, 146, "FRIDAY 20 NOVEMBER 2026", 3, WHITE, bold=True)
    right = "ONE DAY, ONE IMAGE"
    draw_text(996 - 16 - text_w(right, 2), 148, right, 2, WHITE)

    # ---- hero image ----------------------------------------------------
    hx, hy, hw, hh = 28, 184, 968, 300
    hero_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "hero.png")
    try:
        sw, sh, simg = decode_png(hero_path)
        blit_scaled(sw, sh, simg, hx, hy, hw, hh)
    except Exception:
        draw_hero_fallback(hx, hy, hw, hh)
    rect(hx, hy, hw, hh, INK, 2)
    # caption strip on the image bottom
    fill_rect(hx + 2, hy + hh - 30, hw - 4, 28, NAVY)
    draw_text(hx + 14, hy + hh - 22, "ILLUSTRATION - KYIV AT DAWN: SMOKE OVER THE DNIPRO",
              2, WHITE)

    # ---- hero headline -------------------------------------------------
    draw_text(28, 500, HERO_KICKER, 2, RED, bold=True)
    draw_text(28, 522, HERO_HEAD1, 5, INK, bold=True)
    draw_text(28, 562, HERO_HEAD2, 5, INK, bold=True)
    deck = wrap_text(HERO_DECK, 968, 2)
    yy = 608
    for ln in deck[:2]:
        draw_text(28, yy, ln, 2, DARK)
        yy += 17

    # ---- tiles ---------------------------------------------------------
    hline(28, 650, 968, INK, 2)
    tw, th, gap = 312, 136, 12
    tx0, ty0 = 28, 664
    for i, (kicker, accent, head, body) in enumerate(TILES):
        cx = tx0 + (i % 3) * (tw + gap)
        cy = ty0 + (i // 3) * (th + gap)
        draw_tile(cx, cy, tw, th, kicker, accent, head, body)

    # ---- ticker --------------------------------------------------------
    ty = 992 - 40
    fill_rect(28, ty, 968, 40, NAVY)
    tlines = wrap_text(TICKER, 968 - 24, 2)
    yy = ty + 5
    for ln in tlines[:2]:
        draw_text(40, yy, ln, 2, WHITE)
        yy += 15

    # ---- footer --------------------------------------------------------
    draw_text(28 + (968 - text_w(FOOTER, 1)) // 2, 998, FOOTER, 1, GREY)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    draw_page()
    data = encode_png(W, H, px)
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
