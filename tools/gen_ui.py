"""The Organelle's own controls: the knobs (8 pages, with pickup), the 24 keys (all functions: knob pages,
harmony, form, layers, transport, ANCHOR, quick save / recall), aux, the footswitch, the text screen lines, the LED.

The key layout is LOW_KEYS / TOP_KEYS (the manual documents them in that order); keys() wires them, and the
gestures that use a key's release (low A tap / hold, top B tap / hold / + key, aux + top A) are handled at the top
of keys()."""
from pdlib import window, Canvas, proc, X, V, T, Send, Call, SendL, If, run_steps, Line, Later
from data import *
from pdlib import Toast, Arm
from gen_setup import NSET, SETUP_NAMES, GROUP_KEYS, GROUP_START
from data import MIX_KNOBS
import gen_setup as _S

SIDE = {  # what to do after a knob changes a value (index = page*4 + knob)
    0: [Send("ac-densch")],
    2: [Call("ac-brightupd")],
    3: [Call("ac-inputupd")],
    4: [Call("ac-revupd")],
    5: [Call("ac-verbsel")],
    6: [Call("ac-revupd")],
    7: [Call("ac-revupd")],
    9: [SendL("ac-weird", ["acweird"]), Call("ac-brightupd")],
    10: [SendL("ac-motion", ["acmotion"]), Call("ac-stereo")],
    11: [Send("ac-densch"), Call("ac-pulseupd")],
}
for _i in range(12, SEND_KNOBS):              # the SENDS pages
    SIDE[_i] = [V("acsgms", "30"), Call("ac-sendupd"), V("acsgms", "200")]
for _i in range(SEND_KNOBS, MIX_KNOBS):      # the MIX pages: the layer levels (coalesced: knobs send fast)
    SIDE[_i] = [Send("ac-mixch")]
SIDE[28] = [Call("ac-sinkupd")]              # PERFORM: Sink, Blur, Swell (Harm applies at the next choice)
SIDE[29] = [Call("ac-revupd")]
SIDE[30] = [Send("ac-densch"), Call("ac-brightupd"), Call("ac-swellupd")]
NP = len(PAGES)
# The Organelle keys are always functions (notes come from MIDI). Low octave: the playing pages on the white keys
# (SHAPE, SPACE, PIECE, PERFORM), the level pages on the black keys beside them (MIX 1, MIX 2, SENDS 1, SENDS 2),
# then harmony and form (G Root, A chord, A# Resolve, B section); top octave: the layers, then input, Freeze and the
# transport. Aux + a white low key opens a SETUP group (gen_setup.SETUP_GROUPS). The manual (tools/manual.py) documents these, in this order.
LOW_PAGES = {0: 0, 1: 5, 2: 1, 3: 6, 4: 2, 5: 7, 6: 3, 8: 4}     # low key -> knob page (data.PAGE_NAMES)
SAVES_PAGE = SETUP_NAMES.index("SAVES")  # SETUP SAVES (aux + top B)
LOW_KEYS = ["SHAPE page", "MIX 1 page", "SPACE page", "MIX 2 page", "PIECE page", "PERFORM page", "SENDS 1 page",
            "Root (hold)", "SENDS 2 page", "chord change now (hold: CHORD page)", "Resolve", "next section (hold: hold section)"]
LAYER_KEYS = [("acmdrone", "drone", "acgdrone"), ("acmsub", "sub", "acgsub"), ("acmpad", "pads", "acgpad"),
              ("acmbell", "bells", "acgbell"), ("acmmotion", "motion", "acgmotion"), ("acmtex", "textures", "acgtex"),
              ("acmatm", "atmosphere", "acgatm"), ("acmcloud", "cloud", "acgcloud")]
TOP_KEYS = [f"{n} in/out | hold: {n} SHAPE | aux: {n} page" for _, n, _ in LAYER_KEYS] + [
    "input mode | hold: INPUT page | aux: capture", "Freeze | aux: ANCHOR", "start / stop | aux: COMPOSE / DRIFT",
    "new piece | hold: COMPARE | + key: load | aux: SAVES"]
