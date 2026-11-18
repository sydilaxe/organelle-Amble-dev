"""More sounds: electric / synthetic pad types, drone designs, the sub, electric textures, per-piece character
(chorus, tape, ring, crush) on the pads, and the vocoder (input speaks through a synth choir or the pads)."""
from pdlib import Canvas
from gen_dsp import switched, mul, add, ctl, throws, throws_to, _flav_inlets, _out, prm, prmc
from data import TEXG


# ---------------------------------------------------------------- pad types 6..9 (inlets: freq~, bright~)
def flav_saws():
    s, ln = switched("saws", "$0-fw6")
    s.comment("Saws: three detuned saws (an analog ensemble), low one left, high one right, each side through "
              "its own resonant low-pass that tracks the note")
    f, b = _flav_inlets(s, 2)
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    saws = [s.ch(mul(s, f, s.ch(P, f"*~ {2 * (d - 1):.4f}", "+~ 1")), "phasor~", "-~ 0.5") for d in (0.994, 1.0, 1.0065)]
    cf = s.to(mul(s, mul(s, f, s.ch(b, "*~ 9", "+~ 1.5")), s.to(Q, "+~ 0.5")), "clip~ 40 5500")
    outs = []
    for side in ((1, 0.7, 0.25), (0.25, 0.7, 1)):
        sm = s.obj("*~ 0.4")
        for sw, g in zip(saws, side):
            s.c(s.to(sw, f"*~ {g}"), 0, sm, 0)
        v = s.obj("vcf~ 1.6")
        s.c(sm, 0, v, 0)
        s.c(cf, 0, v, 1)
        outs.append(s.ch((v, 1), "hip~ 30", "*~ 2.8"))
    _out(s, outs[0], ln, outs[1])
    return s


def flav_pwm():
    s, ln = switched("pwm", "$0-fw7")
    s.comment("PWM: a pulse whose width breathes, through a slowly sweeping resonant filter (a Juno-like string); "
              "the right side's width moves the other way")
    f, b = _flav_inlets(s, 2)
    ph = s.to(f, "phasor~")
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    lfo = mul(s, s.ch(s.recv("$0-la"), "* 1.7", "osc~", "*~ 0.35"), s.to(P, "*~ 2"))
    sweep = mul(s, s.ch(s.recv("$0-lb"), "osc~", "*~ 0.5", "+~ 0.5"), s.to(Q, "*~ 2"))
    cf = s.to(mul(s, f, add(s, s.to(sweep, "*~ 4"), s.ch(b, "*~ 5", "+~ 1.2"))), "clip~ 40 5000")
    outs = []
    for sign in (1, -1):
        w = s.ch(lfo, f"*~ {sign}", "+~ 0.5")
        p2 = s.to(add(s, ph, w), "wrap~")
        pulse = s.obj("-~")
        s.c(ph, 0, pulse, 0)
        s.c(p2, 0, pulse, 1)
        v = s.obj("vcf~ 2.5")
        s.c(s.to(pulse, "hip~ 20"), 0, v, 0)
        s.c(cf, 0, v, 1)
        outs.append(s.to((v, 1), "*~ 0.75"))
    _out(s, outs[0], ln, outs[1])
    return s


def flav_digi():
    s, ln = switched("digi", "$0-fw8")
    s.comment("Digi: a sine ring-modulated at an inharmonic ratio, then bit-crushed and sample-rate reduced; "
              "the right side rings a hair higher and holds at a slower clock")
    f, b = _flav_inlets(s, 2)
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    car = s.to(f, "osc~")
    outs = []
    for k, (rm, clk) in enumerate(((1.0, 1.0), (1.012, 0.83))):
        rr = s.to(f, f"*~ {1.4142 * rm}")
        s.c(s.to(s.recv("ac-fmr"), f"* {rm}"), 0, rr, 1)
        ring = mul(s, car, s.to(mul(s, rr, s.to(P, "+~ 0.5")), "osc~"))
        x = add(s, s.to(car, "*~ 0.6"), s.to(ring, "*~ 0.5"))
        lv = s.obj("*~ 16")
        s.c(x, 0, lv, 0)
        ctl(s, lv, "ac-weird", "40 - 34*$f1")
        q = s.obj("-~")
        s.c(lv, 0, q, 0)
        s.c(s.to(lv, "wrap~"), 0, q, 1)
        inv = s.obj("/~ 16")
        s.c(q, 0, inv, 0)
        ctl(s, inv, "ac-weird", "40 - 34*$f1")
        hold = s.obj("samphold~")
        s.c(inv, 0, hold, 0)
        s.c(s.to(mul(s, s.ch(b, f"*~ {8000 * clk}", f"+~ {3000 * clk}"), s.ch(Q, "*~ -1", "+~ 1.5")), "phasor~"), 0, hold, 1)
        outs.append(s.ch(hold, "lop~ 7000", "hip~ 20", "*~ 0.5"))
    _out(s, outs[0], ln, outs[1])
    return s


def flav_sync():
    s, ln = switched("sync", "$0-fw9")
    s.comment("Sync: a hard-synced saw whose slave ratio sweeps (brightness and a slow LFO) - an electric lead; "
              "the right side's slave runs a little ahead")
    f, b = _flav_inlets(s, 2)
    ph = s.to(f, "phasor~")
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    ratio = mul(s, add(s, s.ch(b, "*~ 3", "+~ 1.3"), mul(s, s.ch(s.recv("$0-lb"), "* 1.3", "osc~", "*~ 0.6"),
                                                             s.to(Q, "*~ 2"))), s.to(P, "+~ 0.5"))
    win = s.ch(ph, "*~ -1", "+~ 1")
    outs = []
    for off in (0, 0.11):
        r = s.to(ratio, f"+~ {off}") if off else ratio
        sl = s.ch(mul(s, ph, r), "wrap~", "-~ 0.5")
        outs.append(s.ch(mul(s, sl, win), "lop~ 4500", "hip~ 30", "*~ 1.1"))
    _out(s, outs[0], ln, outs[1])
    return s


def flav_tine():
    s, ln = switched("tine", "$0-fw10")
    s.comment("Tine: an electric-piano bell that strikes itself every few seconds - a soft FM body and a "
              "bright tine partial that rings out; the tines sit left and right, a hair apart")
    f, b = _flav_inlets(s, 2)
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    st = s.to(mul(s, s.ch(s.recv("$0-lb"), "* 0.6", "+ 0.12", "sig~"), s.to(Q, "+~ 0.5")), "phasor~")
    dec = s.ch(st, "*~ -1", "+~ 1")
    e2 = mul(s, dec, dec)
    e3 = mul(s, e2, dec)
    e6 = mul(s, e3, e3)
    idx = s.ch(e2, "*~ 1.4", "+~ 0.2")
    amp = s.ch(e3, "*~ 0.6", "+~ 0.4")
    outs = []
    for d, r, pt in ((1.0, 7, 1.0), (1.0023, 7.03, 0.55)):
        fd = s.to(f, f"*~ {d}")
        body = s.ch(add(s, fd, mul(s, mul(s, s.to(fd, "osc~"), idx), fd)), "osc~")
        tine = mul(s, mul(s, s.ch(s.to(f, f"*~ {r}"), "osc~"), s.to(mul(s, e6, s.ch(b, "*~ 0.6", "+~ 0.25")), f"*~ {0.5 * pt}")),
                   s.to(P, "*~ 2"))
        outs.append(s.to(add(s, s.to(mul(s, body, amp), "*~ 0.45"), tine), "*~ 0.8"))
    # mono-safe: the right side keeps part of the left, so a mono sum never cancels
    _out(s, outs[0], ln, add(s, s.to(outs[0], "*~ 0.5"), s.to(outs[1], "*~ 0.65")))
    return s


def flav_sine():
    s, ln = switched("sine", "$0-fw11")
    s.comment("Sine: a harmonic sine pad - the fundamental and harmonics 2-6 at 1/n, brightness tilting the upper "
              "ones in; the right side a hair sharp, its odd and even harmonics balanced the other way")
    f, b = _flav_inlets(s, 2)
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    tilt = [None, b]
    for _ in range(4):
        tilt.append(mul(s, tilt[-1], b))
    P2 = s.to(P, "*~ 2")
    outs = []
    for d, oddeven in ((1.0, (1.0, 0.75)), (1.0009, (0.75, 1.0))):
        sm = s.obj("*~ 0.42")
        fd = mul(s, f, s.ch(Q, f"*~ {2 * (d - 1):.4f}", "+~ 1")) if d != 1.0 else f
        for n in range(1, 7):
            o = s.ch(s.to(fd, f"*~ {n}"), "osc~", f"*~ {1 / n * (oddeven[0] if n % 2 else oddeven[1]):.4f}")
            s.c(mul(s, mul(s, o, tilt[n - 1]), P2) if tilt[n - 1] is not None else o, 0, sm, 0)
        outs.append(sm)
    # mono-safe: the right side keeps part of the left
    _out(s, outs[0], ln, add(s, s.to(outs[0], "*~ 0.5"), s.to(outs[1], "*~ 0.65")))
    return s


def flav_glass():
    s, ln = switched("glass", "$0-fw12")
    s.comment("Glass: two glassy wavetables (acwtA, a soft body; acwtB, sparse high harmonics), brightness and a slow "
              "drift morphing between them; the right side a hair sharp, drifting the other way; a faint octave of "
              "the bright table on top")
    f, b = _flav_inlets(s, 2)
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    outs = []
    for d, rate, ph in ((1.0, 0.083, 0), (1.0011, 0.071, 0.5)):
        fr = s.to(f, f"*~ {d}")
        ta, tb = s.to(fr, "tabosc4~ acwtA"), s.to(fr, "tabosc4~ acwtB")
        lfo = s.obj(f"osc~ {rate}")
        s.c(s.m(s.obj("loadbang"), str(ph)), 0, lfo, 1)
        m = s.to(mul(s, add(s, s.to(b, "*~ 0.75"), s.ch(lfo, "*~ 0.2", "+~ 0.1")), s.to(P, "*~ 2")), "clip~ 0 1")
        dif = s.obj("-~")
        s.c(tb, 0, dif, 0)
        s.c(ta, 0, dif, 1)
        sm = s.obj("*~ 0.4")
        s.c(add(s, ta, mul(s, dif, m)), 0, sm, 0)
        s.c(mul(s, s.ch(s.to(fr, "*~ 2"), "tabosc4~ acwtB", "*~ 0.12"), s.to(Q, "*~ 2")), 0, sm, 0)
        outs.append(sm)
    _out(s, outs[0], ln, add(s, s.to(outs[0], "*~ 0.5"), s.to(outs[1], "*~ 0.65")))   # mono-safe
    return s


