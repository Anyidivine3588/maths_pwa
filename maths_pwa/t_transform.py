"""Transformations of shapes: reflection, rotation, translation, enlargement, describing, combining."""
import math
import re
from fractions import Fraction

import topics
from tcommon import UErr, fm, num, field, select, guard, _ok, _fail
from frac_numeric import table

MINUS = "&minus;"
BLUE, RED, GREEN, ORANGE, GREY, INK = "#1d4ed8", "#dc2626", "#059669", "#d97706", "#64748b", "#0f172a"
LET = "ABCDEFGH"


def HL(s):
    return f"<span class='hl'>{s}</span>"


def ns(v):
    v = Fraction(v)
    s = str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
    return s.replace("-", MINUS)


def P(p):
    return f"({ns(p[0])}, {ns(p[1])})"


def parse_pts(text, label="Points", lo=2, hi=8):
    t = (text or "").replace("−", "-")
    pairs = re.findall(r"\(\s*([^(),]+?)\s*,\s*([^(),]+?)\s*\)", t)
    if not pairs:
        raise UErr(f"{label}: write the corners like (1,1), (3,1), (3,2).")
    if len(pairs) < lo:
        raise UErr(f"{label}: give at least {lo} points.")
    if len(pairs) > hi:
        raise UErr(f"{label}: at most {hi} points please.")
    leftover = re.sub(r"\(\s*[^(),]+?\s*,\s*[^(),]+?\s*\)", "", t)
    if re.search(r"[^\s,;]", leftover):
        raise UErr(f"{label}: I could not read all of that. Write each corner as (x, y), separated by commas.")
    out = []
    for a, b in pairs:
        out.append((Fraction(num(a, label)), Fraction(num(b, label))))
    for p in out:
        if abs(p[0]) > 1000 or abs(p[1]) > 1000:
            raise UErr("Please keep the coordinates between &minus;1000 and 1000.")
    return out


# ------------------------------------------------------------------ plotting ----
def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _halo():
    import matplotlib.patheffects as pe
    return [pe.withStroke(linewidth=3, foreground="white")]


def _b64(fig):
    import base64
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight", facecolor="white")
    _plt().close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def draw(shapes, extra=None, link=True, pts_extra=()):
    """shapes: list of (name, points, colour, label_suffix). First is the object."""
    plt = _plt()
    allp = [(float(x), float(y)) for _, ps, _, _ in shapes for x, y in ps] + [(float(x), float(y)) for x, y in pts_extra] + [(0.0, 0.0)]
    xs, ys = [p[0] for p in allp], [p[1] for p in allp]
    pad = max(max(xs) - min(xs), max(ys) - min(ys), 4) * 0.12 + 1
    x0, x1, y0, y1 = math.floor(min(xs) - pad), math.ceil(max(xs) + pad), math.floor(min(ys) - pad), math.ceil(max(ys) + pad)
    w, h = x1 - x0, y1 - y0
    s = max(w, h)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0, x1, y0, y1 = cx - s / 2, cx + s / 2, cy - s / 2, cy + s / 2
    fig, ax = plt.subplots(figsize=(6.4, 6.4))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal", adjustable="box")
    step = 1 if s <= 16 else (2 if s <= 32 else (5 if s <= 80 else 20))
    ax.set_xticks([t for t in range(int(math.floor(x0)), int(math.ceil(x1)) + 1) if t % step == 0])
    ax.set_yticks([t for t in range(int(math.floor(y0)), int(math.ceil(y1)) + 1) if t % step == 0])
    ax.grid(True, color="#e2e8f0", lw=0.8)
    ax.axhline(0, color="#334155", lw=1.4)
    ax.axvline(0, color="#334155", lw=1.4)
    ax.tick_params(labelsize=8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    if extra:
        extra(ax, (x0, x1, y0, y1))
    obj = shapes[0][1]
    for name, ps, col, suf in shapes:
        xx = [float(p[0]) for p in ps] + [float(ps[0][0])]
        yy = [float(p[1]) for p in ps] + [float(ps[0][1])]
        if len(ps) >= 3:
            ax.fill(xx, yy, color=col, alpha=0.18, zorder=2)
        ax.plot(xx, yy, color=col, lw=2.4, zorder=4, marker="o", ms=5)
        mx, my = sum(float(p[0]) for p in ps) / len(ps), sum(float(p[1]) for p in ps) / len(ps)
        for i, p in enumerate(ps):
            dx, dy = float(p[0]) - mx, float(p[1]) - my
            n = math.hypot(dx, dy) or 1
            ax.annotate(LET[i] + suf, (float(p[0]), float(p[1])), xytext=(dx / n * 13, dy / n * 13), textcoords="offset points", ha="center", va="center",
                        fontsize=11, fontweight="bold", color=col, path_effects=_halo(), zorder=7)
    if link:
        for name, ps, col, suf in shapes[1:]:
            for a, b in zip(obj, ps):
                ax.plot([float(a[0]), float(b[0])], [float(a[1]), float(b[1])], ":", color="#94a3b8", lw=1.1, zorder=3)
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], color=c, lw=3, label=n) for n, _, c, _ in shapes]
    ax.legend(handles=handles, loc="upper left", fontsize=9, framealpha=0.95)
    return _b64(fig)


