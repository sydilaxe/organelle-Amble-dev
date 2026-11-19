"""The composer's control logic: seed, piece, form (sections), harmony (changes), event players.

Conventions: global state lives in [value]s named ac<word> (no dash, so [expr] can read them);
every [send]/[receive] name has a dash (ac-<word>), so values and sends never share a symbol."""
from pdlib import Canvas, proc, X, V, T, Send, Call, SendL, If, Loop, run_steps, Arm, Toast, RNG, Later, Line
from data import *
from data import DRONES, CHARACTERS, ATMOS_NAMES, ATMOS_ROLE, SCENE_DATA, SCENE_ROLE, \
    FLAVOUR_WEIGHTS, FM_RATIO_WEIGHTS, PARTIAL_WEIGHTS, pick_table, STRIKES, BELL_ENGINE_WEIGHTS, MOTION_ENGINE_WEIGHTS

NF = len(FAMILIES)
NS = len(SCALES)
# a piece's own picks: the original types, or every type with SETUP HARMONY New types on
FLAV_N = f"if(acnewt, {len(FLAVOURS)}, {FLAV_AUTO})"
TEX_N = f"if(acnewt, {len(TEXTURES)}, {TEX_AUTO})"
DRONE_N = f"if(acnewt, {len(DRONES)}, {DRONE_AUTO})"
EUCLID_N = f"if(acnewt, {len(EUCLID)}, {EUCLID_AUTO})"

GLOBALS = dict(
    acfamc=0, acflxf=4000,
    acxt=48, acxscf=0, acxsci=0, acxdeg=0, acqt=0, acqd=0, acqr=0, acqn=0, acqi=0, acq3=0, acq4=0, acq6=0, acq7=0,
    acq8=0, acchn=0, acnxn=0, acchgt=0,
    acseed=1, account=0, actonic=38, acsci=0, acn=7, acfamA=0, acfamB=1, acfam=0, acdeg=0, acpend=-1, acxpick=0,
    acmode=1, acrun=1, acended=0, acstopped=0, acready=0, acsecrem=0, acsec=0, acnsec=8, acenergy=0.5, acdeff=0.5, acsecdur=60000, acchsec=20,
    acpage=0, acinmode=0, acfreeze=0, accapt=0, acvfreeze=0,
    acmxq=0, acsgms=200, acmuser=0, acmuk=3, acmun=8, acmurot=0, acmusw=-1, acmghost=0, acmrat=0, acmharm=0, acmpk=3, acmpn=8, acmprot=0, acmpsw=0, acmv=0, acmdl=0, acmpan=0.5, acmh=0, acbuser=0, acbru0=1, acbru1=1, acbru2=1, acbru3=1, acbru4=1, acbt0=0, acbt1=0, acbt2=0, acbt3=0, acbt4=0, acbghost=0, acbrat=0, acbrub=1, acbharm=0, acbv=0, acbpan=0.5, acbh=0, acbint=1000, acbgp=0,  acsubt=0, acsleep=0, acshdt=0.5, acshdd=0, acshdw=0.5, acshst=0.5, acshsd=0, acshsw=0.5, acshpt=0.5, acshpd=0, acshpw=0.5, acshbt=0.5, acshbd=0, acshbw=0.5, acshmt=0.5, acshmd=0, acshmw=0.5, acshtt=0.5, acshtd=0, acshtw=0.5, acshat=0.5, acshad=0, acshaw=0.5, acshct=0.5, acshcd=0, acshcw=0.5, acmdrone=1, acmgd=1, acmgs=1, acmgp=1, acmgb=1, acmgm=1, acmgt=1, acmgc=1, acmga=1, acmpad=1, acmtex=1, acmcloud=1, acmbell=1, acmmotion=1, acmsub=1, acmatm=1, acedrone=1, acsxdrone=0, acsldrone=1, acesub=1, acsxsub=0, acslsub=1, acepad=1, acsxpad=0, acslpad=1, acebell=1, acsxbell=0, acslbell=1, acemotion=1, acsxmotion=0, acslmotion=1, acetex=1, acsxtex=0, acsltex=1, aceatm=1, acsxatm=0, acslatm=1, acecloud=1, acsxcloud=0, acslcloud=1, acscount=0, acsecc=0, acsecsel=0, acsecfol=1, acsecq=0, acsecqn=0, acst=0, acslay=0, acspe=0,
    acfdrone=1, acfpad=1, acftex=1, acfcloud=1, acfbell=1, acfmotion=0, actex1=0, actex2=1, actexA=0, actexB=1,
    acpal1=0, acpal2=1, acpal3=3, acpartI=0, acbellI=0, acsecbright=0.8, actidef=1, acpow=1,
    acpsum=1, acfirst=1, acmodflag=0, acD=0, acp0=0, acp1=0, aci=0, acchg=0, acfade=8000,
    actime=1, acgdrone=0, acgpad=0, acgtex=0, acgcloud=0, acgbell=0, acgmotion=0,
    acgt0=0, acgt1=0, acgt2=0, acgt3=0,
    # how the piece writes (SETUP LINES, HARMONY, PHRASE, DIALOGUE)
    acmgi=-1, acmgn=1, acvc=0, acvd0=0, acvd1=0, acvd2=0, accp=0, acpsd=0, acphc=-1, acphn=0, acphd=4, acphs=3, acsfit=1,
    acsdt=36, acsds=0, acsdg=-1, acsdret=0, acsdnow=0, acmvr=0, acmvq=0, acmvo=0, acvb=0, acvbd=0, acki=0, acmdvt=0,
    acansm=1, acbarn=0, acanst=-1e+06, acant=60, acrestb=0, acrestl=0, acrestp=0,
    acmdg=0, acbdir=0, acbpl=0, acpmi=0, acpmp=0, acsusp=0, acbrq=0, acfinm=0, acfinb=0,
    acphpos=-1, acsecdue=0, acsecwait=0, acsecalm=0, acblt=-1e+06,
    acrcn=8, acrcs=0, acdyn=1, acten=0, acpedal=0, acpedp=43, acgbi=0, acgbp=0, acsgi=0, acsgr=0,
    acmdgl=0, acmpl=0, acmivl=-1, acmbpl=0, acbim=0, acbis=0, acansmp=1, acphsc=-1, acphrs=0, acltx=-1,
    acyon=0, acyrn=0, acyq=0, acyqd=0, acyqb=99, acyj=0, acyt0=0,
    acbi=0, acbc=0, acdropi=0, acbright=0.5, acbp=0, acgdurv=300, acr1=0.5, acr2=0.5, acr3=0.5, acr4=0.5,
    acknown0=0, acknown1=0, acknown2=0, acknown3=0, acinprev=0, acghost=0,
    # form
    acarch=0, acpk=3, acpkv=0, acrecap=-1, achome=38, acaway1=7, acaway2=5, acrole=2, acprogn=0, acprogi=0,
    acmtr=2, acbld=1, acblp=0.5, acvauto=1, acvsec=1, acvtype=1, acrvsize=1,
    # rhythm
    acbpm0=56, acbpm=56, actpos=0.5, acmeter=4, actick=0, acstep=0, acms=0, acmk=5, acmn=8, acmei=0, acmrot=0, acmdiv=1,
    acmarp=0, acshed=0, acmai=0, acmoct=12, acmswing=0, acgdlock=0, acmp=60, acdtype=0, acdtype2=1, acdcur=0, acsubm=0, acsubx=0, acchar=0, accheff=0, acflstag=4200, acres=0, acbela=0, acmota=1, acdauto=0, actex1a=0, actex2a=1, acspad=0, acsdrone=0, acstex=0, acschar=0, acsnew=0, acchamt=0.5, acavoc=0, acgvoc=0, acdb=0, acgt4=0, acgt5=0, acgt6=0, acgt7=0, acgt8=0, acgt9=0, acgt10=0, acgt11=0, acgt12=0, acgt13=0, acgt14=0, acgt15=0, acbbn=0, acbbv=0, acmeisel=0, acbrsel=0, acmeia=0, acrkey=0, acrsel=0, acsgn=0, acsgd=0, acgsub=0, acatm=0, acatmT=0, acatmT2=1, acfatm=0, acatmcur=0, acgatm=0, acscene=0, acmono=0, acwidth=1, acpanmot=0.8, acfd=-1, acgbands=0, acgres=0, ackn=0, ackv=0,
)
for page in PAGES:
    for _, name, d in page:
        GLOBALS[name] = d

ARRAYS = dict(acsroles=12, acslens=12, acssp=12, acsst=96, acslv=96, acscale=16, acfamt=NF * 5, acch=4, acnew=4, acplan=16, acpdur=16, acmotif=8, acmotif0=8,
              acmrhy=8, acmrhya=8, acbrhyt=5 * len(BELL_RHYTHMS), acmoves=12, acmods=12, acmovp=12, acmodp=12, acplfam=len(PLEASING_FAMS), acplsc=len(PLEASING_SCALES), acgrt=12, acfmrt=8, acpartt=24, acbellt=12, acdintt=5, acrhyt=5,
              acparams=4 * len(PAGES), acraw=4, acflav=4, acroles=16, acflpick=40, acbelpk=40, acmotpk=40, acfmrpick=40, acpapick=40, acscn=50,
              acscrole=24, acatmrole=8, ackeyp=16, acprog=8, acrmask=48, acrtide=8,
              acrtempo=8, acrpulse=8, acaway=8, aceuk=len(EUCLID), aceun=len(EUCLID), acmeters=6, acmratios=6, acbrper=4, actlo=5, acthi=5,
              acmtur=8, acvu=4, acvl=4, acmdt=5, acmimit=3, acyou=6, acyout=6, acrcm=64)

# the piece tempo: its place (actpos) in the tempo range chosen in SETUP
# (SETUP FORM Tempo: a fixed tempo instead, the same in every section)
TEMPO0 = ("if(acstempo > 0, " + "if(acstempo == 1, 40, if(acstempo == 2, 48, if(acstempo == 3, 56, if(acstempo == 4, 64, if(acstempo == 5, 72, if(acstempo == 6, 80, if(acstempo == 7, 90, if(acstempo == 8, 100, if(acstempo == 9, 110, if(acstempo == 10, 120, 140))))))))))" + ", actlo[int(actrange)] + int(actpos*(acthi[int(actrange)] - actlo[int(actrange)] + 1)))")
# the beat the slow layers feel: half speed above HALFTIME
BPMH = f"(acbpm/(1 + (acbpm > {HALFTIME})))"

import gen_live as _L
import gen_oled as _O
import gen_setup as _S
import gen_perform as _P
import gen_log as _LG
for _m in (_L, _O, _S, _P, _LG):
    # every value is declared once: two modules declaring one name share it, and one's private counter silently
    # becomes the other's state (the profile's step counter was the live input's acpst; a macro's knob, the rhythm's acmk)
    _same = set(GLOBALS) & set(_m.GLOBALS)
    assert not _same, f"{_m.__name__}: values also declared elsewhere: {sorted(_same)}"
    assert not set(ARRAYS) & set(_m.ARRAYS), f"{_m.__name__}: arrays declared twice: {set(ARRAYS) & set(_m.ARRAYS)}"
    _va = (set(GLOBALS) | set(_m.GLOBALS)) & (set(ARRAYS) | set(_m.ARRAYS))
    assert not _va, f"{_m.__name__}: a value and an array share a name: {sorted(_va)}"
    GLOBALS.update(_m.GLOBALS)
    ARRAYS.update(_m.ARRAYS)

DATA_TABLES = dict(
    acsroles=[8] * 12, acslens=[1] * 12, acssp=[0] * 12, acsst=[0] * 96, acslv=[1] * 96,
    acflpick=pick_table(FLAVOUR_WEIGHTS), acbelpk=pick_table(BELL_ENGINE_WEIGHTS), acmotpk=pick_table(MOTION_ENGINE_WEIGHTS), acfmrpick=pick_table(FM_RATIO_WEIGHTS), acpapick=pick_table(PARTIAL_WEIGHTS),
    acscn=sum(SCENE_DATA, []), acscrole=sum(SCENE_ROLE, []), acatmrole=ATMOS_ROLE,
    acmoves=MOVES, acmods=MODS, acmovp=MOVES_P, acmodp=MODS_P,
    acplfam=[[n for n, _, _ in FAMILIES].index(f) for f in PLEASING_FAMS],
    acplsc=[[n for n, _ in SCALES].index(x) for x in PLEASING_SCALES], acgrt=GRAIN_RATIOS, acfmrt=FM_RATIOS,
    acpartt=sum(PARTIAL_SETS, []), acbellt=sum(BELL_SETS, []), acdintt=DRONE_INTERVALS, acrhyt=RHYTHMS,
    acparams=[d for p in PAGES for _, _, d in p], acraw=[0.5] * 4, aclvn=[-1] * 4, acrmask=sum(ROLE_MASK, []),
    acrtide=ROLE_TIDE, acrtempo=ROLE_TEMPO, acrpulse=ROLE_PULSE, acaway=AWAY, aceuk=[k for k, n in EUCLID],
    aceun=[n for k, n in EUCLID], acbrhyt=sum([r for _, r in BELL_RHYTHMS], []), acmeters=METERS, acmratios=MOTION_RATIOS, acbrper=BREATH_PERIODS,
    actlo=[lo for _, lo, _ in TEMPOS], acthi=[hi for _, _, hi in TEMPOS],
)
DATA_TABLES.update(_P.DATA_TABLES)
DATA_TABLES.update(_S.DATA_TABLES)                 # (SETUP's groups: each page's group, place, count)

# the layers a custom section sets (SETUP SECTION MIX), in the order of the layer keys
SEC_LAYERS = ["drone", "sub", "pad", "bell", "motion", "tex", "atm", "cloud"]
ROLE_ENERGY = [0.15, 0.4, 0.55, 0.75, 1.0, 0.3, 0.5, 0.2]     # a custom section's energy, by role
SEC_LENS = [0.6, 1.0, 1.5]                                     # short, normal, long

# the form archetypes: energy at x (0..1 through the piece)
ARCH_EXPR = ("if(acarch==0, pow(sin(3.14159*X), acpow), if(acarch==1, if(X<0.78, pow(X/0.78, 1.5), (1-X)/0.22), "
             "if(acarch==2, (0.55 - 0.45*cos(12.566*X))*(0.4 + 0.6*sin(3.14159*X)), "
             "if(acarch==3, max(exp(-pow((X-0.33)/0.13, 2)), 0.9*exp(-pow((X-0.75)/0.12, 2))), "
             "min(1, 1.3*pow(sin(3.14159*X), 0.6))))))")


# the bells' own step lengths (top D# held + low keys), read by step index aci
BRU = "if(aci == 0, acbru0, if(aci == 1, acbru1, if(aci == 2, acbru2, if(aci == 3, acbru3, acbru4))))"


def deg2p(d):
    """scale degree (may be negative) -> pitch above the tonic"""
    return (f"(actonic + 12*floor(({d})/acn) + "
            f"acscale[(int({d}) % int(acn) + int(acn)) % int(acn)])")