SAVE_KEY = 83                           # top B: tap = new piece; held, a key loads its slot (aux: saves to it)
ANCHOR_KEY = 81                         # top A: aux + tap = ANCHOR (set, then glide back), aux + hold = anchor here
FKEYS = LOW_KEYS + TOP_KEYS
ROOT_KEY = 60 + LOW_KEYS.index("Root (hold)")
MOTION_KEY = 72 + [n for _, n, _ in LAYER_KEYS].index("motion")      # top E
BELLS_KEY = 72 + [n for _, n, _ in LAYER_KEYS].index("bells")        # top D#
INPUT_KEY = 72 + len(LAYER_KEYS)                                     # top G#
CHORD_KEY = 60 + LOW_KEYS.index("chord change now (hold: CHORD page)")
SECTION_KEY = 60 + LOW_KEYS.index("next section (hold: hold section)")
GLIDE_KEY = 60 + LOW_KEYS.index("PERFORM page")    # low F: held 0.5 s, the GLIDE page
# what holding a key does, said in a toast 0.25 s into the hold (SETUP DISPLAY Hints) - 21 characters at most
HINTS = {GLIDE_KEY: "hold: GLIDE page", CHORD_KEY: "hold: CHORD page", SECTION_KEY: "hold: hold section",
         INPUT_KEY: "hold: INPUT page", SAVE_KEY: "hold: compare / load",
         **{60 + k: f"hold: {n} page" for n, k in _S.MIRRORS},
         **{72 + i: ("hold: SHAPE or rhythm" if 72 + i in (MOTION_KEY, BELLS_KEY) else
                     f"hold: {('ATMOS' if n == 'atmosphere' else n.upper())} SHAPE")
            for i, (_, n, _) in enumerate(LAYER_KEYS)}}
assert all(len(t) <= 21 for t in HINTS.values()), HINTS


