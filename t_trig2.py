"""Trigonometry extras: sine rule (incl. ambiguous case), special angles and exact values, trig equations,
identities / compound and double angles, triangle area, 3-D problems."""
import math
import re
from fractions import Fraction

import topics
from tcommon import UErr, num, field, select, guard, _ok, _fail
from log_core import LogErr
from t_conics import _plt, _halo, _b64, BLUE, RED, GREEN, ORANGE, PURPLE, GREY, INK
import surd_solvers

MINUS = "&minus;"
DEG = "&deg;"


def HL(s):
    return f"<span class='hl'>{s}</span>"


def wrap(fn):
    def w(d):
        try:
            return fn(d)
        except (UErr, LogErr) as e:
            return _fail(str(e))
    w.__name__ = fn.__name__
    return w


def dc(x, p=2):
    s = f"{x:.{p}f}".rstrip("0").rstrip(".")
    return ("0" if s in ("", "-0") else s).replace("-", MINUS)


def fnum(s, label, lo=None, hi=None, strict=True):
    v = float(num(s, label))
    if lo is not None and (v < lo or (strict and v == lo and lo == 0)):
        raise UErr(f"{label} must be bigger than {dc(lo) if lo else '0'}.")
    if hi is not None and v >= hi:
        raise UErr(f"{label} must be less than {dc(hi)}.")
    return v


def S(a):
    return math.sin(math.radians(a))


def Cc(a):
    return math.cos(math.radians(a))


def T(a):
    return math.tan(math.radians(a))


def _out(steps, text, img):
    return _ok(steps, {"image": img, "text": text})


# ----------------------------------------------------------------- triangle drawing
def draw_tri(ax, A, B, C, a, b, c, title="", marks=None, hl=None):
    """angles in degrees; B at origin, C at (a,0), A above"""
    Bp = (0.0, 0.0)
    Cp = (a, 0.0)
    Ap = (c * Cc(B), c * S(B))
    xs = [Bp[0], Cp[0], Ap[0], Bp[0]]
    ys = [Bp[1], Cp[1], Ap[1], Bp[1]]
    ax.fill(xs, ys, color=BLUE, alpha=0.10)
    ax.plot(xs, ys, "-", color=BLUE, lw=2.2)
    cx, cy = (Ap[0] + Bp[0] + Cp[0]) / 3, (Ap[1] + Bp[1] + Cp[1]) / 3

    def out(p, k=0.09):
        vx, vy = p[0] - cx, p[1] - cy
        n = math.hypot(vx, vy) or 1
        s = max(a, b, c) * k
        return p[0] + vx / n * s, p[1] + vy / n * s

    for nm_, p in (("A", Ap), ("B", Bp), ("C", Cp)):
        q = out(p)
        ax.text(q[0], q[1], nm_, fontsize=13, fontweight="bold", color=INK, ha="center", va="center", path_effects=_halo())

    def mid(p, q, k=0.06):
        m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        vx, vy = m[0] - cx, m[1] - cy
        n = math.hypot(vx, vy) or 1
        s = max(a, b, c) * k
        return m[0] + vx / n * s, m[1] + vy / n * s

    for lab, (p, q), col in (("a", (Bp, Cp), RED), ("b", (Cp, Ap), RED), ("c", (Ap, Bp), RED)):
        val = {"a": a, "b": b, "c": c}[lab]
        m = mid(p, q)
        t = marks.get(lab) if marks else None
        ax.text(m[0], m[1], f"{lab} = {t if t else dc(val, 2).replace(MINUS, '-')}", fontsize=9, color=col if not (hl and lab in hl) else GREEN, ha="center", va="center", fontweight="bold", path_effects=_halo())
    for nm_, p, ang, other1, other2 in (("A", Ap, A, Bp, Cp), ("B", Bp, B, Cp, Ap), ("C", Cp, C, Ap, Bp)):
        v1 = (other1[0] - p[0], other1[1] - p[1])
        v2 = (other2[0] - p[0], other2[1] - p[1])
        a1 = math.degrees(math.atan2(v1[1], v1[0]))
        a2 = math.degrees(math.atan2(v2[1], v2[0]))
        lo, hi = sorted((a1, a2))
        if hi - lo > 180:
            lo, hi = hi, lo + 360
        from matplotlib.patches import Arc
        r = max(a, b, c) * 0.1
        ax.add_patch(Arc(p, 2 * r, 2 * r, theta1=lo, theta2=hi, color=ORANGE, lw=1.6))
        mm = math.radians((lo + hi) / 2)
        t = marks.get(nm_) if marks else None
        ax.text(p[0] + r * 1.9 * math.cos(mm), p[1] + r * 1.9 * math.sin(mm), (t if t else dc(ang, 1).replace(MINUS, "-")) + "°", fontsize=8, color=ORANGE, ha="center", va="center", path_effects=_halo(), fontweight="bold")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=10, color=INK)
    ax.margins(0.12)


def tri_sides(A, B, C, a):
    b = a * S(B) / S(A)
    c = a * S(C) / S(A)
    return b, c