def globals_():
    g = Canvas("globals")
    g.comment("Every global value, its default, and the data tables")
    for name in GLOBALS:
        g.obj("v " + name)
    g.col()
    for name, n in ARRAYS.items():
        g.obj(f"array define {name} {n}")
    g.col()
    r = g.recv("ac-init")
    t = g.to(r, "t b b")
    # defaults: [expr acx = 1; acy = 0; ...] stores (the [v]s above declare the names), 50 to a box
    items = list(GLOBALS.items())
    for k in range(0, len(items), 50):
        g.c(t, 1, g.obj("expr " + "; ".join(f"{n} = {v:.10g}" for n, v in items[k:k + 50])), 0)
    g.col()
    fam = []
    for _, typ, offs in FAMILIES:
        fam += [typ] + offs
    tables = dict(acfamt=fam, **DATA_TABLES)
    for name, vals in tables.items():
        m = g.m((t, 0), " ".join(f"{v:g}" for v in vals))
        g.c(m, 0, g.obj("array set " + name), 0)
    g.col()
    # scale loader
    r = g.recv("ac-loadscale")
    e = g.to(r, "expr acsci")
    tl = g.obj("t l l")
    s = g.to(e, "sel " + " ".join(str(i) for i in range(NS)))
    for i, (_, iv) in enumerate(SCALES):
        g.c(g.m((s, i), " ".join(f"{v:g}" for v in iv)), 0, tl, 0)
    g.c(g.to((tl, 1), "list length"), 0, g.obj("v acn"), 0)
    g.c(tl, 0, g.obj("array set acscale"), 0)
    return g


def rng():
    c = Canvas("rng")
    c.comment("ac-rng: refresh acr1..acr4 (0..1). Seeded per piece, so a seed replays its piece.")
    r = c.recv("ac-rng")
    t = c.to(r, "t b b b b")
    rs = c.recv("ac-seedrng")
    ts = c.to(rs, "t f f f f")
    c.col()
    for k in range(4):
        rnd = c.to((t, k), "random 1000000")
        c.ch(rnd, "/ 1e+06", f"v acr{k + 1}")
        # the first draws after a seed are close for some seeds (Pd's LCG): seed, then discard 5 draws
        h = c.to((ts, k), f"expr int(fmod(abs(sin(fmod($f1, 100000)*12.9898 + {k + 1}*78.233))*43758.5453, 1)*16777000) + {k + 1}")
        tw = c.to(h, "t b b b b b f")
        c.c(c.m((tw, 5), "seed $1"), 0, rnd, 0)
        for j in range(5):
            c.c(tw, j, rnd, 0)
    return c


def seed():
    c = Canvas("seed")
    c.comment("A counter in seed.txt goes up at every start-up; with timing jitter it seeds the first piece.")
    td = c.obj("text define acseedf")
    rt = c.obj("realtime")
    r = c.recv("ac-seedinit")
    # the start-up piece is prepared but waits (ready) for Start
    rd = c.to(r, "t b b")
    c.c(c.m((rd, 1), "1"), 0, c.obj("v acready"), 0)
    t = c.to((rd, 0), "t b b b")
    c.c(t, 2, rt, 0)
    c.c(c.m((t, 1), "read seed.txt"), 0, td, 0)
    mo = c.ch((t, 0), "text size acseedf", "moses 1")
    cnt = c.obj("+ 1")
    c.c(c.m((mo, 0), "0"), 0, cnt, 0)
    c.c(c.ch(c.m((mo, 1), "0"), "text get acseedf"), 0, cnt, 0)
    # (one trigger, right to left: save the count, set it, then read it into the seed)
    tf = c.to(cnt, "t b f f")
    c.c(c.m((tf, 2), "set $1, write seed.txt"), 0, td, 0)
    c.c(tf, 1, c.obj("v account"), 0)
    c.c(tf, 0, rt, 1)
    c.ch(rt, "expr int(fmod(account*7919 + $f1*1000003, 9999991))", "s ac-setseed")
    c.col()
    # explicit seed (tests, or to replay a piece) and the new-piece key (seeded by how long the patch ran)
    st = c.to(c.recv("ac-setseed"), "t b f f")
    c.c(st, 2, c.obj("v acseed"), 0)
    c.c(st, 1, c.obj("s ac-seedrng"), 0)
    c.c(st, 0, c.obj("s ac-newpiece"), 0)
    rt2 = c.obj("realtime")
    c.c(c.recv("ac-init"), 0, rt2, 0)
    c.c(c.recv("ac-reseed"), 0, rt2, 1)
    c.ch(rt2, "expr int(fmod(acseed*31 + $f1*977, 9999991)) + 1", "s ac-setseed")
    return c