def flav_beat():
    s, ln = switched("beat", "$0-fw13")
    s.comment("Beat (after Frasil's PARTIALS): five partials, a touch stretched toward a bell, each pulsing at its own "
              "pace; a formant wanders across them (and brightness lifts it), so the spectrum moves while the note "
              "stays; odd partials to the left, even to the right")
    f, b = _flav_inlets(s, 2)
    # the formant's place (harmonic 1.5 .. 5): a slow sweep, lifted by brightness
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    pk = add(s, add(s, s.ch(s.obj("osc~ 0.043"), "*~ 1.2", "+~ 2.6"), s.to(b, "*~ 1.4")), s.ch(P, "-~ 0.5", "*~ 3"))
    L, R = s.obj("*~ 0.5"), s.obj("*~ 0.5")
    for n, rate, (gl, gr) in ((1, 0.31, (1, 1)), (2, 0.53, (0.3, 1.3)), (3, 0.79, (1.3, 0.3)), (4, 1.13, (0.35, 1.25)),
                              (5, 1.61, (1.25, 0.35))):
        st = n * (1 + 0.0035 * n * (n - 1))                 # a touch stretched
        o = s.ch(s.to(f, f"*~ {st:.4f}"), "osc~")
        beat = s.to(mul(s, s.ch(s.obj(f"osc~ {rate}"), "-~ 1"), s.to(Q, "*~ 0.8")), "+~ 1")
        d = s.ch(s.to(pk, f"-~ {n}"), "abs~")
        near = s.obj("/~")                                  # 1 / (1 + 0.8 d^2): the formant's lift
        s.c(s.obj("sig~ 1"), 0, near, 0)
        den = s.ch(mul(s, d, d), "*~ 0.8", "+~ 1")
        s.c(den, 0, near, 1)
        p = mul(s, mul(s, o, beat), s.to(near, f"*~ {1 / n ** 0.5:.3f}"))
        s.c(s.to(p, f"*~ {gl}"), 0, L, 0)
        s.c(s.to(p, f"*~ {gr}"), 0, R, 0)
    _out(s, L, ln, R)
    return s


def flav_reed():
    s, ln = switched("reed", "$0-fw14")
    s.comment("Reed: a clarinet-like tone - a sine driven into soft clipping (odd harmonics, more with brightness), "
              "a slow breathy vibrato, a gentle low-pass; the right side a hair sharp")
    f, b = _flav_inlets(s, 2)
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    drive = mul(s, s.ch(b, "*~ 5", "+~ 1.5"), s.to(P, "*~ 2"))
    outs = []
    for d, rate in ((1.0, 4.3), (1.0012, 4.7)):
        vib = s.to(mul(s, s.ch(s.obj(f"osc~ {rate}"), "*~ 0.003"), s.to(Q, "*~ 2")), f"+~ {d}")
        x = mul(s, s.ch(mul(s, f, vib), "osc~"), drive)
        clip = s.obj("/~")                       # x / (1 + |x|): odd harmonics
        s.c(x, 0, clip, 0)
        s.c(s.ch(x, "abs~", "+~ 1"), 0, clip, 1)
        outs.append(s.ch(clip, "lop~ 2600", "*~ 0.42"))
    _out(s, outs[0], ln, add(s, s.to(outs[0], "*~ 0.5"), s.to(outs[1], "*~ 0.65")))
    return s


def flav_organ():
    s, ln = switched("organ", "$0-fw15")
    s.comment("Organ: drawbars 16' 8' 5 1/3' 4' 2' (harmonics 1 2 3 4 8, the upper ones drawn out with brightness) "
              "and a slow rotary swell, opposite on the two sides")
    f, b = _flav_inlets(s, 2)
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    sm = s.obj("*~ 0.3")
    for h, a, br in ((1, 0.5, 0), (2, 0.45, 0), (3, 0.3, 0.5), (4, 0.25, 0.8), (8, 0.12, 1)):
        o = s.ch(s.to(f, f"*~ {h}"), "osc~", f"*~ {a}")
        o = mul(s, o, s.to(P, "*~ 2")) if h >= 3 else o
        s.c(mul(s, o, s.ch(b, f"*~ {br}", f"+~ {1 - br * 0.7:.2f}")) if br else o, 0, sm, 0)
    rot = mul(s, s.ch(s.obj("osc~ 0.7"), "*~ 0.25"), s.to(Q, "*~ 2"))
    _out(s, mul(s, sm, s.to(rot, "+~ 0.75")), ln, mul(s, sm, s.ch(rot, "*~ -1", "+~ 0.75")))
    return s


def flav_air():
    s, ln = switched("air", "$0-fw16")
    s.comment("Air: a flute - a pure tone with breath around it (noise through a narrow band on the note, more "
              "with brightness) and a slow vibrato that grows in; each side its own breath")
    f, b = _flav_inlets(s, 2)
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    vib = s.to(mul(s, s.ch(s.obj("osc~ 5.1"), "*~ 0.004"), s.to(Q, "*~ 2")), "+~ 1")
    fv = mul(s, f, vib)
    tone = s.ch(fv, "osc~", "*~ 0.35")
    outs = []
    for side in range(2):
        v = s.obj("vcf~ 9")
        s.c(s.obj("noise~"), 0, v, 0)
        s.c(fv, 0, v, 1)
        br = mul(s, mul(s, v, s.ch(b, "*~ 0.6", "+~ 0.25")), s.to(P, "*~ 2"))
        outs.append(add(s, tone, s.to(br, "*~ 0.9")))
    _out(s, outs[0], ln, outs[1])
    return s


def flav_cz():
    s, ln = switched("cz", "$0-fw17")
    s.comment("CZ: phase distortion (the Casio CZ) - a cosine read through a bent phase. Left: the bend moves the "
              "wave from a sine (no bend) towards a saw with brightness and a slow sweep; right: the resonant "
              "wave, a cosine at a higher ratio under a falling ramp, its 'resonance' sweeping the same way")
    f, b = _flav_inlets(s, 2)
    ph = s.to(f, "phasor~")
    sweep = s.ch(s.recv("$0-lb"), "osc~", "*~ 0.5", "+~ 0.5")
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    amt = s.to(mul(s, add(s, s.to(b, "*~ 0.75"), s.to(sweep, "*~ 0.3")), s.to(P, "*~ 2")), "clip~ 0 1")
    d = s.ch(amt, "*~ -0.44", "+~ 0.5")                     # the bend's knee: 0.5 (a sine) .. 0.06 (near a saw)
    bend = s.obj("expr~ cos(6.28319*if($v1 < $v2, $v1*0.5/$v2, 0.5 + ($v1 - $v2)*0.5/(1 - $v2)))")
    s.c(ph, 0, bend, 0)
    s.c(d, 0, bend, 1)
    r = s.to(mul(s, s.to(amt, "*~ 5"), s.to(Q, "*~ 2")), "+~ 1")      # resonance ratio 1 .. 6 (x2 by Resonance)
    res = s.obj("expr~ cos(6.28319*$v1*$v2)*(1 - $v1)")
    s.c(ph, 0, res, 0)
    s.c(r, 0, res, 1)
    L = s.ch(bend, "hip~ 20", "lop~ 6000", "*~ 0.34")
    R = s.ch(res, "hip~ 20", "lop~ 4500", "*~ 0.5")
    _out(s, add(s, L, s.to(R, "*~ 0.35")), ln, add(s, R, s.to(L, "*~ 0.35")))
    return s


VOWELS = [(800, 1150, 2900), (400, 1600, 2700), (350, 2000, 2800), (450, 800, 2830), (325, 700, 2530), (600, 1700, 2600), (500, 900, 2600), (700, 1500, 2600), (620, 1200, 2550)]      # F1 F2 F3 (Hz): a e i o u, then between them


def flav_choir():
    s, ln = switched("choir", "$0-fw18")
    s.comment("Choir: a glottal source (narrow pulses, softer and rounder when dark) through three formants that "
              "wander through nine vowels - a slow quasi-random drift of two unrelated cycles; the right side sings "
              "its own vowel a little apart, a hair sharp")
    f, b = _flav_inlets(s, 2)
    lb = s.obj("loadbang")
    for j in range(3):
        name = f"$0-vf{j}"
        s.obj(f"array define {name} {len(VOWELS) + 3}")
        vals = [VOWELS[-1][j]] + [v[j] for v in VOWELS] + [VOWELS[0][j], VOWELS[1][j]]
        s.c(s.m(lb, " ".join(str(x) for x in vals)), 0, s.obj(f"array set {name}"), 0)
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    expo = mul(s, s.ch(b, "*~ -8", "+~ 12"), s.ch(Q, "*~ -1", "+~ 1.5"))   # pulse narrowness: 12 (dark) .. 4 (bright)
    outs = []
    for side, (d, r1, r2) in enumerate(((1.0, 0.031, 0.047), (1.0025, 0.037, 0.043))):
        vib = s.ch(s.obj(f"osc~ {5.1 + 0.4 * side}"), "*~ 0.004", f"+~ {d}")
        ph = s.ch(mul(s, f, vib), "phasor~", "-~ 0.5", "*~ 2", "abs~")
        src = s.obj("pow~")
        s.c(ph, 0, src, 0)
        s.c(expo, 0, src, 1)
        drift = add(s, s.obj(f"osc~ {r1}"), s.ch(s.obj(f"osc~ {r2}"), "*~ 0.7"))
        idx = s.to(add(s, s.ch(drift, "*~ 0.294", "+~ 0.5", f"*~ {len(VOWELS) - 1}", "+~ 1"), s.ch(P, "-~ 0.5", "*~ 8")),
                   f"clip~ 1 {len(VOWELS)}")
        sm = s.obj("*~ 1")
        for j, (q, a) in enumerate(((7, 1.0), (10, 0.55), (14, 0.25))):
            fm = s.to(idx, f"tabread4~ $0-vf{j}")
            v = s.obj(f"vcf~ {q}")
            s.c(s.to(src, "hip~ 60"), 0, v, 0)
            s.c(fm, 0, v, 1)
            s.c(s.to(v, f"*~ {a}"), 0, sm, 0)
        outs.append(s.to(sm, "*~ 1.6"))
    _out(s, outs[0], ln, outs[1])
    return s