# ----------------------------------------------------------------- sine rule
@wrap
def sine_rule(d):
    plt = _plt()
    mode = d.get("mode", "aas")
    steps = ["<b>The sine rule:</b> a/sin A = b/sin B = c/sin C, where a is the side opposite angle A, b opposite B and c opposite C. "
             "It lets you find a side from an angle pair, or an angle from a side pair, when you know <b>one side and its opposite angle</b>."]
    if mode == "aas":
        A = fnum(d.get("A"), "Angle A", 0, 180)
        B = fnum(d.get("B"), "Angle B", 0, 180)
        a = fnum(d.get("a"), "Side a", 0)
        if A + B >= 180:
            raise UErr("Angles A and B must add up to less than 180°.")
        C = 180 - A - B
        steps.append(f"<b>Given:</b> A = {dc(A)}{DEG}, B = {dc(B)}{DEG}, side a = {dc(a)} (opposite A).")
        steps.append(f"<b>Step 1 &ndash; third angle:</b> angles in a triangle add up to 180&deg;, so C = 180 &minus; {dc(A)} &minus; {dc(B)} = {HL(dc(C) + DEG)}")
        b, c = tri_sides(A, B, C, a)
        steps.append(f"<b>Step 2 &ndash; side b:</b> b/sin B = a/sin A &rArr; b = a &times; sin B / sin A = {dc(a)} &times; sin {dc(B)}&deg; / sin {dc(A)}&deg; = {dc(a)} &times; {dc(S(B), 4)} / {dc(S(A), 4)} = {HL(dc(b, 2))}")
        steps.append(f"<b>Step 3 &ndash; side c:</b> c = a &times; sin C / sin A = {dc(a)} &times; sin {dc(C)}&deg; / sin {dc(A)}&deg; = {dc(a)} &times; {dc(S(C), 4)} / {dc(S(A), 4)} = {HL(dc(c, 2))}")
        fig, ax = plt.subplots(figsize=(6.2, 4.6))
        draw_tri(ax, A, B, C, a, b, c, "Your triangle")
        res = f"<b>C = {dc(C)}&deg;, b = {dc(b)}, c = {dc(c)}</b>"
        return _out(steps, res, _b64(fig))
    # SSA
    a = fnum(d.get("a"), "Side a", 0)
    b = fnum(d.get("b"), "Side b", 0)
    A = fnum(d.get("A"), "Angle A", 0, 180)
    steps.append(f"<b>Given:</b> side a = {dc(a)}, side b = {dc(b)} and angle A = {dc(A)}{DEG} (A is opposite a). This is the <b>SSA</b> (two sides and a non-included angle) situation, which can have <b>0, 1 or 2 triangles</b>: the <b>ambiguous case</b>.")
    h = b * S(A)
    steps.append(f"<b>Step 1 &ndash; use the sine rule to find B:</b> sin B / b = sin A / a &rArr; sin B = b sin A / a = {dc(b)} &times; sin {dc(A)}&deg; / {dc(a)} = {HL(dc(h / a, 4))}")
    sB = h / a
    if sB > 1 + 1e-12:
        steps.append(f"<b>sin B is bigger than 1, which is impossible</b> (sine is never above 1). Side a = {dc(a)} is too short to reach across: the shortest it can be is the height h = b sin A = {dc(h, 3)}. <b>No triangle exists.</b>")
        fig, ax = plt.subplots(figsize=(6.2, 4.2))
        P0 = (0, 0)
        L = b * 1.0
        ax.plot([0, L], [0, 0], color=GREY, lw=1.5)
        Cx, Cy = b * Cc(A), b * S(A)
        ax.plot([0, Cx], [0, Cy], color=BLUE, lw=2.2)
        ax.plot([Cx, Cx], [0, Cy], "--", color=GREEN, lw=1.5)
        t_ = [i * 2 * math.pi / 100 for i in range(101)]
        ax.plot([Cx + a * math.cos(u) for u in t_], [Cy + a * math.sin(u) for u in t_], color=RED, lw=1.8)
        ax.text(Cx + 0.02 * b, Cy + 0.05 * b, f"circle radius a = {dc(a).replace(MINUS, '-')} does not reach the base", fontsize=8, color=RED)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title("The side a is too short: it cannot meet the base line", fontsize=10)
        return _out(steps, "<b>No triangle exists</b>", _b64(fig))
    if abs(sB - 1) < 1e-9:
        sB = 1.0
    B1 = math.degrees(math.asin(min(1.0, sB)))
    B2 = 180 - B1
    sols = []
    steps.append(f"<b>Step 2 &ndash; two possible angles B:</b> B = sin<sup>&minus;1</sup>({dc(sB, 4)}) = {dc(B1, 2)}&deg;. Because sin(180&deg; &minus; x) = sin x, there is a second angle B = 180&deg; &minus; {dc(B1, 2)}&deg; = {dc(B2, 2)}&deg;.")
    for lab, Bx in (("first", B1), ("second", B2)):
        if lab == "second" and abs(B2 - B1) < 1e-6:
            continue
        ok = A + Bx < 180 - 1e-9
        steps.append(f"<b>Test the {lab} angle B = {dc(Bx, 2)}&deg;:</b> A + B = {dc(A)} + {dc(Bx, 2)} = {dc(A + Bx, 2)}&deg;, which is {'less' if ok else 'not less'} than 180&deg; &rArr; {'<b>valid</b> (a triangle exists)' if ok else '<b>rejected</b> (angles of a triangle must add to less than 180&deg;)'}.")
        if ok:
            Cx_ = 180 - A - Bx
            c = a * S(Cx_) / S(A)
            steps.append(f"&nbsp;&nbsp;C = 180 &minus; {dc(A)} &minus; {dc(Bx, 2)} = {dc(Cx_, 2)}&deg;; &nbsp;c = a sin C / sin A = {dc(a)} &times; sin {dc(Cx_, 2)}&deg; / sin {dc(A)}&deg; = {HL(dc(c, 2))}")
            sols.append((Bx, Cx_, c))
    n = len(sols)
    steps.append(f"<b>Conclusion:</b> there {'is' if n == 1 else 'are'} <b>{n} triangle{'s' if n != 1 else ''}</b>."
                 + (" (When a &ge; b, the angle opposite the longer side is bigger, so only the acute B works.)" if n == 1 and a >= b else ""))
    fig, axs = plt.subplots(1, n, figsize=(6.2 * n * 0.9, 4.4), squeeze=False)
    for i, (Bx, Cx_, c) in enumerate(sols):
        draw_tri(axs[0][i], A, Bx, Cx_, a, b, c, f"Triangle {i + 1}" if n > 1 else "The triangle")
    res = " ; ".join(f"B = {dc(Bx, 1)}&deg;, C = {dc(Cx_, 1)}&deg;, c = {dc(c, 2)}" for Bx, Cx_, c in sols)
    return _out(steps, f"<b>{n} triangle{'s' if n != 1 else ''}: {res}</b>", _b64(fig))


# ----------------------------------------------------------------- special angles
def exact_trig(fn, deg):
    """exact value text of sin/cos/tan of a multiple of 30 or 45 (degrees); returns text or None if undefined"""
    d = deg % 360
    if d % 30 and d % 45:
        raise UErr(f"{deg}° is not one of the special angles (multiples of 30° or 45°), so it has no simple exact value.")
    # reduce to reference angle
    if d <= 90:
        ref, ss, cs = d, 1, 1
    elif d <= 180:
        ref, ss, cs = 180 - d, 1, -1
    elif d <= 270:
        ref, ss, cs = d - 180, -1, -1
    else:
        ref, ss, cs = 360 - d, -1, 1
    sv = {0: "0", 30: "1/2", 45: "sqrt(2)/2", 60: "sqrt(3)/2", 90: "1"}[ref]
    cv = {0: "1", 30: "sqrt(3)/2", 45: "sqrt(2)/2", 60: "1/2", 90: "0"}[ref]
    if fn == "sin":
        return ("-" if ss < 0 and sv != "0" else "") + sv
    if fn == "cos":
        return ("-" if cs < 0 and cv != "0" else "") + cv
    if ref == 90:
        return None
    tv = {0: "0", 30: "sqrt(3)/3", 45: "1", 60: "sqrt(3)"}[ref]
    return ("-" if ss * cs < 0 and tv != "0" else "") + tv


TRIG_TOK = re.compile(r"(sin|cos|tan)\s*(\^\s*2)?\s*\(?\s*(-?\s*\d+)\s*(?:°|deg)?\s*\)?", re.I)


@wrap
def exact_values(d):
    raw = str(d.get("e") or "").strip().replace("−", "-").replace("×", "*").replace("°", "")
    if not raw:
        raise UErr("Type an expression such as  sin 30 + cos 60  or  sin^2 45 + cos^2 45")
    used = []
    errors = []

    def rep(m):
        fn = m.group(1).lower()
        sq = bool(m.group(2))
        ang = int(m.group(3).replace(" ", ""))
        try:
            v = exact_trig(fn, ang)
        except UErr as e:
            errors.append(str(e))
            return "0"
        if v is None:
            errors.append(f"tan {ang}° is undefined (the angle is 90° or 270°).")
            return "0"
        used.append((f"{fn}{'&sup2;' if sq else ''} {ang}&deg;", fn, ang, v))
        return f"({v})" + ("^2" if sq else "")

    sub = TRIG_TOK.sub(rep, raw)
    if errors:
        raise UErr(errors[0])
    if not used:
        raise UErr("I could not find sin, cos or tan of an angle. Write angles in degrees, like sin 30 + cos 60.")
    if re.search(r"[a-zA-Z]", re.sub(r"sqrt", "", sub)):
        raise UErr("I could only read sin, cos and tan of numbers (degrees). Remove other letters.")
    steps = [f"<b>Evaluate exactly:</b> {HL(raw)}. Use the exact values of sin, cos and tan for the special angles 0&deg;, 30&deg;, 45&deg;, 60&deg;, 90&deg;.",
             "<table class='stat-table'><tr><th></th><th>0&deg;</th><th>30&deg;</th><th>45&deg;</th><th>60&deg;</th><th>90&deg;</th></tr>"
             "<tr><td><b>sin</b></td><td>0</td><td>1/2</td><td>&radic;2/2</td><td>&radic;3/2</td><td>1</td></tr>"
             "<tr><td><b>cos</b></td><td>1</td><td>&radic;3/2</td><td>&radic;2/2</td><td>1/2</td><td>0</td></tr>"
             "<tr><td><b>tan</b></td><td>0</td><td>&radic;3/3</td><td>1</td><td>&radic;3</td><td>&mdash;</td></tr></table>"]
    seen = set()
    lines = []
    for label, fn, ang, v in used:
        if (fn, ang) in seen:
            continue
        seen.add((fn, ang))
        pretty = v.replace("sqrt(2)", "&radic;2").replace("sqrt(3)", "&radic;3").replace("-", MINUS)
        why = ""
        if ang % 360 > 90:
            quad = {1: "", 2: "second", 3: "third", 4: "fourth"}[(ang % 360 > 90) + (ang % 360 > 180) + (ang % 360 > 270) + 1]
            why = f" (the angle {ang}&deg; is in the {quad} quadrant: use the acute reference angle and the CAST sign)"
        lines.append(f"{fn} {ang}&deg; = {pretty}{why}")
    steps.append("<b>Replace each trig value by its exact value:</b><br>" + "<br>".join(lines))
    shown = re.sub(r"sqrt\((\d)\)", r"&radic;\1", sub).replace("-", MINUS)
    steps.append(f"<b>The expression becomes:</b> {shown}")
    r = surd_solvers.simplify(sub)
    if not r.get("ok"):
        return _fail(r.get("error") or "Could not simplify.")
    steps += r["steps"][1:]
    return _ok(steps, str(r["result"]))


