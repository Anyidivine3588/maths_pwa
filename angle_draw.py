"""Diagrams for the Angles topic (matplotlib, drawn to scale).

Colour code used everywhere:   BLUE = angle given in the question,   RED = angle we found.
"""
import base64
import io
import math

BLUE, RED, GREEN, ORANGE, PURPLE, GREY, INK = "#1d4ed8", "#dc2626", "#059669", "#d97706", "#7c3aed", "#64748b", "#0f172a"
FILL_GIVEN, FILL_FOUND = "#93c5fd", "#fca5a5"
LINE = "#334155"


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def new_fig(w=5.6, h=4.6):
    plt = _plt()
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0.02, 0.07, 0.96, 0.84])
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def to_b64(fig, dpi=110):
    plt = _plt()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def legend(fig, text="Blue = given in the question   |   Red = the angle we found"):
    fig.text(0.5, 0.0, text, ha="center", va="top", fontsize=9, color=GREY)


def _halo():
    import matplotlib.patheffects as pe
    return [pe.withStroke(linewidth=3, foreground="white")]


def ang(p, q):
    return math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))


def pol(v, deg, r):
    return (v[0] + r * math.cos(math.radians(deg)), v[1] + r * math.sin(math.radians(deg)))


def seg(ax, p, q, color=LINE, lw=2.0, **kw):
    ax.plot([p[0], q[0]], [p[1], q[1]], color=color, lw=lw, solid_capstyle="round", **kw)


def dot(ax, p, c=INK, s=5):
    ax.plot([p[0]], [p[1]], "o", color=c, ms=s, zorder=6)


def vlabel(ax, p, text, deg, d, fs=13):
    q = pol(p, deg, d)
    ax.text(q[0], q[1], text, ha="center", va="center", fontsize=fs, fontweight="bold", color=INK, path_effects=_halo(), zorder=7)


# a label is a tuple (line1, line2 or None, kind)  kind: "given" | "expr" | "found"
def mk_label(val, kind, expr_text=None):
    from angle_core import nm
    v = f"{nm(val, 3).replace('&minus;', chr(0x2212))}°"
    if kind == "expr" and expr_text:
        return (expr_text, "= " + v, kind)
    return (v, None, kind)


def put_text(ax, pos, lab, fs=11, tag=None):
    l1, l2, kind = lab
    c1 = BLUE if kind in ("given", "expr") else RED
    if l2:
        ax.annotate(l1, pos, xytext=(0, 7), textcoords="offset points", ha="center", va="center", fontsize=fs,
                    fontweight="bold", color=BLUE, path_effects=_halo(), zorder=8)
        ax.annotate(l2, pos, xytext=(0, -7), textcoords="offset points", ha="center", va="center", fontsize=fs,
                    fontweight="bold", color=RED, path_effects=_halo(), zorder=8)
    else:
        ax.annotate(l1, pos, ha="center", va="center", fontsize=fs, fontweight="bold", color=c1, path_effects=_halo(), zorder=8)


def wedge(ax, v, a1, a2, r, lab=None, fill=None, lw=2.0, label_r=None, fs=11, right_ok=True, tag=None, edge=None):
    """angle wedge from a1 to a2 degrees (counter-clockwise, a2 > a1)"""
    from matplotlib.patches import Wedge, Arc
    sweep = a2 - a1
    kind = lab[2] if lab else "given"
    fc = fill or (FILL_FOUND if kind == "found" else FILL_GIVEN)
    ec = edge or (RED if kind == "found" else BLUE)
    if right_ok and abs(sweep - 90) < 1e-6:
        s = r * 0.55
        p1, p2 = pol(v, a1, s), pol(v, a2, s)
        corner = (p1[0] + p2[0] - v[0], p1[1] + p2[1] - v[1])
        from matplotlib.patches import Polygon
        ax.add_patch(Polygon([v, p1, corner, p2], closed=True, fc=fc, ec=ec, lw=1.6, alpha=0.55, zorder=3))
    else:
        ax.add_patch(Wedge(v, r, a1, a2, fc=fc, ec="white", lw=1.4, alpha=0.7, zorder=2))
        ax.add_patch(Arc(v, 2 * r, 2 * r, theta1=a1, theta2=a2, color=ec, lw=lw, zorder=3))
    if lab:
        mid = (a1 + a2) / 2
        lr = label_r if label_r else (r * 1.75 if sweep >= 40 else r * 2.45)
        put_text(ax, pol(v, mid, lr), lab, fs=fs)
    if tag:
        ax.text(*pol(v, (a1 + a2) / 2, r * 0.62), tag, ha="center", va="center", fontsize=8, color=GREY, zorder=8)