def flav_vosim():
    s, ln = switched("vosim", "$0-fw19")
    s.comment("VOSIM: each period of the note, a train of three sin-squared pulses at a formant frequency, each "
              "weaker than the last - a vowel-like, slightly nasal tone; the formant rises with brightness and "
              "sweeps slowly, the right side's a 3rd above")
    f, b = _flav_inlets(s, 2)
    ph = s.to(f, "phasor~")
    sweep = s.ch(s.recv("$0-la"), "osc~", "*~ 0.15", "+~ 1")
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    fmt = mul(s, mul(s, s.ch(b, "*~ 1600", "+~ 500"), sweep), s.to(P, "+~ 0.5"))
    outs = []
    for k in (1.0, 1.26):
        fx = s.to(fmt, f"*~ {k}")
        vs = s.obj("expr~ if($v1*$v2/max($v3, 1) < 3, pow(sin(3.14159*$v1*$v2/max($v3, 1)), 2)*"
                   "pow($v4, floor($v1*$v2/max($v3, 1))), 0)")
        s.c(s.ch(Q, "*~ 0.7", "+~ 0.3"), 0, vs, 3)
        s.c(ph, 0, vs, 0)
        s.c(fx, 0, vs, 1)
        s.c(f, 0, vs, 2)
        outs.append(s.ch(vs, "hip~ 40", "*~ 0.9"))
    _out(s, outs[0], ln, outs[1])
    return s


def flav_whistle():
    s, ln = switched("whistle", "$0-fw20")
    s.comment("Whistle: the chord whistled - a pure tone two octaves up with a slow, unsteady pitch and a vibrato "
              "that grows with brightness, breath around it (noise in a narrow band on the tone), the octave below "
              "faintly for body; one tone, each side its own breath (two tones a hair apart would beat away in mono)")
    f, b = _flav_inlets(s, 2)
    wob = s.ch(add(s, s.obj("osc~ 0.29"), s.ch(s.obj("osc~ 0.23"), "*~ 0.6")), "*~ 0.002", "+~ 1")
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    vib = mul(s, mul(s, s.ch(s.obj("osc~ 5.4"), "*~ 0.006"), b), s.to(Q, "*~ 2"))
    fw = mul(s, s.to(f, "*~ 4"), add(s, wob, vib))
    tone = s.ch(fw, "osc~", "*~ 0.4")
    body = s.ch(s.to(fw, "*~ 0.5"), "osc~", "*~ 0.08")
    outs = []
    for side in range(2):
        br = s.obj("vcf~ 25")
        s.c(s.obj("noise~"), 0, br, 0)
        s.c(fw, 0, br, 1)
        outs.append(add(s, add(s, tone, body), mul(s, s.to(br, "*~ 0.5"), s.to(P, "*~ 2"))))
    _out(s, outs[0], ln, outs[1])
    return s


def flav_lissa():
    s, ln = switched("lissa", "$0-fw21")
    s.comment("Lissajous: the two sides are the figure's two axes - the note on the left, its fifth (3:2) on the "
              "right drifting slowly in phase, so the stereo image turns; brightness adds each side's octave, and "
              "a little of each side crosses to the other")
    f, b = _flav_inlets(s, 2)
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    x = s.to(f, "osc~")
    y = s.to(add(s, mul(s, f, s.to(P, "+~ 1")), s.to(Q, "*~ 0.14")), "osc~")
    bx = mul(s, s.ch(s.to(f, "*~ 2"), "osc~"), s.to(b, "*~ 0.35"))
    by = mul(s, s.ch(s.to(f, "*~ 3"), "osc~"), s.to(b, "*~ 0.3"))
    L = s.to(add(s, add(s, x, bx), s.to(y, "*~ 0.25")), "*~ 0.45")
    R = s.to(add(s, add(s, y, by), s.to(x, "*~ 0.25")), "*~ 0.45")
    _out(s, L, ln, R)
    return s


def flav_chip():
    s, ln = switched("chip-pad", "$0-fw22")
    s.comment("Chip: a game console's channels, raw - left a pulse whose duty steps between 12.5, 25 and 50 % "
              "(as the hardware does, never smoothly), unfiltered; right the 4-bit triangle (16 steps); brightness "
              "brings the pulse across. A vibrato that comes in late, and the sample rate held down a little")
    f, b = _flav_inlets(s, 2)
    vib = s.ch(s.obj("osc~ 5.6"), "*~ 0.004")
    late = s.ch(s.obj("osc~ 0.09"), "*~ 0.5", "+~ 0.5")       # (the vibrato's depth, slowly in and out)
    fv = mul(s, f, s.to(mul(s, vib, late), "+~ 1"))
    ph = s.to(fv, "phasor~")
    P, Q = prm(s, "p", 0), prm(s, "p", 1)        # (PADS SHAPE knobs 3 and 4: data.PAD_PARAMS)
    dst = s.ch(s.recv("$0-lb"), "osc~", "expr~ if($v1 < -0.33, 0.125, if($v1 < 0.33, 0.25, 0.5))", "-~ 0.5")
    duty = s.to(mul(s, dst, s.ch(P, "*~ 2", "clip~ 0 1")), "+~ 0.5")
    pulse = s.obj("expr~ ($v1 < $v2)*2 - 1")
    s.c(ph, 0, pulse, 0)
    s.c(duty, 0, pulse, 1)
    tri = s.to(ph, "expr~ floor((1 - abs($v1*4 - 2))*7.99)/7.5 - 1")
    # the sample rate held down: a new value every 4 samples (about 11 kHz)
    hold = s.to(s.to(Q, "expr~ 22050*pow(0.25, $v1)"), "phasor~")
    outs = []
    for sig, other in ((pulse, None), (tri, pulse)):
        x = sig if other is None else add(s, sig, mul(s, s.to(other, "*~ 0.6"), b))
        sh = s.obj("samphold~")
        s.c(x, 0, sh, 0)
        s.c(hold, 0, sh, 1)
        outs.append(s.ch(sh, "hip~ 20", "*~ 0.18"))
    _out(s, outs[0], ln, outs[1])
    return s


NEW_FLAVS = (flav_saws, flav_pwm, flav_digi, flav_sync, flav_tine, flav_sine, flav_glass, flav_beat,
             flav_reed, flav_organ, flav_air, flav_cz, flav_choir, flav_vosim, flav_whistle, flav_lissa, flav_chip)


# ---------------------------------------------------------------- drone designs 1..3 (0 is the original)
def _drone_freq(s):
    return s.ch(s.m(s.ch(s.recv("ac-dronep"), "line 0 40", "mtof"), "$1 40"), "line~")


def _drone_out(s, sig, ln, sigR=None):
    """stereo: a second signal for the right, or else a slowly modulated 9-14 ms copy of the left"""
    if sigR is None:
        s.to(sig, "delwrite~ $0-dw 40")
        sigR = s.obj("vd~ $0-dw")
        s.c(s.ch(s.obj("osc~ 0.07"), "*~ 2.5", "+~ 11.5"), 0, sigR, 0)
        sigR = add(s, s.to(sig, "*~ 0.35"), s.to(sigR, "*~ 0.8"))
    oL = mul(s, s.to(sig, "hip~ 25"), ln)
    oR = mul(s, s.to(sigR, "hip~ 25"), ln)
    throws_to("ac-sendd")(s, oL, oR, mix=0.6, send=0.3, src=1, bus="bed")


def drone_analog():
    s, ln = switched("drone-analog", "ac-g-drone1")
    s.comment("Analog drone: two saws and a square an octave down through a slow resonant sweep")
    f = _drone_freq(s)
    sq = s.ch(s.to(f, "*~ 0.5"), "phasor~", "-~ 0.5", "*~ 1000", "clip~ -0.25 0.25")
    br = s.ch(s.recv("ac-bright"), "line~")
    outs = []
    for d, rate in ((1.0, 0.021), (1.0042, 0.017)):          # a saw and its own sweep on each side
        sm = s.obj("*~ 0.3")
        s.c(s.ch(s.to(f, f"*~ {d}"), "phasor~", "-~ 0.5"), 0, sm, 0)
        s.c(s.to(sq, "*~ 0.7"), 0, sm, 0)
        sweep = s.ch(s.obj(f"osc~ {rate}"), "*~ 0.5", "+~ 0.5")
        cf = s.to(mul(s, f, add(s, s.to(mul(s, sweep, br), "*~ 10"), s.obj("sig~ 1.5"))), "clip~ 40 4000")
        v = s.obj("vcf~ 3")
        s.c(sm, 0, v, 0)
        s.c(cf, 0, v, 1)
        outs.append(s.to((v, 1), "*~ 2.6"))
    _drone_out(s, outs[0], ln, outs[1])
    return s


def drone_organ():
    s, ln = switched("drone-organ", "ac-g-drone2")
    s.comment("Organ drone: drawbar partials 1 2 3 4 6 8 with a slow rotary shimmer")
    f = _drone_freq(s)
    sm = s.obj("*~ 1")
    for h, a in ((1, 0.22), (2, 0.16), (3, 0.1), (4, 0.07), (6, 0.04), (8, 0.03)):
        s.c(s.ch(s.to(f, f"*~ {h}"), "osc~", f"*~ {a}"), 0, sm, 0)
    rot = s.ch(s.obj("osc~ 0.8"), "*~ 0.22")
    # rotary: opposite swells left and right, and the right is a slowly moving delayed copy
    s.to(sm, "delwrite~ $0-ow 40")
    dly = s.obj("vd~ $0-ow")
    s.c(s.ch(s.obj("osc~ 0.11"), "*~ 3", "+~ 13"), 0, dly, 0)
    _drone_out(s, mul(s, sm, s.to(rot, "+~ 0.78")), ln, mul(s, dly, s.ch(rot, "*~ -1", "+~ 0.78")))
    return s


def drone_fm():
    s, ln = switched("drone-fm", "ac-g-drone3")
    s.comment("FM drone: an electric growl, the index cycling slowly; a little noise in the attack band")
    f = _drone_freq(s)
    idx = s.ch(s.obj("osc~ 0.037"), "*~ 1.5", "+~ 2")
    mo = mul(s, mul(s, s.to(f, "osc~"), idx), f)
    car = s.to(add(s, f, mo), "osc~")
    _drone_out(s, s.ch(car, "lop~ 1800", "*~ 0.3"), ln)
    return s


