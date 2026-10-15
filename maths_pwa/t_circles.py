"""Circle theorems (with diagrams) and mensuration."""
import base64
import io
import math
from fractions import Fraction
import topics
from tcommon import *
from frac_numeric import _ok, _fail

DEG = "&deg;"


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _b64(fig):
    plt = _plt()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def P_(deg, r=1.0):
    return (r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)))


def _fig():
    plt = _plt()
    fig, ax = plt.subplots(figsize=(5.4, 5.4))
    t = [i / 360 * 2 * math.pi for i in range(361)]
    ax.plot([math.cos(a) for a in t], [math.sin(a) for a in t], color="#1e293b", lw=2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.6, 1.6)
    return fig, ax


def seg(ax, p, q, **kw):
    kw.setdefault("color", "#334155")
    kw.setdefault("lw", 1.8)
    ax.plot([p[0], q[0]], [p[1], q[1]], **kw)


def label(ax, p, text, off=1.13, centre=(0, 0), **kw):
    dx, dy = p[0] - centre[0], p[1] - centre[1]
    n = math.hypot(dx, dy) or 1
    ax.text(p[0] + dx / n * (off - 1), p[1] + dy / n * (off - 1), text, ha="center", va="center", fontsize=13, fontweight="bold", color="#0f172a", **kw)


def dot(ax, p, c="#0f172a"):
    ax.plot([p[0]], [p[1]], "o", color=c, ms=5, zorder=5)


def mark_angle(ax, v, p1, p2, text, r=0.22, color="#dc2626", fs=12):
    from matplotlib.patches import Arc
    text = text.replace("&deg;", "\u00b0")
    a1 = math.degrees(math.atan2(p1[1] - v[1], p1[0] - v[0]))
    a2 = math.degrees(math.atan2(p2[1] - v[1], p2[0] - v[0]))
    diff = (a2 - a1) % 360
    if diff > 180:
        a1, diff = a2, 360 - diff
    ax.add_patch(Arc(v, 2 * r, 2 * r, theta1=a1, theta2=a1 + diff, color=color, lw=2.2))
    mid = math.radians(a1 + diff / 2)
    rr = r + 0.14 + (0.05 if len(text) > 3 else 0)
    ax.text(v[0] + rr * math.cos(mid), v[1] + rr * math.sin(mid), text, color=color, fontsize=fs, ha="center", va="center", fontweight="bold")


def right_mark(ax, v, p1, p2, s=0.09):
    d1 = (p1[0] - v[0], p1[1] - v[1])
    d2 = (p2[0] - v[0], p2[1] - v[1])
    n1, n2 = math.hypot(*d1), math.hypot(*d2)
    u1 = (d1[0] / n1 * s, d1[1] / n1 * s)
    u2 = (d2[0] / n2 * s, d2[1] / n2 * s)
    a = (v[0] + u1[0], v[1] + u1[1])
    b = (v[0] + u1[0] + u2[0], v[1] + u1[1] + u2[1])
    c = (v[0] + u2[0], v[1] + u2[1])
    ax.plot([a[0], b[0], c[0]], [a[1], b[1], c[1]], color="#dc2626", lw=2)


def g(v):
    return fm(v, 4) + DEG


def _angle_in(s, label_, lo=0, hi=360):
    v = num(s, label_)
    if not (lo < v < hi):
        raise UErr(f"{label_} should be between {lo} and {hi} degrees.")
    return v


# ============================================================ circle theorems ==

