"""The fan-out check: a control outlet wired to two or more hot inlets fires them in an order Pd does not
promise, so the generator uses one [t ...] instead (README: "Pd fan-out order is undefined: use one trigger").

    python3 fanout.py [patchdir]            list every fan-out in the built patch (default ../patches/Amble)
    python3 fanout.py --update [patchdir]   write the current ones to fanout_known.txt (the accepted list)

gen.py runs check() after each build and stops it if a fan-out appears that fanout_known.txt does not list, so
new code can't add one; the known ones are older and are fixed (or shown harmless) one by one.

What counts: a control outlet (not a signal one) with two or more connections into hot inlets - inlet 0 of an
object or message box, any inlet of a subpatch or an abstraction, the left inlet of [snapshot~]. Signal objects'
inlets (an osc~'s frequency, a line~'s target) only take a value and are not counted. One idiom is harmless and
skipped: a counter's [+ n] whose only output goes back into the cold inlet of the object that fanned out (pdlib's
Loop: [f] -> [+ 1] -> [f]'s right inlet, and [f] -> the loop body).

Branches that cannot affect each other are skipped too: each target's branch is followed downstream (through
control connections, up to signal objects and the canvas's edges), and the fan-out counts only when two branches
meet again, or one branch does something whose reach can't be seen from the canvas (a send, an outlet, a
subpatch) while another does anything, or one stores into a name ([v], a table, a message to an array) that
another reads ([v], [expr] on an ac... value, a table read) or stores into. Stores into different names, with
nothing reading between them, are left alone (the defaults at start-up).

A fan-out is named by its canvas path, the source box and the target boxes (indices change with every build,
these don't), and counted, since many canvases are built alike."""
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KNOWN = os.path.join(HERE, "fanout_known.txt")
CONTROL_TILDE = {"env~", "snapshot~", "sigmund~", "bonk~", "fiddle~", "threshold~", "tabplay~", "readsf~"}
HOT_TILDE = {"snapshot~"}          # (its left inlet: a bang there outputs a value)
BOX = ("#X obj", "#X msg", "#X floatatom", "#X symbolatom", "#X listbox", "#X text")


def _statements(text):
    return [s.strip() for s in re.split(r"(?<!\\);\s*\n", text) if s.strip()]


def _cls(box):
    kind, txt = box
    if kind != "obj":
        return kind
    return txt.split(" ")[0] if txt else ""


def _canvases(path, abstractions):
    """yield (canvas path, boxes [(kind, text)], connections [(src, outlet, dst, inlet)]) for one .pd file"""
    stack = []
    for s in _statements(open(path).read()):
        if s.startswith("#N canvas"):
            stack.append({"boxes": [], "conns": [], "name": ""})
        elif s.startswith("#X restore"):
            done = stack.pop()
            parts = s.split(" ", 4)
            name = parts[4] if len(parts) > 4 else "pd"
            done["name"] = name
            yield done
            if stack:
                stack[-1]["boxes"].append(("sub", name))
        elif s.startswith("#X connect"):
            a = s.split()
            stack[-1]["conns"].append((int(a[2]), int(a[3]), int(a[4]), int(a[5])))
        elif s.startswith(BOX):
            parts = s.split(" ", 4)
            kind = parts[1]
            txt = re.sub(r", f \d+$", "", parts[4]) if len(parts) > 4 else ""
            if kind == "obj" and txt.split(" ")[0] in abstractions:
                kind = "abs"
            stack[-1]["boxes"].append((kind, txt))
        elif s.startswith("#X") and not s.startswith(("#X coords", "#X declare", "#X array")):
            pass
    while stack:                          # the top canvas has no restore
        done = stack.pop()
        done["name"] = os.path.basename(path)
        yield done


def _hot(box, inlet):
    kind = box[0]
    if kind in ("sub", "abs"):
        return True
    if kind == "text":
        return False
    c = _cls(box)
    if c.endswith("~"):
        return c in HOT_TILDE and inlet == 0
    return inlet == 0


def _signal_out(box):
    c = _cls(box)
    return box[0] == "obj" and c.endswith("~") and c not in CONTROL_TILDE


ACTIVE = {"s", "send", "outlet", "s~", "throw~", "tabsend~", "writesf~", "soundfiler", "text"}


def _touches(box):
    """(writes, reads, active) of one box: the names it stores into, the names it reads, and whether it does
    something whose reach can't be seen from here (a send, an outlet, a subpatch, a message to a receiver)"""
    kind, txt = box
    if kind in ("sub", "abs"):
        return set(), set(), True
    if kind == "msg":
        if "\\;" not in txt and not txt.lstrip().startswith(";"):
            return set(), set(), False
        names = set(re.findall(r"\\;\s*([\w$-]+)", txt))
        return names, set(), False            # (a message to arrays or values: stores into those names)
    c, args = _cls(box), txt.split(" ")[1:]
    if c in ("v", "value") and args:
        return {args[0]}, {args[0]}, False
    if c in ("array", "tabwrite") and args:
        name = args[1] if c == "array" and len(args) > 1 else args[0]
        if c == "array" and args[0] in ("get", "size"):
            return set(), {name}, False
        return {name}, set(), False
    if c in ("tabread", "tabread4") and args:
        return set(), {args[0]}, False
    if c.startswith("expr"):
        return set(), set(re.findall(r"(?<![$\\\w])(ac\w+)", txt)), False
    return set(), set(), c in ACTIVE