def drone_frost():
    s, ln = switched("drone-frost", "ac-g-drone4")
    s.comment("Frost drone (after Frasil's CHOIR and BREATH): three detuned saws - centre, a little flat on the left, "
              "a little sharp on the right - each drifting on its own, through a resonant low-pass that follows the "
              "note and the brightness; under them noise through three resonators on the note (x1, x2, x3), glassy")
    f = _drone_freq(s)
    br = s.ch(s.recv("ac-bright"), "line~")
    saws = []
    for cents, rate in ((0, 0.023), (-7, 0.031), (7, 0.037)):
        dr = s.ch(s.obj(f"osc~ {rate}"), "*~ 0.0025", f"+~ {2 ** (cents / 1200):.5f}")   # +-4 cents of drift
        saws.append(s.ch(mul(s, f, dr), "phasor~", "-~ 0.5"))
    cf = s.to(mul(s, f, add(s, s.to(br, "*~ 5"), s.ch(s.obj("osc~ 0.019"), "*~ 0.6", "+~ 2"))), "clip~ 60 6000")
    outs = []
    for side in (0, 1):
        sm = add(s, s.to(saws[0], "*~ 0.6"), saws[1 + side])
        v = s.obj("vcf~ 2.5")
        s.c(sm, 0, v, 0)
        s.c(cf, 0, v, 1)
        outs.append(s.to((v, 1), "*~ 0.55"))
    nz = s.obj("noise~")
    for k, (h, q) in enumerate(((1, 30), (2, 40), (3, 50))):
        r = s.obj(f"vcf~ {q}")
        s.c(nz, 0, r, 0)
        s.c(s.to(f, f"*~ {h}"), 0, r, 1)
        s.c(s.to(r, f"*~ {0.5 / h:.3f}"), 0, outs[k % 2], 0)
    _drone_out(s, outs[0], ln, outs[1])
    return s


def drone_choir():
    s, ln = switched("drone-choir", "ac-g-drone5")
    s.comment("Choir drone: three voices (the note, a hair sharp, and the fifth) - narrow glottal pulses through "
              "two vowel formants that move slowly between ah, oh and oo")
    f = _drone_freq(s)
    # the vowel: F1 450-750 Hz and F2 800-1150 Hz, wandering together
    vw = s.ch(s.obj("osc~ 0.023"), "*~ 0.5", "+~ 0.5")
    f1, f2 = s.ch(vw, "*~ 300", "+~ 450"), s.ch(vw, "*~ 350", "+~ 800")
    outs = []
    for side, voices in enumerate((((1.0, 4.9), (1.5, 5.3)), ((1.003, 5.1), (1.5, 5.6)))):
        src = s.obj("*~ 1")
        for ratio, vr in voices:
            vib = s.ch(s.obj(f"osc~ {vr}"), "*~ 0.004", f"+~ {ratio}")
            pulse = s.ch(mul(s, f, vib), "phasor~", "-~ 0.5", "*~ 2", "abs~", "pow~ 8")
            s.c(pulse, 0, src, 0)
        sm = s.obj("+~")
        for fm, q in ((f1, 6), (f2, 9)):
            v = s.obj(f"vcf~ {q}")
            s.c(src, 0, v, 0)
            s.c(fm, 0, v, 1)
            s.c(v, 0, sm, 0)
        outs.append(s.to(sm, "*~ 1.1"))
    _drone_out(s, outs[0], ln, outs[1])
    return s


def drone_bowed():
    s, ln = switched("drone-bowed", "ac-g-drone6")
    s.comment("Bowed drone: a cello on the note - a saw with a slow bow-pressure swell and a light vibrato, through "
              "the body's resonances (about 200, 500 and 1300 Hz) and a soft low-pass")
    f = _drone_freq(s)
    outs = []
    for d, vr, pr in ((1.0, 4.7, 0.11), (0.9985, 5.2, 0.09)):
        vib = s.ch(s.obj(f"osc~ {vr}"), "*~ 0.003", f"+~ {d}")
        saw = s.ch(mul(s, f, vib), "phasor~", "-~ 0.5")
        press = s.ch(s.obj(f"osc~ {pr}"), "*~ 0.25", "+~ 0.75")
        x = mul(s, saw, press)
        sm = s.obj("*~ 1")
        s.c(s.to(x, "lop~ 1600"), 0, sm, 0)
        for hz, q, a in ((200, 4, 0.6), (500, 5, 0.5), (1300, 6, 0.3)):
            bp = s.obj(f"bp~ {hz} {q}")
            s.c(x, 0, bp, 0)
            s.c(s.to(bp, f"*~ {a}"), 0, sm, 0)
        outs.append(s.to(sm, "*~ 0.35"))
    _drone_out(s, outs[0], ln, outs[1])
    return s


def drone_spectral():
    s, ln = switched("drone-spectral", "ac-g-drone7")
    s.comment("Spectral drone: eight harmonics, each swelling on its own slow cycle, so the spectrum keeps "
              "shifting while the note holds; odd harmonics lean left, even right")
    f = _drone_freq(s)
    L, R = s.obj("*~ 0.32"), s.obj("*~ 0.32")
    for n in range(1, 9):
        sw = s.ch(s.obj(f"osc~ {0.013 * (1 + 0.37 * n):.4f}"), "*~ 0.5", "+~ 0.5")
        p = mul(s, s.ch(s.to(f, f"*~ {n}"), "osc~"), s.to(sw, f"*~ {1 / n ** 0.7:.3f}"))
        s.c(s.to(p, f"*~ {1.0 if n % 2 else 0.45}"), 0, L, 0)
        s.c(s.to(p, f"*~ {0.45 if n % 2 else 1.0}"), 0, R, 0)
    _drone_out(s, L, ln, R)
    return s


GENDY_N = 12


def drone_gendy():
    s, ln = switched("drone-gendy", "ac-g-drone8")
    s.comment("GENDY drone (Xenakis' stochastic synthesis, gently): a wave of 12 breakpoints read at the drone's "
              "pitch; every 30 ms each breakpoint takes a small random step (mirrored at the edges), so the "
              "timbre keeps breathing while the pitch holds. Its own random numbers (not the piece's). The right "
              "side reads the same wave a hair sharp.")
    tab = "$0-gtab"
    s.obj(f"array define {tab} {GENDY_N + 3}")
    # the walk: each round, each breakpoint (1..N) steps; then the guard points (0 = N, N+1 = 1, N+2 = 2)
    met = s.obj("metro 30")
    s.c(s.obj("loadbang"), 0, met, 0)
    rnd = s.to(met, "t b b b")
    cnt = s.obj("f")
    s.c(s.m((rnd, 2), "0"), 0, cnt, 1)
    s.c(s.ch(s.m((rnd, 1), str(GENDY_N)), "until"), 0, cnt, 0)
    s.c(s.to(cnt, "+ 1"), 0, cnt, 1)
    ix = s.ch(cnt, "+ 1", "t f f")                      # (right to left: the index to write, then read and step)
    tw = s.obj(f"tabwrite {tab}")
    s.c(ix, 1, tw, 1)
    rd = s.ch((ix, 0), f"tabread {tab}", "t f b")
    stp = s.obj("expr $f1 + ($f2/1000 - 0.5)*0.14; if($f1 + ($f2/1000 - 0.5)*0.14 > 0.95, 1.9 - $f1 - ($f2/1000 - 0.5)*0.14, "
                "if($f1 + ($f2/1000 - 0.5)*0.14 < -0.95, -1.9 - $f1 - ($f2/1000 - 0.5)*0.14, $f1 + ($f2/1000 - 0.5)*0.14))")
    s.c(s.ch((rd, 1), "random 1000"), 0, stp, 1)
    s.c((rd, 0), 0, stp, 0)
    s.c((stp, 1), 0, tw, 0)
    g = s.to((rnd, 0), "t b b b")
    s.c(s.ch(s.m((g, 2), f"{GENDY_N} 1"), f"array get {tab}"), 0, s.obj(f"array set {tab} 0"), 0)
    s.c(s.ch(s.m((g, 1), "1 2"), f"array get {tab}"), 0, s.obj(f"array set {tab} {GENDY_N + 1}"), 0)
    f = _drone_freq(s)
    outs = []
    for d in (1.0, 1.0025):
        rdx = s.ch(s.to(f, f"*~ {d}"), "phasor~", f"*~ {GENDY_N}", "+~ 1", f"tabread4~ {tab}")
        outs.append(s.ch(rdx, "lop~ 1800", "lop~ 2400", "*~ 0.55"))
    _drone_out(s, outs[0], ln, outs[1])
    return s


NEW_DRONES = (drone_analog, drone_organ, drone_fm, drone_frost, drone_choir, drone_bowed, drone_spectral, drone_gendy)


def sub():
    s, ln = switched("sub", "ac-g-sub")
    s.comment("Sub: a sine under everything - the pedal an octave under the tonic, or the chord root as a bass "
              "line - softly saturated so small speakers hear its harmonics; swells with the bar pulse")
    f = s.ch(s.recv("ac-subp"), "line~")
    x = s.to(f, "osc~")
    sat = s.ch(x, "*~ 1.8", "clip~ -1 1")
    y0 = add(s, s.to(x, "*~ 0.6"), s.to(sat, "*~ 0.25"))
    # its sound (the sub's SHAPE page): sine (above), warm (a rounder saturation and the octave), pulse (a narrow
    # pulse, low-passed), fm (a slow growl); each crossfaded in by its own gain
    warm = add(s, s.ch(x, "*~ 3", "clip~ -1 1", "*~ 0.55"), s.ch(s.to(f, "*~ 2"), "osc~", "*~ 0.18"))
    pulse = s.ch(f, "phasor~", "-~ 0.75", "*~ 1000", "clip~ -0.5 0.5", "lop~ 220", "lop~ 220", "*~ 1.6")
    idx = s.ch(s.obj("osc~ 0.07"), "*~ 0.5", "+~ 1")
    fm = s.ch(add(s, f, mul(s, mul(s, x, idx), f)), "osc~", "*~ 0.7")
    y = s.obj("+~")
    for k, sig in enumerate((y0, warm, pulse, fm)):
        g = s.ch(s.recv("ac-subt"), f"expr $f1 == {k}", "pack f 200", "line~")
        if k == 0:
            s.c(s.m(s.obj("loadbang"), "1"), 0, g, 0)
        s.c(mul(s, sig, g), 0, y, 0)
    env = s.ch(s.m(s.to(s.recv("ac-dpulse"), "expr max(100, $f1-450)"), "1 450, 0 $1 450"), "vline~")
    dep = s.to(env, "*~ 0")
    pu = s.to(s.recv("ac-pulse"), "t f f")
    s.c(pu, 1, dep, 1)
    pa = s.to(dep, "+~ 1")
    s.c(s.to((pu, 0), "expr 1-$f1"), 0, pa, 1)
    o = mul(s, mul(s, s.to(y, "lop~ 500"), pa), ln)
    throws_to("ac-sendd")(s, o, o, mix=0.42, send=0.05, bus="bed")
    return s


