"""SETUP (hold aux 1 s, or aux + a low key for that page): 29 pages of 4 rows, each row set by its knob.

Where things are:
  the choices of each row        constants below (SPADS, SFORMS, SMORPH ...), next to a comment naming the page
  the pages and their rows       setup_pages() - page by page, the text and what fills it
  what turning a knob does       setup() - the handler, one If(at("PAGE", row), ...) per row
  settings.txt                   SETTINGS (the order on the line) and settings() (load and save)
  a saved piece's fields         SAVE_SCALARS, SAVE_ARRAYS, SAVE_EXTRA (saves and loads: gen_saves)
  CC MAP targets                 TARGETS (what a CC can do; gen_live.cc_map acts on them)
Also the CPU guard (cpu_guard()), whose setting and readout are on the CPU page."""
import re
from pdlib import Sub, Canvas, proc, X, V, T, Send, Call, SendL, If, Loop, run_steps, Chunks, Line, Toast, Later
from gen_oled import Fill, FLIP, gated_text
from data import ENGINE_PARAMS, PAD_PARAMS, MIXED_PARAMS, DRONE_PARAMS, SUB_PARAMS, TEX_PARAMS, ATMOS_PARAMS, CLOUD_PARAMS
from data import FACTORY, PAGES, TEMPOS, FILE_KNOBS, SEND_KNOBS, MIX_KNOBS, SUBMODES, ARCHETYPES, ATMOS_NAMES, ROLES, STRIKES, FLAVOURS, DRONES, TEXTURES, CHARACTERS, SCALES, FAMILIES, NOTE_NAMES, CHORD_NAMES, INMODES, SUBTYPES

GLOBALS = dict(acmout=1, acsync=0, acvintage=0, acoutch=1, accurve=1.2, acsk=0, acsv=0, acextbpm=60,
               acrtb=0, acoutroot=-1, acclkon=0, acclkcont=0, actrange=0,
               acmparts=0, acarpoct=48, acoutbass=-1, acload=0, acloadtest=0, acshedt=0, acldraw=0, acguard=1,
               ackeyc=0, acsclc=0, acchdc=0, acpulc=2, acroute=0, acbrto=0, acpressto=1, acccsel=0, aclastcc=0, aclastv=0, acvibr=5.5,
               acmap0=2, acmap1=1, acmap2=1, acmap3=1, acmap4=6, acmap5=0, acmap6=3, acsbell=0, acsmot=0, acglide=5, acmodesel=0, acssub=0, acsform=0, acstempo=0, acsmeter=0, acsatm=0, acnsx=0, acchx=0, acslot=0, acslotfull=0, acsvp49=1, acsvp50=1, acsvpp=1, acsetpgl=-1, acmixcc=0, acpgm=0, aclfd=1, acsfd=2,
               acmorph=0, acrecall=0, acancg=2, accmp=0, acpump=0, acpumpd=0.5, acduck=0, acduckr=2, acmcsel=0, acmcn=0, acmcin=0,
               acmc0mode=0, acmc0ta=0, acmc0da=0.75, acmc0tb=0, acmc0db=0.75, acmc0v=0, acmc0p=0, acmc1mode=0, acmc1ta=0, acmc1da=0.75, acmc1tb=0, acmc1db=0.75, acmc1v=0, acmc1p=0, acmc2mode=0, acmc2ta=0, acmc2da=0.75, acmc2tb=0, acmc2db=0.75, acmc2v=0, acmc2p=0, acmc3mode=0, acmc3ta=0, acmc3da=0.75, acmc3tb=0, acmc3db=0.75, acmc3v=0, acmc3p=0,
               acsname=0, acstonic=-1, acsscale=0, acspark=0, acsparko=1, acslnm=0, acslkey=-1, acslsc=0, acjour=0, acjpad=0, acjdrone=0, acjstrike=0, acrvpre=0, acrvera=3, acccout=0, acccch=1, acccbase=0, acccrate=1, acchpick=1, acxk=-2, acchsurp=1, acmemon=0, acmemg=2, acsvpm3=1, acsvpm4=1, acmsi=0, acmemk=0,
               acauxlong=0, acscrk=0,
               achints=1, acscope=0, acscopeg=2, acledm=0, achk=-1, acmirk=0, acledin=0, aclbavg=0, aclbnew=0, aclbon=0,
               acmelm=4, acmutp=1, accanon=0, accand=1, acmovm=0, achmvp=1, acsecd=1, acnewt=0,
               acphr=1, acvlead=1, ackplan=0, acrests=1, acmdev=1, acans=1, acphase=0, acreg=1,
               acwrite=1, acpadm=1, acdrsub=1, acendp=1, acpln=0.3, acplv=1, acplm=1, acplp=1, acdrd=0, acdrs=1, acsud=0, acsus=1, acrcell=1, acarc=3, acbassm=1, acctr=1,
               acshbp=0.5, acshbq=0.5, acshmp=0.5, acshmq=0.5,
               **{f"acsh{x}{j}": 0.5 for x in "dsptac" for j in "pq"})
ARRAYS = dict(acout=4, acarp=4)
NP = len(PAGES)
KNOBS = [n for p in PAGES for _, n, _ in p]
SETTINGS = KNOBS[:FILE_KNOBS] + ["acmout", "acsync", "acforce", "acvintage", "acfollow", "acnbr",
                                                  "acoutch", "accurve", "acmono", "acwidth", "acpanmot",
                                                  "actrange", "acmparts", "acarpoct", "acguard"] + KNOBS[FILE_KNOBS:SEND_KNOBS] + \
           ["acspad", "acsdrone", "acstex", "acschar"] + \
           ["ackeyc", "acsclc", "acchdc", "acpulc", "acroute", "acbrto", "acpressto", "acvibr"] + \
           [f"acmap{j}" for j in range(7)] + ["acsbell", "acsmot", "acglide"] + KNOBS[SEND_KNOBS:MIX_KNOBS] + ["acmodesel", "acssub", "acsform", "acstempo", "acsmeter", "acsatm"] + \
           ["acmixcc", "acpgm", "aclfd", "acsfd"] + KNOBS[MIX_KNOBS:] + \
           ["acmorph", "acrecall", "acancg", "acpump", "acpumpd", "acduck", "acduckr"] + \
           [f"acmc{m}{f}" for m in range(4) for f in ("mode", "ta", "da", "tb", "db")] + \
           ["acjour", "acjpad", "acjdrone", "acjstrike", "acrvpre", "acrvera", "acccout", "acccch", "acccbase", "acccrate"] + \
           ["acspark", "acsparko", "acchpick"] + \
           ["achints", "acscope", "acscopeg", "acledm"] + \
           ["acmelm", "acmutp", "accanon", "accand", "acmovm", "achmvp", "acsecd", "acnewt",     # (LINES, HARMONY,
            "acphr", "acvlead", "ackplan", "acrests", "acmdev", "acans", "acphase", "acreg",    # PHRASE, DIALOGUE,
            "acwrite", "acpadm", "acdrsub", "acendp",                                         # WRITING,
            "acrcell", "acarc", "acbassm", "acctr",                                           # ARC,
            "acshbp", "acshbq", "acshmp", "acshmq"] + \
           [f"acsh{x}{j}" for x in "dsptac" for j in "pq"] + \
           ["acpln", "acplv", "acplm", "acplp"] + \
           ["acdrd", "acdrs", "acsud", "acsus"]                     # (PAD LINES, DRIFT)
# (append new settings here, at the end)
IN_IDX = [n for p in PAGES for _, n, _ in p].index("acinput")     # the In knob's slot in acparams
MOUT = ["off", "tempo only", "tempo+note", "notes only"]
PARTS = ["all", "harmony", "arp only"]
# SETUP CPU, CPU guard: on or off, and with the performance log (logs/, see gen_log) or without
SGUARD = ["off", "on", "off + log", "on + log"]
OUTPUTS = ["stereo wide", "mono", "split"]   # split: pads + drone left, everything else right (mono stems)
# the SETUP pages in seven groups (aux + a white low key: the group's first page - C D E F G A B; aux held and knob
# 1 turned: any page, back and forth; an aux tap: the next page). The header: the group, the page, its place in it
SETUP_GROUPS = [("PIECE", ["GENERAL", "MUSIC", "FORM", "SECTIONS", "SECTION MIX"]),
                ("WRITING", ["WRITING", "LINES", "PAD LINES", "HARMONY", "PHRASE", "DIALOGUE", "ARC"]),
                ("SOUND", ["SOUNDS", "VOICES", "COLOUR", "DRIFT", "JOURNEY"]),
                ("LIVE", ["PLAYING", "LIVE", "GROOVE", "MACRO A", "MACRO B"]),
                ("SAVES", ["SAVES", "RECALL", "MEMORY"]),
                ("MIDI", ["MIDI IN", "CC MAP", "NOTES OUT", "CC OUT"]),
                ("SYSTEM", ["OUTPUT", "DISPLAY", "CPU"])]
SETUP_NAMES = [p for _, ps in SETUP_GROUPS for p in ps]
GROUP_KEYS = [0, 2, 4, 5, 7, 9, 11]           # (the white low keys, a group each)
GROUP_START = [SETUP_NAMES.index(ps[0]) for _, ps in SETUP_GROUPS]
DATA_TABLES = dict(acsgrp=[g for g, (_, ps) in enumerate(SETUP_GROUPS) for _ in ps],
                   acspos=[i + 1 for _, ps in SETUP_GROUPS for i in range(len(ps))],
                   acscnt=[len(ps) for _, ps in SETUP_GROUPS for _ in ps])