def mirror_extra(kind, val=None, label=""):
    def f(ax, lim):
        x0, x1, y0, y1 = lim
        if kind == "v":
            ax.axvline(float(val), color=ORANGE, lw=2.2, ls="--", zorder=3)
            ax.annotate(label, (float(val), y1), xytext=(4, -14), textcoords="offset points", color=ORANGE, fontweight="bold", fontsize=10, path_effects=_halo())
        elif kind == "h":
            ax.axhline(float(val), color=ORANGE, lw=2.2, ls="--", zorder=3)
            ax.annotate(label, (x1, float(val)), xytext=(-6, 5), textcoords="offset points", ha="right", color=ORANGE, fontweight="bold", fontsize=10, path_effects=_halo())
        else:
            m = float(val)
            ax.plot([x0, x1], [m * x0, m * x1], color=ORANGE, lw=2.2, ls="--", zorder=3)
            ax.annotate(label, (x1 * 0.8, m * x1 * 0.8), xytext=(6, -14 if m > 0 else 6), textcoords="offset points", color=ORANGE, fontweight="bold", fontsize=10, path_effects=_halo())
    return f


def centre_extra(c, label="centre", rays=None):
    def f(ax, lim):
        if rays:
            for q in rays:
                ax.plot([float(c[0]), float(q[0])], [float(c[1]), float(q[1])], "--", color=ORANGE, lw=1.2, zorder=3)
        ax.plot([float(c[0])], [float(c[1])], "*", color=ORANGE, ms=15, zorder=8, mec="black")
        ax.annotate(label, (float(c[0]), float(c[1])), xytext=(8, -16), textcoords="offset points", color="#b45309", fontweight="bold", fontsize=10, path_effects=_halo(), zorder=9)
    return f


# ----------------------------------------------------------------- maths ----
def reflect(p, kind, a=Fraction(0)):
    x, y = p
    return {"x": (x, -y), "y": (-x, y), "yx": (y, x), "ynx": (-y, -x), "xa": (2 * a - x, y), "yb": (x, 2 * a - y)}[kind]


def rotate(p, c, ang):
    dx, dy = p[0] - c[0], p[1] - c[1]
    r = {90: (-dy, dx), 180: (-dx, -dy), 270: (dy, -dx)}[ang]
    return (c[0] + r[0], c[1] + r[1])


def enlarge(p, c, k):
    return (c[0] + k * (p[0] - c[0]), c[1] + k * (p[1] - c[1]))


def ptable(obj, img, tag, how, src=""):
    if how is None:
        rows = [(f"{LET[i]}{src} = {P(o)}", f"{LET[i]}{tag} = {HL(P(q))}") for i, (o, q) in enumerate(zip(obj, img))]
        return table(rows, ["Before", "After"])
    rows = [(f"{LET[i]} = {P(o)}", how(o, i), f"{LET[i]}{tag} = {HL(P(q))}") for i, (o, q) in enumerate(zip(obj, img))]
    return table(rows, ["Object point", "Working", "Image point"])


MIRRORS = {
    "x": ("the x-axis (the line y = 0)", "(x, y) &rarr; (x, &minus;y)", "the <b>y</b> value changes sign; x stays the same", "h", Fraction(0), "x-axis (y = 0)"),
    "y": ("the y-axis (the line x = 0)", "(x, y) &rarr; (&minus;x, y)", "the <b>x</b> value changes sign; y stays the same", "v", Fraction(0), "y-axis (x = 0)"),
    "yx": ("the line y = x", "(x, y) &rarr; (y, x)", "the x and y values <b>swap places</b>", "d", Fraction(1), "y = x"),
    "ynx": ("the line y = &minus;x", "(x, y) &rarr; (&minus;y, &minus;x)", "x and y swap places AND both change sign", "d", Fraction(-1), "y = &minus;x"),
    "xa": ("the line x = a", "(x, y) &rarr; (2a &minus; x, y)", "the new x is <b>2a &minus; x</b> (as far on the other side of the line); y stays the same", "v", None, None),
    "yb": ("the line y = b", "(x, y) &rarr; (x, 2b &minus; y)", "the new y is <b>2b &minus; y</b>; x stays the same", "h", None, None),
}