def title(ax, text):
    ax.set_title(text, fontsize=12, fontweight="bold", color=INK, pad=8)


def fit(ax, pts, pad=0.45):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)


# =============================================================== fans =====

def fig_fan(items, total, heading=None):
    """angles around a point (360), on a straight line (180) or in a right angle (90).
    items = [(value_deg, label_tuple, tag)]"""
    fig, ax = new_fig(*{360: (5.8, 5.0), 180: (6.0, 3.4), 90: (4.6, 4.4)}[total])
    O = (0.0, 0.0)
    start = {360: 18.0, 180: 0.0, 90: 0.0}[total]
    cum = start
    rays = [start]
    for val, lab, tag in items:
        cum += float(val)
        rays.append(cum)
    L = 1.9
    if total == 180:
        seg(ax, pol(O, 180, L), pol(O, 0, L), lw=2.6)
        for a in rays[1:-1]:
            seg(ax, O, pol(O, a, L))
    elif total == 90:
        seg(ax, O, pol(O, 0, L), lw=2.6)
        seg(ax, O, pol(O, 90, L), lw=2.6)
        for a in rays[1:-1]:
            seg(ax, O, pol(O, a, L))
    else:
        for a in rays[:-1]:
            seg(ax, O, pol(O, a, L))
    dot(ax, O)
    for i, (val, lab, tag) in enumerate(items):
        r = 0.55 + 0.12 * (i % 2)
        wedge(ax, O, rays[i], rays[i + 1], r, lab=lab, tag=tag, label_r=(r + 0.62) if float(val) >= 40 else (r + 0.95))
    lim = L + 0.4
    if total == 90:
        ax.set_xlim(-0.5, lim)
        ax.set_ylim(-0.5, lim)
    else:
        ax.set_xlim(-lim, lim)
        ax.set_ylim((-0.3) if total != 360 else -lim, lim if total == 360 else (L + 0.5))
    if heading:
        title(ax, heading)
    legend(fig)
    return to_b64(fig)


def fig_cross(theta, labels, heading="Two straight lines crossing"):
    """labels: 4 label tuples for [0,t] [t,180] [180,180+t] [180+t,360]; opposite angles share a colour"""
    fig, ax = new_fig(5.4, 4.6)
    O = (0.0, 0.0)
    t = min(max(theta, 25.0), 155.0)
    seg(ax, pol(O, 0, 1.9), pol(O, 180, 1.9), lw=2.6)
    seg(ax, pol(O, t, 1.9), pol(O, t + 180, 1.9), lw=2.6)
    dot(ax, O)
    spans = [(0, t), (t, 180), (180, 180 + t), (180 + t, 360)]
    pair = [("#93c5fd", BLUE), ("#fdba74", ORANGE), ("#93c5fd", BLUE), ("#fdba74", ORANGE)]
    for (a1, a2), lab, (fc, ec) in zip(spans, labels, pair):
        wedge(ax, O, a1, a2, 0.6, lab=lab, fill=fc, edge=ec, right_ok=True)
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-2.1, 2.1)
    title(ax, heading)
    legend(fig, "Blue = given   |   Red = found   |   Same-coloured wedges (opposite each other) are equal")
    return to_b64(fig)


# ========================================================= parallel lines =====

SHAPE_NAME = {"corr": "F-shape", "alt": "Z-shape", "coint": "C-shape (or U-shape)"}


