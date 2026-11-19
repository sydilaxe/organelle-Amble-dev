"""The key map: a two-page PDF of the Organelle's keys and what each does, drawn as the keyboard.

    python3 keymap.py [OUT.pdf]          (default: ../dist/Amble-keymap.pdf; package.sh puts it in the release)

Built from the same tables as the patch: the low and top keys (gen_ui.LOW_KEYS / TOP_KEYS / LOW_PAGES), the knob
pages (data.PAGES), the SETUP pages (gen_setup.SETUP_NAMES). Each key needs an entry in LOW / TOP below; the build
stops if a key in the patch has none, so the map can't fall behind the patch."""
import os
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

import gen_setup as S
import gen_ui as U
from data import PAGES, PAGE_NAMES

NAMES = "C C# D D# E F F# G G# A A# B".split()
BLACK = {1, 3, 6, 8, 10}
WHITE_ORDER = [0, 2, 4, 5, 7, 9, 11]

INK = colors.HexColor("#1d2330")
GREY = colors.HexColor("#6b717d")
# what a key does, by kind: its colour
KIND = {
    "play": colors.HexColor("#3b6ea8"),      # the playing knob pages
    "level": colors.HexColor("#2f8f6b"),     # the level knob pages
    "music": colors.HexColor("#b8692e"),     # harmony and form
    "layer": colors.HexColor("#7b5ea7"),     # the layers
    "control": colors.HexColor("#a83b5b"),   # input, freeze, the transport
    "setup": colors.HexColor("#4d5566"),
}


def knobs(page):
    return " ".join(lab for lab, _, _ in PAGES[page])


def page_key(key):
    p = U.LOW_PAGES[key]
    kind = "level" if PAGE_NAMES[p].startswith(("MIX", "SENDS")) else "play"
    hold = ["hold: GLIDE page"] if key == U.GLIDE_KEY - 60 else \
        [f"hold: {n} page" for n, k in S.MIRRORS if k == key]
    if key == 1:      # (aux + C#: MOSAIC)
        hold += ["aux: MOSAIC in / out", "aux + hold: MOSAIC page"]
    return (PAGE_NAMES[p], ["knobs: " + knobs(p)] + hold, kind)


# low octave: (title, lines, kind) for each name in gen_ui.LOW_KEYS
LOW = {
    "Root (hold)": ("ROOT", ["hold, then a key, a MIDI note or knob 1:", "the next key (at the next chord)"], "music"),
    "chord change now (hold: CHORD page)": ("CHORD", ["tap: change now", "hold: CHORD page -", "knob 1 picks the next chord"],
                                            "music"),
    "Resolve": ("RESOLVE", ["tonic in open fifths, held", "again: release"], "music"),
    "next section (hold: hold section)": ("SECTION", ["tap: next section", "hold 0.6 s: hold section", "(again: move on)"],
                                          "music"),
}
# top octave, for each name in gen_ui.TOP_KEYS
LAYERS = {f"{n} in/out | hold: {n} SHAPE | aux: {n} page": n for _, n, _ in U.LAYER_KEYS}
TOP = {k: (n.upper(), ["tap: in / out", "hold: SHAPE page", "aux + tap: its page"]
           + (["held + low keys:", "rhythm, harmony (C-B)"] if n in ("motion", "bells") else []), "layer")
       for k, n in LAYERS.items()}
TOP.update({
    "input mode | hold: INPUT page | aux: capture": ("INPUT", ["tap: next input mode", "hold: INPUT page", "aux + tap: capture",
                                                               "8 s into the cloud"], "control"),
    "Freeze | aux: ANCHOR": ("FREEZE", ["tap: freeze reverb + cloud", "aux + tap: ANCHOR (set,", "then glide back)",
                                        "aux + hold 0.8 s: anchor here"], "control"),
    "start / stop | aux: COMPOSE / DRIFT": ("START / STOP", ["tap: start or stop", "aux + tap: COMPOSE / DRIFT"],
                                            "control"),
    "new piece | hold: COMPARE | + key: load | aux: SAVES": ("NEW PIECE", [
        "tap (on release): new piece", "hold 0.6 s: COMPARE", "hold + a key: load slot", "aux + hold + key: save slot",
        "aux + tap: SAVES"], "control"),
})