NSET = len(SETUP_NAMES)                    # SETUP pages
# SETUP DISPLAY: hints (a held key's toast, 0.25 s in, says what holding it does), the scope (the play
# view's middle shows the output, left against right) and its gain, the LED (the piece's state, or pulsing with the
# drone's beating). Settings, not saved with a piece.
# SETUP pages 24-28, LINES, HARMONY, PHRASE, DIALOGUE, WRITING: how the piece writes - one motif carried between
# the bells, the motion and (held, slowly) the pads, in phrases that close and breathe. Saved with the piece. WRITING
# Writing still turns all of it off at once (the static, droning piece; the choices kept for moving again).
# Random numbers are drawn only while a feature is on.
# LINES: the motion's melody (arp: the chord tones as before; 1/f: a melody whose steps are mostly small, now and
# then large - three dice changing at 1, 2 and 4 steps; grow: the arpeggio adds a note each round, 1, 12, 123, 1234;
# mutate: an 8-step loop of chord tones whose notes change now and then, by Mutate), and the bells' canon (each
# bell note echoed an octave, a 5th or two octaves up, later by Canon delay, on the other side)
# (motif: the bells' motif as counterpoint - its intervals, against the bells' direction (contrary motion), a chord
# tone on the bar's first step; with Answer motion, a 5th up: the answer to the bells' subject)
SMELM = ["arp", "1/f", "grow", "mutate", "motif"]
SMUTP = [("locked", 0), ("10%", 0.1), ("25%", 0.25), ("50%", 0.5)]
SCANON = ["off", "8va", "5th", "15ma", "motion"]      # (motion: the motion answers each bell, an octave down)
SCAND = [("1/2 beat", 0.5), ("1 beat", 1), ("2 beats", 2), ("1 bar", 0)]
# HARMONY: key moves the piece makes on its own between chords: mediants (to the major or minor key a 3rd away,
# the chord keeping its kind), tonnetz (P, L, R: the chord's 3rd or 5th moves a step, major turns minor), both;
# how often; secondary dominants (a chord's own V, major, just before it); New types: a piece's own picks also take
# the types added later (pads, textures, drones, rhythms, scales) - off, a piece picks only the original ones
SMOVM = ["in key", "mediants", "tonnetz", "both"]
# (by form: where the form wants tension - often while intensifying and at the climax, now and then while
# establishing and developing, never in the return)
SMOVP = [("rare", 0.1), ("some", 0.25), ("often", 0.5), ("by form", 0)]
SSECD = [("off", 0), ("some", 0.25), ("often", 0.5)]
# PHRASE: phrases of 4 or 8 chords in pairs, the first ending open (IV then V), the second closed (V then I); the
# pad voices take the nearest chord tone (common tones held) instead of one each; the key plan of a COMPOSE piece
# (auto: the piece's own; home: no key moves; fifths, thirds: each section away from home a 5th or a major 3rd
# further); breath: the bells and the motion rest a bar as a section starts, and now and then for 1-2 bars (bells,
# motion, or both with the pads dipping)
SPHR = ["off", "4 chords", "8 chords"]
SVLEAD = ["as before", "smooth"]
SKPLAN = ["auto", "home", "fifths", "thirds"]
SBREATH = [("off", 0), ("some", 0.05), ("often", 0.12)]
# DIALOGUE: the motif develops (each section also plays it backwards, slower, faster or in fragments); answer
# (motion: the motion and the bells take 2 bars each in turn; you: the bells answer what you play, with the
# motif, near your note, and keep answering after you stop, fading out over 12 s); phasing (a second motion voice, on the other side, slowly drifts later, a step every 50 or 16 steps); the
# register (spaced: the pads below 77, the motion 67-84, the bells 84-103)
SMDEV = ["fixed", "develops"]
SANS = ["off", "motion", "you"]
SPHASE = [("off", 0), ("slow", 0.02), ("faster", 0.06)]
SREG = ["as before", "spaced"]
# WRITING: still (none of LINES .. DIALOGUE: the piece as it was - static, droning) or moving; the pads carry the
# motif (their top voice takes a motif note as a suspension when it is a step from the chord, resolving halfway); the
# drone subtle (-6 dB) while moving; the ending by phrase (the motion stops, then the bells, the pads and the drone
# fading last)
SWRITE = ["still", "moving"]
SPADM = ["chords", "motif"]
SDRSUB = ["full", "subtle"]
SENDP = ["fade", "by phrase"]
# ARC: the rhythm shared (the motion's hits on the bells' motif rhythm, twice as fast - your rhythm keys
# still win); the phrase's arc (dynamics: the bells and motion louder towards its V, softer at the cadence;
# tension: brighter and more adventurous towards its V, relaxing on the I); the bass (pedal: before a return the
# drone and sub hold its dominant, resolving home with it; ground: the sub a 4-note line from the motif, bar by bar,
# under the changing chords); the counter-melody (the distant song voice sings the motif slowly - a third voice)
SRCELL = ["own", "shared"]
SARC = ["off", "dynamics", "tension", "both"]
SBASSM = ["off", "pedal", "ground", "both"]
SCTR = ["off", "song"]
SSCOPEG = [("x1", 1), ("x2", 2), ("x4", 4), ("x8", 8), ("x16", 16)]
SLEDM = ["state", "beat"]
# SETUP MEMORY: with Memory on, the knobs you turn in a section are kept for it (acsnapt / acsnapv, a
# value per section and knob); when that section comes again they glide back over Glide. Saved with the piece.
SMEMG = [("cut", 0), ("2 s", 2000), ("5 s", 5000), ("10 s", 10000), ("20 s", 20000)]
NSNAP = 12                                  # sections remembered (a DRIFT piece's sections take them in turn)
# quick pages, past SETUP's (aux taps do not reach them; aux leaves them): CHORD (low A held) and one page for
# each layer (aux + its top key): its sound, in / out / auto, its level and its reverb send
LAYER_PAGES = [("DRONE", "acmdrone", "acsdrone", "acmxd", "acsndd"), ("SUB", "acmsub", "acssub", "acmxs", None),
               ("PADS", "acmpad", "acspad", "acmxp", "acsndp"), ("BELLS", "acmbell", "acsbell", "acmxb", "acsndb"),
               ("MOTION", "acmmotion", "acsmot", "acmxm", "acsndm"), ("TEXTURES", "acmtex", "acstex", "acmxt", "acsndt"),
               ("ATMOSPHERE", "acmatm", "acsatm", "acmxa", "acsnda"), ("CLOUD", "acmcloud", None, "acmxc", "acsndc")]
QUICK_NAMES = ["CHORD"] + [n for n, *_ in LAYER_PAGES] + ["INPUT"]
CHORD_PAGE = NSET                          # (acsetpg)
LAYER_PAGE0 = NSET + 1                     # + the layer (gen_ui.LAYER_KEYS order)
SHAPE_X = "dspbmtac"                       # each layer's letter (its SHAPE values acsh<x>t/d/w), LAYER_KEYS order
INPUT_PAGE = LAYER_PAGE0 + len(LAYER_PAGES)  # (top G# held)
SHAPE_PAGE0 = INPUT_PAGE + 1               # + the layer: its SHAPE page (the layer key held)
# the bells' and the motion's SHAPE pages: knobs 3 and 4 are their engine's parameters (data.ENGINE_PARAMS), named
# by the engine that plays (a journey's, your choice, or the piece's)
# (and every other layer whose sounds have their own: the index of the sound playing, and the names - knob 3, knob 4)
SOUND_X = {"b": ("if(acjbi >= 0, acjbi, if(acsbell > 0, acsbell - 1, acbela))", [ENGINE_PARAMS[k] for k in STRIKES]),
           "m": ("if(acjmi >= 0, acjmi, if(acsmot > 0, acsmot - 1, acmota))", [ENGINE_PARAMS[k] for k in STRIKES]),
           # (the pads: one type for all four voices - SETUP SOUNDS - or else a mix, named in general)
           "p": ("if(acspad >= 2, acspad - 1, 0)", [MIXED_PARAMS] + [PAD_PARAMS[k] for k in FLAVOURS]),
           "d": ("acdcur", [DRONE_PARAMS[k] for k in DRONES]),
           "s": ("acsubt", [SUB_PARAMS[k] for k in SUBTYPES]),
           # (the textures: two may sound - the first one's names; both answer in their own ways)
           "t": ("if(acstex > 0, acstex - 1, actex1)", [TEX_PARAMS[k] for k in TEXTURES]),
           "a": ("acatmcur", [ATMOS_PARAMS[k] for k in ATMOS_NAMES]),
           "c": ("0", [CLOUD_PARAMS])}
ENGINE_X = SOUND_X
QUICK_NAMES += [n + " SHAPE" for n, *_ in LAYER_PAGES]
# GLIDE (low F held): the glide times you set while playing, together - the same values as their SETUP rows (VOICES
# Glide, RECALL Morph and Anchor glide, MEMORY Glide); nothing new is saved
GLIDE_PAGE = SHAPE_PAGE0 + len(LAYER_PAGES)
QUICK_NAMES += ["GLIDE"]
# hold pages (a knob-page key held 0.5 s): a SETUP page as a quick page - its rows, and its knobs do what they do
# there; aux leaves. (SETUP page, the low key: D, D#, E)
# (and how the piece writes: low C WRITING, C# PHRASE, F# DIALOGUE, G# HARMONY)
MIRRORS = [("COLOUR", 2), ("GROOVE", 3), ("FORM", 4), ("WRITING", 0), ("PHRASE", 1), ("DIALOGUE", 6), ("HARMONY", 8)]
MIRROR0 = GLIDE_PAGE + 1
QUICK_NAMES += [n for n, _ in MIRRORS]
NALL = NSET + len(QUICK_NAMES)
# the SETUP page whose rows and knobs a page shows (a mirror shows its SETUP page's)
SETPG_OF = ("if(acsetpg >= %d, " % MIRROR0 + "".join(f"if(acsetpg == {MIRROR0 + j}, {SETUP_NAMES.index(n)}, "
                                                    for j, (n, _) in enumerate(MIRRORS)) + "0" + ")" * len(MIRRORS)
            + ", acsetpg)")
SCHPICK = ["next change", "now"]
SPLAYQ = ["out", "auto", "in"]             # a layer's state: 0 out, 1 auto (the piece decides), 2 in
# a saved slot's name: a word, or auto (its key and scale, kept when it was saved)
NAME_WORDS = ["auto", "Dawn", "Ember", "Tide", "Glass", "Frost", "Drift", "Hollow", "Mist", "Lantern", "Harbor", "Orbit",
              "Moss", "Signal", "Velvet", "Ash", "Bloom", "Night", "River", "Static", "Halo", "Cinder", "Prism", "Dune",
              "Echo", "Still", "Aurora", "Rain", "Slate", "Thaw", "Lumen", "Ochre"]
# GLINT (SETUP COLOUR): sparse FM sparkles high over the chord tones while the drone or pads sound
SSPARKO = ["+1 oct", "+2 oct", "+3 oct"]
# SETUP SOUNDS: auto = the piece chooses; otherwise your choice, at once (to audition) and for every section
SPADS = ["auto", "raw"] + FLAVOURS
SDRONES = ["auto"] + DRONES
STEXS = ["auto"] + TEXTURES
SCHARS = ["auto"] + CHARACTERS
# SETUP MUSIC: a fixed key or scale stays (no modulation); the pulse is the drone and sub swell on the bar
SKEYS = ["auto"] + NOTE_NAMES
SSCALES = ["auto"] + [n for n, _ in SCALES]
SCHORDS = ["auto"] + [n for n, _, _ in FAMILIES]
PULSES = ["off", "gentle", "normal", "strong"]
PULSE_X = "if(acpulc == 0, 0, if(acpulc == 1, 0.45, if(acpulc == 2, 1, 1.6)))"
# SETUP MIDI IN: notes (MIDI in and the Organelle keys) play the live voice, or set the chord, the drone,
# strike the bells, or tune the cloud; breath shapes the live voice and the density, or one thing of the piece
ROUTES = ["voice", "chords", "drone", "bells", "cloud"]
BRTOS = ["voice+piece", "voice", "density", "brightness", "reverb", "swell"]
# SETUP CC MAP: what each CC (and channel / poly pressure, on MIDI IN) does. breath = the breath path (Breath
# to); the voice targets act per note on the CC's channel (MPE; channel 1 = every voice); the piece targets move
# the knob of that name
CCS = [1, 2, 7, 11, 64, 71, 74]
CC_DEFAULTS = [2, 1, 1, 1, 6, 0, 3]          # mod = vibrato, 2 / 7 / 11 = breath, 64 = hold, 71 off, 74 = voice tone
TARGETS = ["off", "breath", "vibrato", "voice tone", "voice level", "voice type", "hold", "density", "colour",
           "reverb", "swell", "motion", "resolve", "root", "next section", "chord now", "glide",
           "anchor", "compare", "macro 1", "macro 2", "macro 3", "macro 4", "journey step", "sink", "blur",
           "swell all", "harm", "sparkle", "writing"]
TARGET_KNOB = {7: "acdens", 8: "accolor", 9: "acrvmix", 11: "acmotion",       # piece targets: the knob they move
               24: "acsink", 25: "acblur", 26: "acswell", 27: "acharmx"}