def _branch(boxes, out, start):
    """every box a control message from start can reach on this canvas (a signal object ends the walk)"""
    seen, todo = set(), [start]
    while todo:
        b = todo.pop()
        if b in seen:
            continue
        seen.add(b)
        if _signal_out(boxes[b]) or boxes[b][0] in ("sub", "abs"):
            continue
        for (src, _o), dsts in out.items():
            if src == b:
                todo.extend(d for d, _ in dsts)
    return seen


def _entangled(boxes, out, targets):
    """True if the branches from these targets can see each other's order: they meet again; one does something
    whose reach can't be seen (a send, an outlet, a subpatch) while another does anything; or one stores into a
    name another reads or stores"""
    branches = [_branch(boxes, out, t) for t in targets]
    info = []
    for br in branches:
        w, r, act = set(), set(), False
        for b in br:
            bw, brd, ba = _touches(boxes[b])
            w |= bw
            r |= brd
            act = act or ba
        info.append((w, r, act))
    for i in range(len(branches)):
        for j in range(len(branches)):
            if i >= j:
                continue
            if branches[i] & branches[j]:
                return True
            (wi, ri, ai), (wj, rj, aj) = info[i], info[j]
            if (ai and (aj or wj or rj)) or (aj and (wi or ri)):
                return True
            if wi & (wj | rj) or wj & ri:
                return True
    return False


def _short(box):
    t = (box[1] or box[0]).strip()
    return t if len(t) <= 60 else t[:57] + "..."


def scan(patchdir):
    """every fan-out in the patch, as a Counter of names"""
    files = sorted(f for f in os.listdir(patchdir) if f.endswith(".pd"))
    abstractions = {f[:-3] for f in files}
    found = collections.Counter()
    for f in files:
        for cv in _canvases(os.path.join(patchdir, f), abstractions):
            boxes, out = cv["boxes"], collections.defaultdict(list)
            for src, o, dst, i in cv["conns"]:
                out[(src, o)].append((dst, i))
            for (src, o), dsts in out.items():
                if _signal_out(boxes[src]):
                    continue
                hot = [(d, i) for d, i in dsts if _hot(boxes[d], i)]
                # the counter idiom: a target whose every output lands in a cold inlet of the source
                hot = [(d, i) for d, i in hot
                       if not (out.get((d, 0)) and all(dd == src and ii > 0 for dd, ii in out[(d, 0)])
                               and all(k == 0 for s2, k in out if s2 == d))]
                if len(hot) > 1 and _entangled(boxes, out, [d for d, _ in hot]):
                    tgt = " | ".join(sorted(f"{_short(boxes[d])}:{i}" for d, i in hot))
                    found[f"{f} / {cv['name']} :: [{_short(boxes[src])}]:{o} -> {tgt}"] += 1
    return found


def _known():
    if not os.path.exists(KNOWN):
        return collections.Counter()
    k = collections.Counter()
    for line in open(KNOWN):
        line = line.rstrip("\n")
        if line and not line.startswith("#"):
            n, name = line.split(" ", 1)
            k[name] = int(n)
    return k


def write_known(found):
    with open(KNOWN, "w") as fh:
        fh.write("# fan-outs accepted for now (tools/fanout.py): count, then file / canvas :: [source]:outlet -> "
                 "targets.\n# New code must not add one (use one [t ...]); fix these and refresh with "
                 "python3 fanout.py --update\n")
        for name in sorted(found):
            fh.write(f"{found[name]} {name}\n")


def check(patchdir):
    """raise if the patch has a fan-out (or more of one) that fanout_known.txt does not list"""
    found, known = scan(patchdir), _known()
    new = {n: c - known[n] for n, c in found.items() if c > known[n]}
    if new:
        lines = "\n".join(f"  {c} x {n}" for n, c in sorted(new.items()))
        raise SystemExit(f"fan-out: a control outlet feeds two or more hot inlets (their order is undefined in "
                         f"Pd) - put one [t ...] in front, in the order you need:\n{lines}\n"
                         f"(tools/fanout.py explains the check; fanout_known.txt lists the older ones)")
    gone = sum(c - found[n] for n, c in known.items() if c > found[n])
    if gone:
        print(f"fan-out: {gone} known fan-out(s) are gone - run python3 tools/fanout.py --update to drop them "
              f"from the list")
    return found


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--update"]
    d = args[0] if args else os.path.join(HERE, "..", "patches", "Amble")
    found = scan(d)
    if "--update" in sys.argv:
        write_known(found)
        print(f"{sum(found.values())} fan-out(s) written to {KNOWN}")
    else:
        for name, c in sorted(found.items()):
            print(f"{c} x {name}")
        print(f"{sum(found.values())} fan-out(s)")