@guard
def theorem(d):
    t = d.get("thm", "centre")
    steps = []
    fig, ax = _fig()
    O = (0, 0)
    if t == "centre":
        which = d.get("which", "circ")
        A, B, C = P_(215), P_(325), P_(90)
        if which == "circ":
            ang = _angle_in(d.get("v"), "The angle at the circumference", 0, 180)
            res = 2 * ang
            steps.append("<b>Theorem:</b> the angle at the <b>centre</b> of a circle is <b>twice</b> the angle at the <b>circumference</b> when both stand on the same arc.")
            steps.append(f"Angle ACB is at the circumference = {g(ang)}, standing on arc AB.")
            steps.append(f"Angle AOB (at the centre, same arc) = 2 &times; {g(ang)} = {HL_(g(res))}")
            lab_c, lab_o = g(ang), "x"
            ans = f"<b>Angle AOB = {g(res)}</b>"
        else:
            ang = _angle_in(d.get("v"), "The angle at the centre", 0, 360)
            res = ang / 2
            steps.append("<b>Theorem:</b> the angle at the centre is twice the angle at the circumference (same arc).")
            steps.append(f"Angle AOB at the centre = {g(ang)}.")
            steps.append(f"Angle ACB (circumference) = {g(ang)} &divide; 2 = {HL_(g(res))}")
            lab_c, lab_o = "x", g(ang)
            ans = f"<b>Angle ACB = {g(res)}</b>"
        for p_, n in ((A, "A"), (B, "B"), (C, "C")):
            dot(ax, p_)
            label(ax, p_, n)
        dot(ax, O)
        ax.text(0.0, -0.1, "O", fontsize=13, fontweight="bold", ha="center")
        for p_ in (A, B):
            seg(ax, O, p_)
            seg(ax, C, p_)
        mark_angle(ax, O, A, B, lab_o, r=0.28)
        mark_angle(ax, C, A, B, lab_c, r=0.3)
    elif t == "same":
        ang = _angle_in(d.get("v"), "The angle", 0, 180)
        A, B, C, D_ = P_(215), P_(325), P_(70), P_(115)
        steps.append("<b>Theorem:</b> angles in the <b>same segment</b> of a circle (standing on the same chord, on the same side) are <b>equal</b>.")
        steps.append(f"Angle ACB and angle ADB both stand on chord AB and are on the same side. Angle ACB = {g(ang)}.")
        steps.append(f"So angle ADB = {HL_(g(ang))}")
        for p_, n in ((A, "A"), (B, "B"), (C, "C"), (D_, "D")):
            dot(ax, p_)
            label(ax, p_, n)
        for p_ in (A, B):
            seg(ax, C, p_)
            seg(ax, D_, p_, color="#2563eb")
        mark_angle(ax, C, A, B, g(ang), r=0.3)
        mark_angle(ax, D_, A, B, "x", r=0.3, color="#2563eb")
        ans = f"<b>Angle ADB = {g(ang)}</b>"
    elif t == "semi":
        ang = _angle_in(d.get("v"), "Angle CAB", 0, 90)
        A, B, C = P_(180), P_(0), P_(55)
        steps.append("<b>Theorem:</b> the angle in a <b>semicircle</b> is <b>90&deg;</b> (when AB is a diameter, the angle at C on the circle is a right angle).")
        steps.append(f"So angle ACB = 90{DEG}.")
        steps.append("The angles in a triangle add up to 180&deg;.")
        res = 180 - 90 - ang
        steps.append(f"Angle ABC = 180{DEG} &minus; 90{DEG} &minus; {g(ang)} = {HL_(g(res))}")
        for p_, n in ((A, "A"), (B, "B"), (C, "C")):
            dot(ax, p_)
            label(ax, p_, n)
        seg(ax, A, B)
        seg(ax, A, C)
        seg(ax, C, B)
        dot(ax, O)
        right_mark(ax, C, A, B)
        mark_angle(ax, A, B, C, g(ang), r=0.3)
        mark_angle(ax, B, A, C, "x", r=0.3)
        ans = f"<b>Angle ABC = {g(res)}</b> (and angle ACB = 90{DEG})"
    elif t == "cyclic":
        which = d.get("which", "opp")
        ang = _angle_in(d.get("v"), "The angle", 0, 180)
        A, B, C, D_ = P_(120), P_(215), P_(320), P_(40)
        for p_, n in ((A, "A"), (B, "B"), (C, "C"), (D_, "D")):
            dot(ax, p_)
            label(ax, p_, n)
        for p_, q in ((A, B), (B, C), (C, D_), (D_, A)):
            seg(ax, p_, q)
        if which == "opp":
            res = 180 - ang
            steps.append("<b>Theorem:</b> the <b>opposite angles</b> of a cyclic quadrilateral (all four corners on the circle) add up to <b>180&deg;</b>.")
            steps.append(f"Angle ABC = {g(ang)}, and angle ADC is opposite to it.")
            steps.append(f"Angle ADC = 180{DEG} &minus; {g(ang)} = {HL_(g(res))}")
            mark_angle(ax, B, A, C, g(ang), r=0.3)
            mark_angle(ax, D_, A, C, "x", r=0.3)
            ans = f"<b>Angle ADC = {g(res)}</b>"
        else:
            # exterior angle at C (extend BC beyond C) equals interior opposite angle A  (use angle BAD)
            ext = P_(320)
            dirv = (C[0] - B[0], C[1] - B[1])
            n = math.hypot(*dirv)
            E = (C[0] + dirv[0] / n * 0.55, C[1] + dirv[1] / n * 0.55)
            seg(ax, C, E, ls="--")
            res = ang
            steps.append("<b>Theorem:</b> the <b>exterior angle</b> of a cyclic quadrilateral equals the <b>interior opposite angle</b>.")
            steps.append(f"Side BC is extended to E. The exterior angle DCE = {g(ang)}. The interior opposite angle is angle BAD.")
            steps.append(f"Reason: angle DCE + angle BCD = 180&deg; (straight line) and angle BAD + angle BCD = 180&deg; (cyclic quadrilateral), so angle BAD = angle DCE = {HL_(g(res))}")
            mark_angle(ax, C, D_, E, g(ang), r=0.25)
            mark_angle(ax, A, B, D_, "x", r=0.3)
            ans = f"<b>Angle BAD = {g(res)}</b>"
    elif t == "alt":
        ang = _angle_in(d.get("v"), "The angle between the tangent and the chord", 0, 180)
        A, B, C = P_(270), P_(20), P_(150)
        T1, T2 = (-1.5, -1), (1.5, -1)
        seg(ax, T1, T2, color="#7c3aed")
        for p_, n in ((A, "A"), (B, "B"), (C, "C")):
            dot(ax, p_)
            label(ax, p_, n)
        seg(ax, A, B)
        seg(ax, C, A)
        seg(ax, C, B)
        ax.text(1.45, -0.88, "tangent", color="#7c3aed", fontsize=10, ha="right")
        steps.append("<b>Theorem (alternate segment):</b> the angle between a <b>tangent</b> and a <b>chord</b> equals the angle in the <b>alternate segment</b> (the segment on the other side of the chord).")
        steps.append(f"The angle between tangent at A and chord AB is {g(ang)}.")
        steps.append(f"The angle in the alternate segment, angle ACB, = {HL_(g(ang))}")
        mark_angle(ax, A, B, T2, g(ang), r=0.3)
        mark_angle(ax, C, A, B, "x", r=0.3)
        ans = f"<b>Angle ACB = {g(ang)}</b>"
    elif t == "tangents":
        ang = _angle_in(d.get("v"), "Angle APB (between the two tangents)", 0, 180)
        # O at origin radius 1, P outside on the right
        # place P so tangents PA, PB: OP = 1/sin(ang/2)
        half = math.radians(ang / 2)
        OP = 1 / math.sin(half)
        Pp = (OP, 0)
        ax.set_xlim(-1.3, max(OP, 2) + 0.5)
        beta = math.degrees(math.acos(1 / OP))
        A, B = P_(beta), P_(-beta)
        dot(ax, O)
        ax.text(-0.05, -0.15, "O", fontsize=13, fontweight="bold", ha="center")
        for p_, n, off in ((A, "A", 1.13), (B, "B", 1.13)):
            dot(ax, p_)
            label(ax, p_, n, off)
        dot(ax, Pp)
        ax.text(Pp[0] + 0.1, 0.12, "P", fontsize=13, fontweight="bold")
        for q in (A, B):
            seg(ax, Pp, q, color="#7c3aed")
            seg(ax, O, q)
        seg(ax, O, Pp, ls="--", color="#64748b")
        right_mark(ax, A, O, Pp)
        right_mark(ax, B, O, Pp)
        res_o = 180 - ang
        steps.append("<b>Theorems used:</b> (1) a tangent is <b>perpendicular to the radius</b> at the point of contact, so angle OAP = angle OBP = 90&deg;. "
                     "(2) The two tangents from P are equal in length (PA = PB), and OP bisects angle APB.")
        steps.append(f"Angle APB = {g(ang)}. In the quadrilateral OAPB the angles add to 360&deg;: angle AOB = 360{DEG} &minus; 90{DEG} &minus; 90{DEG} &minus; {g(ang)} = {HL_(g(res_o))}")
        steps.append(f"OP bisects angle APB, so angle OPA = {g(ang)} &divide; 2 = {HL_(g(ang / 2))}. Also angle AOP = {g(res_o / 2)}.")
        mark_angle(ax, Pp, A, B, g(ang), r=0.35)
        mark_angle(ax, O, A, B, "x", r=0.25)
        ans = f"<b>Angle AOB = {g(res_o)}; angle OPA = {g(ang / 2)}</b>"
    elif t == "tanlen":
        r = pos(d.get("r"), "the radius")
        op = pos(d.get("op"), "the distance OP")
        if op <= r:
            raise UErr("The point P must be farther from the centre than the radius.")
        steps.append("<b>Theorem:</b> a tangent is perpendicular to the radius at the point of contact, so triangle OAP has a right angle at A. Use Pythagoras: PA<sup>2</sup> + OA<sup>2</sup> = OP<sup>2</sup>.")
        t2 = op * op - r * r
        steps.append(f"PA<sup>2</sup> = OP<sup>2</sup> &minus; OA<sup>2</sup> = {fm(op, 4)}<sup>2</sup> &minus; {fm(r, 4)}<sup>2</sup> = {fm(op * op, 4)} &minus; {fm(r * r, 4)} = {fm(t2, 4)}")
        pa = math.sqrt(float(t2))
        steps.append(f"PA = &radic;{fm(t2, 4)} = {HL_(f'{pa:.4g}')}")
        ang = math.degrees(math.asin(float(r / op)))
        beta = math.degrees(math.acos(float(r / op)))
        A, B = P_(beta), P_(-beta)
        OP = float(op / r)
        ax.set_xlim(-1.3, max(OP, 2) + 0.5)
        Pp = (OP, 0)
        dot(ax, O)
        ax.text(-0.05, -0.15, "O", fontsize=13, fontweight="bold", ha="center")
        for p_, n in ((A, "A"), (B, "B")):
            dot(ax, p_)
            label(ax, p_, n)
        dot(ax, Pp)
        ax.text(Pp[0] + 0.1, 0.12, "P", fontsize=13, fontweight="bold")
        for q in (A, B):
            seg(ax, Pp, q, color="#7c3aed")
            seg(ax, O, q)
        seg(ax, O, Pp, ls="--", color="#64748b")
        right_mark(ax, A, O, Pp)
        ax.text(OP / 2 + 0.2, 0.05, f"OP = {fm(op, 4)}", fontsize=10)
        ax.text((A[0] + OP) / 2 + 0.05, A[1] / 2 + 0.25, "PA = ?", fontsize=11, color="#7c3aed", fontweight="bold")
        ax.text(A[0] / 2 - 0.35, A[1] / 2 + 0.1, f"r={fm(r, 4)}", fontsize=10)
        ans = f"<b>Tangent length PA = {pa:.4g}</b>"
    elif t == "chord":
        find = d.get("find", "chord")
        r = pos(d.get("r"), "the radius")
        steps.append("<b>Theorem:</b> a line from the centre of a circle <b>perpendicular to a chord bisects the chord</b>. So we get a right-angled triangle with hypotenuse = radius, one side = distance from the centre, and the other side = half the chord.")
        if find == "chord":
            dist = num(d.get("x"), "the distance from the centre")
            if not 0 <= dist < r:
                raise UErr("The distance from the centre must be smaller than the radius.")
            half = math.sqrt(float(r * r - dist * dist))
            steps.append(f"(half chord)<sup>2</sup> = r<sup>2</sup> &minus; d<sup>2</sup> = {fm(r, 4)}<sup>2</sup> &minus; {fm(dist, 4)}<sup>2</sup> = {fm(r * r - dist * dist, 4)}")
            steps.append(f"Half chord = &radic;{fm(r * r - dist * dist, 4)} = {half:.4g}, so the chord = 2 &times; {half:.4g} = {HL_(f'{2 * half:.4g}')}")
            ans = f"<b>Chord length = {2 * half:.4g}</b>"
            dd, hh = float(dist) / float(r), half / float(r)
        else:
            ch = pos(d.get("x"), "the chord length")
            if ch > 2 * r:
                raise UErr("A chord cannot be longer than the diameter.")
            half = ch / 2
            dsq = r * r - half * half
            steps.append(f"Half the chord = {fm(ch, 4)} &divide; 2 = {fm(half, 4)}")
            steps.append(f"d<sup>2</sup> = r<sup>2</sup> &minus; (half chord)<sup>2</sup> = {fm(r * r, 4)} &minus; {fm(half * half, 4)} = {fm(dsq, 4)}")
            dist = math.sqrt(float(dsq))
            steps.append(f"d = &radic;{fm(dsq, 4)} = {HL_(f'{dist:.4g}')}")
            ans = f"<b>Distance from the centre = {dist:.4g}</b>"
            dd, hh = dist / float(r), float(half) / float(r)
        A, B = (-hh, -dd), (hh, -dd)
        M_ = (0, -dd)
        dot(ax, O)
        ax.text(0.04, 0.08, "O", fontsize=13, fontweight="bold")
        for p_, n in ((A, "A"), (B, "B")):
            dot(ax, p_)
            label(ax, p_, n, 1.1)
        seg(ax, A, B)
        seg(ax, O, M_, ls="--", color="#dc2626")
        seg(ax, O, B)
        right_mark(ax, M_, O, B)
        ax.text(0.05, -dd / 2, "d", color="#dc2626", fontsize=12)
        ax.text(hh / 2, -dd - 0.12, "half chord", fontsize=9, ha="center")
    elif t == "inter":
        vals = [num(d.get(k), "", True) for k in ("ax", "xb", "cx", "xd")]
        if sum(v is None for v in vals) != 1:
            raise UErr("Leave exactly ONE of the four lengths empty: that is the one to find.")
        for v in vals:
            if v is not None and v <= 0:
                raise UErr("Lengths must be bigger than 0.")
        steps.append("<b>Theorem (intersecting chords):</b> when two chords AB and CD cross at X, AX &times; XB = CX &times; XD.")
        names = ["AX", "XB", "CX", "XD"]
        i = vals.index(None)
        a, b, c, e = vals
        if i == 0:
            r = c * e / b
            eq = f"AX &times; {fm(b, 4)} = {fm(c, 4)} &times; {fm(e, 4)}, so AX = {FR(fm(c, 4) + ' &times; ' + fm(e, 4), fm(b, 4))}"
        elif i == 1:
            r = c * e / a
            eq = f"{fm(a, 4)} &times; XB = {fm(c, 4)} &times; {fm(e, 4)}, so XB = {FR(fm(c, 4) + ' &times; ' + fm(e, 4), fm(a, 4))}"
        elif i == 2:
            r = a * b / e
            eq = f"{fm(a, 4)} &times; {fm(b, 4)} = CX &times; {fm(e, 4)}, so CX = {FR(fm(a, 4) + ' &times; ' + fm(b, 4), fm(e, 4))}"
        else:
            r = a * b / c
            eq = f"{fm(a, 4)} &times; {fm(b, 4)} = {fm(c, 4)} &times; XD, so XD = {FR(fm(a, 4) + ' &times; ' + fm(b, 4), fm(c, 4))}"
        steps.append(eq + f" = {HL_(fm(r, 4))}")
        ans = f"<b>{names[i]} = {fm(r, 4)}</b>"
        A, B, C, D_ = P_(200), P_(40), P_(120), P_(300)
        # chords AB and CD cross at X
        X = (0.0, 0.0)
        # compute intersection numerically
        x1, y1, x2, y2 = A[0], A[1], B[0], B[1]
        x3, y3, x4, y4 = C[0], C[1], D_[0], D_[1]
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / den
        py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / den
        X = (px, py)
        for p_, n in ((A, "A"), (B, "B"), (C, "C"), (D_, "D")):
            dot(ax, p_)
            label(ax, p_, n)
        seg(ax, A, B)
        seg(ax, C, D_)
        dot(ax, X)
        ax.text(X[0] + 0.07, X[1] + 0.08, "X", fontsize=12, fontweight="bold")
        for (p_, q, tx) in ((A, X, vals[0]), (X, B, vals[1]), (C, X, vals[2]), (X, D_, vals[3])):
            mid = ((p_[0] + q[0]) / 2, (p_[1] + q[1]) / 2)
            ax.text(mid[0] - 0.12, mid[1] + 0.12, fm(tx, 4) if tx is not None else "?", fontsize=10, color="#dc2626", fontweight="bold")
    elif t == "tansec":
        vals = [num(d.get(k), "", True) for k in ("pt", "pa", "pb")]
        if sum(v is None for v in vals) != 1:
            raise UErr("Leave exactly ONE of PT, PA, PB empty.")
        for v in vals:
            if v is not None and v <= 0:
                raise UErr("Lengths must be bigger than 0.")
        steps.append("<b>Theorem (tangent and secant):</b> from an outside point P, tangent PT and a line through the circle meeting it at A (nearer) and B (farther): PT<sup>2</sup> = PA &times; PB.")
        pt_, pa, pb = vals
        if pt_ is None:
            r2 = pa * pb
            r = math.sqrt(float(r2))
            steps.append(f"PT<sup>2</sup> = {fm(pa, 4)} &times; {fm(pb, 4)} = {fm(r2, 4)}, so PT = {HL_(f'{r:.4g}')}")
            ans = f"<b>PT = {r:.4g}</b>"
        elif pa is None:
            r = pt_ * pt_ / pb
            steps.append(f"{fm(pt_, 4)}<sup>2</sup> = PA &times; {fm(pb, 4)}, so PA = {fm(pt_ * pt_, 4)} &divide; {fm(pb, 4)} = {HL_(fm(r, 4))}")
            ans = f"<b>PA = {fm(r, 4)}</b>"
        else:
            r = pt_ * pt_ / pa
            steps.append(f"{fm(pt_, 4)}<sup>2</sup> = {fm(pa, 4)} &times; PB, so PB = {fm(pt_ * pt_, 4)} &divide; {fm(pa, 4)} = {HL_(fm(r, 4))}")
            ans = f"<b>PB = {fm(r, 4)}</b>"
        Pp = (2.0, -0.6)
        # tangent point T and secant through the circle
        # compute tangent from P
        dist = math.hypot(*Pp)
        base = math.degrees(math.atan2(Pp[1], Pp[0]))
        off = math.degrees(math.acos(1 / dist))
        T = P_(base + off)
        # secant: direction toward centre-ish
        dirv = (-Pp[0] + 0.0, -Pp[1] + 0.35)
        n = math.hypot(*dirv)
        u = (dirv[0] / n, dirv[1] / n)
        bq = u[0] * Pp[0] + u[1] * Pp[1]
        disc = bq * bq - (dist * dist - 1)
        s1, s2 = -bq - math.sqrt(disc), -bq + math.sqrt(disc)
        A = (Pp[0] + u[0] * s1, Pp[1] + u[1] * s1)
        B = (Pp[0] + u[0] * s2, Pp[1] + u[1] * s2)
        ax.set_xlim(-1.4, 2.4)
        ax.set_ylim(-1.5, 1.5)
        for p_, n_ in ((Pp, "P"), (T, "T"), (A, "A"), (B, "B")):
            dot(ax, p_)
            ax.text(p_[0] + 0.08, p_[1] + 0.08, n_, fontsize=13, fontweight="bold")
        seg(ax, Pp, T, color="#7c3aed")
        seg(ax, Pp, B)
    else:
        raise UErr("Choose a theorem.")
    img = _b64(fig)
    return _ok(steps, {"image": img, "text": ans})