CCSEL = "if(acccsel == 0, 1, " + ", ".join(f"if(acccsel == {j}, {n}" for j, n in enumerate(CCS) if j) + ", 0" + ")" * 7
MAPSEL = "if(acccsel == 0, acmap0, " + ", ".join(f"if(acccsel == {j}, acmap{j}" for j in range(1, 7)) + ", 0" + ")" * 7
BENDS = [12, 24, 48, 96]
# SETUP VOICES: the engine of the bells and of the motion (auto = the piece's)
SBELLS = ["auto"] + STRIKES
SMOTS = ["auto"] + STRIKES
# how the pad voices move to a new chord: off = they jump; slow = the full glide (25-75 % of the time between
# changes, at least 1.5 s); the steps between scale that glide
GLIDES = ["off", "fast", "short", "medium", "long", "slow"]
# the sub (VOICES row 4): auto = the piece's mode
SSUBS = ["auto"] + SUBMODES
# SETUP FORM: the form's shape (custom = your sections, SECTIONS), a fixed tempo, the meter, the atmosphere
SFORMS = ["auto"] + ARCHETYPES + ["custom"]
STEMPOS = ["auto"] + [f"{t} bpm" for t in (40, 48, 56, 64, 72, 80, 90, 100, 110, 120, 140)]
SMETERS = ["auto"] + [f"{m} beats" for m in (3, 4, 5, 6, 7)]
SATMS = ["auto"] + ATMOS_NAMES
# SETUP pages 11-12, SECTIONS and SECTION MIX: the custom form, section by section (a role of "end" ends the
# piece there); each section's length, pad type, and each layer's play state and level
SROLES = ROLES + ["end"]
SLENS = ["short", "normal", "long"]
SEC_LAYER_NAMES = ["drone", "sub", "pads", "bells", "motion", "textures", "atmos", "cloud"]
SPLAY = ["auto", "off", "on", "in 1/4", "in 1/2", "in 3/4", "out 1/4", "out 1/2", "out 3/4"]
# SETUP LIVE: a bank of 16 CCs (8 layer levels, then 8 layer in/out buttons), program change loads a
# save slot, the fade of a layer key (or button), the swell of a layer coming in or going out within a section
SMIXCC = ["off", "CC 20-35", "CC 102-117"]
MIXCC_BASE = "if(acmixcc == 1, 20, 102)"
SPGM = ["off", "load slot"]
SLFADE = [("0.5 s", 500), ("2.5 s", 2500), ("5 s", 5000), ("10 s", 10000), ("20 s", 20000)]
SSFADE = [("2 s", 2000), ("5 s", 5000), ("10 s", 10000), ("20 s", 20000), ("40 s", 40000)]


def _pick(var, table):
    e = str(table[-1][1])
    for i in range(len(table) - 2, -1, -1):
        e = f"if({var} == {i}, {table[i][1]}, {e})"
    return e


LFADE = _pick("aclfd", SLFADE)


def msel(f):
    """the selected macro's field (SETUP MACRO pages): acmc<m><f>"""
    return "if(acmcsel == 0, acmc0" + f + ", if(acmcsel == 1, acmc1" + f + ", if(acmcsel == 2, acmc2" + f + ", acmc3" + f + ")))"
SFADE = _pick("acsfd", SSFADE)
# SETUP SAVES: 16 slots in saves.txt, each the seed and everything that shapes the piece
NSLOTS = 16
SAVE_SCALARS = ["acseed", "acmodesel"] + [n for p in PAGES[:7] for _, n, _ in p if n != "acinput"] + \
    ["acspad", "acsdrone", "acstex", "acschar", "ackeyc", "acsclc", "acchdc", "acpulc", "acsbell", "acsmot", "acglide",
     "acssub", "acsform", "acstempo", "acsmeter", "acsatm", "acscount"] + \
    ["acm" + n for n in ("drone", "sub", "pad", "bell", "motion", "tex", "atm", "cloud")]
SAVE_ARRAYS = [("acsroles", 12), ("acslens", 12), ("acssp", 12), ("acsst", 96), ("acslv", 96)]
# (added after the arrays, so a line saved before them still loads: they take these defaults)
SAVE_EXTRA = [("acsink", 0), ("acblur", 0), ("acswell", 0), ("acharmx", 0), ("acpump", 0), ("acpumpd", 0.5),
              ("acduck", 0), ("acjour", 0), ("acjpad", 0), ("acjdrone", 0), ("acjstrike", 0), ("acrvpre", 0),
              ("acrvera", 3), ("acsname", 0), ("acstonic", -1), ("acsscale", 0), ("acspark", 0), ("acsparko", 1),
              ("acmeisel", 0), ("acbrsel", 0), ("acsubt", 0)] + \
             [(f"acsh{x}{p}", d) for x in "dspbmtac" for p, d in (("t", 0.5), ("d", 0), ("w", 0.5))] + \
             [("acmemon", 0), ("acmemg", 2)] + \
             [(n, d) for n, d in (("acmuser", 0), ("acmuk", 3), ("acmun", 8), ("acmurot", 0), ("acmusw", -1),
                                  ("acmghost", 0), ("acmrat", 0), ("acmharm", 0), ("acbuser", 0), ("acbru0", 1),
                                  ("acbru1", 1), ("acbru2", 1), ("acbru3", 1), ("acbru4", 1), ("acbghost", 0),
                                  ("acbrat", 0), ("acbrub", 1), ("acbharm", 0))]
SAVE_EXTRA_AT = len(SAVE_SCALARS) + sum(n for _, n in SAVE_ARRAYS)
# then the section memory (MEMORY): a line saved before it lacks it, and it loads empty
SAVE_TAIL = [("acsnapt", NSNAP * len(KNOBS)), ("acsnapv", NSNAP * len(KNOBS))]
SAVE_TAIL_AT = SAVE_EXTRA_AT + len(SAVE_EXTRA)
# then how the piece writes (LINES .. WRITING): a line saved before them takes the defaults
SAVE_MORE = [(n, GLOBALS[n]) for n in ("acmelm", "acmutp", "accanon", "accand", "acmovm", "achmvp", "acsecd", "acnewt",
                                       "acphr", "acvlead", "ackplan", "acrests", "acmdev", "acans", "acphase", "acreg",
                                       "acwrite", "acpadm", "acdrsub", "acendp", "acrcell", "acarc", "acbassm",
                                       "acctr", "acshbp", "acshbq", "acshmp", "acshmq") +
             tuple(f"acsh{x}{j}" for x in "dsptac" for j in "pq") + ("acpln", "acplv", "acplm", "acplp")
             + ("acdrd", "acdrs", "acsud", "acsus")]
SAVE_MORE_AT = SAVE_TAIL_AT + sum(n for _, n in SAVE_TAIL)
SAVE_LEN = SAVE_MORE_AT + len(SAVE_MORE)
# what a recall of "sound only" brings: the knobs, the sounds, the layers - not the seed, the music or the form
SOUND_ONLY = set(KNOBS) | {"acspad", "acsdrone", "acstex", "acschar", "acsbell", "acsmot", "acglide", "acssub",
                          "acsatm"} | {"acm" + n for n in ("drone", "sub", "pad", "bell", "motion", "tex", "atm", "cloud")} \
             | {n for n, _ in SAVE_EXTRA}
# the SAVES page's slot: empty, a factory piece, or a saved one by its name (a word, or its key and scale)
_NSC = len(SCALES)
SLOT_LABELS = (["empty", "saved"] + [n for n, _, _ in FACTORY] + NAME_WORDS[1:]
               + [f"{k} {sc}" for k in NOTE_NAMES for sc, _ in SCALES])
SLOT_LABEL = (f"if(acslotfull == 0, if(acslot < {len(FACTORY)}, 2 + acslot, 0), if(acslnm > 0, {1 + len(FACTORY)} + acslnm, "
              f"if(acslkey >= 0, {1 + len(FACTORY) + len(NAME_WORDS)} + acslkey*{_NSC} + acslsc, 1)))")


# SETUP RECALL: how a load comes in (the knobs glide over Morph; the choices switch at once), what it
# brings, how ANCHOR glides back, and COMPARE (the slot as saved, while the knob is up)
SMORPH = [("cut", 0), ("1 s", 1000), ("2 s", 2000), ("4 s", 4000), ("8 s", 8000), ("15 s", 15000), ("30 s", 30000),
          ("1 min", 60000), ("2 min", 120000)]
SRECALL = ["piece", "sound only"]
SANCG = [("2 s", 2000), ("4 s", 4000), ("8 s", 8000), ("15 s", 15000), ("30 s", 30000)]
# SETUP GROOVE: PUMP ducks the bed (drone, sub, pads, atmosphere) on a grid; DUCK dips the piece while
# you play (notes held or breath), coming back over its release
SPUMP = ["off", "4 bars", "2 bars", "1 bar", "1/2 bar", "beat"]
PUMP_BEATS = "if(acpump == 1, 4*acmeter, if(acpump == 2, 2*acmeter, if(acpump == 3, acmeter, if(acpump == 4, max(1, int(acmeter/2)), 1))))"
SDUCKR = [("0.5 s", 500), ("1 s", 1000), ("2 s", 2000), ("4 s", 4000), ("8 s", 8000)]
# SETUP pages 17-18, MACRO A / B: four macros (CC targets macro 1-4), each moving two knobs with a depth of its
# own (-100 .. +100 %): offset (the knob's value moves away while the macro is up, back as it comes down) or latch
# (the macro drags the knob's value, which stays where it is left)
MT_KNOBS = [i for i, n in enumerate(KNOBS) if n not in ("acinput", "acrvtype")]
_SHORT = {"acrvmix": "Rv mix", "acrvtime": "Rv time", "acrvtone": "Rv tone"}
MTARGETS = ["off"] + [_SHORT.get(KNOBS[i], [l for p in PAGES for l, _, _ in p][i] +
                      (" snd" if 12 <= i < 20 else " lvl" if 20 <= i < 28 else "")) for i in MT_KNOBS]
SMMODE = ["offset", "latch"]
# SETUP JOURNEY: the layers travel through their engines, each step slowly crossfaded - the pad voices
# (each on its own schedule) through a set of pad types, the drone through its designs, the bells and the motion
# through the struck engines. Speed sets the time between steps; a CC (journey step) steps them by hand.
SJOUR = [("held", 0), ("very slow", 180000), ("slow", 90000), ("medium", 40000), ("fast", 15000)]
JPAD_SETS = [("off", []), ("soft", ["sine", "glass", "part", "beat", "vox", "bow"]),
             ("bright", ["saws", "pwm", "sync", "fm", "tine", "digi"]),
             ("all", ["sine", "glass", "beat", "vox", "saws", "pwm", "part", "bow", "tine", "fm", "sync", "fold"])]
SJDRONE = ["off", "on"]
SJSTRIKE = ["off", "bells", "motion", "both"]
# SETUP COLOUR: a pre-delay before every reverb, the era of its converters (70s: narrow band, few
# bits .. now: full band)
SPRE = [0, 10, 25, 50, 80, 120, 200]
SERA = ["70s", "80s", "90s", "now"]
# SETUP CC OUT: what moves inside, out as 16 CCs from a base (the layers' levels, energy, density,
# brightness, the way to the next chord and section, the reverb, the pads' motion, the swell), on change
SCCBASE = [20, 40, 70, 102]
SCCRATE = [("2 Hz", 500), ("5 Hz", 200), ("10 Hz", 100)]
ARRAYS.update({n: len(v) for n, v in DATA_TABLES.items()})
ARRAYS["acsavebuf"] = SAVE_LEN
ARRAYS.update({n: k for n, k in SAVE_TAIL})
ARRAYS["acsetbuf"] = len(SETTINGS) - 12
ARRAYS["acslotbuf"] = SAVE_LEN
SDRIFT = [("very slow", 120), ("slow", 60), ("medium", 25), ("fast", 8)]   # DRIFT: one sweep, s
SPLV = ["top", "top two", "all four"]           # PAD LINES: which voices move
SPLM = ["neighbour", "passing", "free"]          # how: back to the chord tone, on to the next one, or leaps too
SPLP = ["half beat", "beat", "two beats"]        # how often one may
GLIDE_X = "if(acglide == 0, 0, if(acglide == 1, 0.05, if(acglide == 2, 0.15, if(acglide == 3, 0.3, if(acglide == 4, 0.6, 1)))))"


