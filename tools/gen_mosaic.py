"""MOSAIC: one rhythmic pattern carried across the layers - a cascade, like a canon across the ensemble.

The piece brings it into its development sections and its climax (SETUP MOSAIC FORM); aux + low C# (a tap) brings
it in yourself, one layer a bar (bells, pads, sub, drone, textures), and out again the same way
backwards; held, it opens SETUP MOSAIC. The pattern is the motion's Euclidean rhythm (its hits in its steps, rotated),
on the clock's 16ths (an external MIDI clock too) at the MOSAIC Pace; each layer plays it Cascade steps after the
one before. Its pattern is its own (SETUP MOSAIC Hits: k of n steps, or the motion's), not the piece's density; each
layer steps at its own rate (MOSAIC RATES: 1/4x .. 2x the Pace), all on one grid, so they interlock. What each layer
does with a hit is its role (SETUP MOSAIC ROLES):
  bells     off / echo (the chord tones in turn, two octaves up) / high (three)
  pads      held / pulse (all four voices re-articulate) / arpeggio (one voice sounds out at a time, the others
            dip) / lines (a PAD LINES move on each hit)
  sub       held / bass (root, root, 5th, octave, as a bass line) / pulse
  drone     held / pulse / pedal (a 5th up and back, a bar each - the held note that carries over) / pulse+pedal
  textures  held / gated (open on a hit, closing towards the next) - their role is their rate
An accent is the layer's level dipping by Accent and swelling back (pulse), or held down between hits (arpeggio,
gated). Nothing here draws random numbers: seeds replay."""
from pdlib import Canvas, proc, X, V, Send, Call, SendL, If, Toast
import gen_setup as S

GLOBALS = dict(acmos=0, acmosp=0, acmost=0, acmosn=0, acmst=0, acmsd=250, acmbn=0, acmsb=0, acmped=0, acmoskh=-1)
ARRAYS = {}

LAYERS = ["bells", "pads", "sub", "drone", "textures"]      # (their cascade order: the join order)
PACE = "if(acmpace == 0, 1, if(acmpace == 1, 2, 4))"         # (steps of 16ths per mosaic step)
# (the pattern: its hits K in N steps - the motion's, or MOSAIC Hits' own)
K = "if(acmhit == 0, acmk, " + "".join(f"if(acmhit == {i}, {k}, " for i, (_, k, _) in enumerate(S.SMHIT) if i) + "1" + ")" * len(S.SMHIT)
N = "if(acmhit == 0, acmn, " + "".join(f"if(acmhit == {i}, {n}, " for i, (_, _, n) in enumerate(S.SMHIT) if i) + "1" + ")" * len(S.SMHIT)
ROT = "if(acmhit == 0, acmrot, 0)"


def rate(var, shift=0):
    """a layer's step in 16ths: the Pace x its rate (1/4x .. 2x), at least one 16th"""
    return ("max(1, " + PACE + "*" + "".join(f"if({var} - {shift} == {i}, {r}, " for i, (_, r) in enumerate(S.SMRATE))
            + "1" + ")" * len(S.SMRATE) + ")")


def deg2p(d):
    return f"(actonic + 12*floor(({d})/acn) + acscale[(int({d}) % int(acn) + int(acn)) % int(acn)])"


def hit(s):
    """the pattern (Euclidean: K hits spread over N steps) at step s"""
    return f"((((int({s}) + int({ROT})) % int({N}) + int({N})) % int({N})) * int({K})) % int({N}) < {K}"


def pulse(dest):
    """a dip by Accent and a swell back over most of the step"""
    return SendL(dest, ["1 - acmacc", "acmsd*0.8"], "$1 5, 1 $2 5")


def reset(i):
    """layer i leaves the mosaic (or its role changes): its levels and notes back as the piece has them"""
    return [
        [],
        [SendL(f"ac-v{k}-acc", ["1"], "$1 200") for k in range(4)],
        [SendL("ac-acc-s", ["1"], "$1 100"), Call("ac-bassupd")],
        [SendL("ac-acc-d", ["1"], "$1 100"), V("acmped", "0"), Call("ac-bassupd")],
        [SendL("ac-acc-t", ["1"], "$1 100")],
    ][i]


