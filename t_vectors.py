"""Vectors in two dimensions."""
import math
from fractions import Fraction

import topics
from tcommon import UErr, fm, num, field, select, guard, _ok, _fail
from frac_numeric import table
from t_conics import ns, rt, rt_parts, rtv, HL, MINUS, _plt, _halo, _b64, BLUE, RED, GREEN, ORANGE, GREY, INK

LET = "ABCDEFGH"


def col(v):
    return f"<table class='mx'><tr><td>{ns(v[0])}</td></tr><tr><td>{ns(v[1])}</td></tr></table>"


def vtxt(v):
    return f"({ns(v[0])}, {ns(v[1])})"


def mag2(v):
    return v[0] * v[0] + v[1] * v[1]


def angles(v):
    """(angle from +x anticlockwise 0..360, bearing 0..360)"""
    th = math.degrees(math.atan2(float(v[1]), float(v[0]))) % 360
    br = (90 - th) % 360
    return th, br


def vec(d, a, b, lab):
    return (Fraction(num(d.get(a), f"{lab} (top)")), Fraction(num(d.get(b), f"{lab} (bottom)")))


def arrows(items, points=(), title=None):
    """items: (start, end, label, colour, style)"""
    plt = _plt()
    pts = [p for it in items for p in (it[0], it[1])] + list(points) + [(0, 0)]
    xs = [float(p[0]) for p in pts]
    ys = [float(p[1]) for p in pts]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 4)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    half = span * 0.62
    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    ax.set_xlim(cx - half, cx + half)
    ax.set_ylim(cy - half, cy + half)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, color="#e2e8f0", lw=0.8)
    ax.axhline(0, color="#334155", lw=1.3)
    ax.axvline(0, color="#334155", lw=1.3)
    ax.tick_params(labelsize=8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for s, e, lab, colr, sty in items:
        sx, sy, ex, ey = float(s[0]), float(s[1]), float(e[0]), float(e[1])
        ax.annotate("", xy=(ex, ey), xytext=(sx, sy), arrowprops=dict(arrowstyle="-|>", color=colr, lw=2.6 if sty == "-" else 2.0, ls=sty, shrinkA=0, shrinkB=0, mutation_scale=18), zorder=5)
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        dx, dy = ex - sx, ey - sy
        n = math.hypot(dx, dy) or 1
        ax.annotate(lab, (mx, my), xytext=(-dy / n * 15, dx / n * 15), textcoords="offset points", ha="center", va="center", fontsize=11, fontweight="bold", color=colr, path_effects=_halo(), zorder=8)
    for p, lab, colr in [(q[0], q[1], q[2]) for q in []]:
        pass
    return fig, ax


def dot_pts(ax, pts):
    for p, lab, colr in pts:
        ax.plot([float(p[0])], [float(p[1])], "o", color=colr, ms=8, zorder=7, mec="white")
        ax.annotate(f"{lab} ({fm(float(p[0]), 2)}, {fm(float(p[1]), 2)})", (float(p[0]), float(p[1])), xytext=(7, 7), textcoords="offset points", fontsize=10, fontweight="bold", color=colr, path_effects=_halo(), zorder=9)


@guard
def operations(d):
    a, b = vec(d, "a1", "a2", "a"), vec(d, "b1", "b2", "b")
    m = Fraction(num(d.get("m"), "m", True) or 1)
    n = Fraction(num(d.get("n"), "n", True) or 1)
    for v in (a, b, m, n):
        pass
    steps = [f"<b>Column vectors.</b> A vector has a size and a direction. We write it as a column: the <b>top number</b> is how far it moves across (x direction, right is +), the <b>bottom number</b> is how far it moves up (y direction, up is +).",
             f"a = {col(a)} &nbsp;&nbsp; b = {col(b)}"]
    s = (a[0] + b[0], a[1] + b[1])
    df = (a[0] - b[0], a[1] - b[1])
    steps.append(f"<b>Add vectors:</b> add the tops together and the bottoms together. a + b = ({ns(a[0])} + ({ns(b[0])}), {ns(a[1])} + ({ns(b[1])})) = {HL(vtxt(s))}")
    steps.append(f"<b>Subtract vectors:</b> a &minus; b = ({ns(a[0])} &minus; ({ns(b[0])}), {ns(a[1])} &minus; ({ns(b[1])})) = {HL(vtxt(df))}")
    R = (m * a[0] + n * b[0], m * a[1] + n * b[1])
    steps.append(f"<b>Scalar multiples:</b> multiply BOTH numbers by the scalar. {ns(m)}a + ({ns(n)})b = ({ns(m)}&times;({ns(a[0])}) + ({ns(n)})&times;({ns(b[0])}), {ns(m)}&times;({ns(a[1])}) + ({ns(n)})&times;({ns(b[1])})) = {HL(vtxt(R))}")
    for name, v in (("a", a), ("b", b), (f"{ns(m)}a {'+' if n >= 0 else MINUS} {ns(abs(n))}b", R)):
        m2 = mag2(v)
        th, br = angles(v)
        steps.append(f"<b>Magnitude (length) of {name}</b> = &radic;(x&sup2; + y&sup2;) = &radic;(({ns(v[0])})&sup2; + ({ns(v[1])})&sup2;) = &radic;{ns(m2)} = {HL(rt(m2))}"
                     + (f" &nbsp; Direction: {fm(th, 1)}&deg; anticlockwise from the +x axis; bearing {fm(br, 1)}&deg;." if m2 != 0 else ""))
    ma, mb = rtv(mag2(a)), rtv(mag2(b))
    dt = a[0] * b[0] + a[1] * b[1]
    if ma and mb:
        cs = max(-1.0, min(1.0, float(dt) / (ma * mb)))
        steps.append(f"<b>Dot (scalar) product:</b> a &middot; b = ({ns(a[0])})({ns(b[0])}) + ({ns(a[1])})({ns(b[1])}) = {HL(ns(dt))}. "
                     f"The angle between them: cos &theta; = a&middot;b &divide; (|a||b|) = {ns(dt)} &divide; ({fm(ma, 3)} &times; {fm(mb, 3)}) = {fm(cs, 4)}, so &theta; = {HL(fm(math.degrees(math.acos(cs)), 2) + '&deg;')}")
        if dt == 0:
            steps.append("The dot product is 0, so a and b are <b>perpendicular</b>.")
        if a[0] * b[1] == a[1] * b[0]:
            steps.append("Also a and b are <b>parallel</b> (one is a multiple of the other).")
    steps.append("<b>Picture:</b> to add, place b <b>head to tail</b> at the tip of a. The resultant goes from the start of a to the end of b (the green arrow shows a + b).")
    s0 = (Fraction(0), Fraction(0))
    fig, ax = arrows([(s0, a, "a", BLUE, "-"), (s0, b, "b", RED, "-"), (a, s, "b", RED, "--"), (b, s, "a", BLUE, "--"), (s0, s, "a + b", GREEN, "-")])
    return _ok(steps, {"image": _b64(fig), "text": f"<b>a + b = {vtxt(s)}, a &minus; b = {vtxt(df)}, {ns(m)}a + {ns(n)}b = {vtxt(R)}</b>"})


@guard
def points(d):
    A = (Fraction(num(d.get("ax"), "A x")), Fraction(num(d.get("ay"), "A y")))
    B = (Fraction(num(d.get("bx"), "B x")), Fraction(num(d.get("by"), "B y")))
    m = Fraction(num(d.get("m"), "m", True) or 0)
    n = Fraction(num(d.get("n"), "n", True) or 0)
    if m < 0 or n < 0 or (m == 0) != (n == 0):
        if not (m == 0 and n == 0):
            raise UErr("For the ratio use two positive numbers (like 2 and 1), or leave both empty.")
    AB = (B[0] - A[0], B[1] - A[1])
    steps = [f"<b>Position vector</b> of a point = the vector from the origin O to that point. OA = {col(A)}, OB = {col(B)}.",
             f"<b>Vector AB</b> = (position of B) &minus; (position of A) = OB &minus; OA. &nbsp; <i>Remember: end minus start.</i><br>AB = ({ns(B[0])} &minus; {ns(A[0])}, {ns(B[1])} &minus; {ns(A[1])}) = {HL(vtxt(AB))}",
             f"<b>Vector BA</b> goes the opposite way, so it is the negative: BA = {HL(vtxt((-AB[0], -AB[1])))}"]
    m2 = mag2(AB)
    th, br = angles(AB)
    steps.append(f"<b>Distance AB = magnitude of AB</b> = &radic;({ns(AB[0])}&sup2; + {ns(AB[1])}&sup2;) = &radic;{ns(m2)} = {HL(rt(m2))}")
    if m2 != 0:
        steps.append(f"<b>Direction of AB:</b> angle with the +x axis = tan<sup>&minus;1</sup>({ns(AB[1])}/{ns(AB[0])}) &rarr; {fm(th, 1)}&deg; anticlockwise from east. As a <b>bearing</b> (clockwise from North): {HL(fm(br, 1) + '&deg;')}")
    M = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
    steps.append(f"<b>Midpoint of AB</b> = half way = (OA + OB) &divide; 2 = (({ns(A[0])} + {ns(B[0])}) &divide; 2, ({ns(A[1])} + {ns(B[1])}) &divide; 2) = {HL(vtxt(M))}")
    pts_ = [(A, "A", BLUE), (B, "B", RED), (M, "M", GREEN)]
    items = [((Fraction(0), Fraction(0)), A, "OA", GREY, "--"), ((Fraction(0), Fraction(0)), B, "OB", GREY, "--"), (A, B, "AB", ORANGE, "-")]
    extra = f"midpoint M {vtxt(M)}"
    if m != 0:
        P = ((n * A[0] + m * B[0]) / (m + n), (n * A[1] + m * B[1]) / (m + n))
        steps.append(f"<b>Point P dividing AB in the ratio {ns(m)} : {ns(n)}</b> (AP : PB = {ns(m)} : {ns(n)}). Split AB into {ns(m + n)} equal parts; P is {ns(m)} of them from A. "
                     f"AP = {FR_(m, m + n)} of AB, so OP = OA + {FR_(m, m + n)}AB:<br>"
                     f"OP = ({ns(A[0])} + {FR_(m, m + n)}&times;{ns(AB[0])}, {ns(A[1])} + {FR_(m, m + n)}&times;{ns(AB[1])}) = {HL(vtxt(P))}")
        pts_.append((P, "P", "#7c3aed"))
        extra += f"; P {vtxt(P)}"
    pad = [A, B]
    fig, ax = arrows(items, points=pad)
    dot_pts(ax, pts_)
    return _ok(steps, {"image": _b64(fig), "text": f"<b>AB = {vtxt(AB)}, |AB| = {rt(m2)}, {extra}</b>"})


def FR_(a, b):
    f = Fraction(a, 1) / Fraction(b, 1)
    return ns(f)


@guard
def parallel(d):
    mode = d.get("mode", "k")
    if mode == "k":
        a = vec(d, "a1", "a2", "a")
        b2 = Fraction(num(d.get("b2"), "b (bottom)"))
        if a[1] == 0:
            raise UErr("The bottom number of a is 0, so a is horizontal. Then b must also have a bottom number of 0.")
        k = a[0] * b2 / a[1]
        steps = [f"<b>Parallel vectors</b> are multiples of each other: if b = &lambda;a then their numbers are in the same ratio. For a = {col(a)} and b = ({'k'}, {ns(b2)}):",
                 f"Write the two ratios and make them equal: &nbsp; k &divide; {ns(a[0])} = {ns(b2)} &divide; {ns(a[1])}",
                 f"Cross-multiply and solve: k = {ns(a[0])} &times; {ns(b2)} &divide; {ns(a[1])} = {HL(ns(k))}",
                 f"<b>Check:</b> b = ({ns(k)}, {ns(b2)}), and b = {ns(b2 / a[1])} &times; a = ({ns(b2 / a[1] * a[0])}, {ns(b2)}) &check;"]
        return _ok(steps, {"image": None, "text": f"<b>k = {ns(k)}</b>"}) if False else _ok(steps, f"<b>k = {ns(k)}</b>")
    if mode == "perp":
        a = vec(d, "a1", "a2", "a")
        b2 = Fraction(num(d.get("b2"), "b (bottom)"))
        if a[0] == 0:
            raise UErr("The top number of a is 0 here, so k would not be fixed. Choose a with a non-zero top number.")
        k = -a[1] * b2 / a[0]
        steps = ["<b>Perpendicular vectors</b> (at 90&deg;) have a dot product of <b>0</b>.",
                 f"a &middot; b = ({ns(a[0])})(k) + ({ns(a[1])})({ns(b2)}) = 0",
                 f"{ns(a[0])}k + {ns(a[1] * b2)} = 0 &rarr; k = &minus;({ns(a[1] * b2)}) &divide; {ns(a[0])} = {HL(ns(k))}"]
        return _ok(steps, f"<b>k = {ns(k)}</b>")
    # collinear
    P = [(Fraction(num(d.get(f"{c}x"), f"{c} x")), Fraction(num(d.get(f"{c}y"), f"{c} y"))) for c in "abc"]
    A, B, C = P
    AB = (B[0] - A[0], B[1] - A[1])
    BC = (C[0] - B[0], C[1] - B[1])
    steps = ["<b>Three points are collinear</b> (on one straight line) if the vector AB is a multiple of BC. Because B is shared, they then lie on the same line.",
             f"AB = B &minus; A = {vtxt(AB)} &nbsp;&nbsp; BC = C &minus; B = {vtxt(BC)}"]
    ok = AB[0] * BC[1] == AB[1] * BC[0]
    steps.append(f"<b>Test:</b> are the ratios equal? {ns(AB[0])} &times; {ns(BC[1])} = {ns(AB[0] * BC[1])} and {ns(AB[1])} &times; {ns(BC[0])} = {ns(AB[1] * BC[0])}. "
                 + ("They are <b>equal</b>, so AB &#8741; BC and A, B, C are <b>collinear</b>." if ok else "They are <b>not equal</b>, so A, B and C are <b>not</b> on one straight line."))
    if ok and (BC[0] != 0 or BC[1] != 0):
        lam = AB[0] / BC[0] if BC[0] != 0 else AB[1] / BC[1]
        steps.append(f"In fact AB = {ns(lam)} &times; BC.")
    fig, ax = arrows([(A, B, "AB", BLUE, "-"), (B, C, "BC", RED, "-")], points=[A, B, C])
    dot_pts(ax, [(A, "A", BLUE), (B, "B", GREEN), (C, "C", RED)])
    return _ok(steps, {"image": _b64(fig), "text": "<b>Collinear: YES</b>" if ok else "<b>Collinear: NO</b>"})


SPEC = {
    "title": "Vectors",
    "intro": "Column vectors made easy: <b>add, subtract, multiply, magnitude, direction, bearing, dot product</b>, vectors between points, ratio division, parallel and collinear. "
             "<br><b>Key idea:</b> a vector is an instruction to move: <i>this far across, this far up</i>.",
    "tabs": [
        {"id": "vo", "label": "Add, subtract, length", "title": "Operations on two vectors a and b", "endpoint": "operations",
         "fields": [field("a1", "a: top number", "3"), field("a2", "a: bottom number", "2"), field("b1", "b: top number", "-1"), field("b2", "b: bottom number", "4"),
                    field("m", "m (for ma + nb)", "2"), field("n", "n (for ma + nb)", "-1")], "button": "Work it out"},
        {"id": "vp", "label": "Between points", "title": "Vector, distance, midpoint and ratio point from two points", "endpoint": "points",
         "hint": "Give the coordinates of A and B. To find a point P that divides AB in a ratio, also fill the ratio boxes (like 2 and 1 for 2 : 1). Leave them empty to skip.",
         "fields": [field("ax", "A: x", "1"), field("ay", "A: y", "2"), field("bx", "B: x", "7"), field("by", "B: y", "5"), field("m", "Ratio part 1 (optional)", "2"), field("n", "Ratio part 2 (optional)", "1")], "button": "Work it out"},
        {"id": "vl", "label": "Parallel and collinear", "title": "Parallel, perpendicular and collinear", "endpoint": "parallel",
         "fields": [select("mode", "Question", [("k", "find k so that a and b are parallel"), ("perp", "find k so that a and b are perpendicular"), ("col", "are A, B, C on one line?")], wide=True),
                    field("a1", "a: top number", "2", show_if={"mode": ["k", "perp"]}), field("a2", "a: bottom number", "3", show_if={"mode": ["k", "perp"]}),
                    field("b2", "b = (k, ?): the bottom number", "9", show_if={"mode": ["k", "perp"]}),
                    field("ax", "A: x", "1", show_if={"mode": "col"}), field("ay", "A: y", "1", show_if={"mode": "col"}),
                    field("bx", "B: x", "3", show_if={"mode": "col"}), field("by", "B: y", "4", show_if={"mode": "col"}),
                    field("cx", "C: x", "5", show_if={"mode": "col"}), field("cy", "C: y", "7", show_if={"mode": "col"})], "button": "Solve"},
    ],
}
topics.register("vectors", SPEC, {"operations": operations, "points": points, "parallel": parallel})
