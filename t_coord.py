"""Coordinate geometry: equation of a line, parallel/perpendicular lines, section formula, area and collinearity,
circles and the distance from a point to a line (exact fractions + matplotlib diagrams)."""
import math
import re
from fractions import Fraction

import topics
from tcommon import UErr, num, field, select, guard, _ok, _fail
from log_core import LogErr
from mpoly import MP, parse_poly, br
from t_conics import _canvas, _mark, _halo, _b64, BLUE, RED, GREEN, ORANGE, PURPLE, GREY, INK

MINUS = "&minus;"
PTS_RE = r"\(\s*([^(),]+?)\s*,\s*([^(),]+?)\s*\)"


def HL(s):
    return f"<span class='hl'>{s}</span>"


def q_(x):
    x = Fraction(x)
    return (str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}").replace("-", MINUS)


def qp(x):
    """number, bracketed if negative (for substitution)"""
    x = Fraction(x)
    return f"({q_(x)})" if x < 0 else q_(x)


def P_(p):
    return f"({q_(p[0])}, {q_(p[1])})"


def wrap(fn):
    def w(d):
        try:
            return fn(d)
        except (UErr, LogErr) as e:
            return _fail(str(e))
    w.__name__ = fn.__name__
    return w


# ------------------------------------------------------------- exact square roots
def surd(q):
    """sqrt of a non-negative Fraction -> (html text, float, is_exact_rational)"""
    q = Fraction(q)
    if q < 0:
        raise UErr("Cannot take the square root of a negative number here.")
    n = q.numerator * q.denominator
    d = q.denominator
    s = 1
    r = n
    k = 2
    while k * k <= r:
        while r % (k * k) == 0:
            r //= k * k
            s *= k
        k += 1
    val = math.sqrt(float(q))
    if r == 1:
        return q_(Fraction(s, d)), val, True
    top = ("" if s == 1 else str(s)) + f"&radic;{r}"
    return (top if d == 1 else f"{top}/{d}"), val, False


def decim(x, p=3):
    s = f"{x:.{p}f}".rstrip("0").rstrip(".")
    return s.replace("-", MINUS)


# ------------------------------------------------------------- parsing
def parse_pts(text, label="Points", lo=1, hi=8):
    t = (text or "").replace("−", "-")
    pairs = re.findall(PTS_RE, t)
    if len(pairs) < lo:
        raise UErr(f"{label}: write the point{'s' if lo > 1 else ''} like (2, 3){', (5, -1)' if lo > 1 else ''}.")
    if len(pairs) > hi:
        raise UErr(f"{label}: at most {hi} points please.")
    left = re.sub(PTS_RE, "", t)
    if re.search(r"[^\s,;]", left):
        raise UErr(f"{label}: I could not read all of that. Write each point as (x, y), separated by commas.")
    out = [(Fraction(num(a, label)), Fraction(num(b, label))) for a, b in pairs]
    if any(abs(c) > 10 ** 4 for p in out for c in p):
        raise UErr("Please keep the coordinates smaller than 10000.")
    return out


def one_pt(text, label="Point"):
    return parse_pts(text, label, 1, 1)[0]


def parse_line(text, label="Line"):
    """'y = 2x + 3' or '2x - 3y + 6 = 0' -> (A, B, C) integers, A>0 (or A=0,B>0), Ax+By+C=0"""
    s = str(text or "").strip().replace("−", "-")
    if not s:
        raise UErr(f"{label}: please type the equation of the line, for example y = 2x + 3.")
    if s.count("=") > 1:
        raise UErr(f"{label}: use only one = sign.")
    if "=" in s:
        l, r = s.split("=")
        G = parse_poly(l, allow_vars=("x", "y")) - parse_poly(r or "0", allow_vars=("x", "y"))
    else:
        G = parse_poly(s, allow_vars=("x", "y"))
    if G.total_deg() != 1 and not (G.deg_in("x") <= 1 and G.deg_in("y") <= 1 and G.total_deg() == 1):
        raise UErr(f"{label}: this is not a straight line (only x, y and numbers, no x² or xy). Example: 3x - 2y = 6")
    A = G.coeff_in("x", 1).const_value()
    B = G.coeff_in("y", 1).const_value()
    C = G.coeff_in("x", 0).coeff_in("y", 0).const_value()
    if A == 0 and B == 0:
        raise UErr(f"{label}: that is not the equation of a line.")
    return norm_line(A, B, C)


def norm_line(A, B, C):
    A, B, C = Fraction(A), Fraction(B), Fraction(C)
    L = 1
    for v in (A, B, C):
        L = L * v.denominator // math.gcd(L, v.denominator)
    a, b, c = int(A * L), int(B * L), int(C * L)
    g = math.gcd(math.gcd(abs(a), abs(b)), abs(c)) or 1
    a, b, c = a // g, b // g, c // g
    if a < 0 or (a == 0 and b < 0):
        a, b, c = -a, -b, -c
    return Fraction(a), Fraction(b), Fraction(c)


def gen_text(A, B, C):
    return MP({(("x", 1),): Fraction(A), (("y", 1),): Fraction(B), (): Fraction(C)}).text() + " = 0"


def _coef(m, var):
    m = Fraction(m)
    if m == 0:
        return ""
    s = "" if abs(m) == 1 else (q_(abs(m)) if m.denominator == 1 else f"({q_(abs(m))})")
    return s + var


def slope_text(m, c):
    """y = mx + c"""
    m, c = Fraction(m), Fraction(c)
    t = ("" if m >= 0 else MINUS) + _coef(abs(m), "x") if m != 0 else ""
    if c != 0:
        t = (t + (" + " if c > 0 else f" {MINUS} ") + q_(abs(c))) if t else (q_(c))
    return "y = " + (t or "0")


def line_forms(A, B, C):
    """text of the line in both forms"""
    if B == 0:
        return f"x = {q_(-C / A)}", gen_text(A, B, C)
    return slope_text(-A / B, -C / B), gen_text(A, B, C)


def grad(A, B):
    return None if B == 0 else -A / B


# ------------------------------------------------------------- diagram
def scene(boxpts, items):
    fig, ax = _canvas(boxpts)
    xl, yl = ax.get_xlim(), ax.get_ylim()
    for it in items:
        k = it[0]
        if k == "line":
            _, A, B, C, col, lab = it
            A, B, C = float(A), float(B), float(C)
            if B != 0:
                xs = [xl[0], xl[1]]
                ys = [(-A * x - C) / B for x in xs]
            else:
                xs = [-C / A, -C / A]
                ys = [yl[0], yl[1]]
            ax.plot(xs, ys, "-", color=col, lw=2.2, zorder=3)
            if lab:
                # label near the right/top end inside the box
                if B != 0:
                    lx = xl[1] - (xl[1] - xl[0]) * 0.22
                    ly = (-A * lx - C) / B
                    if not (yl[0] < ly < yl[1]):
                        ly = yl[1] - (yl[1] - yl[0]) * 0.08 if ly > yl[1] else yl[0] + (yl[1] - yl[0]) * 0.08
                        lx = (-B * ly - C) / A if A != 0 else lx
                else:
                    lx, ly = -C / A, yl[1] - (yl[1] - yl[0]) * 0.08
                ax.annotate(lab, (lx, ly), fontsize=9, color=col, fontweight="bold", path_effects=_halo(), zorder=8)
        elif k == "pt":
            _, p, lab, col = it
            _mark(ax, (float(p[0]), float(p[1])), lab, col)
        elif k == "seg":
            _, p, q, col, ls = it
            ax.plot([float(p[0]), float(q[0])], [float(p[1]), float(q[1])], ls, color=col, lw=2, zorder=4)
        elif k == "poly":
            _, pts, col = it
            xs = [float(p[0]) for p in pts] + [float(pts[0][0])]
            ys = [float(p[1]) for p in pts] + [float(pts[0][1])]
            ax.fill(xs, ys, color=col, alpha=0.15, zorder=2)
            ax.plot(xs, ys, "-", color=col, lw=2.2, zorder=4)
        elif k == "circle":
            _, h, kk, r, col = it
            t = [i * 2 * math.pi / 200 for i in range(201)]
            ax.plot([float(h) + r * math.cos(a) for a in t], [float(kk) + r * math.sin(a) for a in t], "-", color=col, lw=2.2, zorder=3)
    ax.set_xlim(xl)
    ax.set_ylim(yl)
    return _b64(fig)


def box_from(*groups):
    out = []
    for g in groups:
        out += list(g)
    return [(float(p[0]), float(p[1])) for p in out]


def _out(steps, text, img):
    return _ok(steps, {"image": img, "text": text})