# ----------------------------------------------------------------- trig equations
def trig_solutions(fn, v, b, c, lo, hi):
    """all theta in [lo, hi] with fn(b*theta + c) = v (degrees); returns sorted unique list and base angle info"""
    if fn in ("sin", "cos") and abs(v) > 1 + 1e-12:
        return []
    u_lo, u_hi = (b * lo + c, b * hi + c) if b > 0 else (b * hi + c, b * lo + c)
    if fn == "sin":
        al = math.degrees(math.asin(max(-1, min(1, v))))
        fam = [(al, 360), (180 - al, 360)]
    elif fn == "cos":
        al = math.degrees(math.acos(max(-1, min(1, v))))
        fam = [(al, 360), (-al, 360)]
    else:
        al = math.degrees(math.atan(v))
        fam = [(al, 180)]
    out = []
    for base, per in fam:
        n0 = math.floor((u_lo - base) / per) - 1
        n1 = math.ceil((u_hi - base) / per) + 1
        for n in range(n0, n1 + 1):
            u = base + per * n
            th = (u - c) / b
            if lo - 1e-9 <= th <= hi + 1e-9:
                out.append(round(th, 6))
    return sorted(set(out))


def _fn_plot(fn, a, b, c, k, lo, hi, sols):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    n = 720
    xs = [lo + (hi - lo) * i / n for i in range(n + 1)]
    ys = []
    for x in xs:
        u = b * x + c
        if fn == "sin":
            y = a * S(u)
        elif fn == "cos":
            y = a * Cc(u)
        else:
            cu = Cc(u)
            y = float("nan") if abs(cu) < 1e-3 else a * T(u)
            if y == y and abs(y) > 6 * max(1, abs(a)):
                y = float("nan")
        ys.append(y)
    ax.plot(xs, ys, color=BLUE, lw=2.2, label="y = " + ("%s" % (dc(a).replace(MINUS, "-") + " " if a != 1 else "") + f"{fn}({'' if b == 1 else dc(b).replace(MINUS, '-')}θ{'' if c == 0 else ('+' if c > 0 else '-') + dc(abs(c))})"))
    ax.axhline(k, color=RED, lw=1.8, ls="--", label=f"y = {dc(k).replace(MINUS, '-')}")
    ax.axhline(0, color=GREY, lw=1)
    for s in sols:
        ax.plot([s], [k], "o", color=ORANGE, ms=8, zorder=5)
        ax.annotate(f"{dc(s, 1).replace(MINUS, '-')}°", (s, k), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=9, fontweight="bold", color=ORANGE, path_effects=_halo())
        ax.plot([s, s], [0, k], ":", color=ORANGE, lw=1)
    ax.set_xlim(lo, hi)
    step = 30 if hi - lo <= 360 else 60
    ax.set_xticks([lo + i * step for i in range(int((hi - lo) / step) + 1)])
    ax.tick_params(labelsize=8)
    ax.grid(True, color="#e2e8f0")
    ax.set_xlabel("θ (degrees)")
    ax.legend(fontsize=8, loc="upper right")
    return _b64(fig)


RANGES = {"0-360": (0, 360), "-180-180": (-180, 180), "0-720": (0, 720), "-360-360": (-360, 360)}


def _cast(fn, v):
    if fn == "sin":
        pos = "1st and 2nd" if v > 0 else "3rd and 4th"
    elif fn == "cos":
        pos = "1st and 4th" if v > 0 else "2nd and 3rd"
    else:
        pos = "1st and 3rd" if v > 0 else "2nd and 4th"
    return pos


def _explain_basic(fn, v, steps):
    """narrate the basic angle for fn(u) = v"""
    if v == 0 and fn in ("sin", "tan"):
        steps.append(f"{fn} u = 0: the basic angle is 0&deg;.")
        return
    ref = math.degrees({"sin": math.asin, "cos": math.acos, "tan": math.atan}[fn](abs(v) if fn != "cos" or True else v)) if abs(v) <= 1 or fn == "tan" else None
    ref = math.degrees({"sin": math.asin, "cos": math.acos, "tan": math.atan}[fn](abs(v)))
    if fn == "cos":
        ref = math.degrees(math.acos(abs(v)))
    steps.append(f"<b>Basic (acute) angle</b> = {fn}<sup>&minus;1</sup>(|{dc(v, 4)}|) = {dc(ref, 2)}&deg;. Ignore the sign for now.")
    steps.append(f"<b>CAST rule:</b> {fn} is {'positive' if v > 0 else 'negative'} in the <b>{_cast(fn, v)}</b> quadrants. So the angles are found by putting the basic angle {dc(ref, 2)}&deg; into those quadrants:"
                 f" 1st quadrant: &theta;; 2nd: 180&deg; &minus; &theta;; 3rd: 180&deg; + &theta;; 4th: 360&deg; &minus; &theta;.")


@wrap
def trig_eq(d):
    fn = d.get("fn", "sin")
    a = fnum(d.get("a", "1"), "Coefficient a") if str(d.get("a", "")).strip() else 1.0
    b = float(num(d.get("b", "1"), "Multiple of the angle b")) if str(d.get("b", "")).strip() else 1.0
    c = float(num(d.get("c", "0"), "Shift")) if str(d.get("c", "")).strip() else 0.0
    k = float(num(d.get("k"), "Right-hand side"))
    if a == 0 or b == 0:
        raise UErr("a and b cannot be 0.")
    lo, hi = RANGES.get(d.get("rng", "0-360"), (0, 360))
    v = k / a
    form = f"{'' if a == 1 else dc(a, 3) + ' '}{fn}({'' if b == 1 else dc(b, 3)}&theta;{'' if c == 0 else (' + ' if c > 0 else ' ' + MINUS + ' ') + dc(abs(c), 3) + DEG}) = {dc(k, 4)}"
    steps = [f"<b>Solve</b> {HL(form)} for {lo}&deg; &le; &theta; &le; {hi}&deg;."]
    if a != 1:
        steps.append(f"<b>Step 1 &ndash; isolate the trig function:</b> divide both sides by {dc(a, 3)}: {fn}({'' if b == 1 else dc(b, 3)}&theta;{'' if c == 0 else ' + ' + dc(c, 3) + DEG if c > 0 else ' ' + MINUS + ' ' + dc(-c, 3) + DEG}) = {dc(v, 4)}")
    if fn in ("sin", "cos") and abs(v) > 1:
        steps.append(f"{fn} can only be between &minus;1 and 1, but we need {dc(v, 4)}. <b>No solution.</b>")
        return _out(steps, "<b>No solution</b>", _fn_plot(fn, a, b, c, k, lo, hi, []))
    ushow = "u" if (b != 1 or c != 0) else "&theta;"
    if b != 1 or c != 0:
        steps.append(f"<b>Step 2 &ndash; call the whole angle u</b> (u = {'' if b == 1 else dc(b, 3)}&theta;{'' if c == 0 else (' + ' if c > 0 else ' ' + MINUS + ' ') + dc(abs(c), 3)}). Because &theta; goes from {lo}&deg; to {hi}&deg;, u goes from {dc(min(b * lo + c, b * hi + c), 3)}&deg; to {dc(max(b * lo + c, b * hi + c), 3)}&deg;: that is <b>more than one turn when |b| &gt; 1</b>, so we need extra solutions.")
    _explain_basic(fn, v, steps)
    ulo, uhi = sorted((b * lo + c, b * hi + c))
    # all u values
    us = []
    if fn == "sin":
        al = math.degrees(math.asin(v))
        fam = [(al, 360), (180 - al, 360)]
    elif fn == "cos":
        al = math.degrees(math.acos(v))
        fam = [(al, 360), (-al, 360)]
    else:
        al = math.degrees(math.atan(v))
        fam = [(al, 180)]
    for base, per in fam:
        for n in range(math.floor((ulo - base) / per) - 1, math.ceil((uhi - base) / per) + 2):
            u = base + per * n
            if ulo - 1e-9 <= u <= uhi + 1e-9:
                us.append(round(u, 6))
    us = sorted(set(us))
    steps.append(f"<b>All values of {ushow} in range</b> (add or subtract {'360&deg;' if fn != 'tan' else '180&deg;'} to find more): " + (", ".join(dc(u, 2) + DEG for u in us) if us else "none"))
    sols = trig_solutions(fn, v, b, c, lo, hi)
    if b != 1 or c != 0:
        lines = []
        for u in sorted(us, key=lambda u: (u - c) / b):
            th = (u - c) / b
            lines.append(f"&theta; = (u{'' if c == 0 else (' &minus; ' + dc(c, 3) if c > 0 else ' + ' + dc(-c, 3))})/{dc(b, 3)} = ({dc(u, 2)}{'' if c == 0 else (' &minus; ' + qd(c) if c > 0 else ' + ' + dc(-c, 3))})/{dc(b, 3)} = {dc(th, 2)}&deg;")
        steps.append("<b>Step 3 &ndash; go back to &theta;</b> (subtract the shift, then divide by the multiple):<br>" + "<br>".join(lines))
    ans = ", ".join(dc(s, 1) + DEG for s in sols) if sols else "no solutions in this range"
    steps.append(f"<b>Answer:</b> &theta; = {HL(ans)}")
    return _out(steps, f"<b>&theta; = {ans}</b>", _fn_plot(fn, a, b, c, k, lo, hi, sols))