WHAT = {
    "reflect": "A <b>reflection</b> flips the shape over a mirror line, like looking in a mirror. Each point and its image are the <b>same distance from the mirror line</b>, on opposite sides. The shape stays exactly the same size.",
    "rotate": "A <b>rotation</b> turns the shape about a fixed point called the <b>centre of rotation</b>. Anticlockwise is the positive direction. The shape stays the same size.",
    "translate": "A <b>translation</b> slides every point of the shape the same distance in the same direction. Nothing turns, nothing flips, nothing changes size.",
    "enlarge": "An <b>enlargement</b> makes the shape bigger or smaller. It needs a <b>centre of enlargement</b> and a <b>scale factor k</b>. Every point moves so that its distance from the centre is multiplied by k.",
}


@guard
def reflection(d):
    obj = parse_pts(d.get("pts"), "The shape's corners", 1)
    kind = d.get("line", "x")
    a = Fraction(0)
    nm_, rule, why, mk, mv, lab = MIRRORS[kind]
    if kind in ("xa", "yb"):
        a = Fraction(num(d.get("a"), "The number a (or b)"))
        lab = f"x = {ns(a)}" if kind == "xa" else f"y = {ns(a)}"
        nm_ = f"the line {lab}"
        mv = a
    steps = [WHAT["reflect"], f"<b>Mirror line:</b> {nm_}.", f"<b>Rule:</b> {HL(rule)} &mdash; {why}."]
    img = [reflect(p, kind, a) for p in obj]
    if kind == "x":
        how = lambda o, i: f"({ns(o[0])}, &minus;({ns(o[1])}))"
    elif kind == "y":
        how = lambda o, i: f"(&minus;({ns(o[0])}), {ns(o[1])})"
    elif kind == "yx":
        how = lambda o, i: f"swap: ({ns(o[1])}, {ns(o[0])})"
    elif kind == "ynx":
        how = lambda o, i: f"(&minus;({ns(o[1])}), &minus;({ns(o[0])}))"
    elif kind == "xa":
        how = lambda o, i: f"(2&times;{ns(a)} &minus; ({ns(o[0])}), {ns(o[1])})"
    else:
        how = lambda o, i: f"({ns(o[0])}, 2&times;{ns(a)} &minus; ({ns(o[1])}))"
    steps.append(ptable(obj, img, "'", how))
    steps.append("<b>Check by eye:</b> in the picture, each dotted line joining a point to its image is cut in half by the mirror line, at a right angle.")
    ex = mirror_extra({"h": "h", "v": "v", "d": "d"}[mk], mv, lab.replace("&minus;", "-"))
    image = draw([("Object", obj, BLUE, ""), ("Image", img, RED, "'")], ex)
    return _ok(steps, {"image": image, "text": f"<b>Image: {', '.join(LET[i] + chr(39) + ' ' + P(q) for i, q in enumerate(img))}</b>"})