# ======================================================================= equation of a line
def _through(P, m, steps, name="the line"):
    """equation through P with gradient m (Fraction or None for vertical); returns (A,B,C)"""
    x1, y1 = P
    if m is None:
        steps.append(f"The line is vertical (it goes straight up), so every point on it has the same x: {HL('x = ' + q_(x1))}")
        return norm_line(1, 0, -x1)
    steps.append(f"<b>Use y &minus; y<sub>1</sub> = m(x &minus; x<sub>1</sub>)</b> with the point (x<sub>1</sub>, y<sub>1</sub>) = {P_(P)} and m = {q_(m)}:<br>"
                 f"y &minus; {qp(y1)} = {q_(m)}(x &minus; {qp(x1)})")
    c = y1 - m * x1
    steps.append(f"Multiply out the bracket and move {q_(y1) if y1 != 0 else '0'} across: y = {q_(m)}x {'+' if (-m * x1) >= 0 else MINUS} {q_(abs(m * x1))} {'+' if y1 >= 0 else MINUS} {q_(abs(y1))}, so {HL(slope_text(m, c))}")
    A, B, C = norm_line(-m, 1, -c)
    return A, B, C


def _finish_line(A, B, C, steps, pts=()):
    f1, f2 = line_forms(A, B, C)
    steps.append(f"<b>Final answer</b> in the two usual forms:<br>&bull; gradient-intercept form: {HL(f1)}<br>&bull; general form (whole numbers, no fractions): {HL(f2)}")
    if B != 0:
        m = -A / B
        yi = -C / B
        steps.append(f"<b>Intercepts:</b> put x = 0 to get the y-intercept: y = {q_(yi)}, the point (0, {q_(yi)}). "
                     + (f"Put y = 0 to get the x-intercept: x = {q_(-C / A)}, the point ({q_(-C / A)}, 0)." if A != 0 else "The line is horizontal, so it never meets the x-axis (unless it is the x-axis itself)."))
    else:
        steps.append(f"<b>Intercept:</b> the line is vertical; it meets the x-axis at ({q_(-C / A)}, 0) and never meets the y-axis (unless it is the y-axis).")
    return f1, f2


@wrap
def line_eq(d):
    mode = d.get("mode", "two")
    steps = []
    pts = []
    if mode == "two":
        P1, P2 = one_pt(d.get("p1"), "Point 1"), one_pt(d.get("p2"), "Point 2")
        if P1 == P2:
            raise UErr("The two points are the same. Give two different points.")
        x1, y1 = P1
        x2, y2 = P2
        steps.append(f"<b>Line through</b> A{P_(P1)} and B{P_(P2)}.")
        steps.append(f"<b>Step 1 &ndash; gradient</b> (how steep): m = (y<sub>2</sub> &minus; y<sub>1</sub>)/(x<sub>2</sub> &minus; x<sub>1</sub>) = ({qp(y2)} &minus; {qp(y1)})/({qp(x2)} &minus; {qp(x1)}) = {q_(y2 - y1)}/{q_(x2 - x1)}"
                     + ("" if x1 != x2 else " &rarr; the bottom is 0, so the line is <b>vertical</b> (gradient undefined)."))
        m = None if x1 == x2 else (y2 - y1) / (x2 - x1)
        if m is not None:
            steps[-1] += f" = {HL(q_(m))}"
        A, B, C = _through(P1, m, steps)
        pts = [P1, P2]
        dist2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
        mid = ((x1 + x2) / 2, (y1 + y2) / 2)
    elif mode == "pg":
        P1 = one_pt(d.get("p1"), "Point")
        txt = str(d.get("m") or "").strip().lower()
        if txt in ("undefined", "vertical", "inf"):
            m = None
        else:
            m = Fraction(num(txt, "Gradient"))
        steps.append(f"<b>Line through</b> {P_(P1)} with gradient {q_(m) if m is not None else 'undefined (vertical)'}.")
        A, B, C = _through(P1, m, steps)
        pts = [P1]
        dist2, mid = None, None
    else:
        a = Fraction(num(d.get("a"), "x-intercept"))
        b = Fraction(num(d.get("b"), "y-intercept"))
        if a == 0 or b == 0:
            raise UErr("Intercepts of 0 mean the line passes through the origin; use the 'two points' option instead.")
        steps.append(f"<b>Line cutting the x-axis at {q_(a)} and the y-axis at {q_(b)}.</b> So it passes through ({q_(a)}, 0) and (0, {q_(b)}).")
        steps.append(f"<b>Intercept form:</b> x/a + y/b = 1 &rArr; x/{q_(a)} + y/{q_(b)} = 1")
        steps.append(f"Multiply every term by {q_(a)}&times;{q_(b)} = {q_(a * b)} to clear the fractions: {q_(b)}x + {q_(a)}y = {q_(a * b)}".replace("+ " + MINUS, f"+ {MINUS}"))
        A, B, C = norm_line(b, a, -a * b)
        pts = [(a, Fraction(0)), (Fraction(0), b)]
        dist2, mid = None, None
    f1, f2 = _finish_line(A, B, C, steps)
    if dist2 is not None:
        sq, v, ex = surd(dist2)
        steps.append(f"<b>Extra facts:</b> distance AB = &radic;[(x<sub>2</sub>&minus;x<sub>1</sub>)<sup>2</sup> + (y<sub>2</sub>&minus;y<sub>1</sub>)<sup>2</sup>] = &radic;{q_(dist2)} = {HL(sq)}{'' if ex else ' &asymp; ' + decim(v)}; midpoint = ((x<sub>1</sub>+x<sub>2</sub>)/2, (y<sub>1</sub>+y<sub>2</sub>)/2) = {HL(P_(mid))}")
    items = [("line", A, B, C, BLUE, "")]
    for i, p in enumerate(pts):
        items.append(("pt", p, "ABCD"[i] + P_(p), RED))
    bx = box_from(pts, [(0, 0)])
    if B != 0:
        bx += [(0.0, float(-C / B))]
    if A != 0:
        bx += [(float(-C / A), 0.0)]
    img = scene(bx, items)
    return _out(steps, f"<b>{f1}</b><br>{f2}", img)


# ======================================================================= parallel / perpendicular / meeting / angle
def _meet(L1, L2, steps):
    A1, B1, C1 = L1
    A2, B2, C2 = L2
    det = A1 * B2 - A2 * B1
    if det == 0:
        return None
    x = (B1 * C2 - B2 * C1) / det
    y = (C1 * A2 - C2 * A1) / det
    return x, y