def piece():
    c = Canvas("piece", w=3000)
    c.comment("A new piece: tonic, scale, voicings, timbre palette, ratios, tempo and meter, reverb, form")
    steps = [
        RNG,
        V("actonic", "if(ackeyc > 0, 35 + ackeyc, 36 + int(acr1*12))"),
        # (Harm: 0 = the pleasing palette only; up, more and more often the whole palette)
        V("acsci", f"if(acsclc > 0, acsclc - 1, if(fmod(acr2*13.7, 1) < acharmx, int(acr2*if(acnewt, {NS}, {SCALE_AUTO})), acplsc[int(fmod(acr2*7.31, 1)*{len(PLEASING_SCALES)})]))"),
        Call("ac-loadscale"),
        V("acfamA", f"if(fmod(acr3*11.3, 1) < acharmx, int(acr3*{NF}), acplfam[int(acr3*{len(PLEASING_FAMS)})])"),
        V("acfamB", f"if(fmod(acr4*9.1, 1) < acharmx, int(acr4*{NF}), acplfam[int(acr4*{len(PLEASING_FAMS)})])"),
        RNG,
        # the palette leans to the electronic and bell-like types (weights in data.py)
        X("acflpick[int(acr1*40)]; acflpick[int(acr2*40)]; acflpick[int(acr3*40)]", "v acpal1", "v acpal2",
          "v acpal3"),
        SendL("ac-fmr", ["acfmrt[int(acfmrpick[int(acr4*40)])]"]),
        RNG,
        X("acpapick[int(acr1*40)]; int(acr2*%s); int(acr3*%s); int(acr4*%d)" % (TEX_N, TEX_N, len(BELL_SETS)),
          "v acpartI", "v actexA", "v actexB", "v acbellI"),
        SendL("ac-partials", ["acpartt[int(acpartI)*4+1]", "acpartt[int(acpartI)*4+2]", "acpartt[int(acpartI)*4+3]"]),
        SendL("ac-bellset", ["acbellt[int(acbellI)*3]", "acbellt[int(acbellI)*3+1]", "acbellt[int(acbellI)*3+2]"]),
        RNG,
        SendL("ac-dint", ["acdintt[int(acr1*5)]"]),
        SendL("ac-lvtype", ["if(acvtsel >= 0, acvtsel, acpal1)"]),
        # the piece's drone design (and one for its break), sub mode, character on the pads, auto-vocode
        RNG,
        X(f"int(acr1*{DRONE_N}); int(acr2*{DRONE_N}); int(acr3*3); if(acr4 < 0.22, 0, 1 + int(acr4*4.99) % 4)",
          "v acdtype", "v acdtype2", "v acsubm", "v acchar"),
        RNG,
        X("0.35 + acr1*0.45; acr2 < 0.5", "v acchamt", "v acavoc"),
        RNG,
        X(f"acr1 < 0.55; int(acr2*{len(ATMOS_NAMES)}); int(acr3*{len(ATMOS_NAMES)})", "v acatm", "v acatmT", "v acatmT2"),
        # tempo, meter, motion timbre
        # (and the bells' and motion's engines for Auto, from the same draw: other picks stay as they were)
        X("acr2; acmeters[int(acr3*6)]; acbelpk[int(acr1*40)]; acmotpk[int(acr1*1600) % 40]", "v actpos", "v acmeter",
          "v acbela", "v acmota"),
        V("acmeter", "if(acsmeter > 0, acsmeter + 2, acmeter)"),
        V("acbpm0", TEMPO0),
        SendL("ac-mtimbre", ["acmratios[int(acr4*6)]"]),
        RNG,
        SendL("ac-mtimbre2", ["1 + acr1*4", "250 + acr2*700"]),
        # the reverb this piece likes (Auto): Bloom 1, Bloom 2, Hall, Shimmer
        X("if(acr3<0.42, 1, if(acr3<0.74, 2, if(acr3<0.9, 3, 4))); 0.8 + acr4*0.45", "v acvauto", "v acrvsize"),
        SendL("ac-rvsize", ["acrvsize"]),
        # key areas away from home
        RNG,
        X("actonic; acaway[int(acr1*8)]; acaway[int(acr2*8)]", "v achome", "v acaway1", "v acaway2"),
    ]
    for k in range(4):
        # pad breathing: cycles of 7, 9, 11, 13 half-bars, so the voices phase against each other
        steps += [RNG, SendL(f"ac-v{k}-lfo", [f"1/(30/(acbpm0/(1 + (acbpm0 > {HALFTIME})))*acmeter*acbrper[{k}]*(0.97+acr1*0.06))",
                                              "0.03+acr2*0.15", "0.04+acr3*0.25", "0.03+acr4*0.2"])]
    steps += [
        # the clock and the event players stop until the piece is set up, then start afresh (np3), so a seed
        # replays its piece whatever played before
        Send("ac-playstop"), Send("ac-clockhalt"),
        X("0; -1; 0; 1; 0; 0; 1; 0; 0; 0", "v acdeg", "v acpend", "v acchg", "v acfirst", "v acended", "v accapt",
          "v acrun", "v acsec", "v acprogn", "v acstopped"),
        Send("ac-master", "1 3000"),
        V("acel", "0"), Call("ac-clockstop"),
        X("-1; 0; -1; 0; 0; 0; 0; -1; 1; 0", "v acphc", "v acphn", "v acsdg", "v acsdret", "v acsdnow", "v acrestb",
          "v acrestp", "v acmgi", "v acmgn", "v acpsd"),
        X("0; 0; 0; 0; 0", "v acfinm", "v acfinb", "v acbrq", "v acmdg", "v acsusp"),
        Call("ac-motif0"),
        Call("ac-plan"),
        # the rest in stages a few ms apart (no single long tick): the first section, then the first chord
        Later("ac-np2", 3),
        Later("ac-scr", 109), Later("ac-oledall", 131),
    ]
    proc(c, "ac-newpiece", steps)
    proc(c, "ac-np2", [Call("ac-section"), Later("ac-np3", 5)])
    proc(c, "ac-np3", [
        Call("ac-change"),
        Call("ac-brightupd"), Call("ac-inputupd"),
        SendL("ac-weird", ["acweird"]), SendL("ac-motion", ["acmotion"]),
        V("actick", "-1"), Send("ac-clockgo"), Call("ac-clockstart"),
        Later("ac-playgo", 60), Later("ac-readystop", 75),
    ])
    # ready: a piece prepared (at start-up, or by new piece / mode while stopped) waits for Start, silent, at its
    # beginning
    proc(c, "ac-readystop", [If("acready", [
        X("1; 0; acsecdur*actime", "v acstopped", "v acrun", "v acsecrem"),
        Send("ac-master", "0 0"), Send("ac-chgstop"), Send("ac-secstop"), Call("ac-clockstop"),
        Call("ac-scr"), Send("ac-led"), Arm("ac-sleep", "1000", stop="ac-wake"),
    ])])
    # asleep: stopped, and the fade (8 s) and the reverb's tail are done - the layers, the pads' character and the
    # reverb switch off, so nothing computes in the silence (a performance log showed the same 36 % load stopped as
    # playing); Start wakes them under its fade-in. (Not during the profile, which plays parts while stopped.)
    proc(c, "ac-sleep", [If("acstopped && acprof == 0 && acsleep == 0", [
        V("acsleep", "1"), V("acfade", "300"), Call("ac-layers"), Call("ac-verbsel")])])
    proc(c, "ac-wakeup", [Send("ac-wake"), If("acsleep", [V("acsleep", "0"), V("acfade", "300"), Call("ac-layers"),
                                                           Call("ac-verbsel")])])
    # (a new piece: its own memory, empty)
    proc(c, "ac-newkey", [Call("ac-memclearall"),
                          If("acstopped", [V("acready", "1"), Call("ac-reseed"), Toast("new piece - A# start")],
                             [Call("ac-reseed"), Toast("new piece")])])
    # COMPOSE / DRIFT (aux + A#, SETUP GENERAL): while stopped, the piece is prepared again in that mode, ready;
    # while playing, it switches at once
    proc(c, "ac-modetoggle", [
        V("acmode", "1-acmode"), V("acmodesel", "1-acmode"), Send("ac-dirty"),
        If("acstopped", [V("acready", "1"), SendL("ac-setseed", ["acseed"]),
                         If("acmode", [Toast("COMPOSE - A# start")], [Toast("DRIFT - A# start")])],
           [V("acended", "0"), Send("ac-master", "1 3000"),
            If("acmode==1", [V("acsec", "0"), Call("ac-plan"), Call("ac-section"), Call("ac-change"),
                             Toast("COMPOSE new arc")],
               [Call("ac-section"), Call("ac-change"), Toast("DRIFT endless")])]),
        Call("ac-scr"), Send("ac-led")])
    proc(c, "ac-playgo", [Send(t) for t in ("ac-ctick", "ac-rtick", "ac-btick", "ac-dtick", "ac-ttick", "ac-etick", "ac-bbtick", "ac-sgtick")])
    # the form: an archetype's energy curve over 6-12 sections, then a role for each section
    arch = ARCH_EXPR.replace("X", "((aci+0.5)/acnsec)")
    proc(c, "ac-plan", [
        RNG,
        X("min(12, max(6, int((5 + 25*aclen)/2.6 + acr1*2))); int(acr2*%d); 0.6 + acr3*0.9; 0; 0; 1"
          % len(ARCHETYPES), "v acnsec", "v acarch", "v acpow", "v acpsum", "v acpkv", "v acpk"),
        V("acarch", f"if(acsform > 0 && acsform <= {len(ARCHETYPES)}, acsform - 1, acarch)"),     # SETUP FORM
        Loop("acnsec", "aci", [
            RNG,
            T("acplan", "aci", f"if(aci==0, 0.1+acr2*0.1, if(aci==acnsec-1, 0.2, min(1, max(0.12, 0.12 + 0.85*{arch}"
                               " + (acr1-0.5)*0.16))))"),
            T("acpdur", "aci", "0.7 + acr3*0.6"),
            V("acpsum", "acpsum + acpdur[int(aci)]"),
            If("acplan[int(aci)] > acpkv && aci > 1 && aci < acnsec-1", [V("acpkv", "acplan[int(aci)]"),
                                                                       V("acpk", "aci")]),
        ]),
        V("acrecap", "if(max(acpk+1, int(acnsec*0.72)) <= acnsec-2, max(acpk+1, int(acnsec*0.72)), -1)"),
        Loop("acnsec", "aci", [
            RNG,
            T("acroles", "aci", "if(aci==0, 0, if(aci==acnsec-1, 7, if(aci==acpk, 4, if(aci==acrecap, 6, "
                                "if(aci==1, 1, if(aci>acpk, if(acplan[int(aci)] < acplan[int(aci)-1]-0.15, 5, 2), "
                                "if(acplan[int(aci)] > acplan[int(aci)-1], 3, 2)))))))"),
            T("ackeyp", "aci", "if(acroles[int(aci)]<=1 || acroles[int(aci)]>=6, 0, if(acroles[int(aci)]==4, "
                               "if(acr1<0.5, acaway2, acaway1), if(acroles[int(aci)]==5, if(acr2<0.5, acaway2, 0), "
                               "if(acroles[int(aci)]==2, if(acr3<0.6, acaway1, 0), acaway1))))"),
        ]),
        Call("ac-customapply"), Call("ac-keyplan"),
    ])
    # SETUP PHRASE Key plan: home (no key moves), or each section away from home (not the opening, the return or
    # the end) a 5th or a major 3rd further; auto leaves the piece's own
    away = "(acroles[int(aci)] > 1 && acroles[int(aci)] < 6)"
    proc(c, "ac-keyplan", [If("ackplan > 0", [V("acki", "0"), Loop("acnsec", "aci", [
        V("acki", f"acki + {away}"),
        T("ackeyp", "aci", f"if(ackplan == 1 || {away} == 0, 0, (acki*if(ackplan == 2, 7, 4)) % 12)")])])])
    # SETUP FORM custom: your sections (pages 11-12) replace the generated plan - its roles, energies, lengths
    en = str(ROLE_ENERGY[-1])
    for i in range(len(ROLE_ENERGY) - 2, -1, -1):
        en = f"if(acroles[int(aci)]=={i}, {ROLE_ENERGY[i]}, {en})"
    proc(c, "ac-customapply", [If("acsform == 6", [
        V("acscount", "12"),
        Loop("12", "aci", [If("acsroles[int(aci)] == 8 && acscount == 12", [V("acscount", "max(1, aci)")])]),
        V("acnsec", "acscount"), V("acpsum", "0"),
        Loop("acnsec", "aci", [
            T("acroles", "aci", "if(acsroles[int(aci)] == 8, 2, acsroles[int(aci)])"),
            T("acplan", "aci", en),
            T("acpdur", "aci", f"if(acslens[int(aci)] == 0, {SEC_LENS[0]}, if(acslens[int(aci)] == 1, {SEC_LENS[1]}, {SEC_LENS[2]}))"),
            V("acpsum", "acpsum + acpdur[int(aci)]"),
            T("ackeyp", "aci", "if(acroles[int(aci)]<=1 || acroles[int(aci)]>=6, 0, if(acroles[int(aci)]==5, acaway2, acaway1))"),
        ]),
    ])])
    # the first edit of a section starts from the plan the piece has now
    proc(c, "ac-customcopy", [If("acscount == 0", [
        Loop("12", "aci", [T("acsroles", "aci", "if(aci < acnsec, acroles[int(aci)], 8)"), T("acslens", "aci", "1")]),
        V("acscount", "acnsec")])])
    # a section of the custom form: its layers' states and levels (auto and 100 % otherwise)
    proc(c, "ac-secovr", [V("acsecc", "acsform == 6 && acmode == 1")] + sum(
        [[V("acst", f"acsst[int(acsec)*8 + {i}]"),
          # in at 1/4 .. 3/4: off until that point of the section, then on; out: on, then off
          V(f"acsx{n}", "acsecc*if(acst <= 2, acst, if(acst <= 5, if(acsecq >= acst - 2, 2, 1), "
                        "if(acsecq >= acst - 5, 1, 2)))"), V(f"acsl{n}", f"if(acsecc, acslv[int(acsec)*8 + {i}], 1)")]
         for i, n in enumerate(SEC_LAYERS)], []))
    # FORM shape: applies at once while the piece waits ready (prepared again); custom also to a playing piece
    proc(c, "ac-formset", [If("acsform == 6", [Call("ac-customcopy")]),
                           If("acstopped", [V("acready", "1"), SendL("ac-setseed", ["acseed"])],
                              [If("acsform == 6", [Call("ac-customapply"), Toast("form: custom")],
                                  [Toast("form: next piece")])])])

    # the piece's motif (5 scale degrees, a random walk) and its rhythm
    # (ARC Rhythm shared: the bells' motif rhythm as the motion's pattern - its onsets in 8ths, i.e. twice as fast)
    proc(c, "ac-rcell", [Loop("64", "aci", [T("acrcm", "aci", "0")]), V("acrcs", "0"),
                         Loop("5", "aci", [T("acrcm", "min(63, int(acrcs + 0.5))", "1"), V("acrcs", "acrcs + acmrhy[int(aci)]*2")]),
                         V("acrcn", "min(64, max(4, int(acrcs + 0.5)))")])
    proc(c, "ac-motif0", [Loop("5", "aci", [
        RNG,
        T("acmotif0", "aci", "if(aci==0, int(acr1*3)*2, acmotif0[int(aci)-1] + int(acr1*5) - 2)"),
        T("acmotif", "aci", "acmotif0[int(aci)]"),
        T("acmrhya", "aci", "acrhyt[int(acr2*5)]"),
        T("acmrhy", "aci", "if(acbuser, if(aci == 0, acbru0, if(aci == 1, acbru1, if(aci == 2, acbru2, if(aci == 3, acbru3, acbru4)))), if(acbrsel > 0, acbrhyt[int((acbrsel - 1)*5 + aci)], acmrhya[int(aci)]))"),
    ]), Call("ac-rcell")])
    # each section transforms it by role: inverted (develop), raised and faster (intensify, climax),
    # as it was (establish, return), varied otherwise
    proc(c, "ac-motifgen", [
        RNG, V("acmtr", "2 + 2*int(acr1*2)"),
        Loop("5", "aci", [
            RNG,
            T("acmotif", "aci", "if(acrole==2 && acr1<0.5, -acmotif0[int(aci)], if(acrole==3 || acrole==4, "
                                "acmotif0[int(aci)] + acmtr, if(acrole==6 || acrole<=1, acmotif0[int(aci)], "
                                "acmotif0[int(aci)] + int(acr1*3) - 1)))"),
            T("acmrhya", "aci", "acrhyt[int(acr2*5)] * if(acrole==3 || acrole==4, 0.5, 1)"),
            T("acmrhy", "aci", "if(acbuser, if(aci == 0, acbru0, if(aci == 1, acbru1, if(aci == 2, acbru2, if(aci == 3, acbru3, acbru4)))), if(acbrsel > 0, acbrhyt[int((acbrsel - 1)*5 + aci)], acmrhya[int(aci)]))"),
        ]),
        # SETUP DIALOGUE Motif develops: away from the opening and the return, it is also played backwards, slower
        # (augmented), faster (diminished) or in fragments (its first two notes, sequenced a step up) - the rhythm
        # only when it is the piece's own
        If("(acmdev*acwrite) && acrole != 0 && acrole != 6", [
            RNG, V("acmdvt", "int(acr1*4)"),
            If("acmdvt == 0", [Loop("5", "aci", [T("acmdt", "aci", "acmotif[int(aci)]")]),
                               Loop("5", "aci", [T("acmotif", "aci", "acmdt[4 - int(aci)]")])]),
            If("(acmdvt == 1 || acmdvt == 2) && acbuser == 0 && acbrsel == 0", [Loop("5", "aci", [
                T("acmrhy", "aci", "if(acmdvt == 1, min(4, acmrhy[int(aci)]*2), max(0.25, acmrhy[int(aci)]*0.5))")])]),
            If("acmdvt == 3", [Loop("3", "aci", [T("acmotif", "aci + 2", "acmotif[int(aci) % 2] + int((aci + 2)/2)")])]),
        ]),
        Call("ac-rcell"),
    ])
    # ---- top E (motion) / D# (bells) held + a low key (acrsel 0-11): the rhythm, changed step by step. Yours stays
    #      through the sections (acmuser / acbuser) and is kept in a saved piece; C# gives back the piece's own.
    #      (Random numbers are drawn only by C's randomize, and by ghosts and ratchets while they are on: a piece you
    #      did not touch plays as it always did)
    mtake = [If("acmuser == 0", [X("acmk; acmn; acmrot; 1", "v acmuk", "v acmun", "v acmurot", "v acmuser")])]
    mset = [X("acmuk; acmun; acmurot", "v acmk", "v acmn", "v acmrot")]
    mops = {
        0: mtake + [RNG, V("acmuk", "2 + int(acr1*7)"), V("acmun", "max(acmuk + 1, min(16, 5 + int(acr2*12)))"),
                    V("acmurot", "int(acr3*acmun)")] + mset + [Send("ac-mrhytoast")],
        1: [X("0; -1; 0; 0; 0", "v acmuser", "v acmusw", "v acmghost", "v acmrat", "v acmharm"),
            X("acmpk; acmpn; acmprot; acmpsw", "v acmk", "v acmn", "v acmrot", "v acmswing"), Toast("motion: the piece's own")],
        2: mtake + [V("acmurot", "(acmurot + 1) % acmun")] + mset + [Send("ac-mrhytoast")],
        3: mtake + [V("acmurot", "(acmurot - 1 + acmun) % acmun")] + mset + [Send("ac-mrhytoast")],
        4: mtake + [V("acmuk", "min(acmun, acmuk + 1)")] + mset + [Send("ac-mrhytoast")],
        5: mtake + [V("acmuk", "max(1, acmuk - 1)")] + mset + [Send("ac-mrhytoast")],
        6: mtake + [V("acmun", "min(16, acmun + 1)")] + mset + [Send("ac-mrhytoast")],
        7: mtake + [V("acmun", "max(max(2, acmuk), acmun - 1)"), V("acmurot", "acmurot % acmun")] + mset + [Send("ac-mrhytoast")],
        8: [V("acmharm", "(acmharm + 1) % 4"), Send("ac-mharmtoast")],
        9: [V("acmrat", "if(acmrat < 0.2, 0.25, if(acmrat < 0.4, 0.5, 0))"), Send("ac-mrattoast")],
        10: [V("acmghost", "if(acmghost < 0.2, 0.3, if(acmghost < 0.5, 0.6, 0))"), Send("ac-mghosttoast")],
        11: [V("acmusw", "if(acmusw < 0, 0, if(acmusw < 0.1, 0.15, if(acmusw < 0.2, 0.3, -1)))"),
             V("acmswing", "if(acmusw >= 0, acmusw, acmpsw)"), Send("ac-mswtoast")],
    }
    proc(c, "ac-mop", [If(f"acrsel == {k}", st) for k, st in mops.items()])
    Line("ac-mrhytoast", "list motion $1/$2 rot $3", [("f", "acmk"), ("f", "acmn"), ("f", "acmrot")], "ac-toast")(c)
    Line("ac-mharmtoast", "list motion harmony $1", [("s", "acmharm", ["off", "3rds", "6ths", "triads"])], "ac-toast")(c)
    Line("ac-mrattoast", "list motion ratchets $1%", [("f", "int(acmrat*100)")], "ac-toast")(c)
    Line("ac-mghosttoast", "list motion ghosts $1%", [("f", "int(acmghost*100)")], "ac-toast")(c)
    Line("ac-mswtoast", "list motion swing $1", [("s", "if(acmusw < 0, 0, 1 + int(acmusw*6.67 + 0.5))",
                                                      ["auto", "0%", "15%", "30%"])], "ac-toast")(c)
    # the bells: their 5 step lengths (acbru0-4, from the piece's when first changed)
    btake = [If("acbuser == 0", [X("acmrhy[0]; acmrhy[1]; acmrhy[2]; acmrhy[3]; acmrhy[4]; 1", "v acbru0", "v acbru1",
                                   "v acbru2", "v acbru3", "v acbru4", "v acbuser")])]
    bset = [Loop("5", "aci", [T("acmrhy", "aci", BRU)])]
    rot = lambda order: [X("; ".join(f"acbru{k}" for k in order), *[f"v acbt{k}" for k in range(5)]),
                         X("; ".join(f"acbt{k}" for k in range(5)), *[f"v acbru{k}" for k in range(5)])]
    scale = lambda f: [X("; ".join(f"min(4, max(0.25, acbru{k}*{f}))" for k in range(5)), *[f"v acbru{k}" for k in range(5)])]
    named = [X("; ".join(f"acbrhyt[int((acbrsel - 1)*5 + {k})]" for k in range(5)), *[f"v acbru{k}" for k in range(5)])]
    bops = {
        0: btake + [RNG, X("; ".join(f"acrhyt[int(fmod(acr{1 + k % 4}*{1 + 2.37 * k:.2f}, 1)*5)]" for k in range(5)),
                           *[f"v acbru{k}" for k in range(5)])] + bset + [Toast("bells: random")],
        1: [X("0; 0; 0; 1; 0; 0", "v acbuser", "v acbghost", "v acbrat", "v acbrub", "v acbrsel", "v acbharm"),
            Loop("5", "aci", [T("acmrhy", "aci", "acmrhya[int(aci)]")]), Toast("bells: the piece's own")],
        2: btake + rot([4, 0, 1, 2, 3]) + bset + [Toast("bells: rotate >")],
        3: btake + rot([1, 2, 3, 4, 0]) + bset + [Toast("bells: rotate <")],
        4: btake + scale(0.75) + bset + [Toast("bells: denser")],
        5: btake + scale(1.33) + bset + [Toast("bells: sparser")],
        6: btake + [V("acbrsel", f"acbrsel % {len(BELL_RHYTHMS)} + 1")] + named + bset + [Send("ac-brhytoast")],
        7: btake + [V("acbrsel", f"(acbrsel + {len(BELL_RHYTHMS) - 2} + {len(BELL_RHYTHMS)}) % {len(BELL_RHYTHMS)} + 1")]
           + named + bset + [Send("ac-brhytoast")],
        8: [V("acbharm", "(acbharm + 1) % 4"), Send("ac-bharmtoast")],
        9: [V("acbrat", "if(acbrat < 0.2, 0.25, if(acbrat < 0.4, 0.5, 0))"), Send("ac-brattoast")],
        10: [V("acbghost", "if(acbghost < 0.2, 0.3, if(acbghost < 0.5, 0.6, 0))"), Send("ac-bghosttoast")],
        11: [V("acbrub", "if(acbrub > 0.5 && acbrub < 1.5, 0, if(acbrub < 0.5, 2.5, 1))"), Send("ac-brubtoast")],
    }
    proc(c, "ac-bop", [If(f"acrsel == {k}", st) for k, st in bops.items()] + [Call("ac-rcell")])
    Line("ac-brhytoast", "list bells $1", [("s", "acbrsel", ["auto"] + [n for n, _ in BELL_RHYTHMS])], "ac-toast")(c)
    Line("ac-bharmtoast", "list bells harmony $1", [("s", "acbharm", ["off", "3rds", "6ths", "5ths"])], "ac-toast")(c)
    Line("ac-brattoast", "list bells ratchets $1%", [("f", "int(acbrat*100)")], "ac-toast")(c)
    Line("ac-bghosttoast", "list bells ghosts $1%", [("f", "int(acbghost*100)")], "ac-toast")(c)
    Line("ac-brubtoast", "list bells rubato $1", [("s", "if(acbrub < 0.5, 0, if(acbrub < 1.5, 1, 2))",
                                                       ["strict", "normal", "loose"])], "ac-toast")(c)
    return c