def qd(x):
    return dc(x, 3)


@wrap
def trig_quad(d):
    fn = d.get("fn", "sin")
    A = float(num(d.get("A"), "A"))
    B = float(num(d.get("B"), "B"))
    C = float(num(d.get("C"), "C"))
    if A == 0:
        raise UErr("A cannot be 0 (it would not be a quadratic).")
    lo, hi = RANGES.get(d.get("rng", "0-360"), (0, 360))
    steps = [f"<b>Solve</b> {HL(f'{dc(A, 3)} {fn}&sup2;&theta; + {dc(B, 3)} {fn}&theta; + {dc(C, 3)} = 0')} for {lo}&deg; &le; &theta; &le; {hi}&deg;.".replace("+ " + MINUS, "&minus; ")]
    steps.append(f"<b>Step 1 &ndash; treat it as a quadratic.</b> Let y = {fn}&theta;. Then {dc(A, 3)}y&sup2; + {dc(B, 3)}y + {dc(C, 3)} = 0. Solve for y by factorising or the formula.")
    disc = B * B - 4 * A * C
    steps.append(f"Discriminant = {dc(B, 3)}&sup2; &minus; 4({dc(A, 3)})({dc(C, 3)}) = {dc(disc, 4)}")
    if disc < 0:
        steps.append("The discriminant is negative: no real y, so <b>no solution</b>.")
        return _ok(steps, "<b>No solution</b>")
    ys = sorted({(-B - math.sqrt(disc)) / (2 * A), (-B + math.sqrt(disc)) / (2 * A)})
    steps.append("y = " + " or ".join(dc(y, 4) for y in ys))
    allsol = []
    for y in ys:
        steps.append(f"<b>Now solve {fn}&theta; = {dc(y, 4)}:</b>")
        if fn in ("sin", "cos") and abs(y) > 1 + 1e-12:
            steps.append(f"&nbsp;&nbsp;{fn}&theta; cannot be {dc(y, 4)} (it must be between &minus;1 and 1). <b>Reject.</b>")
            continue
        _explain_basic(fn, y, steps)
        s = trig_solutions(fn, y, 1, 0, lo, hi)
        steps.append(f"&nbsp;&nbsp;&theta; = {', '.join(dc(x, 1) + DEG for x in s)}")
        allsol += s
    allsol = sorted(set(allsol))
    ans = ", ".join(dc(s, 1) + DEG for s in allsol) if allsol else "no solutions"
    steps.append(f"<b>Answer:</b> &theta; = {HL(ans)}")
    plt = _plt()
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    xs = [lo + (hi - lo) * i / 720 for i in range(721)]
    f = {"sin": S, "cos": Cc}.get(fn)
    yv = [A * (f(x) ** 2) + B * f(x) + C for x in xs] if f else [A * T(x) ** 2 + B * T(x) + C if abs(Cc(x)) > 1e-2 else float("nan") for x in xs]
    if not f:
        yv = [v if v == v and abs(v) < 15 else float("nan") for v in yv]
    ax.plot(xs, yv, color=BLUE, lw=2.2)
    ax.axhline(0, color=RED, ls="--", lw=1.6)
    for s in allsol:
        ax.plot([s], [0], "o", color=ORANGE, ms=8, zorder=5)
        ax.annotate(f"{dc(s, 1).replace(MINUS, '-')}°", (s, 0), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=9, color=ORANGE, fontweight="bold", path_effects=_halo())
    ax.set_xlim(lo, hi)
    ax.set_xticks([lo + i * 30 for i in range(int((hi - lo) / 30) + 1)] if hi - lo <= 360 else [lo + i * 60 for i in range(int((hi - lo) / 60) + 1)])
    ax.tick_params(labelsize=8)
    ax.grid(True, color="#e2e8f0")
    ax.set_xlabel("θ (degrees)")
    ax.set_title("Where the quadratic expression crosses zero", fontsize=10)
    return _out(steps, f"<b>&theta; = {ans}</b>", _b64(fig))


# ----------------------------------------------------------------- compound & double angles
def _ex(fn, ang):
    v = exact_trig(fn, int(ang))
    if v is None:
        raise UErr(f"{fn} {int(ang)}° is undefined.")
    return v


def _pretty(v):
    return v.replace("sqrt(2)", "&radic;2").replace("sqrt(3)", "&radic;3").replace("-", MINUS)


def _is_int(x):
    return abs(x - round(x)) < 1e-9