@wrap
def parperp(d):
    mode = d.get("mode", "par")
    steps = []
    items = []
    pts = []
    if mode in ("par", "perp"):
        L = parse_line(d.get("l1"), "Given line")
        P = one_pt(d.get("p"), "Point")
        A, B, C = L
        m0 = grad(A, B)
        f1, f2 = line_forms(A, B, C)
        steps.append(f"<b>Given line:</b> {HL(d.get('l1', '').strip())}. Rewrite it as {f1 if B != 0 else f1}"
                     + (f" so its gradient is <b>m = {q_(m0)}</b>." if m0 is not None else " &ndash; a vertical line with no gradient."))
        if mode == "par":
            steps.append("<b>Parallel lines have the same gradient.</b>")
            m = m0
            steps.append(f"So the new line has gradient {q_(m) if m is not None else 'undefined (vertical)'} and passes through {P_(P)}.")
            nA, nB, nC = _through(P, m, steps)
            col, nm_ = GREEN, "parallel"
        else:
            steps.append("<b>Perpendicular lines:</b> the product of their gradients is &minus;1, so m<sub>2</sub> = &minus;1/m<sub>1</sub> (flip the fraction and change the sign). A horizontal line is perpendicular to a vertical line.")
            if m0 is None:
                m = Fraction(0)
                steps.append("The given line is vertical, so the perpendicular line is horizontal (gradient 0).")
            elif m0 == 0:
                m = None
                steps.append("The given line is horizontal, so the perpendicular line is vertical.")
            else:
                m = -1 / m0
                steps.append(f"m<sub>2</sub> = &minus;1/({q_(m0)}) = {HL(q_(m))}")
            nA, nB, nC = _through(P, m, steps)
            col, nm_ = GREEN, "perpendicular"
        g1, g2 = line_forms(nA, nB, nC)
        steps.append(f"<b>The {nm_} line through {P_(P)}:</b> {HL(g1)} &nbsp;or&nbsp; {HL(g2)}")
        if mode == "perp":
            M = _meet(L, (nA, nB, nC), steps)
            steps.append(f"<i>The two lines meet at {P_(M)} (this is the foot of the perpendicular).</i>")
            pts.append(M)
        items = [("line", A, B, C, BLUE, "given"), ("line", nA, nB, nC, col, nm_), ("pt", P, P_(P), RED)]
        if mode == "perp":
            items.append(("pt", M, P_(M), ORANGE))
        bx = box_from([P], pts, [(0, 0)])
        res = f"<b>{g1}</b><br>{g2}"
    elif mode == "bis":
        P1, P2 = one_pt(d.get("p1"), "Point A"), one_pt(d.get("p2"), "Point B")
        if P1 == P2:
            raise UErr("A and B are the same point.")
        mid = ((P1[0] + P2[0]) / 2, (P1[1] + P2[1]) / 2)
        steps.append(f"<b>Perpendicular bisector of AB</b> where A{P_(P1)}, B{P_(P2)}. It is the line that cuts AB in half at a right angle.")
        steps.append(f"<b>Step 1 &ndash; midpoint</b> of AB = ((x<sub>1</sub>+x<sub>2</sub>)/2, (y<sub>1</sub>+y<sub>2</sub>)/2) = ({q_(P1[0])}+{qp(P2[0])})/2, ({q_(P1[1])}+{qp(P2[1])})/2) = {HL(P_(mid))}".replace("= ((", "= (("))
        if P1[0] == P2[0]:
            m1 = None
            steps.append("<b>Step 2 &ndash; gradient of AB:</b> AB is vertical, so the bisector is horizontal (gradient 0).")
            m = Fraction(0)
        else:
            m1 = (P2[1] - P1[1]) / (P2[0] - P1[0])
            steps.append(f"<b>Step 2 &ndash; gradient of AB:</b> m = ({qp(P2[1])} &minus; {qp(P1[1])})/({qp(P2[0])} &minus; {qp(P1[0])}) = {HL(q_(m1))}")
            if m1 == 0:
                m = None
                steps.append("AB is horizontal, so the bisector is vertical.")
            else:
                m = -1 / m1
                steps.append(f"<b>Step 3 &ndash; perpendicular gradient:</b> &minus;1/({q_(m1)}) = {HL(q_(m))}")
        nA, nB, nC = _through(mid, m, steps)
        g1, g2 = line_forms(nA, nB, nC)
        steps.append(f"<b>Perpendicular bisector:</b> {HL(g1)} &nbsp;or&nbsp; {HL(g2)}")
        items = [("seg", P1, P2, BLUE, "-"), ("line", nA, nB, nC, GREEN, "bisector"), ("pt", P1, "A" + P_(P1), RED), ("pt", P2, "B" + P_(P2), RED), ("pt", mid, "M" + P_(mid), ORANGE)]
        bx = box_from([P1, P2, mid, (0, 0)])
        res = f"<b>{g1}</b><br>{g2}"
    elif mode == "meet":
        L1, L2 = parse_line(d.get("l1"), "Line 1"), parse_line(d.get("l2"), "Line 2")
        steps.append(f"<b>Where do the lines meet?</b> Solve the two equations together (simultaneous equations): {HL(gen_text(*L1))} and {HL(gen_text(*L2))}.")
        M = _meet(L1, L2, steps)
        if M is None:
            same = L1 == L2
            steps.append("The two lines have the <b>same gradient</b>, so " + ("they are the <b>same line</b> (infinitely many common points)." if same else "they are <b>parallel</b> and never meet."))
            res = "<b>" + ("Same line" if same else "Parallel lines: no intersection") + "</b>"
            items = [("line", *L1, BLUE, "L1"), ("line", *L2, RED, "L2")]
            bx = [(0, 0), (5, 5)]
            for L in (L1, L2):
                if L[1] != 0:
                    bx.append((0.0, float(-L[2] / L[1])))
        else:
            A1, B1, C1 = L1
            A2, B2, C2 = L2
            steps.append(f"<b>Elimination:</b> multiply equation 1 by {q_(B2)} and equation 2 by {q_(B1)} so the y-terms match, then subtract: ({q_(A1 * B2)}x) &minus; ({q_(A2 * B1)}x) = {q_(-C1 * B2)} &minus; ({q_(-C2 * B1)}) &rArr; x = {HL(q_(M[0]))}" if B1 != 0 and B2 != 0 else
                         f"Solve: x = {q_(M[0])}")
            steps.append(f"Put x = {q_(M[0])} into one equation to find y: y = {HL(q_(M[1]))}")
            steps.append(f"<b>Check</b> in both equations: {q_(L1[0] * M[0] + L1[1] * M[1] + L1[2])} = 0 &check; and {q_(L2[0] * M[0] + L2[1] * M[1] + L2[2])} = 0 &check;")
            steps.append(f"<b>The lines meet at {HL(P_(M))}.</b>")
            items = [("line", *L1, BLUE, "L1"), ("line", *L2, RED, "L2"), ("pt", M, P_(M), ORANGE)]
            bx = box_from([M, (0, 0)])
            res = f"<b>Meeting point {P_(M)}</b>"
    else:
        L1, L2 = parse_line(d.get("l1"), "Line 1"), parse_line(d.get("l2"), "Line 2")
        m1, m2 = grad(L1[0], L1[1]), grad(L2[0], L2[1])
        steps.append(f"<b>Angle between two lines.</b> Gradients: m<sub>1</sub> = {q_(m1) if m1 is not None else 'undefined (vertical)'}, m<sub>2</sub> = {q_(m2) if m2 is not None else 'undefined (vertical)'}.")
        if m1 is None or m2 is None:
            if m1 is None and m2 is None:
                ang = 0.0
                steps.append("Both lines are vertical, so they are parallel: angle 0&deg;.")
            else:
                mm = m2 if m1 is None else m1
                ang = 90.0 - math.degrees(math.atan(abs(float(mm))))
                steps.append(f"One line is vertical. The other has gradient {q_(mm)}, so it makes an angle of arctan|{q_(mm)}| = {decim(math.degrees(math.atan(abs(float(mm)))), 2)}&deg; with the x-axis. The angle with the vertical line is 90&deg; &minus; that = {HL(decim(ang, 2) + '&deg;')}.")
        else:
            steps.append("<b>Formula:</b> tan &theta; = | (m<sub>1</sub> &minus; m<sub>2</sub>)/(1 + m<sub>1</sub>m<sub>2</sub>) |")
            den = 1 + m1 * m2
            if den == 0:
                ang = 90.0
                steps.append(f"1 + m<sub>1</sub>m<sub>2</sub> = 1 + ({q_(m1)})({q_(m2)}) = 0, so tan &theta; is undefined: the lines are <b>perpendicular</b>, &theta; = {HL('90&deg;')}.")
            else:
                t = abs((m1 - m2) / den)
                ang = math.degrees(math.atan(float(t)))
                steps.append(f"tan &theta; = |({q_(m1)} &minus; {qp(m2)})/(1 + ({q_(m1)})({qp(m2)}))| = |{q_(m1 - m2)}/{q_(den)}| = {q_(t)}")
                steps.append(f"&theta; = tan<sup>&minus;1</sup>({q_(t)}) = {HL(decim(ang, 2) + '&deg;')} (this is the acute angle between the lines)" + ("; they are parallel." if t == 0 else ""))
        items = [("line", *L1, BLUE, "L1"), ("line", *L2, RED, "L2")]
        M = _meet(L1, L2, steps)
        bx = [(0, 0)] if M is None else box_from([M, (0, 0)])
        if M is not None:
            items.append(("pt", M, P_(M), ORANGE))
        res = f"<b>&theta; = {decim(ang, 2)}&deg;</b>"
    img = scene(bx, items)
    return _out(steps, res, img)