# ---------------------------------------------------------------- electric textures 4..6
def tex_radio():
    s, ln = switched("radio", "ac-g-tex4")
    s.comment("Radio: a soft band of static, always there and swelling in and out, and a heterodyne whistle "
              "drifting near a chord tone - tuning between stations (the static's gate is slow and smoothed, so "
              "it never crackles)")
    gate = s.ch(s.obj("noise~"), "lop~ 0.3", "*~ 200", "-~ 0.1", "clip~ 0 1", "lop~ 1", "lop~ 1")
    g2 = s.ch(gate, "*~ 0.65", "+~ 0.35")
    # each side its own static (a diffuse band, not a centred hiss)
    stat, statR = [s.to(mul(s, s.ch(s.obj("noise~"), "hip~ 900", "lop~ 2200", "lop~ 2600"), g2), "*~ 0.6")
                   for _ in range(2)]
    wf = s.ch(s.recv("ac-radio"), "line~")
    drift = s.ch(s.obj("osc~ 0.13"), "*~ 0.004", "+~ 1")
    wh = s.ch(mul(s, wf, drift), "osc~", "*~ 0.06")
    swell = s.ch(s.obj("osc~ 0.05"), "*~ 0.5", "+~ 0.5")
    L = mul(s, add(s, s.to(stat, "*~ 0.5"), mul(s, wh, swell)), ln)
    R = mul(s, add(s, s.to(statR, "*~ 0.35"), s.to(mul(s, wh, swell), "*~ 0.7")), ln)
    throws(s, L, R, mix=0.6, send=0.5)
    return s


def tex_data():
    s, ln = switched("data", "ac-g-tex5")
    s.comment("Data: bursts of tiny square-wave blips on chord tones, crushed - a machine thinking")
    up = s.to(s.recv("ac-data"), "unpack f f")
    env = s.ch(s.m(s.to((up, 1), "t f"), "0.5, 0 $1"), "vline~")
    hz = s.ch((up, 0), "mtof")
    sq = s.ch(s.to(hz, "phasor~"), "-~ 0.5", "*~ 1000", "clip~ -0.2 0.2")
    sig = mul(s, sq, env)
    hold = s.obj("samphold~")
    s.c(sig, 0, hold, 0)
    s.c(s.obj("phasor~ 6000"), 0, hold, 1)
    o = mul(s, s.to(hold, "*~ 3.5"), ln)
    pn = s.ch(s.obj("osc~ 0.3"), "*~ 0.4", "+~ 0.5")
    throws(s, mul(s, o, pn), mul(s, o, s.ch(pn, "*~ -1", "+~ 1")), mix=0.5, send=0.6)
    return s


def tex_buzz():
    s, ln = switched("buzz", "ac-g-tex6")
    s.comment("Buzz: an electric hum on the tonic - a narrow pulse ringing two resonances, swelling and crackling")
    f = s.ch(s.m(s.ch(s.recv("ac-dronep"), "line 0 40", "mtof"), "$1 2000"), "line~")
    pulse = s.ch(s.to(f, "phasor~"), "-~ 0.97", "max~ 0", "*~ 30")
    outs = []
    for h, q in ((3, 18), (5, 25)):
        v = s.obj(f"vcf~ {q}")
        s.c(pulse, 0, v, 0)
        s.c(s.to(f, f"*~ {h}"), 0, v, 1)
        outs.append(v)
    crack = s.ch(s.obj("noise~"), "-~ 0.998", "max~ 0", "*~ 200")
    sw = s.ch(s.obj("osc~ 0.031"), "*~ 0.45", "+~ 0.55")
    L = mul(s, mul(s, add(s, outs[0], crack), sw), ln)
    R = mul(s, mul(s, add(s, outs[1], crack), sw), ln)
    throws(s, s.to(L, "*~ 1.6"), s.to(R, "*~ 1.6"), mix=1, send=0.4)
    return s


# ---------------------------------------------------------------- textures 7..11: voices, echoes, nature
def _lpnoise(s, hz, scale, off, lo, hi):
    """a slowly wandering value: white noise low-passed at hz, scaled, offset, clipped (a jittering centre)"""
    return s.ch(s.obj("noise~"), f"lop~ {hz}", f"*~ {scale}", f"+~ {off}", f"clip~ {lo} {hi}")


def _syllables(s, rate, scale, smooth, phrase_hz, phase):
    """speech-like loudness: random syllable bursts (noise low-passed at rate, clipped) inside slow phrases"""
    syl = s.ch(s.obj("noise~"), f"lop~ {rate}", f"*~ {scale}", "clip~ 0 1", f"lop~ {smooth}")
    ph = s.obj(f"osc~ {phrase_hz}")
    s.c(s.m(s.obj("loadbang"), f"{phase}"), 0, ph, 1)
    phrase = s.ch(ph, "-~ 0.2", "max~ 0", "*~ 1.25")
    return mul(s, syl, phrase)


def tex_murmur():
    s, ln = switched("murmur", "ac-g-tex7")
    s.comment("Murmur: two distant voices - a breathy low buzz through two drifting vowel formants, in syllables "
              "and phrases, far back (mostly reverb)")
    outs = []
    for side, (f0, ph) in enumerate(((112, 0), (147, 0.5))):
        vib = s.ch(s.obj(f"osc~ {4.1 + side}"), "*~ 0.012", "+~ 1")
        buzz = s.ch(mul(s, s.obj(f"sig~ {f0}"), vib), "phasor~", "-~ 0.5", "lop~ 1400")
        src = add(s, buzz, s.ch(s.obj("noise~"), "lop~ 3000", "*~ 0.25"))
        sm = s.obj("+~")
        for q, (hz, sc, off, lo, hi) in ((6, (3, 30000, 550, 250, 900)), (8, (2.5, 80000, 1500, 800, 2500))):
            v = s.obj(f"vcf~ {q}")
            s.c(src, 0, v, 0)
            s.c(_lpnoise(s, hz, sc, off, lo, hi), 0, v, 1)
            s.c(v, 0, sm, 0)
        env = _syllables(s, 5, 120, 20, 0.055 + 0.017 * side, ph)
        outs.append(mul(s, mul(s, s.to(sm, "lop~ 2600"), env), ln))
        s.col(260)
    L = add(s, s.to(outs[0], f"*~ {TEXG['MURMUR_G']}"), s.to(outs[1], f"*~ {TEXG['MURMUR_X']}"))
    R = add(s, s.to(outs[1], f"*~ {TEXG['MURMUR_G']}"), s.to(outs[0], f"*~ {TEXG['MURMUR_X']}"))
    throws(s, L, R, mix=0.35, send=1.0)
    return s


def tex_echoes():
    s, ln = switched("echoes", "ac-g-tex8")
    s.comment("Echoes: alien blips on chord tones (a gliding sine ring-modulated a tritone up) into ping-pong "
              "echoes whose delay times wobble, so each repeat bends in pitch")
    up = s.to(s.recv("ac-echo"), "unpack f f")
    tf = s.to((up, 0), "t f f")
    ex = s.to((tf, 0), "expr $f1; $f1*0.86")
    pk = s.obj("pack f f")
    s.c(ex, 1, pk, 1)
    s.c(ex, 0, pk, 0)
    fr = s.ch(s.m(pk, "$1, $2 160"), "vline~")
    env = s.ch(s.m((tf, 1), "0.6, 0 180"), "vline~")
    blip = mul(s, mul(s, s.to(fr, "osc~"), s.ch(fr, "*~ 1.414", "osc~")), mul(s, env, env))
    pn = s.to((up, 1), "expr cos($f1*1.5708); sin($f1*1.5708)")
    dl, dr = s.to(blip, "*~ 1"), s.to(blip, "*~ 1")
    s.c(pn, 0, dl, 1)
    s.c(pn, 1, dr, 1)
    s.col()
    # ping-pong: each side's echo feeds the other, through a band (lop / hip) so repeats darken
    reads = []
    for name, ms, rate, dep in (("$0-ecL", 420, 0.13, 25), ("$0-ecR", 610, 0.09, 30)):
        vd = s.obj(f"vd~ {name}")
        s.c(s.ch(s.obj(f"osc~ {rate}"), f"*~ {dep}", f"+~ {ms}"), 0, vd, 0)
        reads.append(s.ch(vd, "lop~ 2400", "hip~ 250"))
    for i, (name, dry) in enumerate((("$0-ecL", dl), ("$0-ecR", dr))):
        w = add(s, dry, s.to(reads[1 - i], "*~ 0.58"))
        s.to(w, f"delwrite~ {name} 1500")
    L = mul(s, add(s, s.to(dl, "*~ 0.35"), reads[0]), ln)
    R = mul(s, add(s, s.to(dr, "*~ 0.35"), reads[1]), ln)
    throws(s, s.to(L, f"*~ {TEXG['ECHO_G']}"), s.to(R, f"*~ {TEXG['ECHO_G']}"), mix=0.6, send=0.6)
    return s