@guard
def rotation(d):
    obj = parse_pts(d.get("pts"), "The shape's corners", 1)
    c = (Fraction(num(d.get("cx"), "Centre x", True) or 0), Fraction(num(d.get("cy"), "Centre y", True) or 0))
    deg = int(d.get("deg", "90"))
    way = d.get("dir", "acw")
    ang = deg if way == "acw" else (360 - deg) % 360
    if ang == 0:
        ang = 360
    steps = [WHAT["rotate"], f"<b>You asked for:</b> a turn of {deg}&deg; {'anticlockwise' if way == 'acw' else 'clockwise'} about {P(c)}."]
    if ang == 360:
        raise UErr("That is a full turn, so the shape does not move.")
    steps.append(f"A clockwise turn of {deg}&deg; is the same as an anticlockwise turn of {360 - deg}&deg;, so we use <b>{ang}&deg; anticlockwise</b>." if way == "cw" else f"We use {ang}&deg; anticlockwise.")
    rule = {90: "(dx, dy) &rarr; (&minus;dy, dx)", 180: "(dx, dy) &rarr; (&minus;dx, &minus;dy)", 270: "(dx, dy) &rarr; (dy, &minus;dx)"}[ang]
    steps.append("<b>Method (3 easy moves for every point):</b><br>1) Find dx and dy: how far the point is from the centre (point &minus; centre).<br>"
                 f"2) Turn them with the rule {HL(rule)}.<br>3) Add the centre back to get the image.")
    img, rows = [], []
    for i, o in enumerate(obj):
        dx, dy = o[0] - c[0], o[1] - c[1]
        q = rotate(o, c, ang)
        img.append(q)
        ndx, ndy = q[0] - c[0], q[1] - c[1]
        rows.append((f"{LET[i]} = {P(o)}", f"dx = {ns(dx)}, dy = {ns(dy)}", f"turned: ({ns(ndx)}, {ns(ndy)})", f"{LET[i]}' = {HL(P(q))}"))
    steps.append(table(rows, ["Object point", "Distance from centre", "After the turn", "Image point"]))
    steps.append("<b>Check:</b> every point and its image are the same distance from the centre (the shape swings round like a clock hand).")
    image = draw([("Object", obj, BLUE, ""), ("Image", img, RED, "'")], centre_extra(c, f"centre {P(c)}".replace("&minus;", "-")), link=False,
                 pts_extra=[c])
    return _ok(steps, {"image": image, "text": f"<b>Image: {', '.join(LET[i] + chr(39) + ' ' + P(q) for i, q in enumerate(img))}</b>"})


@guard
def translation(d):
    obj = parse_pts(d.get("pts"), "The shape's corners", 1)
    vx = Fraction(num(d.get("vx"), "The top number of the vector"))
    vy = Fraction(num(d.get("vy"), "The bottom number of the vector"))
    steps = [WHAT["translate"],
             f"<b>The column vector</b> <table class='mx'><tr><td>{ns(vx)}</td></tr><tr><td>{ns(vy)}</td></tr></table> means: move <b>{ns(abs(vx))} {'right' if vx >= 0 else 'left'}</b> "
             f"(top number = x direction) and <b>{ns(abs(vy))} {'up' if vy >= 0 else 'down'}</b> (bottom number = y direction).",
             f"<b>Rule:</b> {HL('(x, y) &rarr; (x + ' + ns(vx) + ', y + ' + ns(vy) + ')')}".replace("+ &minus;", "&minus; ")]
    img = [(o[0] + vx, o[1] + vy) for o in obj]
    steps.append(ptable(obj, img, "'", lambda o, i: f"({ns(o[0])} {'+' if vx >= 0 else MINUS} {ns(abs(vx))}, {ns(o[1])} {'+' if vy >= 0 else MINUS} {ns(abs(vy))})"))
    steps.append("<b>Check:</b> every dotted line in the picture is parallel and the same length. The shape looks identical, just moved.")
    image = draw([("Object", obj, BLUE, ""), ("Image", img, RED, "'")])
    return _ok(steps, {"image": image, "text": f"<b>Image: {', '.join(LET[i] + chr(39) + ' ' + P(q) for i, q in enumerate(img))}</b>"})