@wrap
def compound(d):
    mode = d.get("mode", "comp")
    if mode == "comp":
        fn = d.get("fn", "sin")
        A = float(num(d.get("A"), "Angle A"))
        B = float(num(d.get("B"), "Angle B"))
        op = d.get("op", "+")
        sg = 1 if op == "+" else -1
        w = "+" if sg > 0 else MINUS
        sigma = "+" if sg > 0 else "&minus;"
        steps = [f"<b>Find</b> {HL(fn + '(' + dc(A) + DEG + ' ' + w + ' ' + dc(B) + DEG + ')')} <b>using the compound angle formula.</b>"]
        if fn == "sin":
            steps.append(f"<b>Formula:</b> sin(A {sigma} B) = sin A cos B {sigma} cos A sin B")
            val = S(A + sg * B)
        elif fn == "cos":
            steps.append(f"<b>Formula:</b> cos(A {sigma} B) = cos A cos B {'&minus;' if sg > 0 else '+'} sin A sin B (<i>note the sign flips for cos</i>)")
            val = Cc(A + sg * B)
        else:
            steps.append(f"<b>Formula:</b> tan(A {sigma} B) = (tan A {sigma} tan B) / (1 {'&minus;' if sg > 0 else '+'} tan A tan B)")
            val = T(A + sg * B)
        special = _is_int(A) and _is_int(B) and all((int(x) % 30 == 0 or int(x) % 45 == 0) for x in (A, B))
        expr = None
        if special:
            try:
                a_, b_ = int(A), int(B)
                if fn == "sin":
                    expr = f"({_ex('sin', a_)})*({_ex('cos', b_)}) {'+' if sg > 0 else '-'} ({_ex('cos', a_)})*({_ex('sin', b_)})"
                elif fn == "cos":
                    expr = f"({_ex('cos', a_)})*({_ex('cos', b_)}) {'-' if sg > 0 else '+'} ({_ex('sin', a_)})*({_ex('sin', b_)})"
                else:
                    ta, tb = _ex('tan', a_), _ex('tan', b_)
                    expr = f"(({ta}) {'+' if sg > 0 else '-'} ({tb}))/(1 {'-' if sg > 0 else '+'} ({ta})*({tb}))"
            except UErr:
                expr = None
        if expr:
            steps.append("<b>Both angles are special angles, so use exact values:</b> " + _pretty(expr.replace("*", " &times; ")))
            r = surd_solvers.simplify(expr)
            if r.get("ok"):
                steps += r["steps"][1:]
                steps.append(f"<b>Check with the angle {dc(A + sg * B)}&deg; directly:</b> {fn} {dc(A + sg * B)}&deg; = {dc(val, 5)}. &check;")
                return _ok(steps, str(r["result"]))
        steps.append(f"<b>Using decimals:</b> {fn} {dc(A + sg * B)}&deg; = {HL(dc(val, 5))} (the angles are not both special angles, so no neat surd form)")
        return _ok(steps, f"<b>{fn}({dc(A)}&deg; {w} {dc(B)}&deg;) = {dc(val, 4)}</b>")
    # double angle from a given ratio
    fn = d.get("fn", "sin")
    val = Fraction(num(d.get("v"), "The value"))
    quad = int(d.get("q", "1"))
    if fn in ("sin", "cos") and abs(val) > 1:
        raise UErr(f"{fn} A cannot be bigger than 1 or smaller than &minus;1.")
    signs = {1: (1, 1), 2: (1, -1), 3: (-1, -1), 4: (-1, 1)}[quad]   # sin sign, cos sign
    steps = [f"<b>Given {fn} A = {q(val)}, with A in the {['first', 'second', 'third', 'fourth'][quad - 1]} quadrant.</b> Find sin 2A, cos 2A and tan 2A."]
    # build a right triangle: opp, adj, hyp (positive) -> exact surd text
    if fn == "sin":
        s_ = val
        c2 = 1 - s_ * s_
        cabs = c2
        if signs[0] * (1 if s_ >= 0 else -1) < 0 and s_ != 0:
            raise UErr("The sign of sin A does not match the quadrant (sin is positive in the 1st and 2nd quadrants, negative in the 3rd and 4th).")
        sv, cv = s_, ("sq", c2)
    elif fn == "cos":
        c_ = val
        if signs[1] * (1 if c_ >= 0 else -1) < 0 and c_ != 0:
            raise UErr("The sign of cos A does not match the quadrant (cos is positive in the 1st and 4th, negative in the 2nd and 3rd).")
        sv, cv = ("sq", 1 - c_ * c_), c_
    else:
        t_ = val
        if signs[0] * signs[1] * (1 if t_ >= 0 else -1) < 0 and t_ != 0:
            raise UErr("The sign of tan A does not match the quadrant (tan is positive in the 1st and 3rd, negative in the 2nd and 4th).")
        # sin = t/sqrt(1+t^2) in magnitude
        sv, cv = ("tan_s", t_), ("tan_c", t_)
    # numeric/exact values as (coef Fraction, radicand int)
    def sqf(qv):
        qv = Fraction(qv)
        n_ = qv.numerator * qv.denominator
        dd = qv.denominator
        s__, r__ = 1, n_
        k_ = 2
        while k_ * k_ <= r__:
            while r__ % (k_ * k_) == 0:
                r__ //= k_ * k_
                s__ *= k_
            k_ += 1
        return Fraction(s__, dd), r__

    def ex_from(x, sign, kind):
        if isinstance(x, Fraction):
            return (x, 1)
        if x[0] == "sq":
            co, r_ = sqf(x[1])
            return (sign * co, r_)
        if x[0] == "tan_s":
            t0 = x[1]
            co, r_ = sqf(1 / (1 + t0 * t0))
            return (signs[0] * co, r_)
        co, r_ = sqf(1 / (1 + x[1] * x[1]))
        return (signs[1] * co, r_)

    sA = ex_from(sv, signs[0], "s")
    cA = ex_from(cv, signs[1], "c")

    def tx(e):
        co, r_ = e
        if r_ == 1:
            return q(co)
        mag = abs(co)
        body = ("" if mag == 1 else (str(mag.numerator) if mag.denominator == 1 else f"{mag.numerator}")) + f"&radic;{r_}" + ("" if mag.denominator == 1 else f"/{mag.denominator}")
        return (MINUS if co < 0 else "") + body

    def mul(e1, e2):
        co = e1[0] * e2[0]
        r_ = e1[1] * e2[1]
        s__ = 1
        k_ = 2
        while k_ * k_ <= r_:
            while r_ % (k_ * k_) == 0:
                r_ //= k_ * k_
                s__ *= k_
            k_ += 1
        return (co * s__, r_)

    sA_f, cA_f = float(sA[0]) * math.sqrt(sA[1]), float(cA[0]) * math.sqrt(cA[1])
    steps.append(f"<b>Step 1 &ndash; find sin A and cos A</b> (use sin<sup>2</sup>A + cos<sup>2</sup>A = 1, or a right-angled triangle, and the CAST signs): sin A = {HL(tx(sA))}, cos A = {HL(tx(cA))}")
    s2 = mul((Fraction(2), 1), mul(sA, cA))
    steps.append(f"<b>sin 2A</b> = 2 sin A cos A = 2 &times; ({tx(sA)}) &times; ({tx(cA)}) = {HL(tx(s2))}")
    c2_ = cA_f * cA_f - sA_f * sA_f
    c2e = mul(cA, cA)
    s2e = mul(sA, sA)
    c2v = c2e[0] - s2e[0]
    steps.append(f"<b>cos 2A</b> = cos<sup>2</sup>A &minus; sin<sup>2</sup>A = ({tx(cA)})<sup>2</sup> &minus; ({tx(sA)})<sup>2</sup> = {q(c2e[0])} &minus; {q(s2e[0])} = {HL(q(c2v))} &nbsp;(also = 1 &minus; 2sin<sup>2</sup>A = 2cos<sup>2</sup>A &minus; 1)")
    if c2v == 0:
        steps.append("<b>tan 2A</b> = sin 2A / cos 2A, but cos 2A = 0, so tan 2A is <b>undefined</b>.")
        tan2 = None
    else:
        co, r_ = s2
        tan2 = (co / c2v, r_)
        steps.append(f"<b>tan 2A</b> = sin 2A / cos 2A = ({tx(s2)})/({q(c2v)}) = {HL(tx(tan2))}")
    steps.append(f"<i>Check with decimals: A = {dc(math.degrees(math.atan2(sA_f, cA_f)) % 360, 2)}&deg;, 2A = {dc((2 * math.degrees(math.atan2(sA_f, cA_f))) % 360, 2)}&deg;, sin 2A = {dc(2 * sA_f * cA_f, 4)}, cos 2A = {dc(c2_, 4)}.</i>")
    return _ok(steps, f"<b>sin 2A = {tx(s2)}, cos 2A = {q(c2v)}, tan 2A = {tx(tan2) if tan2 else 'undefined'}</b>")


def q(x):
    x = Fraction(x)
    return (str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}").replace("-", MINUS)


# ----------------------------------------------------------------- identity checker
_ALLOWED = {"sin", "cos", "tan", "sec", "cosec", "csc", "cot", "sqrt", "pi", "x"}


def _prep(expr):
    s = str(expr or "").strip().lower().replace("θ", "x").replace("−", "-").replace("×", "*").replace("°", "").replace("÷", "/").replace("t", "t")
    s = s.replace("theta", "x")
    if not s:
        raise UErr("Please type both sides of the identity.")
    if len(s) > 120 or not re.fullmatch(r"[a-z0-9+\-*/^().\s]+", s):
        raise UErr("Use only numbers, x, + - * / ^, brackets and sin, cos, tan, sec, cosec, cot.")
    s = re.sub(r"(sin|cos|tan|sec|cosec|csc|cot)\s*\^\s*(\d+)\s*\(?\s*(x|\d+(?:\.\d+)?)\s*\)?", r"((\1(\3))^\2)", s)
    s = re.sub(r"(sin|cos|tan|sec|cosec|csc|cot)\s+(x|\d+(?:\.\d+)?)", r"\1(\2)", s)
    s = re.sub(r"(sin|cos|tan|sec|cosec|csc|cot)\s*(\d*x\b|\d+)", lambda m: f"{m.group(1)}({m.group(2)})", s) if False else s
    for tok in re.findall(r"[a-z]+", s):
        if tok not in _ALLOWED:
            raise UErr(f"I do not understand '{tok}'. Use sin, cos, tan, sec, cosec, cot and the letter x.")
    s = re.sub(r"(\d)\s*(?=[a-z(])", r"\1*", s)
    s = re.sub(r"\)\s*(?=[\da-z(])", ")*", s)
    s = re.sub(r"\bx\s*(?=\(|\d|[a-z])", "x*", s)
    s = re.sub(r"(?<=[a-z0-9)])\s+(?=[a-z0-9(])", "*", s)
    s = s.replace("^", "**")
    # function names must be followed by ( : else add
    return s