def tex_whisper():
    s, ln = switched("whisper", "ac-g-tex9")
    s.comment("Whisper: breath noise shaped by two moving formants into fast syllables, in phrases - one each "
              "side")
    outs = []
    for side, ph in enumerate((0, 0.35)):
        src = s.ch(s.obj("noise~"), "hip~ 1200")
        sm = s.obj("+~")
        for q, (hz, sc, off, lo, hi) in ((4, (6, 60000, 2200, 1200, 3500)), (5, (5, 90000, 5000, 3500, 8000))):
            v = s.obj(f"vcf~ {q}")
            s.c(src, 0, v, 0)
            s.c(_lpnoise(s, hz, sc, off, lo, hi), 0, v, 1)
            s.c(v, 0, sm, 0)
        env = _syllables(s, 8, 150, 40, 0.045 + 0.013 * side, ph)
        outs.append(mul(s, mul(s, sm, env), ln))
        s.col(260)
    throws(s, s.to(outs[0], f"*~ {TEXG['WHISPER_G']}"), s.to(outs[1], f"*~ {TEXG['WHISPER_G']}"), mix=0.6, send=0.6)
    return s


def tex_leaves():
    s, ln = switched("leaves", "ac-g-tex10")
    s.comment("Leaves: a rustle in the trees - high noise in a fast flutter, dry little clicks, swelling with gusts")
    gust = s.ch(add(s, s.obj("osc~ 0.051"), s.ch(s.obj("osc~ 0.083"), "*~ 0.7")), "*~ 0.45", "+~ 0.35", "max~ 0.05")
    outs = []
    for side in range(2):
        n = s.ch(s.obj("noise~"), "hip~ 2500", "lop~ 9000")
        flutter = s.ch(s.obj("noise~"), "lop~ 60", "abs~", "*~ 25", "clip~ 0 1")
        ticks = s.ch(s.obj("noise~"), "-~ 0.997", "max~ 0", "*~ 300", "lop~ 7000")
        o = add(s, mul(s, n, flutter), s.to(ticks, "*~ 0.3"))
        outs.append(mul(s, mul(s, o, s.to(gust, f"*~ {1 - 0.15 * side}")), ln))
    throws(s, s.to(outs[0], f"*~ {TEXG['LEAVES_G']}"), s.to(outs[1], f"*~ {TEXG['LEAVES_G']}"), mix=0.6, send=0.4)
    return s


def tex_brook():
    s, ln = switched("brook", "ac-g-tex11")
    s.comment("Brook: a babbling stream - brown noise ringing very narrow bands whose pitch jitters at a few "
              "hertz (the classic brook model), two layers each side")
    outs = []
    for side in range(2):
        brown = s.ch(s.obj("noise~"), "lop~ 70", "*~ 12")
        sm = s.obj("+~")
        for sc, off in ((8000, 500 + 40 * side), (16000, 1000 + 80 * side)):
            v = s.obj("vcf~ 30")
            s.c(brown, 0, v, 0)
            s.c(_lpnoise(s, 14, sc, off, 150, 4000), 0, v, 1)
            s.c(v, 0, sm, 0)
        outs.append(mul(s, s.ch(sm, "hip~ 120"), ln))
    throws(s, s.to(outs[0], f"*~ {TEXG['BROOK_G']}"), s.to(outs[1], f"*~ {TEXG['BROOK_G']}"), mix=0.6, send=0.4)
    return s


# ---------------------------------------------------------------- textures 12..15: oscillators and models
def tex_bubbles():
    s, ln = switched("bubbles", "ac-g-tex12")
    s.comment("Bubbles: water drops tuned to the chord - a sine whose pitch rises as it dies (the bubble model: a "
              "small bubble rings high and short), three at a time, each placed in the stereo field")
    r = s.ch(s.recv("ac-bub"), "route 0 1 2")       # voice, hz, ms, amp, pan
    L, R = s.obj("+~"), s.obj("+~")
    for v in range(3):
        up = s.to((r, v), "unpack f f f f")
        # the pitch: f, then 1.9 f over the life; the level: amp, then a fast decay (squared)
        pk = s.obj("pack f f f")
        tf = s.to((up, 0), "t f f")
        s.c(s.to((tf, 1), "* 1.9"), 0, pk, 1)
        s.c(tf, 0, pk, 0)
        s.c((up, 1), 0, pk, 2)
        fq = s.ch(s.m(pk, "$1, $2 $3"), "vline~")
        ep = s.obj("pack f f")              # (ms, amp: the amp arrives first, into the cold inlet)
        s.c((up, 2), 0, ep, 1)
        s.c((up, 1), 0, ep, 0)
        env = s.ch(s.m(ep, "$2, 0 $1"), "vline~")
        sig = mul(s, s.to(fq, "osc~"), mul(s, env, env))
        pn = s.to((up, 3), "expr cos($f1*1.5708); sin($f1*1.5708)")
        gl, gr = s.obj("*~"), s.obj("*~")
        s.c(sig, 0, gl, 0)
        s.c(sig, 0, gr, 0)
        s.c(pn, 0, gl, 1)
        s.c(pn, 1, gr, 1)
        s.c(gl, 0, L, 0)
        s.c(gr, 0, R, 0)
        s.col(240)
    hp = lambda x: s.ch(x, "hip~ 150", f"*~ {TEXG['BUBBLE_G']}")
    throws(s, mul(s, hp(L), ln), mul(s, hp(R), ln), mix=0.7, send=0.45)
    return s


def tex_crickets():
    s, ln = switched("crickets", "ac-g-tex13")
    s.comment("Crickets: three of them, each a sine (high, on a chord tone) pulsed into chirps of three or four "
              "pulses; each its own pace, drifting - one near each side, one far off in the reverb")
    hz = s.ch(s.recv("ac-cric"), "line~")              # a chord tone, 3-5.5 kHz
    outs = []
    for k, (pulse, chirp, ratio, drift) in enumerate(((31, 1.7, 1.0, 0.07), (27, 1.25, 1.12, 0.05), (35, 2.3, 0.89, 0.09))):
        # the chirp gate: on for the first 0.22 of each chirp cycle, smoothed; its pace drifts slowly
        rate = s.ch(s.obj(f"osc~ {drift}"), f"*~ {chirp * 0.15}", f"+~ {chirp}")
        gate = s.ch(s.to(rate, "phasor~"), "-~ 0.22", "*~ -100", "clip~ 0 1", "lop~ 60")
        # the pulses inside: a raised cosine of each pulse, sharpened
        pl = s.ch(s.obj(f"phasor~ {pulse}"), "cos~", "*~ -0.5", "+~ 0.5", "pow~ 3")
        car = s.ch(mul(s, hz, s.ch(pl, "*~ 0.006", f"+~ {ratio}")), "osc~")        # (a little pitch drop per pulse)
        outs.append(mul(s, car, mul(s, gate, pl)))
        s.col(240)
    far = s.to(outs[2], "*~ 0.35")
    L = add(s, s.to(outs[0], "*~ 0.8"), add(s, s.to(outs[1], "*~ 0.25"), far))
    R = add(s, s.to(outs[1], "*~ 0.8"), add(s, s.to(outs[0], "*~ 0.25"), far))
    g = f"*~ {TEXG['CRICKET_G']}"
    throws(s, mul(s, s.to(L, g), ln), mul(s, s.to(R, g), ln), mix=0.6, send=0.5)
    return s


def tex_harp():
    s, ln = switched("harp", "ac-g-tex14")
    s.comment("Aeolian harp: three strings tuned to the chord (delay lines fed back through a gentle low-pass - "
              "a plucked-string model), sung by the wind: a soft breath of band-passed air, gusting, sweeps "
              "through their overtones")
    gust = s.ch(add(s, s.obj("osc~ 0.037"), s.ch(s.obj("osc~ 0.061"), "*~ 0.6")), "*~ 0.5", "+~ 0.5", "max~ 0")
    outs = []
    for k in range(3):
        per = s.ch(s.recv(f"ac-harp{k}"), "line~")       # the string's period, ms (below 690 Hz: a block's delay)
        air = s.obj("vcf~ 3")
        s.c(s.ch(s.obj("noise~"), "*~ 0.4"), 0, air, 0)
        s.c(s.ch(s.obj(f"osc~ {0.05 + 0.02 * k}"), "*~ 900", f"+~ {1400 + 500 * k}"), 0, air, 1)
        exc = mul(s, air, s.ch(gust, f"pow~ {1.5 + 0.5 * k}"))
        name = f"$0-harp{k}"
        rd = s.obj(f"vd~ {name}")
        s.c(per, 0, rd, 0)
        fb = s.ch(rd, "lop~ 2500", "*~ 0.994")
        s.to(add(s, exc, fb), f"delwrite~ {name} 30")
        outs.append(s.ch(rd, "hip~ 80"))
        s.col(240)
    L = add(s, outs[0], s.to(outs[1], "*~ 0.5"))
    R = add(s, outs[2], s.to(outs[1], "*~ 0.5"))
    g = f"*~ {TEXG['HARP_G']}"
    throws(s, mul(s, s.to(L, g), ln), mul(s, s.to(R, g), ln), mix=0.6, send=0.5)
    return s


def tex_song():
    s, ln = switched("song", "ac-g-tex15")
    s.comment("Song: a distant voice of pure FM singing slow phrases on chord tones - each note glides from the "
              "last, its vibrato and brightness growing as it is held; it wanders across the stereo field")
    up = s.to(s.recv("ac-song"), "unpack f f f")       # hz, glide ms, note ms
    pf = s.obj("pack f f")
    s.c((up, 1), 0, pf, 1)
    s.c((up, 0), 0, pf, 0)
    fq = s.ch(s.m(pf, "$1 $2"), "vline~")
    # the note's swell: up over a third of it, down at its end; the brightness and the vibrato follow it
    ex = s.to((up, 2), "expr $f1*0.33; $f1*0.67")
    ep = s.obj("pack f f")
    s.c(ex, 1, ep, 1)
    s.c(ex, 0, ep, 0)
    env = s.ch(s.m(ep, "1 $1, 0 $1 $2"), "vline~")
    vd = mul(s, s.ch(s.obj("osc~ 4.6"), "*~ 0.012"), env)
    f2 = mul(s, fq, s.to(vd, "+~ 1"))
    mod = mul(s, s.to(f2, "osc~"), s.ch(env, "*~ 1.6"))
    car = s.obj("osc~")
    s.c(add(s, f2, mul(s, mod, f2)), 0, car, 0)
    voice = s.ch(mul(s, car, mul(s, env, env)), "lop~ 3000")
    pos = s.ch(s.obj("osc~ 0.021"), "*~ 0.35", "+~ 0.5")
    from gen_dsp import span
    L, R = span(s, voice, pos)
    g = f"*~ {TEXG['SONG_G']}"
    throws(s, mul(s, s.to(L, g), ln), mul(s, s.to(R, g), ln), mix=0.5, send=0.8)
    return s


