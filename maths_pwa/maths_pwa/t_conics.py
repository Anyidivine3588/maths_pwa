"""Conic sections: ellipse, parabola and hyperbola (pure Python + matplotlib)."""
import math
from fractions import Fraction
from math import isqrt

import topics
from tcommon import UErr, fm, num, pos, field, select, guard, _ok, _fail
from frac_numeric import FR, fr, table

MINUS = "&minus;"
TIMES = "&times;"
DEG = "&deg;"
BLUE, RED, GREEN, ORANGE, PURPLE, GREY, INK = "#1d4ed8", "#dc2626", "#059669", "#d97706", "#7c3aed", "#64748b", "#0f172a"


def HL(s):
    return f"<span class='hl'>{s}</span>"


def nm(v, p=3):
    return fm(v, p).replace("-", MINUS)


def ns(v):
    """number text: integer or p/q (plain)"""
    v = Fraction(v)
    s = str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
    return s.replace("-", MINUS)


def shift(var, h):
    h = Fraction(h)
    if h == 0:
        return var
    return f"({var} {MINUS} {ns(h)})" if h > 0 else f"({var} + {ns(-h)})"


def sg(c, v=''):
    """' + 3x' / ' &minus; 3x' (empty if 0)"""
    c = Fraction(c)
    if c == 0:
        return ''
    return f" {'+' if c > 0 else MINUS} {ns(abs(c))}{v}"


def fac(four_p, var, k):
    k = Fraction(k)
    return f"{ns(four_p)}({var} {MINUS if k > 0 else '+'} {ns(abs(k))})" if k != 0 else f"{ns(four_p)}{var}"


def sq(s):
    return f"{s}<sup>2</sup>"


def rt_parts(x):
    """sqrt of a non-negative Fraction -> (Fraction or None, float)"""
    x = Fraction(x)
    p, q = x.numerator, x.denominator
    ip, iq = isqrt(p), isqrt(q)
    if ip * ip == p and iq * iq == q:
        return Fraction(ip, iq), float(Fraction(ip, iq))
    return None, math.sqrt(float(x))


def rt(x):
    """text for sqrt(x): exact if neat, else surd + decimal"""
    ex, f = rt_parts(x)
    if ex is not None:
        return ns(ex)
    x = Fraction(x)
    inner = str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"
    return f"&radic;{inner} &asymp; {fm(f, 3)}"


def rtv(x):
    return rt_parts(x)[1]


def pt(x, y):
    return f"({ns(x)}, {ns(y)})"


def ptf(xf, yf):
    return f"({fm(xf, 3).replace('-', MINUS)}, {fm(yf, 3).replace('-', MINUS)})"


def stack(n, d):
    return FR(n, d)


def gen_eq(A, B, D, E, F):
    parts = []

    def add(c, v):
        c = Fraction(c)
        if c == 0:
            return
        sign = MINUS if c < 0 else "+"
        a = abs(c)
        co = "" if (a == 1 and v) else ns(a)
        t = f"{co}{v}"
        if not parts:
            parts.append((MINUS if c < 0 else "") + t)
        else:
            parts.append(f" {sign} {t}")

    add(A, "x<sup>2</sup>")
    add(B, "y<sup>2</sup>")
    add(D, "x")
    add(E, "y")
    add(F, "")
    return ("".join(parts) or "0") + " = 0"


# ================================================================= plotting =====