@guard
def enlargement(d):
    obj = parse_pts(d.get("pts"), "The shape's corners", 1)
    c = (Fraction(num(d.get("cx"), "Centre x", True) or 0), Fraction(num(d.get("cy"), "Centre y", True) or 0))
    k = Fraction(num(d.get("k"), "The scale factor k"))
    if k == 0:
        raise UErr("The scale factor cannot be 0.")
    if abs(k) > 100:
        raise UErr("Please use a scale factor between &minus;100 and 100.")
    steps = [WHAT["enlarge"], f"<b>Centre:</b> {P(c)} &nbsp; <b>Scale factor:</b> k = {ns(k)}"]
    if k < 0:
        steps.append("A <b>negative</b> scale factor puts the image on the <b>opposite side</b> of the centre, and turns it upside down (like a 180&deg; turn as well as a size change).")
    elif abs(k) < 1:
        steps.append("The scale factor is between 0 and 1, so this is a <b>reduction</b> (the shape gets smaller).")
    elif k == 1:
        steps.append("Scale factor 1 means no change at all.")
    else:
        steps.append("The scale factor is bigger than 1, so the shape gets <b>bigger</b>.")
    steps.append(f"<b>Method for every point:</b><br>1) Find dx and dy: the distance from the centre (point &minus; centre).<br>2) Multiply both by k = {ns(k)}.<br>3) Add the centre back. "
                 f"In short: {HL('image = centre + k &times; (point &minus; centre)')}")
    img, rows = [], []
    for i, o in enumerate(obj):
        dx, dy = o[0] - c[0], o[1] - c[1]
        q = enlarge(o, c, k)
        img.append(q)
        rows.append((f"{LET[i]} = {P(o)}", f"dx = {ns(dx)}, dy = {ns(dy)}", f"&times;{ns(k)}: ({ns(dx * k)}, {ns(dy * k)})", f"{LET[i]}' = {HL(P(q))}"))
    steps.append(table(rows, ["Object point", "Distance from centre", "Multiplied by k", "Image point"]))
    if len(obj) >= 2:
        L0 = math.hypot(float(obj[0][0] - obj[1][0]), float(obj[0][1] - obj[1][1]))
        L1 = math.hypot(float(img[0][0] - img[1][0]), float(img[0][1] - img[1][1]))
        steps.append(f"<b>Check:</b> side AB has length {fm(L0, 3)}; side A'B' has length {fm(L1, 3)}. {fm(L1, 3)} &divide; {fm(L0, 3)} = {fm(L1 / L0, 3)} = |k|. "
                     f"Areas change by k&sup2; = {ns(k * k)} times.")
    image = draw([("Object", obj, BLUE, ""), ("Image", img, RED, "'")], centre_extra(c, f"centre {P(c)}".replace("&minus;", "-"), rays=img), link=False, pts_extra=[c])
    return _ok(steps, {"image": image, "text": f"<b>Image: {', '.join(LET[i] + chr(39) + ' ' + P(q) for i, q in enumerate(img))}</b>"})


# ---------------------------------------------------------- identify ----
def line_text(mx, my, dx, dy):
    """perpendicular bisector line through (mx,my), normal (dx,dy)"""
    if dy == 0:
        return f"x = {ns(mx)}"
    if dx == 0:
        return f"y = {ns(my)}"
    m = -dx / dy
    cc = my - m * mx
    mt = "" if m == 1 else (MINUS if m == -1 else ns(m))
    if m == -1:
        mt = MINUS
    t = f"y = {mt}x"
    if cc != 0:
        t += f" {'+' if cc > 0 else MINUS} {ns(abs(cc))}"
    return t


def solve2(a1, b1, c1, a2, b2, c2):
    det = a1 * b2 - a2 * b1
    if det == 0:
        return None
    return ((c1 * b2 - c2 * b1) / det, (a1 * c2 - a2 * c1) / det)