def low_entry(k):
    name = U.LOW_KEYS[k]
    return page_key(k) if k in U.LOW_PAGES else LOW[name]


def check():
    missing = [n for k, n in enumerate(U.LOW_KEYS) if k not in U.LOW_PAGES and n not in LOW]
    missing += [n for n in U.TOP_KEYS if n not in TOP]
    assert not missing, f"keymap.py has no entry for keys {missing}: add them to LOW / TOP"


def keyboard(c, x, y, w, h, entries, octave):
    """one octave at (x, y) (its bottom left), w wide, h tall: entries[k] = (title, lines, kind)"""
    ww = w / 7
    bw, bh = ww * 0.66, h * 0.56
    # white keys: label in the lower part (under the black keys)
    for i, k in enumerate(WHITE_ORDER):
        kx = x + i * ww
        title, lines, kind = entries[k]
        c.setFillColor(colors.white)
        c.setStrokeColor(INK)
        c.setLineWidth(0.8)
        c.rect(kx, y, ww, h, fill=1, stroke=1)
        c.setFillColor(KIND[kind])
        c.rect(kx + 1, y + 1, ww - 2, 5, fill=1, stroke=0)
        ty = y + h - bh - 14
        c.setFillColor(GREY)
        c.setFont("Helvetica", 7)
        c.drawString(kx + 4, ty + 2, f"{octave} {NAMES[k]}")
        ty -= 11
        c.setFillColor(KIND[kind])
        c.setFont("Helvetica-Bold", 9.5)
        for ln in simpleSplit(title, "Helvetica-Bold", 9.5, ww - 8):
            c.drawString(kx + 4, ty, ln)
            ty -= 11
        c.setFillColor(INK)
        c.setFont("Helvetica", 7.2)
        for line in lines:
            for ln in simpleSplit(line, "Helvetica", 7.2, ww - 8):
                c.drawString(kx + 4, ty, ln)
                ty -= 8.6
    # black keys: label inside, light on dark
    for k in sorted(BLACK):
        left = WHITE_ORDER.index(k - 1)
        kx = x + (left + 1) * ww - bw / 2
        title, lines, kind = entries[k]
        c.setFillColor(INK)
        c.rect(kx, y + h - bh, bw, bh, fill=1, stroke=0)
        c.setFillColor(KIND[kind])
        c.rect(kx, y + h - bh, bw, 4, fill=1, stroke=0)
        ty = y + h - 11
        c.setFillColor(colors.HexColor("#aab1bf"))
        c.setFont("Helvetica", 6.5)
        c.drawString(kx + 3, ty, f"{octave} {NAMES[k]}")
        ty -= 10
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8.5)
        for ln in simpleSplit(title, "Helvetica-Bold", 8.5, bw - 6):
            c.drawString(kx + 3, ty, ln)
            ty -= 9.5
        c.setFont("Helvetica", 6.6)
        for line in lines:
            for ln in simpleSplit(line, "Helvetica", 6.6, bw - 6):
                c.drawString(kx + 3, ty, ln)
                ty -= 7.6


