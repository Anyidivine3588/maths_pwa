"""Constructions and loci with drawings (matplotlib)."""
import base64
import io
import math
import topics
from tcommon import field, select, guard, UErr, num, pos, fm, fr, FR, esc, _ok, _fail
import numpy as np

DEG = "&deg;"
HL = lambda s: f"<span class='hl'>{s}</span>"
CON = "#94a3b8"      # construction lines
MAIN = "#1d4ed8"
RED = "#dc2626"


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


def _ax(w=6.4, h=5.4):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def arc(ax, c, r, a1, a2, color=CON, lw=1.2, ls="-"):
    t = np.radians(np.linspace(a1, a2, 80))
    ax.plot(c[0] + r * np.cos(t), c[1] + r * np.sin(t), color=color, lw=lw, ls=ls)


def cut(ax, c, r, ang, span=9, color=CON):
    arc(ax, c, r, ang - span, ang + span, color)


def line(ax, p, q, color=MAIN, lw=2.2, ls="-"):
    ax.plot([p[0], q[0]], [p[1], q[1]], color=color, lw=lw, ls=ls)


def pt(ax, p, name, dx=0.12, dy=0.12, color="#0f172a"):
    ax.plot([p[0]], [p[1]], "o", color=color, ms=5, zorder=5)
    if name:
        ax.text(p[0] + dx, p[1] + dy, name, fontsize=13, fontweight="bold", color=color)


def angle_mark(ax, v, a1, a2, text, r=0.7, color=RED):
    arc(ax, v, r, a1, a2, color, 2.2)
    m = math.radians((a1 + a2) / 2)
    ax.text(v[0] + (r + 0.35) * math.cos(m), v[1] + (r + 0.35) * math.sin(m), text.replace("&deg;", "°"), color=color, fontsize=11, fontweight="bold", ha="center", va="center")


def right_mark(ax, v, d1, d2, s=0.22):
    a = (v[0] + d1[0] * s, v[1] + d1[1] * s)
    c = (v[0] + d2[0] * s, v[1] + d2[1] * s)
    b = (a[0] + d2[0] * s, a[1] + d2[1] * s)
    ax.plot([a[0], b[0], c[0]], [a[1], b[1], c[1]], color=RED, lw=1.8)


def _fin(ax, pad=0.8):
    ax.autoscale()
    ax.margins(0.08)


def N(v, label):
    x = num(v, label)
    return x


def P(v, label, hi=1000):
    x = pos(v, label)
    if x > hi:
        raise UErr(f"{label} is too large.")
    return float(x)


def ang(v, label, lo=0, hi=180):
    x = float(num(v, label))
    if not (lo < x < hi):
        raise UErr(f"{label} must be between {lo} and {hi} degrees.")
    return x


# ================================================================ constructions =

def tri_sss(a, b, c):
    if a + b <= c or a + c <= b or b + c <= a:
        raise UErr("Those three sides cannot make a triangle: the two shorter sides must add up to MORE than the longest side.")
    x = (b * b + c * c - a * a) / (2 * c)
    y = math.sqrt(max(b * b - x * x, 0))
    return (0, 0), (c, 0), (x, y)


def tri_angles(A, B, C):
    def ang_(p, q, r):
        v1 = (q[0] - p[0], q[1] - p[1])
        v2 = (r[0] - p[0], r[1] - p[1])
        return math.degrees(math.acos(max(-1, min(1, (v1[0] * v2[0] + v1[1] * v2[1]) / (math.hypot(*v1) * math.hypot(*v2))))))
    return ang_(A, B, C), ang_(B, A, C), ang_(C, A, B)


def _label_sides(ax, A, B, C, a=None, b=None, c=None):
    for p, q, t in ((B, C, a), (A, C, b), (A, B, c)):
        if t is not None:
            ax.text((p[0] + q[0]) / 2 - 0.1, (p[1] + q[1]) / 2 + 0.12, f"{t:g} cm", fontsize=10, color="#334155")