def knobs():
    c = Canvas("knobs", w=2400)
    c.comment("Knob pickup: when a page changes, a knob moves its value proportionally towards the end it "
              "turns to, so nothing jumps")
    c0 = c
    for k in range(4):
        c, _ = window(c0, f"knob{k + 1}")
        kr = c.recv(f"knob{k + 1}")
        if k == 0:     # while Root (low G) is held, knob 1 picks the next key
            k1 = c.to(kr, "t f f")              # (right to left: the Root pick, then the knob)
            kr = (k1, 0)
            rs = c.obj("spigot")
            kt = c.to((k1, 1), "t f b")
            c.c(c.to((kt, 1), "expr acroothold"), 0, rs, 1)
            c.c(kt, 0, rs, 0)
            rt_ = c.to(rs, "t b f")
            c.c(rt_, 1, c.obj("v acrootk"), 0)
            run_steps(c, (rt_, 0), [V("acrootn", "int(acrootk*11.99)"),
                                                     If("acrootn != acpend", [Call("ac-rootset")])])
        if k == 0:     # in SETUP, aux held: knob 1 picks the page (all of them, back and forth)
            k2 = c.to(kr, "t f f")
            tb = c.to((k2, 1), "t b f")
            c.c(tb, 1, c.obj("v acscrk"), 0)
            run_steps(c, (tb, 0), [If(f"acsetup && acauxheld && acsetpg < {NSET}", [
                X(f"1; min({NSET - 1}, int(acscrk*{NSET}))", "v acauxused", "v acsnew"),
                If("acsnew != acsetpg", [V("acsetpg", "acsnew"), Call("ac-oledsetup")])])])
            kr = (k2, 0)
        mo = c.ch(kr, f"expr if((acroothold || (acsetup && acauxheld && acsetpg < {NSET})) && {k} == 0, -1000, "
                      f"if(acsetup, -1 - $f1, $f1))", "moses 0")
        sk = c.to((mo, 0), "moses -500")
        c.c(c.m(c.to((sk, 1), "expr -1 - $f1"), f"{k} $1"), 0, c.obj("s ac-setknob"), 0)
        t = c.to((mo, 1), "t f f")
        P = f"acparams[int(acpage*4+{k})]"
        R = f"acraw[{k}]"
        e = c.to((t, 1), f"expr if(acknown{k}, min(1, max(0, if($f1 > {R}, {P} + ($f1-{R})*(1-{P})/max(0.001, 1-{R}), "
                         f"{P} - ({R}-$f1)*{P}/max(0.001, {R})))), {P}); acpage*4+{k}")
        pk = c.obj("pack f f")
        c.c(e, 1, pk, 1)
        c.c(e, 0, pk, 0)
        tl = c.to(pk, "t l l")
        up = c.to((tl, 1), "unpack f f")
        tw = c.obj("tabwrite acparams")
        c.c(up, 1, tw, 1)
        c.c(up, 0, tw, 0)
        c.c(c.m((tl, 0), "$2 $1"), 0, c.obj("s ac-param"), 0)
        tr = c.to((t, 0), "t b f")
        ex = c.to((tr, 1), f"expr $f1; {k}")
        tw2 = c.obj("tabwrite acraw")
        c.c(ex, 1, tw2, 1)
        c.c(ex, 0, tw2, 0)
        c.c(c.m((tr, 0), "1"), 0, c.obj(f"v acknown{k}"), 0)
    c = c0
    r = c.recv("ac-param")
    names = [n for p in PAGES for _, n, _ in p]
    rt = c.to(r, "route " + " ".join(str(i) for i in range(4 * NP)))
    for i, n in enumerate(names):
        pc, inl = window(c, f"param-{n}", (rt, i))
        tb = pc.to(inl, "t b f")
        pc.c(tb, 1, pc.obj("v " + n), 0)
        # (a value a morph or a macro offset moves is not your hand: it neither shows nor stops the morph)
        # (your hand, not a morph or a macro: with MEMORY on, kept for the playing section)
        mem = [] if n == "acinput" else [If("acmemon", [T("acsnapt", f"(int(acsec) % {_S.NSNAP})*{len(names)} + {i}", "1"),
                                                         T("acsnapv", f"(int(acsec) % {_S.NSNAP})*{len(names)} + {i}", n)])]
        run_steps(pc, (tb, 0), SIDE.get(i, []) + [If("acmorphing == 0", [T("acmtouch", i, "1"), V("aclastk", str(i)),
                                                                         Call("ac-oledknob")] + mem), Send("ac-dirty")])
    # the scaled length shown on the screen
    return c