def settings():
    c = Canvas("settings", w=2400)
    c.comment("settings.txt: the first 12 knob values, the SETUP values, then the SENDS knobs, one line. Loaded at start-up, "
              "saved 3 s after a change and when SETUP closes.")
    td = c.obj("text define acsettings")
    r = c.recv("ac-loadsettings")
    t = c.to(r, "t b b")
    c.c(c.m((t, 1), "read settings.txt"), 0, td, 0)
    mo = c.ch((t, 0), "text size acsettings", "moses 1")
    got = c.ch(c.m((mo, 1), "0"), "text get acsettings")
    ln = c.to(got, "t b l l")           # (right to left: the knobs, the SETUP values, then apply them)
    c.c(c.ch((ln, 2), "list split 12"), 0, c.obj("array set acparams"), 0)
    sp = c.ch((ln, 1), "list split 12")
    up = c.to((sp, 1), "unpack " + " ".join(["f"] * (len(SETTINGS) - 12)))
    for i, n in enumerate(SETTINGS[12:]):     # SETUP values, then the knobs after the first 12 (older files lack them)
        c.c(up, i, c.obj("v " + n), 0)
    c.col()
    # knob values out of the array into their values
    tb = c.to((ln, 0), "t b")
    # the In knob (external audio) always starts at 0, whatever was saved: nothing reaches the input until
    # you turn it up
    run_steps(c, (tb, 0), [T("acparams", IN_IDX, "0")]
              + [T("acparams", FILE_KNOBS + i, n) for i, n in enumerate(KNOBS[FILE_KNOBS:])] + [
                           Loop(str(len(KNOBS)), "aci", [SendL("ac-pset", ["aci", "acparams[int(aci)]"])]),
                           Call("ac-sendupd"),
                           SendL("ac-vintage", ["acvintage"]),
                           SendL("ac-lvvibr", ["acvibr"]), V("acmode", "acmodesel == 0"),
                           Call("ac-rvcolour"), Call("ac-sinkupd"), Call("ac-pumpupd"), Call("ac-sparkupd"), Later("ac-jourupd", 400),
                           Later("ac-logupd", 500)])
    rt = c.to(c.recv("ac-pset"), "route " + " ".join(str(i) for i in range(len(KNOBS))))
    for i, n in enumerate(KNOBS):
        c.c(rt, i, c.obj("v " + n), 0)
    c.col()
    # save (3 s after the last change)
    d = c.to(c.recv("ac-dirty"), "delay 3000")
    c.c(d, 0, c.obj("s ac-save"), 0)
    # (the values go through an array: one expr holds at most 100 of them)
    tsv = c.to(c.recv("ac-save"), "t b b")
    run_steps(c, (tsv, 1), [T("acsetbuf", i, n) for i, n in enumerate(SETTINGS[12:])])
    t2 = c.to((tsv, 0), "t b b")
    la = c.obj("list append")
    c.c(c.to((t2, 1), "array get acsetbuf"), 0, la, 1)
    c.c(c.to((t2, 0), f"array get acparams 0 {FILE_KNOBS}"), 0, la, 0)
    tl = c.to(la, "t b l")
    c.c(c.ch((tl, 1), "list prepend set", "list trim"), 0, td, 0)
    c.c(c.m((tl, 0), "write settings.txt"), 0, td, 0)
    return c


def setup_pages():
    """SETUP's pages in their order (SETUP_GROUPS)"""
    pages = dict(_setup_pages())
    assert set(pages) == set(SETUP_NAMES), set(pages) ^ set(SETUP_NAMES)
    return [(n, pages[n]) for n in SETUP_NAMES]


def _setup_pages():
    """SETUP, page by page: (name, [row 1, row 2, row 3, row 4]), each row (text with $n, parts) - the parts as
    Line takes them, or None for a fixed text. Knob k of a page sets its row k (setup(): the handler, by at()). Also
    read by tools/manual.py, so the manual lists exactly these rows."""
    return [
        ("GENERAL", [
            ("list 1 MIDI out $1", [("s", "acmout", MOUT)]),
            ("list 2 Sync $1", [("s", "acsync", ["internal", "follow clock"])]),
            ("list 3 Mode $1", [("s", "acmodesel", ["COMPOSE", "DRIFT"])]),
            ("list 4 Bloom $1", [("s", "acvintage", ["clean", "vintage"])]),
        ]),
        ("PLAYING", [
            ("list 1 Follow you $1", [("f", "int(acfollow*100)")]),
            ("list 2 MPE bend $1", [("f", "acnbr")]),
            ("list 3 MIDI out ch $1", [("f", "acoutch")]),
            ("list 4 Breath curve $1", [("f", "int(accurve*100)")]),
        ]),
        ("OUTPUT", [
            ("list 1 Output $1", [("s", "acmono", OUTPUTS)]),
            ("list 2 Width $1", [("f", "int(acwidth*100)")]),
            ("list 3 Pan motion $1", [("f", "int(acpanmot*100)")]),
            ("list 4 Tempo $1 $2-$3", [("s", "actrange", [n for n, _, _ in TEMPOS]), ("f", "actlo[int(actrange)]"), ("f", "acthi[int(actrange)]")]),
        ]),
        ("NOTES OUT", [
            ("list 1 MIDI notes $1", [("s", "acmparts", PARTS)]),
            ("list 2 Arp octave C$1", [("f", "acarpoct/12 - 1")]),
            ("list 3 -", None),
            ("list 4 -", None),
        ]),
        # CPU: the load (and the lite step the guard took), knob 1 fully up runs the profile (gen_log); the guard,
        # with or without the performance log
        ("CPU", [
            ("list 1 CPU $1% lite $2", [("f", "int(acload*100)"), ("f", "acshed")]),
            ("list 2 CPU guard $1", [("s", "acguard", SGUARD)]),
            ("list 3 -", None),
            ("list 4 -", None),
        ]),
        ("SOUNDS", [
            ("list 1 Pads $1", [("s", "acspad", SPADS)]),
            ("list 2 Drone $1", [("s", "acsdrone", SDRONES)]),
            ("list 3 Texture $1", [("s", "acstex", STEXS)]),
            ("list 4 Character $1", [("s", "acschar", SCHARS)]),
        ]),
        ("MUSIC", [
            ("list 1 Key $1", [("s", "ackeyc", SKEYS)]),
            ("list 2 Scale $1", [("s", "acsclc", SSCALES)]),
            ("list 3 Chords $1", [("s", "acchdc", SCHORDS)]),
            ("list 4 Pulse $1", [("s", "acpulc", PULSES)]),
        ]),
        ("MIDI IN", [
            ("list 1 Notes to $1", [("s", "acroute", ROUTES)]),
            ("list 2 Breath $1", [("s", "acbrto", BRTOS)]),
            ("list 3 Press $1", [("s", "acpressto", TARGETS)]),
            ("list 4 Breath in $1%", [("f", "int(aclbv*100)")]),
        ]),
        ("CC MAP", [
            ("list 1 CC $1", [("f", CCSEL)]),
            ("list 2 to $1", [("s", MAPSEL, TARGETS)]),
            ("list 3 Last CC $1 = $2", [("f", "aclastcc"), ("f", "aclastv")]),
            ("list 4 Vib rate $1 Hz", [("f", "acvibr")]),
        ]),
        ("VOICES", [
            ("list 1 Bells $1", [("s", "acsbell", SBELLS)]),
            ("list 2 Motion $1", [("s", "acsmot", SMOTS)]),
            ("list 3 Glide $1", [("s", "acglide", GLIDES)]),
            ("list 4 Sub $1", [("s", "acssub", SSUBS)]),
        ]),
        ("FORM", [
            ("list 1 Form $1", [("s", "acsform", SFORMS)]),
            ("list 2 Tempo $1", [("s", "acstempo", STEMPOS)]),
            ("list 3 Meter $1", [("s", "acsmeter", SMETERS)]),
            ("list 4 Atmos $1", [("s", "acsatm", SATMS)]),
        ]),
        ("SECTIONS", [
            ("list 1 Section $1/$2 $3", [("f", "acsecsel + 1"), ("f", "if(acscount > 0, acscount, acnsec)"), ("s", "acsecfol", ["fixed", "now"])]),
            ("list 2 Role $1", [("s", "if(acscount > 0, acsroles[int(acsecsel)], acroles[int(acsecsel)])", SROLES)]),
            ("list 3 Length $1", [("s", "acslens[int(acsecsel)]", SLENS)]),
            ("list 4 Pads $1", [("s", "acssp[int(acsecsel)]", SPADS)]),
        ]),
        ("SECTION MIX", [
            ("list 1 Section $1 $2", [("f", "acsecsel + 1"), ("s", "acsecfol", ["fixed", "now"])]),
            ("list 2 Layer $1", [("s", "acslay", SEC_LAYER_NAMES)]),
            ("list 3 Play $1", [("s", "acsst[int(acsecsel*8 + acslay)]", SPLAY)]),
            ("list 4 Level $1%", [("f", "int(acslv[int(acsecsel*8 + acslay)]*100)")]),
        ]),
        ("SAVES", [
            ("list 1 Slot $1 $2", [("f", "acslot + 1"), ("s", SLOT_LABEL, SLOT_LABELS)]),
            ("list 2 Save - turn up", None),
            ("list 3 Load - turn up", None),
            ("list 4 Name $1", [("s", "acsname", NAME_WORDS)]),
        ]),
        ("LIVE", [
            ("list 1 Mix CCs $1", [("s", "acmixcc", SMIXCC)]),
            ("list 2 Program $1", [("s", "acpgm", SPGM)]),
            ("list 3 Key fade $1", [("s", "aclfd", [n for n, _ in SLFADE])]),
            ("list 4 Entry fade $1", [("s", "acsfd", [n for n, _ in SSFADE])]),
        ]),
        ("RECALL", [
            ("list 1 Morph $1", [("s", "acmorph", [n for n, _ in SMORPH])]),
            ("list 2 Recall $1", [("s", "acrecall", SRECALL)]),
            ("list 3 Anchor glide $1", [("s", "acancg", [n for n, _ in SANCG])]),
            ("list 4 Compare $1", [("s", "accmp", ["yours", "saved"])]),
        ]),
        ("GROOVE", [
            ("list 1 Pump $1", [("s", "acpump", SPUMP)]),
            ("list 2 Pump depth $1%", [("f", "int(acpumpd*100)")]),
            ("list 3 Duck $1%", [("f", "int(acduck*100)")]),
            ("list 4 Duck release $1", [("s", "acduckr", [n for n, _ in SDUCKR])]),
        ]),
        ("MACRO A", [
            ("list 1 Macro $1", [("f", "acmcsel + 1")]),
            ("list 2 Mode $1", [("s", msel("mode"), SMMODE)]),
            ("list 3 A $1", [("s", msel("ta"), MTARGETS)]),
            ("list 4 A depth $1%", [("f", f"int(200*{msel('da')} - 100)")]),
        ]),
        ("MACRO B", [
            ("list 1 Macro $1", [("f", "acmcsel + 1")]),
            ("list 2 B $1", [("s", msel("tb"), MTARGETS)]),
            ("list 3 B depth $1%", [("f", f"int(200*{msel('db')} - 100)")]),
            ("list 4 Value $1%", [("f", f"int(100*{msel('v')})")]),
        ]),
        ("JOURNEY", [
            ("list 1 Speed $1", [("s", "acjour", [n for n, _ in SJOUR])]),
            ("list 2 Pads $1", [("s", "acjpad", [n for n, _ in JPAD_SETS])]),
            ("list 3 Drone $1", [("s", "acjdrone", SJDRONE)]),
            ("list 4 Bells $1", [("s", "acjstrike", SJSTRIKE)]),
        ]),
        ("COLOUR", [
            ("list 1 Pre-delay $1 ms", [("f", _pick("acrvpre", list(enumerate(SPRE))))]),
            ("list 2 Era $1", [("s", "acrvera", SERA)]),
            ("list 3 Sparkle $1%", [("f", "int(acspark*100)")]),
            ("list 4 Sparkle $1", [("s", "acsparko", SSPARKO)]),
        ]),
        ("CC OUT", [
            ("list 1 CC out $1", [("s", "acccout", ["off", "on"])]),
            ("list 2 Channel $1", [("f", "acccch")]),
            ("list 3 From CC $1", [("f", _pick("acccbase", list(enumerate(SCCBASE))))]),
            ("list 4 Rate $1", [("s", "acccrate", [n for n, _ in SCCRATE])]),
        ]),
        ("MEMORY", [
            ("list 1 Memory $1", [("s", "acmemon", ["off", "on"])]),
            ("list 2 Glide $1", [("s", "acmemg", [n for n, _ in SMEMG])]),
            ("list 3 Clear sec $1 - up", [("f", f"int(acsec) % {NSNAP} + 1")]),
            ("list 4 Clear all - turn up", None),
        ]),
        ("DISPLAY", [
            ("list 1 Hints $1", [("s", "achints", ["off", "on"])]),
            ("list 2 Scope $1", [("s", "acscope", ["off", "on"])]),
            ("list 3 Scope gain $1", [("s", "acscopeg", [n for n, _ in SSCOPEG])]),
            ("list 4 LED $1", [("s", "acledm", SLEDM)]),
        ]),
        ("LINES", [
            ("list 1 Melody $1", [("s", "acmelm", SMELM)]),
            ("list 2 Mutate $1", [("s", "acmutp", [n for n, _ in SMUTP])]),
            ("list 3 Canon $1", [("s", "accanon", SCANON)]),
            ("list 4 Canon delay $1", [("s", "accand", [n for n, _ in SCAND])]),
        ]),
        ("DRIFT", [
            ("list 1 Drone drift $1%", [("f", "int(acdrd*100)")]),
            ("list 2 Drone speed $1", [("s", "acdrs", [n for n, _ in SDRIFT])]),
            ("list 3 Sub drift $1%", [("f", "int(acsud*100)")]),
            ("list 4 Sub speed $1", [("s", "acsus", [n for n, _ in SDRIFT])]),
        ]),
        ("PAD LINES", [
            ("list 1 Lines $1%", [("f", "int(acpln*100)")]),
            ("list 2 Voices $1", [("s", "acplv", SPLV)]),
            ("list 3 Moves $1", [("s", "acplm", SPLM)]),
            ("list 4 Pace $1", [("s", "acplp", SPLP)]),
        ]),
        ("HARMONY", [
            ("list 1 Moves $1", [("s", "acmovm", SMOVM)]),
            ("list 2 How often $1", [("s", "achmvp", [n for n, _ in SMOVP])]),
            ("list 3 Dominants $1", [("s", "acsecd", [n for n, _ in SSECD])]),
            ("list 4 New types $1", [("s", "acnewt", ["off", "on"])]),
        ]),
        ("PHRASE", [
            ("list 1 Phrases $1", [("s", "acphr", SPHR)]),
            ("list 2 Voicing $1", [("s", "acvlead", SVLEAD)]),
            ("list 3 Key plan $1", [("s", "ackplan", SKPLAN)]),
            ("list 4 Breath $1", [("s", "acrests", [n for n, _ in SBREATH])]),
        ]),
        ("DIALOGUE", [
            ("list 1 Motif $1", [("s", "acmdev", SMDEV)]),
            ("list 2 Answer $1", [("s", "acans", SANS)]),
            ("list 3 Phasing $1", [("s", "acphase", [n for n, _ in SPHASE])]),
            ("list 4 Register $1", [("s", "acreg", SREG)]),
        ]),
        ("WRITING", [
            ("list 1 Writing $1", [("s", "acwrite", SWRITE)]),
            ("list 2 Pads carry $1", [("s", "acpadm", SPADM)]),
            ("list 3 Drone level $1", [("s", "acdrsub", SDRSUB)]),
            ("list 4 Ending $1", [("s", "acendp", SENDP)]),
        ]),
        ("ARC", [
            ("list 1 Rhythm $1", [("s", "acrcell", SRCELL)]),
            ("list 2 Arc $1", [("s", "acarc", SARC)]),
            ("list 3 Bass $1", [("s", "acbassm", SBASSM)]),
            ("list 4 Counter $1", [("s", "acctr", SCTR)]),
        ]),
    ]