def HL_(s):
    return f"<span class='hl'>{s}</span>"


# ============================================================== mensuration =====

PI_OPTS = [("22/7", "&pi; = 22/7"), ("3.14", "&pi; = 3.14"), ("3.142", "&pi; = 3.142"), ("3.1416", "&pi; = 3.1416"), ("exact", "leave in terms of &pi;")]


def pi_choice(d):
    c = d.get("pi", "22/7")
    if c == "22/7":
        return Fraction(22, 7), "22/7", False
    if c == "exact":
        return Fraction(314159265358979, 10 ** 14), "&pi;", True
    if c in ("3.14", "3.142", "3.1416"):
        return Fraction(c), c, False
    raise UErr("Choose a value for &pi;.")


def piq(coef, pv, ptxt, exact, p=2):
    """coef * pi -> text"""
    coef = Fraction(coef)
    if exact:
        c = fr(coef) if coef != 1 else ""
        return f"{c}&pi;" if coef.denominator == 1 or True else ""
    return fm(coef * pv, p)


def piq_full(coef, pv, ptxt, exact, p=2):
    if exact:
        return f"{piq(coef, pv, ptxt, exact)} &asymp; {fm(coef * Fraction(math.pi).limit_denominator(10 ** 12), p)}"
    return fm(coef * pv, p)