def keys():
    c = keys_c = Canvas("keys", w=3200)
    c.comment("The Organelle keys are functions: low octave = knob pages, harmony and form (aux + key = that SETUP "
              "page), top octave = layers, input, Freeze, transport. Hold Root (low G) and play a key or MIDI note, "
              "or turn knob 1: the next key. Aux tap: next page. Footswitch: change now.")
    nc, _ = window(c, "notesRaw", w=3200)
    up = nc.to(nc.recv("notesRaw"), "unpack f f")
    nc.c(up, 1, nc.obj("v ackv"), 0)
    kb = nc.to(up, "t b f")
    nc.c(kb, 1, nc.obj("v ackn"), 0)
    run_steps(nc, (kb, 0), [Send("ac-hintstop"), If("ackv > 0", [
        # a key that does something when held: its hint, 0.25 s in, if it is still held alone
        If("acauxheld == 0 && acrkey == 0 && acbdown == 0 && acroothold == 0",
           [V("achk", "ackn"), Arm("ac-hint", "250", stop="ac-hintstop")]),
        V("acauxused", "acauxheld || acauxused"),
        # top E (motion) / D# (bells) held: a low key picks its rhythm
        If(f"ackn == {MOTION_KEY} || ackn == {BELLS_KEY}", [V("acrkey", f"1 + (ackn == {BELLS_KEY})")]),
        # top B held: the next key is a slot (low C..B = 1-12, top C..D# = 13-16) - loaded, or with aux saved
        If(f"ackn == {SAVE_KEY}", [X("1; 0; 0", "v acbdown", "v acbused", "v acbcmp"),
                                   Arm("ac-cmphold", "600", stop="ac-bstop")],
           [If("acbdown", [V("acbused", "1"), Send("ac-bstop"), If("ackn >= 60 && ackn <= 75", [
               V("acslot", "ackn - 60"), Call("ac-slotcheck"),
               If("acauxheld", [Call("ac-savepiece")], [Call("ac-loadpiece")])])],
              [If(f"acroothold && ackn != {ROOT_KEY}", [V("acrootn", "int(ackn) % 12"), Call("ac-rootset")],
                  [SendL("ac-fkey", ["ackn"])])])])],
        [If(f"ackn == {ROOT_KEY}", [V("acroothold", "0")]),
         If(f"ackn == {MOTION_KEY} || ackn == {BELLS_KEY}", [V("acrkey", "0")]),
         # a layer key let go: a tap takes it in / out; a hold already opened its SHAPE page
         If("acshk >= 0 && ackn - 72 == acshk", [Send("ac-shpstop"), If("acshkh == 0", [
             If(f"acshk == {i}", [Call(f"ac-laytog{i}")]) for i in range(len(LAYER_KEYS))]), V("acshk", "-1")]),
         # top G# let go: a tap steps the input mode; a hold already opened the INPUT page
         If(f"ackn == {INPUT_KEY} && acinkh >= 0", [Send("ac-inhstop"), If("acinkh == 0", [Call("ac-inmodestep")]),
                                                  V("acinkh", "-1")]),
         # top B let go: a tap is a new piece (aux: the SAVES page); a hold was COMPARE, which ends
         If(f"ackn == {SAVE_KEY} && acbdown", [Send("ac-bstop"),
            If("acbcmp", [Call("ac-cmpoff")], [If("acbused == 0", [
                If("acauxheld", [V("acsetup", "1"), V("acsetpg", str(SAVES_PAGE)), Call("ac-oledsetup")],
                   [Call("ac-newkey")])])]),
            X("0; 0", "v acbdown", "v acbcmp")]),
         # top A let go (aux + A): a tap glides back to the anchor (or sets it); a hold already anchored here
         If(f"ackn == {ANCHOR_KEY} && acanp", [Send("ac-ancstop"), If("acanheld == 0", [Call("ac-anchortap")]),
                                              X("0; 0", "v acanp", "v acanheld")]),
         # low F let go: (a hold already opened the GLIDE page)
         If(f"ackn == {GLIDE_KEY}", [Send("ac-glstop")]),
         If(" || ".join(f"ackn == {60 + k}" for _, k in _S.MIRRORS), [Send("ac-mhstop")]),
         # low A let go: a tap changes to the next chord now; a hold already opened the CHORD page
         If(f"ackn == {CHORD_KEY}", [Send("ac-rrstop"), If("acrr == 0", [Call("ac-chordnow")]), V("acrr", "-1")]),
         # low B let go: a tap is the next section; a hold (0.6 s) already held or released the section
         If(f"ackn == {SECTION_KEY} && acsbk >= 0", [Send("ac-sbstop"), If("acsbk == 0", [Call("ac-secnow")]),
                                                    V("acsbk", "-1")])])])
    mo = c.ch(c.recv("ac-fkey"), "- 60", "moses 12")
    lsel = c.to((mo, 0), "sel " + " ".join(str(i) for i in range(12)))
    tsel = c.ch((mo, 1), "- 12", "sel " + " ".join(str(i) for i in range(12)))
    c.col()

    def layer(i, var, label, g):
        # a tap (on its release): in (always on) if it's silent now, out if it plays; held 0.5 s: its SHAPE page;
        # aux + tap: the layer's page (its sound, in / out / auto, level, reverb send)
        # (the bells: out only if you could hear them - in, or a strike in the last 6 s: a layer that is on but has
        # not struck yet sounds silent; brought in, a note at once, as the fade begins)
        on = f"{g} > 0.01" + (" && (acmbell == 2 || acnow - acblt < 6000)" if label == "bells" else "")
        now = [Later("ac-bellnow", 400)] if label == "bells" else []
        proc(c, f"ac-laytog{i}", [If(on, [V(var, "0"), Toast(label + " out")], [V(var, "2"), Toast(label + " in")] + now),
                                  V("acfade", _S.LFADE), Call("ac-layers")])
        return [If("acauxheld", [V("acsetup", "1"), V("acsetpg", str(_S.LAYER_PAGE0 + i)), Call("ac-oledsetup")],
                   [X(f"{i}; 0", "v acshk", "v acshkh"), Arm("ac-shphold", "500", stop="ac-shpstop")])]

    def page(p):
        return [V("acpage", str(p)), If("acsetup", [V("acsetup", "0"), Send("ac-save"), Call("ac-oledall")]),
                Call("ac-oledpage")]

    low = [page(LOW_PAGES[k]) if k in LOW_PAGES else None for k in range(12)]
    # low D, D#, E: their page at once; held 0.5 s, a SETUP page as a quick page (gen_setup.MIRRORS)
    for j, (_, k) in enumerate(_S.MIRRORS):
        low[k] = page(LOW_PAGES[k]) + [V("acmirk", str(j)), Arm("ac-mhold", "500", stop="ac-mhstop")]
    # low F: the PERFORM page at once (as every page key); held 0.5 s, the GLIDE page too
    low[GLIDE_KEY - 60] = page(LOW_PAGES[GLIDE_KEY - 60]) + [Arm("ac-glhold", "500", stop="ac-glstop")]
    low[7] = [V("acroothold", "1"), Toast("root: note or knob 1")]
    low[9] = [V("acrr", "0"), Arm("ac-chordhold", "500", stop="ac-rrstop")]
    low[10] = [Call("ac-resolvetoggle")]
    low[11] = [V("acsbk", "0"), Arm("ac-sbhold", "600", stop="ac-sbstop")]      # (its release: above)
    proc(c, "ac-secnow", [V("acsec", "acsec+1"), Call("ac-section"), Toast("next section")])
    proc(c, "ac-sbhold", [V("acsbk", "1"), V("acsecfz", "1 - acsecfz"),
                          If("acsecfz", [Toast("section held")], [Toast("section moves on")]), Call("ac-oledbottom")])
    for i, lk in enumerate(LAYER_KEYS):
        proc(c, f"ac-laykey{i}", layer(i, *lk))
    top = [[Call(f"ac-laykey{i}")] for i in range(len(LAYER_KEYS))] + [
        [If("acauxheld", [Call("ac-capture")], [V("acinkh", "0"), Arm("ac-inhold", "500", stop="ac-inhstop")])],
        [If("acauxheld", [X("1; 0", "v acanp", "v acanheld"), Arm("ac-ancheld", "800", stop="ac-ancstop")],
            [Call("ac-freezetoggle")])],
        [If("acauxheld", [Call("ac-modetoggle")], [Call("ac-startstop")])],
        [],          # top B: on its release (above)
    ]
    assert len(low) == len(LOW_KEYS) and len(top) == len(TOP_KEYS)
    for i, f in enumerate(low):
        kc, inl = window(c, f"lowkey{i}", (lsel, i))
        b = kc.to(inl, "t b")
        # top E / D# held (with or without aux): a low key picks the motion's / the bells' rhythm - and the held key
        # then neither opens its SHAPE page nor takes the layer in / out when let go; aux + a low key: that SETUP page
        pick = [V("acrsel", str(i)), Send("ac-shpstop"), V("acshkh", "1")]
        run_steps(kc, (b, 0), [If("acrkey == 1", pick + [Call("ac-mop")], [
            If("acrkey == 2", pick + [Call("ac-bop")], [If("acauxheld", [
                V("acsetup", "1"), V("acsetpg", str(GROUP_START[GROUP_KEYS.index(i)])), Call("ac-oledsetup")]
                if i in GROUP_KEYS else [], f)])])])
    for i, f in enumerate(top):
        kc, inl = window(c, f"topkey{i}", (tsel, i))
        run_steps(kc, (kc.to(inl, "t b"), 0), f)
    # top B held 0.6 s with no key: COMPARE (the slot as saved) until it is let go
    proc(c, "ac-cmphold", [If("acbdown && acbused == 0", [V("acbcmp", "1"), Call("ac-cmpon")])])
    proc(c, "ac-ancheld", [V("acanheld", "1"), Call("ac-anchorset")])
    proc(c, "ac-rootset", [V("acpend", "acrootn"), Send("ac-keytoast"), Call("ac-chordnext")])
    # low A held 0.5 s: the CHORD page (knob 1 picks the next chord; gen_setup)
    proc(c, "ac-shphold", [V("acshkh", "1"), V("acsetup", "1"), V("acsetpg", f"{_S.SHAPE_PAGE0} + acshk"),
                           Call("ac-oledsetup")])
    proc(c, "ac-inmodestep", [V("acinmode", "(acinmode+1) % 8"), Call("ac-inputupd"), Call("ac-inmodetoast"),
                              Call("ac-scr5")])
    # top G# held 0.5 s: the INPUT page (gen_setup)
    proc(c, "ac-inhold", [V("acinkh", "1"), V("acsetup", "1"), V("acsetpg", str(_S.INPUT_PAGE)), Call("ac-oledsetup")])
    # low F held 0.5 s: the GLIDE page (the glide times; gen_setup)
    proc(c, "ac-mhold", [V("acsetup", "1"), V("acsetpg", f"{_S.MIRROR0} + acmirk"), Call("ac-oledsetup")])
    proc(c, "ac-hint", [If("achints && acsetup == 0", [If(f"achk == {n}", [Toast(t)]) for n, t in sorted(HINTS.items())])])
    proc(c, "ac-glhold", [V("acsetup", "1"), V("acsetpg", str(_S.GLIDE_PAGE)), Call("ac-oledsetup")])
    proc(c, "ac-chordhold", [V("acrr", "1"), V("acsetup", "1"), V("acsetpg", str(_S.CHORD_PAGE)), Call("ac-oledsetup")])
    proc(c, "ac-chordnow", [Call("ac-change"), Toast("chord change")])
    proc(c, "ac-resolvetoggle", [V("acres", "1 - acres"), Call("ac-resolveupd")])
    proc(c, "ac-resolveupd", [Call("ac-change"),
                              If("acres", [Toast("resolve - open fifths")], [Toast("resolve released")])])
    proc(c, "ac-freezetoggle", [
        V("acvfreeze", "1-acvfreeze"), V("acfreeze", "acvfreeze"), Call("ac-freezeupd"), Call("ac-revupd"),
        If("acvfreeze", [Toast("freeze: verb + cloud")], [Toast("freeze released")]), Call("ac-oledbottom")])
    Line("ac-keytoast", "list next key $1", [("s", "acpend", NOTE_NAMES)], "ac-toast")(c)
    Line("ac-inmodetoast", "list input $1", [("s", "acinmode", INMODES)], "ac-toast")(c)
    # aux: knob page
    c, _ = window(c, "aux", w=3200)
    a = c.ch(c.recv("aux"), "sel 0")
    b = c.to((a, 1), "t b")
    run_steps(c, (b, 0), [X("1; 0; 0", "v acauxheld", "v acauxused", "v acauxlong")])
    run_steps(c, (a, 0), [V("acauxheld", "0"), If("acauxlong", [V("acauxlong", "0"), If("acauxused == 0", [
        V("acsetup", "0"), Send("ac-save"), Call("ac-oledall"), Toast("settings saved")])], [
        If("acauxused == 0", [If("acsetup", [If(f"acsetpg >= {NSET}", [
        # (a quick page: aux leaves it)
        V("acsetup", "0"), Send("ac-save"), Call("ac-oledall")], [
        V("acsetpg", f"(acsetpg + 1) % {NSET}"), Call("ac-oledsetup")])], [
        V("acpage", f"(acpage+1) % {NP}"), Call("ac-oledpage")])])])])
    f = c.ch(c.recv("fs"), "sel 0")
    c.c(c.to((f, 1), "t b"), 0, c.obj("s ac-change"), 0)
    return keys_c