def setup_rows():
    """the same table row by row: [(1, page 1 row 1, page 2 row 1, ...), (2, ...), ...] (setup() draws it so)"""
    pages = setup_pages()
    assert [n for n, _ in pages] == SETUP_NAMES
    return [(k + 1,) + tuple(rows[k] for _, rows in pages) for k in range(4)]

def quick_pages():
    """the quick pages, as setup_pages(): CHORD, a page per layer, INPUT, a SHAPE page per layer, GLIDE"""
    types = dict(acsubt=SUBTYPES, acsdrone=SDRONES, acssub=SSUBS, acspad=SPADS, acsbell=SBELLS, acsmot=SMOTS, acstex=STEXS, acsatm=SATMS)
    pages = [("CHORD", [
        ("list 1 Next $1  $2/$3", [("s", "acnxn", CHORD_NAMES), ("f", "acxdeg + 1"), ("f", "acn")]),
        ("list 2 Now $1", [("s", "acchn", CHORD_NAMES)]),
        ("list 3 Another - turn up", None),
        ("list 4 On pick $1", [("s", "acchpick", SCHPICK)]),
    ])]
    for name, m, t, mx, snd in LAYER_PAGES:
        pages.append((name, [
            ("list 1 Sound $1", [("s", t, types[t])]) if t else ("list 1 Sound -", None),
            ("list 2 Play $1", [("s", m, SPLAYQ)]),
            ("list 3 Level $1%", [("f", f"int({mx}*100)")]),
            ("list 4 Verb send $1%", [("f", f"int({snd}*100)")]) if snd else ("list 4 Verb send -", None),
        ]))
    # INPUT (top G# held): what the input does (the mode: resonators, grains, tape, ghost bells, bands, vocoding,
    # morphing - the pads carry its spectrum), how loud, how much it steers the composition, its reverb send
    pages.append(("INPUT", [
        ("list 1 Mode $1", [("s", "acinmode", INMODES)]),
        ("list 2 In $1%", [("f", "int(acinput*100)")]),
        ("list 3 Follow you $1%", [("f", "int(acfollow*100)")]),
        ("list 4 Verb send $1%", [("f", "int(acsndi*100)")]),
    ]))
    # each layer's SHAPE (its key held): its sound, then tone, drive and width (gen_dsp.shaped)
    for (name, m, t, mx, snd), x in zip(LAYER_PAGES, SHAPE_X):
        t = "acsubt" if t == "acssub" else t           # (the sub's page: its mode; its SHAPE: its sound)
        pages.append((name + " SHAPE", [
            ("list 1 Sound $1", [("s", t, types[t])]) if t else ("list 1 Sound -", None),
            ("list 2 Tone $1 $2%", [("s", f"if(acsh{x}t < 0.49, 0, if(acsh{x}t > 0.51, 2, 1))", ["dark", "open", "thin"]),
                                     ("f", f"int(abs(acsh{x}t - 0.5)*200)")]),
        ] + ([] if x not in ENGINE_X else
             # (the bells and the motion: their engine's two parameters, named by the engine playing)
             [(f"list {3 + j} $1 $2%", [("s", SOUND_X[x][0], [nm[j] for nm in SOUND_X[x][1]]),
                                        ("f", f"int(acsh{x}{'pq'[j]}*100)")]) for j in range(2)])))
    pages.append(("GLIDE", [
        ("list 1 Chords $1", [("s", "acglide", GLIDES)]),
        ("list 2 Morph $1", [("s", "acmorph", [n for n, _ in SMORPH])]),
        ("list 3 Anchor $1", [("s", "acancg", [n for n, _ in SANCG])]),
        ("list 4 Memory $1", [("s", "acmemg", [n for n, _ in SMEMG])]),
    ]))
    setup = dict(setup_pages())
    pages += [(n, setup[n]) for n, _ in MIRRORS]
    assert [n for n, _ in pages] == QUICK_NAMES
    return pages


PICK_MS = 150        # a sound picked by a knob acts once the knob has rested this long (see type_act)


def _pick_actions(var):
    """what picking a layer's sound does (after the knob rests: type_act)"""
    # (a pick by hand wins over JOURNEY, which carries on from it: gen_perform ac-jpick-*)
    jpick = dict(acspad="ac-jpick-pad", acsdrone="ac-jpick-drone", acsbell="ac-jpick-bell", acsmot="ac-jpick-mot")
    if var in ("acspad", "acsdrone", "acstex", "acschar"):
        return ([V("acflstag", "0"), Call("ac-padpick")] if var == "acspad" else []) + (
            [Call(jpick[var])] if var in jpick else []) + [Call("ac-sndovr"), V("acfade", "1500"), Call("ac-layers")]
    if var in ("acsbell", "acsmot"):
        return [Call(jpick[var]), V("acfade", "600"), Call("ac-layers")]
    if var == "acsubt":
        return [SendL("ac-subt", ["acsubt"])]
    if var == "acsatm":       # the atmosphere: from now (auto: the next section picks)
        return [If("acsatm > 0", [V("acatmcur", "acsatm - 1"), V("acfade", "3000"), Call("ac-layers")])]
    return []


PICKED = set()       # the sounds type_act was used for: setup() builds their ac-pick-<var>
SETTLE = {}          # settle(): name -> the steps that wait for the knob to rest (setup() builds ac-act-<name>)


def settle(name, act):
    """a choice whose effect is heavy (a chord change, a new plan, the layers): the screen shows it at once, act runs
    once the knob has rested PICK_MS (ac-act-<name>) - a turn through the choices acts once, for the last"""
    SETTLE[name] = act
    return Later(f"ac-act-{name}", PICK_MS)


def type_act(var):
    """a layer's sound chosen (SOUNDS, VOICES, FORM or its quick page), from acsv: acts only when it changes. The
    choice shows at once; the sound follows once the knob has rested PICK_MS (ac-pick-<var>), so turning through the
    choices crossfades only to the last one - every one passed would otherwise start (CPU, audio drop-outs)"""
    opts = dict(acspad=SPADS, acsdrone=SDRONES, acstex=STEXS, acschar=SCHARS, acsbell=SBELLS, acsmot=SMOTS,
                acssub=SSUBS, acsatm=SATMS, acsubt=SUBTYPES)[var]
    then = [V(var, "acsnew")]
    if _pick_actions(var):
        PICKED.add(var)
        then.append(Later(f"ac-pick-{var}", PICK_MS))
    return [V("acsnew", f"int(acsv*{len(opts) - 0.01})"), If(f"acsnew != {var}", then)]