# ======================================================================= section formula
@wrap
def section(d):
    mode = d.get("mode", "int")
    A, B = one_pt(d.get("a"), "Point A"), one_pt(d.get("b"), "Point B")
    if A == B:
        raise UErr("A and B are the same point.")
    steps = []
    items = [("seg", A, B, BLUE, "-"), ("pt", A, "A" + P_(A), RED), ("pt", B, "B" + P_(B), RED)]
    if mode in ("int", "ext"):
        m = Fraction(num(d.get("m"), "m"))
        n = Fraction(num(d.get("n"), "n"))
        if m <= 0 or n <= 0:
            raise UErr("The ratio numbers m and n must be positive.")
        if mode == "int":
            steps.append(f"<b>P divides AB internally in the ratio {q_(m)} : {q_(n)}.</b> That means P is on the line between A and B, and AP : PB = {q_(m)} : {q_(n)}.")
            steps.append("<b>Section formula (internal):</b> P = ( (n x<sub>1</sub> + m x<sub>2</sub>)/(m + n) , (n y<sub>1</sub> + m y<sub>2</sub>)/(m + n) ). Note: the ratio number m goes with the <i>second</i> point B.")
            den = m + n
            px = (n * A[0] + m * B[0]) / den
            py = (n * A[1] + m * B[1]) / den
            steps.append(f"x = ({q_(n)}&times;{qp(A[0])} + {q_(m)}&times;{qp(B[0])})/({q_(m)} + {q_(n)}) = {q_(n * A[0] + m * B[0])}/{q_(den)} = {HL(q_(px))}")
            steps.append(f"y = ({q_(n)}&times;{qp(A[1])} + {q_(m)}&times;{qp(B[1])})/({q_(m)} + {q_(n)}) = {q_(n * A[1] + m * B[1])}/{q_(den)} = {HL(q_(py))}")
            if m == n:
                steps.append("<i>Since m = n, P is the <b>midpoint</b> of AB.</i>")
        else:
            if m == n:
                raise UErr("External division in the ratio 1:1 is impossible (the point would be at infinity). Use m and n different.")
            steps.append(f"<b>P divides AB externally in the ratio {q_(m)} : {q_(n)}.</b> P lies on the line AB <i>outside</i> the segment (beyond B if m &gt; n, beyond A if m &lt; n), with AP : PB = {q_(m)} : {q_(n)}.")
            steps.append("<b>Section formula (external):</b> P = ( (m x<sub>2</sub> &minus; n x<sub>1</sub>)/(m &minus; n) , (m y<sub>2</sub> &minus; n y<sub>1</sub>)/(m &minus; n) ). (It is the internal formula with n replaced by &minus;n.)")
            den = m - n
            px = (m * B[0] - n * A[0]) / den
            py = (m * B[1] - n * A[1]) / den
            steps.append(f"x = ({q_(m)}&times;{qp(B[0])} &minus; {q_(n)}&times;{qp(A[0])})/({q_(m)} &minus; {q_(n)}) = {q_(m * B[0] - n * A[0])}/{q_(den)} = {HL(q_(px))}")
            steps.append(f"y = ({q_(m)}&times;{qp(B[1])} &minus; {q_(n)}&times;{qp(A[1])})/({q_(m)} &minus; {q_(n)}) = {q_(m * B[1] - n * A[1])}/{q_(den)} = {HL(q_(py))}")
        Pp = (px, py)
        steps.append(f"<b>P = {HL(P_(Pp))}</b>")
        ratio_check = ""
        items.append(("pt", Pp, "P" + P_(Pp), GREEN))
        if mode == "ext":
            items[0] = ("seg", A, B, BLUE, "-")
            items.append(("seg", B if m > n else A, Pp, GREEN, "--"))
        res = f"<b>P = {P_(Pp)}</b>"
        bx = box_from([A, B, Pp, (0, 0)])
    elif mode == "find":
        Pp = one_pt(d.get("p"), "Point P")
        steps.append(f"<b>Find the ratio in which P{P_(Pp)} divides AB</b> where A{P_(A)}, B{P_(B)}.")
        steps.append("<b>Idea:</b> let the ratio AP : PB = m : n = k : 1. The section formula gives x = (x<sub>1</sub> + k x<sub>2</sub>)/(1 + k). Solve for k.")
        # (x - x1) = k (x2 - x)
        if A[0] != B[0]:
            num_, den_ = Pp[0] - A[0], B[0] - Pp[0]
            how = "x"
        else:
            num_, den_ = Pp[1] - A[1], B[1] - Pp[1]
            how = "y"
        if how == "x":
            steps.append(f"Using x: {q_(Pp[0])}(1 + k) = {q_(A[0])} + {q_(B[0])}k &rArr; {q_(Pp[0])} + {q_(Pp[0])}k = {q_(A[0])} + {q_(B[0])}k &rArr; k({q_(Pp[0] - B[0])}) = {q_(A[0] - Pp[0])} &rArr; k = ({q_(Pp[0])} &minus; {qp(A[0])})/({qp(B[0])} &minus; {qp(Pp[0])})")
        if den_ == 0:
            raise UErr("P is the same as B in the x (or y) direction in a way that makes the ratio undefined; check that P lies on the line AB.")
        k = num_ / den_
        # collinearity check
        cross = (B[0] - A[0]) * (Pp[1] - A[1]) - (B[1] - A[1]) * (Pp[0] - A[0])
        if cross != 0:
            raise UErr("P is not on the line AB, so it does not divide AB in any ratio. Check the points.")
        steps.append(f"k = {q_(num_)}/{q_(den_)} = {HL(q_(k))}")
        if k == 0:
            raise UErr("P is the same point as A.")
        L = k.denominator
        mm, nn = k.numerator, k.denominator
        kind = "internal" if k > 0 else "external"
        steps.append(f"AP : PB = {q_(k)} : 1 = {HL(str(abs(mm)) + ' : ' + str(nn))}. " + ("k is positive, so the division is <b>internal</b> (P is between A and B)." if k > 0 else "k is negative, so the division is <b>external</b> (P is outside AB); the ratio is " + str(abs(mm)) + " : " + str(nn) + " externally."))
        items.append(("pt", Pp, "P" + P_(Pp), GREEN))
        res = f"<b>AP : PB = {abs(mm)} : {nn} ({kind})</b>"
        bx = box_from([A, B, Pp, (0, 0)])
    else:
        steps.append(f"<b>Midpoint and distance of A{P_(A)} and B{P_(B)}.</b>")
        mid = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)
        steps.append(f"Midpoint = ((x<sub>1</sub>+x<sub>2</sub>)/2, (y<sub>1</sub>+y<sub>2</sub>)/2) = (({q_(A[0])}+{qp(B[0])})/2, ({q_(A[1])}+{qp(B[1])})/2) = {HL(P_(mid))}")
        d2 = (B[0] - A[0]) ** 2 + (B[1] - A[1]) ** 2
        sq, v, ex = surd(d2)
        steps.append(f"Distance = &radic;[(x<sub>2</sub>&minus;x<sub>1</sub>)<sup>2</sup> + (y<sub>2</sub>&minus;y<sub>1</sub>)<sup>2</sup>] = &radic;[({qp(B[0])}&minus;{qp(A[0])})<sup>2</sup> + ({qp(B[1])}&minus;{qp(A[1])})<sup>2</sup>] = &radic;{q_(d2)} = {HL(sq)}{'' if ex else ' &asymp; ' + decim(v)}")
        if B[0] != A[0]:
            steps.append(f"Gradient = ({qp(B[1])}&minus;{qp(A[1])})/({qp(B[0])}&minus;{qp(A[0])}) = {HL(q_((B[1] - A[1]) / (B[0] - A[0])))}")
        else:
            steps.append("Gradient: undefined (vertical line).")
        items.append(("pt", mid, "M" + P_(mid), GREEN))
        res = f"<b>Midpoint {P_(mid)}, distance {sq}</b>"
        bx = box_from([A, B, mid, (0, 0)])
    return _out(steps, res, scene(bx, items))


# ======================================================================= area / collinearity (coordinates may contain one letter)
def parse_pts_mp(text, lo=3, hi=8):
    t = (text or "").replace("−", "-")
    pairs = re.findall(PTS_RE, t)
    if len(pairs) < lo or len(pairs) > hi:
        raise UErr(f"Give between {lo} and {hi} points, like (1, 2), (3, 7), (6, 2).")
    left = re.sub(PTS_RE, "", t)
    if re.search(r"[^\s,;]", left):
        raise UErr("I could not read all of that. Write each point as (x, y), separated by commas.")
    pts = [(parse_poly(a), parse_poly(b)) for a, b in pairs]
    letters = set()
    for p in pts:
        for c in p:
            if c.total_deg() > 1:
                raise UErr("Use the unknown letter (like k) only to the first power in a coordinate.")
            letters |= set(c.vars())
    if len(letters) > 1:
        raise UErr("Use at most one unknown letter (like k).")
    return pts, (next(iter(letters)) if letters else None)


