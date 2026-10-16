"""Quadratic functions and graphs."""
import math
import re
from fractions import Fraction

import topics
from tcommon import UErr, fm, num, field, select, guard, _ok, _fail
from frac_numeric import table
from t_conics import ns, rt, rt_parts, rtv, shift, sq, HL, MINUS, _plt, _halo, _b64, BLUE, RED, GREEN, ORANGE, GREY, INK


def poly_txt(a, b, c, var="x"):
    out = ""
    for co, v in ((a, f"{var}<sup>2</sup>"), (b, var), (c, "")):
        co = Fraction(co)
        if co == 0:
            continue
        sign = MINUS if co < 0 else "+"
        mag = abs(co)
        body = (ns(mag) if (mag != 1 or not v) else "") + v
        out += (f"{MINUS if co < 0 else ''}{body}" if not out else f" {sign} {body}")
    return out or "0"


def sgt(v):
    v = Fraction(v)
    return f"{'+' if v >= 0 else MINUS} {ns(abs(v))}"


def coefs(d):
    a = Fraction(num(d.get("a"), "a"))
    b = Fraction(num(d.get("b"), "b", True) or 0)
    c = Fraction(num(d.get("c"), "c", True) or 0)
    if a == 0:
        raise UErr("a cannot be 0, otherwise it is a straight line and not a quadratic.")
    if max(abs(a), abs(b), abs(c)) > 10 ** 6:
        raise UErr("Please use smaller numbers (below 1,000,000).")
    return a, b, c


def roots_of(a, b, c):
    D = b * b - 4 * a * c
    if D < 0:
        return D, []
    s = math.sqrt(float(D))
    r = sorted({(-float(b) - s) / (2 * float(a)), (-float(b) + s) / (2 * float(a))})
    return D, r