def _dispatch(item, steps):
    """steps with a run of If(item == n, [...]) handlers in the middle: the item is computed once and [sel] runs
    only its own handler(s), in order, instead of every condition in turn (about 150, at each knob step). The same
    as the chain, since no handler changes the page or the knob (acsetpg, acsk) - only keys and aux do."""
    pat = re.compile(r"^" + re.escape(item) + r" == (\d+)$")

    def items_of(st):         # If(at(...) [|| at(...)]) with no else: the items it handles, else None
        parts = (getattr(st, "cond", None) or "").split(" || ")
        ms = [pat.match(p) for p in parts]
        return [int(m.group(1)) for m in ms] if all(ms) and not st.els else None
    keyed = [items_of(st) is not None for st in steps]
    first, last = keyed.index(True), len(keyed) - 1 - keyed[::-1].index(True)
    assert all(keyed[first:last + 1]), "SETUP knob handlers: a step that isn't If(at(...)) among them"
    def timers(sts):         # (an Arm / Later: its [delay] would be built once per item)
        return any(st.__qualname__.split(".")[0] in ("Arm", "Later") or timers(getattr(st, "then", None))
                   or timers(getattr(st, "els", None)) for st in sts or [])
    groups = {}
    for st in steps[first:last + 1]:
        assert len(items_of(st)) == 1 or not timers(st.then), "a handler of several SETUP knobs holds a delay"
        for k in items_of(st):
            groups.setdefault(k, []).extend(st.then)
    keys = sorted(groups)

    def dispatch(c, src):
        e = c.obj("expr " + item)
        c.c(*src, e, 0)
        sel = c.obj("sel " + " ".join(str(k) for k in keys))
        c.c(e, 0, sel, 0)
        for i, k in enumerate(keys):
            Sub(f"setup-knob-{k // 4}-{k % 4 + 1}", groups[k])(c, (sel, i))
    return steps[:first] + [dispatch] + steps[last + 1:]


def quick_knobs(item):
    """the quick pages' knobs (item: the page x 4 + the knob)"""
    def at(pg, row):
        return f"{item} == {pg * 4 + row - 1}"

    def knob(name):        # a knob page's value set from here (as a macro does: not shown as your hand)
        i = KNOBS.index(name)
        return [T("acparams", i, "acsv"), V("acmorphing", "1"), SendL("ac-param", [str(i), "acsv"]), V("acmorphing", "0")]
    st = [
        # CHORD: knob 1 the next chord, from the key's chords (and, with On pick now, at once); knob 3 fully up
        # another one picked by the piece (re-armed below 90 %)
        # (knob 1 picks when it moves to another chord - not when the piece's own next chord differs from it, which
        #  after every change it does: the first value after the page opens only notes where the knob is)
        If(at(CHORD_PAGE, 1), [V("acsnew", "int(acsv*(acn - 0.01))"), If("acxk == -2", [V("acxk", "acsnew")], [
            If("acsnew != acxk", [
                X("acsnew; acsnew; actonic; 0; 1", "v acxk", "v acxdeg", "v acxt", "v acxscf", "v acxpick"),
                Call("ac-chordshow"),
                # (a chord picked by hand wins over Resolve, which would hold the tonic: released)
                settle("chordpick", [If("acres", [V("acres", "0"), Toast("resolve released")]),
                                     If("acchpick && acxpick", [Call("ac-chordnow")])])])])]),
        If(at(CHORD_PAGE, 3), [If("acsv > 0.9 && acchsurp <= 0.9", [Call("ac-chordnext")]), V("acchsurp", "acsv")]),
        If(at(CHORD_PAGE, 4), [V("acchpick", "acsv > 0.5")]),
    ]
    for j, (name, m, t, mx, snd) in enumerate(LAYER_PAGES):
        pg = LAYER_PAGE0 + j
        st += ([If(at(pg, 1), type_act(t))] if t else []) + [
            If(at(pg, 2), [V("acsnew", "int(acsv*2.99)"), If(f"acsnew != {m}", [V(m, "acsnew"), V("acfade", LFADE),
                                                                                Call("ac-layers")])]),
            If(at(pg, 3), knob(mx))] + ([If(at(pg, 4), knob(snd))] if snd else [])
    for j, ((name, m, t, mx, snd), x) in enumerate(zip(LAYER_PAGES, SHAPE_X)):
        pg = SHAPE_PAGE0 + j
        t = "acsubt" if t == "acssub" else t
        st += ([If(at(pg, 1), type_act(t))] if t else []) + [
            If(at(pg, 2), [V(f"acsh{x}t", "acsv"), Call(f"ac-shpupd-{x}")]),
            If(at(pg, 3), [V(f"acsh{x}d" if x not in SOUND_X else f"acsh{x}p", "acsv"), Call(f"ac-shpupd-{x}")]),
            If(at(pg, 4), [V(f"acsh{x}w" if x not in SOUND_X else f"acsh{x}q", "acsv"), Call(f"ac-shpupd-{x}")])]
    st += [If(at(INPUT_PAGE, 1), [V("acsnew", f"int(acsv*{len(INMODES) - 0.01})"), If("acsnew != acinmode", [
               V("acinmode", "acsnew"), Call("ac-inputupd"), Call("ac-scr5")])]),
           If(at(INPUT_PAGE, 2), knob("acinput")),
           If(at(INPUT_PAGE, 3), [V("acfollow", "acsv")]),
           If(at(INPUT_PAGE, 4), knob("acsndi"))]
    st += [If(at(GLIDE_PAGE, 1), [V("acglide", f"int(acsv*{len(GLIDES) - 0.01})")]),
           If(at(GLIDE_PAGE, 2), [V("acmorph", f"int(acsv*{len(SMORPH) - 0.01})")]),
           If(at(GLIDE_PAGE, 3), [V("acancg", f"int(acsv*{len(SANCG) - 0.01})")]),
           If(at(GLIDE_PAGE, 4), [V("acmemg", f"int(acsv*{len(SMEMG) - 0.01})")])]
    return st


