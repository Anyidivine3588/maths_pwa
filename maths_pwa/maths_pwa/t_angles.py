"""Angles: every rule explained with a diagram, plus solvers for angles in lines,
parallel lines, triangles, quadrilaterals, polygons and circles."""
import math
import re
from fractions import Fraction

import topics
from tcommon import UErr, fm, num, field, select, guard, exact_or_dec, _ok, _fail
import angle_core as C
import angle_draw as D
from angle_core import (Lin, parse_lin, parse_opt, lin_str, dstr, nm, HL, DEG, MINUS, TIMES, solve_angles,
                        answer_html, summ, eq, fix, lin, need_int)

LET = "abcdefghijklmnopqrstuvw"


def _label(res, n):
    return D.mk_label(res["vals"][n], res["kinds"][n], lin_str(res["exprs"][n], plain=True))


def _table(rows, head=None):
    h = "".join(f"<th>{c}</th>" for c in head) if head else ""
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table class='stat-table'>{('<tr>' + h + '</tr>') if h else ''}{body}</table>"


def _list(s, label, lo=2, hi=12):
    parts = re.split(r"[,;]", s or "")
    if len(parts) > hi or len([p for p in parts if p.strip()]) < 1:
        raise UErr(f"{label}: type between {lo} and {hi} angles, separated by commas.")
    out = []
    for i, p in enumerate(parts):
        p = p.strip()
        if p in ("", "?"):
            out.append(None)
        else:
            out.append(parse_lin(p, f"{label} number {i + 1}"))
    if len(out) < lo:
        raise UErr(f"{label}: type at least {lo} angles, separated by commas.")
    return out


# =========================================================== basic angle rules ==

BASIC = {
    "point": (360, "angles around a point",
              "Go all the way round a point and you make <b>one full turn</b>. A full turn is <b>360&deg;</b>.",
              "angles at a point add up to 360&deg;"),
    "line": (180, "angles on a straight line",
             "A straight line is a <b>half turn</b>. All the angles that sit on one side of a straight line add up to <b>180&deg;</b>.",
             "angles on a straight line add up to 180&deg;"),
    "right": (90, "angles in a right angle",
              "A right angle (like the corner of your exercise book) is <b>90&deg;</b>. Two angles that together make a right angle are called <b>complementary</b> angles.",
              "angles in a right angle add up to 90&deg;"),
}


@guard
def basic(d):
    kind = d.get("kind", "point")
    if kind in BASIC:
        total, what, expl, why = BASIC[kind]
        items = _list(d.get("angles"), "Angles", 2, 10)
        names = list(LET[:len(items)])
        nice = {n: f"angle {n}" for n in names}
        given = dict(zip(names, items))
        text = " + ".join(names) + f" = {total}&deg;"
        steps = [f"<b>The rule:</b> {expl}", f"So: {HL(text)}"]
        res = solve_angles(names, nice, given, [summ(names, total, why, text)], maxang=total, what=what[:-1] if what.endswith("s") else what)
        steps += res["steps"]
        pretty = [(res["vals"][n], _label(res, n), n) for n in names]
        steps.append(f"<b>Check:</b> " + " + ".join(nm(res["vals"][n]) for n in names) + f" = {nm(sum(res['vals'].values()))}{DEG} &#10003;")
        head = {"point": "Angles at a point (360°)", "line": "Angles on a straight line (180°)", "right": "Angles in a right angle (90°)"}[kind]
        img = D.fig_fan(pretty, total, head)
        return _ok(steps, {"image": img, "text": answer_html(res, names, nice)})
    if kind == "vert":
        a1 = parse_lin(d.get("a1"), "The first angle")
        a2 = parse_opt(d.get("a2"), "The vertically opposite angle")
        names = ["P", "R", "Q", "S"]
        nice = {n: f"angle {n}" for n in names}
        given = {"P": a1, "Q": a2, "R": None, "S": None}
        steps = ["<b>The rule:</b> when two straight lines cross, the angles <b>opposite each other</b> (the ones that touch only at the crossing point) are called <b>vertically opposite angles</b>, and they are <b>equal</b>.",
                 "Also, two angles side by side on a straight line add up to 180&deg;. In the picture, P and Q are opposite each other; R and S are opposite each other."]
        rels = [eq(["P", "Q"], "vertically opposite angles are equal"), eq(["R", "S"], "vertically opposite angles are equal"),
                summ(["P", "R"], 180, "angles on a straight line add up to 180&deg;", "P + R = 180&deg;"),
                summ(["R", "Q"], 180, "angles on a straight line add up to 180&deg;", "R + Q = 180&deg;")]
        res = solve_angles(names, nice, given, rels, maxang=180, what="pair of crossing lines")
        steps += res["steps"]
        labs = [_label(res, n) for n in ("P", "R", "Q", "S")]
        img = D.fig_cross(float(res["vals"]["P"]), labs)
        return _ok(steps, {"image": img, "text": answer_html(res, names, nice)})
    if kind == "classify":
        v = num(d.get("v"), "The angle")
        if not (0 < v <= 360):
            raise UErr("Type an angle between 0 and 360 degrees.")
        steps = []
        if v < 90:
            nme, why = "an <b>acute</b> angle", "it is smaller than 90&deg; (smaller than a corner of your book)"
        elif v == 90:
            nme, why = "a <b>right</b> angle", "it is exactly 90&deg; (the corner of your book)"
        elif v < 180:
            nme, why = "an <b>obtuse</b> angle", "it is bigger than 90&deg; but smaller than 180&deg;"
        elif v == 180:
            nme, why = "a <b>straight</b> angle", "it is exactly 180&deg; (a straight line)"
        elif v < 360:
            nme, why = "a <b>reflex</b> angle", "it is bigger than 180&deg; but smaller than 360&deg;"
        else:
            nme, why = "a <b>full turn</b>", "it is exactly 360&deg; (all the way round)"
        steps.append(f"{nm(v)}{DEG} is {nme}: {why}.")
        if v < 90:
            steps.append(f"Its <b>complement</b> (what you add to make 90&deg;): 90&deg; &minus; {nm(v)}&deg; = {HL(nm(90 - v) + DEG)}")
        if v < 180:
            steps.append(f"Its <b>supplement</b> (what you add to make 180&deg;): 180&deg; &minus; {nm(v)}&deg; = {HL(nm(180 - v) + DEG)}")
        if v < 360:
            steps.append(f"The rest of the full turn: 360&deg; &minus; {nm(v)}&deg; = {HL(nm(360 - v) + DEG)}")
        fig, ax = D.new_fig(4.6, 4.0)
        O = (0, 0)
        D.seg(ax, O, D.pol(O, 0, 1.7), lw=2.6)
        if v < 360:
            D.seg(ax, O, D.pol(O, float(v), 1.7), lw=2.6)
        D.dot(ax, O)
        from matplotlib.patches import Circle
        if v == 360:
            ax.add_patch(Circle(O, 0.6, fc=D.FILL_GIVEN, ec=D.BLUE, lw=2, alpha=0.55))
            D.put_text(ax, (0, 0), (f"{nm(v)}°", None, "given"))
        else:
            D.wedge(ax, O, 0, float(v), 0.6, lab=(f"{nm(v, 2)}°", None, "given"), label_r=0.95)
        ax.set_xlim(-2, 2)
        ax.set_ylim(-2, 2)
        D.title(ax, f"{nm(v, 2)}° is " + re.sub(r"<[^>]+>", "", nme))
        img = D.to_b64(fig)
        return _ok(steps, {"image": img, "text": f"<b>{nm(v)}&deg; is {nme}</b>"})
    raise UErr("Choose what you want to do.")


# ============================================================== parallel lines ==