@guard
def circle(d):
    pv, ptxt, exact = pi_choice(d)
    kind = d.get("kind", "r")
    steps = []
    if kind in ("r", "d"):
        x = pos(d.get("x"), "the radius" if kind == "r" else "the diameter")
        r = x if kind == "r" else x / 2
        if kind == "d":
            steps.append(f"Radius = diameter &divide; 2 = {fm(x, 4)} &divide; 2 = {fm(r, 4)}")
        c = 2 * r
        a = r * r
        steps.append(f"<b>Circumference</b> C = 2&pi;r = 2 &times; {ptxt} &times; {fm(r, 4)} = {HL_(piq_full(c, pv, ptxt, exact))}"
                     if not exact else f"<b>Circumference</b> C = 2&pi;r = 2&pi;({fm(r, 4)}) = {HL_(piq_full(c, pv, ptxt, exact))}")
        steps.append(f"<b>Area</b> A = &pi;r<sup>2</sup> = {ptxt} &times; {fm(r, 4)}<sup>2</sup> = {HL_(piq_full(a, pv, ptxt, exact))}")
        return _ok(steps, f"<b>C = {piq_full(c, pv, ptxt, exact)}; A = {piq_full(a, pv, ptxt, exact)}</b>")
    if kind == "C":
        C = pos(d.get("x"), "the circumference")
        r = C / (2 * pv)
        steps.append(f"C = 2&pi;r, so r = {FR('C', '2&pi;')} = {FR(fm(C, 4), '2 &times; ' + ptxt)} = {fm(r, 4)}")
        a = pv * r * r
        steps.append(f"Area = &pi;r<sup>2</sup> = {ptxt} &times; {fm(r, 4)}<sup>2</sup> = {HL_(fm(a, 2))}")
        return _ok(steps, f"<b>r = {fm(r, 4)}; A = {fm(a, 2)}</b>")
    A = pos(d.get("x"), "the area")
    r2 = A / pv
    r = math.sqrt(float(r2))
    steps.append(f"A = &pi;r<sup>2</sup>, so r<sup>2</sup> = {FR('A', '&pi;')} = {FR(fm(A, 4), ptxt)} = {fm(r2, 4)}")
    steps.append(f"r = &radic;{fm(r2, 4)} = {r:.4g}")
    c = 2 * float(pv) * r
    steps.append(f"Circumference = 2&pi;r = 2 &times; {ptxt} &times; {r:.4g} = {HL_(f'{c:.4g}')}")
    return _ok(steps, f"<b>r = {r:.4g}; C = {c:.4g}</b>")


def _sector_fig(r, th, seg_=False):
    plt = _plt()
    from matplotlib.patches import Wedge, Polygon
    fig, ax = plt.subplots(figsize=(4.8, 4.8))
    ax.set_aspect("equal")
    ax.axis("off")
    rr = 1.0
    if seg_:
        a, b = math.radians(90 - th / 2), math.radians(90 + th / 2)
        pts = [(math.cos(a), math.sin(a)), (math.cos(b), math.sin(b))]
        w = Wedge((0, 0), rr, 90 - th / 2, 90 + th / 2, fc="#e2e8f0", ec="#1e293b", lw=1.8)
        ax.add_patch(w)
        ax.add_patch(Polygon([(0, 0), pts[0], pts[1]], fc="white", ec="#1e293b", lw=1.8))
        # segment shaded
        import numpy as np
        t = np.linspace(a, b, 60)
        xs = [math.cos(v) for v in t[::-1]] + [pts[0][0]]
        ys = [math.sin(v) for v in t[::-1]] + [pts[0][1]]
        ax.fill([pts[0][0]] + [math.cos(v) for v in np.linspace(a, b, 60)], [pts[0][1]] + [math.sin(v) for v in np.linspace(a, b, 60)], color="#93c5fd", alpha=.9)
        ax.text(0, 0.5 * math.cos(math.radians(th / 2)) + 0.35 * (1 - math.cos(math.radians(th / 2))) + 0.03, "segment", ha="center", fontsize=9)
    else:
        ax.add_patch(Wedge((0, 0), rr, 90 - th / 2, 90 + th / 2, fc="#93c5fd", ec="#1e293b", lw=1.8))
    ax.text(0, -0.08, "O", ha="center", fontsize=12, fontweight="bold")
    ax.text(0.0, 0.25, f"{fm(th, 4)}{DEG}".replace("&deg;", "°"), ha="center", fontsize=11, color="#dc2626")
    ax.text(0.45 * math.cos(math.radians(90 - th / 2)) + 0.05, 0.45 * math.sin(math.radians(90 - th / 2)) - 0.05, f"r = {fm(r, 4)}", fontsize=10)
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.3, 1.2)
    return _b64(fig)