def identify_core(obj, img, steps):
    n = len(obj)
    if all(o == q for o, q in zip(obj, img)):
        steps.append("The object and the image are exactly the same, so nothing has moved (identity).")
        return "No change (the shape did not move)", None
    # translation
    v = (img[0][0] - obj[0][0], img[0][1] - obj[0][1])
    if all((q[0] - o[0], q[1] - o[1]) == v for o, q in zip(obj, img)):
        steps.append(f"<b>Test 1: every point moves by the same amount?</b> Image &minus; object for each point: "
                     + ", ".join(f"{LET[i]}: ({ns(q[0] - o[0])}, {ns(q[1] - o[1])})" for i, (o, q) in enumerate(zip(obj, img)))
                     + ". They are all the same, so it is a <b>translation</b>.")
        return f"<b>Translation</b> by the vector ({ns(v[0])}, {ns(v[1])}): {ns(abs(v[0]))} {'right' if v[0] >= 0 else 'left'} and {ns(abs(v[1]))} {'up' if v[1] >= 0 else 'down'}", None
    steps.append("<b>Test 1:</b> the points do not all move by the same amount, so it is not a simple translation.")
    if n < 2:
        return None, "With one point I cannot tell which transformation it is. Give at least 2 points (3 is best)."
    # enlargement
    o0, o1, q0, q1 = obj[0], obj[1], img[0], img[1]
    dxo, dyo = o1[0] - o0[0], o1[1] - o0[1]
    dxq, dyq = q1[0] - q0[0], q1[1] - q0[1]
    k = None
    if dxo != 0 and dxq * dyo == dyq * dxo:
        k = dxq / dxo
    elif dyo != 0 and dxq * dyo == dyq * dxo:
        k = dyq / dyo
    if k is not None and k != 0 and k != 1:
        c = ((img[0][0] - k * obj[0][0]) / (1 - k), (img[0][1] - k * obj[0][1]) / (1 - k))
        if all(enlarge(o, c, k) == q for o, q in zip(obj, img)):
            steps.append(f"<b>Test 2: are the sides in the same direction but a different length?</b> Side AB goes ({ns(dxo)}, {ns(dyo)}) and side A'B' goes ({ns(dxq)}, {ns(dyq)}). "
                         f"A'B' is {ns(k)} times AB, so the scale factor is <b>k = {ns(k)}</b>. The centre is where the lines joining each point to its image meet: "
                         f"from A' = centre + k(A &minus; centre) we get centre = (A' &minus; kA) &divide; (1 &minus; k) = {HL(P(c))}.")
            return f"<b>Enlargement</b>, centre {P(c)}, scale factor {ns(k)}" + (" (this is also a rotation of 180&deg; about the same centre)" if k == -1 else ""), None
    # same size? rotation or reflection
    sq = lambda a, b: (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
    if sq(o0, o1) != sq(q0, q1):
        return None, "The size changed, but not in a way that fits one enlargement. It may be a combination of transformations."
    steps.append("<b>Test 2:</b> the size is the same (side AB and side A'B' have equal length), so it is a rotation or a reflection.")
    # find two points that moved
    moved = [i for i in range(n) if obj[i] != img[i]]
    # reflection candidate
    i0 = moved[0]
    dxm, dym = img[i0][0] - obj[i0][0], img[i0][1] - obj[i0][1]
    mx, my = (img[i0][0] + obj[i0][0]) / 2, (img[i0][1] + obj[i0][1]) / 2
    def refl_pt(p):
        # reflect p in line through (mx,my) with normal (dxm,dym)
        t = ((p[0] - mx) * dxm + (p[1] - my) * dym) / (dxm * dxm + dym * dym)
        return (p[0] - 2 * t * dxm, p[1] - 2 * t * dym)
    if all(refl_pt(o) == q for o, q in zip(obj, img)):
        lt = line_text(mx, my, dxm, dym)
        steps.append(f"<b>Test 3: is there a mirror line?</b> Take {LET[i0]} and {LET[i0]}'. The mirror line passes through the <b>midpoint</b> of {LET[i0]}{LET[i0]}' = {P((mx, my))} at a <b>right angle</b> to {LET[i0]}{LET[i0]}'. "
                     f"That line is {HL(lt)}. Reflecting every point in it gives the image exactly, so it is a <b>reflection</b>.")
        return f"<b>Reflection</b> in the line {lt}", None
    # rotation: centre from two moved points
    if len(moved) >= 2:
        j = moved[1]
        a1, b1 = img[i0][0] - obj[i0][0], img[i0][1] - obj[i0][1]
        c1 = a1 * mx + b1 * my
        a2, b2 = img[j][0] - obj[j][0], img[j][1] - obj[j][1]
        m2x, m2y = (img[j][0] + obj[j][0]) / 2, (img[j][1] + obj[j][1]) / 2
        c2 = a2 * m2x + b2 * m2y
        cen = solve2(a1, b1, c1, a2, b2, c2)
        if cen is not None:
            ok = True
            angs = set()
            for o, q in zip(obj, img):
                if (o[0] - cen[0]) ** 2 + (o[1] - cen[1]) ** 2 != (q[0] - cen[0]) ** 2 + (q[1] - cen[1]) ** 2:
                    ok = False
                    break
            if ok and (obj[i0] != cen):
                u = (obj[i0][0] - cen[0], obj[i0][1] - cen[1])
                w = (img[i0][0] - cen[0], img[i0][1] - cen[1])
                ang = math.degrees(math.atan2(float(u[0] * w[1] - u[1] * w[0]), float(u[0] * w[0] + u[1] * w[1])))
                ang = round(ang, 2)
                good = True
                r = math.radians(ang)
                for o, q in zip(obj, img):
                    dx, dy = float(o[0] - cen[0]), float(o[1] - cen[1])
                    nx = float(cen[0]) + dx * math.cos(r) - dy * math.sin(r)
                    ny = float(cen[1]) + dx * math.sin(r) + dy * math.cos(r)
                    if abs(nx - float(q[0])) > 0.02 or abs(ny - float(q[1])) > 0.02:
                        good = False
                if good:
                    a_abs = abs(ang)
                    if abs(a_abs - round(a_abs)) < 0.01:
                        a_abs = round(a_abs)
                    way = "anticlockwise" if ang > 0 else "clockwise"
                    steps.append("<b>Test 3: is there a mirror line?</b> No: reflecting does not give the image, so it is a rotation.")
                    steps.append(f"<b>Find the centre of rotation:</b> the centre is the same distance from a point and its image, so it lies on the perpendicular bisector of AA' and also of "
                                 f"{LET[j]}{LET[j]}'. Where those two lines cross is the centre: {HL(P(cen))}.")
                    steps.append(f"<b>Find the angle:</b> the turn from {LET[i0]} to {LET[i0]}' about the centre is {HL(str(a_abs) + '&deg; ' + way)}.")
                    return f"<b>Rotation</b> of {a_abs}&deg; {way} about {P(cen)}", None
    return None, "I could not match this to one single transformation (it may be a combination, or the image points are in a different order from the object points). Check the order of the points."


@guard
def identify(d):
    obj = parse_pts(d.get("obj"), "The object's corners", 2)
    img = parse_pts(d.get("img"), "The image's corners", 2)
    if len(obj) != len(img):
        raise UErr("The object and the image must have the same number of corners, in the same order (A, B, C ... and A', B', C' ...).")
    steps = ["<b>Describing a transformation</b> means saying <b>which type</b> it is and giving <b>all the details</b> (mirror line, or centre and angle, or vector, or centre and scale factor). "
             "We test the types one by one. Corners must be in matching order: A &rarr; A', B &rarr; B' ..."]
    res, err = identify_core(obj, img, steps)
    if err:
        raise UErr(err)
    image = draw([("Object", obj, BLUE, ""), ("Image", img, RED, "'")])
    return _ok(steps, {"image": image, "text": res})


# ------------------------------------------------------------ combined ----
OPS = [("rx", "Reflect in the x-axis"), ("ry", "Reflect in the y-axis"), ("ryx", "Reflect in y = x"), ("rynx", "Reflect in y = &minus;x"),
       ("r90", "Rotate 90&deg; anticlockwise about the origin"), ("r180", "Rotate 180&deg; about the origin"), ("r270", "Rotate 90&deg; clockwise about the origin"),
       ("tr", "Translate by a vector"), ("en", "Enlarge about the origin")]
O0 = (Fraction(0), Fraction(0))


def apply_op(op, par, pts):
    if op == "rx":
        return [reflect(p, "x") for p in pts], "reflection in the x-axis"
    if op == "ry":
        return [reflect(p, "y") for p in pts], "reflection in the y-axis"
    if op == "ryx":
        return [reflect(p, "yx") for p in pts], "reflection in y = x"
    if op == "rynx":
        return [reflect(p, "ynx") for p in pts], "reflection in y = &minus;x"
    if op in ("r90", "r180", "r270"):
        a = int(op[1:])
        return [rotate(p, O0, a) for p in pts], {90: "rotation 90&deg; anticlockwise about the origin", 180: "rotation 180&deg; about the origin", 270: "rotation 90&deg; clockwise about the origin"}[a]
    if op == "tr":
        m = re.fullmatch(r"\s*\(?\s*([^,()]+?)\s*,\s*([^,()]+?)\s*\)?\s*", (par or "").replace("−", "-"))
        if not m:
            raise UErr("For a translation write the vector as two numbers, like 3, -2.")
        v = (Fraction(num(m.group(1), "vector")), Fraction(num(m.group(2), "vector")))
        return [(p[0] + v[0], p[1] + v[1]) for p in pts], f"translation by ({ns(v[0])}, {ns(v[1])})"
    k = Fraction(num(par, "The scale factor"))
    if k == 0 or abs(k) > 100:
        raise UErr("Use a scale factor that is not 0 and between &minus;100 and 100.")
    return [enlarge(p, O0, k) for p in pts], f"enlargement about the origin, scale factor {ns(k)}"


@guard
def combined(d):
    obj = parse_pts(d.get("pts"), "The shape's corners", 1)
    s1, d1 = apply_op(d.get("t1", "rx"), d.get("p1"), obj)
    s2, d2 = apply_op(d.get("t2", "r90"), d.get("p2"), s1)
    steps = ["<b>Combined transformation:</b> do the first one, then do the second one on the <b>new</b> shape (the first image).",
             f"<b>Step 1:</b> {d1}.<br>" + ptable(obj, s1, "'", None),
             f"<b>Step 2:</b> {d2}, applied to A'B'C'...<br>" + ptable(s1, s2, "''", None, "'")]
    s = []
    res, err = identify_core(obj, s2, s) if len(obj) >= 2 else (None, "")
    if res:
        steps.append(f"<b>Is there one single transformation that does the same job?</b> Yes: {res}")
        steps.extend(s[-1:] if False else [])
    elif len(obj) >= 2:
        steps.append("This combination cannot be replaced by one simple transformation of these types.")
    steps.append("<b>Remember:</b> the ORDER matters. Reflecting then rotating usually gives a different result from rotating then reflecting.")
    image = draw([("Object", obj, BLUE, ""), ("After step 1", s1, ORANGE, "'"), ("After step 2", s2, RED, "''")], link=False)
    return _ok(steps, {"image": image, "text": f"<b>Final image: {', '.join(LET[i] + chr(39) * 2 + ' ' + P(q) for i, q in enumerate(s2))}</b>"})


# ---------------------------------------------------------------- spec ----
PTS = "(1, 1), (4, 1), (4, 3)"
SPEC = {
    "title": "Transformations",
    "intro": "Reflection, rotation, translation and enlargement, with every step shown and a graph that shows the <b>object (blue)</b> and the <b>image (red)</b>. "
             "Type the corners of your shape like <b>(1, 1), (4, 1), (4, 3)</b>. The first corner is called A, the next B, and so on.",
    "tabs": [
        {"id": "trf", "label": "Reflection", "title": "Reflect a shape in a mirror line", "endpoint": "reflection",
         "fields": [field("pts", "Corners of the shape", PTS, wide=True, half=False),
                    select("line", "Mirror line", [("x", "x-axis (y = 0)"), ("y", "y-axis (x = 0)"), ("yx", "y = x"), ("ynx", "y = &minus;x"), ("xa", "x = a number"), ("yb", "y = a number")], wide=True),
                    field("a", "The number", "5", show_if={"line": ["xa", "yb"]})], "button": "Reflect"},
        {"id": "trr", "label": "Rotation", "title": "Rotate a shape about a point", "endpoint": "rotation",
         "fields": [field("pts", "Corners of the shape", PTS, wide=True, half=False),
                    field("cx", "Centre x (empty = 0)", "0"), field("cy", "Centre y (empty = 0)", "0"),
                    select("deg", "Angle", [("90", "90&deg;"), ("180", "180&deg;"), ("270", "270&deg;")]),
                    select("dir", "Direction", [("acw", "anticlockwise"), ("cw", "clockwise")])], "button": "Rotate"},
        {"id": "trt", "label": "Translation", "title": "Translate (slide) a shape", "endpoint": "translation",
         "fields": [field("pts", "Corners of the shape", PTS, wide=True, half=False),
                    field("vx", "Vector, top number (right/left)", "3"), field("vy", "Vector, bottom number (up/down)", "-2")], "button": "Translate"},
        {"id": "tre", "label": "Enlargement", "title": "Enlarge a shape", "endpoint": "enlargement",
         "fields": [field("pts", "Corners of the shape", PTS, wide=True, half=False),
                    field("cx", "Centre x (empty = 0)", "0"), field("cy", "Centre y (empty = 0)", "0"),
                    field("k", "Scale factor k (can be 2, 1/2, -1 ...)", "2")], "button": "Enlarge"},
        {"id": "tri", "label": "Describe it", "title": "Describe the transformation from object and image", "endpoint": "identify",
         "hint": "Give the corners of the object and of the image <b>in matching order</b> (A, B, C &hellip; and A', B', C' &hellip;). The app tells you which transformation it is, with full details.",
         "fields": [field("obj", "Object corners", "(1, 1), (4, 1), (4, 3)", wide=True, half=False),
                    field("img", "Image corners", "(-1, 1), (-4, 1), (-4, 3)", wide=True, half=False)], "button": "Describe"},
        {"id": "trc", "label": "Combined", "title": "Do one transformation, then another", "endpoint": "combined",
         "fields": [field("pts", "Corners of the shape", PTS, wide=True, half=False),
                    select("t1", "First transformation", OPS, wide=True),
                    field("p1", "Vector (like 3, -2)", "3, -2", show_if={"t1": "tr"}), field("p1", "Scale factor", "2", show_if={"t1": "en"}),
                    select("t2", "Then", OPS, wide=True),
                    field("p2", "Vector (like 3, -2)", "3, -2", show_if={"t2": "tr"}), field("p2", "Scale factor", "2", show_if={"t2": "en"})], "button": "Do both"},
    ],
}

topics.register("transform", SPEC, {"reflection": reflection, "rotation": rotation, "translation": translation, "enlargement": enlargement, "identify": identify, "combined": combined})