@guard
def parallel(d):
    rel = d.get("rel", "corr")
    if rel == "all":
        a = num(d.get("a1"), "The angle")
        if not (0 < a < 180):
            raise UErr("The angle must be between 0 and 180 degrees.")
        b = 180 - a
        rows = [("a", a, "the angle you were given"),
                ("b", b, "on a straight line with a (a + b = 180&deg;)"),
                ("c", a, "vertically opposite a"),
                ("d", b, "vertically opposite b (or on a straight line with a)"),
                ("e", a, "corresponding to a (F-shape)"),
                ("f", b, "corresponding to b (F-shape)"),
                ("g", a, "corresponding to c &nbsp;(also alternate to e... see below)"),
                ("h", b, "corresponding to d")]
        rows[6] = ("g", a, "corresponding to c (F-shape)")
        steps = ["<b>Idea:</b> two parallel lines cut by a third line (called a <b>transversal</b>) make <b>eight angles</b>, but only <b>two different sizes</b>: the angle you know and its partner that adds up with it to 180&deg;.",
                 f"Given angle a = {nm(a)}&deg;, the other size is 180&deg; &minus; {nm(a)}&deg; = {HL(nm(b) + DEG)}.",
                 _table([(r[0], nm(r[1], 3) + DEG, r[2]) for r in rows], ["Angle", "Size", "Why"]),
                 "<b>Equal pairs:</b><br>&bull; Corresponding (F-shape): a&amp;e, b&amp;f, c&amp;g, d&amp;h<br>&bull; Alternate (Z-shape): c&amp;e and d&amp;f (inside), a&amp;g and b&amp;h (outside)<br>&bull; Vertically opposite: a&amp;c, b&amp;d, e&amp;g, f&amp;h",
                 "<b>Pairs that add up to 180&deg;:</b><br>&bull; Co-interior (C-shape): c&amp;f and d&amp;e<br>&bull; Any two angles side by side on a straight line, like a&amp;b"]
        labs = {}
        for L_, (nme, val, w) in zip("abcdefgh", rows):
            labs[L_] = D.mk_label(val, "given" if L_ == "a" else "found")
        img = D.fig_parallel(float(a), "all", labs)
        return _ok(steps, {"image": img, "text": f"<b>Two sizes only: {nm(a, 3)}&deg; and {nm(b, 3)}&deg;</b>"})
    a1 = parse_lin(d.get("a1"), "The first angle")
    a2 = parse_opt(d.get("a2"), "The second angle")
    nice = {"X": "angle X", "Y": "angle Y"}
    names = ["X", "Y"]
    given = {"X": a1, "Y": a2}
    intro = {
        "corr": ("<b>Corresponding angles</b> sit in the <b>same position</b> at the two crossings (for example both are 'above the line and to the right of the slanted line'). Look for the letter <b>F</b>. When the lines are parallel, corresponding angles are <b>equal</b>.", "corresponding angles (F-shape) are equal"),
        "alt": ("<b>Alternate angles</b> are <b>between the parallel lines</b>, on <b>opposite sides</b> of the slanted line. Look for the letter <b>Z</b>. When the lines are parallel, alternate angles are <b>equal</b>.", "alternate angles (Z-shape) are equal"),
        "coint": ("<b>Co-interior angles</b> (also called allied angles) are <b>between the parallel lines</b> on the <b>same side</b> of the slanted line. Look for the letter <b>C</b> or <b>U</b>. When the lines are parallel they <b>add up to 180&deg;</b>.", "co-interior angles (C-shape) add up to 180&deg;"),
        "line": ("Two angles that sit side by side on a <b>straight line</b> add up to <b>180&deg;</b>.", "angles on a straight line add up to 180&deg;"),
        "vert": ("When two lines cross, the angles <b>opposite</b> each other are <b>vertically opposite angles</b>, and they are <b>equal</b>.", "vertically opposite angles are equal"),
    }
    if rel not in intro:
        raise UErr("Choose which pair of angles you want.")
    text, why = intro[rel]
    steps = [f"<b>The rule:</b> {text}"]
    if rel in ("corr", "alt", "vert"):
        rels = [eq(["X", "Y"], why)]
        steps.append(f"So angle X = angle Y.")
    else:
        rels = [summ(["X", "Y"], 180, why, "X + Y = 180&deg;")]
        steps.append(f"So {HL('X + Y = 180&deg;')}")
    res = solve_angles(names, nice, given, rels, maxang=180, what="pair of angles")
    steps += res["steps"]
    X, Y = res["vals"]["X"], res["vals"]["Y"]
    if rel == "vert":
        other = 180 - X
        labs = [_label(res, "X"), D.mk_label(other, "found"), _label(res, "Y"), D.mk_label(other, "found")]
        img = D.fig_cross(float(X), labs, "Vertically opposite angles")
    else:
        img = D.fig_parallel(float(X), rel, {"X": _label(res, "X"), "Y": _label(res, "Y")})
    steps.append("Look at the diagram: the orange shape traces the " + {"corr": "F", "alt": "Z", "coint": "C", "line": "straight line", "vert": "crossing"}[rel] + ", and the coloured corners are the two angles.")
    return _ok(steps, {"image": img, "text": answer_html(res, names, nice)})


# ================================================================== triangles ==

def _tri_poly(vals, order):
    return D.poly_pts([float(vals[n]) for n in order])


@guard
def triangle(d):
    kind = d.get("kind", "any")
    base_rule = "The three angles inside <b>any</b> triangle always add up to <b>180&deg;</b>."
    sumrel = summ(["A", "B", "C"], 180, "angles in a triangle add up to 180&deg;", "A + B + C = 180&deg;")
    names = ["A", "B", "C"]
    nice = {n: f"angle {n}" for n in names}
    fixed = set()
    ticks = None
    if kind == "any":
        given = {n: parse_opt(d.get(n.lower()), f"Angle {n}") for n in names}
        steps = [f"<b>The rule:</b> {base_rule}", f"So: {HL('A + B + C = 180&deg;')}"]
        rels = [sumrel]
        head = "Triangle ABC: angles add up to 180°"
    elif kind == "iso":
        given = {n: parse_opt(d.get("i" + n.lower()), f"Angle {n}") for n in names}
        steps = ["<b>The rule:</b> an <b>isosceles</b> triangle has <b>two equal sides</b>. The angles at the bottom of those two sides (the <b>base angles</b>) are <b>equal</b>. "
                 "In triangle ABC, AB = AC, so angle B = angle C, and A is the angle at the top (the apex).", base_rule]
        rels = [eq(["B", "C"], "base angles of an isosceles triangle are equal"), sumrel]
        ticks = {1: 1, 2: 1}
        head = "Isosceles triangle: AB = AC, so B = C"
    elif kind == "equi":
        a = parse_opt(d.get("e"), "The angle")
        given = {"A": a, "B": None, "C": None}
        steps = ["<b>The rule:</b> an <b>equilateral</b> triangle has <b>three equal sides</b> and so <b>three equal angles</b>. Since they add up to 180&deg;, each one is 180&deg; &divide; 3 = <b>60&deg;</b>."]
        rels = [fix(["A", "B", "C"], 60, "equilateral triangle: every angle is 60&deg;")]
        ticks = {0: 1, 1: 1, 2: 1}
        head = "Equilateral triangle: every angle is 60°"
        if a is None:
            given = {"A": None, "B": None, "C": None}
    elif kind == "right":
        given = {"A": parse_opt(d.get("ra"), "Angle A"), "B": parse_opt(d.get("rb"), "Angle B"), "C": None}
        steps = ["<b>The rule:</b> a <b>right-angled</b> triangle has one angle of <b>90&deg;</b> (angle C here). The other two angles share what is left of the 180&deg;, so <b>the two acute angles add up to 90&deg;</b>.", base_rule]
        rels = [fix(["C"], 90, "C is the right angle"), sumrel]
        fixed = {"C"}
        head = "Right-angled triangle: C = 90°"
    elif kind == "ext":
        names = ["E", "A", "B"]
        nice = {"E": "the exterior angle", "A": "angle A", "B": "angle B"}
        given = {"E": parse_opt(d.get("ee"), "The exterior angle"), "A": parse_opt(d.get("ea"), "Angle A"), "B": parse_opt(d.get("eb"), "Angle B")}
        steps = ["<b>What is an exterior angle?</b> Extend one side of the triangle outwards. The angle between that extension and the next side is the <b>exterior angle</b>.",
                 "<b>The rule:</b> the exterior angle equals the <b>sum of the two interior opposite angles</b> (the two inside angles that are NOT next to it). "
                 "Why? The inside angle at C and the exterior angle are on a straight line, so they add to 180&deg;. The three inside angles also add to 180&deg;. So the exterior angle must equal A + B.",
                 f"So: {HL('exterior angle = A + B')}"]

        def fmt(u, val, g):
            if u == "E":
                return f"Exterior angle = angle A + angle B = {dstr(val['A'])} + {dstr(val['B'])}"
            if u == "A":
                return f"Angle A = exterior angle &minus; angle B = {dstr(val['E'])} &minus; {dstr(val['B'])}"
            return f"Angle B = exterior angle &minus; angle A = {dstr(val['E'])} &minus; {dstr(val['A'])}"
        rels = [lin({"E": 1, "A": -1, "B": -1}, 0, "exterior angle of a triangle", "exterior angle = A + B", fmt)]
        head = "Exterior angle of a triangle"
    else:
        raise UErr("Choose a type of triangle.")
    res = solve_angles(names, nice, given, rels, maxang=180, what="triangle")
    for n in fixed:
        res["kinds"][n] = "given"
    steps += res["steps"]
    v = res["vals"]
    if kind == "ext":
        Cin = 180 - v["E"]
        steps.append(f"<b>Check:</b> the inside angle at C is 180&deg; &minus; {nm(v['E'])}&deg; = {nm(Cin)}&deg;, and {nm(v['A'])}&deg; + {nm(v['B'])}&deg; + {nm(Cin)}&deg; = 180&deg; &#10003;")
        pts = D.poly_pts([float(v["B"]), float(Cin), float(v["A"])])
        order = ["B", "C", "A"]
        fig, ax = D.new_fig(6.0, 4.4)
        labels = {"A": _label(res, "A"), "B": _label(res, "B"), "C": None}
        D.draw_polygon(ax, pts, order, labels)
        Bp, Cp, Ap = pts
        size = math.hypot(*(Ap[i] - Bp[i] for i in range(2))) + 0.1
        a0 = D.ang(Bp, Cp)
        ext_pt = D.pol(Cp, a0, 0.9 * math.dist(Bp, Cp))
        D.seg(ax, Cp, ext_pt, color=D.GREY, lw=2.2, ls="--")
        a2 = D.ang(Cp, Ap)
        while a2 <= a0:
            a2 += 360
        rr = 0.17 * max(math.dist(Bp, Cp), math.dist(Ap, Cp))
        D.wedge(ax, Cp, a0, a2, rr, lab=_label(res, "E"), fill="#fdba74", edge=D.ORANGE, label_r=rr * 1.9, right_ok=False)
        xs = [p[0] for p in pts] + [ext_pt[0]]
        ys = [p[1] for p in pts]
        ax.set_xlim(min(xs) - 0.3, max(xs) + 0.3)
        ax.set_ylim(min(ys) - 0.3, max(ys) + 0.3)
        D.title(ax, head)
        D.legend(fig, "Blue = given   |   Red = found   |   Orange wedge = the exterior angle")
        img = D.to_b64(fig)
    else:
        steps.append("<b>Check:</b> " + " + ".join(nm(v[n]) for n in ("A", "B", "C")) + f" = {nm(sum(v.values()))}{DEG} &#10003;")
        order = ["B", "C", "A"]
        pts = _tri_poly(v, order)
        labels = {n: _label(res, n) for n in order}
        img = D.fig_polygon(pts, order, labels, head, ticks=ticks)
    return _ok(steps, {"image": img, "text": answer_html(res, names, nice)})