@guard
def sector(d):
    pv, ptxt, exact = pi_choice(d)
    kind = d.get("kind", "all")
    r = pos(d.get("r"), "the radius")
    steps = []
    if kind == "all":
        th = num(d.get("th"), "the angle")
        if not 0 < th <= 360:
            raise UErr("The angle must be between 0 and 360 degrees.")
        frac = th / 360
        steps.append(f"The sector is {FR(fm(th, 4), 360)} of a whole circle (angle &divide; 360).")
        arc = frac * 2 * r
        area = frac * r * r
        steps.append(f"<b>Arc length</b> = {FR('&theta;', 360)} &times; 2&pi;r = {FR(fm(th, 4), 360)} &times; 2 &times; {ptxt} &times; {fm(r, 4)} = {HL_(piq_full(arc, pv, ptxt, exact))}")
        steps.append(f"<b>Area of sector</b> = {FR('&theta;', 360)} &times; &pi;r<sup>2</sup> = {FR(fm(th, 4), 360)} &times; {ptxt} &times; {fm(r, 4)}<sup>2</sup> = {HL_(piq_full(area, pv, ptxt, exact))}")
        per = arc * pv + 2 * r if not exact else None
        if exact:
            steps.append(f"<b>Perimeter of the sector</b> = arc + 2 radii = {piq_full(arc, pv, ptxt, exact)} + {fm(2 * r, 4)}")
            pertxt = f"{piq(arc, pv, ptxt, exact)} + {fm(2 * r, 4)} &asymp; {fm(arc * Fraction(math.pi).limit_denominator(10**12) + 2 * r, 2)}"
        else:
            steps.append(f"<b>Perimeter of the sector</b> = arc + 2 radii = {fm(arc * pv, 2)} + 2 &times; {fm(r, 4)} = {HL_(fm(per, 2))}")
            pertxt = fm(per, 2)
        res = f"<b>Arc length = {piq_full(arc, pv, ptxt, exact)}<br>Sector area = {piq_full(area, pv, ptxt, exact)}<br>Perimeter = {pertxt}</b>"
        return _ok(steps, {"image": _sector_fig(float(r), float(th)), "text": res})
    if kind == "seg":
        th = num(d.get("th"), "the angle")
        if not 0 < th < 180:
            raise UErr("For a segment use an angle less than 180 degrees.")
        thr = math.radians(float(th))
        sect = float(th) / 360 * float(pv) * float(r) ** 2 if not exact else float(th) / 360 * math.pi * float(r) ** 2
        tri = 0.5 * float(r) ** 2 * math.sin(thr)
        chord = 2 * float(r) * math.sin(thr / 2)
        steps.append(f"<b>Idea:</b> area of segment = area of sector &minus; area of triangle OAB.")
        steps.append(f"Area of sector = {FR(fm(th, 4), 360)} &times; &pi;r<sup>2</sup> = {sect:.4f}")
        steps.append(f"Area of triangle = &frac12;r<sup>2</sup> sin &theta; = &frac12; &times; {fm(r, 4)}<sup>2</sup> &times; sin {fm(th, 4)}&deg; = {tri:.4f}")
        steps.append(f"Area of segment = {sect:.4f} &minus; {tri:.4f} = {HL_(f'{sect - tri:.4f}')}")
        steps.append(f"<b>Chord length</b> AB = 2r sin(&theta;/2) = 2 &times; {fm(r, 4)} &times; sin {fm(th / 2, 4)}&deg; = {HL_(f'{chord:.4f}')}")
        return _ok(steps, {"image": _sector_fig(float(r), float(th), True),
                           "text": f"<b>Segment area = {sect - tri:.2f}<br>Chord length = {chord:.2f}</b>"})
    if kind == "arc_angle":
        arc = pos(d.get("v"), "the arc length")
        th = arc * 360 / (2 * pv * r)
        steps.append(f"Arc = {FR('&theta;', 360)} &times; 2&pi;r, so &theta; = {FR('arc &times; 360', '2&pi;r')} = {FR(fm(arc, 4) + ' &times; 360', '2 &times; ' + ptxt + ' &times; ' + fm(r, 4))} = {HL_(fm(th, 2) + DEG)}")
        return _ok(steps, f"<b>&theta; = {fm(th, 2)}{DEG}</b>")
    if kind == "area_angle":
        A = pos(d.get("v"), "the sector area")
        th = A * 360 / (pv * r * r)
        steps.append(f"Area = {FR('&theta;', 360)} &times; &pi;r<sup>2</sup>, so &theta; = {FR('Area &times; 360', '&pi;r<sup>2</sup>')} = {FR(fm(A, 4) + ' &times; 360', ptxt + ' &times; ' + fm(r, 4) + '<sup>2</sup>')} = {HL_(fm(th, 2) + DEG)}")
        return _ok(steps, f"<b>&theta; = {fm(th, 2)}{DEG}</b>")
    if kind == "cone":
        th = num(d.get("th"), "the angle")
        if not 0 < th < 360:
            raise UErr("The angle must be between 0 and 360 degrees.")
        steps.append("<b>Idea:</b> when a sector is rolled up to make a cone, the sector's <b>radius</b> becomes the cone's <b>slant height l</b>, and the sector's <b>arc</b> becomes the <b>circumference of the cone's base</b>.")
        arc = th / 360 * 2 * pv * r
        steps.append(f"Arc length = {FR(fm(th, 4), 360)} &times; 2&pi; &times; {fm(r, 4)} = {fm(arc, 4)}")
        rb = arc / (2 * pv)
        steps.append(f"Base radius: 2&pi;r<sub>b</sub> = {fm(arc, 4)}, so r<sub>b</sub> = {fm(rb, 4)} (it also equals {FR(fm(th, 4), 360)} &times; {fm(r, 4)})")
        hh2 = r * r - rb * rb
        if hh2 <= 0:
            raise UErr("This sector cannot make a cone.")
        h = math.sqrt(float(hh2))
        steps.append(f"Height: h<sup>2</sup> = l<sup>2</sup> &minus; r<sub>b</sub><sup>2</sup> = {fm(r, 4)}<sup>2</sup> &minus; {fm(rb, 4)}<sup>2</sup> = {fm(hh2, 4)}, so h = {h:.4g}")
        vol = float(pv) / 3 * float(rb) ** 2 * h
        steps.append(f"Volume = &frac13;&pi;r<sub>b</sub><sup>2</sup>h = {vol:.4g}")
        return _ok(steps, f"<b>Base radius = {fm(rb, 4)}; height = {h:.4g}; volume = {vol:.4g}</b>")
    raise UErr("Choose a type of problem.")


# ----------------------------------------------------------------------- solids ---

def _sqrt_txt(x):
    x = float(x)
    return f"{math.sqrt(x):.4g}"