@guard
def construct(d):
    k = d.get("kind", "sss")
    steps = []
    fig, ax = _ax()
    if k == "sss":
        a, b, c = P(d.get("a"), "side a (BC)"), P(d.get("b"), "side b (CA)"), P(d.get("c"), "side c (AB)")
        A, B, C = tri_sss(a, b, c)
        steps.append(f"<b>Construct triangle ABC</b> with AB = {c:g} cm, BC = {a:g} cm, CA = {b:g} cm (three sides: SSS). Tools: ruler (cm scale), pair of compasses, pencil.")
        steps.append(f"<b>Step 1.</b> Draw a straight line and mark A. Using the ruler, measure {c:g} cm from A and mark B.")
        steps.append(f"<b>Step 2.</b> Open the compasses to <b>{b:g} cm</b>. Put the point on <b>A</b> and draw an arc above AB.")
        steps.append(f"<b>Step 3.</b> Open the compasses to <b>{a:g} cm</b>. Put the point on <b>B</b> and draw an arc that crosses the first arc. Mark the crossing as <b>C</b>.")
        steps.append("<b>Step 4.</b> Join A to C and B to C with the ruler. Do <b>not</b> rub out the arcs: they show your method.")
        angA, angB, angC = tri_angles(A, B, C)
        for cen, r, t0 in ((A, b, math.degrees(math.atan2(C[1], C[0]))), (B, a, math.degrees(math.atan2(C[1], C[0] - c)))):
            arc(ax, cen, r, t0 - 14, t0 + 14)
        for p, n, dx, dy in ((A, "A", -0.3, -0.3), (B, "B", 0.1, -0.3), (C, "C", 0.0, 0.15)):
            pt(ax, p, n, dx, dy)
        line(ax, A, B)
        line(ax, A, C)
        line(ax, B, C)
        _label_sides(ax, A, B, C, a, b, c)
        s = (a + b + c) / 2
        area = math.sqrt(s * (s - a) * (s - b) * (s - c))
        res = f"Angles: A = {angA:.1f}&deg;, B = {angB:.1f}&deg;, C = {angC:.1f}&deg; (use these to check your protractor reading). Area = {area:.2f} cm&sup2;"
    elif k == "sas":
        b, c = P(d.get("b"), "side b (AC)"), P(d.get("c"), "side c (AB)")
        th = ang(d.get("th"), "the angle at A")
        A, B = (0, 0), (c, 0)
        C = (b * math.cos(math.radians(th)), b * math.sin(math.radians(th)))
        a = math.hypot(C[0] - B[0], C[1] - B[1])
        steps.append(f"<b>Construct triangle ABC</b> with AB = {c:g} cm, angle BAC = {th:g}&deg;, AC = {b:g} cm (two sides and the angle <i>between</i> them: SAS). Tools: ruler, protractor.")
        steps.append(f"<b>Step 1.</b> Draw AB = {c:g} cm.")
        steps.append(f"<b>Step 2.</b> Put the protractor's centre on A with its base line along AB. Mark a dot at {th:g}&deg; (read from the scale that starts at 0 on AB). Draw a long faint line from A through the dot.")
        steps.append(f"<b>Step 3.</b> Measure {b:g} cm along that line from A and mark <b>C</b>.")
        steps.append("<b>Step 4.</b> Join B to C. The triangle is complete.")
        line(ax, A, B)
        line(ax, A, C)
        line(ax, B, C)
        for p, n, dx, dy in ((A, "A", -0.3, -0.3), (B, "B", 0.1, -0.3), (C, "C", 0.0, 0.15)):
            pt(ax, p, n, dx, dy)
        angle_mark(ax, A, 0, th, f"{th:g}°", r=min(b, c) * 0.25)
        _label_sides(ax, A, B, C, None, b, c)
        angA, angB, angC = tri_angles(A, B, C)
        res = f"BC = {a:.2f} cm (cosine rule); angles B = {angB:.1f}&deg;, C = {angC:.1f}&deg;"
    elif k == "asa":
        c = P(d.get("c"), "side c (AB)")
        al, be = ang(d.get("al"), "angle A"), ang(d.get("be"), "angle B")
        if al + be >= 180:
            raise UErr("The two angles must add up to less than 180 degrees.")
        ga = 180 - al - be
        b = c * math.sin(math.radians(be)) / math.sin(math.radians(ga))
        A, B = (0, 0), (c, 0)
        C = (b * math.cos(math.radians(al)), b * math.sin(math.radians(al)))
        steps.append(f"<b>Construct triangle ABC</b> with AB = {c:g} cm, angle A = {al:g}&deg;, angle B = {be:g}&deg; (two angles and a side: ASA).")
        steps.append(f"<b>Step 1.</b> Draw AB = {c:g} cm.")
        steps.append(f"<b>Step 2.</b> At A, use the protractor to mark {al:g}&deg; from AB (above the line) and draw a long faint line from A.")
        steps.append(f"<b>Step 3.</b> At B, use the protractor to mark {be:g}&deg; from BA (on the same side) and draw a long faint line from B (measure from the BA side, so read the scale that starts at 0 on BA).")
        steps.append("<b>Step 4.</b> Where the two lines cross is <b>C</b>. Angle C = 180&deg; &minus; " + f"{al:g}&deg; &minus; {be:g}&deg; = {ga:g}&deg;.")
        line(ax, A, B)
        line(ax, A, C)
        line(ax, B, C)
        for p, n, dx, dy in ((A, "A", -0.3, -0.3), (B, "B", 0.1, -0.3), (C, "C", 0.0, 0.15)):
            pt(ax, p, n, dx, dy)
        r_ = c * 0.18
        angle_mark(ax, A, 0, al, f"{al:g}°", r=r_)
        angle_mark(ax, B, 180 - be, 180, f"{be:g}°", r=r_)
        res = f"AC = {b:.2f} cm, BC = {c * math.sin(math.radians(al)) / math.sin(math.radians(ga)):.2f} cm, angle C = {ga:g}&deg;"
    elif k == "perp":
        L = P(d.get("L"), "the length of AB")
        A, B = (0, 0), (L, 0)
        R = 0.65 * L
        h = math.sqrt(R * R - L * L / 4)
        steps.append(f"<b>Construct the perpendicular bisector of AB</b> (AB = {L:g} cm). It is the line that cuts AB in half at right angles, and every point on it is the same distance from A and from B.")
        steps.append(f"<b>Step 1.</b> Draw AB = {L:g} cm.")
        steps.append(f"<b>Step 2.</b> Open the compasses to MORE than half of AB (for example {R:.1f} cm). With the point on <b>A</b>, draw one arc above AB and one arc below AB.")
        steps.append("<b>Step 3.</b> Keep the SAME compass opening. With the point on <b>B</b>, draw two arcs that cross the first two arcs.")
        steps.append("<b>Step 4.</b> Join the two crossing points with a ruler. This line is the perpendicular bisector. It meets AB at its midpoint M, so AM = MB = " + f"{L / 2:g} cm.")
        arc(ax, A, R, -50, 50)
        arc(ax, B, R, 130, 230)
        line(ax, A, B)
        line(ax, (L / 2, h * 1.25), (L / 2, -h * 1.25), color=RED)
        pt(ax, A, "A", -0.3, -0.3)
        pt(ax, B, "B", 0.1, -0.3)
        pt(ax, (L / 2, 0), "M", 0.1, -0.3)
        pt(ax, (L / 2, h), "", 0, 0)
        pt(ax, (L / 2, -h), "", 0, 0)
        right_mark(ax, (L / 2, 0), (1, 0), (0, 1), s=L * 0.06)
        res = f"The perpendicular bisector passes through the midpoint M of AB, {L / 2:g} cm from each end."
    elif k == "bisect":
        th = ang(d.get("th"), "the angle", 0, 180)
        O = (0, 0)
        r = 1.6
        L = 5.0
        steps.append(f"<b>Bisect an angle of {th:g}&deg;</b> (cut it exactly in half, giving two angles of {th / 2:g}&deg;).")
        steps.append(f"<b>Step 1.</b> Draw the angle {th:g}&deg; with the protractor, with vertex O.")
        steps.append("<b>Step 2.</b> Put the compass point on <b>O</b> and draw an arc that crosses both arms. Call the crossing points P and Q.")
        steps.append("<b>Step 3.</b> Put the compass point on <b>P</b> and draw an arc between the arms (any opening bigger than half of PQ). Keep the SAME opening, put the point on <b>Q</b> and draw another arc that crosses it. Call the crossing R.")
        steps.append(f"<b>Step 4.</b> Draw a straight line from O through R. This is the bisector; each half angle = {th:g}&deg; &divide; 2 = {HL(f'{th / 2:g}&deg;')}.")
        Pp = (r, 0)
        Q = (r * math.cos(math.radians(th)), r * math.sin(math.radians(th)))
        rho = r * (math.sin(math.radians(th / 2)) + 0.4)
        dd = r * math.cos(math.radians(th / 2)) + math.sqrt(rho ** 2 - (r * math.sin(math.radians(th / 2))) ** 2)
        Rr = (dd * math.cos(math.radians(th / 2)), dd * math.sin(math.radians(th / 2)))
        line(ax, O, (L, 0))
        line(ax, O, (L * math.cos(math.radians(th)), L * math.sin(math.radians(th))))
        arc(ax, O, r, -5, th + 5)
        a_p = math.degrees(math.atan2(Rr[1] - Pp[1], Rr[0] - Pp[0]))
        a_q = math.degrees(math.atan2(Rr[1] - Q[1], Rr[0] - Q[0]))
        arc(ax, Pp, rho, a_p - 14, a_p + 14)
        arc(ax, Q, rho, a_q - 14, a_q + 14)
        line(ax, O, (L * 0.9 * math.cos(math.radians(th / 2)), L * 0.9 * math.sin(math.radians(th / 2))), color=RED)
        pt(ax, O, "O", -0.35, -0.3)
        pt(ax, Pp, "P", 0.05, -0.35)
        pt(ax, Q, "Q", -0.4, 0.1)
        pt(ax, Rr, "R", 0.1, 0.05)
        angle_mark(ax, O, 0, th / 2, f"{th / 2:g}°", r=0.7, color=RED)
        angle_mark(ax, O, th / 2, th, f"{th / 2:g}°", r=0.7, color=RED)
        res = f"The bisector makes two angles of {th / 2:g}&deg;."
    elif k == "angle":
        t = int(float(d.get("std", "60")))
        O = (0, 0)
        r = 2.0
        L = 6.0
        line(ax, O, (L, 0))
        pt(ax, O, "O", -0.35, -0.3)
        arc(ax, O, r, -5, 100 if t in (15, 30, 60) else 185)
        pt(ax, (r, 0), "P", 0.05, -0.35)
        bis = lambda a1, a2: (a1 + a2) / 2

        def bisect_pts(a1, a2):
            """draw bisector arcs between points at angles a1,a2 on circle r; return point on bisector"""
            half = math.radians((a2 - a1) / 2)
            rho = r * (math.sin(half) + 0.45)
            dd = r * math.cos(half) + math.sqrt(rho ** 2 - (r * math.sin(half)) ** 2)
            mid = math.radians((a1 + a2) / 2)
            R_ = (dd * math.cos(mid), dd * math.sin(mid))
            for aa in (a1, a2):
                c0 = (r * math.cos(math.radians(aa)), r * math.sin(math.radians(aa)))
                an = math.degrees(math.atan2(R_[1] - c0[1], R_[0] - c0[0]))
                arc(ax, c0, rho, an - 14, an + 14)
            return R_

        def step_off(base_ang, new_ang, name):
            c0 = (r * math.cos(math.radians(base_ang)), r * math.sin(math.radians(base_ang)))
            cut(ax, c0, r, new_ang, 14)
            q = (r * math.cos(math.radians(new_ang)), r * math.sin(math.radians(new_ang)))
            pt(ax, q, name, 0.08, 0.1)
            return q

        S60 = ("<b>To make 60&deg;:</b> keep the compasses at the same opening (say 4 cm... any radius). Put the point on O and draw an arc crossing the line at P. Without changing the opening, put the point on P and draw an arc crossing the first arc at Q. Join O to Q: angle POQ = 60&deg; (triangle OPQ is equilateral).")
        if t == 60:
            steps.append(S60)
            q = step_off(0, 60, "Q")
            final = 60
        elif t == 120:
            steps += [S60, "<b>Then</b> keep the same opening, put the point on Q and draw an arc crossing the big arc at R. Angle POR = 60&deg; + 60&deg; = <b>120&deg;</b>."]
            step_off(0, 60, "Q")
            step_off(60, 120, "R")
            final = 120
        elif t == 90:
            steps += ["<b>To make 90&deg;:</b> first make 60&deg; and 120&deg; (steps stated above): arc from P cuts at Q (60&deg;); arc from Q cuts at R (120&deg;).",
                      "Now <b>bisect</b> angle QOR: with the same opening, put the point on Q, then on R, and draw arcs that cross at S. Join O to S: angle POS = 60&deg; + 30&deg; = <b>90&deg;</b>."]
            step_off(0, 60, "Q")
            step_off(60, 120, "R")
            R_ = bisect_pts(60, 120)
            pt(ax, R_, "S", 0.08, 0.05)
            final = 90
        elif t == 30:
            steps += [S60, "Now <b>bisect</b> angle POQ (see the bisecting method: arcs from P and from Q cross at R). Angle POR = 60&deg; &divide; 2 = <b>30&deg;</b>."]
            step_off(0, 60, "Q")
            R_ = bisect_pts(0, 60)
            pt(ax, R_, "R", 0.08, 0.05)
            final = 30
        elif t == 45:
            steps += ["<b>To make 45&deg;:</b> first construct 90&deg; (via 60&deg; and 120&deg;, then bisect QOR to get S).", "Then <b>bisect</b> the 90&deg; angle POS: arcs from P and S cross at T. Angle POT = <b>45&deg;</b>."]
            step_off(0, 60, "Q")
            step_off(60, 120, "R")
            S_ = bisect_pts(60, 120)
            Sp = (r * math.cos(math.radians(90)), r * math.sin(math.radians(90)))
            pt(ax, Sp, "S", -0.35, 0.05)
            R2 = bisect_pts(0, 90)
            pt(ax, R2, "T", 0.08, 0.05)
            final = 45
        elif t == 150:
            steps += ["<b>To make 150&deg;:</b> make 90&deg; (via 60&deg;, 120&deg; and the bisector, giving S).", "Put the compass point on S (same opening) and draw an arc crossing the big arc at U. Angle POU = 90&deg; + 60&deg; = <b>150&deg;</b>."]
            step_off(0, 60, "Q")
            step_off(60, 120, "R")
            bisect_pts(60, 120)
            step_off(90, 150, "U")
            final = 150
        elif t == 75:
            steps += ["<b>To make 75&deg;:</b> first make 150&deg; (60&deg; + 90&deg;, see above).", "Then <b>bisect</b> the 150&deg; angle: arcs from P and U cross at V. Angle POV = 150&deg; &divide; 2 = <b>75&deg;</b>."]
            step_off(0, 60, "Q")
            step_off(60, 120, "R")
            bisect_pts(60, 120)
            step_off(90, 150, "U")
            V = bisect_pts(0, 150)
            pt(ax, V, "V", 0.08, 0.05)
            final = 75
        elif t == 105:
            steps += ["<b>To make 105&deg;:</b> make 60&deg; and 150&deg; (see above), then <b>bisect</b> the angle between them: (60&deg; + 150&deg;) &divide; 2 = <b>105&deg;</b>."]
            step_off(0, 60, "Q")
            step_off(60, 120, "R")
            bisect_pts(60, 120)
            step_off(90, 150, "U")
            V = bisect_pts(60, 150)
            pt(ax, V, "W", 0.08, 0.05)
            final = 105
        elif t == 135:
            steps += ["<b>To make 135&deg;:</b> extend PO backwards to make a straight line (180&deg;). Make 90&deg; as above. <b>Bisect</b> the right angle between OS (90&deg;) and the extended line (180&deg;): the bisector is at 135&deg;."]
            step_off(0, 60, "Q")
            step_off(60, 120, "R")
            bisect_pts(60, 120)
            line(ax, O, (-L, 0), ls="--")
            R2 = bisect_pts(90, 180)
            pt(ax, R2, "X", 0.08, 0.05)
            final = 135
        elif t == 15:
            steps += ["<b>To make 15&deg;:</b> make 30&deg; (by bisecting 60&deg;), then bisect it again: 30&deg; &divide; 2 = <b>15&deg;</b>."]
            step_off(0, 60, "Q")
            bisect_pts(0, 60)
            R2 = bisect_pts(0, 30)
            pt(ax, R2, "Y", 0.08, 0.05)
            final = 15
        else:
            raise UErr("Choose one of the listed angles.")
        end = (L * math.cos(math.radians(final)), L * math.sin(math.radians(final)))
        line(ax, O, end, color=RED)
        angle_mark(ax, O, 0, final, f"{final}°", r=0.8)
        res = f"Angle {final}&deg; constructed with compasses only (check with a protractor)."
    elif k == "perpfrom":
        h = P(d.get("h"), "the distance of P from the line")
        Pp = (0, h)
        rho = 1.5 * h
        x1 = math.sqrt(rho * rho - h * h)
        X, Y = (-x1, 0), (x1, 0)
        steps.append(f"<b>Drop a perpendicular from a point P to a line</b> (P is {h:g} cm above the line).")
        steps.append(f"<b>Step 1.</b> Put the compass point on <b>P</b>. Open it wide enough (more than {h:g} cm) so that the arc cuts the line twice. Draw the arc and label the crossings <b>X</b> and <b>Y</b>.")
        steps.append("<b>Step 2.</b> Put the point on <b>X</b> and draw an arc BELOW the line. Keep the same opening, put the point on <b>Y</b> and draw an arc that crosses it at Z.")
        steps.append("<b>Step 3.</b> Join P to Z with a ruler. It meets the line at F at 90&deg;. PF is the shortest distance from P to the line, " + f"{h:g} cm.")
        line(ax, (-2.2 * x1, 0), (2.2 * x1, 0))
        arc(ax, Pp, rho, 250, 290)
        arc(ax, X, rho, -75, -35)
        arc(ax, Y, rho, 215, 255)
        Z = (0, -h)
        line(ax, Pp, Z, color=RED)
        pt(ax, Pp, "P", 0.1, 0.1)
        pt(ax, X, "X", -0.3, 0.1)
        pt(ax, Y, "Y", 0.1, 0.1)
        pt(ax, Z, "Z", 0.1, -0.3)
        pt(ax, (0, 0), "F", 0.1, 0.12)
        right_mark(ax, (0, 0), (1, 0), (0, 1), s=h * 0.12)
        res = f"PF = {h:g} cm and is at 90&deg; to the line."
    elif k == "hexagon":
        r = P(d.get("r"), "the radius")
        steps.append(f"<b>Construct a regular hexagon</b> inside a circle of radius {r:g} cm.")
        steps.append(f"<b>Step 1.</b> Draw a circle with centre O and radius {r:g} cm. Mark a point A on the circle.")
        steps.append(f"<b>Step 2.</b> Keep the compasses at {r:g} cm (the radius!). Put the point on A and mark B on the circle. Put the point on B and mark C, and so on round the circle until you have six points A, B, C, D, E, F.")
        steps.append(f"<b>Step 3.</b> Join the six points in order. Each side = {r:g} cm (the radius) and each interior angle = 120&deg;.")
        t = np.radians(np.linspace(0, 360, 200))
        ax.plot(r * np.cos(t), r * np.sin(t), color=CON, lw=1.2)
        pts = [(r * math.cos(math.radians(60 * i)), r * math.sin(math.radians(60 * i))) for i in range(6)]
        for i, p in enumerate(pts):
            line(ax, p, pts[(i + 1) % 6])
            pt(ax, p, "ABCDEF"[i], p[0] * 0.12 / r, p[1] * 0.12 / r)
            cut(ax, p, r, math.degrees(math.atan2(pts[(i + 1) % 6][1] - p[1], pts[(i + 1) % 6][0] - p[0])) - 0, 6)
        pt(ax, (0, 0), "O", 0.05, -0.2 * r / 3)
        res = f"Each side = {r:g} cm; perimeter = {6 * r:g} cm; area = {3 * math.sqrt(3) / 2 * r * r:.2f} cm&sup2;."
    else:
        raise UErr("Choose a construction.")
    _fin(ax)
    return _ok(steps, {"image": _b64(fig), "text": f"<b>{res}</b>"})