# ============================================================== quadrilaterals ==

QUAD_FACTS = {
    "square": "<b>Square:</b> 4 equal sides, <b>4 right angles (90&deg;)</b>. The diagonals are equal, cross at 90&deg;, and cut each corner into two <b>45&deg;</b> angles.",
    "rectangle": "<b>Rectangle:</b> opposite sides equal, <b>4 right angles (90&deg;)</b>. The two diagonals are equal and cut each other in half, so each half-diagonal makes an isosceles triangle.",
    "parallelogram": "<b>Parallelogram:</b> opposite sides are parallel and equal. <b>Opposite angles are equal</b> (A = C, B = D) and <b>neighbouring angles add up to 180&deg;</b> (A + B = 180&deg;).",
    "rhombus": "<b>Rhombus:</b> a parallelogram with 4 equal sides. <b>Opposite angles are equal</b>, neighbouring angles add to 180&deg;. The diagonals cross at <b>90&deg;</b> and cut each corner exactly in half.",
    "trap": "<b>Trapezium:</b> one pair of parallel sides (here AB &#8741; DC, the green arrows). Angles between the two parallel sides along the same leg are co-interior, so <b>A + D = 180&deg;</b> and <b>B + C = 180&deg;</b>.",
    "itrap": "<b>Isosceles trapezium:</b> one pair of parallel sides and equal legs. The two angles on the same parallel side are equal (<b>A = B</b> and <b>C = D</b>), and A + D = 180&deg;, B + C = 180&deg;.",
    "kite": "<b>Kite:</b> two pairs of equal neighbouring sides. The angles where the two different sides meet are equal (<b>B = D</b>). The diagonal AC is a line of symmetry. All four angles add up to 360&deg;.",
    "cyclic": "<b>Cyclic quadrilateral:</b> all four corners touch a circle. <b>Opposite angles add up to 180&deg;</b> (A + C = 180&deg; and B + D = 180&deg;).",
    "any": "<b>Any four-sided shape:</b> draw one diagonal and it splits into 2 triangles, so the four angles add up to 2 &times; 180&deg; = <b>360&deg;</b>.",
}


def _quad_rels(shape):
    S = "angles in a quadrilateral add up to 360&deg;"
    if shape in ("square", "rectangle"):
        return [fix(list("ABCD"), 90, f"every angle of a {shape} is 90&deg;")]
    if shape in ("parallelogram", "rhombus"):
        w = f"opposite angles of a {shape} are equal"
        s = "neighbouring angles of a parallelogram add up to 180&deg;"
        return [eq(["A", "C"], w), eq(["B", "D"], w), summ(["A", "B"], 180, s, "A + B = 180&deg;"), summ(["B", "C"], 180, s, "B + C = 180&deg;"),
                summ(["C", "D"], 180, s, "C + D = 180&deg;"), summ(["D", "A"], 180, s, "D + A = 180&deg;")]
    if shape == "trap":
        s = "co-interior angles between parallel sides add up to 180&deg;"
        return [summ(["A", "D"], 180, s, "A + D = 180&deg;"), summ(["B", "C"], 180, s, "B + C = 180&deg;")]
    if shape == "itrap":
        s = "co-interior angles between parallel sides add up to 180&deg;"
        return [eq(["A", "B"], "base angles of an isosceles trapezium are equal"), eq(["C", "D"], "base angles of an isosceles trapezium are equal"),
                summ(["A", "D"], 180, s, "A + D = 180&deg;"), summ(["B", "C"], 180, s, "B + C = 180&deg;")]
    if shape == "kite":
        return [eq(["B", "D"], "a kite has one pair of equal angles"), summ(list("ABCD"), 360, S, "A + B + C + D = 360&deg;")]
    if shape == "cyclic":
        w = "opposite angles of a cyclic quadrilateral add up to 180&deg;"
        return [summ(["A", "C"], 180, w, "A + C = 180&deg;"), summ(["B", "D"], 180, w, "B + D = 180&deg;")]
    return [summ(list("ABCD"), 360, S, "A + B + C + D = 360&deg;")]


def _kite_pts(A, B):
    """A at the top, B = D the side angles (degrees). returns (A, D, C, B) points or None"""
    a0 = -90 + A / 2
    P = (0.0, 0.0)
    Bp = D.pol(P, a0, 1.0)
    phi = a0 + 180 + B
    ux, uy = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    if ux >= -1e-6 or uy >= -1e-6:
        return None
    t = -Bp[0] / ux
    Cp = (Bp[0] + t * ux, Bp[1] + t * uy)
    return [P, (-Bp[0], Bp[1]), Cp, Bp]


def _trap_pts(A, B):
    """A bottom-left, B bottom-right, C top-right, D top-left; AB parallel to DC"""
    cA = 1 / math.tan(math.radians(A))
    cB = 1 / math.tan(math.radians(B))
    Lb = max(1.2, cA + cB + 1.6)
    return [(0.0, 0.0), (Lb, 0.0), (Lb - cB, 1.0), (cA, 1.0)]


def _cyclic_pts(A, B, C_, D_):
    """points on the unit circle (ccw) giving interior angles A,B,C,D"""
    best = None
    for i in range(0, 3600):
        t = 360 * i / 3600
        a_ab, a_bc, a_cd, a_da = t, 2 * D_ - t, 2 * A - 2 * D_ + t, 2 * B - 2 * A + 2 * D_ - t
        m = min(a_ab, a_bc, a_cd, a_da)
        if best is None or m > best[0]:
            best = (m, a_ab, a_bc, a_cd, a_da)
    m, a_ab, a_bc, a_cd, a_da = best
    if m <= 1:
        return None
    ang0 = 90 + a_da / 2
    pts = []
    cur = ang0
    for arc in (a_ab, a_bc, a_cd, a_da):
        pts.append((math.cos(math.radians(cur)), math.sin(math.radians(cur))))
        cur += arc
    return pts