@guard
def solids(d):
    pv, ptxt, exact = pi_choice(d)
    s = d.get("solid", "cuboid")
    steps = []
    rows = []

    def pos_(k, lab):
        return pos(d.get(k), lab)

    def show_pi(coef, p=2):
        return piq_full(coef, pv, ptxt, exact, p)

    if s == "cuboid":
        l, w, h = pos_("l", "the length"), pos_("w", "the width"), pos_("h", "the height")
        V = l * w * h
        T = 2 * (l * w + l * h + w * h)
        dg = math.sqrt(float(l * l + w * w + h * h))
        steps += [f"<b>Volume</b> = l &times; w &times; h = {fm(l, 4)} &times; {fm(w, 4)} &times; {fm(h, 4)} = {HL_(fm(V, 4))}",
                  f"<b>Total surface area</b> = 2(lw + lh + wh) = 2({fm(l * w, 4)} + {fm(l * h, 4)} + {fm(w * h, 4)}) = {HL_(fm(T, 4))}",
                  f"<b>Space diagonal</b> = &radic;(l<sup>2</sup> + w<sup>2</sup> + h<sup>2</sup>) = &radic;({fm(l * l, 4)} + {fm(w * w, 4)} + {fm(h * h, 4)}) = {HL_(f'{dg:.4g}')}"]
        res = f"Volume = {fm(V, 4)}<br>Total surface area = {fm(T, 4)}<br>Diagonal = {dg:.4g}"
    elif s == "cube":
        a = pos_("l", "the side")
        V, T = a ** 3, 6 * a * a
        dg = float(a) * math.sqrt(3)
        steps += [f"<b>Volume</b> = s<sup>3</sup> = {fm(a, 4)}<sup>3</sup> = {HL_(fm(V, 4))}",
                  f"<b>Total surface area</b> = 6s<sup>2</sup> = 6 &times; {fm(a * a, 4)} = {HL_(fm(T, 4))}",
                  f"<b>Space diagonal</b> = s&radic;3 = {HL_(f'{dg:.4g}')}"]
        res = f"Volume = {fm(V, 4)}<br>Surface area = {fm(T, 4)}<br>Diagonal = {dg:.4g}"
    elif s == "cylinder":
        r, h = pos_("r", "the radius"), pos_("h", "the height")
        steps += [f"<b>Volume</b> = &pi;r<sup>2</sup>h = {ptxt} &times; {fm(r, 4)}<sup>2</sup> &times; {fm(h, 4)} = {HL_(show_pi(r * r * h))}",
                  f"<b>Curved surface area</b> = 2&pi;rh = 2 &times; {ptxt} &times; {fm(r, 4)} &times; {fm(h, 4)} = {HL_(show_pi(2 * r * h))}",
                  f"<b>Total surface area</b> = 2&pi;r(r + h) = curved + 2 circles = 2&pi;r<sup>2</sup> + 2&pi;rh = {HL_(show_pi(2 * r * (r + h)))}"]
        res = f"Volume = {show_pi(r * r * h)}<br>Curved surface = {show_pi(2 * r * h)}<br>Total surface = {show_pi(2 * r * (r + h))}"
    elif s == "cone":
        r = pos_("r", "the base radius")
        h_s, l_s = (d.get("h") or "").strip(), (d.get("sl") or "").strip()
        if h_s:
            h = pos_("h", "the height")
            l2 = r * r + h * h
            l = math.sqrt(float(l2))
            steps.append(f"<b>Slant height</b> l: l<sup>2</sup> = r<sup>2</sup> + h<sup>2</sup> = {fm(r * r, 4)} + {fm(h * h, 4)} = {fm(l2, 4)}, so l = {l:.4g}")
        elif l_s:
            l = float(pos_("sl", "the slant height"))
            h2 = l * l - float(r * r)
            if h2 <= 0:
                raise UErr("The slant height must be longer than the radius.")
            h = Fraction(math.sqrt(h2)).limit_denominator(10 ** 9)
            steps.append(f"<b>Height</b> h: h<sup>2</sup> = l<sup>2</sup> &minus; r<sup>2</sup> = {l * l:.4g} &minus; {fm(r * r, 4)}, so h = {float(h):.4g}")
        else:
            raise UErr("Give either the height or the slant height.")
        V = Fraction(1, 3) * r * r * h
        steps.append(f"<b>Volume</b> = &frac13;&pi;r<sup>2</sup>h = &frac13; &times; {ptxt} &times; {fm(r, 4)}<sup>2</sup> &times; {float(h):.4g} = {HL_(show_pi(V))}")
        csa = float(r) * l
        csa_txt = (f"{csa:.4g}&pi; &asymp; {csa * math.pi:.2f}" if exact else fm(Fraction(csa) * pv, 2))
        steps.append(f"<b>Curved surface area</b> = &pi;rl = {ptxt} &times; {fm(r, 4)} &times; {l:.4g} = {HL_(csa_txt)}")
        tsa = float(r) * (float(r) + l)
        tsa_txt = (f"{tsa:.4g}&pi; &asymp; {tsa * math.pi:.2f}" if exact else fm(Fraction(tsa) * pv, 2))
        steps.append(f"<b>Total surface area</b> = &pi;r(r + l) = {HL_(tsa_txt)}")
        res = f"Volume = {show_pi(V)}<br>Curved surface = {csa_txt}<br>Total surface = {tsa_txt}"
    elif s == "sphere":
        r = pos_("r", "the radius")
        V, A = Fraction(4, 3) * r ** 3, 4 * r * r
        steps += [f"<b>Volume</b> = {FR(4, 3)}&pi;r<sup>3</sup> = {FR(4, 3)} &times; {ptxt} &times; {fm(r, 4)}<sup>3</sup> = {HL_(show_pi(V))}",
                  f"<b>Surface area</b> = 4&pi;r<sup>2</sup> = 4 &times; {ptxt} &times; {fm(r, 4)}<sup>2</sup> = {HL_(show_pi(A))}"]
        res = f"Volume = {show_pi(V)}<br>Surface area = {show_pi(A)}"
    elif s == "hemi":
        r = pos_("r", "the radius")
        V, C, T = Fraction(2, 3) * r ** 3, 2 * r * r, 3 * r * r
        steps += [f"<b>Volume</b> = {FR(2, 3)}&pi;r<sup>3</sup> = {HL_(show_pi(V))}",
                  f"<b>Curved surface area</b> = 2&pi;r<sup>2</sup> = {HL_(show_pi(C))}",
                  f"<b>Total surface area</b> = curved + flat circle = 2&pi;r<sup>2</sup> + &pi;r<sup>2</sup> = 3&pi;r<sup>2</sup> = {HL_(show_pi(T))}"]
        res = f"Volume = {show_pi(V)}<br>Curved surface = {show_pi(C)}<br>Total surface = {show_pi(T)}"
    elif s == "pyramid":
        l, w, h = pos_("l", "the base length"), pos_("w", "the base width"), pos_("h", "the height")
        V = Fraction(1, 3) * l * w * h
        s1 = math.sqrt(float(h * h + (w / 2) ** 2))
        s2 = math.sqrt(float(h * h + (l / 2) ** 2))
        T = float(l * w) + float(l) * s1 + float(w) * s2
        steps += [f"<b>Volume</b> = &frac13; &times; base area &times; height = &frac13; &times; {fm(l, 4)} &times; {fm(w, 4)} &times; {fm(h, 4)} = {HL_(fm(V, 4))}",
                  f"<b>Slant heights</b> of the sloping faces (Pythagoras): {s1:.4g} (on the sides of length {fm(l, 4)}) and {s2:.4g} (on the sides of length {fm(w, 4)}).",
                  f"<b>Total surface area</b> = base + 4 triangles = {fm(l * w, 4)} + {fm(l, 4)} &times; {s1:.4g} + {fm(w, 4)} &times; {s2:.4g} = {HL_(f'{T:.4g}')}"]
        res = f"Volume = {fm(V, 4)}<br>Total surface area = {T:.4g}"
    elif s == "prism":
        a, b, c = pos_("a", "side a"), pos_("b", "side b"), pos_("c", "side c")
        L = pos_("L", "the length of the prism")
        if a + b > c and a + c > b and b + c > a:
            sp = (a + b + c) / 2
            area2 = sp * (sp - a) * (sp - b) * (sp - c)
            area = math.sqrt(float(area2))
        else:
            raise UErr("Those three sides cannot make a triangle.")
        V = area * float(L)
        T = 2 * area + float(a + b + c) * float(L)
        steps += [f"<b>Area of the triangular end</b> (Heron's formula): s = (a + b + c) &divide; 2 = {fm(sp, 4)}; area = &radic;[s(s&minus;a)(s&minus;b)(s&minus;c)] = &radic;{fm(area2, 4)} = {area:.4g}",
                  f"<b>Volume</b> = area of end &times; length = {area:.4g} &times; {fm(L, 4)} = {HL_(f'{V:.4g}')}",
                  f"<b>Total surface area</b> = 2 ends + 3 rectangles = 2 &times; {area:.4g} + ({fm(a + b + c, 4)}) &times; {fm(L, 4)} = {HL_(f'{T:.4g}')}"]
        res = f"Volume = {V:.4g}<br>Total surface area = {T:.4g}"
    elif s == "frustum":
        R, r, h = pos_("R", "the big radius"), pos_("r", "the small radius"), pos_("h", "the height")
        if R <= r:
            raise UErr("The big radius R must be larger than the small radius r.")
        V = Fraction(1, 3) * h * (R * R + R * r + r * r)
        l = math.sqrt(float(h * h + (R - r) ** 2))
        csa = float(R + r) * l
        tsa = csa + float(R * R + r * r)
        steps += [f"<b>Volume</b> = &frac13;&pi;h(R<sup>2</sup> + Rr + r<sup>2</sup>) = &frac13; &times; {ptxt} &times; {fm(h, 4)} &times; ({fm(R * R, 4)} + {fm(R * r, 4)} + {fm(r * r, 4)}) = {HL_(show_pi(V))}",
                  f"<b>Slant height</b> l = &radic;(h<sup>2</sup> + (R &minus; r)<sup>2</sup>) = &radic;({fm(h * h, 4)} + {fm((R - r) ** 2, 4)}) = {l:.4g}",
                  f"<b>Curved surface area</b> = &pi;(R + r)l = {HL_((f'{csa:.4g}&pi; &asymp; {csa * math.pi:.2f}') if exact else fm(Fraction(csa) * pv, 2))}",
                  f"<b>Total surface area</b> = curved + top circle + bottom circle = {HL_((f'{tsa:.4g}&pi; &asymp; {tsa * math.pi:.2f}') if exact else fm(Fraction(tsa) * pv, 2))}"]
        res = f"Volume = {show_pi(V)}<br>Curved surface = {(f'{csa:.4g}&pi;' if exact else fm(Fraction(csa) * pv, 2))}<br>Total surface = {(f'{tsa:.4g}&pi;' if exact else fm(Fraction(tsa) * pv, 2))}"
    else:
        raise UErr("Choose a solid.")
    return _ok(steps, f"<b>{res}</b>")