@wrap
def area(d):
    from t_algebra2 import _solve_quad_in_k
    pts, k = parse_pts_mp(d.get("pts"))
    n = len(pts)
    names = "ABCDEFGH"[:n]
    steps = []
    if k is None:
        fp = [(c[0].const_value(), c[1].const_value()) for c in pts]
        steps.append("<b>Area of a polygon by the shoelace method.</b> List the corners <i>in order</i> (clockwise or anticlockwise), repeat the first corner at the bottom, multiply downwards-right and downwards-left, subtract, and halve.")
        tbl = "<table class='stat-table'><tr><th>Corner</th><th>x</th><th>y</th></tr>"
        for nm_, p in zip(names + names[0], fp + [fp[0]]):
            tbl += f"<tr><td>{nm_}</td><td>{q_(p[0])}</td><td>{q_(p[1])}</td></tr>"
        tbl += "</table>"
        steps.append(tbl)
        s1 = sum(fp[i][0] * fp[(i + 1) % n][1] for i in range(n))
        s2 = sum(fp[i][1] * fp[(i + 1) % n][0] for i in range(n))
        t1 = " + ".join(f"({q_(fp[i][0])})({q_(fp[(i + 1) % n][1])})" for i in range(n))
        t2 = " + ".join(f"({q_(fp[i][1])})({q_(fp[(i + 1) % n][0])})" for i in range(n))
        steps.append(f"<b>Downwards (x &times; next y):</b> {t1} = {q_(s1)}<br><b>Upwards (y &times; next x):</b> {t2} = {q_(s2)}")
        ar = abs(s1 - s2) / 2
        steps.append(f"<b>Area</b> = &frac12; |{q_(s1)} &minus; {qp(s2)}| = &frac12; &times; {q_(abs(s1 - s2))} = {HL(q_(ar) + ' square units')}")
        res = f"<b>Area = {q_(ar)} square units</b>"
        if n == 3:
            if ar == 0:
                steps.append(f"<b>The area is 0, so the three points are <u>collinear</u></b> (they lie on one straight line).")
                res += "<br><b>Collinear</b>"
            else:
                steps.append("The area is not 0, so the points are <b>not collinear</b> (they form a real triangle).")
            cx, cy = sum(p[0] for p in fp) / 3, sum(p[1] for p in fp) / 3
            steps.append(f"<b>Centroid</b> (where the medians meet) = ((x<sub>1</sub>+x<sub>2</sub>+x<sub>3</sub>)/3, (y<sub>1</sub>+y<sub>2</sub>+y<sub>3</sub>)/3) = {HL(P_((cx, cy)))}")
            for (i, j) in ((0, 1), (1, 2), (0, 2)):
                dd = (fp[i][0] - fp[j][0]) ** 2 + (fp[i][1] - fp[j][1]) ** 2
                sq, v, ex = surd(dd)
                steps.append(f"Length {names[i]}{names[j]} = &radic;{q_(dd)} = {sq}{'' if ex else ' &asymp; ' + decim(v)}")
        items = [("poly", fp, BLUE)] + [("pt", p, names[i] + P_(p), RED) for i, p in enumerate(fp)]
        if n == 3 and ar != 0:
            items.append(("pt", (cx, cy), "G" + P_((cx, cy)), GREEN))
        return _out(steps, res, scene(box_from(fp, [(0, 0)]), items))
    # with an unknown letter
    steps.append(f"<b>The points contain the unknown {HL(k)}.</b> Use the shoelace formula, with x and y as letters we cannot calculate yet:")
    s1 = MP.const(0)
    s2 = MP.const(0)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        s1 = s1 + a[0] * b[1]
        s2 = s2 + a[1] * b[0]
    diff = s1 - s2
    steps.append(f"Downwards: {s1.text()}; upwards: {s2.text()}. So 2 &times; (signed area) = {HL(diff.text())}")
    given = (d.get("area") or "").strip()
    if not given:
        if n != 3:
            raise UErr("The collinearity test needs exactly 3 points.")
        steps.append("<b>Collinear</b> means the area of the 'triangle' is zero. So set it equal to 0:")
        target = [Fraction(0)]
        steps.append(f"{diff.text()} = 0")
    else:
        a0 = Fraction(num(given, "Area"))
        if a0 <= 0:
            raise UErr("The area must be bigger than 0.")
        steps.append(f"The area is {q_(a0)}, and area = &frac12;|{diff.text()}|, so {diff.text()} = {q_(2 * a0)} <b>or</b> {diff.text()} = {MINUS}{q_(2 * a0)} (because of the absolute value).")
        target = [2 * a0, -2 * a0]
    sols = []
    for t in target:
        e = diff - MP.const(t)
        if e.deg_in(k) > 2:
            raise UErr("The equation in " + k + " is too hard for this tool.")
        cs = [e.coeff_in(k, i).const_value() for i in range(3)]
        if cs[2] == 0 and cs[1] == 0:
            continue
        for v, tx in _solve_quad_in_k(cs[2], cs[1], cs[0]):
            sols.append(tx)
    sols = list(dict.fromkeys(sols))
    steps.append(f"Solve: {HL(' or '.join(k + ' = ' + s for s in sols) if sols else 'no real solution')}")
    return _ok(steps, "<b>" + (" or ".join(k + " = " + s for s in sols) if sols else "No real value") + "</b>")


# ======================================================================= circles
def _eq_circle(txt):
    s = str(txt or "").replace("−", "-").strip()
    if not s:
        raise UErr("Type the equation of the circle, for example x^2 + y^2 - 6x + 4y - 12 = 0")
    if "=" in s:
        l, r = s.split("=")
        G = parse_poly(l, allow_vars=("x", "y")) - parse_poly(r or "0", allow_vars=("x", "y"))
    else:
        G = parse_poly(s, allow_vars=("x", "y"))
    a, b = G.coeff_in("x", 2).coeff_in("y", 0).const_value(), G.coeff_in("y", 2).coeff_in("x", 0).const_value()
    xy = G.coeff_in("x", 1).coeff_in("y", 1).const_value()
    if a == 0 or a != b or xy != 0 or G.total_deg() != 2:
        raise UErr("That is not a circle: a circle has x² and y² with the same coefficient and no xy term.")
    D = G.coeff_in("x", 1).coeff_in("y", 0).const_value() / a
    E = G.coeff_in("y", 1).coeff_in("x", 0).const_value() / a
    F = G.coeff_in("x", 0).coeff_in("y", 0).const_value() / a
    return D, E, F


def circ_text(D, E, F):
    return MP({(("x", 2),): Fraction(1), (("y", 2),): Fraction(1), (("x", 1),): Fraction(D), (("y", 1),): Fraction(E), (): Fraction(F)}).text() + " = 0"


def centre_form(h, k, r2):
    def part(v, c):
        return f"{v}<sup>2</sup>" if c == 0 else (f"({v} {MINUS} {q_(c)})<sup>2</sup>" if c > 0 else f"({v} + {q_(-c)})<sup>2</sup>")
    return f"{part('x', h)} + {part('y', k)} = {q_(r2)}"


def read_radius(txt):
    s = str(txt or "").strip().lower().replace(" ", "").replace("√", "sqrt")
    m = re.fullmatch(r"(\d*\.?\d*)\*?sqrt\(?(\d+)\)?", s)
    if m and m.group(2):
        c = Fraction(m.group(1)) if m.group(1) else Fraction(1)
        return c * c * Fraction(m.group(2))
    r = Fraction(num(s, "Radius"))
    if r <= 0:
        raise UErr("The radius must be bigger than 0.")
    return r * r


def _circle_pic(h, k, r2, extra=(), lines=()):
    r = math.sqrt(float(r2))
    items = [("circle", h, k, r, BLUE), ("pt", (h, k), "C" + P_((h, k)), RED)]
    items += [("line", *L, GREEN, lab) for L, lab in lines]
    items += list(extra)
    bx = [(float(h) - r, float(k) - r), (float(h) + r, float(k) + r), (0.0, 0.0)]
    return scene(bx, items)


@wrap
def circle(d):
    mode = d.get("mode", "cr")
    steps = []
    if mode == "cr":
        h, k = one_pt(d.get("c"), "Centre")
        r2 = read_radius(d.get("r"))
        sq, v, ex = surd(r2)
        steps.append(f"<b>Circle with centre ({q_(h)}, {q_(k)}) and radius {sq}.</b>")
        steps.append(f"<b>Standard form:</b> (x &minus; h)<sup>2</sup> + (y &minus; k)<sup>2</sup> = r<sup>2</sup>. With h = {q_(h)}, k = {q_(k)}, r<sup>2</sup> = {q_(r2)}: {HL(centre_form(h, k, r2))}")
        D, E, F = -2 * h, -2 * k, h * h + k * k - r2
        steps.append(f"<b>Expand the brackets</b> to get the general form x<sup>2</sup> + y<sup>2</sup> + 2gx + 2fy + c = 0: x<sup>2</sup> {MINUS if h > 0 else '+'} {q_(abs(2 * h))}x + {q_(h * h)} + y<sup>2</sup> ... then move r<sup>2</sup> across.")
        steps.append(f"<b>General form:</b> {HL(circ_text(D, E, F))}")
        res = f"<b>{circ_text(D, E, F)}</b>"
    else:
        D, E, F = _eq_circle(d.get("eq"))
        h, k = -D / 2, -E / 2
        r2 = h * h + k * k - F
        steps.append(f"<b>Circle:</b> {HL(circ_text(D, E, F))}. Find the centre and radius by <b>completing the square</b> (or compare with x<sup>2</sup> + y<sup>2</sup> + 2gx + 2fy + c = 0, centre (&minus;g, &minus;f)).")
        steps.append(f"<b>Group x and y terms:</b> (x<sup>2</sup> {'+' if D >= 0 else MINUS} {q_(abs(D))}x) + (y<sup>2</sup> {'+' if E >= 0 else MINUS} {q_(abs(E))}y) = {q_(-F)}")
        steps.append(f"<b>Complete the square:</b> add (half of the x-number)<sup>2</sup> = ({q_(D / 2)})<sup>2</sup> = {q_(D * D / 4)} and (half of the y-number)<sup>2</sup> = ({q_(E / 2)})<sup>2</sup> = {q_(E * E / 4)} to <b>both sides</b>:")
        steps.append(f"(x {'+' if D >= 0 else MINUS} {q_(abs(D / 2))})<sup>2</sup> + (y {'+' if E >= 0 else MINUS} {q_(abs(E / 2))})<sup>2</sup> = {q_(-F)} + {q_(D * D / 4)} + {q_(E * E / 4)} = {HL(q_(r2))}")
        if r2 <= 0:
            steps.append(f"The right side is {q_(r2)}, which is not positive, so this is {'a single point' if r2 == 0 else 'not a real circle (no points)'}.")
            return _ok(steps, f"<b>{'Single point' if r2 == 0 else 'Not a real circle'}</b>")
        sq, v, ex = surd(r2)
        steps.append(f"<b>Centre = ({q_(h)}, {q_(k)}),&nbsp; radius = &radic;{q_(r2)} = {HL(sq)}</b>{'' if ex else ' &asymp; ' + decim(v)}")
        res = f"<b>Centre ({q_(h)}, {q_(k)}), radius {sq}</b>"
    return _out(steps, res, _circle_pic(h, k, r2))