@guard
def quad(d):
    shape = d.get("shape", "square")
    if shape not in QUAD_FACTS:
        raise UErr("Choose a shape.")
    names = list("ABCD")
    nice = {n: f"angle {n}" for n in names}
    steps = [QUAD_FACTS[shape]]
    if shape in ("square", "rectangle"):
        x1 = parse_opt(d.get("sa"), "The angle")
        given = {"A": x1, "B": None, "C": None, "D": None}
    elif shape == "kite":
        given = {n: parse_opt(d.get("k" + n.lower()), f"Angle {n}") for n in names}
    elif shape == "any":
        given = {n: parse_opt(d.get("q" + n.lower()), f"Angle {n}") for n in names}
    else:
        given = {n: parse_opt(d.get(n.lower()), f"Angle {n}") for n in names}
    rels = _quad_rels(shape)
    if shape == "rectangle" and True:
        pass
    res = solve_angles(names, nice, given, rels, maxang=(360 if shape == "any" else 180), what="quadrilateral")
    if shape in ("square", "rectangle"):
        for n in names:
            res["kinds"][n] = "given"
    steps += res["steps"]
    v = res["vals"]
    steps.append("<b>Check:</b> " + " + ".join(nm(v[n]) for n in names) + f" = {nm(sum(v.values()))}{DEG} &#10003;")
    labels = {n: _label(res, n) for n in names}
    fa = {n: float(v[n]) for n in names}
    heading = {"square": "Square", "rectangle": "Rectangle", "parallelogram": "Parallelogram", "rhombus": "Rhombus",
               "trap": "Trapezium (AB ∥ DC)", "itrap": "Isosceles trapezium (AB ∥ DC)", "kite": "Kite", "cyclic": "Cyclic quadrilateral", "any": "Four-sided shape"}[shape]
    ticks = parallel = None
    order = names
    if shape == "square":
        pts = [(0, 0), (1, 0), (1, 1), (0, 1)]
        ticks = {0: 1, 1: 1, 2: 1, 3: 1}
    elif shape == "rectangle":
        th = num(d.get("theta"), "The diagonal angle", blank=True)
        th = float(th) if th is not None else 35.0
        if not (0 < th < 90):
            raise UErr("The angle the diagonal makes with the side must be between 0 and 90 degrees.")
        w = 1.0
        h = math.tan(math.radians(th)) * w
        if h > 1.4:
            w, h = 1.4 / h * w if False else w * (1.4 / h), 1.4
        pts = [(0, 0), (w, 0), (w, h), (0, h)]
        steps.append(f"<b>Diagonals:</b> in rectangle ABCD, if the diagonal AC makes {nm(th, 3)}&deg; with side AB:")
        steps.append(f"&bull; The diagonal makes {nm(90 - th, 3)}&deg; with side AD (because angle A = 90&deg; and {nm(th, 3)}&deg; + {nm(90 - th, 3)}&deg; = 90&deg;).<br>"
                     f"&bull; The diagonals cross at O and OA = OB (the diagonals of a rectangle are equal and cut each other in half), so triangle OAB is isosceles: angle OBA = {nm(th, 3)}&deg;.<br>"
                     f"&bull; Angle AOB = 180&deg; &minus; 2 &times; {nm(th, 3)}&deg; = {HL(nm(180 - 2 * th, 3) + DEG)}.<br>"
                     f"&bull; Angle AOD is on a straight line with AOB: 180&deg; &minus; {nm(180 - 2 * th, 3)}&deg; = {HL(nm(2 * th, 3) + DEG)}.")
        fig, ax = D.new_fig(*D.auto_size(pts, 6.2, 1.0))
        D.draw_polygon(ax, pts, names, {n: None for n in names}, ticks=None)
        Ap, Bp, Cp, Dp = pts
        O = ((Ap[0] + Cp[0]) / 2, (Ap[1] + Cp[1]) / 2)
        D.seg(ax, Ap, Cp, color=D.GREY, lw=1.8, ls="--")
        D.seg(ax, Bp, Dp, color=D.GREY, lw=1.8, ls="--")
        D.dot(ax, O)
        ax.text(O[0], O[1] + 0.06 * max(w, h) + 0.02, "O", fontsize=11, fontweight="bold", ha="center", color=D.INK, path_effects=D._halo(), zorder=9)
        size = math.hypot(w, h)
        D.wedge(ax, Ap, 0, th, 0.2 * size, lab=(f"{nm(th, 3)}°", None, "given"), label_r=0.34 * size if th > 25 else 0.42 * size)
        D.wedge(ax, Ap, th, 90, 0.14 * size, lab=(f"{nm(90 - th, 3)}°", None, "found"), label_r=0.26 * size, right_ok=False)
        D.wedge(ax, O, 180 + th, 360 - th, 0.12 * size, lab=(f"{nm(180 - 2 * th, 3)}°", None, "found"), label_r=0.25 * size, right_ok=False)
        D.seg(ax, (0, 0), (0, 0))
        ax.set_xlim(-0.35, w + 0.35)
        ax.set_ylim(-0.35, h + 0.35)
        D.title(ax, "Rectangle with its diagonals")
        D.legend(fig, "Blue = given   |   Red = found   |   dashed lines are the diagonals")
        img = D.to_b64(fig)
        return _ok(steps, {"image": img, "text": answer_html(res, names, nice) + f"<br><b>Angle AOB = {nm(180 - 2 * th, 3)}&deg;, angle AOD = {nm(2 * th, 3)}&deg;</b>"})
    elif shape in ("parallelogram", "rhombus", "any"):
        hint = [1.7, 1.0, 1.7, 1.0] if shape == "parallelogram" else None
        pts = D.poly_pts([fa[n] for n in names], hint=hint)
        if shape == "parallelogram":
            ticks = {0: 1, 2: 1, 1: 2, 3: 2}
            parallel = {0: 1, 2: 1, 1: 2, 3: 2}
        elif shape == "rhombus":
            ticks = {0: 1, 1: 1, 2: 1, 3: 1}
            parallel = {0: 1, 2: 1, 1: 2, 3: 2}
            half_a, half_b = v["A"] / 2, v["B"] / 2
            steps.append(f"<b>Diagonals of a rhombus:</b> they cross at {HL('90&deg;')} and cut each corner in half. So the diagonal AC splits angle A into two angles of {nm(v['A'], 3)}&deg; &divide; 2 = {HL(nm(half_a, 3) + DEG)}, "
                         f"and the diagonal BD splits angle B into two angles of {nm(v['B'], 3)}&deg; &divide; 2 = {HL(nm(half_b, 3) + DEG)}. "
                         f"(Check inside one small triangle: {nm(half_a, 3)}&deg; + {nm(half_b, 3)}&deg; + 90&deg; = 180&deg; &#10003;)")
    elif shape in ("trap", "itrap"):
        pts = _trap_pts(fa["A"], fa["B"])
        parallel = {0: 1, 2: 1}
        if shape == "itrap":
            ticks = {1: 1, 3: 1}
    elif shape == "kite":
        kp = _kite_pts(fa["A"], fa["B"])
        if kp is None:
            pts = D.poly_pts([fa[n] for n in names])
        else:
            order = ["A", "D", "C", "B"]
            pts = kp
            ticks = {0: 1, 3: 1, 1: 2, 2: 2}
    elif shape == "cyclic":
        pts = _cyclic_pts(fa["A"], fa["B"], fa["C"], fa["D"])
        if pts is None:
            raise UErr("Those angles cannot be drawn as a cyclic quadrilateral. Check them.")
    if shape == "cyclic":
        fig, ax = D.new_fig(5.8, 5.2)
        from matplotlib.patches import Circle
        ax.add_patch(Circle((0, 0), 1.0, fc="white", ec=D.PURPLE, lw=2.2, zorder=0))
        D.draw_polygon(ax, pts, names, labels)
        ax.set_xlim(-1.45, 1.45)
        ax.set_ylim(-1.45, 1.45)
        D.title(ax, heading)
        D.legend(fig)
        img = D.to_b64(fig)
    else:
        img = D.fig_polygon(pts, order, labels, heading, ticks=ticks, parallel=parallel)
    if shape == "square":
        img = _square_fig(labels)
        steps.append(f"<b>Diagonals of a square:</b> each diagonal cuts a 90&deg; corner into two equal parts: 90&deg; &divide; 2 = {HL('45&deg;')}. The two diagonals cross at {HL('90&deg;')}.")
    return _ok(steps, {"image": img, "text": answer_html(res, names, nice)})


def _square_fig(labels):
    fig, ax = D.new_fig(5.4, 5.0)
    pts = [(0, 0), (1, 0), (1, 1), (0, 1)]
    D.draw_polygon(ax, pts, list("ABCD"), labels, ticks={0: 1, 1: 1, 2: 1, 3: 1}, rfrac=0.14, fs=9.5)
    D.seg(ax, pts[0], pts[2], color=D.GREY, lw=1.8, ls="--")
    D.seg(ax, pts[1], pts[3], color=D.GREY, lw=1.8, ls="--")
    O = (0.5, 0.5)
    D.dot(ax, O)
    from matplotlib.patches import Polygon
    s = 0.06
    ax.add_patch(Polygon([O, (0.5 + s * 0.7071, 0.5 + s * 0.7071), (0.5, 0.5 + s * 1.4142), (0.5 - s * 0.7071, 0.5 + s * 0.7071)], closed=True, fc="none", ec=D.RED, lw=1.8))
    ax.text(0.5, 0.74, "90°", fontsize=10, fontweight="bold", color=D.RED, ha="center", path_effects=D._halo())
    ax.text(0.30, 0.10, "45°", fontsize=10, fontweight="bold", color=D.RED, ha="center", path_effects=D._halo())
    ax.set_xlim(-0.3, 1.3)
    ax.set_ylim(-0.3, 1.3)
    D.title(ax, "Square with its diagonals")
    D.legend(fig)
    return D.to_b64(fig)


# =================================================================== polygons ==

POLY_NAMES = {3: "triangle", 4: "quadrilateral", 5: "pentagon", 6: "hexagon", 7: "heptagon", 8: "octagon", 9: "nonagon",
              10: "decagon", 11: "hendecagon", 12: "dodecagon"}


def _poly_formulas(n, pre=None):
    name = POLY_NAMES.get(n, f"{n}-sided polygon")
    S = (n - 2) * 180
    inter = Fraction(S, n)
    ext = Fraction(360, n)
    diag = n * (n - 3) // 2
    steps = list(pre or [])
    steps.append(f"<b>A polygon with n = {n} sides</b> is called a {name}.")
    steps.append(f"<b>Sum of interior angles.</b> Pick one corner and draw straight lines from it to every other corner (not the neighbours). "
                 f"This cuts the polygon into <b>n &minus; 2 = {n - 2} triangles</b>. Every triangle has angles adding up to 180&deg;, so:<br>"
                 f"{HL('Sum of interior angles = (n &minus; 2) &times; 180&deg;')}<br>= ({n} &minus; 2) &times; 180&deg; = {n - 2} &times; 180&deg; = {HL(nm(S) + DEG)}")
    steps.append(f"<b>Each interior angle of a REGULAR polygon</b> (all sides and angles equal): share the sum equally.<br>"
                 f"{HL('Each interior angle = (n &minus; 2) &times; 180&deg; &divide; n')}<br>= {nm(S)}&deg; &divide; {n} = {HL((nm(inter) if inter.denominator == 1 else fm(inter, 2)) + DEG)}")
    steps.append(f"<b>Exterior angles.</b> Walk round the polygon: at each corner you turn a little. After going all the way round you have turned exactly one full turn, so "
                 f"{HL('the exterior angles of ANY polygon add up to 360&deg;')}<br>"
                 f"For a regular polygon: {HL('each exterior angle = 360&deg; &divide; n')} = 360&deg; &divide; {n} = {HL((nm(ext) if ext.denominator == 1 else fm(ext, 2)) + DEG)}")
    steps.append(f"<b>Link between them:</b> interior angle + exterior angle = 180&deg; (they sit on a straight line). Check: {fm(inter, 2)}&deg; + {fm(ext, 2)}&deg; = {fm(inter + ext, 2)}&deg; &#10003;")
    steps.append(f"<b>Number of diagonals</b> = n(n &minus; 3) &divide; 2 = {n} &times; {n - 3} &divide; 2 = {diag}")
    rows = [("Sum of interior angles", "(n &minus; 2) &times; 180&deg;", nm(S) + DEG),
            ("Each interior angle (regular)", "(n &minus; 2) &times; 180&deg; &divide; n", fm(inter, 2) + DEG),
            ("Sum of exterior angles", "always 360&deg;", "360&deg;"),
            ("Each exterior angle (regular)", "360&deg; &divide; n", fm(ext, 2) + DEG),
            ("Number of sides when ext. angle is known", "n = 360&deg; &divide; exterior angle", str(n)),
            ("Number of triangles inside", "n &minus; 2", str(n - 2)),
            ("Number of diagonals", "n(n &minus; 3) &divide; 2", str(diag))]
    steps.append(_table(rows, ["What", "Formula", f"For n = {n}"]))
    ans = f"<b>{name.capitalize()}: sum of interior angles = {nm(S)}&deg;, each interior angle = {fm(inter, 2)}&deg;, each exterior angle = {fm(ext, 2)}&deg;</b>"
    if n <= 24:
        return _ok(steps, {"image": D.fig_regular(n, inter, ext), "text": ans})
    return _ok(steps, ans)


