"""Bells and motion engines (SETUP page 9): the struck bars (the bells' own), FM pings (the motion's own), a filtered
analog blip, a wooden bar, a glassy wavetable and a metallophone - each one available to both layers.

The bells' bars and the motion's FM pings stay in gen_dsp.bells() / motion_fm(); this module builds the other
engines of each layer, each in its own switched subpatch (on only while chosen and its layer plays: no cost
otherwise). Bell engines throw to the mix like the bells; motion engines throw to ac-mvL / ac-mvR, where the
motion's tempo echoes and soft limit (gen_dsp.motion()) take them."""
from pdlib import Canvas
from gen_dsp import switched, mul, add, throws_to
from data import STRIKES, STRIKE_GAIN, STRIKE_DEC, STRIKE_MDEC, WAVETABLES, MODES

LAYERS = {   # layer: (note message, voices, gain prefix, its own engine)
    "bell": ("ac-bell", 2, "ac-g-bel", "bars"),
    "motion": ("ac-mnote", 3, "ac-g-mot", "fm"),
}


def wavetables():
    c = Canvas("wavetables")
    c.comment("The glassy wavetables of the glass pad and the wave engine (2048 points + 3 guard points)")
    lb = c.obj("loadbang")
    for name, harm in WAVETABLES.items():
        c.obj(f"array define {name} 2051")
        amps = [harm.get(n, 0) for n in range(1, max(harm) + 1)]
        c.m(lb, f"; {name} sinesum 2048 " + " ".join(f"{a:g}" for a in amps) + f"; {name} normalize 1")
    return c


def _voices(s, layer):
    """the layer's notes dealt in turn to its voices: per voice an object whose outlets give note, velocity, pan
    (right to left: the note comes last). Motion notes carry a delay (swing) and wait for it."""
    recv, n, _, _ = LAYERS[layer]
    tl = s.to(s.recv(recv), "t l b")
    cnt = s.obj("f")
    s.c(tl, 1, cnt, 0)
    s.c(s.ch(cnt, "+ 1", f"% {n}"), 0, cnt, 1)
    lp = s.obj("list prepend")
    s.c(cnt, 0, lp, 1)
    s.c(tl, 0, lp, 0)
    rt = s.to(lp, "route " + " ".join(str(j) for j in range(n)))
    outs = []
    for j in range(n):
        if layer == "bell":
            outs.append(s.to((rt, j), "unpack f f f"))
        else:
            up = s.to((rt, j), "unpack f f f f")
            pk = s.obj("pack f f f")
            pp = s.obj("pipe f f f 0")
            s.c(up, 2, pp, 3)
            s.c(up, 3, pk, 2)
            s.c(up, 1, pk, 1)
            s.c(up, 0, pk, 0)
            s.c(pk, 0, pp, 0)
            outs.append(pp)
    return outs


def _env(s, vel, hz, amp, att, dec, slen, sq=True):
    """a struck envelope: velocity x amp, attack att ms, decay dec ms x the engine's length value slen - started by
    the note (hz arrives last; vel is stored first). Returns a vline~ (squared: an exponential-like decay)."""
    ex = s.obj(f"expr $f2*{amp}; {dec}*{slen}")
    s.c(vel, 0, ex, 1)
    s.c(hz, 0, ex, 0)
    pk = s.obj("pack f f")
    s.c(ex, 1, pk, 1)
    s.c(ex, 0, pk, 0)
    e = s.ch(s.m(pk, f"$1 {att}, 0 $2 {att}"), "vline~")
    return mul(s, e, e) if sq else e


def _partials(s, vel, hz, parts, dec, slen, scale_hz=None):
    """sine partials (ratio, amp, decay factor) of hz, each with its own struck envelope; ratios None = from
    [r ac-bellset] (the piece's bar tuning)"""
    sm = s.obj("*~ 1")
    for k, (ratio, amp, df) in enumerate(parts):
        fr = s.to(hz, f"* {ratio if ratio is not None else 1}")
        if ratio is None:
            s.c(scale_hz, k, fr, 1)
        e = _env(s, vel, hz, amp, 1 if df < 0.3 else 2, int(dec * df), slen)
        s.c(mul(s, s.to(fr, "osc~"), e), 0, sm, 0)
    return sm