def _ev(code, xdeg):
    env = {
        "sin": lambda a: math.sin(math.radians(a)), "cos": lambda a: math.cos(math.radians(a)), "tan": lambda a: math.tan(math.radians(a)),
        "sec": lambda a: 1 / math.cos(math.radians(a)), "cosec": lambda a: 1 / math.sin(math.radians(a)), "csc": lambda a: 1 / math.sin(math.radians(a)),
        "cot": lambda a: 1 / math.tan(math.radians(a)), "sqrt": math.sqrt, "pi": math.pi, "x": xdeg,
    }
    return eval(code, {"__builtins__": {}}, env)


@wrap
def identity(d):
    l, r = str(d.get("l") or ""), str(d.get("r") or "")
    cl, cr = _prep(l), _prep(r)
    try:
        c1, c2 = compile(cl, "l", "eval"), compile(cr, "r", "eval")
    except SyntaxError:
        raise UErr("I could not read one side. Write functions with brackets, like sin(x), and use * for multiplication.")
    angles = [7, 19, 33, 48, 62, 77, 101, 123, 151, 187, 214, 256, 301, 342]
    rows = []
    bad = None
    good = 0
    for a in angles:
        try:
            v1, v2 = _ev(c1, a), _ev(c2, a)
        except (ZeroDivisionError, ValueError, OverflowError, NameError, TypeError):
            continue
        good += 1
        okk = abs(v1 - v2) <= 1e-9 * max(1, abs(v1), abs(v2))
        rows.append((a, v1, v2, okk))
        if not okk and bad is None:
            bad = (a, v1, v2)
    if good < 4:
        raise UErr("I could not evaluate these expressions at enough angles. Check the brackets and function names.")
    steps = [f"<b>Test whether</b> {HL(l.strip() + ' = ' + r.strip())} <b>is an identity</b> (true for <i>every</i> angle). I try many different angles and compare the left side (LHS) with the right side (RHS).",
             "<table class='stat-table'><tr><th>x</th><th>LHS</th><th>RHS</th><th>Equal?</th></tr>" +
             "".join(f"<tr><td>{a}&deg;</td><td>{dc(v1, 5)}</td><td>{dc(v2, 5)}</td><td>{'&check;' if ok else '&times;'}</td></tr>" for a, v1, v2, ok in rows[:10]) + "</table>"]
    if bad:
        steps.append(f"<b>They differ at x = {bad[0]}&deg;</b> (LHS = {dc(bad[1], 5)}, RHS = {dc(bad[2], 5)}). <b>This is NOT an identity.</b> One counter-example is enough to disprove it. (It might still be an <i>equation</i> true only for some angles: use the Trig equations tab.)")
        return _ok(steps, f"<b>Not an identity</b> (fails at x = {bad[0]}&deg;)")
    steps.append(f"Both sides agree at all {good} angles tested, so this is <b>very probably an identity</b>.")
    steps.append("<b>Important:</b> a numerical test is strong evidence but not a proof. In an exam you must <b>prove</b> it by starting from one side and using known identities, for example: "
                 "sin<sup>2</sup>x + cos<sup>2</sup>x = 1; tan x = sin x/cos x; 1 + tan<sup>2</sup>x = sec<sup>2</sup>x; 1 + cot<sup>2</sup>x = cosec<sup>2</sup>x; sin 2x = 2 sin x cos x; cos 2x = cos<sup>2</sup>x &minus; sin<sup>2</sup>x.")
    return _ok(steps, "<b>Probably an identity (true at every angle tested)</b>")


# ----------------------------------------------------------------- triangle area
@wrap
def tri_area(d):
    plt = _plt()
    mode = d.get("mode", "sas")
    if mode == "sas":
        a = fnum(d.get("a"), "Side a", 0)
        b = fnum(d.get("b"), "Side b", 0)
        C = fnum(d.get("C"), "Angle C", 0, 180)
        ar = 0.5 * a * b * S(C)
        steps = [f"<b>Area of a triangle from two sides and the angle between them:</b> Area = &frac12; a b sin C. (C must be the angle <i>between</i> sides a and b.)",
                 f"Area = &frac12; &times; {dc(a)} &times; {dc(b)} &times; sin {dc(C)}&deg; = &frac12; &times; {dc(a * b)} &times; {dc(S(C), 5)} = {HL(dc(ar, 3) + ' square units')}"]
        c = math.sqrt(a * a + b * b - 2 * a * b * Cc(C))
        A = math.degrees(math.acos((b * b + c * c - a * a) / (2 * b * c)))
        B = 180 - A - C
        steps.append(f"<i>For the picture, the third side is c = &radic;(a&sup2; + b&sup2; &minus; 2ab cos C) = {dc(c, 3)} (cosine rule).</i>")
    elif mode == "heron":
        a = fnum(d.get("a"), "Side a", 0)
        b = fnum(d.get("b"), "Side b", 0)
        c = fnum(d.get("c"), "Side c", 0)
        if a + b <= c or a + c <= b or b + c <= a:
            raise UErr("These three lengths cannot make a triangle (two sides must add up to more than the third).")
        s = (a + b + c) / 2
        ar = math.sqrt(s * (s - a) * (s - b) * (s - c))
        steps = ["<b>Heron's formula</b> (use it when you know all three sides): s = (a + b + c)/2 and Area = &radic;[ s(s &minus; a)(s &minus; b)(s &minus; c) ].",
                 f"<b>Step 1:</b> s = ({dc(a)} + {dc(b)} + {dc(c)})/2 = {dc(s, 3)}",
                 f"<b>Step 2:</b> s &minus; a = {dc(s - a, 3)}, s &minus; b = {dc(s - b, 3)}, s &minus; c = {dc(s - c, 3)}",
                 f"<b>Step 3:</b> Area = &radic;({dc(s, 3)} &times; {dc(s - a, 3)} &times; {dc(s - b, 3)} &times; {dc(s - c, 3)}) = &radic;{dc(s * (s - a) * (s - b) * (s - c), 3)} = {HL(dc(ar, 3) + ' square units')}"]
        A = math.degrees(math.acos((b * b + c * c - a * a) / (2 * b * c)))
        B = math.degrees(math.acos((a * a + c * c - b * b) / (2 * a * c)))
        C = 180 - A - B
        R = a * b * c / (4 * ar)
        r_in = ar / s
        steps.append(f"<b>Bonus:</b> radius of the circle through the three corners R = abc/(4 &times; Area) = {dc(R, 3)}; radius of the inscribed circle r = Area/s = {dc(r_in, 3)}.")
    else:
        r = fnum(d.get("r"), "Radius", 0)
        th = fnum(d.get("th"), "Angle at the centre", 0, 360)
        sector = math.pi * r * r * th / 360
        tri = 0.5 * r * r * S(th)
        seg = sector - tri
        steps = [f"<b>Area of a segment</b> (the part of a circle cut off by a chord). Segment = area of sector &minus; area of the triangle formed by the two radii and the chord.",
                 f"<b>Sector</b> = (&theta;/360) &times; &pi;r&sup2; = ({dc(th)}/360) &times; &pi; &times; {dc(r)}&sup2; = {dc(sector, 3)}",
                 f"<b>Triangle</b> = &frac12; r&sup2; sin &theta; = &frac12; &times; {dc(r)}&sup2; &times; sin {dc(th)}&deg; = {dc(tri, 3)}",
                 f"<b>Segment</b> = {dc(sector, 3)} &minus; {dc(tri, 3)} = {HL(dc(seg, 3) + ' square units')}"]
        fig, ax = plt.subplots(figsize=(5.2, 5.2))
        t_ = [i * 2 * math.pi / 200 for i in range(201)]
        ax.plot([r * math.cos(u) for u in t_], [r * math.sin(u) for u in t_], color=BLUE, lw=2)
        a1, a2 = math.radians(90 - th / 2), math.radians(90 + th / 2)
        P1 = (r * math.cos(a1), r * math.sin(a1))
        P2 = (r * math.cos(a2), r * math.sin(a2))
        arc = [a1 + (a2 - a1) * i / 80 for i in range(81)]
        ax.fill([r * math.cos(u) for u in arc] + [], [r * math.sin(u) for u in arc], color=ORANGE, alpha=0.35)
        ax.plot([0, P1[0]], [0, P1[1]], color=RED, lw=2)
        ax.plot([0, P2[0]], [0, P2[1]], color=RED, lw=2)
        ax.plot([P1[0], P2[0]], [P1[1], P2[1]], color=GREEN, lw=2.4)
        ax.text(0, r * 0.2, f"{dc(th).replace(MINUS, '-')}°", ha="center", fontsize=11, fontweight="bold", color=INK, path_effects=_halo())
        ax.text(P1[0] / 2 + 0.03 * r, P1[1] / 2, f"r = {dc(r).replace(MINUS, '-')}", fontsize=9, color=RED, fontweight="bold", path_effects=_halo())
        ax.text(0, r * 0.93, "segment", ha="center", fontsize=9, color=INK, path_effects=_halo())
        ax.set_aspect("equal")
        ax.axis("off")
        return _out(steps, f"<b>Segment area = {dc(seg, 3)}</b>", _b64(fig))
    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    draw_tri(ax, A, B, C, a if mode == "heron" else a, b if mode == "heron" else b, c, f"Area = {dc(ar, 2).replace(MINUS, '-')}")
    # in sas mode draw_tri expects side a opposite A: recompute consistent triangle
    if mode == "sas":
        ax.clear()
        draw_tri(ax, A, B, C, a, b, c, f"Area = {dc(ar, 2).replace(MINUS, '-')}")
    return _out(steps, f"<b>Area = {dc(ar, 3)} square units</b>", _b64(fig))