# ====================================================================== loci ====

@guard
def loci(d):
    k = d.get("kind", "circle")
    steps = []
    fig, ax = _ax()
    if k == "circle":
        r = P(d.get("r"), "the distance")
        steps.append("<b>Locus</b> means 'the set of all points that obey a rule'. Here the rule is: <b>a fixed distance from a point O</b>.")
        steps.append(f"<b>Answer:</b> a <b>circle</b> with centre O and radius {r:g} cm. To draw it: set the compasses to {r:g} cm, put the point on O and draw a full circle.")
        steps.append(f"Points <b>inside</b> the circle are less than {r:g} cm from O; points <b>outside</b> are more than {r:g} cm away.")
        t = np.radians(np.linspace(0, 360, 300))
        ax.fill(r * np.cos(t), r * np.sin(t), color="#bfdbfe", alpha=.5)
        ax.plot(r * np.cos(t), r * np.sin(t), color=MAIN, lw=2.4)
        pt(ax, (0, 0), "O", 0.1, 0.1)
        ax.text(r / 2 * 0.8, 0.12, f"{r:g} cm", fontsize=10)
        line(ax, (0, 0), (r, 0), color=RED, lw=1.5)
        res = f"The locus is a circle, radius {r:g} cm."
    elif k == "perp":
        L = P(d.get("L"), "the distance AB")
        steps.append("<b>Rule:</b> points that are the <b>same distance from A and from B</b> (equidistant).")
        steps.append(f"<b>Answer:</b> the <b>perpendicular bisector</b> of AB. Draw AB = {L:g} cm, then construct its perpendicular bisector (arcs of equal radius, more than {L / 2:g} cm, from A and from B; join the crossings).")
        steps.append("Points on A's side of the line are <b>nearer to A</b>; points on B's side are nearer to B.")
        A, B = (0, 0), (L, 0)
        line(ax, A, B, color=CON, lw=1.5)
        line(ax, (L / 2, -L * 0.8), (L / 2, L * 0.8), color=MAIN)
        ax.fill([-L * 0.5, L / 2, L / 2, -L * 0.5], [-L * 0.8, -L * 0.8, L * 0.8, L * 0.8], color="#bfdbfe", alpha=.45)
        pt(ax, A, "A", -0.3, -0.3)
        pt(ax, B, "B", 0.1, -0.3)
        ax.text(-L * 0.35, L * 0.7, "nearer A", fontsize=10)
        ax.text(L * 0.62, L * 0.7, "nearer B", fontsize=10)
        res = "The locus is the perpendicular bisector of AB."
    elif k == "band":
        L = P(d.get("L"), "the length of AB")
        r = P(d.get("r"), "the distance")
        steps.append(f"<b>Rule:</b> points that are <b>{r:g} cm from the line segment AB</b> (AB = {L:g} cm).")
        steps.append(f"<b>Answer:</b> a 'running-track' (stadium) shape: two straight lines {r:g} cm from AB (parallel to it, one each side) joined by two semicircles of radius {r:g} cm centred on A and on B.")
        steps.append(f"To draw: draw AB; use the compasses to mark {r:g} cm above and below at each end (perpendiculars); draw the parallels; then draw a semicircle at each end, centre A and centre B, radius {r:g} cm.")
        t = np.radians(np.linspace(90, 270, 100))
        left = (-r * -np.cos(t) * 0 + (r * np.cos(t)), r * np.sin(t))
        xs = list(r * np.cos(np.radians(np.linspace(-90, 90, 100))) + L) + list(r * np.cos(np.radians(np.linspace(90, 270, 100))))
        ys = list(r * np.sin(np.radians(np.linspace(-90, 90, 100)))) + list(r * np.sin(np.radians(np.linspace(90, 270, 100))))
        ax.fill(xs, ys, color="#bfdbfe", alpha=.5)
        ax.plot(xs + [xs[0]], ys + [ys[0]], color=MAIN, lw=2.4)
        line(ax, (0, 0), (L, 0), color=RED, lw=2)
        pt(ax, (0, 0), "A", -0.3, -0.35)
        pt(ax, (L, 0), "B", 0.1, -0.35)
        res = f"The locus (boundary) is a stadium shape {r:g} cm from AB; the area inside is {2 * r * L + math.pi * r * r:.2f} cm&sup2; for those within {r:g} cm."
    elif k == "anglebis":
        th = ang(d.get("th"), "the angle between the lines")
        steps.append(f"<b>Rule:</b> points that are the <b>same distance from two lines</b> that meet at an angle of {th:g}&deg;.")
        steps.append(f"<b>Answer:</b> the <b>angle bisector</b> of the angle between the lines: a line through the meeting point that splits the angle into two angles of {th / 2:g}&deg;. (The other pair of angles also has a bisector, at right angles to the first.)")
        steps.append("Method: bisect the angle with compasses (arc from the vertex cutting both lines, then equal arcs from those two points crossing).")
        L = 5
        for a_ in (0, th):
            line(ax, (-L * math.cos(math.radians(a_)), -L * math.sin(math.radians(a_))), (L * math.cos(math.radians(a_)), L * math.sin(math.radians(a_))), color=CON, lw=1.8)
        for m_ in (th / 2, th / 2 + 90):
            line(ax, (-L * math.cos(math.radians(m_)), -L * math.sin(math.radians(m_))), (L * math.cos(math.radians(m_)), L * math.sin(math.radians(m_))), color=MAIN, ls="--" if m_ > th / 2 else "-")
        pt(ax, (0, 0), "O", 0.1, -0.35)
        angle_mark(ax, (0, 0), 0, th / 2, f"{th / 2:g}°", r=1.2)
        angle_mark(ax, (0, 0), th / 2, th, f"{th / 2:g}°", r=1.2)
        res = f"The locus is the angle bisector: each half is {th / 2:g}&deg;."
    elif k == "combined":
        a, b, c = P(d.get("a"), "side a (BC)"), P(d.get("b"), "side b (CA)"), P(d.get("c"), "side c (AB)")
        A, B, C = tri_sss(a, b, c)
        A, B, C = np.array(A, float), np.array(B, float), np.array(C, float)
        steps.append(f"<b>Step 1 - Draw the triangle</b> ABC with AB = {c:g} cm, BC = {a:g} cm, CA = {b:g} cm (SSS construction with compasses).")
        conds = []
        n = 2
        X, Y = np.meshgrid(np.linspace(min(A[0], B[0], C[0]) - 3, max(A[0], B[0], C[0]) + 3, 700), np.linspace(min(A[1], B[1], C[1]) - 3, max(A[1], B[1], C[1]) + 3, 700))
        mask = np.ones_like(X, dtype=bool)
        draws = []

        def dist_to_line(P1, P2):
            dx, dy = P2 - P1
            return np.abs(dx * (Y - P1[1]) - dy * (X - P1[0])) / math.hypot(dx, dy)
        if d.get("c1", "no") == "yes":
            side = d.get("c1s", "A")
            if side == "A":
                m = (X - A[0]) ** 2 + (Y - A[1]) ** 2 < (X - B[0]) ** 2 + (Y - B[1]) ** 2
            else:
                m = (X - A[0]) ** 2 + (Y - A[1]) ** 2 > (X - B[0]) ** 2 + (Y - B[1]) ** 2
            mask &= m
            steps.append(f"<b>Step {n} - 'Nearer to {side} than to {'B' if side == 'A' else 'A'}':</b> draw the <b>perpendicular bisector of AB</b> (the points equally far from A and B). The wanted side is the side containing {side}.")
            n += 1
            draws.append(("perpAB", None))
        if d.get("c2", "no") == "yes":
            side = d.get("c2s", "AB")
            dAB, dAC = dist_to_line(A, B), dist_to_line(A, C)
            # restrict to the angle at A region: use bisector comparisons
            m = dAB < dAC if side == "AB" else dAB > dAC
            mask &= m
            steps.append(f"<b>Step {n} - 'Nearer to {side} than to {'AC' if side == 'AB' else 'AB'}':</b> draw the <b>bisector of angle A</b> (points equally far from lines AB and AC). The wanted side is the side next to {side}.")
            n += 1
            draws.append(("bisA", None))
        if d.get("c3", "no") == "yes":
            r1 = P(d.get("r1"), "the distance from C")
            mask &= (X - C[0]) ** 2 + (Y - C[1]) ** 2 < r1 * r1
            steps.append(f"<b>Step {n} - 'Within {r1:g} cm of C':</b> draw a <b>circle</b>, centre C, radius {r1:g} cm. The wanted region is INSIDE it.")
            n += 1
            draws.append(("circC", r1))
        if d.get("c4", "no") == "yes":
            r2 = P(d.get("r2"), "the distance from A")
            mask &= (X - A[0]) ** 2 + (Y - A[1]) ** 2 > r2 * r2
            steps.append(f"<b>Step {n} - 'More than {r2:g} cm from A':</b> draw a <b>circle</b>, centre A, radius {r2:g} cm. The wanted region is OUTSIDE it.")
            n += 1
            draws.append(("circA", r2))
        if d.get("c5", "yes") == "yes":
            def side_(P1, P2, Pt):
                return (P2[0] - P1[0]) * (Pt[1] - P1[1]) - (P2[1] - P1[1]) * (Pt[0] - P1[0])
            s1, s2, s3 = side_(A, B, (X, Y)), side_(B, C, (X, Y)), side_(C, A, (X, Y))
            mask &= (s1 >= 0) & (s2 >= 0) & (s3 >= 0)
            steps.append(f"<b>Step {n} - 'Inside the triangle':</b> the region must also lie inside triangle ABC.")
            n += 1
        if len(steps) == 1:
            raise UErr("Choose at least one condition (nearer to ..., within ... of ...).")
        steps.append(f"<b>Step {n} - Shade the region</b> that satisfies ALL the conditions at the same time (where all the wanted sides overlap). Label it R.")
        cell = (X[0, 1] - X[0, 0]) * (Y[1, 0] - Y[0, 0])
        area = float(mask.sum() * cell)
        ax.contourf(X, Y, mask.astype(float), levels=[0.5, 1.5], colors=["#93c5fd"], alpha=0.75)
        for p, q in ((A, B), (B, C), (C, A)):
            line(ax, p, q, color="#334155", lw=2)
        for kk, val in draws:
            if kk == "perpAB":
                mid = (A + B) / 2
                v = B - A
                nrm = np.array([-v[1], v[0]]) / math.hypot(*v)
                line(ax, mid - nrm * 5, mid + nrm * 5, color=RED, lw=1.6, ls="--")
            elif kk == "bisA":
                u1 = (B - A) / np.linalg.norm(B - A)
                u2 = (C - A) / np.linalg.norm(C - A)
                bs = u1 + u2
                bs /= np.linalg.norm(bs)
                line(ax, A, A + bs * (max(a, b, c) * 1.1), color=RED, lw=1.6, ls="--")
            elif kk == "circC":
                arc(ax, C, val, 0, 360, color=RED, lw=1.6, ls="--")
            elif kk == "circA":
                arc(ax, A, val, 0, 360, color=RED, lw=1.6, ls="--")
        pt(ax, tuple(A), "A", -0.3, -0.35)
        pt(ax, tuple(B), "B", 0.1, -0.35)
        pt(ax, tuple(C), "C", 0.0, 0.15)
        ax.set_xlim(X.min(), X.max())
        ax.set_ylim(Y.min(), Y.max())
        if mask.sum() > 50:
            ax.text(float(X[mask].mean()), float(Y[mask].mean()), "R", fontsize=20, fontweight="bold", ha="center", va="center", color="#1e3a8a")
        res = f"Region R found (shaded). Its area is about {area:.2f} cm&sup2;." if mask.sum() > 20 else "No point satisfies all of these conditions together."
    else:
        raise UErr("Choose a type of locus.")
    if k != "combined":
        _fin(ax)
    return _ok(steps, {"image": _b64(fig), "text": f"<b>{res}</b>"})