def setup():
    c = Canvas("setup", w=2600)
    c.comment("SETUP: hold aux 1 s. Knobs set the 4 items of the page (absolute), aux tap = other page.")
    # aux held 1 s without a key: enter / leave SETUP
    d = c.obj("delay 1000")
    c.c(c.to((c.ch(c.recv("aux"), "sel 0"), 1), "t b"), 0, d, 0)
    c.c(c.m(c.ch(c.recv("aux"), "sel 0"), "stop"), 0, d, 0)
    # (in SETUP the hold only marks itself: SETUP closes when aux is let go - unless knob 1 turned meanwhile, scrolling
    # the pages)
    run_steps(c, (d, 0), [If("acauxheld && acauxused == 0", [If("acsetup", [V("acauxlong", "1")], [
        V("acauxused", "1"), V("acsetup", "1"), V("acsetpg", "0"), Call("ac-oledsetup")])])])
    c.col()
    # knob values in SETUP arrive here as "knob value"
    up = c.to(c.recv("ac-setknob"), "unpack f f")
    c.c(up, 1, c.obj("v acsv"), 0)
    tb = c.to(up, "t b f")
    c.c(tb, 1, c.obj("v acsk"), 0)
    item = f"{SETPG_OF}*4 + acsk"        # the knob turned: page (0..) x 4 + knob (0..3) (a mirror: its SETUP page's)

    def at(page, row):
        """the condition: knob `row` (1-4) turned on SETUP page `page` (its name)"""
        return f"{item} == {SETUP_NAMES.index(page) * 4 + row - 1}"
    run_steps(c, (tb, 0), _dispatch(item, [
        If("acsetpg != acsetpgl", [X("1; 1; 1; 1; 1; 1; acsetpg; -2", "v acsvp49", "v acsvp50", "v acsvpp", "v acchsurp", "v acsvpm3", "v acsvpm4", "v acsetpgl", "v acxk")]),
        If(at("GENERAL", 1), [V("acmout", "int(acsv*3.99)"), If("acmout == 0 || acmout == 3", [Call("ac-clockstop")],
                                                               [Call("ac-clockstart")]),
                            If("acmout < 2", [Call("ac-notesoff")], [Call("ac-outchord")])]),
        If(at("GENERAL", 2), [V("acsync", "acsv > 0.5"), SendL("ac-bpm", ["acbpm"])]),
        If(at("GENERAL", 3), [V("acmodesel", "acsv > 0.5"),
                              settle("mode", [If("acmodesel != 1 - acmode", [Call("ac-modetoggle")])])]),
        If(at("GENERAL", 4), [V("acvintage", "acsv > 0.5"), SendL("ac-vintage", ["acvintage"])]),
        If(at("PLAYING", 1), [V("acfollow", "acsv")]),
        If(at("PLAYING", 2), [V("acnbr", "if(acsv < 0.25, 12, if(acsv < 0.5, 24, if(acsv < 0.75, 48, 96)))")]),
        If(at("PLAYING", 3), [V("acoutch", "1 + int(acsv*12.99)")]),
        If(at("PLAYING", 4), [V("accurve", "0.5 + 1.5*acsv")]),
        If(at("OUTPUT", 1), [V("acmono", f"int(acsv*{len(OUTPUTS) - 0.01})"), Call("ac-stereo")]),
        If(at("OUTPUT", 2), [V("acwidth", "0.5 + acsv"), Call("ac-stereo")]),
        If(at("OUTPUT", 3), [V("acpanmot", "acsv"), Call("ac-stereo")]),
        If(at("OUTPUT", 4), [V("actrange", f"int(acsv*{len(TEMPOS) - 0.01})"), Call("ac-settempo")]),
        If(at("NOTES OUT", 1), [V("acmparts", f"int(acsv*{len(PARTS) - 0.01})"), Call("ac-notesoff"), Call("ac-outchord")]),
        If(at("NOTES OUT", 2), [V("acarpoct", "24 + 12*int(acsv*4.99)"), Call("ac-notesoff"), Call("ac-outchord")]),
        # knob 3 turned fully up (re-armed below 90 %): the profile run (gen_log)
        If(at("CPU", 1), [If("acsv > 0.9 && acsvpp <= 0.9", [Call("ac-profile")]), V("acsvpp", "acsv")]),
        If(at("CPU", 2), [V("acguard", f"int(acsv*{len(SGUARD) - 0.01})"), Call("ac-logupd"),
                             If("acguard % 2 == 0 && acshed > 0", [V("acshed", "0"), Call("ac-layers"), Call("ac-inputupd")])]),
    ] + [
        # SOUNDS: act only when the choice changes, so turning the knob within one choice does not re-pick
        If(at("SOUNDS", 1 + j), type_act(var)) for j, var in enumerate(("acspad", "acsdrone", "acstex", "acschar"))
    ] + [
        # MUSIC: a choice applies at the next chord, which comes now
        If(at("MUSIC", 1), [V("acsnew", f"int(acsv*{len(SKEYS) - 0.01})"), If("acsnew != ackeyc", [
            V("ackeyc", "acsnew"), settle("key", [If("ackeyc > 0", [V("acpend", "ackeyc - 1"), V("achome", "35 + ackeyc"),
                                                                  Call("ac-change")])])])]),
        If(at("MUSIC", 2), [V("acsnew", f"int(acsv*{len(SSCALES) - 0.01})"), If("acsnew != acsclc", [
            V("acsclc", "acsnew"), settle("scale", [If("acsclc > 0", [V("acsci", "acsclc - 1"), Call("ac-loadscale"),
                                                                    Call("ac-change")])])])]),
        If(at("MUSIC", 3), [V("acsnew", f"int(acsv*{len(SCHORDS) - 0.01})"), If("acsnew != acchdc", [
            V("acchdc", "acsnew"), settle("chords", [If("acchdc > 0", [V("acfam", "acchdc - 1"), Call("ac-change")])])])]),
        If(at("MUSIC", 4), [V("acpulc", f"int(acsv*{len(PULSES) - 0.01})"), Call("ac-pulseupd")]),
        # MIDI IN
        If(at("MIDI IN", 1), [V("acsnew", f"int(acsv*{len(ROUTES) - 0.01})"), If("acsnew != acroute", [
            V("acroute", "acsnew"), settle("route", [Call("ac-allnotesoff"), Call("ac-routehome"), V("acfade", "1500"),
                                                     Call("ac-layers")])])]),
        If(at("MIDI IN", 2), [V("acsnew", f"int(acsv*{len(BRTOS) - 0.01})"), If("acsnew != acbrto", [
            V("acbrto", "acsnew"), Call("ac-brfxoff")])]),
        If(at("MIDI IN", 3), [V("acpressto", f"int(acsv*{len(TARGETS) - 0.01})")]),
        # CC MAP: knob 1 picks a CC, knob 2 its target, knob 4 the vibrato rate
        If(at("CC MAP", 1), [V("acccsel", f"int(acsv*{len(CCS) - 0.01})")]),
        If(at("CC MAP", 2), [If(f"acccsel == {j}", [V(f"acmap{j}", f"int(acsv*{len(TARGETS) - 0.01})")])
                             for j in range(len(CCS))] + [If("achold && " + " && ".join(f"acmap{j} != 6" for j in range(7))
                                                            + " && acpressto != 6", [V("achold", "0"), Call("ac-holdoff")])]),
        If(at("CC MAP", 4), [V("acvibr", "0.5*int(6 + 10*acsv)"), SendL("ac-lvvibr", ["acvibr"])]),
        # VOICES: the bells' and the motion's engine, crossfaded at once
    ] + [
        If(at("VOICES", 1 + j), type_act(var)) for j, var in enumerate(("acsbell", "acsmot"))
    ] + [
        # the glide applies from the next chord change
        If(at("VOICES", 3), [V("acglide", f"int(acsv*{len(GLIDES) - 0.01})")]),
        If(at("VOICES", 4), type_act("acssub")),
        # FORM: the shape applies to the next piece (or now, while the piece waits ready); the tempo and meter at
        # once; the atmosphere from the next section
        If(at("FORM", 1), [V("acsnew", f"int(acsv*{len(SFORMS) - 0.01})"), If("acsnew != acsform", [
            V("acsform", "acsnew"), Call("ac-formset")])]),
        If(at("FORM", 2), [V("acsnew", f"int(acsv*{len(STEMPOS) - 0.01})"), If("acsnew != acstempo", [
            V("acstempo", "acsnew"), Call("ac-settempo")])]),
        If(at("FORM", 3), [V("acsnew", f"int(acsv*{len(SMETERS) - 0.01})"), If("acsnew != acsmeter", [
            V("acsmeter", "acsnew"), If("acsmeter > 0", [V("acmeter", "acsmeter + 2")])])]),
        If(at("FORM", 4), type_act("acsatm")),
        # SECTIONS / SECTION MIX: editing a section turns the form to custom (from the piece's plan, the first
        # time); it applies to the piece at once (sections to come; the current one's layers now)
        # the section: turned fully down = now (follows the playing section), then sections 1-12
        If(at("SECTIONS", 1) + " || " + at("SECTION MIX", 1), [V("acsnew", "int(acsv*12.99)"), V("acsecfol", "acsnew == 0"),
                                             V("acsecsel", "if(acsnew == 0, min(11, acsec), acsnew - 1)")]),
        If(at("SECTION MIX", 2), [V("acslay", "int(acsv*7.99)")]),
    ] + [If(it, [Call("ac-customcopy"), V("acsform", "6"), act,
                 settle(name, [Call("ac-customapply"), Call("ac-secovr"), V("acfade", "1000"), Call("ac-layers")] + extra)])
         for name, (it, act, extra) in zip(("sroles", "slens", "spad", "splay", "slevel"), (
             (at("SECTIONS", 2), T("acsroles", "acsecsel", f"int(acsv*{len(SROLES) - 0.01})"), []),
             (at("SECTIONS", 3), T("acslens", "acsecsel", f"int(acsv*{len(SLENS) - 0.01})"), []),
             (at("SECTIONS", 4), T("acssp", "acsecsel", f"int(acsv*{len(SPADS) - 0.01})"), [If("acsecsel == acsec", [Call("ac-padpick")])]),
             (at("SECTION MIX", 3), T("acsst", "acsecsel*8 + acslay", f"int(acsv*{len(SPLAY) - 0.01})"), []),
             (at("SECTION MIX", 4), T("acslv", "acsecsel*8 + acslay", "2*acsv"), [])))
    ] + [
        # SAVES: knob 1 the slot, knob 2 up past 90 % saves, knob 3 loads (each re-arms below 90 %; a page change
        # re-arms only after the knob has gone down, so arriving with a knob up does nothing)
        If(at("SAVES", 1), [V("acslot", f"int(acsv*{NSLOTS - 0.01})"), Call("ac-slotcheck")]),
        If(at("SAVES", 2), [If("acsv > 0.9 && acsvp49 <= 0.9", [Call("ac-savepiece")]), V("acsvp49", "acsv")]),
        If(at("SAVES", 3), [If("acsv > 0.9 && acsvp50 <= 0.9", [Call("ac-loadpiece")]), V("acsvp50", "acsv")]),
        # LIVE
        If(at("LIVE", 1), [V("acmixcc", f"int(acsv*{len(SMIXCC) - 0.01})")]),
        If(at("LIVE", 2), [V("acpgm", f"int(acsv*{len(SPGM) - 0.01})")]),
        If(at("LIVE", 3), [V("aclfd", f"int(acsv*{len(SLFADE) - 0.01})")]),
        If(at("LIVE", 4), [V("acsfd", f"int(acsv*{len(SSFADE) - 0.01})")]),
        # RECALL
        If(at("RECALL", 1), [V("acmorph", f"int(acsv*{len(SMORPH) - 0.01})")]),
        If(at("RECALL", 2), [V("acrecall", "acsv > 0.5")]),
        If(at("RECALL", 3), [V("acancg", f"int(acsv*{len(SANCG) - 0.01})")]),
        If(at("RECALL", 4), [If("(acsv > 0.5) != accmp", [If("acsv > 0.5", [Call("ac-cmpon")], [Call("ac-cmpoff")])])]),
        # GROOVE
        If(at("GROOVE", 1), [V("acpump", f"int(acsv*{len(SPUMP) - 0.01})")]),
        If(at("GROOVE", 2), [V("acpumpd", "acsv")]),
        If(at("GROOVE", 3), [V("acduck", "acsv")]),
        If(at("GROOVE", 4), [V("acduckr", f"int(acsv*{len(SDUCKR) - 0.01})")]),
        # MACRO A / B
        If(at("MACRO A", 1) + " || " + at("MACRO B", 1), [V("acmcsel", "int(acsv*3.99)")]),
        If(at("MACRO A", 2), [If("acmcsel == 0", [V("acmc0mode", "acsv > 0.5")]), If("acmcsel == 1", [V("acmc1mode", "acsv > 0.5")]), If("acmcsel == 2", [V("acmc2mode", "acsv > 0.5")]), If("acmcsel == 3", [V("acmc3mode", "acsv > 0.5")])]),
        If(at("MACRO A", 3), [If("acmcsel == 0", [V("acmc0ta", f"int(acsv*{len(MTARGETS) - 0.01})")]), If("acmcsel == 1", [V("acmc1ta", f"int(acsv*{len(MTARGETS) - 0.01})")]), If("acmcsel == 2", [V("acmc2ta", f"int(acsv*{len(MTARGETS) - 0.01})")]), If("acmcsel == 3", [V("acmc3ta", f"int(acsv*{len(MTARGETS) - 0.01})")])]),
        If(at("MACRO A", 4), [If("acmcsel == 0", [V("acmc0da", "acsv")]), If("acmcsel == 1", [V("acmc1da", "acsv")]), If("acmcsel == 2", [V("acmc2da", "acsv")]), If("acmcsel == 3", [V("acmc3da", "acsv")])]),
        If(at("MACRO B", 2), [If("acmcsel == 0", [V("acmc0tb", f"int(acsv*{len(MTARGETS) - 0.01})")]), If("acmcsel == 1", [V("acmc1tb", f"int(acsv*{len(MTARGETS) - 0.01})")]), If("acmcsel == 2", [V("acmc2tb", f"int(acsv*{len(MTARGETS) - 0.01})")]), If("acmcsel == 3", [V("acmc3tb", f"int(acsv*{len(MTARGETS) - 0.01})")])]),
        If(at("MACRO B", 3), [If("acmcsel == 0", [V("acmc0db", "acsv")]), If("acmcsel == 1", [V("acmc1db", "acsv")]), If("acmcsel == 2", [V("acmc2db", "acsv")]), If("acmcsel == 3", [V("acmc3db", "acsv")])]),
        If(at("MACRO B", 4), [V("acmcn", "acmcsel"), V("acmcin", "acsv"), Call("ac-macro")]),
        # JOURNEY
        If(at("JOURNEY", 1), [V("acjour", f"int(acsv*{len(SJOUR) - 0.01})"), settle("journey1", [Call("ac-jourupd")])]),
        If(at("JOURNEY", 2), [V("acjpad", f"int(acsv*{len(JPAD_SETS) - 0.01})"), settle("journey2", [Call("ac-jourupd")])]),
        If(at("JOURNEY", 3), [V("acjdrone", "acsv > 0.5"), settle("journey3", [Call("ac-jourupd")])]),
        If(at("JOURNEY", 4), [V("acjstrike", "int(acsv*3.99)"), settle("journey4", [Call("ac-jourupd")])]),
        # COLOUR (the reverbs; GLINT below)
        If(at("COLOUR", 1), [V("acrvpre", f"int(acsv*{len(SPRE) - 0.01})"), Call("ac-rvcolour")]),
        If(at("COLOUR", 2), [V("acrvera", "int(acsv*3.99)"), Call("ac-rvcolour")]),
        If(at("COLOUR", 3), [V("acspark", "acsv"), Call("ac-sparkupd")]),
        If(at("COLOUR", 4), [V("acsparko", f"int(acsv*{len(SSPARKO) - 0.01})")]),
        If(at("SAVES", 4), [V("acsname", f"int(acsv*{len(NAME_WORDS) - 0.01})")]),
        # CC OUT
        # MEMORY: on / off, the glide; knob 3 fully up clears the playing section's memory, knob 4 all of it
        If(at("MEMORY", 1), [V("acmemon", "acsv > 0.5")]),
        If(at("MEMORY", 2), [V("acmemg", f"int(acsv*{len(SMEMG) - 0.01})")]),
        If(at("MEMORY", 3), [If("acsv > 0.9 && acsvpm3 <= 0.9", [Call("ac-memclear")]), V("acsvpm3", "acsv")]),
        If(at("MEMORY", 4), [If("acsv > 0.9 && acsvpm4 <= 0.9", [Call("ac-memclearall")]), V("acsvpm4", "acsv")]),
        If(at("DISPLAY", 1), [V("achints", "acsv > 0.5")]),
        If(at("DISPLAY", 2), [V("acscope", "acsv > 0.5"), Call("ac-oledall")]),
        If(at("DISPLAY", 3), [V("acscopeg", f"int(acsv*{len(SSCOPEG) - 0.01})")]),
        If(at("DISPLAY", 4), [V("acledm", "acsv > 0.5"), Send("ac-led")]),
        If(at("LINES", 1), [V("acmelm", f"int(acsv*{len(SMELM) - 0.01})")]),
        If(at("LINES", 2), [V("acmutp", f"int(acsv*{len(SMUTP) - 0.01})")]),
        If(at("LINES", 3), [V("accanon", f"int(acsv*{len(SCANON) - 0.01})")]),
        If(at("LINES", 4), [V("accand", f"int(acsv*{len(SCAND) - 0.01})")]),
        If(at("HARMONY", 1), [V("acmovm", f"int(acsv*{len(SMOVM) - 0.01})")]),
        If(at("HARMONY", 2), [V("achmvp", f"int(acsv*{len(SMOVP) - 0.01})")]),
        If(at("HARMONY", 3), [V("acsecd", f"int(acsv*{len(SSECD) - 0.01})")]),
        If(at("HARMONY", 4), [V("acnewt", "acsv > 0.5")]),
        If(at("PHRASE", 1), [V("acsnew", f"int(acsv*{len(SPHR) - 0.01})"), If("acsnew != acphr", [
            X("acsnew; -1; 0", "v acphr", "v acphc", "v acphn")])]),
        If(at("PHRASE", 2), [V("acvlead", f"int(acsv*{len(SVLEAD) - 0.01})")]),
        # (the key plan: for the sections still to come)
        If(at("PHRASE", 3), [V("acsnew", f"int(acsv*{len(SKPLAN) - 0.01})"), If("acsnew != ackplan", [
            V("ackplan", "acsnew"), Call("ac-keyplan")])]),
        If(at("PHRASE", 4), [V("acrests", f"int(acsv*{len(SBREATH) - 0.01})"),
                             If("acrests == 0 && acrestp", [X("0; 0; 1500", "v acrestb", "v acrestp", "v acfade"),
                                                             Call("ac-layers")])]),
        If(at("DIALOGUE", 1), [V("acmdev", f"int(acsv*{len(SMDEV) - 0.01})")]),
        If(at("DIALOGUE", 2), [V("acans", f"int(acsv*{len(SANS) - 0.01})")]),
        If(at("DIALOGUE", 3), [V("acphase", f"int(acsv*{len(SPHASE) - 0.01})"), V("acpsd", "0")]),
        If(at("DIALOGUE", 4), [V("acreg", f"int(acsv*{len(SREG) - 0.01})")]),
        If(at("WRITING", 1), [V("acsnew", "acsv > 0.5"), If("acsnew != acwrite", [
            V("acwrite", "acsnew"), settle("writing", [X("0; 0; 1500", "v acrestb", "v acrestp", "v acfade"), Call("ac-layers"),
                                                       If("acwrite", [Toast("writing: moving")], [Toast("writing: still")])])])]),
        If(at("WRITING", 2), [V("acpadm", "acsv > 0.5")]),
        If(at("PAD LINES", 1), [V("acpln", "acsv")]),
        # (DRIFT back to 0: the sound's parameters back where its SHAPE page has them)
        If(at("DRIFT", 1), [V("acdrd", "acsv"), If("acdrd <= 0.001", [Call("ac-shpupd-d")])]),
        If(at("DRIFT", 2), [V("acdrs", f"int(acsv*{len(SDRIFT) - 0.01})")]),
        If(at("DRIFT", 3), [V("acsud", "acsv"), If("acsud <= 0.001", [Call("ac-shpupd-s")])]),
        If(at("DRIFT", 4), [V("acsus", f"int(acsv*{len(SDRIFT) - 0.01})")]),
        If(at("PAD LINES", 2), [V("acplv", f"int(acsv*{len(SPLV) - 0.01})")]),
        If(at("PAD LINES", 3), [V("acplm", f"int(acsv*{len(SPLM) - 0.01})")]),
        If(at("PAD LINES", 4), [V("acplp", f"int(acsv*{len(SPLP) - 0.01})")]),
        If(at("WRITING", 3), [V("acdrsub", "acsv > 0.5"), settle("drsub", [V("acfade", "1500"), Call("ac-layers")])]),
        If(at("WRITING", 4), [V("acendp", "acsv > 0.5")]),
        If(at("ARC", 1), [V("acrcell", "acsv > 0.5")]),
        If(at("ARC", 2), [V("acarc", f"int(acsv*{len(SARC) - 0.01})"), Call("ac-brightupd")]),
        If(at("ARC", 3), [V("acbassm", f"int(acsv*{len(SBASSM) - 0.01})")]),
        If(at("ARC", 4), [V("acctr", "acsv > 0.5"), settle("ctr", [V("acfade", "2000"), Call("ac-layers")])]),
        If(at("CC OUT", 1), [V("acccout", "acsv > 0.5")]),
        If(at("CC OUT", 2), [V("acccch", "1 + int(acsv*15.99)")]),
        If(at("CC OUT", 3), [V("acccbase", "int(acsv*3.99)")]),
        If(at("CC OUT", 4), [V("acccrate", f"int(acsv*{len(SCCRATE) - 0.01})")]),
    ] + quick_knobs(item) + [
        Call("ac-oledsetup"), Send("ac-dirty"),
    ]))
    c.col()
    for var in sorted(PICKED):
        proc(c, f"ac-pick-{var}", _pick_actions(var))
    for name in sorted(SETTLE):
        proc(c, f"ac-act-{name}", SETTLE[name])
    proc(c, "ac-oledsetup", [
        Fill(0, 0, 128, 64, 0),
        Call("ac-setl0"), Call("ac-setl1"), Call("ac-setl2"), Call("ac-setl3"), Call("ac-setl4"),
        FLIP,
    ])
    # the header: SETUP n NAME; on a quick page its name (CHORD with the key and scale)
    proc(c, "ac-setl0", [If(f"acsetpg < {NSET}", [Send("ac-setl0s")], [
        If(f"acsetpg == {CHORD_PAGE}", [Send("ac-setl0c")], [
            If(f"acsetpg >= {MIRROR0}", [Send("ac-setl0m")], [If(f"acsetpg == {GLIDE_PAGE}", [Send("ac-setl0g")], [
                If(f"acsetpg >= {SHAPE_PAGE0}", [Send("ac-setl0h")], [Send("ac-setl0q")])])])])])])
    Line("ac-setl0s", "list $1 $2 $3/$4", [("s", "acsgrp[int(acsetpg)]", [g for g, _ in SETUP_GROUPS]),
                                            ("s", "acsetpg", SETUP_NAMES), ("f", "acspos[int(acsetpg)]"),
                                            ("f", "acscnt[int(acsetpg)]")], "ac-sett0")(c)
    Line("ac-setl0c", "list CHORD  key $1 $2", [("s", "int(actonic) % 12", NOTE_NAMES),
                                                ("s", "acsci", [n for n, _ in SCALES])], "ac-sett0")(c)
    Line("ac-setl0q", "list $1  aux: back", [("s", f"acsetpg - {LAYER_PAGE0}", QUICK_NAMES[1:INPUT_PAGE - NSET + 1])],
         "ac-sett0")(c)
    c.c(c.m(c.recv("ac-setl0g"), "list GLIDE  aux: back"), 0, c.obj("s ac-sett0"), 0)
    Line("ac-setl0m", "list $1  aux: back", [("s", f"acsetpg - {MIRROR0}", [n for n, _ in MIRRORS])], "ac-sett0")(c)
    Line("ac-setl0h", "list $1 shape", [("s", f"acsetpg - {SHAPE_PAGE0}", [n for n, *_ in LAYER_PAGES])], "ac-sett0")(c)
    # page-dependent rows: a Line per page and row, chosen by the page
    quick = quick_pages()
    for k, *rows in setup_rows():     # a subpatch per row, and per 8 pages (Pd connects a small window faster)
        rows = rows + [qr[k - 1] for _, qr in quick]
        rc = Canvas(f"setup-row{k}", w=2600)
        c.sub(rc)
        s = rc.ch(rc.recv(f"ac-setl{k}"), "expr acsetpg", "sel " + " ".join(str(j) for j in range(NALL)))
        for j in range(len(rows)):
            rc.c(rc.to((s, j), "t b"), 0, rc.obj(f"s ac-setl{k}p{j}"), 0)
        for j0 in range(0, len(rows), 8):
            pc = Canvas(f"setup-row{k}-{j0 // 8 + 1}", w=2600)
            rc.sub(pc)
            for j, (ln, parts) in list(enumerate(rows))[j0:j0 + 8]:
                if parts:
                    Line(f"ac-setl{k}p{j}", ln, parts, f"ac-sett{k}")(pc)
                else:
                    pc.c(pc.m(pc.recv(f"ac-setl{k}p{j}"), ln), 0, pc.obj(f"s ac-sett{k}"), 0)
    for k in range(5):
        gated_text(c, f"ac-sett{k}", "acsetup", 0, 2 + k * 12)
    # aux tap in SETUP: the other page
    return c