@guard
def polygon(d):
    kind = d.get("kind", "formulas")
    if kind == "formulas":
        n = need_int(d.get("n"), "The number of sides", 3, 360)
        return _poly_formulas(n)
    if kind == "reg":
        find = d.get("find", "int")
        v = num(d.get("v"), "The value")
        if find == "int":
            if not (0 < v < 180):
                raise UErr("An interior angle of a polygon is between 0 and 180 degrees.")
            e = 180 - v
            n = Fraction(360) / e
            pre = [f"<b>Step 1:</b> interior + exterior = 180&deg;, so the exterior angle = 180&deg; &minus; {nm(v)}&deg; = {HL(nm(e) + DEG)}.",
                   f"<b>Step 2:</b> each exterior angle = 360&deg; &divide; n, so n = 360&deg; &divide; {nm(e)}&deg; = {HL(nm(n, 3))}"]
        elif find == "ext":
            if not (0 < v < 180):
                raise UErr("An exterior angle of a polygon is between 0 and 180 degrees.")
            n = Fraction(360) / v
            pre = [f"<b>Step 1:</b> each exterior angle = 360&deg; &divide; n, so n = 360&deg; &divide; {nm(v)}&deg; = {HL(nm(n, 3))}"]
        else:
            if v <= 0:
                raise UErr("The sum must be bigger than 0.")
            n = Fraction(v) / 180 + 2
            pre = [f"<b>Step 1:</b> sum = (n &minus; 2) &times; 180&deg;. Divide by 180&deg;: n &minus; 2 = {nm(v)} &divide; 180 = {nm(Fraction(v) / 180, 3)}",
                   f"<b>Step 2:</b> n = {nm(Fraction(v) / 180, 3)} + 2 = {HL(nm(n, 3))}"]
        if n.denominator != 1 or not (3 <= n <= 360):
            return _fail(f"The number of sides comes out as {nm(n, 3)}, which is not a whole number from 3 up. So no polygon fits those numbers. Check what you typed.")
        n = int(n)
        pre.append(f"n must be a whole number: {HL('n = ' + str(n))} sides. Now here is everything about this polygon:")
        return _poly_formulas(n, pre)
    if kind == "missing":
        items = _list(d.get("angles"), "Interior angles", 3, 14)
        n = len(items)
        names = [chr(65 + k) for k in range(n)]
        nice = {m: f"angle {m}" for m in names}
        S = (n - 2) * 180
        given = dict(zip(names, items))
        steps = [f"You typed {n} angles, so the shape has <b>n = {n} sides</b>.",
                 f"<b>The rule:</b> the interior angles of a polygon with n sides add up to (n &minus; 2) &times; 180&deg; = {n - 2} &times; 180&deg; = {HL(nm(S) + DEG)}.",
                 f"So: {HL(' + '.join(names) + f' = {S}&deg;')}"]
        res = solve_angles(names, nice, given, [summ(names, S, "interior angles of a polygon", None)], maxang=360, what="polygon")
        steps += res["steps"]
        v = res["vals"]
        steps.append("<b>Check:</b> " + " + ".join(nm(v[m], 3) for m in names) + f" = {nm(sum(v.values()))}{DEG} &#10003;")
        img = None
        try:
            pts = D.poly_pts([float(v[m]) for m in names])
            labels = {m: _label(res, m) for m in names}
            img = D.fig_polygon(pts, names, labels, f"Polygon with {n} sides: angles add up to {nm(S)}°")
        except Exception:
            img = None
        out = answer_html(res, names, nice)
        return _ok(steps, {"image": img, "text": out} if img else out)
    if kind == "missing_ext":
        items = _list(d.get("angles"), "Exterior angles", 3, 14)
        n = len(items)
        names = [chr(65 + k) for k in range(n)]
        nice = {m: f"exterior angle at {m}" for m in names}
        given = dict(zip(names, items))
        steps = [f"You typed {n} exterior angles, so the shape has <b>n = {n} sides</b>.",
                 f"<b>The rule:</b> the exterior angles of <b>any</b> polygon always add up to {HL('360&deg;')}.",
                 f"So: {HL(' + '.join(names) + ' = 360&deg;')}"]
        res = solve_angles(names, nice, given, [summ(names, 360, "exterior angles of a polygon", None)], maxang=180, what="polygon")
        steps += res["steps"]
        v = res["vals"]
        steps.append("<b>Check:</b> " + " + ".join(nm(v[m], 3) for m in names) + f" = {nm(sum(v.values()))}{DEG} &#10003;")
        inter = [180 - v[m] for m in names]
        steps.append("<b>Interior angles</b> (interior = 180&deg; &minus; exterior): " + ", ".join(f"{m} = {nm(i, 3)}&deg;" for m, i in zip(names, inter)))
        img = None
        try:
            pts = D.poly_pts([float(i) for i in inter])
            img = D.fig_polygon_ext(pts, names, {m: _label(res, m) for m in names}, f"Exterior angles of a {n}-sided polygon")
        except Exception:
            img = None
        out = answer_html(res, names, nice)
        return _ok(steps, {"image": img, "text": out} if img else out)
    raise UErr("Choose what you want to do.")


# ===================================================================== circles ==

@guard
def circle(d):
    thm = d.get("thm", "centre")
    if thm not in ("isorad", "tanrad"):
        import t_circles
        return t_circles.theorem(d)
    from t_circles import _fig, P_, seg as cseg, label as clabel, dot as cdot, mark_angle, right_mark, _b64, g, HL_
    steps = []
    fig, ax = _fig()
    O = (0, 0)
    if thm == "isorad":
        which = d.get("which", "centre")
        A, B = P_(205), P_(335)
        if which == "centre":
            v = num(d.get("v"), "The angle at the centre")
            if not (0 < v < 180):
                raise UErr("The angle at the centre must be between 0 and 180 degrees.")
            base = (180 - v) / 2
            steps += ["<b>Idea:</b> OA and OB are both <b>radii</b> of the same circle, so OA = OB. That makes triangle OAB an <b>isosceles</b> triangle, so its two base angles (at A and at B) are equal.",
                      f"Angle AOB = {g(v)}. The three angles of triangle OAB add up to 180&deg;.",
                      f"Base angles together = 180&deg; &minus; {g(v)} = {nm(180 - v)}&deg;",
                      f"Each base angle = {nm(180 - v)}&deg; &divide; 2 = {HL_(g(base))}"]
            lab_o, lab_a = g(v), "x"
            ans = f"<b>Angle OAB = angle OBA = {g(base)}</b>"
        else:
            v = num(d.get("v"), "The base angle")
            if not (0 < v < 90):
                raise UErr("A base angle must be between 0 and 90 degrees.")
            c = 180 - 2 * v
            steps += ["<b>Idea:</b> OA = OB (radii), so triangle OAB is isosceles and the base angles at A and B are equal.",
                      f"Angle OAB = angle OBA = {g(v)}.",
                      f"Angle AOB = 180&deg; &minus; {g(v)} &minus; {g(v)} = 180&deg; &minus; {nm(2 * v)}&deg; = {HL_(g(c))}"]
            lab_o, lab_a = "x", g(v)
            ans = f"<b>Angle AOB = {g(c)}</b>"
        for p_, n_ in ((A, "A"), (B, "B")):
            cdot(ax, p_)
            clabel(ax, p_, n_)
        cdot(ax, O)
        ax.text(0.0, -0.12, "O", fontsize=13, fontweight="bold", ha="center")
        cseg(ax, O, A)
        cseg(ax, O, B)
        cseg(ax, A, B)
        mark_angle(ax, O, A, B, lab_o, r=0.26)
        mark_angle(ax, A, O, B, lab_a, r=0.22)
        mark_angle(ax, B, A, O, lab_a, r=0.22)
    else:
        which = d.get("which", "centre")
        Ap = P_(215)
        # tangent at A is perpendicular to OA
        dirv = (math.cos(math.radians(305)), math.sin(math.radians(305)))
        T = (Ap[0] + dirv[0] * 1.15, Ap[1] + dirv[1] * 1.15)
        if which == "centre":
            v = num(d.get("v"), "Angle AOT")
        else:
            v = num(d.get("v"), "Angle ATO")
        if not (0 < v < 90):
            raise UErr("That angle must be between 0 and 90 degrees (it is inside a right-angled triangle).")
        r = 90 - v
        steps += ["<b>Rule:</b> a <b>tangent</b> (a line that just touches the circle at one point) is at <b>90&deg;</b> to the <b>radius</b> drawn to that point.",
                  "So in the picture, angle OAT = 90&deg;, and triangle OAT has a right angle at A. Its other two angles add up to 90&deg;."]
        if which == "centre":
            steps.append(f"Angle AOT = {g(v)}, so angle ATO = 90&deg; &minus; {g(v)} = {HL_(g(r))}")
            lab_o, lab_t, ans = g(v), "x", f"<b>Angle ATO = {g(r)}</b>"
        else:
            steps.append(f"Angle ATO = {g(v)}, so angle AOT = 90&deg; &minus; {g(v)} = {HL_(g(r))}")
            lab_o, lab_t, ans = "x", g(v), f"<b>Angle AOT = {g(r)}</b>"
        cdot(ax, Ap)
        clabel(ax, Ap, "A")
        cdot(ax, T)
        ax.text(T[0] + 0.12, T[1] - 0.1, "T", fontsize=13, fontweight="bold")
        cdot(ax, O)
        ax.text(0.05, 0.12, "O", fontsize=13, fontweight="bold")
        cseg(ax, O, Ap)
        cseg(ax, O, T)
        cseg(ax, Ap, T, color="#7c3aed")
        right_mark(ax, Ap, O, T)
        mark_angle(ax, O, Ap, T, lab_o, r=0.3)
        mark_angle(ax, T, Ap, O, lab_t, r=0.3)
        ax.set_xlim(-1.6, 1.9)
        ax.set_ylim(-1.9, 1.5)
    return _ok(steps, {"image": _b64(fig), "text": ans})