def engine(layer, kind):
    recv, n, gp, _ = LAYERS[layer]
    idx = STRIKES.index(kind)
    s, ln = switched(f"{layer}-{kind}", f"{gp}{idx}")
    s.comment({"bars": "Bars: the bells' 3-partial struck bars, at the piece's tuning",
               "fm": "FM: a ping - a carrier and a modulator at the piece's ratio, the index falling fast",
               "blip": "Blip: an analog blip - a saw and a sub sine, a pitch flick, through a resonant low-pass "
                       "that closes fast",
               "wood": "Wood: a wooden bar - a mallet knock and three short modes (a marimba's 1 : 3.9 : 9.2)",
               "wave": "Wave: a glassy wavetable - it strikes bright (acwtB) and settles to its body (acwtA), "
                       "with a faint octave shimmer",
               "metal": "Metal: a metallophone - vibraphone modes (1 : 4 : 10), a beating twin, the motor's "
                        "tremolo",
               "kalimba": "Kalimba: a thumb piano - a warm tine (the note and its far, quickly fading overtones "
                          "5.9 and 13.6) and the click of the thumb",
               "steel": "Steel: a steel pan - the note, its octave and twelfth tuned in, a hair of pitch bend up "
                        "at the strike",
               "pluck": "Pluck: a plucked string - harmonics 1-6 at 1/n, the higher ones dying sooner, a short "
                        "bright attack",
               "bowl": "Bowl: a singing bowl's modes (1 : 2.76 : 5.4 : 8.9), the lower two beating with their twins, "
                       "struck by a soft mallet",
               "plate": "Plate: a thin metal plate's close, inharmonic modes (1 : 1.59 : 2.14 : 2.30 : 2.65 : 3.6)",
               "crystal": "Crystal: a wine glass's modes (1 : 2.32 : 4.25 : 6.63), long and pure, the fundamental "
                          "beating slowly",
               "lpg": "LPG: a west-coast pluck - a sine through a wavefolder (harder notes fold brighter) and a "
                      "low-pass gate, the filter and the level closing together like a vactrol",
               "gong": "Gong: FM as on the DX7's bells - two modulators at inharmonic ratios (1.41, 2.83); the "
                       "index swells for 0.12 s after the strike, then falls slower than the level (a tam-tam's bloom)",
               "chip": "Chip: a game console's pulse - a narrow pulse for hard notes, a square for soft ones (on the motion, "
                       "each note an arpeggio: root, 5th, octave, 18 times a second), its "
                       "level stepping down in 16 steps (4-bit), a short tick of pitch at the start"}[kind])
    # the length of the layer's notes: the bells ring their full decay; the motion follows the piece's ping
    # decay (250-950 ms) times the engine's own factor
    # (a value per engine: [v] names are global)
    slen = f"acslen{layer}{kind}"
    lv = s.obj("v " + slen)
    if layer == "bell":
        s.c(s.m(s.obj("loadbang"), "1"), 0, lv, 0)
    else:
        t2 = s.to(s.recv("ac-mtimbre2"), "unpack f f")
        s.c(s.to((t2, 1), f"expr $f1/{STRIKE_DEC[kind]}*{STRIKE_MDEC[kind]}"), 0, lv, 0)
        s.c(s.m(s.obj("loadbang"), f"{600 / STRIKE_DEC[kind] * STRIKE_MDEC[kind]:.4f}"), 0, lv, 0)
    dec = STRIKE_DEC[kind]
    L, R = s.obj("*~"), s.obj("*~")
    s.c(ln, 0, L, 1)
    s.c(ln, 0, R, 1)
    noise = s.obj("noise~") if kind in ("wood", "bowl", "plate", "crystal") else None
    bset = s.to(s.recv("ac-bellset"), "unpack f f f") if kind == "bars" else None
    voices = _voices(s, layer)
    s.col()
    for up in voices:
        vel = (up, 1)                      # into each envelope's cold inlet, before the note
        hz = s.to((up, 0), "mtof")
        pn = s.to((up, 2), "expr cos($f1*1.5708); sin($f1*1.5708)")
        if kind == "bars":
            sig = _partials(s, vel, hz, [(None, 0.32, 1.0), (None, 0.15, 0.5), (None, 0.08, 0.21)], dec, slen, bset)
        elif kind == "fm":
            rat = s.to(hz, "* 1")
            s.c(s.recv("ac-mtimbre"), 0, rat, 1)
            ie = _env(s, vel, hz, 3.0, 1, int(dec * 0.12), slen, sq=False)
            fsig = s.to(hz, "sig~")
            dev = mul(s, mul(s, s.to(rat, "osc~"), ie), fsig)
            sig = mul(s, s.to(add(s, fsig, dev), "osc~"), _env(s, vel, hz, 0.5, 3, dec, slen))
        elif kind == "blip":
            # pitch: a flick down from a fifth above in 14 ms
            fl = s.obj("expr $f1*1.5; $f1")
            s.c(hz, 0, fl, 0)
            pk = s.obj("pack f f")
            s.c(fl, 1, pk, 1)
            s.c(fl, 0, pk, 0)
            fv = s.ch(s.m(pk, "$1, $2 14"), "vline~")
            saw = s.ch(fv, "phasor~", "-~ 0.5")
            sub = s.ch(s.to(fv, "*~ 0.5"), "osc~", "*~ 0.35")
            src = add(s, saw, sub)
            # cutoff: from 2-11x the note (by velocity) down to 1.2x
            cx = s.obj(f"expr $f1*(2 + 9*$f2); $f1*1.2; {int(dec * 0.35)}*{slen}")
            s.c(vel, 0, cx, 1)
            s.c(hz, 0, cx, 0)
            ck = s.obj("pack f f f")
            for i in (2, 1, 0):
                s.c(cx, i, ck, i)
            cf = s.ch(s.m(ck, "$1, $2 $3"), "vline~", "clip~ 30 12000")
            vf = s.obj("vcf~ 4")
            s.c(src, 0, vf, 0)
            s.c(cf, 0, vf, 1)
            sig = mul(s, s.to((vf, 1), "*~ 1"), _env(s, vel, hz, 0.6, 2, dec, slen))
        elif kind == "wood":
            sig = _partials(s, vel, hz, [(1, 0.5, 1.0), (3.93, 0.2, 0.2), (9.2, 0.07, 0.06)], dec, slen)
            # the mallet: a noise knock through a band-pass at about 2.5x the note
            kn = mul(s, noise, _env(s, vel, hz, 0.9, 0.5, 9, 1))
            bp = s.obj("bp~ 1000 2")
            s.c(kn, 0, bp, 0)
            s.c(s.to(hz, "* 2.5"), 0, bp, 1)
            s.c(bp, 0, sig, 0)
        elif kind == "wave":
            fs = s.to(hz, "sig~")
            ta, tb = s.to(fs, "tabosc4~ acwtA"), s.to(fs, "tabosc4~ acwtB")
            me = _env(s, vel, hz, 1.0, 1, int(dec * 0.25), slen, sq=False)    # bright at the strike
            mo = s.to(me, "clip~ 0 1")
            dif = s.obj("-~")
            s.c(tb, 0, dif, 0)
            s.c(ta, 0, dif, 1)
            body = add(s, ta, mul(s, dif, mo))
            sh = s.ch(s.to(fs, "*~ 2.003"), "tabosc4~ acwtB", "*~ 0.15")
            sig = mul(s, add(s, body, sh), _env(s, vel, hz, 0.45, 3, dec, slen))
        elif kind == "kalimba":
            sig = _partials(s, vel, hz, [(1, 0.55, 1.0), (5.9, 0.12, 0.12), (13.6, 0.05, 0.05)], dec, slen)
            ck = mul(s, s.obj("noise~"), _env(s, vel, hz, 0.35, 0.3, 4, 1))
            bp = s.obj("bp~ 3000 3")
            s.c(ck, 0, bp, 0)
            s.c(bp, 0, sig, 0)
        elif kind == "steel":
            # a bend: the note a quarter-tone sharp at the strike, settling in 60 ms
            bx = s.obj("expr $f1*1.015; $f1")
            s.c(hz, 0, bx, 0)
            pk = s.obj("pack f f")
            s.c(bx, 1, pk, 1)
            s.c(bx, 0, pk, 0)
            fv = s.ch(s.m(pk, "$1, $2 60"), "vline~")
            sig = s.obj("*~ 1")
            for ratio, amp, df in ((1, 0.45, 1.0), (2, 0.3, 0.6), (3, 0.16, 0.35)):
                e = _env(s, vel, hz, amp, 2, int(dec * df), slen)
                s.c(mul(s, s.ch(fv, f"*~ {ratio}", "osc~"), e), 0, sig, 0)
        elif kind == "pluck":
            sig = _partials(s, vel, hz, [(n, 0.5 / n, 1.0 / n ** 0.8) for n in range(1, 7)], dec, slen)
        elif kind in MODES:
            sig = _partials(s, vel, hz, [(r, a, d) for r, a, d, _ in MODES[kind]], dec, slen)
            for r, a, d, tw in MODES[kind]:
                if tw:          # the mode's twin, a few tenths of a Hz up: the slow beating of a real bowl
                    o = s.ch(s.to(hz, f"* {r}"), f"+ {tw}", "osc~")
                    s.c(mul(s, o, _env(s, vel, hz, a * 0.6, 2, int(dec * d), slen)), 0, sig, 0)
            # the strike: a short noise knock through a band at twice the note (softer for the bowl's mallet)
            kn = mul(s, noise, _env(s, vel, hz, {"bowl": 0.25, "plate": 0.5, "crystal": 0.3}[kind], 0.5, 5, 1))
            bp = s.obj("bp~ 1000 3")
            s.c(kn, 0, bp, 0)
            s.c(s.to(hz, "* 2"), 0, bp, 1)
            s.c(bp, 0, sig, 0)
        elif kind == "lpg":
            # the fold: sin(pi/2 x) - a sine below 1, folding back above it - its depth by velocity, falling
            fd = s.ch(_env(s, vel, hz, 3.0, 1, int(dec * 0.5), slen, sq=False), "+~ 0.6")
            x = mul(s, s.to(hz, "osc~"), fd)
            fo = s.ch(x, "*~ 0.25", "-~ 0.25", "cos~")
            # the gate: one envelope closes the low-pass (from the note + 6 kHz down to the note) and the level
            cf = s.to(add(s, s.to(hz, "sig~"), _env(s, vel, hz, 6000, 1, int(dec * 0.45), slen)), "clip~ 30 12000")
            lp = s.obj("vcf~ 0.8")
            s.c(fo, 0, lp, 0)
            s.c(cf, 0, lp, 1)
            sig = mul(s, s.to((lp, 1), "*~ 1"), _env(s, vel, hz, 0.55, 1, dec, slen))
        elif kind == "gong":
            fsig = s.to(hz, "sig~")
            i1 = _env(s, vel, hz, 4.5, 120, int(dec * 0.7), slen, sq=False)     # (rising 120 ms: the bloom)
            i2 = _env(s, vel, hz, 1.2, 40, int(dec * 0.3), slen, sq=False)
            d1 = mul(s, mul(s, s.ch(hz, "* 1.41", "osc~"), i1), fsig)
            d2 = mul(s, mul(s, s.ch(hz, "* 2.83", "osc~"), i2), fsig)
            car = s.to(add(s, add(s, fsig, d1), d2), "osc~")
            sig = mul(s, car, _env(s, vel, hz, 0.42, 4, dec, slen))
        elif kind == "chip":
            # the duty: 0.5 (soft) .. 0.125 (hard); a pitch tick from a 4th up in 25 ms
            du = s.obj("expr 0.5 - 0.375*$f1")
            s.c(vel, 0, du, 0)
            tk = s.obj("expr $f1*1.335; $f1")
            s.c(hz, 0, tk, 0)
            pk = s.obj("pack f f")
            s.c(tk, 1, pk, 1)
            s.c(tk, 0, pk, 0)
            fv = s.ch(s.m(pk, "$1, $2 25"), "vline~")
            pl = s.obj("expr~ ($v1 < $v2)*2 - 1")
            if layer == "motion":     # (the console arpeggio: each note runs root, 5th, octave, 18 times a second)
                fv = mul(s, fv, s.ch(s.obj("phasor~ 18"), "expr~ if($v1 < 0.333, 1, if($v1 < 0.667, 1.4983, 2))"))
            s.c(s.to(fv, "phasor~"), 0, pl, 0)
            s.c(s.to(du, "sig~"), 0, pl, 1)
            e = s.to(_env(s, vel, hz, 1.0, 1, dec, slen), "expr~ floor($v1*15)/15")
            sig = mul(s, s.to(pl, "lop~ 9000"), s.to(e, "*~ 0.22"))
        else:   # metal
            sig = _partials(s, vel, hz, [(1, 0.4, 1.0), (4.0, 0.12, 0.3), (10.0, 0.05, 0.08)], dec, slen)
            # a beating twin of the fundamental, 0.8 Hz up
            tw = s.ch(s.to(hz, "+ 0.8"), "osc~")
            s.c(mul(s, tw, _env(s, vel, hz, 0.14, 2, dec, slen)), 0, sig, 0)
        for side, dst in ((0, L), (1, R)):
            m = s.to(sig, "*~ 1")
            s.c(pn, side, m, 1)
            s.c(m, 0, dst, 0)
        s.col(170)
    g = STRIKE_GAIN[layer][kind] * (0.7 if layer == "bell" else 0.35)
    oL, oR = s.to(L, f"*~ {g}"), s.to(R, f"*~ {g}")
    if kind == "metal":       # the vibraphone's motor: a gentle tremolo on everything
        tr = s.ch(s.obj("osc~ 5.2"), "*~ 0.2", "+~ 0.8")
        oL, oR = mul(s, oL, tr), mul(s, oR, tr)
    if layer == "bell":
        throws_to("ac-sendb")(s, oL, oR, mix=1.1, send=1.0)
    else:
        s.c(oL, 0, s.obj("throw~ ac-mvL"), 0)
        s.c(oR, 0, s.obj("throw~ ac-mvR"), 0)
    return s


def engines():
    """every engine of both layers except each layer's own (in gen_dsp)"""
    return [engine(layer, k) for layer, (_, _, _, own) in LAYERS.items() for k in STRIKES if k != own]