def section():
    c = Canvas("section", w=3600)
    c.comment("A section: its role (from the plan, or chosen when drifting) sets layers, key, tempo, "
              "harmonic pace, motif, rhythm and reverb")
    rest = [
        RNG,
        V("acrole", "if(acmode==1, acroles[int(acsec)], if(acr1<0.25, 1, if(acr1<0.55, 2, "
                    "if(acr1<0.8, 3, 5))))"),
        V("acenergy", "if(acmode==1, acplan[int(acsec)], 0.3 + acr2*0.7)"),
        # (PHRASE Breath, while moving: the opening, the break and the ending stay mostly held - sparse bells and motion)
        V("acsecalm", "(acrests*acwrite) > 0 && (acrole == 0 || acrole == 5 || acrole == 7)"),
        V("acfam", f"if(acchdc > 0, acchdc - 1, if(acrole==6, acfamA, if(acr3<0.55, acfamA, if(acr3<0.88, acfamB, if(fmod(acr4*9.7, 1) < acharmx, int(acr4*{NF}), acplfam[int(acr4*{len(PLEASING_FAMS)})])))))"),
        RNG,
        V("actidef", "acrtide[int(acrole)] * (0.85 + acr1*0.3)"),
        V("acdauto", "if(acrole == 5 && acr2 < 0.6, acdtype2, acdtype)"),
        V("acsecbright", "min(1, max(0.3, 0.55 + 0.45*acenergy + (acr2-0.5)*0.25))"),
    ]
    # (a held section's checks and the last section's timers end here; SETUP's section editor follows "now")
    rest += [Send("ac-secstop"), V("acsecq", "0"), If("acsecfol", [V("acsecsel", "min(11, acsec)")]),
             Call("ac-secovr"), Call("ac-padpick")]
    for i, lay in enumerate(LAYERS):
        extra = {"drone": " || acdens < 0.3", "cloud": " || accapt"}.get(lay, "")
        # (while moving, the bells - the motif's voice - come in at least 4 sections in 5, but the calm ones)
        chance = (f"if(acwrite && acrole != 0 && acrole != 5 && acrole != 7, max(0.8, acrmask[int(acrole)*6+{i}]), "
                  f"acrmask[int(acrole)*6+{i}])" if lay == "bell" else f"acrmask[int(acrole)*6+{i}]")
        rest += [RNG, V("acf" + lay, f"acr1 < {chance}{extra}")]
    rest += [
        RNG,
        X("if(acr1<0.5, actexA, actexB); if(acr2<0.5, actexB, int(acr3*%s))" % TEX_N, "v actex1a", "v actex2a"),
        Call("ac-sndovr"),
        # rhythm of the motion layer: a Euclidean pattern, its rotation, 16ths or 8ths, arpeggio shape
        RNG,
        X(f"int(acr1*{EUCLID_N}); int(acr2*8); 1 + (acr3<0.35); int(acr4*4)", "v acmeia", "v acmrot", "v acmdiv", "v acmarp"),
        V("acmei", "if(acmeisel > 0, acmeisel - 1, acmeia)"),        # (aux + top E + a low key chose one)
        V("acmdiv", f"acmdiv * (1 + (acbpm0 > {HALFTIME}))"),
        X("aceuk[int(acmei)]; aceun[int(acmei)]", "v acmk", "v acmn"),
        RNG,
        X("12*(1 + int(acr1*2)); (0.08 + acr2*0.25)*acrhythm; (acrole==3 || acrole==4) && acr3 < 0.6",
          "v acmoct", "v acmswing", "v acgdlock"),
        # (the piece's own pattern kept; yours - top E held + low keys - over it)
        X("acmk; acmn; acmrot; acmswing", "v acmpk", "v acmpn", "v acmprot", "v acmpsw"),
        If("acmuser", [X("acmuk; acmun; acmurot", "v acmk", "v acmn", "v acmrot")]),
        If("acmusw >= 0", [V("acmswing", "acmusw")]),
        # key plan: move to this section's key area at the next chord change
        If("acmode==1 && ackeyc == 0", [V("acpend", "if(((int(actonic)-36) % 12) != ((int(achome)-36 + int(ackeyp[int(acsec)])) "
                                     "% 12 + 12) % 12, ((int(achome)-36 + int(ackeyp[int(acsec)])) % 12 + 12) % 12, "
                                     "acpend)"), If("acpend >= 0", [Call("ac-chordnext")])]),
        V("acprogi", "0"),
        # tempo and the drone's pulse on the bar
        Call("ac-settempo"),
        Call("ac-pulseupd"),
        # the stereo scene: where the pads live, where bells and motion play, how far the cloud spreads
        RNG,
        V("acscene", "acscrole[int(acrole)*3 + int(acr1*3)]"),
    ] + [SendL(f"ac-v{k}-home", [f"acscn[int(acscene)*10 + {k}]", "6000"]) for k in range(4)] + [
        SendL("ac-cloudspread", ["acscn[int(acscene)*10 + 8]*0.5"]),
        Later("ac-stereo", 11),
        # an atmosphere in some sections of pieces that have one (the break may use the second kind)
        RNG,
        X("acatm && acr1 < acatmrole[int(acrole)]; if(acrole == 5 && acr2 < 0.5, acatmT2, acatmT)", "v acfatm",
          "v acatmcur"),
        V("acatmcur", "if(acsatm > 0, acsatm - 1, acatmcur)"),      # SETUP FORM Atmos
        # reverb: Auto takes the piece's own, and sometimes Shimmer at the climax
        RNG,
        V("acvsec", "if(acrole==4 && acr1 < 0.4, 4, acvauto)"),
        Later("ac-verbsel", 23),
        Send("ac-rvin", "1.8 1500"), Arm("ac-rvback", "3500"),
        V("acsecel", "0"),
        V("acsecdur", "if(acmode==1, (5 + 25*aclen)*60000*acpdur[int(acsec)]/acpsum, "
                      "(1.5 + 6*aclen)*60000*(0.7 + acr4*0.6))"),
        Arm("ac-nextsec", "acsecdur*actime", stop="ac-secstop"),
        V("acfade", "9000*actime + 500"),
        SendL("ac-master", ["0.62 + 0.38*acenergy", "acfade"]),
        Later("ac-layers", 41),
        Later("ac-brightupd", 53),
        Later("ac-motifgen", 67),
        Later("ac-memsec", 79),
        # (ARC Bass pedal: in the section before a return, the drone and sub hold the home key's dominant; the
        # return resolves it - the drone glides home with the key plan)
        X("((acbassm*acwrite) == 1 || (acbassm*acwrite) == 3) && acmode == 1 && acsec + 1 < acnsec && acroles[int(acsec) + 1] == 6; 36 + (int(achome) - 36 + 7) % 12",
          "v acpedal", "v acpedp"),
        If("(acrests*acwrite) > 0", [X("1; 3; 0", "v acrestb", "v acrestl", "v acrestp")]),
        Later("ac-scr", 97),
        Send("ac-led"),
    ]
    # (MEMORY: the section's kept knobs, once its own settings are in)
    proc(c, "ac-section", [If("acmode==1 && acsec>=acnsec", [Call("ac-fin")],
                              rest + [If("acmemon", [Later("ac-memrecall", 30)])])])
    # the pad types of the 4 voices: the piece's palette, or SETUP SOUNDS (raw = the first demos' dry, buzzy types:
    # vox, partials, fold, pulsar; or one type for all four voices)
    steps = []
    for k in range(4):
        steps += [RNG, X(f"if(acspe==0, if(acr1<0.4, acpal1, if(acr1<0.72, acpal2, if(acr1<0.9, acpal3, "
                         f"int(acr2*{FLAV_N})))), if(acspe==1, {RAW_EXPR}, acspe-2))",
                         lambda c, src, k=k: _flav(c, src, k))]
    steps += [SendL("ac-lvtype", ["if(acvtsel >= 0, acvtsel, if(acspe>=2, acspe-2, if(acspe==1, 5, acpal1)))"])]
    # (a custom section's pad type wins over SETUP SOUNDS)
    proc(c, "ac-padpick", [V("acspe", "if(acsform == 6 && acmode == 1 && acssp[int(acsec)] > 0, acssp[int(acsec)], acspad)"),
                           If("acjpad == 0 || acjforce", steps), V("acflstag", "4200")])
    # SETUP SOUNDS overrides on what the section chose (auto = the section's own choice)
    proc(c, "ac-sndovr", [
        V("acdcur", "if(acjdi >= 0, acjdi, if(acsdrone > 0, acsdrone - 1, acdauto))"),
        V("actex1", "if(acstex > 0, acstex - 1, actex1a)"),
        V("actex2", "if(acstex > 0, acstex - 1, actex2a)"),
        V("accheff", "if(acschar > 0, acschar - 1, if(acspad == 1, 0, acchar))"),
    ])
    # while you play (breath, or notes held), a section waits for you, up to 3 times 30 s
    # held (low B): looks again every 2 s, and moves on once released
    proc(c, "ac-nextsec", [If("acsecfz", [Arm("ac-nextsec", "2000", stop="ac-secstop")], [
        If("acmode==1 && acsechold < 3 && (acnow - acbreatht < 4000 || acheld > 0)", [
            V("acsechold", "acsechold + 1"), Arm("ac-nextsec", "30000*actime", stop="ac-secstop"),
            Toast("holding: you play")],
           # (with Phrases, while moving: the section waits for the phrase to close - at most 60 s - and changes
           # near the end of its last chord, after the breath)
           [If("(acphr*acwrite) > 0 && acsecwait == 0 && acrun", [X("1; 1", "v acsecdue", "v acsecwait"),
                                                    Arm("ac-nextsec", "60000*actime", stop="ac-secstop")],
               [X("0; 0; 0", "v acsechold", "v acsecdue", "v acsecwait"), V("acsec", "acsec+1"), Call("ac-section")])])])])
    proc(c, "ac-secgo", [If("acrun", [X("0; 0; 0", "v acsechold", "v acsecdue", "v acsecwait"), V("acsec", "acsec+1"),
                                      Call("ac-section")])])
    proc(c, "ac-rvback", [Send("ac-rvin", "1 5000")])
    # the end of a composition: fade out, then switch the layers off
    # (ac-finarm N: switch the layers off N ms from now; a later one restarts the wait)
    c.ch(c.recv("ac-finarm"), "delay", "s ac-finoff")
    # (SETUP WRITING Ending by phrase: the motion stops first, the bells 9 s later; the pads and drone fade last)
    proc(c, "ac-finbell", [V("acfinb", "1")])
    # (SETUP WRITING Ending by phrase: the chords stop and everything fades over 30 s, but the motion stops first, the
    # bells 9 s later, and the rest plays out under the fade until 20 s; the pads and the drone fade last)
    proc(c, "ac-fin", [If("(acendp*acwrite)", [
        X("1; 0", "v acfinm", "v acfinb"), Send("ac-master", "0 30000"), Send("ac-chgstop"), Send("ac-secstop"),
        Arm("ac-finbell", "9000*actime"), Arm("ac-fin2", "20000*actime")], [
        V("acrun", "0"),
        Send("ac-master", "0 30000"),
        Send("ac-chgstop"), Send("ac-secstop"), Call("ac-clockstop"),
        SendL("ac-finarm", ["30500*actime + 500"]),
        Call("ac-scr"),
    ])])
    proc(c, "ac-fin2", [If("acrun", [
        V("acrun", "0"), Call("ac-clockstop"), SendL("ac-finarm", ["10500*actime + 500"]), Call("ac-scr")])])
    # Start / Stop (A#, or an incoming MIDI Start / Stop when following a clock): Stop fades out over 2.5 s and
    # freezes the piece where it is (section, chord, time left); Start fades back in and goes on from there.
    # After FIN, Start begins a new piece.
    proc(c, "ac-stop", [If("acrun && acended == 0 && acstopped == 0", [
        X("1; 0; max(1000, acsecdur*actime - acsecel)", "v acstopped", "v acrun", "v acsecrem"),
        Send("ac-master", "0 8000"),            # a long fade: the sound and its reverb die away slowly
        Send("ac-chgstop"), Send("ac-secstop"), Call("ac-clockstop"),
        Toast("stopped - A# to start"), Call("ac-scr"), Send("ac-led"), If("aclogon", [Send("ac-logwrite")]),
        Arm("ac-sleep", "12000", stop="ac-wake"),
    ])])
    proc(c, "ac-start", [If("acstopped", [
        If("acready", [Toast("start - playing")], [Toast("playing again")]),
        Call("ac-wakeup"),
        V("acclkcont", "acready == 0"),         # (resuming: MIDI Continue; a piece from its start: Start)
        X("0; 1; 0", "v acstopped", "v acrun", "v acready"),
        SendL("ac-master", ["0.62 + 0.38*acenergy", "2500"]),
        Arm("ac-nextsec", "acsecrem", stop="ac-secstop"),
        Arm("ac-change", "max(2500, 0.5*acchsec*1000*actime)", stop="ac-chgstop"),
        Call("ac-clockstart"), Call("ac-outchord"),
        Call("ac-scr"), Send("ac-led"),
    ])])
    proc(c, "ac-startstop", [If("acprof", [Call("ac-profabort")], [If("acstopped", [Call("ac-start")],
                                [If("acended || acrun == 0", [Call("ac-reseed"), Toast("new piece")],
                                    [Call("ac-stop")])])])])
    proc(c, "ac-finoff", [If("acrun==0", [V("acended", "1"), V("acfade", "2000"), Call("ac-layers"),
                                          Call("ac-scr"), Send("ac-led")])])
    return c


def _flav(c, src, k):
    """a voice's new type: the voices change one after another (voice k after k x acflstag ms), so at most one
    voice crossfades two types at a time (a section change otherwise doubled the pads' CPU for 4 s)"""
    t = c.obj("t f f f")
    c.c(*src, t, 0)
    pp = c.obj("pipe 0")
    c.c(c.to((t, 2), f"expr {k}*acflstag*(acfirst == 0)"), 0, pp, 1)   # a new piece: all at once
    c.c(t, 1, pp, 0)
    c.c(pp, 0, c.obj(f"s ac-v{k}-flav"), 0)
    tw = c.obj("tabwrite acflav")
    ex = c.to(t, f"expr $f1; {k}")
    c.c(ex, 1, tw, 1)
    c.c(ex, 0, tw, 0)