# ===================================================================== rules ==

RULES = [
    ("types", "Types of angles (acute, right, obtuse, straight, reflex)"),
    ("comp", "Complementary and supplementary angles"),
    ("point", "Angles at a point = 360&deg;"),
    ("line", "Angles on a straight line = 180&deg;"),
    ("vert", "Vertically opposite angles are equal"),
    ("corr", "Parallel lines: corresponding angles (F)"),
    ("alt", "Parallel lines: alternate angles (Z)"),
    ("coint", "Parallel lines: co-interior angles (C)"),
    ("tri", "Triangle: angles add up to 180&deg;"),
    ("tri_ext", "Triangle: exterior angle"),
    ("tri_iso", "Isosceles triangle"),
    ("tri_equi", "Equilateral triangle"),
    ("tri_right", "Right-angled triangle"),
    ("quad", "Quadrilateral: angles add up to 360&deg;"),
    ("rect", "Square and rectangle"),
    ("para", "Parallelogram"),
    ("rhombus", "Rhombus"),
    ("trap", "Trapezium"),
    ("kite", "Kite"),
    ("cyc", "Cyclic quadrilateral"),
    ("poly", "Polygon: sum of interior angles"),
    ("poly_ext", "Polygon: exterior angles = 360&deg;"),
    ("poly_reg", "Regular polygon: each angle, and the number of sides"),
    ("circ", "Angles in a circle"),
    ("all", "Cheat sheet: every formula in one table"),
]

_EX = {
    "point": (basic, {"kind": "point", "angles": "120, 2x, x+30"}),
    "line": (basic, {"kind": "line", "angles": "50, 2x, x+10"}),
    "vert": (basic, {"kind": "vert", "a1": "3x+10", "a2": "2x+40"}),
    "corr": (parallel, {"rel": "corr", "a1": "3x+10", "a2": "2x+40"}),
    "alt": (parallel, {"rel": "alt", "a1": "4x-20", "a2": "2x+30"}),
    "coint": (parallel, {"rel": "coint", "a1": "3x+10", "a2": "2x+20"}),
    "tri": (triangle, {"kind": "any", "a": "50", "b": "2x", "c": "x+10"}),
    "tri_ext": (triangle, {"kind": "ext", "ee": "3x+20", "ea": "50", "eb": "x+30"}),
    "tri_iso": (triangle, {"kind": "iso", "ia": "40", "ib": "", "ic": ""}),
    "tri_equi": (triangle, {"kind": "equi", "e": ""}),
    "tri_right": (triangle, {"kind": "right", "ra": "2x+10", "rb": "x+20"}),
    "quad": (quad, {"shape": "any", "qa": "x", "qb": "2x", "qc": "3x", "qd": "90"}),
    "rect": (quad, {"shape": "rectangle", "sa": "", "theta": "35"}),
    "para": (quad, {"shape": "parallelogram", "a": "70", "b": "", "c": "", "d": ""}),
    "rhombus": (quad, {"shape": "rhombus", "a": "70", "b": "", "c": "", "d": ""}),
    "trap": (quad, {"shape": "trap", "a": "75", "b": "60", "c": "", "d": ""}),
    "kite": (quad, {"shape": "kite", "ka": "100", "kb": "70", "kc": "", "kd": ""}),
    "cyc": (quad, {"shape": "cyclic", "a": "80", "b": "105", "c": "", "d": ""}),
    "poly": (polygon, {"kind": "missing", "angles": "100, 2x, 3x, 120, 110"}),
    "poly_ext": (polygon, {"kind": "missing_ext", "angles": "60, 2x, 3x, 90"}),
    "poly_reg": (polygon, {"kind": "formulas", "n": "8"}),
    "circ": (circle, {"thm": "centre", "which": "circ", "v": "40"}),
}