def cpu_guard():
    c = Canvas("cpu-guard", w=1800)
    c.comment("CPU guard: Pd's load = CPU time / logical time, each second. Above 78 % the piece gets lighter "
              "(1: cloud and atmosphere off, 2: textures and pad character off, 3: auto-vocoder off); below 50 % "
              "for 20 s it steps back. SETUP CPU can turn the guard off. In a batch (offline) run the load reads near 0. acloadtest overrides "
              "it for tests.")
    met = c.obj("metro 1000")
    c.c(c.to(c.recv("ac-init"), "delay 3000"), 0, met, 0)
    # right to left: elapsed logical time, elapsed CPU time (-> the load), then both restart
    tb = c.to(met, "t b b b b")
    ct, tm = c.obj("cputime"), c.obj("timer")
    pk = c.obj("pack f f")
    c.c(tb, 3, tm, 1)
    c.c(tm, 0, pk, 1)
    c.c(tb, 2, ct, 1)
    c.c(ct, 0, pk, 0)
    c.c(tb, 1, ct, 0)
    c.c(tb, 0, tm, 0)
    up = c.ch(pk, "expr $f1/max(1, $f2)", "t b f")
    c.c(up, 1, c.obj("v acldraw"), 0)
    run_steps(c, (up, 0), [V("acload", "max(acloadtest, 0.6*acload + 0.4*acldraw)"), Call("ac-cpucheck")])
    c.col()
    proc(c, "ac-cpucheck", [
        If("acguard % 2 && acload > 0.78 && acshed < 3 && acnow - acshedt > 4000", [
            X("acshed + 1; acnow", "v acshed", "v acshedt"), Call("ac-layers"), Call("ac-inputupd"),
            Toast("CPU high - lighter"),
        ]),
        If("acload < 0.5 && acshed > 0 && acnow - acshedt > 20000", [
            X("acshed - 1; acnow", "v acshed", "v acshedt"), Call("ac-layers"), Call("ac-inputupd"),
        ]),
        If(f"acsetup && acsetpg == {SETUP_NAMES.index('CPU')}", [Call("ac-oledsetup")]),
    ])
    return c