def layers():
    c = Canvas("layers", w=2600)
    c.comment("Layer levels from density (knob x section energy), the section's layers, mutes, input mode")
    th = lambda t: f"min(1, max(0, (acdeff-{t})/0.15))"
    lay = [
        # each layer: acm<layer> 0 = off, 1 = auto (the section and density decide), 2 = on (always, full level)
        ("drone", "(acedrone>0)*(1-acended)*max(max(acfdrone, acedrone==2)*(0.55+0.45*min(1, acdeff*3)), (acroute==2)*0.9)"),
        ("pad", f"(acepad>0)*(1-acended)*max(acfpad*{th(0.06)}, acepad==2)"),
        ("tex", f"(acshed < 2)*(acetex>0)*(1-acended)*max(acftex*{th(0.28)}, acetex==2)"),
        ("cloud", f"(acshed < 1)*(acecloud>0)*(1-acended)*max(max(acfcloud*{th(0.42)}, acecloud==2), max(((acinmode==2) || (acinmode==0)*(acinclass>=1))"
                  f"*min(1, acinput*2)*0.8, (acroute==4)*0.85))"),
        # (while moving, the bells need less density: 0.25 for 0.45 - they carry the motif)
        ("bell", f"(acebell>0)*(1-acended)*max(max(acfbell*{th('if(acwrite, 0.25, 0.45)')}, acebell==2), max((acinmode==4)*min(1, acinput*2), (acroute==3)*0.9))"),
        ("motion", f"(acemotion>0)*(1-acended)*max(acfmotion*{th(0.3)}*min(1, acrhythm*2.5), acemotion==2)"),
    ]
    # the effective state of each layer: your key (off / on) wins; on auto, a custom section's own (SETUP SECTION MIX)
    steps = [V(f"ace{n}", f"if(acm{n} != 1, acm{n}, if(acsx{n} == 1, 0, if(acsx{n} == 2, 2, 1)))") for n in SEC_LAYERS]
    # the MIX knobs as gains (data.level: even dB steps; 50 % = x1)
    # (asleep - stopped, after the fade - every layer is off, so its subpatch stops computing)
    steps += [V(f"acmg{x}", f"({level(f'acmx{x}')})*(1 - acsleep)") for x in "dspbmtca"]
    steps += [V("acdeff", "min(1, 0.45*acswell + if(acmode==1, acenergy*(0.35+1.3*acdens), acdens*(0.8+0.4*acenergy)) + 0.35*acbreath*"
                             "(acbrto == 0 || acbrto == 2))")]
    for name, e in lay:
        steps += [V("acg" + name, e)]
        if name == "drone":
            steps += [SendL("ac-g-drone", ["acmgd*acsldrone*acgdrone*if((acdrsub*acwrite), 0.5, 1)*(acdcur==0)", "acfade"])]
            steps += [SendL(f"ac-g-drone{i}", [f"acmgd*acsldrone*acgdrone*if((acdrsub*acwrite), 0.5, 1)*(acdcur=={i})", "acfade"]) for i in range(1, len(DRONES))]
            # the sub: auto follows the drone; on plays it alone too
            steps += [V("acgsub", "(acesub>0)*(1-acended)*if(acesub==2, 1, acgdrone)"),
                      SendL("ac-g-sub", ["acmgs*acslsub*acgsub", "acfade"])]
        elif name == "bell":    # the engine chosen in SETUP VOICES, or the piece's (auto)
            steps += [SendL(f"ac-g-bel{i}", [f"acmgb*acslbell*acgbell*(if(acjbi >= 0, acjbi, if(acsbell > 0, acsbell - 1, acbela)) == {i})", "acfade"])
                      for i in range(len(STRIKES))]
        elif name == "motion":  # the echoes, and the engine through them
            steps += [SendL("ac-g-motion", ["acgmotion", "acfade"])]
            steps += [SendL(f"ac-g-mot{i}", [f"acmgm*acslmotion*acgmotion*(if(acjmi >= 0, acjmi, if(acsmot > 0, acsmot - 1, acmota)) == {i})", "acfade"])
                      for i in range(len(STRIKES))]
        elif name != "tex":
            mx = {"pad": "acmxp", "cloud": "acmxc"}[name]
            # (SETUP PHRASE Breath: the pads dip while the bells and the motion rest)
            dip = (f"*(1 - 0.7*acrestp)*(1 + (acphpos >= 0)*(0.2*(acphpos == 4*(acphr*acwrite) - 2) - 0.12*(acphpos == 4*(acphr*acwrite) - 1)))"
                   if name == "pad" else "")
            steps += [SendL("ac-g-" + name, [f"acmg{mx[-1]}*acsl{name}*acg{name}{dip}", "acfade"])]
    # the atmosphere: auto = the section's, and off with the textures (as before); on = always
    steps += [V("acgatm", "(acshed < 1)*(aceatm>0)*(1-acended)*if(aceatm==2, 1, acfatm*(acetex>0))*(0.55 + 0.45*min(1, acdeff*2))")]
    steps += [SendL(f"ac-g-atm{i}", [f"acmga*acslatm*acgatm*(acatmcur=={i})", "acfade*1.5"]) for i in range(len(ATMOS_NAMES))]
    # the pad character: SETUP SOUNDS, else none for raw pads, else the piece's
    steps += [V("accheff", "if(acschar > 0, acschar - 1, if(acspad == 1, 0, acchar))")]
    steps += [SendL(f"ac-g-ch{i}", [f"(acshed < 2)*(accheff=={i})*min(1, acchamt*if(acrole==4, 1.3, 1))*min(1, acgpad*4)*(1 - acsleep)", "acfade"])
              for i in range(1, len(CHARACTERS))]
    # (tape, crush and the rotor take the dry pads' place; chorus, ring and dimension add to them)
    steps += [SendL("ac-chdry", ["1 - (acshed < 2)*((accheff==2)*0.9*acchamt + (accheff==4)*0.6*acchamt + (accheff==5)*0.9*acchamt)", "acfade"])]
    for i in range(len(TEXTURES)):
        steps += [V(f"acgt{i}", f"acgtex*((actex1=={i}) || (actex2=={i}))" if i != 15 else
          # (the song's voice also sings the counter-melody: ARC Counter, while the pads play)
          # (and only while the textures are in: their key out silences it too)
          "max(acgtex*((actex1==15) || (actex2==15)), (acctr*acwrite)*(acetex > 0)*0.8*min(1, acgpad*3)*(1 - acended)*(acshed < 2))"),
                  SendL(f"ac-g-tex{i}", [f"acmgt*acsltex*acgt{i}", "acfade"])]
    proc(c, "ac-layers", steps)
    # a MIX knob: the levels follow while it turns - an update 20 ms after the first change, each gliding over 25 ms
    # into the next (a [delay] restarted by every knob message waited for the knob to stop, then jumped; 50 + 60 ms
    # felt laggy)
    proc(c, "ac-mixch", [If("acmxq == 0", [V("acmxq", "1"), Later("ac-mixgo", 20)])])
    proc(c, "ac-mixgo", [V("acmxq", "0"), V("acfade", "25"), Call("ac-layers")])
    d = c.to(c.recv("ac-densch"), "delay 150")
    run_steps(c, (d, 0), [V("acfade", "1500"), Call("ac-layers")])
    c.col()
    proc(c, "ac-brightupd", [
        V("acbright", "min(1, accolor*acsecbright*1.25 + 0.3*acswell + 0.18*acten)"),
        SendL("ac-bright", ["acbright", "4000"]),
        # grains: free, or locked to the beat (rhythmic grain streams in intense sections)
        V("acgdurv", "if(acgdlock, 60000/acbpm/(2 + 2*(acrhythm>0.6)), 70 + 480*(1-acbright)*(0.4+acweird))"),
        SendL("ac-gdur", ["acgdurv"]),
        SendL("ac-resfb", ["0.93 + 0.066*accolor"]),
        SendL("ac-resdamp", ["1200 + 5000*accolor"]),
    ])
    A = "(acinmode==0)"
    proc(c, "ac-inputupd", [
        # the pitch tracker runs only while there is input to hear
        # (the input stage runs at any In above 0; the pitch tracker from 1 %)
        SendL("ac-trk", ["acinput > 0.01"]), SendL("ac-insw", ["acinput > 0"]),
        If("acinput <= 0.01", [X("-1; 0", "v acinp", "v acinclr")]),
        If("acinput <= 0", [X("0; 0", "v acinlvl", "v acinhf")]),
        V("acgres", f"acinput * if(acinmode==1, 1, {A}*if(acinclass==1, if(acavoc, 0.3, 0.8), if(acinclass==2, 0.4, 0)))"),
        V("acgvoc", f"acinput * ((acinmode==6) || (acinmode==7) || {A}*(acinclass==1)*acavoc*(acshed < 3))"),
        SendL("ac-g-voc", ["acgvoc", "1500"]),
        SendL("ac-vcsyn", [f"(acinmode==6) || {A}", "800"]),
        SendL("ac-vcpad", ["acinmode==7", "800"]),
        V("acgbands", f"acinput * ((acinmode==5) || {A}*(acinclass==3))"),
        V("acharm", f"((acinmode==2) || {A}) && acinclass==1 && acinput > 0.05"),
        V("acgdry", "acinput * if(acinmode==4 || acinmode >= 6, 0.15*(acinmode >= 6), if(acinmode==2 || acinmode==5, 0.3, "
                    f"if({A} && acinclass==3, 0.3, 0.6)))"),
        SendL("ac-g-res", ["acgres", "1500"]),
        SendL("ac-g-bands", ["acgbands", "1500"]),
        SendL("ac-g-tape", ["(acinmode==3)*acinput", "1500"]),
        SendL("ac-g-oct", ["(acinmode==8)*acinput", "1500"]), SendL("ac-g-fmt", ["(acinmode==9)*acinput", "1500"]),
        SendL("ac-g-dry", ["acgdry", "300"]),
        SendL("ac-incl", [f"if(accapt, 1, ((acinmode==2) || {A}*(acinclass>=1))*min(1, acinput*3))", "500"]),
        SendL("ac-inclr", [f"1 - if(accapt, 1, ((acinmode==2) || {A}*(acinclass>=1))*min(1, acinput*3))", "500"]),
        SendL("ac-ghost", ["(acinmode==4)*acinput"]),
        V("acfade", "1500"), Later("ac-layers", 7), Later("ac-grains", 17),
    ])
    return c


ROLE_WIDTH = [0.95, 1.05, 1.1, 1.15, 1.25, 1.2, 1.05, 1.1]


def stereo():
    c = Canvas("stereo")
    c.comment("Width (mid/side at the master) by section role x SETUP Width, 0 in mono; pad orbit depth")
    proc(c, "ac-stereo", [
        SendL("ac-split", ["acmono == 2", "300"]),
        SendL("ac-width", [f"(acmono != 1) * acwidth * if(acrole==0, {ROLE_WIDTH[0]}, " +
                           "".join(f"if(acrole=={i}, {w}, " for i, w in enumerate(ROLE_WIDTH[1:], 1)) + "1"
                           + ")" * 8, "3000"]),
        SendL("ac-pandepth", ["acpanmot * 0.5 * (0.5 + acmotion) * acscn[int(acscene)*10 + 9]"]),
    ])
    return c


def verb():
    c = Canvas("verb-ctl", w=2400)
    c.comment("Reverb choice and settings. Verb knob: Auto, Bloom 1, Bloom 2, Hall, Shimmer. Time 1.5-30 s.")
    tsec = "((1.5 + 28.5*pow(acrvtime, 1.5)) * if(acrole==4, 1.5, if(acrole==7, 1.4, 1)) * (1 + 1.5*acblur))"
    proc(c, "ac-verbsel", [
        V("acvtype", "if(acrvtype < 0.2, acvsec, 1 + min(3, int((acrvtype-0.2)/0.2)))"),
        SendL("ac-g-rvb", ["(acvtype==1 || acvtype==2)*(1 - acsleep)", "2500"]),
        SendL("ac-g-rvh", ["(acvtype>=3)*(1 - acsleep)", "2500"]),
        SendL("ac-shim", ["(acvtype==4)*0.3", "3000"]),
        Call("ac-revupd"),
    ])
    from data import SEND_BUS
    # (200 ms glides, but 30 ms while a SENDS knob turns: acsgms)
    # the layers' SHAPE stages (gen_dsp.shaped): tone 0..1 (50 % open: below, a low-pass from 20 kHz down to 300 Hz;
    # above, a high-pass from 5 Hz up to 2 kHz), drive, width (x2)
    from gen_dsp import SHAPE_LAYERS
    # one proc per layer (ac-shpupd-<x>): a SHAPE knob sends only its own layer's values - all of them reach some
    # 700 receivers (each pad type in each voice has its own), a long tick to repeat at every knob step
    for x in SHAPE_LAYERS:
        proc(c, f"ac-shpupd-{x}", [SendL(f"ac-shp-{x}", [f"if(acsh{x}t < 0.5, 300*pow(66.67, acsh{x}t*2), 20000)",
                                                       f"if(acsh{x}t > 0.5, 5*pow(400, acsh{x}t*2 - 1), 5)",
                                                       f"acsh{x}d", f"2*acsh{x}w"])]
             + ([SendL("ac-subt", ["acsubt"])] if x == "s" else [])      # (and the sub's sound: its SHAPE page)
             # (the layer's two sound parameters, knobs 3 and 4 of its SHAPE page: as signals and as values)
             + [SendL(f"ac-prm-{x}{j}", [f"acsh{x}{j}", "80"]) for j in "pq" if x in "dsptac"]
             + [SendL(f"ac-prmc-{x}{j}", [f"acsh{x}{j}"]) for j in "pq" if x in "dsptac"])
    proc(c, "ac-shpupd", [Call(f"ac-shpupd-{x}") for x in SHAPE_LAYERS])
    # (after the defaults: ac-init's other receivers set them, in no set order)
    c.c(c.to(c.recv("ac-init"), "delay 20"), 0, c.obj("s ac-shpupd"), 0)
    proc(c, "ac-sendupd", [SendL("ac-sg-" + n, [level(n), "acsgms"]) for n in SEND_BUS])
    c.c(c.to(c.recv("ac-init"), "t b"), 0, c.obj("s ac-sendupd"), 0)
    proc(c, "ac-revupd", [
        # Bloom: loop gain exp(-4.2*size/T), as Conduit's; damping = the loop low-pass pole (0.5 = the unit)
        V("acbld", f"if(acvfreeze, 1/0.75, exp(-4.2*acrvsize/{tsec})/0.75)"),
        V("acblp", "if(acvfreeze, 0.2, min(0.9, 0.05 + 0.9*(1-acrvtone)*if(acrole==7, 1.15, 1)))"),
        SendL("ac-blk1", ["0.5*acbld*(1-acblp)"]), SendL("ac-blpole", ["acblp"]),
        SendL("ac-blsize", ["acrvsize"]), SendL("ac-blpre", ["if(acvtype==2, 85.33, 0)"]),
    ] + [SendL(f"ac-rg{i}", [f"if(acvfreeze, 1, pow(10, -3*{ms}*acrvsize/(1000*{tsec})))"])
         for i, ms in enumerate(HALL_MS)] + [
        SendL("ac-hdamp", ["1500 + 9000*pow(acrvtone, 1.5)*if(acrole==7, 0.7, 1)"]),
        # (BLUR: toward 90 % wet and a longer tail, the knobs left where they are)
        SendL("ac-rwet", ["0.06 + 0.9*(acrvmix + (0.95 - acrvmix)*acblur)", "400"]),
        SendL("ac-rvfz", ["1 - acvfreeze", "300"]),
    ])
    return c