def fig_parallel(theta, rel, labels):
    """rel: corr | alt | coint | line | all.  labels: dict 'X','Y' (or 'a'..'h' for all) -> label tuples"""
    big = rel == "all"
    fig, ax = new_fig(*((7.6, 5.4) if big else (6.2, 4.4)))
    t = min(max(theta, 28.0), 152.0)
    H = 2.4 if big else 1.7
    dx = H / math.tan(math.radians(t))
    V2 = (-dx / 2, 0.0)
    V1 = (dx / 2, H)
    xmin = min(V1[0], V2[0]) - 1.9
    xmax = max(V1[0], V2[0]) + 1.9
    for y in (0.0, H):
        seg(ax, (xmin, y), (xmax, y), lw=2.6)
        for k in (0.0, 0.16):
            ax.annotate("", xy=(xmax - 0.5 + k + 0.12, y), xytext=(xmax - 0.5 + k, y),
                        arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=2, mutation_scale=14))
    ax.text(xmax + 0.12, 0, "P", fontsize=13, fontweight="bold", color=INK, va="center")
    ax.text(xmax + 0.12, H, "Q", fontsize=13, fontweight="bold", color=INK, va="center")
    seg(ax, pol(V2, t + 180, 0.7), pol(V1, t, 0.7), lw=2.6, color="#7c3aed")
    dot(ax, V1)
    dot(ax, V2)
    reg = {"UR": (0, t), "UL": (t, 180), "LL": (180, 180 + t), "LR": (180 + t, 360)}

    def put(V, key, lab, r=0.5, fs=11, label_r=None):
        a1, a2 = reg[key]
        wedge(ax, V, a1, a2, r, lab=lab, right_ok=True, fs=fs, label_r=label_r)

    heading = None
    if rel in ("corr", "alt", "coint"):
        # highlight the F / Z / C shape
        if rel == "corr":
            path = [pol(V1, 0, 1.25), V1, V2, pol(V2, 0, 1.25)]
            put(V1, "UR", labels["X"]); put(V2, "UR", labels["Y"])
            heading = "Corresponding angles: the F-shape  (equal)"
        elif rel == "alt":
            path = [pol(V1, 180, 1.25), V1, V2, pol(V2, 0, 1.25)]
            put(V1, "LL", labels["X"]); put(V2, "UR", labels["Y"])
            heading = "Alternate angles: the Z-shape  (equal)"
        else:
            path = [pol(V1, 180, 1.25), V1, V2, pol(V2, 180, 1.25)]
            put(V1, "LL", labels["X"]); put(V2, "UL", labels["Y"])
            heading = "Co-interior angles: the C-shape  (add up to 180°)"
        ax.plot([p[0] for p in path], [p[1] for p in path], color=ORANGE, lw=9, alpha=0.28, solid_capstyle="round", solid_joinstyle="round", zorder=1)
    elif rel == "line":
        put(V1, "UR", labels["X"]); put(V1, "UL", labels["Y"])
        heading = "Angles on a straight line  (add up to 180°)"
    else:
        letters = ["a", "b", "c", "d", "e", "f", "g", "h"]
        keys = [(V1, "UR"), (V1, "UL"), (V1, "LL"), (V1, "LR"), (V2, "UR"), (V2, "UL"), (V2, "LL"), (V2, "LR")]
        for L_, (V, k) in zip(letters, keys):
            a1, a2 = reg[k]
            small = labels[L_]
            fill = FILL_FOUND if small[2] == "found" else FILL_GIVEN
            if (k in ("UL", "LR")):
                fill = "#fdba74" if small[2] != "found" else "#fdba74"
            wedge(ax, V, a1, a2, 0.4, lab=small, fill=fill, edge=(RED if small[2] == "found" else BLUE), fs=10.5, label_r=0.78 if (a2 - a1) >= 60 else 0.95)
            mid = (a1 + a2) / 2
            q = pol(V, mid, 0.2)
            ax.text(q[0], q[1], L_, fontsize=7.5, color=GREY, ha="center", va="center", zorder=9)
        heading = "All eight angles from one angle"
    ax.set_xlim(xmin - 0.2, xmax + 0.6)
    ax.set_ylim(-1.0, H + 1.0)
    title(ax, heading)
    legend(fig, "Green arrows show the two lines are PARALLEL   |   Blue = given   |   Red = found")
    return to_b64(fig)


# ================================================================ polygons =====

def poly_pts(angles, hint=None, scale=1.0):
    """vertices (counter-clockwise) of a polygon with the given interior angles (degrees).
    Edge k runs from vertex k to vertex k+1; the first edge points along +x."""
    import numpy as np
    n = len(angles)
    phi = [0.0]
    for k in range(1, n):
        phi.append(phi[-1] + (180.0 - angles[k]))
    A = np.array([[math.cos(math.radians(p)) for p in phi], [math.sin(math.radians(p)) for p in phi]])
    h = np.array(hint if hint else [1.0] * n, dtype=float)
    for _ in range(40):
        L = h - A.T @ np.linalg.solve(A @ A.T, A @ h)
        if L.min() > 0.10 * L.max():
            break
        h = np.maximum(L, 0.18 * max(L.max(), 1e-9))
    L = L * scale
    pts = [(0.0, 0.0)]
    for k in range(n - 1):
        pts.append((pts[-1][0] + L[k] * math.cos(math.radians(phi[k])), pts[-1][1] + L[k] * math.sin(math.radians(phi[k]))))
    return pts