# ----------------------------------------------------------------- 3-D problems
def proj(p, k=0.55, ang=40):
    x, y, z = p
    return x + k * y * math.cos(math.radians(ang)), z + k * y * math.sin(math.radians(ang))


def _seg3(ax, p, q, hidden=False, col=INK, lw=1.8):
    a, b = proj(p), proj(q)
    ax.plot([a[0], b[0]], [a[1], b[1]], color=col, lw=lw, ls="--" if hidden else "-", zorder=3)


def _lab3(ax, p, t, dx=0, dy=0, col=INK):
    a = proj(p)
    ax.annotate(t, a, xytext=(6 + dx, 6 + dy), textcoords="offset points", fontsize=11, fontweight="bold", color=col, path_effects=_halo(), zorder=8)


@wrap
def solid(d):
    plt = _plt()
    mode = d.get("mode", "cuboid")
    l = fnum(d.get("l"), "Length", 0)
    w = fnum(d.get("w"), "Width", 0)
    fig, ax = plt.subplots(figsize=(6.4, 5))
    if mode == "cuboid":
        h = fnum(d.get("h"), "Height", 0)
        A, B, C, D = (0, 0, 0), (l, 0, 0), (l, w, 0), (0, w, 0)
        E, F, G, H = (0, 0, h), (l, 0, h), (l, w, h), (0, w, h)
        for p, q, hid in ((A, B, 0), (B, C, 0), (C, D, 0), (D, A, 1), (E, F, 0), (F, G, 0), (G, H, 0), (H, E, 0), (A, E, 0), (B, F, 0), (C, G, 0), (D, H, 1)):
            _seg3(ax, p, q, hid)
        # the 'hidden' edges per this oblique view are the ones at the back-bottom-left: D-A, D-C?, D-H
        _seg3(ax, C, D, True)
        _seg3(ax, A, C, True, ORANGE, 2.2)
        _seg3(ax, A, G, False, RED, 2.6)
        _seg3(ax, C, G, False, GREEN, 2.2)
        for nm_, p in zip("ABCDEFGH", (A, B, C, D, E, F, G, H)):
            _lab3(ax, p, nm_)
        AC = math.hypot(l, w)
        AG = math.sqrt(l * l + w * w + h * h)
        ang = math.degrees(math.atan(h / AC))
        angAB = math.degrees(math.acos(l / AG))
        angp = math.degrees(math.atan(h / w))
        steps = [f"<b>Cuboid</b> ABCDEFGH: length AB = {dc(l)}, width BC = {dc(w)}, height AE = {dc(h)}. The base is ABCD and the top is EFGH.",
                 f"<b>Base diagonal AC</b> (Pythagoras in the base rectangle ABC): AC = &radic;(AB&sup2; + BC&sup2;) = &radic;({dc(l)}&sup2; + {dc(w)}&sup2;) = {HL(dc(AC, 3))}",
                 f"<b>Space diagonal AG</b> (Pythagoras in the <i>vertical</i> right-angled triangle ACG, with right angle at C): AG = &radic;(AC&sup2; + CG&sup2;) = &radic;({dc(AC * AC, 3)} + {dc(h)}&sup2;) = {HL(dc(AG, 3))}",
                 f"<b>Angle between AG and the base ABCD:</b> the 'shadow' of AG on the base is AC, so the angle is angle GAC. In triangle ACG: tan(GAC) = opposite/adjacent = CG/AC = {dc(h)}/{dc(AC, 3)} &rArr; angle = {HL(dc(ang, 2) + DEG)}",
                 f"<b>Angle between AG and the edge AB:</b> triangle ABG has a right angle at B (BG is in the right face). cos(GAB) = AB/AG = {dc(l)}/{dc(AG, 3)} &rArr; angle = {HL(dc(angAB, 2) + DEG)}",
                 f"<b>Angle between the sloping plane ABGH and the base:</b> look at the right-angled triangle BCG (the plane rises from BC to GH): tan = CG/BC = {dc(h)}/{dc(w)} &rArr; angle = {HL(dc(angp, 2) + DEG)}",
                 f"<b>Volume</b> = l &times; w &times; h = {dc(l * w * h, 3)}; <b>surface area</b> = 2(lw + lh + wh) = {dc(2 * (l * w + l * h + w * h), 3)}"]
        res = f"<b>AC = {dc(AC, 3)}, AG = {dc(AG, 3)}, angle GAC = {dc(ang, 2)}&deg;</b>"
    else:
        known = d.get("known", "h")
        val = fnum(d.get("h"), "Height or edge", 0)
        half = math.hypot(l, w) / 2
        if known == "e":
            if val <= half:
                raise UErr("The sloping edge must be longer than half the base diagonal (" + dc(half, 3) + ").")
            h = math.sqrt(val * val - half * half)
        else:
            h = val
        A, B, C, D = (0, 0, 0), (l, 0, 0), (l, w, 0), (0, w, 0)
        O = (l / 2, w / 2, 0)
        V = (l / 2, w / 2, h)
        for p, q, hid in ((A, B, 0), (B, C, 0), (C, D, 1), (D, A, 1)):
            _seg3(ax, p, q, hid)
        for p, hid in ((A, 0), (B, 0), (C, 0), (D, 1)):
            _seg3(ax, V, p, hid)
        _seg3(ax, V, O, True, GREEN, 2.2)
        _seg3(ax, A, C, True, ORANGE, 1.8)
        _seg3(ax, B, D, True, ORANGE, 1.8)
        _seg3(ax, V, A, False, RED, 2.6)
        for nm_, p in zip("ABCDVO", (A, B, C, D, V, O)):
            _lab3(ax, p, nm_)
        edge = math.sqrt(half * half + h * h)
        angE = math.degrees(math.atan(h / half))
        sl_w = math.hypot(h, w / 2)
        sl_l = math.hypot(h, l / 2)
        angF = math.degrees(math.atan(h / (w / 2)))
        steps = [f"<b>Pyramid VABCD</b> with a rectangular base AB = {dc(l)}, BC = {dc(w)} and apex V directly above the centre O of the base (so VO is vertical).",
                 f"<b>Base diagonal</b> AC = &radic;({dc(l)}&sup2; + {dc(w)}&sup2;) = {dc(math.hypot(l, w), 3)}, and AO = AC/2 = {HL(dc(half, 3))} (O is the midpoint of AC).",
                 (f"<b>Height VO</b> from the edge: in right-angled triangle VOA, VO&sup2; = VA&sup2; &minus; AO&sup2; = {dc(val)}&sup2; &minus; {dc(half, 3)}&sup2; &rArr; VO = {HL(dc(h, 3))}" if known == "e" else f"<b>Height</b> VO = {HL(dc(h, 3))}"),
                 f"<b>Sloping edge</b> VA = &radic;(VO&sup2; + AO&sup2;) = &radic;({dc(h, 3)}&sup2; + {dc(half, 3)}&sup2;) = {HL(dc(edge, 3))}",
                 f"<b>Angle between edge VA and the base:</b> the shadow of VA on the base is AO, so it is angle VAO. tan(VAO) = VO/AO = {dc(h, 3)}/{dc(half, 3)} &rArr; {HL(dc(angE, 2) + DEG)}",
                 f"<b>Angle between the face VAB and the base:</b> let M be the midpoint of AB. Then OM = BC/2 = {dc(w / 2, 3)} and OM &perp; AB. tan(VMO) = VO/OM = {dc(h, 3)}/{dc(w / 2, 3)} &rArr; {HL(dc(angF, 2) + DEG)}. The slant height VM = &radic;({dc(h, 3)}&sup2; + {dc(w / 2, 3)}&sup2;) = {dc(sl_w, 3)}",
                 f"<b>Volume</b> = &frac13; &times; base area &times; height = &frac13; &times; {dc(l * w, 3)} &times; {dc(h, 3)} = {dc(l * w * h / 3, 3)}"]
        res = f"<b>Height = {dc(h, 3)}, edge = {dc(edge, 3)}, angle VAO = {dc(angE, 2)}&deg;</b>"
    ax.set_aspect("equal")
    ax.axis("off")
    ax.margins(0.12)
    ax.set_title("Oblique drawing (dashed lines are hidden edges; red = the line we need)", fontsize=9, color=INK)
    return _out(steps, res, _b64(fig))