@guard
def solid_inverse(d):
    pv, ptxt, exact = pi_choice(d)
    s = d.get("solid", "cyl_h")
    V = pos(d.get("V"), "the volume")
    steps = []
    if s == "cyl_h":
        r = pos(d.get("k"), "the radius")
        h = V / (pv * r * r)
        steps.append(f"V = &pi;r<sup>2</sup>h, so h = {FR('V', '&pi;r<sup>2</sup>')} = {FR(fm(V, 4), ptxt + ' &times; ' + fm(r, 4) + '<sup>2</sup>')} = {HL_(fm(h, 4))}")
        res = f"h = {fm(h, 4)}"
    elif s == "cyl_r":
        h = pos(d.get("k"), "the height")
        r2 = V / (pv * h)
        steps.append(f"V = &pi;r<sup>2</sup>h, so r<sup>2</sup> = {FR('V', '&pi;h')} = {FR(fm(V, 4), ptxt + ' &times; ' + fm(h, 4))} = {fm(r2, 4)}")
        r = math.sqrt(float(r2))
        steps.append(f"r = &radic;{fm(r2, 4)} = {HL_(f'{r:.4g}')}")
        res = f"r = {r:.4g}"
    elif s == "cone_h":
        r = pos(d.get("k"), "the radius")
        h = 3 * V / (pv * r * r)
        steps.append(f"V = &frac13;&pi;r<sup>2</sup>h, so h = {FR('3V', '&pi;r<sup>2</sup>')} = {FR('3 &times; ' + fm(V, 4), ptxt + ' &times; ' + fm(r, 4) + '<sup>2</sup>')} = {HL_(fm(h, 4))}")
        res = f"h = {fm(h, 4)}"
    elif s == "cone_r":
        h = pos(d.get("k"), "the height")
        r2 = 3 * V / (pv * h)
        steps.append(f"V = &frac13;&pi;r<sup>2</sup>h, so r<sup>2</sup> = {FR('3V', '&pi;h')} = {fm(r2, 4)}")
        r = math.sqrt(float(r2))
        steps.append(f"r = &radic;{fm(r2, 4)} = {HL_(f'{r:.4g}')}")
        res = f"r = {r:.4g}"
    elif s == "sph_r":
        r3 = 3 * V / (4 * pv)
        steps.append(f"V = {FR(4, 3)}&pi;r<sup>3</sup>, so r<sup>3</sup> = {FR('3V', '4&pi;')} = {FR('3 &times; ' + fm(V, 4), '4 &times; ' + ptxt)} = {fm(r3, 4)}")
        r = float(r3) ** (1 / 3)
        steps.append(f"r = &sup3;&radic;{fm(r3, 4)} = {HL_(f'{r:.4g}')}")
        res = f"r = {r:.4g}"
    elif s == "cube_s":
        r = float(V) ** (1 / 3)
        steps.append(f"V = s<sup>3</sup>, so s = &sup3;&radic;{fm(V, 4)} = {HL_(f'{r:.4g}')}")
        res = f"s = {r:.4g}"
    else:
        raise UErr("Choose what to find.")
    return _ok(steps, f"<b>{res}</b>")


@guard
def similar(d):
    kind = d.get("kind", "lengths")
    steps = []
    if kind == "lengths":
        a, b = _ratio2(d.get("r"))
        steps.append(f"<b>Rule:</b> for similar shapes with length ratio a : b, the AREA ratio is a<sup>2</sup> : b<sup>2</sup> and the VOLUME ratio is a<sup>3</sup> : b<sup>3</sup>.")
        steps.append(f"Length ratio = {fm(a, 4)} : {fm(b, 4)}")
        steps.append(f"Area ratio = {fm(a * a, 4)} : {fm(b * b, 4)}; Volume ratio = {fm(a ** 3, 4)} : {fm(b ** 3, 4)}")
        known = num(d.get("val"), "", True)
        kk = d.get("what", "area")
        res = f"Area ratio {fm(a * a, 4)} : {fm(b * b, 4)}, volume ratio {fm(a ** 3, 4)} : {fm(b ** 3, 4)}"
        if known is not None:
            ex = 2 if kk == "area" else 3
            new = known * Fraction(b) ** ex / Fraction(a) ** ex
            steps.append(f"The {kk} of the first figure is {fm(known, 4)}. {kk.title()} of second = {fm(known, 4)} &times; {FR(fm(b ** ex, 4), fm(a ** ex, 4))} = {HL_(fm(new, 4))}")
            res += f"; second {kk} = {fm(new, 4)}"
        return _ok(steps, f"<b>{res}</b>")
    if kind == "areas":
        A1, A2 = pos(d.get("a1"), "the first area"), pos(d.get("a2"), "the second area")
        rr = float(A2 / A1) ** 0.5
        steps.append(f"Area ratio = {fm(A1, 4)} : {fm(A2, 4)} = 1 : {fm(A2 / A1, 4)}")
        steps.append(f"Length ratio = square root of the area ratio = 1 : &radic;{fm(A2 / A1, 4)} = 1 : {rr:.4g}")
        steps.append(f"Volume ratio = cube of the length ratio = 1 : {rr ** 3:.4g}")
        return _ok(steps, f"<b>Length ratio 1 : {rr:.4g}; volume ratio 1 : {rr ** 3:.4g}</b>")
    V1, V2 = pos(d.get("a1"), "the first volume"), pos(d.get("a2"), "the second volume")
    rr = float(V2 / V1) ** (1 / 3)
    steps.append(f"Volume ratio = {fm(V1, 4)} : {fm(V2, 4)} = 1 : {fm(V2 / V1, 4)}")
    steps.append(f"Length ratio = cube root of the volume ratio = 1 : {rr:.4g}")
    steps.append(f"Area ratio = square of the length ratio = 1 : {rr ** 2:.4g}")
    return _ok(steps, f"<b>Length ratio 1 : {rr:.4g}; area ratio 1 : {rr ** 2:.4g}</b>")