_INTRO = {
    "point": ("angles at a point", "a + b + c + &hellip; = 360&deg;",
              ["Stand in the middle of a room and turn all the way round until you face the same way again. That is <b>one full turn</b>, and it measures <b>360&deg;</b>.",
               "Now imagine lines going out from the point you are standing on, splitting the full turn into pieces. Every piece is an angle, and <b>all the pieces together make 360&deg;</b>."]),
    "line": ("angles on a straight line", "a + b + c + &hellip; = 180&deg;",
             ["A straight line is exactly <b>half a full turn</b>, and half of 360&deg; is <b>180&deg;</b>.",
              "If some lines come out of a point on a straight line, all the angles on <b>one side</b> of the line add up to 180&deg;. Two angles like this are called <b>supplementary</b>."]),
    "vert": ("vertically opposite angles", "vertically opposite angles are EQUAL",
             ["When two straight lines cross they make four angles. The two angles that are <b>directly opposite each other</b> (touching only at the crossing point) are called <b>vertically opposite angles</b>.",
              "They are always <b>equal</b>. (Reason: each one makes 180&deg; with the same neighbour, so they must be the same size.)"]),
    "corr": ("corresponding angles", "corresponding angles are EQUAL (F-shape)",
             ["Draw two <b>parallel</b> lines (lines that never meet, like railway tracks) and a third line cutting across both. The cutting line is called a <b>transversal</b>.",
              "<b>Corresponding angles</b> are in the <b>same position</b> at the two crossings, like two corners that both face 'up and right'. Look for the letter <b>F</b> (it can be back to front or upside down).",
              "Because the lines are parallel, corresponding angles are <b>equal</b>. <b>This only works when the lines are parallel.</b>"]),
    "alt": ("alternate angles", "alternate angles are EQUAL (Z-shape)",
            ["<b>Alternate angles</b> are <b>inside</b> the two parallel lines, on <b>opposite sides</b> of the cutting line. Look for the letter <b>Z</b> (or a back-to-front Z).",
             "When the lines are parallel, alternate angles are <b>equal</b>. The corners inside the Z are the two equal angles."]),
    "coint": ("co-interior (allied) angles", "co-interior angles add up to 180&deg; (C-shape)",
              ["<b>Co-interior angles</b> are <b>inside</b> the two parallel lines on the <b>same side</b> of the cutting line. Look for the letter <b>C</b> (or <b>U</b>).",
               "When the lines are parallel, co-interior angles <b>add up to 180&deg;</b>. They are not equal (unless both are 90&deg;)."]),
    "tri": ("the angles of a triangle", "A + B + C = 180&deg;",
            ["Tear the three corners off any paper triangle and put them side by side: they make a <b>straight line</b>. That is why the three angles of <b>every</b> triangle add up to <b>180&deg;</b>.",
             "So if you know two angles, the third is <b>180&deg; minus the other two</b>."]),
    "tri_ext": ("the exterior angle of a triangle", "exterior angle = sum of the two interior opposite angles",
                ["Extend one side of the triangle outwards. The angle outside the triangle, between the extension and the next side, is the <b>exterior angle</b>.",
                 "It equals the <b>two inside angles that are far away from it</b> added together. This is a quick shortcut so you don't need to find the third angle first."]),
    "tri_iso": ("an isosceles triangle", "two equal sides &rarr; two equal base angles",
                ["An <b>isosceles</b> triangle has <b>two sides the same length</b> (marked with matching little ticks on the diagram).",
                 "The angles at the <b>bottom of those two equal sides</b> are the <b>base angles</b>, and they are <b>equal</b>. Then use 180&deg; for the triangle total."]),
    "tri_equi": ("an equilateral triangle", "each angle = 60&deg;",
                 ["<b>Equilateral</b> means <b>all three sides are equal</b>, so <b>all three angles are equal</b> too.",
                  "Since the angles add up to 180&deg;: 180&deg; &divide; 3 = <b>60&deg;</b> each."]),
    "tri_right": ("a right-angled triangle", "the two acute angles add up to 90&deg;",
                  ["A <b>right-angled</b> triangle has one angle of exactly <b>90&deg;</b> (shown by the little square).",
                   "The other two angles must share what is left of 180&deg;: 180&deg; &minus; 90&deg; = 90&deg;. So they add up to <b>90&deg;</b>."]),
    "quad": ("the angles of a quadrilateral", "A + B + C + D = 360&deg;",
             ["A <b>quadrilateral</b> is any shape with <b>4 straight sides</b>. Draw one diagonal and it splits into <b>2 triangles</b>.",
              "Each triangle has angles adding to 180&deg;, so the four angles add up to 2 &times; 180&deg; = <b>360&deg;</b>."]),
    "rect": ("squares and rectangles", "all four angles are 90&deg;",
             ["A <b>square</b> and a <b>rectangle</b> both have <b>four right angles</b>. The diagonals of a rectangle are equal and cut each other in half."]),
    "para": ("a parallelogram", "opposite angles equal; neighbouring angles add to 180&deg;",
             ["A <b>parallelogram</b> has two pairs of parallel sides (green arrows). Opposite angles are <b>equal</b>. Angles next to each other are co-interior angles between parallel lines, so they add to <b>180&deg;</b>."]),
    "rhombus": ("a rhombus", "a parallelogram with four equal sides; diagonals cross at 90&deg;",
                ["A <b>rhombus</b> is a parallelogram with <b>4 equal sides</b>. Opposite angles are equal and neighbouring angles add to 180&deg;.",
                 "Its diagonals cross at <b>90&deg;</b> and <b>cut the corners in half</b>."]),
    "trap": ("a trapezium", "A + D = 180&deg; and B + C = 180&deg;",
             ["A <b>trapezium</b> has <b>one pair of parallel sides</b>. The two slanted sides are like transversals cutting the parallel sides, so the angles on the same slanted side are <b>co-interior</b> and add up to <b>180&deg;</b>."]),
    "kite": ("a kite", "one pair of equal angles; 4 angles add to 360&deg;",
             ["A <b>kite</b> has <b>two pairs of equal neighbouring sides</b>. It is symmetrical about one diagonal, so the two angles at the ends of the other diagonal are <b>equal</b>.",
              "As with any quadrilateral, the four angles add up to 360&deg;."]),
    "cyc": ("a cyclic quadrilateral", "opposite angles add up to 180&deg;",
            ["A quadrilateral whose four corners all lie <b>on a circle</b> is called <b>cyclic</b>.",
             "Its <b>opposite angles add up to 180&deg;</b> (A + C = 180&deg; and B + D = 180&deg;)."]),
    "poly": ("the interior angles of a polygon", "sum = (n &minus; 2) &times; 180&deg;",
             ["A <b>polygon</b> is a flat shape with straight sides; <b>n</b> is the number of sides. Draw lines from one corner to all the others: you get <b>n &minus; 2 triangles</b>.",
              "So the interior angles add up to <b>(n &minus; 2) &times; 180&deg;</b>."]),
    "poly_ext": ("the exterior angles of a polygon", "exterior angles always add up to 360&deg;",
                 ["Extend each side of the polygon a little. The angle between each extension and the next side is an <b>exterior angle</b>.",
                  "Walk round the edge of the polygon: you turn at every corner and end up facing the way you started, so the turns add up to exactly <b>one full turn = 360&deg;</b>. This works for <b>every</b> polygon.",
                  "At each corner: interior angle + exterior angle = 180&deg;."]),
    "poly_reg": ("a regular polygon", "each exterior = 360&deg; &divide; n; each interior = 180&deg; &minus; exterior",
                 ["A <b>regular</b> polygon has all its sides equal and all its angles equal.",
                  "So each exterior angle = 360&deg; &divide; n, and each interior angle = 180&deg; &minus; exterior (or (n &minus; 2) &times; 180&deg; &divide; n). If you are given an angle, you can work out n backwards."]),
    "circ": ("angles in a circle", "angle at the centre = 2 &times; angle at the circumference",
             ["The most important rule: an angle at the <b>centre</b> of a circle is <b>double</b> the angle at the <b>edge</b> (circumference) when both are made from the same two points. More rules are on the <b>Angles in a circle</b> tab."]),
}


def _cheat():
    rows = [
        ("Angles at a point", "a + b + c + &hellip; = 360&deg;"),
        ("Angles on a straight line", "a + b + &hellip; = 180&deg;"),
        ("Complementary angles", "a + b = 90&deg;"),
        ("Vertically opposite angles", "equal"),
        ("Corresponding angles (F), parallel lines", "equal"),
        ("Alternate angles (Z), parallel lines", "equal"),
        ("Co-interior angles (C), parallel lines", "add up to 180&deg;"),
        ("Triangle (any)", "A + B + C = 180&deg;"),
        ("Exterior angle of a triangle", "= sum of the two interior opposite angles"),
        ("Isosceles triangle", "base angles equal"),
        ("Equilateral triangle", "each angle = 60&deg;"),
        ("Right-angled triangle", "the other two angles add up to 90&deg;"),
        ("Quadrilateral (any)", "A + B + C + D = 360&deg;"),
        ("Square, rectangle", "each angle = 90&deg;"),
        ("Parallelogram, rhombus", "opposite angles equal; neighbours add to 180&deg;"),
        ("Rhombus diagonals", "cross at 90&deg; and bisect the corners"),
        ("Trapezium (AB &#8741; DC)", "A + D = 180&deg;, B + C = 180&deg;"),
        ("Kite", "one pair of opposite angles equal (B = D)"),
        ("Cyclic quadrilateral", "opposite angles add up to 180&deg;"),
        ("Polygon, sum of interior angles", "(n &minus; 2) &times; 180&deg;"),
        ("Polygon, sum of exterior angles", "360&deg;"),
        ("Regular polygon, each exterior angle", "360&deg; &divide; n"),
        ("Regular polygon, each interior angle", "(n &minus; 2) &times; 180&deg; &divide; n  or  180&deg; &minus; exterior"),
        ("Number of sides of a regular polygon", "n = 360&deg; &divide; exterior angle"),
        ("Circle: angle at centre", "2 &times; angle at the circumference"),
        ("Circle: angle in a semicircle", "90&deg;"),
        ("Circle: angles in the same segment", "equal"),
        ("Circle: tangent and radius", "meet at 90&deg;"),
    ]
    return rows


@guard
def rules(d):
    k = d.get("rule", "types")
    if k == "types":
        steps = ["An <b>angle</b> measures how much a line has <b>turned</b>. We measure it in <b>degrees</b> (&deg;). A full turn all the way round is 360&deg;.",
                 "We give angles names depending on their size:",
                 _table([("Acute", "smaller than 90&deg;", "like a slice of pizza"), ("Right angle", "exactly 90&deg;", "corner of your book"),
                         ("Obtuse", "bigger than 90&deg;, smaller than 180&deg;", "a door opened wide"),
                         ("Straight", "exactly 180&deg;", "a straight line"),
                         ("Reflex", "bigger than 180&deg;, smaller than 360&deg;", "the 'outside' of a corner"),
                         ("Full turn", "exactly 360&deg;", "all the way round")], ["Name", "Size", "Think of it as"])]
        return _ok(steps, {"image": D.fig_types(), "text": "<b>Acute &lt; 90&deg; &lt; Obtuse &lt; 180&deg; &lt; Reflex &lt; 360&deg;</b>"})
    if k == "comp":
        steps = ["<b>Complementary angles</b> are two angles that add up to <b>90&deg;</b>. (Think: C for Corner &mdash; a right-angled corner.)",
                 "<b>Supplementary angles</b> are two angles that add up to <b>180&deg;</b>. (Think: S for Straight line.)",
                 "To find the partner: <b>complement = 90&deg; &minus; the angle</b>, and <b>supplement = 180&deg; &minus; the angle</b>.",
                 "Example: the complement of 35&deg; is 90&deg; &minus; 35&deg; = 55&deg;, and the supplement of 60&deg; is 180&deg; &minus; 60&deg; = 120&deg;."]
        return _ok(steps, {"image": D.fig_comp_supp(), "text": "<b>Complementary: 90&deg; &nbsp;|&nbsp; Supplementary: 180&deg;</b>"})
    if k == "all":
        steps = ["<b>Every angle rule on one page.</b> Pick any rule from the list above to see it drawn and worked out step by step.",
                 _table(_cheat(), ["Rule", "Formula / fact"])]
        return _ok(steps, "<b>Learn the rule first, then practise with the other tabs.</b>")
    if k not in _EX:
        raise UErr("Choose a rule.")
    title_, formula, expl = _INTRO[k]
    fn, args = _EX[k]
    inner = fn(dict(args))
    if not inner.get("ok"):
        return inner
    steps = [f"<b>{title_.capitalize()}</b>", f"<b>Rule:</b> {HL(formula)}"] + expl
    steps.append("<b>Worked example</b> (you can try your own numbers in the other tabs):")
    steps += inner["steps"]
    return _ok(steps, inner["result"])