def solve3(M, v):
    """Gaussian elimination Fractions"""
    n = len(M)
    A = [row[:] + [v[i]] for i, row in enumerate(M)]
    for c in range(n):
        p = next((r for r in range(c, n) if A[r][c] != 0), None)
        if p is None:
            return None
        A[c], A[p] = A[p], A[c]
        A[c] = [x / A[c][c] for x in A[c]]
        for r in range(n):
            if r != c and A[r][c] != 0:
                f = A[r][c]
                A[r] = [x - f * y for x, y in zip(A[r], A[c])]
    return [A[i][n] for i in range(n)]


@wrap
def circle3(d):
    pts = parse_pts(d.get("pts"), "Points", 3, 3)
    names = "ABC"
    steps = [f"<b>Circle through A{P_(pts[0])}, B{P_(pts[1])}, C{P_(pts[2])}.</b> Use the general form x<sup>2</sup> + y<sup>2</sup> + Dx + Ey + F = 0. Each point must satisfy it, which gives three equations in D, E, F."]
    rows, rhs = [], []
    for nm_, (x, y) in zip(names, pts):
        steps.append(f"Point {nm_}: {q_(x * x)} + {q_(y * y)} + D({qp(x)}) + E({qp(y)}) + F = 0 &rArr; {HL(q_(x) + 'D + ' + q_(y) + 'E + F = ' + q_(-(x * x + y * y)))}".replace("+ " + MINUS, "+ " + MINUS))
        rows.append([x, y, Fraction(1)])
        rhs.append(-(x * x + y * y))
    sol = solve3(rows, rhs)
    if sol is None:
        raise UErr("These three points lie on a straight line (they are collinear), so no circle passes through all of them.")
    steps.append("<b>Solve the three equations</b> (subtract equations to remove F, then solve the two that remain for D and E, then find F).")
    D, E, F = sol
    steps.append(f"D = {HL(q_(D))}, E = {HL(q_(E))}, F = {HL(q_(F))}")
    steps.append(f"<b>Equation:</b> {HL(circ_text(D, E, F))}")
    h, k = -D / 2, -E / 2
    r2 = h * h + k * k - F
    sq, v, ex = surd(r2)
    steps.append(f"<b>Centre</b> = (&minus;D/2, &minus;E/2) = ({q_(h)}, {q_(k)}); <b>radius</b> = &radic;(h<sup>2</sup> + k<sup>2</sup> &minus; F) = &radic;{q_(r2)} = {sq}{'' if ex else ' &asymp; ' + decim(v)}")
    steps.append("<b>Check:</b> distance from the centre to each point = radius: " + ", ".join(f"{nm_}: {q_((p[0] - h) ** 2 + (p[1] - k) ** 2)} = {q_(r2)} &check;" for nm_, p in zip(names, pts)))
    extra = [("pt", p, nm_ + P_(p), ORANGE) for nm_, p in zip(names, pts)]
    return _out(steps, f"<b>{circ_text(D, E, F)}</b><br>Centre ({q_(h)}, {q_(k)}), radius {sq}", _circle_pic(h, k, r2, extra))


@wrap
def circ_line(d):
    mode = d.get("mode", "tan")
    D, E, F = _eq_circle(d.get("eq"))
    h, k = -D / 2, -E / 2
    r2 = h * h + k * k - F
    if r2 <= 0:
        raise UErr("That is not a real circle.")
    steps = [f"<b>Circle:</b> {HL(circ_text(D, E, F))}: centre ({q_(h)}, {q_(k)}), radius<sup>2</sup> = {q_(r2)}."]
    if mode == "tan":
        P = one_pt(d.get("p"), "Point")
        val = P[0] ** 2 + P[1] ** 2 + D * P[0] + E * P[1] + F
        steps.append(f"<b>Is {P_(P)} on the circle?</b> Put it in: {q_(P[0] ** 2)} + {q_(P[1] ** 2)} + ({q_(D)})({qp(P[0])}) + ({q_(E)})({qp(P[1])}) + ({q_(F)}) = {q_(val)}.")
        if val != 0:
            raise UErr(f"The point is not on the circle (the left side should be 0 but it is {q_(val)}). A tangent at a point needs the point to be on the circle.")
        steps.append("It equals 0, so the point is on the circle &check;.")
        C = (h, k)
        steps.append("<b>Key fact:</b> the tangent is <b>perpendicular to the radius</b> at the point of contact.")
        if P[0] == h:
            m_r = None
        else:
            m_r = (P[1] - k) / (P[0] - h)
        if m_r is None:
            mt = Fraction(0)
            steps.append("The radius is vertical, so the tangent is horizontal (gradient 0).")
        elif m_r == 0:
            mt = None
            steps.append("The radius is horizontal, so the tangent is vertical.")
        else:
            steps.append(f"<b>Gradient of the radius</b> (centre to point) = ({qp(P[1])} &minus; {qp(k)})/({qp(P[0])} &minus; {qp(h)}) = {q_(m_r)}")
            mt = -1 / m_r
            steps.append(f"<b>Gradient of the tangent</b> = &minus;1/({q_(m_r)}) = {HL(q_(mt))}")
        tA, tB, tC = _through(P, mt, steps)
        mn = (-1 / mt) if mt not in (None, 0) else (None if mt == 0 else Fraction(0))
        t1, t2 = line_forms(tA, tB, tC)
        steps.append(f"<b>Tangent:</b> {HL(t1)} &nbsp;or&nbsp; {HL(t2)}")
        steps.append("<b>The normal</b> is the line through the point and the centre (along the radius).")
        nA, nB, nC = _through(P, m_r, steps)
        n1, n2 = line_forms(nA, nB, nC)
        steps.append(f"<b>Normal:</b> {HL(n1)}")
        img = _circle_pic(h, k, r2, [("pt", P, "P" + P_(P), ORANGE)], [((tA, tB, tC), "tangent")])
        return _out(steps, f"<b>Tangent: {t1}</b><br>{t2}<br>Normal: {n1}", img)
    L = parse_line(d.get("l"), "Line")
    A, B, C0 = L
    steps.append(f"<b>Line:</b> {HL(gen_text(*L))}. Find where it meets the circle: substitute the line into the circle equation.")
    if B != 0:
        m = -A / B
        c = -C0 / B
        steps.append(f"From the line, y = {q_(m)}x + ({q_(c)}). Put this in x<sup>2</sup> + y<sup>2</sup> + ({q_(D)})x + ({q_(E)})y + ({q_(F)}) = 0:")
        # x^2 + (mx+c)^2 + Dx + E(mx+c) + F
        qa = 1 + m * m
        qb = 2 * m * c + D + E * m
        qc = c * c + E * c + F
        steps.append(f"x<sup>2</sup> + ({q_(m)}x + {qp(c)})<sup>2</sup> + ... &rArr; {HL(MP({(('x', 2),): qa, (('x', 1),): qb, (): qc}).text() + ' = 0')}")
        var = "x"
    else:
        xv = -C0 / A
        steps.append(f"The line is x = {q_(xv)}. Put x = {q_(xv)} in the circle: y<sup>2</sup> + ({q_(E)})y + ({q_(xv * xv + D * xv + F)}) = 0")
        qa, qb, qc = Fraction(1), E, xv * xv + D * xv + F
        var = "y"
    disc = qb * qb - 4 * qa * qc
    steps.append(f"<b>Discriminant</b> b<sup>2</sup> &minus; 4ac = ({q_(qb)})<sup>2</sup> &minus; 4({q_(qa)})({q_(qc)}) = {q_(disc)}")
    pts_hit = []
    if disc < 0:
        steps.append("The discriminant is negative: the line <b>does not meet</b> the circle.")
        res = "<b>The line misses the circle</b>"
    else:
        sq, v, ex = surd(disc)
        if disc == 0:
            steps.append(f"The discriminant is 0: the line <b>touches the circle at exactly one point</b> &ndash; it is a <b>tangent</b>.")
        else:
            steps.append("The discriminant is positive: the line cuts the circle at <b>two points</b>.")
        vals = []
        for sgn in ((1,) if disc == 0 else (1, -1)):
            if ex:
                vals.append((-qb + sgn * Fraction(sq.replace(MINUS, "-")) if False else None))
        rts = []
        for sgn in ((1,) if disc == 0 else (-1, 1)):
            rts.append((-float(qb) + sgn * math.sqrt(float(disc))) / (2 * float(qa)))
        if ex:
            r_ = surd(disc)[1]
            exact = [(-qb - Fraction(r_).limit_denominator(10 ** 6)) / (2 * qa), (-qb + Fraction(r_).limit_denominator(10 ** 6)) / (2 * qa)] if disc != 0 else [-qb / (2 * qa)]
            steps.append(f"Solve the quadratic: {var} = {' or '.join(q_(e) for e in exact)}")
            for e in exact:
                if var == "x":
                    pts_hit.append((e, m * e + c))
                else:
                    pts_hit.append((xv, e))
        else:
            steps.append(f"Solve with the formula: {var} = (&minus;({q_(qb)}) &plusmn; &radic;{q_(disc)})/(2&times;{q_(qa)}) &asymp; {', '.join(decim(r) for r in rts)}")
            for e in rts:
                pts_hit.append((e, float(m) * e + float(c)) if var == "x" else (float(xv), e))
        if var == "x" and ex:
            steps.append("Find y from the line equation for each x: " + ", ".join(P_(p) for p in pts_hit))
        res = "<b>Meets at " + " and ".join("(" + (q_(p[0]) if isinstance(p[0], Fraction) else decim(p[0])) + ", " + (q_(p[1]) if isinstance(p[1], Fraction) else decim(p[1])) + ")" for p in pts_hit) + "</b>"
    extra = [("pt", p, "", ORANGE) for p in pts_hit]
    return _out(steps, res, _circle_pic(h, k, r2, extra, [(L, "line")]))