def rhythm():
    c = Canvas("rhythm", w=3000)
    c.comment("Clock at 24 ticks a beat (MIDI clock rate): steps (16ths), beats, bars. "
              "The motion layer plays a Euclidean pattern over the chord.")
    met = c.obj("metro 40")
    c.c(c.to(c.recv("ac-init"), "delay 50"), 0, met, 0)
    c.c(c.to(c.recv("ac-bpm"), "expr 60000/max(20, $f1)/24"), 0, met, 1)
    c.c(met, 0, c.obj("s ac-mtick"), 0)
    c.c(c.m(c.recv("ac-clockhalt"), "stop"), 0, met, 0)
    c.c(c.recv("ac-clockgo"), 0, met, 0)
    proc(c, "ac-mtick", [If("acsync == 0", [Send("ac-tick")])])
    # the tempo of this section: the piece's place in the tempo range, x the role's tempo
    proc(c, "ac-settempo", [V("acbpm0", TEMPO0), V("acbpm", "acbpm0 * if(acstempo > 0, 1, acrtempo[int(acrole)])"),
                            SendL("ac-bpm", ["acbpm"])])
    c.col()
    proc(c, "ac-tick", shared=True, steps=[
        V("actick", "(actick + 1) % (24*acmeter*64)"),
        If("actick % 6 == 0", [
            V("acstep", "int(actick/6)"), Call("ac-step"),
            If("actick % 24 == 0 && acpump > 0", [Call("ac-pumpbeat")]),
            If("actick % (24*acmeter) == 0", [Call("ac-bar")]),
        ]),
    ])
    proc(c, "ac-ansturn", [If("acansm == 0 && acansmp == 1 && (acmelm*acwrite) == 4 && acvc >= 3",
                              [X("3; int(acvc) % 3", "v acbim", "v acbis")]), V("acansmp", "acansm")])
    # (ARC Bass ground: the sub a 4-note line from the motif's first four degrees, from the home key, one a bar)
    proc(c, "ac-ground", [If("((acbassm*acwrite) >= 2) && acrun", [
        V("acgbi", "(acgbi + 1) % 4"),
        V("acgbp", "(actonic + 12*floor((acmotif0[int(acgbi)])/acn) + acscale[(int(acmotif0[int(acgbi)]) % int(acn) + int(acn)) % int(acn)])"),
        V("acgbp", "acgbp - 12*ceil(max(0, acgbp - 43)/12) + 12*ceil(max(0, 28 - acgbp)/12)"),
        SendL("ac-subp", ["mtof(acgbp)", "250"])])])
    proc(c, "ac-bar", [Call("ac-ground"), SendL("ac-dpulse", [f"60000/{BPMH}*acmeter"]), If("acgdlock && acgcloud > 0", [Send("ac-cloud-on")]),
                       # SETUP DIALOGUE Answer motion: the motion plays 2 bars, then the bells 2
                       If("(acans*acwrite) == 1 && ((acphr*acwrite) > 0) == 0", [V("acbarn", "acbarn + 1"), V("acansm", "int(acbarn/2) % 2 == 0"),
                                                                                 Call("ac-ansturn")]),
                       # SETUP PHRASE Breath: a rest counts down; or one may start (bells, motion, or both with the
                       # pads dipping)
                       If("(acrests*acwrite) > 0", [If("acrestb > 0", [V("acrestb", "acrestb - 1"), If("acrestb == 0 && acrestp", [
                           X("0; 3000", "v acrestp", "v acfade"), Call("ac-layers")])], [
                           If("(acphr*acwrite) == 0", [RNG, If(f"acr1 < {_S._pick('acrests', _S.SBREATH)}", [
                               X("1 + int(acr2*2); int(acr3*3)", "v acrestb", "v acrestl"),
                               If("acrestl == 2", [X("1; 2500", "v acrestp", "v acfade"), Call("ac-layers")])])])])])])
    # (SETUP DIALOGUE Answer motion: the motion's turn; PHRASE Breath: not resting)
    go = ("((acans*acwrite) != 1 || acansm) && ((acrests*acwrite) == 0 || acrestb == 0 || acrestl == 0) && ((acendp*acwrite) == 0 || acfinm == 0)"
          # (a phrase's last chord, and a calm section: every other step)
          " && ((acphpos != 4*(acphr*acwrite) - 1 || acphpos < 0) && acsecalm == 0 || int(acstep/acmdiv) % 2 == 0)")
    proc(c, "ac-step", shared=True, steps=[If(f"acgmotion > 0.01 && acrun && int(acstep) % int(acmdiv) == 0 && {go}", [
        V("acms", "int(acstep/acmdiv)"),
        If("if((acrcell*acwrite) && acmuser == 0, acrcm[int(acms) % int(acrcn)], "
           "((int(acms + acmrot) % int(acmn)) * int(acmk)) % int(acmn) < acmk)", [
            RNG,
            V("acmai", "((int(if(acmarp==0, acmai+1, if(acmarp==1, acmai-1, if(acmarp==2, acr1*4, "
                       "acmai + if(acr1<0.5, 1, -1))))) % 4) + 4) % 4"),
            # SETUP LINES Melody: grow (the arpeggio adds a note each round: 1, 12, 123, 1234, then 1 again) and
            # mutate (an 8-step loop of chord tones - an octave up from 4 - whose steps change by Mutate)
            If("(acmelm*acwrite) == 2", [V("acmgi", "acmgi + 1"), If("acmgi >= acmgn", [X("0; acmgn % 4 + 1", "v acmgi", "v acmgn")]),
                               V("acmai", "acmgi")]),
            If("(acmelm*acwrite) == 3", [RNG, If(f"acr1 < {_S._pick('acmutp', _S.SMUTP)}", [
                T("acmtur", "int(acvc) % 8", "int(acr2*4) + 4*(acr3 < 0.3)")]),
                V("acmai", "acmtur[int(acvc) % 8] % 4")]),
            V("acmp", "acnew[int(acmai)] + acmoct + 12*((acmelm*acwrite) == 3 && acmtur[int(acvc) % 8] >= 4)"),
            # 1/f: three dice, changing every step, every 2nd and every 4th: their sum is a scale degree above the
            # chord's root - mostly small steps, now and then a leap (Voss)
            If("(acmelm*acwrite) == 1", [RNG, X("int(acr1*3); if(int(acvc) % 2 == 0, int(acr2*3), acvd1); "
                                      "if(int(acvc) % 4 == 0, int(acr3*3), acvd2)", "v acvd0", "v acvd1", "v acvd2"),
                               V("acmp", f"{deg2p('acdeg + acvd0 + acvd1 + acvd2')} + acmoct"),
                               V("acmai", "(acvd0 + acvd1 + acvd2) % 4")]),
            # motif: the bells' motif as counterpoint - its intervals, each step against the bells' last direction
            # (contrary motion), kept within -3..9 degrees (turning back at the edges), a chord tone on the pattern's
            # first step; with Answer motion, a 5th up (the answer to the bells' subject)
            If("(acmelm*acwrite) == 4", [
                V("acmdg", "acmdg + if(acbdir != 0, -acbdir*abs(acmotif[(int(acvc) + 1) % 5] - acmotif[int(acvc) % 5]), "
                           "acmotif[(int(acvc) + 1) % 5] - acmotif[int(acvc) % 5])"),
                V("acmdg", "if(acmdg > 9, 18 - acmdg, if(acmdg < -3, -6 - acmdg, acmdg))"),
                V("acmdg", "if(int(acms) % int(acmn) == 0, 2*floor(acmdg/2 + 0.5), acmdg)"),
                # (a step may pass between chord tones; a leap lands on one - an even degree from the root)
                V("acmdg", "if(abs(acmdg - acmdgl) > 1, 2*floor(acmdg/2 + 0.5), acmdg)"),
                V("acmp", f"{deg2p('acdeg + acmdg + 4*((acans*acwrite) == 1)')} + 12 + acmoct"),
                V("acmp", "if(acmp > 100, acmp - 12*ceil((acmp - 100)/12), acmp)"),
                # (no parallel 5ths or octaves: the bells moved, the motion moved, and the same perfect interval
                # again - the motion takes the step above instead)
                If("acbpl != acmbpl && acmp != acmpl && acmivl == ((int(acmp - acbpl) % 12) + 12) % 12 && "
                   "(acmivl == 0 || acmivl == 7)", [
                    V("acmdg", "acmdg + 1"),
                    V("acmp", f"{deg2p('acdeg + acmdg + 4*((acans*acwrite) == 1)')} + 12 + acmoct"),
                    V("acmp", "if(acmp > 100, acmp - 12*ceil((acmp - 100)/12), acmp)")]),
                X("((int(acmp - acbpl) % 12) + 12) % 12; acmp; acbpl; acmdg", "v acmivl", "v acmpl", "v acmbpl", "v acmdgl"),
                # (its last three degrees, for the bells to imitate)
                T("acmimit", "int(acvc) % 3", "acmdg"),
                V("acmai", "(int(acmdg) % 4 + 4) % 4")]),
            If("(acmelm*acwrite) > 0", [V("acvc", "acvc + 1")]),
            V("acmp", "if(acmp>100, acmp-12, acmp)"),
            # SETUP DIALOGUE Register spaced: the motion between 67 and 84
            If("(acreg*acwrite)", [V("acmp", "acmp + 12*ceil(max(0, 67 - acmp)/12) - 12*ceil(max(0, acmp - 84)/12)")]),
            X("if(int(acms) % int(acmn) == 0, 1, 0.5 + acr2*0.3); "
              "(int(acms) % 2 == 1)*acmswing*15000/acbpm*acmdiv + acr3*14*acrhythm; "
              "min(0.97, max(0.03, acscn[int(acscene)*10 + 6] + acscn[int(acscene)*10 + 7]*(acmai/3 - 0.5)"
              " + (acr4 - 0.5)*0.12))", "v acmv", "v acmdl", "v acmpan"),
            SendL("ac-mnote", ["acmp", "acmv*acdyn", "acmdl", "acmpan"]),
            # SETUP DIALOGUE Phasing: the same note again on the other side, later by a delay that grows a little
            # every step, around the whole pattern (then they meet in unison again)
            If("(acphase*acwrite) > 0", [
                V("acpsd", f"fmod(acpsd + {_S._pick('(acphase*acwrite)', _S.SPHASE)}*15000/acbpm*acmdiv, 15000/acbpm*acmdiv*acmn)"),
                SendL("ac-mlater", ["acmp", "acmv*0.75", "acmdl", "1 - acmpan", "acpsd"])]),
            # harmony (top E held + G#): the next chord tones above, in the piece's key and scale
        ] + [If(cond, [V("acmh", f"acmp + ((int(acnew[int((acmai + {k}) % 4)]) - int(acmp)) % 12 + 12) % 12"),
                       V("acmh", "if(acmh == acmp, acmh + 12, acmh)"), V("acmh", "if(acmh > 103, acmh - 12, acmh)"),
                       SendL("ac-mnote", ["acmh", "acmv*0.6", "acmdl", "1 - acmpan"])])
             for k, cond in ((1, "acmharm == 1 || acmharm == 3"), (2, "acmharm == 2 || acmharm == 3"))] + [
            # ratchets: a repeat half a step later
            If("acmrat > 0", [RNG, If("acr1 < acmrat", [
                SendL("ac-mnote", ["acmp", "acmv*0.55", "acmdl + 7500/acbpm*acmdiv", "acmpan"])])]),
        ], [
            # ghost notes: soft notes on the rests
            If("acmghost > 0", [RNG, If("acr1 < acmghost", [
                V("acmh", "acnew[int(acr2*4)] + acmoct"),
                SendL("ac-mnote", ["if(acmh > 100, acmh - 12, acmh)", "0.15 + acr3*0.1", "acr4*14*acrhythm", "acr3"])])]),
        ]),
    ])])
    return c