def _signed_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return a / 2


def draw_polygon(ax, pts, names, labels, ticks=None, parallel=None, letters=True, rfrac=0.105, fs=11, vfs=13):
    """pts must be counter-clockwise.  labels: name -> label tuple or None (no wedge)"""
    n = len(pts)
    if _signed_area(pts) < 0:
        raise ValueError("polygon must be counter-clockwise")
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    size = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    cx, cy = sum(xs) / n, sum(ys) / n
    ax.fill([p[0] for p in pts], [p[1] for p in pts], color="#f1f5f9", zorder=0)
    for k in range(n):
        seg(ax, pts[k], pts[(k + 1) % n], lw=2.4)
    for k in range(n):
        v = pts[k]
        nxt, prv = pts[(k + 1) % n], pts[k - 1]
        a1 = ang(v, nxt)
        a2 = ang(v, prv)
        while a2 <= a1:
            a2 += 360
        sweep = a2 - a1
        lab = labels.get(names[k])
        edge_min = min(math.dist(v, nxt), math.dist(v, prv))
        r = min(rfrac * size, 0.36 * edge_min)
        if lab:
            wedge(ax, v, a1, a2, r, lab=lab, fs=fs, label_r=(r * (1.45 if sweep >= 100 else (1.75 if sweep >= 70 else (2.2 if sweep >= 40 else 2.9)))))
        if letters:
            out = (a1 + a2) / 2 + 180
            q = pol(v, out, 0.075 * size + 0.02)
            ax.text(q[0], q[1], names[k], ha="center", va="center", fontsize=vfs, fontweight="bold", color=INK, path_effects=_halo(), zorder=9)
        dot(ax, v, s=4)
    if ticks:
        for k, c in ticks.items():
            tick(ax, pts[k], pts[(k + 1) % n], c, size)
    if parallel:
        for k, c in parallel.items():
            par_arrows(ax, pts[k], pts[(k + 1) % n], c, size)
    pad = 0.2 * size
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)


def tick(ax, p, q, count, size, frac=0.36):
    mx, my = p[0] + (q[0] - p[0]) * frac, p[1] + (q[1] - p[1]) * frac
    d = math.atan2(q[1] - p[1], q[0] - p[0])
    nx, ny = -math.sin(d), math.cos(d)
    tx, ty = math.cos(d), math.sin(d)
    h = 0.028 * size
    gap = 0.022 * size
    for i in range(count):
        o = (i - (count - 1) / 2) * gap
        cx, cy = mx + tx * o, my + ty * o
        ax.plot([cx - nx * h, cx + nx * h], [cy - ny * h, cy + ny * h], color=RED, lw=2.2, zorder=6)


def par_arrows(ax, p, q, count, size, frac=0.66):
    mx, my = p[0] + (q[0] - p[0]) * frac, p[1] + (q[1] - p[1]) * frac
    d = math.atan2(q[1] - p[1], q[0] - p[0])
    tx, ty = math.cos(d), math.sin(d)
    gap = 0.035 * size
    for i in range(count):
        o = (i - (count - 1) / 2) * gap
        x0, y0 = mx + tx * (o - 0.012 * size), my + ty * (o - 0.012 * size)
        x1, y1 = mx + tx * (o + 0.012 * size), my + ty * (o + 0.012 * size)
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=2, mutation_scale=14), zorder=7)


def auto_size(pts, W=6.0, extra=1.0):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    xr, yr = (max(xs) - min(xs)) or 1.0, (max(ys) - min(ys)) or 1.0
    sz = math.hypot(xr, yr)
    px, py = xr + 0.4 * sz, yr + 0.4 * sz
    H = 1.143 * W * py / px
    return (W, min(max(H, 3.0), 7.0))


def fig_polygon(pts, names, labels, heading=None, ticks=None, parallel=None, extra_legend=None, size=None):
    fig, ax = new_fig(*(size or auto_size(pts)))
    draw_polygon(ax, pts, names, labels, ticks=ticks, parallel=parallel)
    if heading:
        title(ax, heading)
    legend(fig, extra_legend or "Blue = given in the question   |   Red = the angle we found")
    return to_b64(fig)