# ======================================================================= distance point to line
@wrap
def dist(d):
    mode = d.get("mode", "pt")
    steps = []
    if mode == "pt":
        P = one_pt(d.get("p"), "Point")
        L = parse_line(d.get("l"), "Line")
        A, B, C = L
        steps.append(f"<b>Shortest distance from {P_(P)} to the line {HL(gen_text(*L))}.</b> The shortest distance is along the <b>perpendicular</b> from the point to the line.")
        steps.append("<b>Formula:</b> for the line Ax + By + C = 0 and the point (x<sub>1</sub>, y<sub>1</sub>): &nbsp; d = |A x<sub>1</sub> + B y<sub>1</sub> + C| / &radic;(A<sup>2</sup> + B<sup>2</sup>)")
        top = A * P[0] + B * P[1] + C
        bot2 = A * A + B * B
        steps.append(f"<b>Top:</b> |{q_(A)}({qp(P[0])}) + {q_(B)}({qp(P[1])}) + {qp(C)}| = |{q_(top)}| = {q_(abs(top))}")
        bs, bv, bex = surd(bot2)
        steps.append(f"<b>Bottom:</b> &radic;({q_(A)}<sup>2</sup> + {q_(B)}<sup>2</sup>) = &radic;{q_(bot2)} = {bs}")
        dv = abs(top) / bv
        if bex:
            exact = q_(abs(top) / Fraction(bs.replace(MINUS, "-")))
        else:
            exact = None
        # rationalised exact text
        if bex:
            ans = exact
        else:
            ans = f"{q_(abs(top))}/&radic;{q_(bot2)}"
            rat, v, ex = surd(Fraction(top * top, 1) / bot2)
            ans = rat
        steps.append(f"<b>Distance</b> = {q_(abs(top))}/{bs} = {HL(ans)}" + ("" if bex else f" &asymp; {HL(decim(dv, 3))} units"))
        # foot of perpendicular
        t = top / bot2
        foot = (P[0] - A * t, P[1] - B * t)
        steps.append(f"<b>Foot of the perpendicular</b> (the closest point on the line) = (x<sub>1</sub> &minus; A&middot;t, y<sub>1</sub> &minus; B&middot;t) where t = ({q_(top)})/{q_(bot2)}: {HL(P_(foot))}")
        items = [("line", A, B, C, BLUE, "line"), ("seg", P, foot, GREEN, "--"), ("pt", P, "P" + P_(P), RED), ("pt", foot, "F" + P_(foot), ORANGE)]
        return _out(steps, f"<b>Distance = {ans}{'' if bex else ' ≈ ' + decim(dv, 3)}</b>", scene(box_from([P, foot, (0, 0)]), items))
    L1, L2 = parse_line(d.get("l"), "Line 1"), parse_line(d.get("l2"), "Line 2")
    steps.append(f"<b>Distance between the parallel lines</b> {HL(gen_text(*L1))} and {HL(gen_text(*L2))}.")
    if L1[0] * L2[1] != L1[1] * L2[0]:
        raise UErr("These lines are not parallel (their gradients differ), so they meet and the distance is 0.")
    A, B, C1 = L1
    # scale L2 to the same A,B
    f = (A / L2[0]) if L2[0] != 0 else (B / L2[1])
    C2 = L2[2] * f
    steps.append(f"Make the x and y numbers the same in both: line 1: {q_(A)}x + {q_(B)}y + {q_(C1)} = 0; line 2: {q_(A)}x + {q_(B)}y + {q_(C2)} = 0.")
    steps.append("<b>Formula:</b> d = |C<sub>1</sub> &minus; C<sub>2</sub>| / &radic;(A<sup>2</sup> + B<sup>2</sup>)")
    bot2 = A * A + B * B
    top = abs(C1 - C2)
    bs, bv, bex = surd(bot2)
    rat, v, ex = surd(top * top / bot2)
    steps.append(f"d = |{q_(C1)} &minus; ({q_(C2)})|/&radic;{q_(bot2)} = {q_(top)}/{bs} = {HL(rat)}" + ("" if ex else f" &asymp; {decim(v, 3)} units"))
    items = [("line", *L1, BLUE, "L1"), ("line", A, B, C2, RED, "L2")]
    bx = [(0.0, 0.0), (5.0, 5.0)]
    for L in (L1, (A, B, C2)):
        if L[1] != 0:
            bx.append((0.0, float(-L[2] / L[1])))
    return _out(steps, f"<b>Distance = {rat}{'' if ex else ' ≈ ' + decim(v, 3)}</b>", scene(bx, items))


