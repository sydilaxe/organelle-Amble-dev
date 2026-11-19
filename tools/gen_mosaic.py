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
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, Toast
import gen_setup as S

GLOBALS = dict(acbars=0, acmkn=0, acmos=0, acmosp=0, acmost=0, acmosn=0, acmst=0, acmsd=250, acmbn=0, acmsb=0, acmped=0, acmoskh=-1)
ARRAYS = dict(acmjt=6)            # (when each layer joined: it fades in over two bars)

LAYERS = ["bells", "pads", "sub", "drone", "textures", "sparkle"]     # (their cascade order: the join order)
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


def fade(i):
    """layer i's share of the mosaic: 0 when it joins, all of it two bars later (it fades in, not suddenly)"""
    return f"min(1, max(0, (acnow - acmjt[{i}])/max(1, 120000/acbpm*acmeter)))"


def dep(i):
    return f"acmacc*{fade(i)}"


def pulse(dest, i):
    """a dip by Accent and a swell back over most of the step"""
    return SendL(dest, [f"1 - {dep(i)}", "acmsd*0.8"], "$1 5, 1 $2 5")


def reset(i):
    """layer i leaves the mosaic (or its role changes): its levels and notes back as the piece has them"""
    # (the levels ease back over 1.5 s - it fades out, not suddenly)
    return [
        [],
        [SendL(f"ac-v{k}-acc", ["1"], "$1 1500") for k in range(4)],
        [SendL("ac-acc-s", ["1"], "$1 1500"), Call("ac-bassupd")],
        [SendL("ac-acc-d", ["1"], "$1 1500"), V("acmped", "0"), Call("ac-bassupd")],
        [SendL(f"ac-acc-{x}", ["1"], "$1 1500") for x in "tac"],
        [Call("ac-sparkupd")],
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
    join = [If(f"acmosn == {i + 1}", [T("acmjt", i, "acnow"), Toast(f"mosaic + {n}")] + (
        [Call("ac-sparkupd")] if n == "sparkle" else [])) for i, n in enumerate(LAYERS)]
    leave = [If(f"acmosn == {i}", reset(i)) for i in range(len(LAYERS))]
    pedal = "acmosn > 3 && (acmrd == 2 || acmrd == 3)"
    proc(c, "ac-mosbar", [
        V("acbars", "(acbars + 1) % 64"),        # (bars counted, whatever the meter: DRIFT Lock's clock)
        V("acmost", f"if(acmos, {len(LAYERS)}, acmosp)"),
        If("acmsjo == 1 && acmosn != acmost", [
            *[If(f"{i} >= acmost && {i} < acmosn", reset(i)) for i in range(len(LAYERS))],
            *[If(f"{i} < acmost && {i} >= acmosn", [T("acmjt", i, "acnow")]) for i in range(len(LAYERS))],
            If("acmosn == 0", [Toast("mosaic in")]), V("acmosn", "acmost"), Call("ac-sparkupd"),
            If("acmosn == 0", [Toast("mosaic out")])], [
            If("acmosn < acmost", [V("acmosn", "acmosn + 1")] + join),
            If("acmosn > acmost", [V("acmosn", "acmosn - 1")] + leave + [If("acmosn == 0", [Toast("mosaic out")])])]),
        If(f"{pedal} && acgdrone > 0.01", [
            V("acmped", "1 - acmped"),
            SendL("ac-dronep", ["if(acpedal, acpedp, if(acsdnow, acsdt, actonic)) + 7*acmped", "3000"])],
           [If("acmped", [V("acmped", "0"), Call("ac-bassupd")])]),
    ])
    # a 16th: each layer on its own step (its rate), on the pattern Cascade of its steps after the layer before
    acts = [
        # bells: the chord tones in turn, high (the bar's first step a little stronger), louder as they fade in
        ("acmrtb", 0, If("acmrb > 0 && acgbell > 0.01", [
            V("acmbn", "(acmbn + 1) % 4"),
            SendL("ac-bell", ["min(103, acnew[int(acmbn)] + 12*(1 + acmrb))",
                              f"(0.4 + 0.15*(int(acmst) % 8 == 0))*(0.3 + 0.7*{fade(0)})", "0.25 + 0.5*(int(acmst) % 2)"])])),
        # pads: pulse, arpeggio, or lines - the PAD LINES carried on the pattern: a line move on each hit, the voice
        # that moved sounding out; where no line moves (a still chord, Lines at 0) the chord is arpeggiated instead
        ("acmrtp", 0, If("acgpad > 0.01", [
            If("acmrp == 1", [pulse(f"ac-v{k}-acc", 1) for k in range(4)]),
            If("acmrp == 3", [X("1; 0", "v acplforce", "v acplmv"), Call("ac-plgo"), V("acplforce", "0")]),
            If("acmrp == 3 && acplmv", [If(f"acplk == {k}", [pulse(f"ac-v{k}-acc", 1)]) for k in range(4)]),
            If("acmrp == 2 || (acmrp == 3 && acplmv == 0)",
               [SendL(f"ac-v{k}-acc", [f"if(int(acmst) % 4 == {k}, 1, 1 - {dep(1)})", "15"]) for k in range(4)])])),
        # sub: a bass line (root, root, 5th, octave) or a pulse
        ("acmrts", 0, If("acgsub > 0.01", [
            If("acmrs == 1", [
                V("acmsb", "(acmsb + 1) % 4"),
                V("acmbn", deg2p("acdeg + if(acmsb == 2, 4, if(acmsb == 3, acn, 0))")),
                V("acmbn", "acmbn - 12*ceil(max(0, acmbn - 43)/12) + 12*ceil(max(0, 28 - acmbn)/12)"),
                SendL("ac-subp", ["mtof(acmbn)", f"30 + 400*(1 - {fade(2)})"])]),
            If("acmrs == 2", [pulse("ac-acc-s", 2)])])),
        # drone: a pulse (pulse, pulse+pedal), at the Pace
        (None, 0, If("acgdrone > 0.01 && (acmrd == 1 || acmrd == 3)", [pulse("ac-acc-d", 3)])),
        # textures, atmosphere and cloud: gated, open on the hit, closing towards the next (held, or 1/4x .. 2x)
        ("acmrtt", 1, If("acmrtt > 0", [SendL(f"ac-acc-{x}", [f"1 - {dep(4)}", "acmsd*0.8"], "1 3, $1 $2 3")
                                        for x in "tac"])),
        # sparkle: GLINT's small bells high on the chord tones, on the pattern (off, or 1/4x .. 2x)
        ("acmspk", 1, If("acmspk > 0", [
            V("acmkn", "(acmkn + 1) % 4"),
            SendL("ac-glint", ["min(108, acnew[int(acmkn)] + 24 + 12*(int(acmst) % 3 == 0))",
                               f"(0.3 + 0.1*(int(acmst) % 4 == 0))*{fade(5)}", "0.15 + 0.7*fmod(acmst*0.37, 1)", "700"])])),
    ]
    steps = []
    for i, (rv, shift, act) in enumerate(acts):
        r = rate(rv, shift) if rv else PACE
        steps.append(If(f"acmosn > {i} && int(acstep) % int({r}) == 0", [
            V("acmst", f"int(acstep/int({r}))"), V("acmsd", f"15000/acbpm*int({r})"),
            If(hit(f"acmst - {i}*acmcas"), [act])]))
    proc(c, "ac-step", shared=True, steps=[If("acmosn > 0 && acrun", steps)])
    return c