def change():
    c = Canvas("change", w=3600)
    c.comment("A chord change: maybe modulate (key plan or by chance), move the chord root (or replay the "
              "opening progression in a return section), voice-lead the 4 pad voices, retune everything")
    steps = [
        RNG,
        V("acchsec", "(6 + 84*pow(actide, 2)) * actidef * (0.75+acr3*0.5)"),
        V("acfamc", f"if(fmod(acr4*5.3, 1) < acharmx*0.5, int(fmod(acr4*3.7, 1)*{NF}), acfam)"),
        # the chord was picked at the last change (ac-chordnext), so the screen shows it coming; a piece's first
        # chord is picked now
        If("acfirst", [Call("ac-chordnext")]),
        # a key move asked for since (Root, SETUP Key, the key plan, a note held) wins; while resolved it waits
        # (a chord picked on the CHORD page wins: a key move waits for the change after it)
        V("acxt", "if(acres, actonic, if(acpend >= 0 && acxpick == 0, 36 + acpend, acxt))"),
        X("acxt != actonic; acxt; if(acres || acxpick, acpend, -1); 0", "v acmodflag", "v actonic", "v acpend", "v acxpick"),
        If("acxscf && acfirst==0", [V("acsci", "acxsci"), Call("ac-loadscale")]),
        # (back from a secondary dominant: the chord it led to, in the key)
        V("acdeg", "if((acmodflag && acsdret == 0) || acfirst || acres, 0, int(acxdeg) % int(acn))"),
        V("acprogi", "acprogi + (acrole==6)"),
        # listening: what you hold (or sing) pulls the chord - pick a root whose triad contains it
        If("acfocus >= 0 && acr3 < acfollow && acfirst == 0 && acmodflag == 0 && acres == 0", [
            V("acfd", "-1"),
            Loop("acn", "aci", [If("abs(fmod(actonic + acscale[int(aci)] - acfocus + 1200, 12)) < 0.6 || "
                                   "abs(fmod(actonic + acscale[int(aci)] - acfocus + 1200, 12)) > 11.4",
                                   [V("acfd", "aci")])]),
            If("acfd >= 0", [RNG, V("acdeg", "((int(acfd) - 2*int(acr1*3)) % int(acn) + int(acn)) % int(acn)")]),
        ]),
        # remember the opening progression (for the return)
        If("acmode==1 && acsec <= 1 && acprogn < 8", [T("acprog", "acprogn", "acdeg"), V("acprogn", "acprogn+1")]),
    ]
    for k in range(4):
        steps += [
            V("acD", f"acdeg + acfamt[int(acfamc)*5+{1 + k}]"),
            V("acp0", f"if(acfamt[int(acfamc)*5]==0, {deg2p('acD')} + 12, "
                      f"actonic + 12 + acscale[int(acdeg)] + acfamt[int(acfamc)*5+{1 + k}])"),
            # Resolve: the tonic as open fifths (root, 5th, octave, 12th - pure 5ths, whatever the scale)
            V("acp0", f"if(acres, actonic + 12 + {[0, 7, 12, 19][k]}, acp0)"),
            RNG,
            V("acp1", f"if(acfirst || acfamt[int(acfamc)*5]==1 || acr1>0.7, acp0, "
                      f"acp0 + 12*floor((acch[{k}]-acp0)/12 + 0.5))"),
            V("acp1", "if(acp1<43, acp1+12, if(acp1>86, acp1-12, acp1))"),
            V("acp1", "if(acp1<43, acp1+12, if(acp1>86, acp1-12, acp1))"),
            V("acp1", "if((acreg*acwrite) && acp1 > 76, acp1 - 12, acp1)"),       # (SETUP DIALOGUE Register spaced)
            T("acnew", k, "acp1"),
        ]
    # SETUP PHRASE Voicing smooth: each voice in turn takes the free chord tone nearest to where it is (a common
    # tone stays), in the octave nearest to it
    near = lambda j, k: f"(acnew[int({j})] + 12*floor((acch[{k}] - acnew[int({j})])/12 + 0.5))"
    vl = [Loop("4", "aci", [T("acvu", "aci", "0")])]
    for k in range(4):
        vl += [X("-1; 99", "v acvb", "v acvbd"),
               Loop("4", "aci", [If(f"acvu[int(aci)] == 0 && abs({near('aci', k)} - acch[{k}]) < acvbd", [
                   X(f"aci; abs({near('aci', k)} - acch[{k}])", "v acvb", "v acvbd")])]),
               T("acvu", "acvb", "1"), T("acvl", k, near("acvb", k))]
    vl += [Loop("4", "aci", [T("acnew", "aci", "acvl[int(aci)]"), T("acnew", "aci", "if(acnew[int(aci)] < 43, acnew[int(aci)] + 12, "
                                                                            "if(acnew[int(aci)] > if((acreg*acwrite), 76, 86), acnew[int(aci)] - 12, acnew[int(aci)]))")])]
    steps += [If("(acvlead*acwrite) && acfirst == 0 && acres == 0 && acfamt[int(acfamc)*5] == 0", vl)]
    # SETUP WRITING Pads carry motif: the top voice takes the motif's next note (one a chord) when it is a step or two
    # from its chord tone - a suspension, resolving into the chord halfway through it (the motif, very slowly)
    steps += [V("acsusp", "0"), If("(acpadm*acwrite) && acfirst == 0 && acres == 0", [
        V("acpmi", "(acpmi + 1) % 5"),
        V("acpmp", f"{deg2p('acdeg + acmotif[int(acpmi)]')} + 24"),
        V("acpmp", "acpmp + 12*floor((acnew[3] - acpmp)/12 + 0.5)"),
        V("acsusp", "abs(acpmp - acnew[3]) >= 0.5 && abs(acpmp - acnew[3]) <= 3.5"),
        If("acsusp", [Arm("ac-padres", "acchsec*600*actime", stop="ac-chgstop")])])]
    for k in range(4):
        steps += [RNG,
                  SendL(f"ac-v{k}-pitch", [f"if(acsusp, acpmp, acnew[3])" if k == 3 else f"acnew[{k}]",
                                           # the glide (SETUP Glide scales it; off = the voices jump), and the
                                           # voice's delay (off: all at once)
                                           f"if(acfirst, 0, ({_S.GLIDE_X})*max(1500, (0.25+0.5*acr1)*acchsec*1000*actime))",
                                           "if(acfirst || acglide == 0, 0, acr2*0.35*acchsec*1000*actime)"]),
                  T("acch", k, f"acnew[{k}]")]
        steps += [SendL(f"ac-res{k}", [f"1000/mtof(43 + fmod(acnew[{k}]-43, 24))", "2500"])]
    # the chord's name now, and the next chord picked and named (the screen shows both)
    steps += [V("acchgt", "acnow"), X("actonic; acdeg; acres", "v acqt", "v acqd", "v acqr"), Call("ac-chordname"),
              V("acchn", "acqn"), V("acsdnow", "acsdg >= 0"),
              # (Phrases, while moving: the sounding chord's place in its phrase - the section waits for the last;
              # Answer motion: the bells call in the phrase's first half, the motion answers in the second; the
              # pads swell into the phrase's V and settle on its last chord)
              V("acphpos", "if((acphr*acwrite) > 0, acphc, -1)"),
              # (ARC: the phrase's arc - towards its V louder (dynamics) and brighter, more adventurous (tension);
              # on the cadence's I softer and relaxed)
              X("if(((acarc*acwrite) == 1 || (acarc*acwrite) == 3) && acphpos >= 0, if(acphpos <= 4*(acphr*acwrite) - 2, 0.72 + 0.28*acphpos/max(1, 4*(acphr*acwrite) - 2), 0.7), 1); "
                "if(((acarc*acwrite) >= 2) && acphpos >= 0, if(acphpos <= 4*(acphr*acwrite) - 2, acphpos/max(1, 4*(acphr*acwrite) - 2), 0), 0)", "v acdyn", "v acten"),
              If("((acarc*acwrite) >= 2)", [Call("ac-brightupd")]),
              If("(acphr*acwrite) > 0", [
                  If("acsecdue && acphpos == 4*(acphr*acwrite) - 1", [V("acsecdue", "0"), Arm("ac-secgo", "acchsec*900*actime", stop="ac-secstop")]),
                  If("(acans*acwrite) == 1", [V("acansm", "acphpos >= 2*(acphr*acwrite) || acphpos < 0"), Call("ac-ansturn")]),
                  V("acfade", "acchsec*400*actime"), Call("ac-layers")]),
              If("acbrq", [V("acbrq", "0"), Arm("ac-breathgo", "acchsec*500*actime", stop="ac-chgstop")]),
              Call("ac-chordnext")]
    steps += [Later("ac-grains", 13), Later("ac-change2", 29, stop="ac-chgstop")]
    # the next chord: a key move (pending root, or by chance in DRIFT), a chance scale change, the next degree
    # (or the opening progression in a return section); then its name for the screen.
    proc(c, "ac-chordnext", [
        RNG,
        V("acxt", "if(acres, actonic, if(acpend>=0, 36 + acpend, if(acmode==0 && ackeyc == 0 && acr1 < 0.03 + acweird*0.15 && acfirst==0, "
                  "36 + ((int(actonic) - 36 + int(if(fmod(acr2*5.9, 1) < acharmx, acmods[int(acr2*12)], acmodp[int(acr2*12)]))) % 12 + 12) % 12, actonic)))"),
        V("acxscf", "acr3 < acweird*0.12*acharmx && acfirst==0 && acsclc == 0"),
        RNG, V("acxsci", f"int(acr4*if(acnewt, {NS}, {SCALE_AUTO}))"),
        RNG,
        V("acxdeg", "if(acxt != actonic || acfirst || acres, 0, if(acrole==6 && acprogi < acprogn, acprog[int(acprogi)], "
                    "if(acr1 < 0.1 + 0.15*(1-acweird) && acdeg != 0, 0, "
                    "((int(acdeg) + int(if(fmod(acr2*17.3, 1) < min(1, acharmx + 0.35*acten), acmoves[int(acr2*12)], acmovp[int(acr2*12)]))) % int(acn) + int(acn)) % int(acn))))"),
        # after a secondary dominant: the chord it leads to, back in the key; otherwise SETUP PHRASE and HARMONY
        If("acsdg >= 0", [X("acsdt; 1; acsds; acsdg; 1; -1", "v acxt", "v acxscf", "v acxsci", "v acxdeg", "v acsdret",
                            "v acsdg")], [V("acsdret", "0"), Call("ac-chordplan")]),
        Call("ac-chordshow"),
    ])
    # (only while the next chord stays in the key and nothing chose it: a key move, Resolve, the CHORD page - and
    # the key moves not with a fixed key or scale)
    ok = "acxt == actonic && acfirst == 0 && acres == 0 && acpend < 0 && acxpick == 0 && ackeyc == 0 && acsclc == 0"
    # What the scale offers: its V and IV (its degrees at 7 and 5 semitones, -1 if it has none) and whether it is
    # near 12-tone (pelog, harm7, slendro are not). A feature the scale can't carry steps aside: phrases need a V
    # (a missing IV leaves that chord the piece's own); the key moves and secondary dominants (to ionian, aeolian,
    # mixolydian) a 12-tone scale with a V - and secondary dominants 7 notes or more
    # Phrases: 4 or 8 chords, in pairs: the first ends open (IV, V), the second closed (V, I). A key move starts
    # a new phrase.
    cad = "acphc >= 4*(acphr*acwrite) - 2 && acphd >= 0"
    proc(c, "ac-chordplan", [
        If("(acphr*acwrite) > 0 || (acmovm*acwrite) > 0 || (acsecd*acwrite) > 0", [
            X("-1; -1; 1", "v acphd", "v acphs", "v acsfit"),
            Loop("acn", "aci", [If("abs(acscale[int(aci)] - 7) < 0.3", [V("acphd", "aci")]),
                                If("abs(acscale[int(aci)] - 5) < 0.6", [V("acphs", "aci")]),
                                If("abs(acscale[int(aci)] - int(acscale[int(aci)] + 0.5)) > 0.2", [V("acsfit", "0")])])]),
        If("(acphr*acwrite) > 0", [If("acxt == actonic && acfirst == 0 && acres == 0 && acpend < 0 && acxpick == 0", [
            V("acphc", "(acphc + 1) % (4*(acphr*acwrite))"),
            If(cad, [
                V("acxdeg", "if(acphc == 4*(acphr*acwrite) - 1, if(acphn % 2, 0, acphd), if(acphn % 2, acphd, if(acphs >= 0, acphs, acxdeg)))"),
                # (a closed phrase's V borrows the leading tone - aeolian from harmonic minor, dorian from melodic
                # minor, mixolydian from ionian, lydian dominant from lydian - and its I takes the scale back)
                If("acphc == 4*(acphr*acwrite) - 2 && acphn % 2 == 1 && acsclc == 0 && acphrs == 0", [V("acltx", "if(acsci == 2, 17, if(acsci == 1, 13, if(acsci == 3, 4, if(acsci == 12, 0, -1))))"), If("acltx >= 0", [
                    X("acsci; 1; 1; acltx", "v acphsc", "v acphrs", "v acxscf", "v acxsci")])]),
                If("acphc == 4*(acphr*acwrite) - 1 && acphrs", [X("0; 1; acphsc", "v acphrs", "v acxscf", "v acxsci")]),
                If("acphc == 4*(acphr*acwrite) - 1 && acphn % 2 == 1", [V("acbrq", "1")]),
                If("acphc == 4*(acphr*acwrite) - 1", [V("acphn", "acphn + 1")])])],
            [V("acphc", "-1")])]),
        # key moves of the piece's own: a chromatic mediant (the major or minor key a 3rd away, the chord keeping
        # its kind) or a tonnetz step (P: the parallel; R: the relative; L: the leading-tone exchange - major turns
        # minor and back). The new key's tonic chord comes, in ionian or aeolian
        If(f"(acmovm*acwrite) > 0 && acsfit && acphd >= 0 && ({ok}) && ((acphr*acwrite) == 0 || ({cad}) == 0)", [RNG, If(f"acr1 < if(achmvp == 3, if(acrole == 3 || acrole == 4, 0.4, if(acrole == 1 || acrole == 2, 0.05, 0)), {_S._pick('achmvp', _S.SMOVP)})", [
            X("int(acchn/6); acchn % 6; if((acmovm*acwrite) == 3, 1 + int(acr2*2), (acmovm*acwrite))", "v acmvr", "v acmvq", "v acmvo"),
            If("acmvq <= 1", [
                If("acmvo == 1", [V("acmvo", "if(acr3 < 0.25, 3, if(acr3 < 0.5, 4, if(acr3 < 0.75, 8, 9)))")],
                   [X("if(acr3 < 0.34, 0, if(acr3 < 0.67, if(acmvq, 3, 9), if(acmvq, 8, 4))); 1 - acmvq", "v acmvo", "v acmvq")]),
                X("36 + (int(acmvr) + int(acmvo)) % 12; 1; if(acmvq, 2, 4); 0", "v acxt", "v acxscf", "v acxsci", "v acxdeg"),
            ])])]),
        # secondary dominants: before a chord (not the tonic) its own V comes, a major chord a 5th above it (its
        # key's mixolydian), the drone staying on the key
        If(f"(acsecd*acwrite) > 0 && acsfit && acphd >= 0 && ({ok}) && acxdeg != 0 && acn >= 7 && ((acphr*acwrite) == 0 || ({cad}) == 0)", [
            RNG, If(f"acr1 < {_S._pick('(acsecd*acwrite)', _S.SSECD)}", [
                X("actonic; acsci; acxdeg", "v acsdt", "v acsds", "v acsdg"),
                X("36 + (int(actonic) - 36 + int(acscale[int(acsdg)] + 0.5) + 7) % 12; 1; 3; 0", "v acxt", "v acxscf",
                  "v acxsci", "v acxdeg")])]),
    ])
    # the next chord's name, on the play screen (and the CHORD page, low A held, picks it: gen_setup)
    proc(c, "ac-chordshow", [X("acxt; acxdeg; acres", "v acqt", "v acqd", "v acqr"), Call("ac-chordname"),
                             V("acnxn", "acqn"), Send("ac-scr2")])
    # a chord's name (an index into CHORD_NAMES): its root, and its 3rd and 5th found in the scale
    proc(c, "ac-chordname", [
        X("0; 0; 0; 0; 0", "v acq3", "v acq4", "v acq6", "v acq7", "v acq8"),
        Loop("acn", "aci", [
            V("acqi", "fmod(acscale[int(aci)] - acscale[int(acqd)] + 1200, 12)"),
            X("acq3 || abs(acqi - 3) < 0.5; acq4 || abs(acqi - 4) < 0.5; acq6 || abs(acqi - 6) < 0.5; "
              "acq7 || abs(acqi - 7) < 0.5; acq8 || abs(acqi - 8) < 0.5", "v acq3", "v acq4", "v acq6", "v acq7", "v acq8"),
        ]),
        V("acqn", f"int(fmod(acqt + acscale[int(acqd)] + 0.5, 12))*{len(CHORD_SUFFIXES)} + "
                  "if(acqr, 5, if(acq4, if(acq7 == 0 && acq8, 3, 0), if(acq3, if(acq7 == 0 && acq6, 2, 1), 4)))"),
    ])
    # Notes to chords: while you hold notes, they are the chord (the composer waits)
    proc(c, "ac-change", [If("acrun && (acroute != 1 || acheld == 0)", steps,
                             [If("acrun", [Arm("ac-change", "3000", stop="ac-chgstop")])])])
    steps = [V("acsubx", "if(acssub > 0, acssub - 1, acsubm)")]
    steps += [SendL(f"ac-band{k}", [f"mtof(min(120, acnew[{k % 4}] + {12 * (k // 4) + 12}))", "3000"]) for k in range(8)]
    steps += [
        # (Notes to drone: the drone stays on your note while you hold it)
        If("acroute != 2 || acheld == 0", [
            # (under a secondary dominant the drone and the sub's pedal stay on the key's tonic)
            # (ARC Bass pedal: before a return, the home key's dominant; ground: the sub plays its own line, by bar)
            SendL("ac-dronep", ["if(acpedal, acpedp, if(acsdnow, acsdt, actonic))", "if(acfirst, 0, if(acmodflag || acpedal, 9000, 200))"]),
            If("((acbassm*acwrite) >= 2) == 0", [SendL("ac-subp", ["mtof(if(acpedal, acpedp - 12, if(acsubx==0 || (acsubx==2 && int(acsec) % 2 == 0), if(acsdnow, acsdt, actonic) - 12, "
                              "acnew[0] - 12*ceil((acnew[0] - 42)/12))))", "if(acfirst, 0, if(acmodflag, 9000, 1800))"])])]),
        SendL("ac-ringf", ["mtof(acnew[1] + 12)", "3000"]),
        SendL("ac-radio", ["mtof(min(115, acnew[2] + 36))", "4000"]),
    ] + [SendL(f"ac-atmf{k}", [f"mtof(min(112, acnew[{k % 4}] + {24 + 12 * (k // 4)}))", "6000"]) for k in range(6)] + [
        SendL("ac-atmc0", ["1000/mtof(40 + fmod(acnew[0] - 40, 12))", "5000"]),
        SendL("ac-atmc1", ["1000/mtof(40 + fmod(acnew[0] - 40 + 7, 12))", "5000"]),
    ] + [SendL(f"ac-atmn{k}", [f"mtof(min(119, acnew[{k % 4}] + {48 + 12 * (k % 2)}))", "3000"]) for k in range(6)] + [
    ] + [SendL(f"ac-voccar{k}", [f"mtof(acnew[{k}])", "600"]) for k in range(4)] + [
        RNG,
        SendL("ac-dharm", ["2 + int(acr1*5)", "6000"]),
        SendL("ac-wind", ["mtof(acnew[1]+24)", "mtof(acnew[3]+12)", "5000"]),
        # crickets: a chord tone moved up by octaves into 3-6 kHz; the harp's strings: chord tones below 600 Hz
        SendL("ac-cric", ["mtof(acnew[2]) * pow(2, ceil(log(3000/mtof(acnew[2]))/log(2)))", "3000"]),
    ] + [SendL(f"ac-harp{k}", [f"1000/(mtof(acnew[{k}]) / pow(2, max(0, ceil(log(mtof(acnew[{k}])/600)/log(2)))))",
                               "1500"]) for k in range(3)] + [
        X("acchg + 1; 0", "v acchg", "v acfirst"),
        Arm("ac-change", "acchsec*1000*actime", stop="ac-chgstop"),
        Later("ac-scr2", 37), Later("ac-scr3", 43), Send("ac-flash"), Call("ac-outchord"),
    ]
    proc(c, "ac-change2", [If("acrun", steps)])
    proc(c, "ac-padres", [If("acrun", [SendL("ac-v3-pitch", ["acnew[3]", "acchsec*250*actime", "0"])])])
    # a closed phrase's last chord: halfway into it, the bells and the motion breathe (1 bar, or 2), the pads hold
    proc(c, "ac-breathgo", [If("(acrests*acwrite) > 0 && acrun", [X("1 + ((acrests*acwrite) == 2); 3", "v acrestb", "v acrestl")])])
    gs = []
    for i in range(4):
        gs += [RNG, SendL(f"ac-gr{i}", [f"if(acharm && acinp > 0, pow(2, (acnew[{i}] + 12*floor((acinp - acnew[{i}])/12 + 0.5)"
                                        f" - acinp)/12), acgrt[int(acr1*12)] * if(acr2 < acweird*0.3, -1, 1))"])]
    # Notes to cloud: held notes tune the grain streams (the chord's ratios come back when you let go)
    proc(c, "ac-grains", [If("acroute != 4 || acheld == 0", gs)])
    proc(c, "ac-pulseupd", [SendL("ac-pulse", ["min(0.9, acrpulse[int(acrole)] * (0.3 + 1.4*acrhythm) * " + _S.PULSE_X + ")"])])
    return c