# ====================================================================== spec ==

_RULE_OPTS = [(k, l) for k, l in RULES]

_THM = [("centre", "Angle at the centre = 2 &times; angle at the circumference"), ("same", "Angles in the same segment are equal"),
        ("semi", "Angle in a semicircle = 90&deg;"), ("cyclic", "Cyclic quadrilateral"), ("alt", "Alternate segment (tangent &amp; chord)"),
        ("tangents", "Two tangents from a point (angles)"), ("isorad", "Triangle made by two radii (isosceles)"),
        ("tanrad", "Tangent meets radius at 90&deg;")]

SPEC = {
    "title": "Angles",
    "intro": "Every angle rule <b>drawn to scale</b> and worked out <b>step by step</b>, from angles on a line to polygons and circles. "
             "<b>Start with the first tab</b> to see each rule explained, then practise with the other tabs. "
             "You can type a number (like <b>50</b>) or an expression with x (like <b>3x+10</b>).",
    "tabs": [
        {"id": "arl", "label": "Learn the rules", "title": "Learn the angle rules", "endpoint": "rules",
         "hint": "Pick a rule to see a clear drawing, an explanation in plain words and a worked example.",
         "fields": [select("rule", "Which rule?", _RULE_OPTS, wide=True)], "button": "Show me"},
        {"id": "aba", "label": "Lines and points", "title": "Angles at a point, on a line and vertically opposite", "endpoint": "basic",
         "hint": "Type the angles separated by commas. Use <b>x</b> (or leave an angle empty) for what you want to find. Example: <b>120, 2x, x+30</b>",
         "fields": [select("kind", "What kind of angles?", [("point", "Angles at a point (360&deg;)"), ("line", "Angles on a straight line (180&deg;)"),
                                                           ("right", "Angles in a right angle (90&deg;)"), ("vert", "Two lines crossing (vertically opposite)"),
                                                           ("classify", "Name an angle (acute, obtuse&hellip;)")], wide=True),
                    field("angles", "Angles (separate with commas)", "120, 2x, x+30", show_if={"kind": "point"}),
                    field("angles", "Angles (separate with commas)", "50, 2x, x+10", show_if={"kind": "line"}),
                    field("angles", "Angles (separate with commas)", "30, 2x", show_if={"kind": "right"}),
                    field("a1", "One angle", "3x+10", show_if={"kind": "vert"}),
                    field("a2", "The angle opposite it (optional)", "2x+40", show_if={"kind": "vert"}),
                    field("v", "The angle", "130", show_if={"kind": "classify"})]},
        {"id": "apl", "label": "Parallel lines", "title": "Parallel lines and a transversal", "endpoint": "parallel",
         "hint": "Give one angle, and the angle you want. Leave the second box empty to find it, or type expressions with x in both to find x.",
         "fields": [select("rel", "How are the two angles related?", [("corr", "Corresponding angles (F-shape)"), ("alt", "Alternate angles (Z-shape)"),
                                                                      ("coint", "Co-interior angles (C-shape)"), ("line", "Angles on a straight line"),
                                                                      ("vert", "Vertically opposite angles"), ("all", "Show ALL eight angles from one angle")], wide=True),
                    field("a1", "Angle X", "65"),
                    field("a2", "Angle Y (leave empty to find it)", "", show_if={"rel": ["corr", "alt", "coint", "line", "vert"]})]},
        {"id": "atr", "label": "Triangles", "title": "Angles in triangles", "endpoint": "triangle",
         "hint": "Leave one angle empty to find it, or use x in the angles.",
         "fields": [select("kind", "Type of triangle", [("any", "Any triangle (angles add up to 180&deg;)"), ("iso", "Isosceles triangle"), ("equi", "Equilateral triangle"),
                                                       ("right", "Right-angled triangle"), ("ext", "Exterior angle")], wide=True),
                    field("a", "Angle A", "50", show_if={"kind": "any"}), field("b", "Angle B", "2x", show_if={"kind": "any"}), field("c", "Angle C (empty = find it)", "x+10", show_if={"kind": "any"}),
                    field("ia", "Apex angle A (the top, between the equal sides)", "40", show_if={"kind": "iso"}),
                    field("ib", "Base angle B", "", show_if={"kind": "iso"}), field("ic", "Base angle C", "", show_if={"kind": "iso"}),
                    field("e", "An angle written with x (optional)", "", show_if={"kind": "equi"}),
                    field("ra", "Acute angle A", "2x+10", show_if={"kind": "right"}), field("rb", "Acute angle B", "x+20", show_if={"kind": "right"}),
                    field("ee", "Exterior angle", "3x+20", show_if={"kind": "ext"}), field("ea", "Interior opposite angle A", "50", show_if={"kind": "ext"}),
                    field("eb", "Interior opposite angle B", "x+30", show_if={"kind": "ext"})]},
        {"id": "aqu", "label": "Quadrilaterals", "title": "Angles in four-sided shapes", "endpoint": "quad",
         "hint": "Pick the shape, then give the angles you know. Leave the rest empty.",
         "fields": [select("shape", "Shape", [("square", "Square"), ("rectangle", "Rectangle"), ("parallelogram", "Parallelogram"), ("rhombus", "Rhombus"),
                                              ("trap", "Trapezium"), ("itrap", "Isosceles trapezium"), ("kite", "Kite"), ("cyclic", "Cyclic quadrilateral"),
                                              ("any", "Any quadrilateral")], wide=True),
                    field("sa", "An angle written with x (optional)", "", show_if={"shape": ["square", "rectangle"]}),
                    field("theta", "Angle the diagonal makes with the long side", "35", show_if={"shape": "rectangle"}),
                    field("a", "Angle A", "70", show_if={"shape": ["parallelogram", "rhombus", "trap", "itrap", "cyclic"]}),
                    field("b", "Angle B", "", show_if={"shape": ["parallelogram", "rhombus", "trap", "itrap", "cyclic"]}),
                    field("c", "Angle C", "", show_if={"shape": ["parallelogram", "rhombus", "trap", "itrap", "cyclic"]}),
                    field("d", "Angle D", "", show_if={"shape": ["parallelogram", "rhombus", "trap", "itrap", "cyclic"]}),
                    field("ka", "Angle A (top)", "100", show_if={"shape": "kite"}), field("kb", "Angle B (side)", "70", show_if={"shape": "kite"}),
                    field("kc", "Angle C (bottom)", "", show_if={"shape": "kite"}), field("kd", "Angle D (side)", "", show_if={"shape": "kite"}),
                    field("qa", "Angle A", "x", show_if={"shape": "any"}), field("qb", "Angle B", "2x", show_if={"shape": "any"}),
                    field("qc", "Angle C", "3x", show_if={"shape": "any"}), field("qd", "Angle D", "90", show_if={"shape": "any"})]},
        {"id": "apo", "label": "Polygons", "title": "Polygons: interior and exterior angles", "endpoint": "polygon",
         "hint": "Use the formulas for any polygon, or find missing angles of a polygon that is not regular.",
         "fields": [select("kind", "What do you want to do?", [("formulas", "Formulas for a polygon with n sides"), ("reg", "Regular polygon: find n from an angle"),
                                                              ("missing", "Find a missing interior angle (irregular polygon)"),
                                                              ("missing_ext", "Find a missing exterior angle")], wide=True),
                    field("n", "Number of sides (n)", "6", show_if={"kind": "formulas"}),
                    select("find", "I know", [("int", "each interior angle"), ("ext", "each exterior angle"), ("sum", "the sum of the interior angles")], show_if={"kind": "reg"}),
                    field("v", "That angle (degrees)", "135", show_if={"kind": "reg"}),
                    field("angles", "Interior angles (commas; empty or x = find it)", "100, 2x, 3x, 120, 110", show_if={"kind": "missing"}),
                    field("angles", "Exterior angles (commas; empty or x = find it)", "60, 2x, 3x, 90", show_if={"kind": "missing_ext"})]},
        {"id": "aci", "label": "Angles in a circle", "title": "Angles in a circle", "endpoint": "circle",
         "hint": "Circle theorems with diagrams. (More circle work, like arcs and sectors, is in the Circle Theorems topic.)",
         "fields": [select("thm", "Rule", _THM, wide=True),
                    select("which", "Which angle do you know?", [("circ", "the angle at the circumference"), ("centre", "the angle at the centre")], show_if={"thm": "centre"}),
                    select("which", "What do you know?", [("opp", "one angle (find the opposite angle)"), ("ext", "an exterior angle (find the interior opposite angle)")], show_if={"thm": "cyclic"}),
                    select("which", "What do you know?", [("centre", "the angle at the centre AOB"), ("base", "a base angle")], show_if={"thm": "isorad"}),
                    select("which", "What do you know?", [("centre", "angle AOT (at the centre)"), ("t", "angle ATO (at the tangent point)")], show_if={"thm": "tanrad"}),
                    field("v", "The angle (degrees)", "40", show_if={"thm": ["centre", "same", "semi", "cyclic", "alt", "tangents", "isorad", "tanrad"]})]},
    ],
}

topics.register("angles", SPEC, {"rules": rules, "basic": basic, "parallel": parallel, "triangle": triangle, "quad": quad, "polygon": polygon, "circle": circle})