# ======================================================================= table & graph of a straight line
@wrap
def line_table(d):
    from frac_numeric import table
    A, B, C = parse_line(d.get("eq"), "Equation")
    if B == 0:
        raise UErr("This is a vertical line (x = a number), so y does not depend on x and a table of values is not possible. A table needs y = mx + c.")
    m, c = -A / B, -C / B
    lo = int(Fraction(num(d.get("x0"), "x from")))
    hi = int(Fraction(num(d.get("x1"), "x to")))
    if lo >= hi:
        raise UErr("'x from' must be smaller than 'x to'.")
    if hi - lo > 14:
        raise UErr("Please use at most 15 values of x (for example &minus;4 to 6).")
    f1, f2 = line_forms(A, B, C)
    steps = [f"<b>Table of values</b> for the straight line {HL(f1)}. Gradient m = {HL(q_(m))} (how much y goes up when x goes up by 1) and y-intercept c = {HL(q_(c))} (where the line crosses the y-axis).",
             "<b>The table has one column for each term</b> of the equation (the x term and the number), then a last column <b>y</b> that adds them up."]
    parts = [(m, 1)] + ([(c, 0)] if c != 0 else [])
    parts = [(co, pw) for co, pw in parts if co != 0] or [(Fraction(0), 0)]

    def lab(co, pw, first):
        mag = abs(co)
        if pw and mag.denominator != 1:
            body = ("" if mag.numerator == 1 else str(mag.numerator)) + f"x/{mag.denominator}"
        else:
            body = (("" if (mag == 1 and pw) else q_(mag)) + ("x" if pw else ""))
        return (MINUS + body) if co < 0 else (body if first else "+ " + body)
    head = ["x"] + [lab(co, pw, i == 0) for i, (co, pw) in enumerate(parts)] + ["y"]
    rows, pts = [], []
    for x in range(lo, hi + 1):
        vals = [co * (x ** pw) for co, pw in parts]
        y = sum(vals)
        rows.append([str(x).replace("-", MINUS)] + [q_(v) for v in vals] + [f"<b>{q_(y)}</b>"])
        pts.append((Fraction(x), y))
    x0 = lo
    v0 = [co * (x0 ** pw) for co, pw in parts]
    ex = " ; ".join((f"{lab(co, pw, True)} = {q_(co)} &times; ({str(x0).replace('-', MINUS)}) = {q_(v)}" if pw else f"{q_(co)} = {q_(v)}") for (co, pw), v in zip(parts, v0))
    steps.append(f"<b>Worked example, x = {str(x0).replace('-', MINUS)}:</b> {ex}. Add them: y = {' + '.join('(' + q_(v) + ')' if v < 0 else q_(v) for v in v0)} = <b>{q_(sum(v0))}</b>")
    steps.append(table(rows, head))
    steps.append("<b>Plot:</b> each pair (x, y) is a point. Because the equation is <b>linear</b>, all the points lie on <b>one straight line</b>: join them with a ruler and extend the line a little beyond the first and last points.")
    xi = -c / m if m != 0 else None
    if xi is not None:
        steps.append(f"<b>Where the line crosses the axes:</b> y-intercept (0, {q_(c)}); x-intercept: put y = 0, so x = &minus;c/m = {q_(xi)}, the point ({q_(xi)}, 0).")
    items = [("line", A, B, C, BLUE, "")] + [("pt", p, "", RED) for p in pts]
    items.append(("pt", (Fraction(0), c), "y-int (0, " + q_(c) + ")", GREEN))
    if xi is not None:
        items.append(("pt", (xi, Fraction(0)), "x-int (" + q_(xi) + ", 0)", GREEN))
    # gradient triangle: run 1, rise m
    tri = [(Fraction(0), c), (Fraction(1), c), (Fraction(1), c + m)]
    items += [("seg", tri[0], tri[1], ORANGE, "--"), ("seg", tri[1], tri[2], ORANGE, "--")]
    bx = box_from([(lo, min(float(p[1]) for p in pts)), (hi, max(float(p[1]) for p in pts)), (0, 0)])
    steps.append(f"<b>The dashed orange triangle shows the gradient:</b> move 1 across (run) and {q_(m)} {'up' if m > 0 else ('down' if m < 0 else '(flat)')} (rise).")
    return _out(steps, f"<b>{f1}</b><br>Gradient {q_(m)}, y-intercept {q_(c)}", scene(bx, items))


# ======================================================================= spec
SPEC = {
    "title": "Coordinate Geometry",
    "intro": "Straight lines and circles on the x-y plane, with a labelled graph every time. Type points as <b>(2, 3)</b> and lines like <b>y = 2x + 3</b> or <b>3x - 2y = 6</b>. Fractions such as 2/3 are fine.",
    "tabs": [
        {"id": "le", "label": "Equation of a line", "title": "Find the equation of a straight line", "endpoint": "line_eq",
         "fields": [select("mode", "I know", [("two", "two points on the line"), ("pg", "a point and the gradient"), ("ic", "the two intercepts")], wide=True),
                    field("p1", "Point 1", "(1, 2)", show_if={"mode": ["two", "pg"]}), field("p2", "Point 2", "(4, 8)", show_if={"mode": "two"}),
                    field("m", "Gradient (or 'vertical')", "-2/3", show_if={"mode": "pg"}),
                    field("a", "x-intercept", "4", show_if={"mode": "ic"}), field("b", "y-intercept", "-3", show_if={"mode": "ic"})], "button": "Find equation"},
        {"id": "lt", "label": "Table & graph of a line", "title": "Table of values and graph of a straight line", "endpoint": "line_table",
         "hint": "Type the line like <b>y = 2x + 3</b>, <b>y = -x/2 + 1</b> or <b>3x + 2y = 6</b>. The table has a column for each term, then y.",
         "fields": [field("eq", "Equation of the line", "y = 2x + 3", wide=True, half=False), field("x0", "x from", "-3"), field("x1", "x to", "3")], "button": "Make table and graph"},
        {"id": "pp", "label": "Parallel, perpendicular & meeting", "title": "Parallel and perpendicular lines, bisectors, intersections and angles", "endpoint": "parperp",
         "fields": [select("mode", "What do you want", [("par", "Line parallel to a given line, through a point"), ("perp", "Line perpendicular to a given line, through a point"), ("bis", "Perpendicular bisector of two points"), ("meet", "Where two lines meet"), ("angle", "Angle between two lines")], wide=True),
                    field("l1", "Given line", "3x - 2y = 6", wide=True, half=False, show_if={"mode": ["par", "perp", "meet", "angle"]}),
                    field("l2", "Second line", "x + y = 7", wide=True, half=False, show_if={"mode": ["meet", "angle"]}),
                    field("p", "Point to pass through", "(1, 5)", show_if={"mode": ["par", "perp"]}),
                    field("p1", "Point A", "(1, 2)", show_if={"mode": "bis"}), field("p2", "Point B", "(5, 6)", show_if={"mode": "bis"})], "button": "Solve"},
        {"id": "sc", "label": "Section formula", "title": "Dividing a line in a ratio, midpoint and distance", "endpoint": "section",
         "fields": [select("mode", "What do you want", [("int", "Point dividing AB internally in ratio m:n"), ("ext", "Point dividing AB externally in ratio m:n"), ("find", "Find the ratio in which P divides AB"), ("mid", "Midpoint, distance and gradient of AB")], wide=True),
                    field("a", "Point A", "(2, 3)"), field("b", "Point B", "(8, 9)"),
                    field("m", "m", "2", show_if={"mode": ["int", "ext"]}), field("n", "n", "1", show_if={"mode": ["int", "ext"]}),
                    field("p", "Point P", "(4, 5)", show_if={"mode": "find"})], "button": "Calculate"},
        {"id": "ar", "label": "Area & collinearity", "title": "Area of a triangle or polygon, collinear points, centroid", "endpoint": "area",
         "hint": "Give the corners in order. For three points the app also checks if they are on one line and finds the centroid. You may use one unknown letter (k) in a coordinate: leave 'Area' empty to find k for collinear points, or give the area to find k.",
         "fields": [field("pts", "Points", "(1, 2), (5, 3), (3, 8)", wide=True, half=False), field("area", "Given area (only when finding k)", "")], "button": "Calculate"},
        {"id": "ci", "label": "Circle equation", "title": "Equation of a circle and centre/radius", "endpoint": "circle",
         "fields": [select("mode", "I know", [("cr", "the centre and radius"), ("gen", "the equation (find centre and radius)")], wide=True),
                    field("c", "Centre", "(2, -1)", show_if={"mode": "cr"}), field("r", "Radius (e.g. 5 or sqrt(20))", "5", show_if={"mode": "cr"}),
                    field("eq", "Equation", "x^2 + y^2 - 6x + 4y - 12 = 0", wide=True, half=False, show_if={"mode": "gen"})], "button": "Solve"},
        {"id": "c3", "label": "Circle through 3 points", "title": "Circle through three points", "endpoint": "circle3",
         "fields": [field("pts", "Three points", "(0, 0), (4, 0), (0, 2)", wide=True, half=False)], "button": "Find the circle"},
        {"id": "cl", "label": "Tangent & line meets circle", "title": "Tangent at a point, or where a line meets a circle", "endpoint": "circ_line",
         "fields": [field("eq", "Circle equation", "x^2 + y^2 - 6x + 4y - 12 = 0", wide=True, half=False),
                    select("mode", "What do you want", [("tan", "Tangent and normal at a point on the circle"), ("int", "Where a line meets the circle")], wide=True),
                    field("p", "Point on the circle", "(3, 3)", show_if={"mode": "tan"}),
                    field("l", "Line", "y = x - 2", wide=True, half=False, show_if={"mode": "int"})], "button": "Solve"},
        {"id": "di", "label": "Distance to a line", "title": "Distance from a point to a line (or between parallel lines)", "endpoint": "dist",
         "fields": [select("mode", "What do you want", [("pt", "Distance from a point to a line"), ("par", "Distance between two parallel lines")], wide=True),
                    field("p", "Point", "(3, 4)", show_if={"mode": "pt"}),
                    field("l", "Line", "3x - 4y + 5 = 0", wide=True, half=False),
                    field("l2", "Second line (parallel)", "3x - 4y - 10 = 0", wide=True, half=False, show_if={"mode": "par"})], "button": "Find distance"},
    ],
}

topics.register("coordgeo", SPEC, {"line_table": line_table, "line_eq": line_eq, "parperp": parperp, "section": section, "area": area, "circle": circle,
                                   "circle3": circle3, "circ_line": circ_line, "dist": dist})