def tex_pulsar():
    s, ln = switched("pulsar-tex", "ac-g-tex16")
    s.comment("Pulsar: two pulse trains (Roads' pulsar synthesis) on chord tones - each pulse a burst of the tone "
              "fading out within the first fifth of the period; the pulse rate wanders between a rhythm (4 Hz) and "
              "a low pitch (90 Hz), some pulses masked at random; the two trains on opposite sides, half a period "
              "apart")
    rate = s.ch(add(s, s.obj("osc~ 0.011"), s.ch(s.obj("osc~ 0.029"), "*~ 0.5")), "*~ 0.66", "+~ 1", "*~ 1.5",
                "expr~ 4*pow(22.5, max(0, min(1, $v1/3)))")
    outs = []
    for k, off in ((0, 0.0), (2, 0.5)):
        hz = s.ch(s.recv(f"ac-voccar{k}"), "line~")
        tone = s.to(hz, "*~ 2")
        ph = s.ch(s.to(rate, "phasor~"), f"+~ {off}", "wrap~")
        p = s.obj("expr~ if($v1 < 0.2, sin(6.28319*$v1*$v2/max($v3, 0.5))*(1 - $v1/0.2), 0)")
        s.c(ph, 0, p, 0)
        s.c(tone, 0, p, 1)
        s.c(rate, 0, p, 2)
        mask = s.obj("samphold~")
        s.c(s.obj("noise~"), 0, mask, 0)
        s.c(ph, 0, mask, 1)
        outs.append(mul(s, p, s.to(mask, "expr~ $v1 > -0.5")))
    g = f"*~ {TEXG['PULSAR_G']}"
    throws(s, mul(s, s.to(outs[0], g), ln), mul(s, s.to(outs[1], g), ln), mix=0.6, send=0.5)
    return s


NEW_TEXTURES = (tex_radio, tex_data, tex_buzz, tex_murmur, tex_echoes, tex_whisper, tex_leaves, tex_brook,
                tex_bubbles, tex_crickets, tex_harp, tex_song, tex_pulsar)


# ---------------------------------------------------------------- character on the pads (inlet 0 L, 1 R)
def _char(name, idx):
    s, ln = switched(name, f"ac-g-ch{idx}")
    L, R = s.obj("inlet~", 20, 5), s.obj("inlet~", 160, 5)
    return s, ln, L, R


def _char_out(s, ln, l, r):
    for i, o in enumerate((l, r)):
        s.c(mul(s, o, ln), 0, s.obj("outlet~", 20 + i * 200, 980), 0)


def ch_chorus():
    s, ln, L, R = _char("chorus", 1)
    s.comment("Chorus: two modulated delays a side (ensemble width)")
    outs = []
    for side, src, rates in (("l", L, (0.61, 0.83)), ("r", R, (0.71, 0.97))):
        s.to(src, f"delwrite~ $0-ch{side} 40")
        o = s.obj("*~ 0.6")
        for j, rt in enumerate(rates):
            vd = s.obj(f"vd~ $0-ch{side}")
            s.c(s.ch(s.obj(f"osc~ {rt}"), "*~ 2.5", f"+~ {11 + 6 * j}"), 0, vd, 0)
            s.c(vd, 0, o, 0)
        outs.append(o)
    _char_out(s, ln, *outs)
    return s


def ch_tape():
    s, ln, L, R = _char("tape-wear", 2)
    s.comment("Tape: wow and flutter, soft saturation, hiss, a darker top")
    wow = add(s, s.ch(s.obj("osc~ 0.37"), "*~ 1.6"), s.ch(s.obj("osc~ 6.1"), "*~ 0.12"))
    outs = []
    for side, src in (("l", L), ("r", R)):
        s.to(src, f"delwrite~ $0-tp{side} 60")
        vd = s.obj(f"vd~ $0-tp{side}")
        s.c(s.to(wow, "+~ 25"), 0, vd, 0)
        x = s.to(vd, "*~ 1.6")
        den = s.ch(x, "abs~", "+~ 1")
        sat = s.obj("/~")
        s.c(x, 0, sat, 0)
        s.c(den, 0, sat, 1)
        lvl = s.ch(src, "abs~", "lop~ 4", "*~ 0.02", "clip~ 0 0.004")
        hiss = mul(s, s.ch(s.obj("noise~"), "hip~ 4000"), lvl)
        outs.append(s.to(add(s, s.to(sat, "lop~ 7500"), hiss), "*~ 0.9"))
    _char_out(s, ln, *outs)
    return s


def ch_ring():
    s, ln, L, R = _char("ring", 3)
    s.comment("Ring: ring modulation by a sine on a chord tone (a metallic, electric halo)")
    car = s.ch(s.recv("ac-ringf"), "line~", "osc~")
    _char_out(s, ln, mul(s, L, car), mul(s, R, car))
    return s


def ch_crush():
    s, ln, L, R = _char("crush", 4)
    s.comment("Crush: 6-bit steps and a 9 kHz sample rate")
    clk = s.obj("phasor~ 9000")
    outs = []
    for src in (L, R):
        lv = s.to(src, "*~ 32")
        q = s.obj("-~")
        s.c(lv, 0, q, 0)
        s.c(s.to(lv, "wrap~"), 0, q, 1)
        h = s.obj("samphold~")
        s.c(s.to(q, "*~ 0.03125"), 0, h, 0)
        s.c(clk, 0, h, 1)
        outs.append(s.to(h, "lop~ 8000"))
    _char_out(s, ln, *outs)
    return s


def ch_rotor():
    s, ln, L, R = _char("rotor", 5)
    s.comment("Rotor: a rotary speaker, slow (chorale) - the pads split at 800 Hz; the horn (above) turns at 0.83 "
              "Hz, the drum (below) at 0.68 Hz the other way, each a moving delay (Doppler) and a swelling level, "
              "the two sides a quarter turn apart")
    mono = s.to(add(s, L, R), "*~ 0.5")
    hi, lo = s.to(mono, "hip~ 800"), s.to(mono, "lop~ 800")
    s.to(hi, "delwrite~ $0-rh 20")
    s.to(lo, "delwrite~ $0-rl 20")
    outs = []
    for side, ph in ((0, 0), (1, 0.25)):
        o = s.obj("*~ 1")
        for nm, rate, dly, dep, am in (("$0-rh", 0.83, 2.0, 0.45, 0.4), ("$0-rl", -0.68, 3.0, 0.3, 0.2)):
            ang = s.to(s.obj(f"phasor~ {rate}"), f"+~ {ph}")
            cs = s.to(ang, "cos~")
            vd = s.obj(f"vd~ {nm}")
            s.c(s.ch(cs, f"*~ {dep}", f"+~ {dly}"), 0, vd, 0)
            s.c(mul(s, vd, s.ch(cs, f"*~ {am}", f"+~ {1 - am}")), 0, o, 0)
        outs.append(o)
    _char_out(s, ln, *outs)
    return s


def ch_dim():
    s, ln, L, R = _char("dimension", 6)
    s.comment("Dimension: the Roland Dimension D's gentle width - two short delays (about 6 ms) swept very slowly and "
              "shallowly in opposite directions, each side its own minus a little of the other's, so the pads open "
              "out without the chorus's wobble")
    mono = s.to(add(s, L, R), "*~ 0.5")
    s.to(mono, "delwrite~ $0-dm 20")
    lfo = s.ch(s.obj("phasor~ 0.25"), "-~ 0.5", "abs~", "*~ 4", "-~ 1")           # a triangle
    d = []
    for sign in (1, -1):
        vd = s.obj("vd~ $0-dm")
        s.c(s.ch(lfo, f"*~ {0.35 * sign}", "+~ 6"), 0, vd, 0)
        d.append(vd)
    oL = add(s, d[0], s.to(d[1], "*~ -0.35"))
    oR = add(s, d[1], s.to(d[0], "*~ -0.35"))
    _char_out(s, ln, s.to(oL, "*~ 0.7"), s.to(oR, "*~ 0.7"))
    return s


CHARS = (ch_chorus, ch_tape, ch_ring, ch_crush, ch_rotor, ch_dim)


def input_octave():
    s, ln = switched("in-octave", "ac-g-oct")
    s.comment("Input mode octave: the input with its octave above (full-wave rectified, its DC removed) and its "
              "octave below (ring-modulated at half its tracked pitch, which also gives the fifth above - an "
              "organ-like doubling); the dry input stays as in the other modes")
    x = s.ch(s.obj("r~ ac-in"), "hip~ 40")
    up = s.ch(x, "abs~", "hip~ 60", "*~ 1.2")
    met = s.obj("metro 50")
    s.c(s.obj("loadbang"), 0, met, 0)
    hz = s.ch(met, "v acinp", "moses 1")
    sub = s.ch(s.m(s.ch((hz, 1), "mtof", "/ 2"), "$1 60"), "line~", "osc~")
    dn = mul(s, x, sub)
    throws_to("ac-sendi")(s, mul(s, add(s, up, s.to(dn, "*~ 1.3")), ln),
                          mul(s, add(s, s.to(up, "*~ 0.8"), s.to(dn, "*~ 1.5")), ln), mix=1.0, send=0.5)
    return s


FMT_BANDS = [300, 450, 650, 850, 1100, 1500, 1950, 2500]