def screen():
    c = Canvas("screen", w=3600)
    c.comment("Line 1 state, 2 key/scale/voicing, 3 pad timbres + texture (and toasts), 4-5 the knob page")
    # (ac-txt1-3 reach no screen on the Organelle (only lines 4-5 are drawn, gen_oled), but they are the checks'
    # readout of the piece's state - form, key, scale, pad types: tools/ci_check.py reads them. They compute on a
    # section or chord change only, so they cost next to nothing; keep them.)
    proc(c, "ac-scr", [Call(f"ac-scr{i}") for i in range(1, 6)])
    # line 1
    s1 = c.ch(c.recv("ac-scr1"), "expr if(acready && acstopped, 4, if(acstopped, 3, if(acended || acrun==0, 2, acmode)))",
              "sel 0 1 2 3 4")
    c.c(c.m((s1, 3), "list STOPPED - A# start"), 0, c.obj("s ac-txt1"), 0)
    c.c(c.to((s1, 4), "t b"), 0, c.obj("s ac-scr1r"), 0)
    c.c(c.to((s1, 0), "t b"), 0, c.obj("s ac-scr1d"), 0)
    c.c(c.to((s1, 1), "t b"), 0, c.obj("s ac-scr1c"), 0)
    c.c(c.m((s1, 2), "list FIN - B new piece"), 0, c.obj("s ac-txt1"), 0)
    c.col()
    Line("ac-scr1r", "list READY $1 - A# go", [("s", "acmode", ["DRIFT", "COMPOSE"])], "ac-txt1")(c)
    Line("ac-scr1d", "list DRIFT $1 $2",
         [("s", "acrole", ROLES), ("f", "acseed % 10000")], "ac-txt1")(c)
    Line("ac-scr1c", "list COMP $1 of $2 $3",
         [("f", "acsec+1"), ("f", "acnsec"),
          ("s", "acrole", ROLES)], "ac-txt1")(c)
    Line("ac-scr2", "list $1 $2 $3",
         [("s", "int(actonic) % 12", NOTE_NAMES), ("s", "acsci", [n for n, _ in SCALES]),
          ("s", "acfam", [n for n, _, _ in FAMILIES])], "ac-txt2")(c)
    # the OLED's line 2: the chord now and the next one (key and scale are on the bottom line)
    Line("ac-scr2", "list $1 > $2", [("s", "acchn", CHORD_NAMES), ("s", "acnxn", CHORD_NAMES)], "ac-oledtop")(c)
    Line("ac-scr3", "list $1 $2 $3 $4 $5",
         [("s", f"acflav[{k}]", FLAVOURS) for k in range(4)] + [("s", "actex1", TEXTURES)], "ac-txt3")(c)
    for ln in (4, 5):
        s = c.ch(c.recv(f"ac-scr{ln}"), "expr acpage", "sel " + " ".join(str(i) for i in range(NP)))
        for i in range(NP):
            c.c(c.to((s, i), "t b"), 0, c.obj(f"s ac-scr{ln}p{i}"), 0)
    c.col()
    Line("ac-scr4p0", "list Dens $1 Tide $2", [("f", "int(acdens*100)"), ("f", "int(actide*100)")], "ac-txt4")(c)
    Line("ac-scr5p0", "list Colr $1 In $2 $3",
         [("f", "int(accolor*100)"), ("f", "int(acinput*100)"),
          ("s", f"if(acinmode==0, {len(INMODES)} + acinclass, acinmode)", INMODES + ["auto", "pitched", "plucked", "texture"])],
         "ac-txt5")(c)
    Line("ac-scr4p1", "list Mix $1 Verb $2", [("f", "int(acrvmix*100)"),
                                              ("s", "if(acrvtype < 0.2, 0, 1 + min(3, int((acrvtype-0.2)/0.2)))", VERBS)],
         "ac-txt4")(c)
    Line("ac-scr5p1", "list Time $1 s Tone $2",
         [("f", "int(1.5 + 28.5*pow(acrvtime, 1.5))"), ("f", "int(acrvtone*100)")], "ac-txt5")(c)
    Line("ac-scr4p2", "list Len $1 min Weird $2", [("f", "int(5 + 25*aclen)"), ("f", "int(acweird*100)")],
         "ac-txt4")(c)
    Line("ac-scr5p2", "list Mot $1 Rhy $2", [("f", "int(acmotion*100)"), ("f", "int(acrhythm*100)")], "ac-txt5")(c)
    # the SENDS pages: "Drone 50 Pads 50" ...
    for pg in range(3, len(PAGES)):
        for ln, pair in ((4, PAGES[pg][:2]), (5, PAGES[pg][2:])):
            Line(f"ac-scr{ln}p{pg}", "list " + " ".join(f"{lab} ${i + 1}" for i, (lab, _, _) in enumerate(pair)),
                 [("f", f"int({n}*100)") for _, n, _ in pair], f"ac-txt{ln}")(c)
    # LED: green drifting, blue composing, off when finished; white flash on a chord change
    led = c.obj("s led")
    lc = c.ch(c.recv("ac-led"), "expr if(acended || acstopped, 0, if(acmode, 5, 3))")
    c.c(lc, 0, led, 0)
    fl = c.to(c.recv("ac-flash"), "t b b")
    c.c(c.to((fl, 0), "delay 150"), 0, c.obj("s ac-led"), 0)
    c.c(c.m((fl, 1), "7"), 0, led, 0)
    c.sub(led_beat())
    return c