def regular_pts(n, r=1.0):
    return [(r * math.cos(math.radians(90 + 360.0 * k / n)), r * math.sin(math.radians(90 + 360.0 * k / n))) for k in range(n)]


def fig_regular(n, interior, exterior):
    """two panels: triangles inside a polygon, and its exterior angles"""
    from angle_core import nm
    plt = _plt()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 5.0))
    pts = regular_pts(n)
    pal = ["#bfdbfe", "#fde68a", "#bbf7d0", "#fbcfe8", "#ddd6fe", "#fed7aa", "#a5f3fc", "#fecaca"]
    names = [chr(65 + k) if k < 26 else "" for k in range(n)]
    for ax in (a1, a2):
        ax.set_aspect("equal")
        ax.axis("off")
    # left: triangulation from vertex 0
    for k in range(1, n - 1):
        a1.fill([pts[0][0], pts[k][0], pts[k + 1][0]], [pts[0][1], pts[k][1], pts[k + 1][1]], color=pal[(k - 1) % len(pal)], alpha=0.8, zorder=0)
    for k in range(n):
        seg(a1, pts[k], pts[(k + 1) % n], lw=2.4)
    for k in range(2, n - 1):
        seg(a1, pts[0], pts[k], lw=1.4, color=GREY, ls="--")
    for k in range(n):
        dot(a1, pts[k], s=4)
        q = (pts[k][0] * 1.17, pts[k][1] * 1.17)
        if n <= 26:
            a1.text(q[0], q[1], names[k], ha="center", va="center", fontsize=12, fontweight="bold", color=INK)
    # interior angle marked at the vertex on the right (vertex 1)
    v = pts[1]
    t1, t2 = ang(v, pts[2]), ang(v, pts[0])
    while t2 <= t1:
        t2 += 360
    wedge(a1, v, t1, t2, 0.32, lab=(f"{nm(interior, 2).replace('&minus;', '-')}°", None, "found"), label_r=0.62, fs=10)
    a1.set_xlim(-1.5, 1.5)
    a1.set_ylim(-1.4, 1.45)
    a1.set_title(f"{n - 2} triangles  →  {n - 2} × 180° = {nm((n - 2) * 180)}°", fontsize=12, fontweight="bold", color=INK)
    # right: exterior angles
    for k in range(n):
        seg(a2, pts[k], pts[(k + 1) % n], lw=2.4)
    a2.fill([p[0] for p in pts], [p[1] for p in pts], color="#f1f5f9", zorder=0)
    for k in range(n):
        v = pts[k]
        pv, nx = pts[k - 1], pts[(k + 1) % n]
        phi_in = ang(pv, v)
        phi_out = ang(v, nx)
        while phi_out <= phi_in:
            phi_out += 360
        ext_end = pol(v, phi_in, 0.42)
        seg(a2, v, ext_end, color=GREY, lw=1.6, ls="--")
        pcol = pal[k % len(pal)]
        lab = (f"{nm(exterior, 2).replace('&minus;', '-')}°", None, "found") if k == 1 else None
        wedge(a2, v, phi_in, phi_out, 0.26 if n < 14 else 0.18, lab=lab, fill=pcol, edge=ORANGE, label_r=0.62, fs=10, right_ok=False)
        dot(a2, v, s=4)
    a2.set_xlim(-1.5, 1.5)
    a2.set_ylim(-1.4, 1.45)
    a2.set_title(f"{n} exterior angles  →  they always add up to 360°", fontsize=12, fontweight="bold", color=INK)
    fig.tight_layout()
    return to_b64(fig)


# ============================================================ angle types =====