def _ratio2(s):
    import re
    parts = [p for p in re.split(r"\s*[:;,]\s*", (s or "").strip()) if p]
    if len(parts) != 2:
        raise UErr("Write the ratio as two numbers with a colon, like 2:3.")
    a, b = num(parts[0], "a ratio term"), num(parts[1], "a ratio term")
    if a <= 0 or b <= 0:
        raise UErr("Ratio terms must be bigger than 0.")
    return a, b


# ----------------------------------------------------------------------- spec ---

def _pi():
    return select("pi", "Value of &pi;", PI_OPTS)


_THM = [("centre", "Angle at the centre = 2 &times; angle at the circumference"), ("same", "Angles in the same segment are equal"),
        ("semi", "Angle in a semicircle = 90&deg;"), ("cyclic", "Cyclic quadrilateral"), ("alt", "Alternate segment (tangent &amp; chord)"),
        ("tangents", "Two tangents from a point (angles)"), ("tanlen", "Length of a tangent (Pythagoras)"),
        ("chord", "Chord and perpendicular from the centre"), ("inter", "Intersecting chords"), ("tansec", "Tangent and secant lengths")]

SPEC = {
    "title": "Circle Theorems & Mensuration",
    "intro": "Circle theorems drawn with diagrams, plus circles, sectors, solids and similar figures.",
    "tabs": [
        {"id": "cth", "label": "Circle theorems", "title": "Circle theorems", "endpoint": "theorem",
         "fields": [select("thm", "Theorem", _THM, wide=True),
                    select("which", "Which angle do you know?", [("circ", "the angle at the circumference"), ("centre", "the angle at the centre")], show_if={"thm": "centre"}),
                    select("which", "What do you know?", [("opp", "one angle (find the opposite angle)"), ("ext", "an exterior angle (find the interior opposite angle)")], show_if={"thm": "cyclic"}),
                    field("v", "The angle (degrees)", "40", show_if={"thm": ["centre", "same", "semi", "cyclic", "alt", "tangents"]}),
                    field("r", "Radius", "5", show_if={"thm": ["tanlen", "chord"]}),
                    field("op", "Distance OP (centre to the outside point)", "13", show_if={"thm": "tanlen"}),
                    select("find", "Find", [("chord", "the chord length (know distance from centre)"), ("dist", "the distance from the centre (know chord)")], show_if={"thm": "chord"}),
                    field("x", "The known length", "3", show_if={"thm": "chord"}),
                    field("ax", "AX", "4", show_if={"thm": "inter"}), field("xb", "XB", "6", show_if={"thm": "inter"}),
                    field("cx", "CX", "3", show_if={"thm": "inter"}), field("xd", "XD (leave one empty)", "", show_if={"thm": "inter"}),
                    field("pt", "PT (tangent)", "", show_if={"thm": "tansec"}), field("pa", "PA", "4", show_if={"thm": "tansec"}),
                    field("pb", "PB", "9", show_if={"thm": "tansec"})]},
        {"id": "cci", "label": "Circles", "title": "Circumference and area", "endpoint": "circle",
         "fields": [select("kind", "I know the", [("r", "radius"), ("d", "diameter"), ("C", "circumference"), ("A", "area")]),
                    field("x", "Value", "7"), _pi()]},
        {"id": "cse", "label": "Arcs, sectors, segments", "title": "Arc length, sector and segment", "endpoint": "sector",
         "fields": [select("kind", "Find", [("all", "arc length, sector area and perimeter"), ("seg", "segment area and chord length"),
                                            ("arc_angle", "the angle from the arc length"), ("area_angle", "the angle from the sector area"),
                                            ("cone", "cone made by rolling up a sector")], wide=True),
                    field("r", "Radius", "7"), field("th", "Angle &theta; (degrees)", "90", show_if={"kind": ["all", "seg", "cone"]}),
                    field("v", "The arc length / sector area", "11", show_if={"kind": ["arc_angle", "area_angle"]}), _pi()]},
        {"id": "cso", "label": "Solids", "title": "Volume and surface area of solids", "endpoint": "solids",
         "fields": [select("solid", "Solid", [("cuboid", "cuboid"), ("cube", "cube"), ("cylinder", "cylinder"), ("cone", "cone"), ("sphere", "sphere"),
                                              ("hemi", "hemisphere"), ("pyramid", "rectangular pyramid"), ("prism", "triangular prism"), ("frustum", "frustum of a cone")], wide=True),
                    field("l", "Length (or side of cube)", "6", show_if={"solid": ["cuboid", "cube", "pyramid"]}),
                    field("w", "Width", "4", show_if={"solid": ["cuboid", "pyramid"]}),
                    field("r", "Radius", "7", show_if={"solid": ["cylinder", "cone", "sphere", "hemi", "frustum"]}),
                    field("R", "Big radius R", "10", show_if={"solid": "frustum"}),
                    field("h", "Height", "10", show_if={"solid": ["cuboid", "cylinder", "cone", "pyramid", "frustum"]}),
                    field("sl", "OR slant height (cone, if no height)", "", show_if={"solid": "cone"}),
                    field("a", "Triangle side a", "3", show_if={"solid": "prism"}), field("b", "Triangle side b", "4", show_if={"solid": "prism"}),
                    field("c", "Triangle side c", "5", show_if={"solid": "prism"}), field("L", "Length of prism", "10", show_if={"solid": "prism"}),
                    _pi()]},
        {"id": "cin", "label": "Find a missing dimension", "title": "Find the radius, height or side from a volume", "endpoint": "inverse",
         "fields": [select("solid", "Find", [("cyl_h", "cylinder: height"), ("cyl_r", "cylinder: radius"), ("cone_h", "cone: height"), ("cone_r", "cone: radius"),
                                             ("sph_r", "sphere: radius"), ("cube_s", "cube: side")], wide=True),
                    field("V", "Volume", "770"), field("k", "The other known length (radius or height)", "5", show_if={"solid": ["cyl_h", "cyl_r", "cone_h", "cone_r"]}), _pi()]},
        {"id": "csi", "label": "Similar figures", "title": "Similar figures: length, area and volume ratios", "endpoint": "similar",
         "fields": [select("kind", "I know the ratio of", [("lengths", "lengths (find area and volume ratios)"), ("areas", "areas"), ("volumes", "volumes")], wide=True),
                    field("r", "Length ratio first:second", "2:3", show_if={"kind": "lengths"}),
                    select("what", "A known quantity of the first figure", [("area", "area"), ("volume", "volume")], show_if={"kind": "lengths"}),
                    field("val", "Its value (optional)", "20", show_if={"kind": "lengths"}),
                    field("a1", "First", "9", show_if={"kind": ["areas", "volumes"]}), field("a2", "Second", "16", show_if={"kind": ["areas", "volumes"]})]},
    ],
}

topics.register("circles", SPEC, {"theorem": theorem, "circle": circle, "sector": sector, "solids": solids, "inverse": solid_inverse, "similar": similar})