def players():
    c = Canvas("players", w=2400)
    c.comment("Event players: bell motif, rain drops, creature chirps, input onsets")
    bellp = f"{deg2p('acdeg + acmotif[int(acbi)]')} + 24"
    hoff = "if(acbharm == 1, 2, if(acbharm == 2, 5, 4))"     # harmony: a 3rd, a 6th or a 5th up the scale
    # (SETUP DIALOGUE Answer you: the bells answer what you play (or sing) with the piece's motif - as it develops,
    # with its rhythm, harmony and canon - moved by octaves near your last note, while you play and after, fading
    # out 4-12 s after your last note; Register spaced: 84-103)
    play = [V("acbp", bellp), If("(acans*acwrite) == 2", [V("acbp", "acbp + 12*floor((acant + 12 - acbp)/12 + 0.5)")]),
            # (Answer motion, motif melody: the bells' turn opens with the motion's last three notes, imitated)
            If("acbim > 0", [V("acbp", f"{deg2p('acdeg + acmimit[int(acbis + 3 - acbim) % 3]')} + 24"),
                             V("acbim", "acbim - 1")]),
            V("acbp", "if(acbp<67, acbp+12, if(acbp>96, acbp-12, acbp))"),
            If("(acreg*acwrite)", [V("acbp", "acbp + 12*ceil(max(0, 84 - acbp)/12) - 12*ceil(max(0, acbp - 103)/12)")]),
            # (Answer you: full for 4 s after your last note, then fading out over 8 s)
            X("(0.35+0.65*acr2)*if((acans*acwrite) == 2, min(1, max(0, (12000 - (acnow - acanst))/8000)), 1); min(0.97, max(0.03, acscn[int(acscene)*10 + 4] + acscn[int(acscene)*10 + 5]*(acr3 - 0.5)))",
              "v acbv", "v acbpan"),
            SendL("ac-bell", ["acbp", "acbv*acdyn", "acbpan"]),
            X("(acbp > acbpl) - (acbp < acbpl); acbp; acnow", "v acbdir", "v acbpl", "v acblt"),
            # SETUP LINES Canon: the note again an octave, a scale's 5th or two octaves up, later, on the other side
            If("(accanon*acwrite) == 4", [SendL("ac-mlater", ["acbp - 12", "acbv*0.6", "0", "1 - acbpan",
                                                    f"60000/{BPMH}*if(accand == 3, acmeter, {_S._pick('accand', _S.SCAND)})"])]),
            If("(accanon*acwrite) > 0 && (accanon*acwrite) < 4", [
                # (the 5th: four degrees up in a 7-note scale; in another scale, the octave)
                V("accp", f"if((accanon*acwrite) == 2 && acn == 7, {deg2p('acdeg + acmotif[int(acbi)] + 4')} + 24 + 12*floor((acbp + 7 - "
                          f"({deg2p('acdeg + acmotif[int(acbi)] + 4')} + 24))/12 + 0.5), acbp + 12*(accanon*acwrite) - 12*((accanon*acwrite) >= 2))"),
                V("accp", "accp - 12*ceil(max(0, accp - 108)/12)"),
                SendL("ac-blater", ["accp", "acbv*0.55", "1 - acbpan",
                                    f"60000/{BPMH}*if(accand == 3, acmeter, {_S._pick('accand', _S.SCAND)})"])]),
            If("acbharm > 0", [V("acbh", f"{deg2p(f'acdeg + acmotif[int(acbi)] + {hoff}')} + 24"),
                               V("acbh", "acbp + ((int(acbh) - int(acbp)) % 12 + 12) % 12"),
                               V("acbh", "if(acbh == acbp, acbh + 12, acbh)"),
                               SendL("ac-bell", ["acbh", "acbv*0.6", "1 - acbpan"])]),
            If("acbrat > 0", [RNG, If("acr1 < acbrat", [Arm("ac-bratch", "110 + acr2*70", stop="ac-playstop")])])]
    # a note snapped to the key: the scale tone nearest it
    proc(c, "ac-yquant", [X("0; 99", "v acyqd", "v acyqb"), Loop("acn", "acyj", [
        If("abs(fmod(acyq - actonic - acscale[int(acyj)] + 1206, 12) - 6) < acyqb", [
            X("abs(fmod(acyq - actonic - acscale[int(acyj)] + 1206, 12) - 6); fmod(acyq - actonic - acscale[int(acyj)] + 1206, 12) - 6",
              "v acyqb", "v acyqd")])]), V("acyq", "acyq - acyqd")])
    # Answer you: once you have been quiet 0.8 s, the bells echo your phrase - its notes in the key, an octave up,
    # in its own rhythm, side to side - then go on with the motif near your last note
    proc(c, "ac-yecho", [If("(acans*acwrite) == 2 && acrun && (acmbell > 0)", [Loop("acyon", "aci", [
        V("acyq", "acyou[int(aci)]"), Call("ac-yquant"),
        V("acyq", "acyq + 12 + 12*(acyq < 55)"), V("acyq", "if(acyq<67, acyq+12, if(acyq>96, acyq-12, acyq))"),
        If("(acreg*acwrite)", [V("acyq", "acyq + 12*ceil(max(0, 84 - acyq)/12) - 12*ceil(max(0, acyq - 103)/12)")]),
        SendL("ac-blater", ["acyq", "0.55", "0.3 + 0.4*(int(aci) % 2)", "acyout[int(aci)]"])])]), V("acyon", "0")])
    proc(c, "ac-bratch", [If("acrun", [SendL("ac-bell", ["acbp", "acbv*0.5", "acbpan"])])])
    proc(c, "ac-bghost", [If("acgbell > 0.01 && acrun", [
        RNG, V("acbgp", f"{deg2p('acdeg + acmotif[int(acr1*5)]')} + 24"),
        V("acbgp", "if(acbgp<67, acbgp+12, if(acbgp>96, acbgp-12, acbgp))"),
        If("(acreg*acwrite)", [V("acbgp", "acbgp + 12*ceil(max(0, 84 - acbgp)/12) - 12*ceil(max(0, acbgp - 103)/12)")]),
        SendL("ac-bell", ["acbgp", "0.12 + acr2*0.1", "acr3"])])])
    proc(c, "ac-btick", [
        If("acgbell > 0.01 && acrun && (acroute != 3 || acnow - aclnt > 8000)", [
            RNG,
            # (SETUP DIALOGUE Answer: the bells' turn, or after you play; PHRASE Breath: not resting)
            # (a calm section: the bells play less than half as often)
            # (bells you bring in with their key - acebell 2 - play through a calm section and both halves of a
            # phrase: you asked for them; a calm section otherwise keeps about 2 in 3 of them)
            If("acr1 > 0.18 && (acsecalm == 0 || acr1 > 0.45 || acebell == 2) && ((acans*acwrite) == 0 || ((acans*acwrite) == 1 && (acansm == 0 || acebell == 2)) || ((acans*acwrite) == 2 && acnow - acanst > 300 && "
               "acnow - acanst < 12000)) && ((acrests*acwrite) == 0 || acrestb == 0 || acrestl == 1) && ((acendp*acwrite) == 0 || acfinb == 0)", play),
            V("acbi", "(acbi+1) % 5"),
            If("acbi==0 && acr3<0.6", [RNG, T("acmotif", "int(acr1*5)", "acmotif[int(acr1*5)] + int(acr2*5) - 2")]),
        ]),
        RNG,
        # (rubato: top D# held + B - 0 strict, 1 as always, 2.5 loose)
        V("acbint", f"(60000/{BPMH}) * acmrhy[int(acbi)] * (1 + int(acr4*3)) * (1.6 - 0.7*acdeff) * (1 + (acr1 - 0.5)*0.2*acbrub)"),
        Arm("ac-btick", "acbint", stop="ac-playstop"),
        # ghost notes: a soft one between the strikes
        If("acbghost > 0 && acgbell > 0.01 && acrun", [RNG, If("acr1 < acbghost", [Arm("ac-bghost", "acbint*0.5",
                                                                                      stop="ac-playstop")])]),
    ])
    proc(c, "ac-bellnow", [If("acmbell && acrun", [RNG] + play + [V("acbi", "(acbi+1) % 5")])])
    proc(c, "ac-rtick", [
        RNG,
        If("acgt0 > 0.01", [V("acdropi", "(acdropi+1) % 3")]),     # (rain is all signal now: no drop events)
        RNG,
        Arm("ac-rtick", "(90 + 2200*(1-acdeff)) * (0.15 + 1.7*acr4)", stop="ac-playstop"),
    ])
    proc(c, "ac-ctick", [
        If("acgt3 > 0.01", [
            If("acbc > 0", [
                RNG,
                SendL("ac-chirp", ["mtof(min(110, acch[int(acr1*4)] + 36))", "0.55+acr2*0.9", "40+acr3*130", "acr4"]),
                V("acbc", "acbc - 1"),
            ], [RNG, V("acbc", "2 + int(acr1*5)")]),
        ]),
        RNG,
        Arm("ac-ctick", "if(acbc>0, 80 + acr2*240, 1500 + acr3*9000)", stop="ac-playstop"),
    ])
    # echoes texture: an alien blip on a chord tone now and then, into its wobbling ping-pong echoes
    proc(c, "ac-etick", [
        RNG,
        If("acgt8 > 0.01", [SendL("ac-echo", ["mtof(min(100, acch[int(acr1*4)] + 24 + 12*int(acr2*2)))", "acr3"])]),
        Arm("ac-etick", "(1800 + acr4*5000) * (1.4 - 0.6*acdeff)", stop="ac-playstop"),
    ])
    # bubbles: bursts of drops on chord tones (higher = shorter), three voices in turn. (These two players draw
    # random numbers only while their texture sounds: drawing them always moved every later choice of a piece, so
    # a seed - or a saved piece - no longer played what it did)
    proc(c, "ac-bbtick", [If("acgt12 > 0.01", [
        If("acbbn > 0", [
            RNG, V("acbbv", "(acbbv + 1) % 3"),
            SendL("ac-bub", ["acbbv", "mtof(min(108, acch[int(acr1*4)] + 24 + 12*int(acr2*2)))", "25 + acr3*90",
                             "0.15 + acr4*0.35", "fmod(acr1*7.3, 1)"]),
            V("acbbn", "acbbn - 1")], [RNG, V("acbbn", "2 + int(acr1*8)")]),
        RNG,
        Arm("ac-bbtick", "if(acbbn > 0, 40 + acr2*180, (800 + acr3*4000) * (1.4 - 0.6*acdeff))", stop="ac-playstop")],
        [Arm("ac-bbtick", "1500", stop="ac-playstop")])])
    # song: phrases of 2-5 notes on chord tones, each gliding from the last, then a rest
    # (ARC Counter song: while the song texture itself is not chosen, its voice sings the motif - twice as slow, a
    # rest of a bar after each round - a distant third voice)
    proc(c, "ac-sgtick", [If("(acctr*acwrite) && actex1 != 15 && actex2 != 15 && acgt15 > 0.01", [
        If("acsgi < 5", [
            V("acsgr", f"60000/{BPMH}*acmrhy[int(acsgi)]*2"),
            SendL("ac-song", [f"mtof((actonic + 12*floor((acdeg + acmotif[int(acsgi)])/acn) + acscale[(int(acdeg + acmotif[int(acsgi)]) % int(acn) + int(acn)) % int(acn)]) + 24)", "400", "acsgr"]),
            V("acsgi", "acsgi + 1"), Arm("ac-sgtick", "acsgr", stop="ac-playstop")],
           [V("acsgi", "0"), Arm("ac-sgtick", f"60000/{BPMH}*acmeter", stop="ac-playstop")])], [Call("ac-sgtick0")])])
    proc(c, "ac-sgtick0", [If("acgt15 > 0.01", [
        If("acsgn > 0", [
            RNG, V("acsgd", "900 + acr4*2200"),
            SendL("ac-song", ["mtof(acch[int(acr1*4)] + 12*int(acr2*2))", "150 + acr3*700", "acsgd"]),
            V("acsgn", "acsgn - 1")], [RNG, X("2 + int(acr1*4); 0", "v acsgn", "v acsgd")]),
        RNG,
        Arm("ac-sgtick", "if(acsgn > 0, if(acsgd > 0, acsgd*0.92, 300), (2500 + acr3*7000) * (1.4 - 0.6*acdeff))",
            stop="ac-playstop")],
        [Arm("ac-sgtick", "1500", stop="ac-playstop")])])
    # ghost input mode: a played onset rings the next bell note
    # data texture: bursts of blips on chord tones
    proc(c, "ac-ttick", [RNG, If("acgatm > 0.01 && acatmcur == 1 && acr1 < 0.4", [Send("ac-thunder")]),
                         Arm("ac-ttick", "9000 + acr2*20000", stop="ac-playstop")])
    proc(c, "ac-dtick", [
        If("acgt5 > 0.01", [If("acdb > 0", [
            RNG, SendL("ac-data", ["min(110, acnew[int(acr1*4)] + 36 + 12*int(acr2*2))", "25 + acr3*50"]),
            V("acdb", "acdb - 1")], [RNG, V("acdb", "4 + int(acr1*10)")])]),
        RNG,
        Arm("ac-dtick", "if(acdb > 0, 45 + acr2*80, 1200 + acr3*6000)", stop="ac-playstop"),
    ])
    # input onsets: counted for the class; in ghost mode (and for plucked sounds in auto) they ring a bell
    # Answer you: your notes recorded (up to 6; after 3 s of quiet a new phrase starts), for the bells to echo
    proc(c, "ac-yrec", [If("acnow - acanst > 3000 || acyon == 0", [X("0; acnow", "v acyon", "v acyt0")]),
                        If("acyon < 6 && acyrn > 0", [T("acyou", "acyon", "acyrn"), T("acyout", "acyon", "acnow - acyt0"),
                                                      V("acyon", "acyon + 1")]),
                        Arm("ac-yecho", "800", stop="ac-playstop")])
    proc(c, "ac-inonset", [Call("ac-inonset2"),
                           If("(acans*acwrite) == 2", [V("acyrn", "acinp"), Call("ac-yrec"), X("acnow; if(acinp > 0, acinp, acant)", "v acanst", "v acant")]),
                           If("(acinmode==4 || (acinmode==0 && acinclass==2)) && acinput > 0.05",
                              [Call("ac-bellnow"), RNG, If("acr1 < 0.08 && acinmode==4", [Call("ac-change")])])])
    return c


def later():
    c = Canvas("later")
    c.comment("Notes played later: the bells' canon (ac-blater: pitch, velocity, pan, delay) and the motion's "
              "phasing voice (ac-mlater: pitch, velocity, delay, pan, then the delay). Stop clears them.")
    for r, n, s in (("ac-blater", 3, "ac-bell"), ("ac-mlater", 4, "ac-mnote")):
        pp = c.to(c.recv(r), "pipe " + " ".join(["0"] * (n + 1)))     # (its last argument: the delay)
        c.c(c.m(c.recv("ac-playstop"), "clear"), 0, pp, 0)
        pk = c.obj("pack " + " ".join(["f"] * n))
        for i in range(n):
            c.c(pp, i, pk, i)
        c.c(pk, 0, c.obj("s " + s), 0)
        c.col()
    return c


def capture():
    c = Canvas("capture")
    c.comment("Capture: 8 s of the input into the cloud buffer, then freeze it there")
    proc(c, "ac-capture", [
        X("1; 0; 1", "v accapt", "v acfreeze", "v acfcloud"),
        Call("ac-freezeupd"), Call("ac-inputupd"), Send("ac-cwstart"), Call("ac-memrec"),
        Toast("capturing 8 s"),
        Arm("ac-capdone", "8100"),
    ])
    proc(c, "ac-capdone", [X("0; 1", "v accapt", "v acfreeze"), Call("ac-freezeupd"), Call("ac-inputupd"),
                           Toast("captured - frozen")])
    return c