def fig_types():
    plt = _plt()
    fig, axs = plt.subplots(2, 3, figsize=(9.6, 6.0))
    cases = [("Acute", "less than 90°", 40), ("Right angle", "exactly 90°", 90), ("Obtuse", "between 90° and 180°", 130),
             ("Straight", "exactly 180°", 180), ("Reflex", "between 180° and 360°", 250), ("Full turn", "exactly 360°", 360)]
    for ax, (nme, desc, a) in zip(axs.flat, cases):
        ax.set_aspect("equal")
        ax.axis("off")
        O = (0, 0)
        seg(ax, O, pol(O, 0, 1.5), lw=2.6)
        if a < 360:
            seg(ax, O, pol(O, a, 1.5), lw=2.6)
        dot(ax, O)
        from matplotlib.patches import Wedge
        if a == 360:
            from matplotlib.patches import Circle
            ax.add_patch(Circle(O, 0.6, fc="#bfdbfe", ec=BLUE, lw=2, alpha=0.6))
            ax.annotate("", xy=(0.6, 0.02), xytext=(0.6, -0.12), arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=2))
        else:
            wedge(ax, O, 0, a, 0.6, lab=None, right_ok=True)
        mid = a / 2 if a < 360 else 0
        ax.text(0, -1.75, f"{a}°", ha="center", fontsize=14, fontweight="bold", color=RED)
        ax.set_title(f"{nme}\n{desc}", fontsize=11, fontweight="bold", color=INK)
        ax.set_xlim(-1.7, 1.7)
        ax.set_ylim(-2.1, 1.7)
    fig.tight_layout()
    return to_b64(fig)


def fig_comp_supp():
    plt = _plt()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 4.2))
    for ax in (a1, a2):
        ax.set_aspect("equal")
        ax.axis("off")
    O = (0, 0)
    seg(a1, O, pol(O, 0, 1.7), lw=2.6)
    seg(a1, O, pol(O, 90, 1.7), lw=2.6)
    seg(a1, O, pol(O, 35, 1.7))
    dot(a1, O)
    wedge(a1, O, 0, 35, 0.7, lab=("35°", None, "given"), label_r=1.1)
    wedge(a1, O, 35, 90, 0.55, lab=("55°", None, "found"), label_r=0.95, right_ok=False)
    a1.set_title("Complementary angles add up to 90°\n35° + 55° = 90°", fontsize=12, fontweight="bold", color=INK)
    a1.set_xlim(-0.4, 2.0)
    a1.set_ylim(-0.4, 2.0)
    seg(a2, pol(O, 180, 1.9), pol(O, 0, 1.9), lw=2.6)
    seg(a2, O, pol(O, 60, 1.9))
    dot(a2, O)
    wedge(a2, O, 0, 60, 0.7, lab=("60°", None, "given"), label_r=1.1)
    wedge(a2, O, 60, 180, 0.55, lab=("120°", None, "found"), label_r=1.0)
    a2.set_title("Supplementary angles add up to 180°\n60° + 120° = 180°", fontsize=12, fontweight="bold", color=INK)
    a2.set_xlim(-2.1, 2.1)
    a2.set_ylim(-0.4, 2.0)
    fig.tight_layout()
    return to_b64(fig)


def fig_polygon_ext(pts, names, ext_labels, heading=None):
    """polygon with every exterior angle marked (extend each incoming side)"""
    fig, ax = new_fig(5.8, 4.8)
    n = len(pts)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    size = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    ax.fill(xs, ys, color="#f1f5f9", zorder=0)
    for k in range(n):
        seg(ax, pts[k], pts[(k + 1) % n], lw=2.4)
    pal = ["#fdba74", "#fde68a", "#bbf7d0", "#fbcfe8", "#ddd6fe", "#a5f3fc", "#fecaca", "#bfdbfe"]
    for k in range(n):
        v = pts[k]
        pv, nx = pts[k - 1], pts[(k + 1) % n]
        phi_in = ang(pv, v)
        phi_out = ang(v, nx)
        while phi_out <= phi_in:
            phi_out += 360
        seg(ax, v, pol(v, phi_in, 0.30 * size), color=GREY, lw=1.6, ls="--")
        lab = ext_labels.get(names[k])
        r = min(0.13 * size, 0.4 * min(math.dist(v, nx), math.dist(v, pv)))
        wedge(ax, v, phi_in, phi_out, r, lab=lab, fill=pal[k % len(pal)], edge=ORANGE, label_r=r * 2.0, fs=10, right_ok=False)
        cen = ((phi_in + phi_out) / 2) + 180
        q = pol(v, (ang(v, nx) + ang(v, pv)) / 2 + (0 if True else 0), 0)
        ax.text(*pol(v, ((phi_in + phi_out) / 2) + 180, 0.07 * size + 0.02), names[k], ha="center", va="center", fontsize=13, fontweight="bold", color=INK, path_effects=_halo(), zorder=9)
        dot(ax, v, s=4)
    pad = 0.4 * size
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)
    if heading:
        title(ax, heading)
    legend(fig, "Dashed lines extend each side  |   Blue = given   |   Red = found   |   Exterior angles add up to 360\u00b0")
    return to_b64(fig)