def mosaic():
    c = Canvas("mosaic", w=3000)
    c.comment("MOSAIC: the motion's rhythm carried across the layers, a cascade (aux + low C#; SETUP MOSAIC)")
    proc(c, "ac-mostoggle", [V("acmos", "1 - acmos"), If("acmos", [Toast("mosaic in")], [Toast("mosaic out")])])
    # aux + low C# held 0.5 s: the MOSAIC page (gen_ui)
    proc(c, "ac-moshold", [V("acmoskh", "1"), V("acsetup", "1"), V("acsetpg", str(S.SETUP_NAMES.index("MOSAIC"))),
                           Call("ac-oledsetup")])
    # the piece's own (SETUP MOSAIC FORM): at each section, how many layers it wants - a development section Develop's,
    # a climax all five (Sections: off, climax, develop+climax, all but the calm emerge / break / dissolve)
    want = ("(acmsec*acwrite) > 0 && acrun && (acrole == 4 || ((acmsec*acwrite) >= 2 && (acrole == 2 || acrole == 3)) || "
            "((acmsec*acwrite) == 3 && acrole != 0 && acrole != 5 && acrole != 7))")
    proc(c, "ac-mossec", [V("acmosp", f"({want})*if(acrole == 4, {len(LAYERS)}, acmspn + 2)")])
    # a bar: a layer in (or out) towards the target - all five while you have it in (aux + C#), else the piece's;
    # Joins at once: straight there. And the drone's pedal.
    join = [If(f"acmosn == {i + 1}", [Toast(f"mosaic + {n}")]) for i, n in enumerate(LAYERS)]
    leave = [If(f"acmosn == {i}", reset(i)) for i in range(len(LAYERS))]
    pedal = "acmosn > 3 && (acmrd == 2 || acmrd == 3)"
    proc(c, "ac-mosbar", [
        V("acmost", f"if(acmos, {len(LAYERS)}, acmosp)"),
        If("acmsjo == 1 && acmosn != acmost", [
            *[If(f"{i} >= acmost && {i} < acmosn", reset(i)) for i in range(len(LAYERS))],
            If("acmosn == 0", [Toast("mosaic in")]), V("acmosn", "acmost"), If("acmosn == 0", [Toast("mosaic out")])], [
            If("acmosn < acmost", [V("acmosn", "acmosn + 1")] + join),
            If("acmosn > acmost", [V("acmosn", "acmosn - 1")] + leave + [If("acmosn == 0", [Toast("mosaic out")])])]),
        If(f"{pedal} && acgdrone > 0.01", [
            V("acmped", "1 - acmped"),
            SendL("ac-dronep", ["if(acpedal, acpedp, if(acsdnow, acsdt, actonic)) + 7*acmped", "3000"])],
           [If("acmped", [V("acmped", "0"), Call("ac-bassupd")])]),
    ])
    # a 16th: each layer on its own step (its rate), on the pattern Cascade of its steps after the layer before
    acts = [
        # bells: the chord tones in turn, high (the bar's first step a little stronger)
        ("acmrtb", 0, If("acmrb > 0 && acgbell > 0.01", [
            V("acmbn", "(acmbn + 1) % 4"),
            SendL("ac-bell", ["min(103, acnew[int(acmbn)] + 12*(1 + acmrb))", "0.4 + 0.15*(int(acmst) % 8 == 0)",
                              "0.25 + 0.5*(int(acmst) % 2)"])])),
        # pads
        ("acmrtp", 0, If("acgpad > 0.01", [
            If("acmrp == 1", [pulse(f"ac-v{k}-acc") for k in range(4)]),
            If("acmrp == 2", [SendL(f"ac-v{k}-acc", [f"if(int(acmst) % 4 == {k}, 1, 1 - acmacc)", "15"])
                              for k in range(4)]),
            If("acmrp == 3", [V("acplforce", "1"), Call("ac-plgo"), V("acplforce", "0")])])),
        # sub: a bass line (root, root, 5th, octave) or a pulse
        ("acmrts", 0, If("acgsub > 0.01", [
            If("acmrs == 1", [
                V("acmsb", "(acmsb + 1) % 4"),
                V("acmbn", deg2p("acdeg + if(acmsb == 2, 4, if(acmsb == 3, acn, 0))")),
                V("acmbn", "acmbn - 12*ceil(max(0, acmbn - 43)/12) + 12*ceil(max(0, 28 - acmbn)/12)"),
                SendL("ac-subp", ["mtof(acmbn)", "30"]), V("acmbn", "int(acmst) % 4")]),
            If("acmrs == 2", [pulse("ac-acc-s")])])),
        # drone: a pulse (pulse, pulse+pedal), at the Pace
        (None, 0, If("acgdrone > 0.01 && (acmrd == 1 || acmrd == 3)", [pulse("ac-acc-d")])),
        # textures: gated, open on the hit, closing towards the next (their rate: held, or 1/4x .. 2x)
        ("acmrtt", 1, If("acmrtt > 0 && acgtex > 0.01", [SendL("ac-acc-t", ["1 - acmacc", "acmsd*0.8"], "1 3, $1 $2 3")])),
    ]
    steps = []
    for i, (rv, shift, act) in enumerate(acts):
        r = rate(rv, shift) if rv else PACE
        steps.append(If(f"acmosn > {i} && int(acstep) % int({r}) == 0", [
            V("acmst", f"int(acstep/int({r}))"), V("acmsd", f"15000/acbpm*int({r})"),
            If(hit(f"acmst - {i}*acmcas"), [act])]))
    proc(c, "ac-step", shared=True, steps=[If("acmosn > 0 && acrun", steps)])
    return c