def legend(c, x, y, items):
    for name, kind in items:
        c.setFillColor(KIND[kind])
        c.rect(x, y - 1, 9, 9, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont("Helvetica", 8)
        c.drawString(x + 13, y, name)
        x += 13 + c.stringWidth(name, "Helvetica", 8) + 16


def header(c, W, H, title, sub, version):
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(36, H - 44, title)
    c.setFont("Helvetica", 9)
    c.setFillColor(GREY)
    c.drawString(36, H - 58, sub)
    c.drawRightString(W - 36, H - 44, f"Amble {version}")


def text_block(c, x, y, w, rows, size=8.2):
    """rows of (bold lead, rest): wrapped to w; returns the y under them"""
    for lead, rest in rows:
        c.setFont("Helvetica-Bold", size)
        c.setFillColor(INK)
        c.drawString(x, y, lead)
        lw = c.stringWidth(lead + "  ", "Helvetica-Bold", size)
        c.setFont("Helvetica", size)
        lines = simpleSplit(rest, "Helvetica", size, w - lw)
        for i, ln in enumerate(lines):
            c.drawString(x + lw, y, ln)
            y -= size + 3.2
        y -= 2
    return y


def aux_top():
    """aux + each top key, read from gen_ui.TOP_KEYS ('... | aux: X'): the layers' shared one, then the others"""
    out, layers = [], []
    for k, name in enumerate(U.TOP_KEYS):
        aux = [p.split("aux:", 1)[1].strip() for p in name.split("|") if "aux:" in p]
        if not aux:
            continue
        if name in LAYERS:
            layers.append(NAMES[k])
        else:
            out.append((f"top {NAMES[k]}", aux[0]))
    return layers, out


AUX_MORE = {     # what the short aux names in TOP_KEYS mean
    "page": "the layer's page: knob 1 its sound (or auto), 2 in / out / auto, 3 its level, 4 its reverb send; "
            "aux leaves",
    "capture": "record 8 s of the input into the cloud, kept as a memory",
    "ANCHOR": "set the anchor, then glide every knob back to it; held 0.8 s: anchor here anew",
    "COMPOSE / DRIFT": "switch the mode (COMPOSE: a form of sections; DRIFT: endless)",
    "SAVES": "tap: the SAVES page (SETUP SAVES); held with a key: save to that slot",
}


def aux_panel(c, x, y, w):
    """the aux button and everything it does: alone, with a low key, with a top key"""
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(INK)
    c.drawString(x, y, "THE AUX BUTTON")
    cy = y - 34
    c.setFillColor(INK)
    c.circle(x + 22, cy, 18, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x + 22, cy - 3, "AUX")
    col = (w - 56) / 3
    x0 = x + 56
    # alone
    yy = text_block(c, x0, y - 16, col - 10, [
        ("Tap:", "the next knob page (in SETUP: the next SETUP page)."),
        ("Hold 1 s:", "SETUP; in SETUP, hold and let go to leave (settings are saved)."),
    ])
    # with a low key
    text_block(c, x0 + col, y - 16, col - 10, [
        ("+ low key:", "a white key: a SETUP group (page 2); in SETUP, + knob 1: scroll the pages."),
        ("+ top B, + key:", "save to that slot (low C-B = 1-12, top C-D# = 13-16)."),
    ])
    # with a top key
    layers, others = aux_top()
    rows = [(f"+ top {layers[0]}-{layers[-1]}:", AUX_MORE["page"])] if layers else []
    for key, what in others:
        rows.append((f"+ {key}:", f"{what} - {AUX_MORE[what]}" if what in AUX_MORE else what))
    text_block(c, x0 + 2 * col, y - 16, col - 10, rows, size=7.6)
    return yy


def build(out, version="dev"):
    check()
    W, H = landscape(letter)
    c = canvas.Canvas(out, pagesize=(W, H))
    c.setTitle("Amble key map")
    c.setAuthor("Amble")
    kw, kh = W - 72, 195
    # ---- page 1: the keys
    header(c, W, H, "Amble - the Organelle keys",
           "The keys are functions (play notes from MIDI). Low octave: the knob pages, harmony and form. Top octave: "
           "the layers, input, Freeze, the transport.", version)
    legend(c, 36, H - 80, [("playing knob pages", "play"), ("level knob pages", "level"),
                           ("harmony and form", "music"), ("layers", "layer"), ("input, freeze, transport", "control")])
    y1 = H - 100 - kh
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(INK)
    c.drawString(36, y1 + kh + 6, "LOW OCTAVE")
    keyboard(c, 36, y1, kw, kh, {k: low_entry(k) for k in range(12)}, "low")
    y2 = y1 - 30 - kh
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(INK)
    c.drawString(36, y2 + kh + 6, "TOP OCTAVE")
    keyboard(c, 36, y2, kw, kh, {k: TOP[n] for k, n in enumerate(U.TOP_KEYS)}, "top")
    c.setFont("Helvetica", 8)
    c.setFillColor(GREY)
    c.drawString(36, y2 - 16, "White keys C D E F: the playing pages; the black key beside each: a level page. "
                              "A knob page shows its four knobs for 6 s; MIX and SENDS show the MIX view.")
    c.drawString(36, y2 - 28, "Footswitch: chord change now.   Aux tap: next knob page.   Aux held 1 s: SETUP "
                              "(held and let go again: leave and save).   Page 2: aux + key, slots, knobs.")
    c.showPage()

    # ---- page 2: aux + key (SETUP pages), the slots, the knob pages, the other controls
    header(c, W, H, "Amble - aux, slots and knobs",
           "Hold aux and press a white low key: a SETUP group. Hold top B and press a key: a save slot.", version)
    setup = {k: ("-", ["free"], "setup") for k in range(12)}
    setup.update({k: (g, ps[:3] + (["..."] if len(ps) > 3 else []), "setup") for k, (g, ps) in zip(S.GROUP_KEYS, S.SETUP_GROUPS)})
    yk = H - 80 - 120
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(INK)
    c.drawString(36, yk + 126, "AUX + LOW KEY: SETUP GROUPS (their first page)")
    keyboard(c, 36, yk, kw, 120, setup, "low")
    groups = "; ".join(f"{g}: {', '.join(ps)}" for g, ps in S.SETUP_GROUPS)
    y = text_block(c, 36, yk - 16, kw, [
        ("The groups:", f"{groups}. Aux + top B opens SAVES."),
        ("In SETUP:", "aux taps step through the pages; aux held + knob 1 scrolls through all of them, back and forth. "
                      "The four knobs set the four rows (absolute). Hold aux and let go (without knob 1), or press a "
                      "knob page key, to leave; settings are saved."),
    ])
    # the slots
    y -= 6
    c.setFont("Helvetica-Bold", 10)
    c.drawString(36, y, "SAVE SLOTS (hold top B)")
    y -= 14
    y = text_block(c, 36, y, kw, [
        ("Load:", "hold top B, press a key - low C to B = slots 1-12, top C to D# = slots 13-16. The piece morphs in "
                  "(SETUP RECALL)."),
        ("Save:", "hold aux and top B, press a key."),
        ("Compare:", "hold top B 0.6 s - the slot as loaded or saved, while held. Empty slots 1-6 hold the factory "
                     "pieces."),
    ])
    # the knob pages
    y -= 6
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(INK)
    c.drawString(36, y, "KNOB PAGES (knobs 1-4)")
    y -= 14
    keys_of = {p: NAMES[k] for k, p in U.LOW_PAGES.items()}
    colw = kw / 4
    for i, p in enumerate(sorted(range(len(PAGES)), key=lambda p: NAMES.index(keys_of[p]))):
        cx, cy = 36 + (i % 4) * colw, y - (i // 4) * 30
        kind = "level" if PAGE_NAMES[p].startswith(("MIX", "SENDS")) else "play"
        c.setFillColor(KIND[kind])
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(cx, cy, f"{PAGE_NAMES[p]} (low {keys_of[p]})")
        c.setFillColor(INK)
        c.setFont("Helvetica", 8)
        c.drawString(cx, cy - 11, "  ".join(f"{j + 1} {lab}" for j, (lab, _, _) in enumerate(PAGES[p])))
    y -= 30 * ((len(PAGES) + 3) // 4) + 4
    y = text_block(c, 36, y, kw, [
        ("Pickup:", "after a page change a knob moves its value towards the end it turns to, so nothing jumps."),
        ("Levels:", "MIX and SENDS - 50 % is the designed balance, 100 % +6 dB; below 50 % even steps to -24 dB at 5 %, "
                    "then off."),
        ("Rhythm keys:", "hold top E (motion) or D# (bells), press low keys: C random, C# the piece's own, D / D# rotate, "
                         "E / F more / fewer hits (bells: denser / sparser), F# / G longer / shorter cycle (bells: next / "
                         "previous named rhythm), G# harmony in the key, A ratchets, A# ghost notes, B swing (bells: rubato)."),
    ])
    aux_panel(c, 36, y - 8, kw)
    c.showPage()
    c.save()
    return out


if __name__ == "__main__":
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist", "Amble-keymap.pdf")
    out = sys.argv[1] if len(sys.argv) > 1 else default
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    print(build(out, sys.argv[2] if len(sys.argv) > 2 else "dev"))