def plot(a, b, c, extra_curves=(), roots=None, vertex=True, pts=(), x_range=None, label_pts=True, axis=True):
    plt = _plt()
    a, b, c = float(a), float(b), float(c)
    h = -b / (2 * a)
    k = c - b * b / (4 * a)
    D = b * b - 4 * a * c
    keyx = [h, 0.0]
    if D >= 0:
        s = math.sqrt(D)
        keyx += [(-b - s) / (2 * a), (-b + s) / (2 * a)]
    keyx += [p[0] for p in pts]
    if x_range:
        keyx += list(x_range)
    lo, hi = min(keyx), max(keyx)
    span = max(hi - lo, 4.0)
    lo, hi = lo - span * 0.35, hi + span * 0.35
    xs = [lo + (hi - lo) * i / 500 for i in range(501)]
    ys = [a * x * x + b * x + c for x in xs]
    ymin_key = min([k, 0.0] + [p[1] for p in pts])
    ymax_key = max([k, 0.0, c] + [p[1] for p in pts])
    yspan = max(ymax_key - ymin_key, 4.0)
    ylo, yhi = ymin_key - yspan * 0.3, ymax_key + yspan * 0.3
    if a > 0:
        yhi = max(yhi, ymax_key + yspan * 0.5)
    else:
        ylo = min(ylo, ymin_key - yspan * 0.5)
    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    ax.set_xlim(lo, hi)
    ax.set_ylim(ylo, yhi)
    ax.grid(True, color="#e2e8f0", lw=0.8)
    ax.axhline(0, color="#334155", lw=1.3)
    ax.axvline(0, color="#334155", lw=1.3)
    ax.tick_params(labelsize=8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.plot(xs, ys, color=BLUE, lw=2.8, zorder=3, label="y = " + re.sub("<[^>]+>", "", poly_txt(Fraction(a).limit_denominator(1000), Fraction(b).limit_denominator(1000), Fraction(c).limit_denominator(1000)).replace("<sup>2</sup>", "\u00b2")).replace("&minus;", "-"))
    for (m, n, col, lab) in extra_curves:
        ax.plot(xs, [m * x + n for x in xs], color=ORANGE, lw=2.4, zorder=3, label=lab)
    if axis:
        ax.plot([h, h], [ylo, yhi], "--", color=GREY, lw=1.3, zorder=2)
        ax.annotate(f"axis x = {fm(h, 3)}", (h, yhi), xytext=(4, -14), textcoords="offset points", fontsize=9, color=GREY, fontweight="bold", path_effects=_halo())

    def mark(p, t, col, off=(7, 7)):
        ax.plot([p[0]], [p[1]], "o", color=col, ms=7, zorder=6, mec="white")
        if label_pts:
            ax.annotate(t, p, xytext=off, textcoords="offset points", fontsize=9.5, fontweight="bold", color=col, path_effects=_halo(), zorder=7)

    if vertex:
        mark((h, k), f"vertex ({fm(h, 2)}, {fm(k, 2)})", "#b45309", (8, 10 if a < 0 else -16))
    if roots is None:
        roots = [] if D < 0 else sorted({(-b - math.sqrt(D)) / (2 * a), (-b + math.sqrt(D)) / (2 * a)})
    for r in roots:
        mark((r, 0), f"({fm(r, 2)}, 0)", RED, (6, -16 if a > 0 else 8))
    mark((0, c), f"y-intercept (0, {fm(c, 2)})", GREEN, (8, 6))
    for p in pts:
        ax.plot([p[0]], [p[1]], "o", color=RED, ms=8, zorder=7, mec="white")
        ax.annotate(f"({fm(p[0], 2)}, {fm(p[1], 2)})", p, xytext=(8, -14), textcoords="offset points", fontsize=9, fontweight="bold", color=RED, path_effects=_halo(), zorder=8)
    ax.legend(loc="best", fontsize=9)
    return _b64(fig)


def complete_square(a, b, c, steps):
    h = -b / (2 * a)
    k = c - b * b / (4 * a)
    if a != 1:
        steps.append(f"<b>Completing the square:</b> take out the number in front of x&sup2; from the x terms: {ns(a)}(x&sup2; {'+' if b / a >= 0 else MINUS} {ns(abs(b / a))}x) {'+' if c >= 0 else MINUS} {ns(abs(c))}" if b != 0 else
                     f"<b>Completing the square:</b> there is no x term, so it is already {ns(a)}x&sup2; {'+' if c >= 0 else MINUS} {ns(abs(c))}.")
    if b != 0:
        half = b / (2 * a)
        steps.append(f"Half of {ns(b / a)} is {ns(half)}. Square it: {ns(half * half)}. Add and subtract it inside the bracket: "
                     f"{ns(a) if a != 1 else ''}(x&sup2; {'+' if b / a >= 0 else MINUS} {ns(abs(b / a))}x + {ns(half * half)}) {sgt(-a * half * half)} {sgt(c)}")
    form = f"{ns(a) if a not in (1, -1) else ('' if a == 1 else MINUS)}{sq(shift('x', h))}{(' + ' + ns(k)) if k > 0 else ((' ' + MINUS + ' ' + ns(-k)) if k < 0 else '')}"
    steps.append(f"The bracket is now a perfect square: {HL('y = ' + form)}. This is called <b>vertex form</b>, y = a(x &minus; h)&sup2; + k, with vertex (h, k) = ({ns(h)}, {ns(k)}).")
    return h, k


@guard
def analyse(d):
    a, b, c = coefs(d)
    steps = [f"<b>Your quadratic:</b> y = {poly_txt(a, b, c)}. Compare with y = ax&sup2; + bx + c: <b>a = {ns(a)}, b = {ns(b)}, c = {ns(c)}</b>.",
             f"<b>Shape:</b> a is {'positive' if a > 0 else 'negative'}, so the curve opens <b>{'upwards (a smile, U shape)' if a > 0 else 'downwards (a frown, n shape)'}</b>. "
             f"It has a {'lowest (minimum)' if a > 0 else 'highest (maximum)'} point called the <b>vertex</b>.",
             f"<b>y-intercept</b> (where the curve crosses the y-axis, x = 0): y = c = {HL(ns(c))}, the point (0, {ns(c)})."]
    h = -b / (2 * a)
    k = c - b * b / (4 * a)
    steps.append(f"<b>Axis of symmetry</b> (the mirror line through the vertex): x = &minus;b &divide; 2a = &minus;({ns(b)}) &divide; (2 &times; {ns(a)}) = x = {HL(ns(h))}")
    steps.append(f"<b>Vertex:</b> put x = {ns(h)} into the equation to get y: y = {ns(a)}({ns(h)})&sup2; {sgt(b)}({ns(h)}) {sgt(c)} = {HL(ns(k))}. "
                 f"So the vertex is {HL('(' + ns(h) + ', ' + ns(k) + ')')}, and the {'minimum' if a > 0 else 'maximum'} value of y is {ns(k)}.")
    complete_square(a, b, c, steps)
    D = b * b - 4 * a * c
    steps.append(f"<b>Discriminant</b> (tells us how many times the curve touches the x-axis): b&sup2; &minus; 4ac = ({ns(b)})&sup2; &minus; 4({ns(a)})({ns(c)}) = {HL(ns(D))}")
    if D > 0:
        steps.append("D is <b>positive</b>: the curve cuts the x-axis at <b>two different points</b> (two real roots).")
    elif D == 0:
        steps.append("D is <b>zero</b>: the curve just <b>touches</b> the x-axis at one point, the vertex (two equal roots).")
    else:
        steps.append("D is <b>negative</b>: the curve <b>never reaches</b> the x-axis (no real roots).")
    if D >= 0:
        steps.append(f"<b>Roots</b> (x-intercepts), using x = (&minus;b &plusmn; &radic;D) &divide; 2a = ({ns(-b)} &plusmn; {rt(D)}) &divide; {ns(2 * a)}")
        ex, sv = rt_parts(D)
        if ex is not None:
            r1, r2 = (-b - ex) / (2 * a), (-b + ex) / (2 * a)
            rs = sorted({r1, r2})
            steps.append(f"x = {' or x = '.join(ns(r) for r in rs)}. &nbsp; Check: the curve crosses the x-axis at " + " and ".join(f"({ns(r)}, 0)" for r in rs) + ". "
                         "Because the roots are exact numbers the quadratic <b>factorises</b>: " + f"y = {ns(a) if a != 1 else ''}{shift('x', rs[0])}{shift('x', rs[-1]) if len(rs) > 1 else shift('x', rs[0])}".replace("(x", "(x", 1))
        else:
            r = [(-float(b) - sv) / (2 * float(a)), (-float(b) + sv) / (2 * float(a))]
            steps.append(f"x &asymp; {fm(min(r), 3).replace('-', MINUS)} or x &asymp; {fm(max(r), 3).replace('-', MINUS)} (the roots are not neat numbers, so this does not factorise nicely).")
    rng = f"y &ge; {ns(k)}" if a > 0 else f"y &le; {ns(k)}"
    steps.append(f"<b>Range</b> (all possible y values): {HL(rng)}. The domain (all x values) is every real number.")
    rows = [("Opens", "upwards" if a > 0 else "downwards"), ("Vertex", f"({ns(h)}, {ns(k)})"), ("Axis of symmetry", f"x = {ns(h)}"),
            ("Minimum" if a > 0 else "Maximum", f"y = {ns(k)} at x = {ns(h)}"), ("y-intercept", f"(0, {ns(c)})"), ("Discriminant", ns(D)),
            ("x-intercepts", "none" if D < 0 else ("one: (" + ns(h) + ", 0)" if D == 0 else " and ".join(f"({fm(r, 3).replace('-', MINUS)}, 0)" for r in roots_of(a, b, c)[1]))), ("Range", rng)]
    steps.append(table(rows, ["Feature", "Value"]))
    steps.append("<b>Sketch tip:</b> mark the vertex, the y-intercept and the x-intercepts, draw the mirror line, then join the points in a smooth curve (never pointed, never straight).")
    return _ok(steps, {"image": plot(a, b, c), "text": f"<b>Vertex ({ns(h)}, {ns(k)}); axis x = {ns(h)}; y-intercept (0, {ns(c)}); " + ("no real roots" if D < 0 else "roots at x = " + " and ".join(fm(r, 3).replace("-", MINUS) for r in roots_of(a, b, c)[1])) + "</b>"})


@guard
def table_graph(d):
    a, b, c = coefs(d)
    lo = int(Fraction(num(d.get("x0"), "x from")))
    hi = int(Fraction(num(d.get("x1"), "x to")))
    if lo >= hi:
        raise UErr("'x from' must be smaller than 'x to'.")
    if hi - lo > 14:
        raise UErr("Please use at most 15 values of x (for example &minus;4 to 6).")
    steps = [f"<b>Table of values</b> for y = {poly_txt(a, b, c)}. For each x, put it into the equation to find y. Do it carefully: square first, then multiply.",
             ]
    rows = []
    pts = []
    for x in range(lo, hi + 1):
        y = a * x * x + b * x + c
        work = f"{ns(a)}({x})&sup2; + {ns(b)}({x}) + {ns(c)}".replace("+ " + MINUS, MINUS + " ")
        rows.append((str(x).replace("-", MINUS), work, ns(y)))
        pts.append((x, float(y)))
    steps.append(table(rows, ["x", "Working: ax&sup2; + bx + c", "y"]))
    steps.append("<b>Plot:</b> each pair (x, y) is a point. Plot them all, then join with a <b>smooth curve</b> using a pencil, not a ruler.")
    h = -b / (2 * a)
    return _ok(steps, {"image": plot(a, b, c, x_range=(lo, hi)), "text": f"<b>Turning point at x = {ns(h)}, y = {ns(c - b * b / (4 * a))}</b>"})


@guard
def build(d):
    mode = d.get("mode", "roots")
    steps = []
    if mode == "roots":
        p = Fraction(num(d.get("p"), "The first root"))
        q = Fraction(num(d.get("q"), "The second root"))
        a = Fraction(num(d.get("a"), "a", True) or 1)
        if a == 0:
            raise UErr("a cannot be 0.")
        steps.append(f"<b>You know the roots</b> (where it crosses the x-axis): x = {ns(p)} and x = {ns(q)}. Each root gives a bracket: (x &minus; root).")
        steps.append(f"y = {ns(a) if a != 1 else ''}{shift('x', p)}{shift('x', q)}")
        b = -a * (p + q)
        c = a * p * q
        steps.append(f"<b>Expand</b> (multiply out): x&sup2; &minus; (sum of roots)x + (product of roots) = x&sup2; &minus; ({ns(p + q)})x + ({ns(p * q)}). Multiply by a = {ns(a)}.")
        steps.append(f"<b>Answer:</b> y = {HL(poly_txt(a, b, c))}")
    elif mode == "vertex":
        h = Fraction(num(d.get("h"), "Vertex x"))
        k = Fraction(num(d.get("k"), "Vertex y"))
        a = Fraction(num(d.get("a"), "a"))
        if a == 0:
            raise UErr("a cannot be 0.")
        steps.append(f"<b>Vertex form:</b> y = a(x &minus; h)&sup2; + k with vertex (h, k) = ({ns(h)}, {ns(k)}) and a = {ns(a)}: y = {ns(a) if a != 1 else ''}{sq(shift('x', h))} + {ns(k)}".replace("+ &minus;", "&minus; "))
        b = -2 * a * h
        c = a * h * h + k
        steps.append(f"<b>Expand</b> (x &minus; {ns(h)})&sup2; = x&sup2; &minus; {ns(2 * h)}x + {ns(h * h)}, multiply by {ns(a)}, then add {ns(k)}.")
        steps.append(f"<b>Answer:</b> y = {HL(poly_txt(a, b, c))}")
    else:
        pts = []
        for i in (1, 2, 3):
            pts.append((Fraction(num(d.get(f"x{i}"), f"x{i}")), Fraction(num(d.get(f"y{i}"), f"y{i}"))))
        if len({p[0] for p in pts}) < 3:
            raise UErr("The three points must have three different x values.")
        steps.append("<b>Three points fix a quadratic.</b> Put each point into y = ax&sup2; + bx + c to get three equations:")
        for i, (x, y) in enumerate(pts, 1):
            steps.append(f"Point {i}: ({ns(x)}, {ns(y)}) gives &nbsp; {ns(x * x)}a {sgt(x)}b + c = {ns(y)}")
        (x1, y1), (x2, y2), (x3, y3) = pts
        # subtract equations
        A1, B1, R1 = x1 * x1 - x2 * x2, x1 - x2, y1 - y2
        A2, B2, R2 = x2 * x2 - x3 * x3, x2 - x3, y2 - y3
        steps.append(f"<b>Subtract</b> equation 2 from 1, and 3 from 2, to remove c: &nbsp; {ns(A1)}a {sgt(B1)}b = {ns(R1)} &nbsp; and &nbsp; {ns(A2)}a {sgt(B2)}b = {ns(R2)}")
        det = A1 * B2 - A2 * B1
        if det == 0:
            raise UErr("These points do not lie on a quadratic curve (they may lie on a straight line).")
        a = (R1 * B2 - R2 * B1) / det
        b = (A1 * R2 - A2 * R1) / det
        c = y1 - a * x1 * x1 - b * x1
        steps.append(f"<b>Solve these two:</b> a = {HL(ns(a))}, b = {HL(ns(b))}. Put back into equation 1: c = {ns(y1)} &minus; {ns(a * x1 * x1)} &minus; {ns(b * x1)} = {HL(ns(c))}")
        if a == 0:
            raise UErr("The three points lie on a straight line, so a = 0 and it is not a quadratic.")
        steps.append(f"<b>Answer:</b> y = {HL(poly_txt(a, b, c))}")
    return _ok(steps, {"image": plot(a, b, c), "text": f"<b>y = {poly_txt(a, b, c)}</b>"})


@guard
def line_meets(d):
    a, b, c = coefs(d)
    m = Fraction(num(d.get("m"), "The gradient m"))
    n = Fraction(num(d.get("n"), "The intercept n", True) or 0)
    steps = [f"<b>Where does the curve y = {poly_txt(a, b, c)} meet the line y = {poly_txt(0, m, n)}?</b> At those points both y values are equal, so set the two right-hand sides equal:",
             f"{poly_txt(a, b, c)} = {poly_txt(0, m, n)}"]
    A, B, C = a, b - m, c - n
    steps.append(f"<b>Move everything to one side</b> so the other side is 0: {HL(poly_txt(A, B, C) + ' = 0')}")
    D = B * B - 4 * A * C
    steps.append(f"<b>Discriminant:</b> B&sup2; &minus; 4AC = ({ns(B)})&sup2; &minus; 4({ns(A)})({ns(C)}) = {HL(ns(D))}")
    pts = []
    if D < 0:
        steps.append("D is negative: the line and the curve <b>never meet</b>.")
        res = "The line does not meet the curve."
    else:
        if D == 0:
            steps.append("D = 0: the line <b>touches</b> the curve at exactly one point (it is a <b>tangent</b>).")
        else:
            steps.append("D is positive: the line cuts the curve at <b>two points</b>.")
        s = math.sqrt(float(D))
        xs = sorted({(-float(B) - s) / (2 * float(A)), (-float(B) + s) / (2 * float(A))})
        steps.append(f"x = ({ns(-B)} &plusmn; {rt(D)}) &divide; {ns(2 * A)}, so x = " + " or x = ".join(fm(x, 3).replace("-", MINUS) for x in xs))
        for x in xs:
            y = float(m) * x + float(n)
            pts.append((x, y))
        steps.append("<b>Find y</b> by putting each x into the straight line (it is easier): " + "; ".join(f"x = {fm(x, 3)} gives y = {fm(y, 3)}".replace("-", MINUS) for x, y in pts))
        res = "Meeting point(s): " + " and ".join(f"({fm(x, 3)}, {fm(y, 3)})" for x, y in pts)
        res = res.replace("-", MINUS)
    img = plot(a, b, c, extra_curves=[(float(m), float(n), ORANGE, "y = " + re.sub("<[^>]+>", "", poly_txt(0, m, n)).replace(MINUS, "-").replace("&minus;", "-"))], roots=[], pts=pts, label_pts=False, axis=False, vertex=False)
    return _ok(steps, {"image": img, "text": f"<b>{res}</b>"})


SPEC = {
    "title": "Quadratic Functions & Graphs",
    "intro": "Everything about y = ax&sup2; + bx + c: <b>vertex, axis of symmetry, roots, intercepts, completing the square</b>, a table of values and a clear graph.",
    "tabs": [
        {"id": "qa", "label": "Analyse y = ax²+bx+c", "title": "Analyse a quadratic and sketch its graph", "endpoint": "analyse",
         "hint": "Type a, b and c from y = ax&sup2; + bx + c. Leave b or c empty if that term is missing. Example: y = x&sup2; &minus; 4x &minus; 5 means a = 1, b = &minus;4, c = &minus;5.",
         "fields": [field("a", "a (number in front of x&sup2;)", "1"), field("b", "b (number in front of x)", "-4"), field("c", "c (the plain number)", "-5")], "button": "Analyse"},
        {"id": "qt", "label": "Table and graph", "title": "Table of values and graph", "endpoint": "table_graph",
         "fields": [field("a", "a", "1"), field("b", "b", "-4"), field("c", "c", "-5"), field("x0", "x from", "-2"), field("x1", "x to", "6")], "button": "Make table"},
        {"id": "qb", "label": "Find the equation", "title": "Find the equation of a quadratic", "endpoint": "build",
         "fields": [select("mode", "I know", [("roots", "the roots (x-intercepts)"), ("vertex", "the vertex"), ("pts", "three points on it")], wide=True),
                    field("p", "First root", "-1", show_if={"mode": "roots"}), field("q", "Second root", "5", show_if={"mode": "roots"}),
                    field("a", "a (empty = 1)", "1", show_if={"mode": "roots"}),
                    field("h", "Vertex x", "2", show_if={"mode": "vertex"}), field("k", "Vertex y", "-9", show_if={"mode": "vertex"}), field("a", "a", "1", show_if={"mode": "vertex"}),
                    field("x1", "Point 1: x", "0", show_if={"mode": "pts"}), field("y1", "Point 1: y", "-5", show_if={"mode": "pts"}),
                    field("x2", "Point 2: x", "1", show_if={"mode": "pts"}), field("y2", "Point 2: y", "-8", show_if={"mode": "pts"}),
                    field("x3", "Point 3: x", "5", show_if={"mode": "pts"}), field("y3", "Point 3: y", "0", show_if={"mode": "pts"})], "button": "Find equation"},
        {"id": "ql", "label": "Line meets curve", "title": "Where does a straight line meet the curve?", "endpoint": "line_meets",
         "fields": [field("a", "a", "1"), field("b", "b", "-4"), field("c", "c", "-5"), field("m", "Line gradient m", "1"), field("n", "Line intercept n", "-1")], "button": "Find meeting points"},
    ],
}
topics.register("quadgraph", SPEC, {"analyse": analyse, "table_graph": table_graph, "build": build, "line_meets": line_meets})