# ====================================================================== spec ====

def _f(name, label, ph="", **kw):
    return field(name, label, ph, **kw)


SPEC = {
    "title": "Loci & Constructions",
    "intro": "Step-by-step ruler-and-compass constructions and loci, drawn for you with the construction arcs left in.",
    "tabs": [
        {"id": "lc", "label": "Constructions", "title": "Geometrical constructions", "endpoint": "construct",
         "fields": [select("kind", "Construct", [("sss", "triangle from three sides (SSS)"), ("sas", "triangle from two sides and the angle between (SAS)"),
                                                 ("asa", "triangle from two angles and a side (ASA)"), ("perp", "perpendicular bisector of a line"),
                                                 ("bisect", "bisector of an angle"), ("angle", "an angle with compasses (60&deg;, 90&deg;, 45&deg;...)"),
                                                 ("perpfrom", "perpendicular from a point to a line"), ("hexagon", "regular hexagon")], wide=True),
                    _f("a", "Side a = BC (cm)", "5", show_if={"kind": "sss"}), _f("b", "Side b = CA (cm)", "6", show_if={"kind": ["sss", "sas"]}),
                    _f("c", "Side c = AB (cm)", "7", show_if={"kind": ["sss", "sas", "asa"]}),
                    _f("th", "Angle (degrees)", "50", show_if={"kind": ["sas", "bisect"]}),
                    _f("al", "Angle A (degrees)", "50", show_if={"kind": "asa"}), _f("be", "Angle B (degrees)", "60", show_if={"kind": "asa"}),
                    _f("L", "Length of AB (cm)", "8", show_if={"kind": "perp"}),
                    select("std", "Angle to construct", [(str(v), f"{v}&deg;") for v in (15, 30, 45, 60, 75, 90, 105, 120, 135, 150)], show_if={"kind": "angle"}),
                    _f("h", "Distance of P from the line (cm)", "4", show_if={"kind": "perpfrom"}),
                    _f("r", "Radius of the circle (cm)", "4", show_if={"kind": "hexagon"})]},
        {"id": "ll", "label": "Loci", "title": "Loci (paths of points)", "endpoint": "loci",
         "hint": "A <b>locus</b> is the path of a point that obeys a rule. For the last option, tick the conditions you need and the region that obeys <i>all</i> of them is shaded.",
         "fields": [select("kind", "Rule", [("circle", "a fixed distance from a point"), ("perp", "equal distance from two points"), ("band", "a fixed distance from a line segment"),
                                            ("anglebis", "equal distance from two lines"), ("combined", "combined loci in a triangle (region)")], wide=True),
                    _f("r", "Distance (cm)", "3", show_if={"kind": ["circle", "band"]}),
                    _f("L", "Distance AB / length of AB (cm)", "6", show_if={"kind": ["perp", "band"]}),
                    _f("th", "Angle between the lines (degrees)", "60", show_if={"kind": "anglebis"}),
                    _f("a", "Side a = BC (cm)", "6", show_if={"kind": "combined"}), _f("b", "Side b = CA (cm)", "7", show_if={"kind": "combined"}),
                    _f("c", "Side c = AB (cm)", "8", show_if={"kind": "combined"}),
                    select("c1", "Condition: nearer to A than B (or B than A)?", [("no", "not used"), ("yes", "use it")], show_if={"kind": "combined"}),
                    select("c1s", "Nearer to", [("A", "A"), ("B", "B")], show_if={"kind": "combined"}),
                    select("c2", "Condition: nearer to AB than AC (bisector of angle A)?", [("no", "not used"), ("yes", "use it")], show_if={"kind": "combined"}),
                    select("c2s", "Nearer to line", [("AB", "AB"), ("AC", "AC")], show_if={"kind": "combined"}),
                    select("c3", "Condition: within a distance of C?", [("no", "not used"), ("yes", "use it")], show_if={"kind": "combined"}),
                    _f("r1", "Distance from C (cm)", "4", show_if={"kind": "combined"}),
                    select("c4", "Condition: more than a distance from A?", [("no", "not used"), ("yes", "use it")], show_if={"kind": "combined"}),
                    _f("r2", "Distance from A (cm)", "2", show_if={"kind": "combined"}),
                    select("c5", "Must be inside the triangle?", [("yes", "yes"), ("no", "no")], show_if={"kind": "combined"})]},
    ],
}

topics.register("loci", SPEC, {"construct": construct, "loci": loci})