def led_beat():
    """SETUP DISPLAY LED beat: the LED lights while the harmony bed (drone, sub) is louder than its own running
    average, so it blinks at the bed's beating; computes only while chosen and a piece plays (each ac-led - a state
    change or a flash's end - turns it on or off; off, the LED shows the state as before)"""
    c = Canvas("led-beat", w=900, h=500)
    sw = c.obj("switch~")
    c.c(c.m(c.obj("loadbang"), "0"), 0, sw, 0)
    on = c.ch(c.recv("ac-led"), "expr acledm && acrun && acended == 0 && acstopped == 0", "change")
    c.c(on, 0, sw, 0)
    e = c.ch(c.obj("r~ ac-bedmono"), "env~ 1024 256", "t b f")    # (dB every 5.8 ms)
    c.c(e, 1, c.obj("v acledin"), 0)
    run_steps(c, (e, 0), [
        V("aclbavg", "if(aclbavg < 1, acledin, aclbavg*0.97 + acledin*0.03)"),
        V("aclbnew", "if(acledin > aclbavg + 0.4, 1, if(acledin < aclbavg - 0.2, 0, aclbon))"),
        If("aclbnew != aclbon", [V("aclbon", "aclbnew"), SendL("led", ["if(aclbon, if(acmode, 5, 3), 0)"])]),
    ])
    return c