# ----------------------------------------------------------------- spec
SPEC = {
    "title": "Trigonometry Extras",
    "intro": "Sine rule with the ambiguous case, exact values of special angles, trig equations, identities, compound and double angles, triangle area and 3-D problems. "
             "Angles are in <b>degrees</b>. Every result comes with a diagram or graph.",
    "tabs": [
        {"id": "sr", "label": "Sine rule", "title": "Sine rule (including the ambiguous case)", "endpoint": "sine_rule",
         "hint": "Choose <b>two angles and a side</b> for the normal case, or <b>two sides and an angle</b> (SSA) to see whether 0, 1 or 2 triangles exist.",
         "fields": [select("mode", "I know", [("aas", "two angles and a side (A, B, a)"), ("ssa", "two sides and an angle (a, b, A) &ndash; ambiguous case")], wide=True),
                    field("A", "Angle A (degrees)", "30"), field("B", "Angle B (degrees)", "60", show_if={"mode": "aas"}),
                    field("a", "Side a (opposite A)", "7"), field("b", "Side b (opposite B)", "10", show_if={"mode": "ssa"})], "button": "Solve the triangle"},
        {"id": "ev", "label": "Exact values", "title": "Exact values of special angles", "endpoint": "exact_values",
         "hint": "Works with sin, cos and tan of 0, 30, 45, 60, 90 and their multiples up to 360 (like 120, 150, 210, 315). Examples: <b>sin 30 + cos 60</b>, <b>tan 60 * cos 30 - sin 150</b>, <b>sin^2 45 + cos^2 45</b>.",
         "fields": [field("e", "Expression", "tan 60 * cos 30 - sin 150", wide=True, half=False)], "button": "Evaluate exactly"},
        {"id": "te", "label": "Trig equations", "title": "Solve a trigonometric equation", "endpoint": "trig_eq",
         "hint": "Form: <b>a &times; f(b&theta; + c) = k</b>. Example: 2 sin(&theta;) = 1, or cos(2&theta; + 30) = &minus;0.5. Leave b = 1 and c = 0 for a simple equation.",
         "fields": [select("fn", "Function", [("sin", "sin"), ("cos", "cos"), ("tan", "tan")]), field("a", "a (coefficient)", "2"),
                    field("b", "b (multiple of &theta;)", "1"), field("c", "c (added angle, degrees)", "0"),
                    field("k", "k (right-hand side)", "1"),
                    select("rng", "Range", [("0-360", "0&deg; to 360&deg;"), ("-180-180", "&minus;180&deg; to 180&deg;"), ("0-720", "0&deg; to 720&deg;"), ("-360-360", "&minus;360&deg; to 360&deg;")])], "button": "Solve"},
        {"id": "tq", "label": "Quadratic trig equations", "title": "Equations like 2sin&sup2;&theta; &minus; sin&theta; &minus; 1 = 0", "endpoint": "trig_quad",
         "fields": [select("fn", "Function", [("sin", "sin"), ("cos", "cos"), ("tan", "tan")]),
                    field("A", "A (coefficient of f&sup2;)", "2"), field("B", "B (coefficient of f)", "-1"), field("C", "C (number)", "-1"),
                    select("rng", "Range", [("0-360", "0&deg; to 360&deg;"), ("-180-180", "&minus;180&deg; to 180&deg;"), ("0-720", "0&deg; to 720&deg;")])], "button": "Solve"},
        {"id": "cp", "label": "Compound & double angles", "title": "Compound angle and double angle formulae", "endpoint": "compound",
         "fields": [select("mode", "What do you want", [("comp", "sin / cos / tan of (A + B) or (A &minus; B)"), ("dbl", "sin 2A, cos 2A, tan 2A from a given value")], wide=True),
                    select("fn", "Function", [("sin", "sin"), ("cos", "cos"), ("tan", "tan")]),
                    select("op", "Sign", [("+", "A + B"), ("-", "A &minus; B")], show_if={"mode": "comp"}),
                    field("A", "Angle A (degrees)", "45", show_if={"mode": "comp"}), field("B", "Angle B (degrees)", "30", show_if={"mode": "comp"}),
                    field("v", "Value (like 3/5)", "3/5", show_if={"mode": "dbl"}),
                    select("q", "A is in the", [("1", "1st quadrant (acute)"), ("2", "2nd quadrant"), ("3", "3rd quadrant"), ("4", "4th quadrant")], show_if={"mode": "dbl"})], "button": "Calculate"},
        {"id": "id", "label": "Identity checker", "title": "Test a trigonometric identity", "endpoint": "identity",
         "hint": "Write sin(x), cos(x), tan(x), sec(x), cosec(x), cot(x) and use <b>^</b> for powers. Example: sin(x)^2 + cos(x)^2 and 1.",
         "fields": [field("l", "Left side", "(1 - cos(2x))/2", wide=True, half=False), field("r", "Right side", "sin(x)^2", wide=True, half=False)], "button": "Test it"},
        {"id": "ta", "label": "Area of a triangle", "title": "Area using sine, Heron's formula, or a segment", "endpoint": "tri_area",
         "fields": [select("mode", "I know", [("sas", "two sides and the angle between them"), ("heron", "all three sides (Heron)"), ("seg", "radius and angle (area of a segment)")], wide=True),
                    field("a", "Side a", "8", show_if={"mode": ["sas", "heron"]}), field("b", "Side b", "11", show_if={"mode": ["sas", "heron"]}),
                    field("C", "Angle C between them (degrees)", "40", show_if={"mode": "sas"}),
                    field("c", "Side c", "9", show_if={"mode": "heron"}),
                    field("r", "Radius", "10", show_if={"mode": "seg"}), field("th", "Angle at the centre (degrees)", "70", show_if={"mode": "seg"})], "button": "Find the area"},
        {"id": "s3", "label": "3-D problems", "title": "Lengths and angles in a cuboid or pyramid", "endpoint": "solid",
         "fields": [select("mode", "Solid", [("cuboid", "Cuboid"), ("pyramid", "Pyramid on a rectangle")], wide=True),
                    field("l", "Length AB", "8"), field("w", "Width BC", "6"),
                    field("h", "Height AE", "5", show_if={"mode": "cuboid"}),
                    select("known", "I know the pyramid's", [("h", "height VO"), ("e", "sloping edge VA")], show_if={"mode": "pyramid"}),
                    field("h", "Height or edge length", "7", show_if={"mode": "pyramid"})], "button": "Solve and draw"},
    ],
}

topics.register("trig2", SPEC, {"sine_rule": sine_rule, "exact_values": exact_values, "trig_eq": trig_eq, "trig_quad": trig_quad,
                                "compound": compound, "identity": identity, "tri_area": tri_area, "solid": solid})