def input_formant():
    s, ln = switched("in-formant", "ac-g-fmt")
    s.comment("Input mode formant: the chord sings your vowel - the input's two formants found from 8 bands (the "
              "weighted centre of 300-850 Hz and of 1100-2500 Hz, 25 times a second), set on a glottal choir on the "
              "chord's four tones, which follows the input's level")
    x = s.obj("r~ ac-in")
    snaps = []
    for fc in FMT_BANDS:
        v = s.obj("vcf~ 4")
        s.c(x, 0, v, 0)
        s.c(s.obj(f"sig~ {fc}"), 0, v, 1)
        snaps.append(s.ch(v, "abs~", "lop~ 12", "snapshot~"))
    met = s.obj("metro 40")
    s.c(s.obj("loadbang"), 0, met, 0)
    n = len(FMT_BANDS)
    tb = s.to(met, "t " + " ".join(["b"] * n))
    pk = s.obj("pack " + " ".join(["f"] * n))
    for i in range(n - 1, -1, -1):             # (right to left: the last band first, the first into the hot inlet)
        s.c(tb, i, snaps[i], 0)
        s.c(snaps[i], 0, pk, i)
    lo = " + ".join(f"$f{i + 1}" for i in range(4))
    hi = " + ".join(f"$f{i + 1}" for i in range(4, 8))
    ex = s.obj("expr (" + " + ".join(f"{FMT_BANDS[i]}*$f{i + 1}" for i in range(4)) + f")/max(1e-06, {lo}); ("
               + " + ".join(f"{FMT_BANDS[i]}*$f{i + 1}" for i in range(4, 8)) + f")/max(1e-06, {hi})")
    s.c(pk, 0, ex, 0)
    f1 = s.ch(s.m((ex, 0), "$1 40"), "line~")
    f2 = s.ch(s.m((ex, 1), "$1 40"), "line~")
    env = s.ch(x, "abs~", "lop~ 15", "*~ 6", "clip~ 0 1")
    src = s.obj("*~ 0.3")
    for k in range(4):
        hz = s.ch(s.recv(f"ac-voccar{k}"), "line~")
        s.c(s.ch(hz, "phasor~", "-~ 0.5", "*~ 2", "abs~", "pow~ 8"), 0, src, 0)
    outs = []
    for side, (a1, a2) in enumerate(((1.0, 0.6), (0.8, 0.75))):
        sm = s.obj("*~ 1")
        for fm, q, a in ((f1, 7, a1), (f2, 10, a2)):
            v = s.obj(f"vcf~ {q}")
            s.c(s.to(src, "hip~ 60"), 0, v, 0)
            s.c(fm, 0, v, 1)
            s.c(s.to(v, f"*~ {a}"), 0, sm, 0)
        outs.append(mul(s, s.to(sm, "*~ 3"), env))
    throws_to("ac-sendi")(s, mul(s, outs[0], ln), mul(s, outs[1], ln), mix=1.0, send=0.6)
    return s


# ---------------------------------------------------------------- vocoder
VOC_BANDS = [round(150 * (46.7 ** (i / 9))) for i in range(10)]


def vocoder():
    """The vocoder at half rate (22.05 kHz; its bands reach 7 kHz): an outer canvas feeds the input and the pad
    signal in, and throws what comes out."""
    o = Canvas("vocoder", w=900)
    o.comment("Vocoder: the input's 10 band envelopes shape a carrier - a synth choir on the chord (vocode) or "
              "the pads themselves (morph). The work runs at half rate inside.")
    core = o.sub(_vocoder_core())
    o.c(o.ch(o.obj("r~ ac-in"), "lop~ 8000"), 0, core, 0)
    o.c(o.ch(o.obj("r~ ac-padsig"), "lop~ 8000"), 0, core, 1)
    throws_to("ac-sendi")(o, (core, 0), (core, 1), mix=1.0, send=0.6, src=0.3)
    return o


def _vocoder_core():
    s, ln = switched("vocoder-core", "ac-g-voc", block="32 1 0.5")   # = one parent block: even load
    m = s.obj("inlet~", 20, 5)
    padsig = s.obj("inlet~", 200, 5)
    # carriers
    choir = s.obj("*~ 0.25")
    for k in range(4):
        hz = s.ch(s.recv(f"ac-voccar{k}"), "line~")
        s.c(s.ch(s.to(hz, "phasor~"), "-~ 0.5"), 0, choir, 0)
        s.c(s.ch(s.to(hz, "*~ 1.006"), "phasor~", "-~ 0.5"), 0, choir, 0)
    s.c(s.ch(s.obj("noise~"), "hip~ 5000", "*~ 0.15"), 0, choir, 0)
    car = add(s, mul(s, choir, s.ch(s.recv("ac-vcsyn"), "line~")),
              mul(s, s.to(padsig, "*~ 4"), s.ch(s.recv("ac-vcpad"), "line~")))
    L, R = s.obj("*~ 11"), s.obj("*~ 11")
    s.col()
    for i, fc in enumerate(VOC_BANDS):
        q = 5
        mb = s.obj(f"vcf~ {q}")
        s.c(m, 0, mb, 0)
        s.c(s.obj(f"sig~ {fc}"), 0, mb, 1)
        envl = s.ch(mb, "abs~", "lop~ 30")
        cb = s.obj(f"vcf~ {q}")
        s.c(car, 0, cb, 0)
        s.c(s.obj(f"sig~ {fc}"), 0, cb, 1)
        s.c(mul(s, cb, envl), 0, L if i % 2 == 0 else R, 0)
        if i % 3 == 2:
            s.col(160)
    for i, x in enumerate((L, R)):
        s.c(mul(s, x, ln), 0, s.obj("outlet~ lin", 20 + i * 200, 980), 0)
    return s


# ---------------------------------------------------------------- atmospheres (a background bed, not every piece)
def atm_haze():
    s, ln = switched("atm-haze", "ac-g-atm0")
    s.comment("Haze: air shimmering on the chord - noise through 6 narrow bands on chord partials, each "
              "swelling on its own, spread across the field")
    L, R = s.obj("*~ 3"), s.obj("*~ 3")
    for k in range(6):
        v = s.obj("vcf~ 14")
        s.c(s.obj("noise~"), 0, v, 0)
        s.c(s.ch(s.recv(f"ac-atmf{k}"), "line~"), 0, v, 1)
        sw = s.ch(s.obj(f"osc~ {0.021 + 0.013 * k}"), "*~ 0.5", "+~ 0.5")
        b = mul(s, v, sw)
        gl, gr = [(1, 0.2), (0.2, 1), (0.8, 0.5), (0.5, 0.8), (1, 0.4), (0.4, 1)][k]
        s.c(s.to(b, f"*~ {gl}"), 0, L, 0)
        s.c(s.to(b, f"*~ {gr}"), 0, R, 0)
    throws_to("ac-senda")(s, mul(s, L, ln), mul(s, R, ln), mix=0.5, send=0.6)
    return s


def atm_deep():
    s, ln = switched("atm-deep", "ac-g-atm1")
    s.comment("Deep: a low rumble, different on each side, swelling slowly; now and then distant thunder rolls")
    th = s.ch(s.m(s.recv("ac-thunder"), "1 2500, 0 7000 2500"), "vline~")
    outs = []
    for k, rate in enumerate((0.027, 0.019)):
        r = s.ch(s.obj("noise~"), "lop~ 90", "lop~ 180", "*~ 14")
        sw = s.ch(s.obj(f"osc~ {rate}"), "*~ 0.4", "+~ 0.6")
        thn = mul(s, s.ch(s.obj("noise~"), "lop~ 260", "lop~ 400", "*~ 10"), s.to(th, f"*~ {[1, 0.6][k]}"))
        outs.append(mul(s, add(s, mul(s, r, sw), thn), ln))
    throws_to("ac-senda")(s, outs[0], outs[1], mix=0.22, send=0.25)
    return s


def atm_space():
    s, ln = switched("atm-space", "ac-g-atm2")
    s.comment("Space: air ringing in two combs tuned to the chord (root left, fifth right) - a far-away choir")
    outs = []
    for k in range(2):
        a = s.obj("+~")
        s.c(s.ch(s.obj("noise~"), "lop~ 3000", "*~ 0.03"), 0, a, 0)
        s.to(a, f"delwrite~ $0-sp{k} 40")
        vd = s.obj(f"vd~ $0-sp{k}")
        s.c(s.ch(s.recv(f"ac-atmc{k}"), "line~"), 0, vd, 0)
        s.c(s.ch(vd, "lop~ 2200", "*~ 0.985"), 0, a, 1)
        sw = s.ch(s.obj(f"osc~ {0.017 + 0.009 * k}"), "*~ 0.45", "+~ 0.55")
        outs.append(mul(s, mul(s, s.ch(vd, "hip~ 60", "*~ 5"), sw), ln))
    throws_to("ac-senda")(s, outs[0], outs[1], mix=0.8, send=0.8)
    return s


def atm_night():
    s, ln = switched("atm-night", "ac-g-atm3")
    s.comment("Night: distant insects - six high tones chirring at their own rates, scattered across the field, "
              "over a faint hiss")
    L, R = s.obj("*~ 0.16"), s.obj("*~ 0.16")
    for k in range(6):
        tone = s.ch(s.recv(f"ac-atmn{k}"), "line~", "osc~")
        pulse = s.ch(s.obj(f"osc~ {19 + 2.3 * k}"), "max~ 0")
        gate = s.ch(s.obj(f"osc~ {0.09 + 0.07 * k}"), "-~ 0.3", "max~ 0", "*~ 1.4")
        b = mul(s, mul(s, tone, mul(s, pulse, pulse)), gate)
        pos = [0.1, 0.85, 0.35, 0.65, 0.2, 0.95][k]
        s.c(s.to(b, f"*~ {(1 - pos) ** 0.5:.3f}"), 0, L, 0)
        s.c(s.to(b, f"*~ {pos ** 0.5:.3f}"), 0, R, 0)
    bed = [s.ch(s.obj("noise~"), "hip~ 6000", "*~ 0.004") for _ in range(2)]
    throws_to("ac-senda")(s, mul(s, add(s, L, bed[0]), ln), mul(s, add(s, R, bed[1]), ln), mix=1, send=0.5)
    return s


def atm_tides():
    s, ln = switched("atm-tides", "ac-g-atm4")
    s.comment("Tides: waves that wash across from one side to the other - noise whose level and brightness "
              "rise and fall over ~11 s, the right side a third of a wave behind")
    ph = s.obj("phasor~ 0.09")
    outs = []
    for off in (0, 0.33):
        p = s.ch(ph, f"+~ {off}", "wrap~") if off else ph
        e = s.ch(p, "cos~", "*~ -0.5", "+~ 0.5")
        e2 = mul(s, e, e)
        v = s.obj("vcf~ 0.8")
        s.c(s.obj("noise~"), 0, v, 0)
        s.c(s.ch(e2, "*~ 2200", "+~ 300"), 0, v, 1)
        outs.append(mul(s, s.ch(mul(s, (v, 1), e2), "*~ 1.1"), ln))
    throws_to("ac-senda")(s, outs[0], outs[1], mix=0.9, send=0.5)
    return s


ATMOS = (atm_haze, atm_deep, atm_space, atm_night, atm_tides)