def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _canvas(boxpts):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    xs = [p[0] for p in boxpts] + [0]
    ys = [p[1] for p in boxpts] + [0]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = x1 - x0 or 1, y1 - y0 or 1
    s = max(w, h)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    half = s * 0.62
    ax.set_xlim(cx - half * 1.05, cx + half * 1.05)
    ax.set_ylim(cy - half, cy + half)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, color="#e2e8f0", lw=0.8)
    ax.axhline(0, color="#475569", lw=1.2)
    ax.axvline(0, color="#475569", lw=1.2)
    ax.tick_params(labelsize=8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    return fig, ax


def _mark(ax, p, text, color, dx=0.0, dy=0.0, size=10):
    ax.plot([p[0]], [p[1]], "o", color=color, ms=6, zorder=6)
    ax.annotate(text, (p[0], p[1]), xytext=(6 + dx, 6 + dy), textcoords="offset points", fontsize=size, fontweight="bold", color=color,
                path_effects=_halo(), zorder=7)


def _halo():
    import matplotlib.patheffects as pe
    return [pe.withStroke(linewidth=3, foreground="white")]


def _b64(fig):
    import base64
    import io
    plt = _plt()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def plot_ellipse(h, k, a2, b2, horiz):
    a, b = rtv(a2), rtv(b2)           # a2, b2 are the denominators under x and y
    c = math.sqrt(abs(a2 - b2)) if a2 != b2 else 0.0
    h, k = float(h), float(k)
    ra, rb = a, b                      # radius in x and in y
    fig, ax = _canvas([(h - ra, k - rb), (h + ra, k + rb)])
    ts = [i / 400 * 2 * math.pi for i in range(401)]
    ax.fill([h + ra * math.cos(t) for t in ts], [k + rb * math.sin(t) for t in ts], color="#dbeafe", alpha=0.6, zorder=1)
    ax.plot([h + ra * math.cos(t) for t in ts], [k + rb * math.sin(t) for t in ts], color=BLUE, lw=2.6, zorder=3)
    ax.plot([h - ra, h + ra], [k, k], "--", color=GREY, lw=1.2)
    ax.plot([h, h], [k - rb, k + rb], "--", color=GREY, lw=1.2)
    _mark(ax, (h, k), "centre", INK, size=9)
    if a2 != b2:
        if horiz:
            f1, f2 = (h - c, k), (h + c, k)
            v1, v2 = (h - ra, k), (h + ra, k)
        else:
            f1, f2 = (h, k - c), (h, k + c)
            v1, v2 = (h, k - rb), (h, k + rb)
        _mark(ax, f1, "F₁", RED)
        _mark(ax, f2, "F₂", RED)
        _mark(ax, v1, "V₁", ORANGE)
        _mark(ax, v2, "V₂", ORANGE)
        # a point on the curve with its two focal distances
        t = math.radians(55)
        P = (h + ra * math.cos(t), k + rb * math.sin(t))
        ax.plot([f1[0], P[0], f2[0]], [f1[1], P[1], f2[1]], color=GREEN, lw=1.6, zorder=4)
        _mark(ax, P, "P", GREEN)
    return _b64(fig)


def plot_hyperbola(h, k, a2, b2, horiz):
    a, b = rtv(a2), rtv(b2)
    c = math.sqrt(a2 + b2)
    h, k = float(h), float(k)
    reach = max(a, b, c) * 2.2
    pts = [(h - reach, k - reach), (h + reach, k + reach)]
    fig, ax = _canvas(pts)
    T = math.acosh(max(1.0, reach / max(a, 1e-9))) + 0.2
    ts = [(-T + 2 * T * i / 400) for i in range(401)]
    if horiz:
        for sgn in (1, -1):
            ax.plot([h + sgn * a * math.cosh(t) for t in ts], [k + b * math.sinh(t) for t in ts], color=BLUE, lw=2.6, zorder=3)
        slope = b / a
        v1, v2 = (h - a, k), (h + a, k)
        f1, f2 = (h - c, k), (h + c, k)
    else:
        for sgn in (1, -1):
            ax.plot([h + b * math.sinh(t) for t in ts], [k + sgn * a * math.cosh(t) for t in ts], color=BLUE, lw=2.6, zorder=3)
        slope = a / b
        v1, v2 = (h, k - a), (h, k + a)
        f1, f2 = (h, k - c), (h, k + c)
    xs = [h - reach, h + reach]
    for sg in (1, -1):
        ax.plot(xs, [k + sg * slope * (x - h) for x in xs], "--", color=ORANGE, lw=1.6, zorder=2)
    _mark(ax, (h, k), "centre", INK, size=9)
    _mark(ax, v1, "V₁", ORANGE)
    _mark(ax, v2, "V₂", ORANGE)
    _mark(ax, f1, "F₁", RED)
    _mark(ax, f2, "F₂", RED)
    xl, yl = ax.get_xlim(), ax.get_ylim()
    ax.set_xlim(xl)
    ax.set_ylim(yl)
    return _b64(fig)


def plot_parabola(h, k, p, vertical):
    h, k, p = float(h), float(k), float(p)
    H = max(5 * abs(p), 4.0)
    R = math.sqrt(4 * abs(p) * H)
    if vertical:
        focus = (h, k + p)
        pts = [(h - R, k - 0.2 * H), (h + R, k + H), focus, (h, k - abs(p))]
    else:
        focus = (h + p, k)
        pts = [(h - 0.2 * H, k - R), (h + H, k + R), focus, (h - abs(p), k)]
    fig, ax = _canvas(pts)
    ts = [(-1 + 2 * i / 400) for i in range(401)]
    sgn = 1 if p > 0 else -1
    if vertical:
        xs = [h + R * t for t in ts]
        ys = [k + (x - h) ** 2 / (4 * p) for x in xs]
        ax.plot(xs, ys, color=BLUE, lw=2.6, zorder=3)
        ax.axhline(k - p, color=ORANGE, lw=1.8, ls="--", zorder=2)
        ax.plot([h, h], [k - 3 * abs(p) - 1, k + H], "--", color=GREY, lw=1.2)
        ax.annotate("directrix", (h + R * 0.55, k - p), xytext=(0, 6), textcoords="offset points", color=ORANGE, fontsize=9, fontweight="bold", ha="center", path_effects=_halo())
        X = h + 0.8 * R * 0.6
        P = (X, k + (X - h) ** 2 / (4 * p))
        ax.plot([P[0], focus[0]], [P[1], focus[1]], color=GREEN, lw=1.6, zorder=4)
        ax.plot([P[0], P[0]], [P[1], k - p], color=GREEN, lw=1.6, zorder=4)
    else:
        ys = [k + R * t for t in ts]
        xs = [h + (y - k) ** 2 / (4 * p) for y in ys]
        ax.plot(xs, ys, color=BLUE, lw=2.6, zorder=3)
        ax.axvline(h - p, color=ORANGE, lw=1.8, ls="--", zorder=2)
        ax.plot([h - 3 * abs(p) - 1, h + H], [k, k], "--", color=GREY, lw=1.2)
        ax.annotate("directrix", (h - p, k + R * 0.55), xytext=(6, 0), textcoords="offset points", color=ORANGE, fontsize=9, fontweight="bold", path_effects=_halo())
        Y = k + 0.8 * R * 0.6
        P = (h + (Y - k) ** 2 / (4 * p), Y)
        ax.plot([P[0], focus[0]], [P[1], focus[1]], color=GREEN, lw=1.6, zorder=4)
        ax.plot([P[0], h - p], [P[1], P[1]], color=GREEN, lw=1.6, zorder=4)
    _mark(ax, (h, k), "vertex", ORANGE, size=9)
    _mark(ax, focus, "focus", RED, size=9)
    _mark(ax, P, "P", GREEN)
    return _b64(fig)


# ============================================================ analysis steps =====

DEF = {
    "ellipse": "An <b>ellipse</b> is a stretched circle (an oval). Pick any point P on it and measure its distance to two fixed points called the <b>foci</b> (F&#8321; and F&#8322;): those two distances <b>always add up to the same number, 2a</b>.",
    "hyperbola": "A <b>hyperbola</b> has two separate curved branches that open away from each other. For any point P on it, the <b>difference</b> between its distances to the two <b>foci</b> is always the same number, <b>2a</b>.",
    "parabola": "A <b>parabola</b> is the shape of the graph of y = x&sup2;. Every point P on it is <b>the same distance from a fixed point (the focus) and a fixed line (the directrix)</b>.",
}


def describe_ellipse(h, k, A2, B2, steps, via=""):
    """(x-h)^2/A2 + (y-k)^2/B2 = 1 with A2, B2 > 0"""
    h, k, A2, B2 = map(Fraction, (h, k, A2, B2))
    horiz = A2 >= B2
    a2, b2 = (A2, B2) if horiz else (B2, A2)
    std = f"{stack(sq(shift('x', h)), ns(A2))} + {stack(sq(shift('y', k)), ns(B2))} = 1"
    steps.append(f"<b>Standard form of the ellipse:</b> {HL(std)}")
    if A2 == B2:
        r = rt(A2)
        steps.append(f"The two numbers under x and y are equal, so this is a <b>circle</b> with centre {pt(h, k)} and radius {r}.")
        rows = [("Centre", pt(h, k)), ("Radius", r)]
        steps.append(table(rows, ["Feature", "Value"]))
        return plot_ellipse(h, k, A2, B2, True), f"<b>Circle: centre {pt(h, k)}, radius {r}</b>"
    c2 = a2 - b2
    big = "horizontal" if horiz else "vertical"
    steps.append(f"<b>Read it:</b> the centre is {HL(pt(h, k))} (the opposite signs inside the brackets). "
                 f"The bigger number under the {'x' if horiz else 'y'}-bracket is a&sup2; = {ns(a2)}, and the smaller is b&sup2; = {ns(b2)}. "
                 f"So the long (major) axis is <b>{big}</b>.")
    steps.append(f"a = &radic;{ns(a2)} = {rt(a2)} &nbsp;(half the long axis) &nbsp;&nbsp; b = &radic;{ns(b2)} = {rt(b2)} &nbsp;(half the short axis)")
    steps.append(f"<b>Distance from the centre to each focus:</b> c&sup2; = a&sup2; &minus; b&sup2; = {ns(a2)} &minus; {ns(b2)} = {ns(c2)}, so c = {HL(rt(c2))}")
    a, b, c = rtv(a2), rtv(b2), rtv(c2)
    ex_a, ex_b, ex_c = rt_parts(a2)[0], rt_parts(b2)[0], rt_parts(c2)[0]
    hf, kf = float(h), float(k)
    if horiz:
        F1, F2 = ptx(h, k, -1, ex_c, c, True), ptx(h, k, 1, ex_c, c, True)
        V1, V2 = ptx(h, k, -1, ex_a, a, True), ptx(h, k, 1, ex_a, a, True)
        W1, W2 = ptx(h, k, -1, ex_b, b, False), ptx(h, k, 1, ex_b, b, False)
        dirx = f"x = {fm(hf - float(a2) / c, 3)} and x = {fm(hf + float(a2) / c, 3)}".replace("-", MINUS)
    else:
        F1, F2 = ptx(h, k, -1, ex_c, c, False), ptx(h, k, 1, ex_c, c, False)
        V1, V2 = ptx(h, k, -1, ex_a, a, False), ptx(h, k, 1, ex_a, a, False)
        W1, W2 = ptx(h, k, -1, ex_b, b, True), ptx(h, k, 1, ex_b, b, True)
        dirx = f"y = {fm(kf - float(a2) / c, 3)} and y = {fm(kf + float(a2) / c, 3)}".replace("-", MINUS)
    e = c / a
    steps.append(f"<b>Eccentricity</b> (how stretched it is, always between 0 and 1): e = c &divide; a = {fm(c, 3)} &divide; {fm(a, 3)} = {HL(fm(e, 3))}")
    rows = [("Centre", pt(h, k)), ("Vertices (ends of the long axis)", f"{V1} and {V2}"), ("Co-vertices (ends of the short axis)", f"{W1} and {W2}"),
            ("Foci", f"{F1} and {F2}"), ("Length of long (major) axis = 2a", fm(2 * a, 3)), ("Length of short (minor) axis = 2b", fm(2 * b, 3)),
            ("Eccentricity e = c/a", fm(e, 3)), ("Directrices x = h &plusmn; a&sup2;/c", dirx),
            ("Length of each latus rectum = 2b&sup2;/a", fm(2 * float(b2) / a, 3))]
    steps.append(table(rows, ["Feature", "Value"]))
    steps.append("<b>Quick check with the definition:</b> for any point P on the ellipse, PF&#8321; + PF&#8322; = 2a = " + fm(2 * a, 3) + ". (The green lines in the picture.)")
    return plot_ellipse(h, k, A2, B2, horiz), f"<b>Ellipse: centre {pt(h, k)}, foci {F1} and {F2}, e = {fm(e, 3)}</b>"


def ptx(h, k, sign, ex, f, along_x):
    """point text: centre +/- distance along x (or y), exact when possible"""
    if ex is not None:
        return pt(h + sign * ex, k) if along_x else pt(h, k + sign * ex)
    if along_x:
        return ptf(float(h) + sign * f, float(k))
    return ptf(float(h), float(k) + sign * f)


def describe_hyperbola(h, k, a2, b2, horiz, steps):
    """horiz: (x-h)^2/a2 - (y-k)^2/b2 = 1 ; else (y-k)^2/a2 - (x-h)^2/b2 = 1"""
    h, k, a2, b2 = map(Fraction, (h, k, a2, b2))
    if horiz:
        std = f"{stack(sq(shift('x', h)), ns(a2))} {MINUS} {stack(sq(shift('y', k)), ns(b2))} = 1"
    else:
        std = f"{stack(sq(shift('y', k)), ns(a2))} {MINUS} {stack(sq(shift('x', h)), ns(b2))} = 1"
    steps.append(f"<b>Standard form of the hyperbola:</b> {HL(std)}")
    steps.append(f"<b>Read it:</b> the centre is {HL(pt(h, k))}. The term with the <b>plus</b> sign in front (the first one) tells us the branches open "
                 f"<b>{'left and right' if horiz else 'up and down'}</b>. The number under it is a&sup2; = {ns(a2)}; the number under the other is b&sup2; = {ns(b2)}.")
    steps.append(f"a = &radic;{ns(a2)} = {rt(a2)} &nbsp;&nbsp; b = &radic;{ns(b2)} = {rt(b2)}")
    c2 = a2 + b2
    steps.append(f"<b>Distance from the centre to each focus</b> (for a hyperbola you ADD): c&sup2; = a&sup2; + b&sup2; = {ns(a2)} + {ns(b2)} = {ns(c2)}, so c = {HL(rt(c2))}")
    a, b, c = rtv(a2), rtv(b2), rtv(c2)
    ex_a, ex_c = rt_parts(a2)[0], rt_parts(c2)[0]
    V1, V2 = ptx(h, k, -1, ex_a, a, horiz), ptx(h, k, 1, ex_a, a, horiz)
    F1, F2 = ptx(h, k, -1, ex_c, c, horiz), ptx(h, k, 1, ex_c, c, horiz)
    e = c / a
    sl = b / a if horiz else a / b
    ex_b = rt_parts(b2)[0]
    if ex_a is not None and ex_b is not None:
        slope_txt = ns(ex_b / ex_a) if horiz else ns(ex_a / ex_b)
    else:
        slope_txt = fm(sl, 3)
    asy = f"y {MINUS} {ns(k) if k != 0 else '0'} = &plusmn; {slope_txt} (x {MINUS} {ns(h) if h != 0 else '0'})"
    asy = asy.replace(f" {MINUS} 0", "").replace(f"y {MINUS} 0", "y")
    steps.append(f"<b>Asymptotes</b> (the two straight lines the branches get closer and closer to): the slopes are "
                 f"{'&plusmn; b/a' if horiz else '&plusmn; a/b'} = &plusmn; {slope_txt}, and the lines pass through the centre: {HL(asy)}")
    steps.append(f"<b>Eccentricity</b> (always bigger than 1): e = c &divide; a = {fm(c, 3)} &divide; {fm(a, 3)} = {HL(fm(e, 3))}")
    rows = [("Centre", pt(h, k)), ("Vertices", f"{V1} and {V2}"), ("Foci", f"{F1} and {F2}"),
            ("Transverse axis length = 2a", fm(2 * a, 3)), ("Conjugate axis length = 2b", fm(2 * b, 3)),
            ("Asymptotes", asy), ("Eccentricity e = c/a", fm(e, 3)),
            ("Length of each latus rectum = 2b&sup2;/a", fm(2 * float(b2) / a, 3))]
    steps.append(table(rows, ["Feature", "Value"]))
    if a == b:
        steps.append("Because a = b, this is a <b>rectangular hyperbola</b> (its asymptotes are at right angles).")
    return plot_hyperbola(h, k, a2, b2, horiz), f"<b>Hyperbola: centre {pt(h, k)}, vertices {V1} and {V2}, e = {fm(e, 3)}</b>"


def describe_parabola(h, k, p, vertical, steps):
    h, k, p = map(Fraction, (h, k, p))
    if vertical:
        std = f"{sq(shift('x', h))} = {ns(4 * p)}{shift('y', k) if k != 0 else 'y'}"
        dirn = "upwards" if p > 0 else "downwards"
        F = pt(h, k + p)
        D = f"y = {ns(k - p)}"
        axis = f"x = {ns(h)}"
        lr = pt(h - 2 * abs(p), k + p) + " to " + pt(h + 2 * abs(p), k + p)
    else:
        std = f"{sq(shift('y', k))} = {ns(4 * p)}{shift('x', h) if h != 0 else 'x'}"
        dirn = "to the right" if p > 0 else "to the left"
        F = pt(h + p, k)
        D = f"x = {ns(h - p)}"
        axis = f"y = {ns(k)}"
        lr = pt(h + p, k - 2 * abs(p)) + " to " + pt(h + p, k + 2 * abs(p))
    steps.append(f"<b>Standard form of the parabola:</b> {HL(std)} &nbsp; which matches {'(x &minus; h)&sup2; = 4p(y &minus; k)' if vertical else '(y &minus; k)&sup2; = 4p(x &minus; h)'}")
    steps.append(f"<b>Read it:</b> the <b>vertex</b> (the turning point) is {HL(pt(h, k))}. Compare the number in front with 4p: 4p = {ns(4 * p)}, so p = {HL(ns(p))}. "
                 f"p is the distance from the vertex to the focus. Because p is {'positive' if p > 0 else 'negative'} and the squared letter is {'x' if vertical else 'y'}, the parabola opens <b>{dirn}</b>.")
    rows = [("Vertex", pt(h, k)), ("Focus (vertex moved p along the axis)", F), ("Directrix", D), ("Axis of symmetry", axis),
            ("Opens", dirn), ("Latus rectum (width at the focus = 4|p|)", f"{ns(4 * abs(p))}, from {lr}"), ("Eccentricity", "1")]
    steps.append(table(rows, ["Feature", "Value"]))
    steps.append("<b>Quick check with the definition:</b> any point P on the curve is the same distance from the focus and from the directrix (the two green lines in the picture have equal length).")
    return plot_parabola(h, k, p, vertical), f"<b>Parabola: vertex {pt(h, k)}, focus {F}, directrix {D}</b>"


# ============================================================= general equation =====

def _coef(d, key, label, blank_ok=True):
    v = num(d.get(key), label, blank=blank_ok)
    return Fraction(0) if v is None else Fraction(v)


@guard
def identify(d):
    A, B = _coef(d, "A", "A"), _coef(d, "B", "B")
    Dd, E, F = _coef(d, "D", "D"), _coef(d, "E", "E"), _coef(d, "F", "F")
    for v in (A, B, Dd, E, F):
        if abs(v) > 10 ** 9:
            raise UErr("Those numbers are too big. Use smaller numbers.")
    if A == 0 and B == 0:
        raise UErr("A and B cannot both be 0. At least one of x&sup2; or y&sup2; must be in the equation.")
    steps = [f"<b>Your equation:</b> {gen_eq(A, B, Dd, E, F)} &nbsp; (written as Ax&sup2; + By&sup2; + Dx + Ey + F = 0)"]
    # ---------- parabola
    if A == 0 or B == 0:
        if B == 0:   # x squared only
            if E == 0:
                raise UErr("With only x&sup2; and no y term this is a pair of vertical lines (or nothing), not a parabola. Add a y term.")
            steps.append("<b>Which conic?</b> Only x is squared (no y&sup2;), so it is a <b>parabola</b> that opens up or down.")
            steps.append(f"<b>Get the squared part alone:</b> move y and the number to the right: x&sup2;{sg(Dd / A, 'x')} = {ns(-E / A)}y{sg(-F / A)}")
            hh = -Dd / (2 * A)
            steps.append(f"<b>Complete the square on x:</b> half of {ns(Dd / A)} is {ns(Dd / (2 * A))}; square it: {ns((Dd / (2 * A)) ** 2)}. Add it to both sides: "
                         f"(x {'+' if Dd / (2 * A) >= 0 else MINUS} {ns(abs(Dd / (2 * A)))})&sup2; = {ns(-E / A)}y{sg(-F / A + (Dd / (2 * A)) ** 2)}")
            k = -F / E + Dd * Dd / (4 * A * E)
            four_p = -E / A
            steps.append(f"<b>Factor the right side</b> so it looks like 4p(y &minus; k): {fac(four_p, 'y', k)}")
            img, ans = describe_parabola(hh, k, four_p / 4, True, steps)
        else:        # y squared only
            if Dd == 0:
                raise UErr("With only y&sup2; and no x term this is a pair of horizontal lines (or nothing), not a parabola. Add an x term.")
            steps.append("<b>Which conic?</b> Only y is squared (no x&sup2;), so it is a <b>parabola</b> that opens left or right.")
            steps.append(f"<b>Get the squared part alone:</b> y&sup2;{sg(E / B, 'y')} = {ns(-Dd / B)}x{sg(-F / B)}")
            kk = -E / (2 * B)
            steps.append(f"<b>Complete the square on y:</b> half of {ns(E / B)} is {ns(E / (2 * B))}; square it: {ns((E / (2 * B)) ** 2)}. Add it to both sides: "
                         f"(y {'+' if E / (2 * B) >= 0 else MINUS} {ns(abs(E / (2 * B)))})&sup2; = {ns(-Dd / B)}x{sg(-F / B + (E / (2 * B)) ** 2)}")
            h2 = -F / Dd + E * E / (4 * B * Dd)
            four_p = -Dd / B
            steps.append(f"<b>Factor the right side</b> so it looks like 4p(x &minus; h): {fac(four_p, 'x', h2)}")
            img, ans = describe_parabola(h2, kk, four_p / 4, False, steps)
        return _ok(steps, {"image": img, "text": ans})
    # ---------- ellipse / hyperbola
    kind = "ellipse (or circle)" if A * B > 0 else "hyperbola"
    steps.append(f"<b>Which conic?</b> Both x and y are squared. A = {ns(A)} and B = {ns(B)} have the {'<b>same</b> sign &rarr; ellipse (circle if A = B)' if A * B > 0 else '<b>opposite</b> signs &rarr; hyperbola'}.")
    gx = f"{'' if A == 1 else ns(A)}(x&sup2; {'+' if Dd / A >= 0 else MINUS} {ns(abs(Dd / A))}x)" if Dd != 0 else f"{'' if A == 1 else ns(A)}x&sup2;"
    gy = f"{'' if B == 1 else ns(B)}(y&sup2; {'+' if E / B >= 0 else MINUS} {ns(abs(E / B))}y)" if E != 0 else f"{'' if B == 1 else ns(B)}y&sup2;"
    steps.append(f"<b>Group the x terms and the y terms</b> and move the plain number across: {gx} + {gy} = {ns(-F)}")
    hx, ky = -Dd / (2 * A), -E / (2 * B)
    addx, addy = A * (Dd / (2 * A)) ** 2, B * (E / (2 * B)) ** 2
    if Dd != 0 or E != 0:
        steps.append("<b>Complete the square</b> (take half of the number in front of x, square it, and add it to BOTH sides; do the same for y). "
                     f"For x: half of {ns(Dd / A)} is {ns(Dd / (2 * A))}, squared is {ns((Dd / (2 * A)) ** 2)}"
                     + (f", and it is multiplied by {ns(A)} outside the bracket, so we really add {ns(addx)}" if A != 1 else "") + ". "
                     f"For y: half of {ns(E / B)} is {ns(E / (2 * B))}, squared is {ns((E / (2 * B)) ** 2)}"
                     + (f", times {ns(B)} gives {ns(addy)}" if B != 1 else "") + ".")
    R = -F + addx + addy
    steps.append(f"{ns(A) + '' if A != 1 else ''}{shift('x', hx) if Dd != 0 else 'x'}<sup>2</sup> + {ns(B) if B != 1 else ''}{shift('y', ky) if E != 0 else 'y'}<sup>2</sup> = {HL(ns(R))}".replace("1(", "(")
                 if False else f"<b>After completing the squares:</b> {ns(A) if A != 1 else ''}{sq(shift('x', hx))} + {ns(B) if B != 1 else ''}{sq(shift('y', ky))} = {HL(ns(R))}")
    if R == 0:
        if A * B > 0:
            raise UErr(f"The right-hand side is 0, so the only point on this graph is the single point {pt(hx, ky)}. It is not an ellipse.")
        raise UErr("The right-hand side is 0, so this is just two crossing straight lines, not a hyperbola.")
    steps.append(f"<b>Divide everything by {ns(R)}</b> so the right side becomes 1:")
    A2, B2 = R / A, R / B
    if A * B > 0:
        if A2 < 0:
            raise UErr("The right-hand side comes out negative while x&sup2; and y&sup2; are positive, so no points satisfy the equation. There is no graph.")
        img, ans = describe_ellipse(hx, ky, A2, B2, steps)
    else:
        if A2 > 0:
            img, ans = describe_hyperbola(hx, ky, A2, -B2, True, steps)
        else:
            img, ans = describe_hyperbola(hx, ky, B2, -A2, False, steps)
    return _ok(steps, {"image": img, "text": ans})


# =========================================================== build from properties =====

@guard
def ellipse(d):
    mode = d.get("mode", "axes")
    h = Fraction(num(d.get("h"), "The centre x", blank=True) or 0)
    k = Fraction(num(d.get("k"), "The centre y", blank=True) or 0)
    steps = [DEF["ellipse"]]
    if mode == "axes":
        p = Fraction(pos(d.get("p"), "The horizontal semi-axis"))
        q = Fraction(pos(d.get("q"), "The vertical semi-axis"))
        steps.append(f"<b>You know:</b> from the centre the ellipse reaches {ns(p)} sideways (left and right) and {ns(q)} up and down. "
                     f"The numbers under x and y in the equation are these distances SQUARED: {ns(p)}&sup2; = {ns(p * p)} and {ns(q)}&sup2; = {ns(q * q)}.")
        A2, B2 = p * p, q * q
    else:
        a = Fraction(pos(d.get("a"), "a (half the long axis)"))
        c = Fraction(pos(d.get("c"), "c (centre to focus)"))
        if c >= a:
            raise UErr("c (distance to a focus) must be SMALLER than a for an ellipse.")
        b2 = a * a - c * c
        horiz = d.get("orient", "h") == "h"
        steps.append(f"<b>You know:</b> a = {ns(a)} and c = {ns(c)}. Use c&sup2; = a&sup2; &minus; b&sup2;, so b&sup2; = a&sup2; &minus; c&sup2; = {ns(a * a)} &minus; {ns(c * c)} = {HL(ns(b2))}.")
        A2, B2 = (a * a, b2) if horiz else (b2, a * a)
        steps.append(f"The long axis is {'horizontal' if horiz else 'vertical'}, so a&sup2; goes under the {'x' if horiz else 'y'} term.")
    img, ans = describe_ellipse(h, k, A2, B2, steps)
    return _ok(steps, {"image": img, "text": ans})


@guard
def hyperbola(d):
    mode = d.get("mode", "ab")
    h = Fraction(num(d.get("h"), "The centre x", blank=True) or 0)
    k = Fraction(num(d.get("k"), "The centre y", blank=True) or 0)
    horiz = d.get("orient", "h") == "h"
    steps = [DEF["hyperbola"]]
    if mode == "ab":
        a = Fraction(pos(d.get("a"), "a"))
        b = Fraction(pos(d.get("b"), "b"))
        steps.append(f"<b>You know:</b> a = {ns(a)} (centre to each vertex) and b = {ns(b)}. Square them: a&sup2; = {ns(a * a)}, b&sup2; = {ns(b * b)}.")
        a2, b2 = a * a, b * b
    else:
        a = Fraction(pos(d.get("a"), "a"))
        c = Fraction(pos(d.get("c"), "c"))
        if c <= a:
            raise UErr("For a hyperbola c (centre to focus) must be BIGGER than a.")
        b2 = c * c - a * a
        a2 = a * a
        steps.append(f"<b>You know:</b> a = {ns(a)} and c = {ns(c)}. For a hyperbola c&sup2; = a&sup2; + b&sup2;, so b&sup2; = c&sup2; &minus; a&sup2; = {ns(c * c)} &minus; {ns(a * a)} = {HL(ns(b2))}.")
    steps.append(f"The branches open {'left and right' if horiz else 'up and down'}.")
    img, ans = describe_hyperbola(h, k, a2, b2, horiz, steps)
    return _ok(steps, {"image": img, "text": ans})


@guard
def parabola(d):
    mode = d.get("mode", "vertex")
    steps = [DEF["parabola"]]
    if mode == "vertex":
        h = Fraction(num(d.get("h"), "The vertex x", blank=True) or 0)
        k = Fraction(num(d.get("k"), "The vertex y", blank=True) or 0)
        p = Fraction(pos(d.get("p"), "p (vertex to focus)"))
        direction = d.get("dir", "up")
        vertical = direction in ("up", "down")
        sign = 1 if direction in ("up", "right") else -1
        pp = p * sign
        steps.append(f"<b>You know:</b> vertex {pt(h, k)} and p = {ns(p)}, opening {direction}. The equation is "
                     f"{'(x &minus; h)&sup2; = 4p(y &minus; k)' if vertical else '(y &minus; k)&sup2; = 4p(x &minus; h)'} with 4p = {ns(4 * pp)} "
                     f"({'negative because it opens ' + direction if sign < 0 else 'positive'}).")
    elif mode == "focus":
        fx = Fraction(num(d.get("fx"), "The focus x"))
        fy = Fraction(num(d.get("fy"), "The focus y"))
        which = d.get("dline", "y")
        c0 = Fraction(num(d.get("dv"), "The directrix value"))
        if which == "y":
            if fy == c0:
                raise UErr("The focus cannot lie on the directrix.")
            h, k = fx, (fy + c0) / 2
            pp = (fy - c0) / 2
            vertical = True
            steps.append(f"<b>Use the definition.</b> P(x, y) is the same distance from the focus ({ns(fx)}, {ns(fy)}) and the line y = {ns(c0)}:<br>"
                         f"(x {MINUS} {ns(fx)})&sup2; + (y {MINUS} {ns(fy)})&sup2; = (y {MINUS} {ns(c0)})&sup2; (squared both distances)<br>"
                         f"(x {MINUS} {ns(fx)})&sup2; = (y {MINUS} {ns(c0)})&sup2; {MINUS} (y {MINUS} {ns(fy)})&sup2; = {ns(2 * (fy - c0))}(y {MINUS} {ns(k)})<br>"
                         f"The vertex is half way between focus and directrix: {pt(h, k)}, and p = {ns(pp)}.")
        else:
            if fx == c0:
                raise UErr("The focus cannot lie on the directrix.")
            k, h = fy, (fx + c0) / 2
            pp = (fx - c0) / 2
            vertical = False
            steps.append(f"<b>Use the definition.</b> P(x, y) is the same distance from the focus ({ns(fx)}, {ns(fy)}) and the line x = {ns(c0)}:<br>"
                         f"(x {MINUS} {ns(fx)})&sup2; + (y {MINUS} {ns(fy)})&sup2; = (x {MINUS} {ns(c0)})&sup2;<br>"
                         f"(y {MINUS} {ns(fy)})&sup2; = (x {MINUS} {ns(c0)})&sup2; {MINUS} (x {MINUS} {ns(fx)})&sup2; = {ns(2 * (fx - c0))}(x {MINUS} {ns(h)})<br>"
                         f"The vertex is half way between focus and directrix: {pt(h, k)}, and p = {ns(pp)}.")
    else:
        raise UErr("Choose what you know.")
    if mode == "vertex":
        pass
    img, ans = describe_parabola(h, k, pp, vertical, steps)
    return _ok(steps, {"image": img, "text": ans})


# ===================================================================== spec ==

SPEC = {
    "title": "Ellipse, Parabola & Hyperbola",
    "intro": "The three conic sections, each drawn with its centre, vertices, foci, directrix or asymptotes. Type any equation like "
             "<b>4x&sup2; + 9y&sup2; &minus; 16x + 18y &minus; 11 = 0</b> into the first tab and the app completes the square for you, step by step.",
    "tabs": [
        {"id": "kid", "label": "Identify any conic", "title": "Identify and analyse any conic from its equation", "endpoint": "identify",
         "hint": "Write your equation as <b>A x&sup2; + B y&sup2; + D x + E y + F = 0</b> and type the numbers A, B, D, E, F. Leave a box empty if that term is missing (it means 0). "
                 "Example: 4x&sup2; + 9y&sup2; &minus; 16x + 18y &minus; 11 = 0 means A=4, B=9, D=&minus;16, E=18, F=&minus;11.",
         "fields": [field("A", "A (number in front of x&sup2;)", "4"), field("B", "B (number in front of y&sup2;)", "9"),
                    field("D", "D (number in front of x)", "-16"), field("E", "E (number in front of y)", "18"),
                    field("F", "F (the plain number)", "-11")], "button": "Analyse"},
        {"id": "kel", "label": "Ellipse", "title": "Build and analyse an ellipse", "endpoint": "ellipse",
         "fields": [select("mode", "I know", [("axes", "how far it reaches sideways and up/down"), ("focus", "a and c (focus distance)")], wide=True),
                    field("h", "Centre x (empty = 0)", "0"), field("k", "Centre y (empty = 0)", "0"),
                    field("p", "Horizontal semi-axis (centre to left/right end)", "5", show_if={"mode": "axes"}),
                    field("q", "Vertical semi-axis (centre to top/bottom end)", "3", show_if={"mode": "axes"}),
                    field("a", "a (half the long axis)", "5", show_if={"mode": "focus"}), field("c", "c (centre to focus)", "4", show_if={"mode": "focus"}),
                    select("orient", "Long axis is", [("h", "horizontal"), ("v", "vertical")], show_if={"mode": "focus"})]},
        {"id": "kpa", "label": "Parabola", "title": "Build and analyse a parabola", "endpoint": "parabola",
         "fields": [select("mode", "I know", [("vertex", "the vertex and p"), ("focus", "the focus and the directrix")], wide=True),
                    field("h", "Vertex x (empty = 0)", "0", show_if={"mode": "vertex"}), field("k", "Vertex y (empty = 0)", "0", show_if={"mode": "vertex"}),
                    field("p", "p (distance from vertex to focus)", "2", show_if={"mode": "vertex"}),
                    select("dir", "Opens", [("up", "upwards"), ("down", "downwards"), ("right", "to the right"), ("left", "to the left")], show_if={"mode": "vertex"}),
                    field("fx", "Focus x", "0", show_if={"mode": "focus"}), field("fy", "Focus y", "2", show_if={"mode": "focus"}),
                    select("dline", "The directrix is the line", [("y", "y = a number"), ("x", "x = a number")], show_if={"mode": "focus"}),
                    field("dv", "That number", "-2", show_if={"mode": "focus"})]},
        {"id": "khy", "label": "Hyperbola", "title": "Build and analyse a hyperbola", "endpoint": "hyperbola",
         "fields": [select("mode", "I know", [("ab", "a and b"), ("ac", "a and c (focus distance)")], wide=True),
                    field("h", "Centre x (empty = 0)", "0"), field("k", "Centre y (empty = 0)", "0"),
                    field("a", "a (centre to vertex)", "3"), field("b", "b", "4", show_if={"mode": "ab"}), field("c", "c (centre to focus)", "5", show_if={"mode": "ac"}),
                    select("orient", "Branches open", [("h", "left and right"), ("v", "up and down")])]},
    ],
}

topics.register("conics", SPEC, {"identify": identify, "ellipse": ellipse, "parabola": parabola, "hyperbola": hyperbola})
