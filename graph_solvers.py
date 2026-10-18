"""Table of values and plotting for the Graphs topic (uses graph_core; no sympy)."""
import base64
import io
import math

import numpy as np

import graph_core as G
from graph_core import GErr

MINUS = "−"


def _fail(msg):
    return {"steps": [], "result": None, "ok": False, "error": msg}


def _ok(steps, result):
    return {"steps": steps, "result": result, "ok": True, "error": None}


def _unit(d):
    return "rad" if str(d.get("unit", "deg")).lower().startswith("r") else "deg"


def _fmtnum(v, dp=2):
    if v is None or not math.isfinite(v) or abs(v) > 1e9:
        return "undefined"
    r = round(v, dp)
    if r == 0:
        r = 0.0
    if abs(r - round(r)) < 1e-12:
        s = str(int(round(r)))
    else:
        s = f"{r:.{dp}f}".rstrip("0").rstrip(".")
    return s.replace("-", MINUS)


def _xlabel(v, unit):
    """x value text; in radians show multiples of pi when neat"""
    if unit == "rad" and abs(v) > 1e-12:
        from fractions import Fraction
        fr = Fraction(v / math.pi).limit_denominator(12)
        if abs(float(fr) * math.pi - v) < 1e-9:
            n, dn = fr.numerator, fr.denominator
            sgn = MINUS if n < 0 else ""
            n = abs(n)
            body = "π" if n == 1 else f"{n}π"
            return f"{sgn}{body}" + (f"/{dn}" if dn != 1 else "")
    return _fmtnum(v, 4)


def _angle_unit_text(unit):
    return "degrees" if unit == "deg" else "radians"


def _xs(x0, x1, step):
    if step <= 0:
        raise GErr("The step must be bigger than 0.")
    n = int(math.floor((x1 - x0) / step + 1e-9))
    if n + 1 > 400:
        raise GErr("That would give more than 400 rows. Use a bigger step.")
    return [x0 + i * step for i in range(n + 1)]


def table(d):
    try:
        node = G.parse(d.get("expr"))
        unit = _unit(d)
        x0 = G.parse_number(d.get("x_min"), "x min")
        x1 = G.parse_number(d.get("x_max"), "x max")
        step = G.parse_number(d.get("step") or "1", "Step")
        if x0 >= x1:
            raise GErr("x min must be less than x max.")
        try:
            dp = int(str(d.get("dp") or "2").strip())
        except ValueError:
            raise GErr("Decimal places must be a whole number from 0 to 6.")
        if not 0 <= dp <= 6:
            raise GErr("Decimal places must be a whole number from 0 to 6.")
        xs = _xs(x0, x1, step)
        trig = G.has_trig(node)
        tl = G.terms(node)
        cols = tl if 1 < len(tl) <= 6 else None
        yv = [float(G.evaluate(node, v, unit)) for v in xs]
        steps = []
        ftxt = G.fmt(node)
        steps.append(f"<b>The function:</b> <span class='hl'>y = {ftxt}</span>" + (f" &nbsp;(angles in <b>{_angle_unit_text(unit)}</b>)" if trig else ""))
        if cols:
            steps.append("<b>The table has one column for each term</b> of the function, then a last column <b>y</b> that adds them up. "
                         "Work out each term first (a calculator in " + ("DEG" if unit == "deg" else "RAD") + " mode if there is a sin, cos or tan), then add." if trig else
                         "<b>The table has one column for each term</b> of the function, then a last column <b>y</b> that adds them up.")
        # worked example for the first defined row
        ex = next((i for i, v in enumerate(yv) if math.isfinite(v) and abs(v) < 1e9), None)
        if ex is not None:
            xv = xs[ex]
            xl = _xlabel(xv, unit) + ("&deg;" if (trig and unit == "deg") else "")
            if cols:
                parts = []
                tvals = []
                for sg, tn in cols:
                    tv = sg * float(G.evaluate(tn, xv, unit))
                    tvals.append(tv)
                    lab = (MINUS if sg < 0 else "") + G.fmt(tn, 3)
                    parts.append(f"{lab} = {_fmtnum(tv, dp)}")
                total = " + ".join(f"({_fmtnum(t, dp)})" if t < 0 else _fmtnum(t, dp) for t in tvals)
                steps.append(f"<b>Worked example, x = {xl}:</b> " + "; &nbsp;".join(parts) + f". Add them: y = {total} = <b>{_fmtnum(yv[ex], dp)}</b>")
            else:
                steps.append(f"<b>Worked example, x = {xl}:</b> put x = {xl} into the function: y = <b>{_fmtnum(yv[ex], dp)}</b>")
        if any(not math.isfinite(v) or abs(v) > 1e9 for v in yv):
            steps.append("<b>'undefined'</b> means the function has no value at that x (for example tan 90&deg;, or dividing by 0). On a graph the curve has a gap or a vertical asymptote there.")
        # build table
        head = "<tr><th>x" + ("&deg;" if (trig and unit == "deg") else "") + "</th>"
        if cols:
            for i, (sg, tn) in enumerate(cols):
                lab = G.fmt(tn, 3)
                lab = (MINUS + lab) if sg < 0 else (("+ " + lab) if i else lab)
                head += f"<th>{lab}</th>"
        head += "<th>y</th></tr>"
        rows = ""
        for xv, y in zip(xs, yv):
            rows += f"<tr><td>{_xlabel(xv, unit)}</td>"
            if cols:
                for sg, tn in cols:
                    tv = sg * float(G.evaluate(tn, xv, unit))
                    rows += f"<td>{_fmtnum(tv, dp)}</td>"
            rows += f"<td><b>{_fmtnum(y, dp)}</b></td></tr>"
        html = f"<table>{head}{rows}</table>"
        return _ok(steps, {"table": html})
    except GErr as e:
        return _fail(str(e))
    except Exception as e:  # never leak a traceback to students
        return _fail(f"Could not make the table: {e}")


def _nice_step(span):
    for s in (15, 30, 45, 60, 90, 180, 360, 720):
        if span / s <= 14:
            return s
    return 720


def _roots(h, x0, x1):
    """numeric roots of h(x)=0 on [x0,x1] (sign changes + near-touches)"""
    xs = np.linspace(x0, x1, 6001)
    with np.errstate(all="ignore"):
        hv = h(xs)
    hv = np.where(np.isfinite(hv) & (np.abs(hv) < 1e8), hv, np.nan)
    out = []
    for i in range(len(xs) - 1):
        a, b = hv[i], hv[i + 1]
        if not (np.isfinite(a) and np.isfinite(b)):
            continue
        if a == 0:
            out.append(float(xs[i]))
        elif a * b < 0:
            lo, hi = float(xs[i]), float(xs[i + 1])
            flo = float(a)
            for _ in range(70):
                mid = (lo + hi) / 2
                fm_ = float(h(np.array([mid]))[0])
                if (fm_ < 0) == (flo < 0):
                    lo, flo = mid, fm_
                else:
                    hi = mid
            r = (lo + hi) / 2
            fr = abs(float(h(np.array([r]))[0]))
            if fr < 1e-6 * (1 + abs(a) + abs(b)) or fr < 1e-6:
                out.append(r)
    # tangent (double) roots: local minima of |h| that are almost zero
    ah = np.abs(hv)
    for i in range(1, len(xs) - 1):
        if np.isfinite(ah[i]) and ah[i] < ah[i - 1] and ah[i] <= ah[i + 1] and ah[i] < 1e-3 * (1 + np.nanmax(ah[np.isfinite(ah)]) if np.isfinite(ah).any() else 1):
            lo, hi = float(xs[i - 1]), float(xs[i + 1])
            for _ in range(80):
                m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
                if abs(float(h(np.array([m1]))[0])) < abs(float(h(np.array([m2]))[0])):
                    hi = m2
                else:
                    lo = m1
            r = (lo + hi) / 2
            if abs(float(h(np.array([r]))[0])) < 1e-9:
                out.append(r)
    out.sort()
    uniq = []
    for r in out:
        if not uniq or abs(r - uniq[-1]) > 1e-6 * max(1.0, abs(r)):
            uniq.append(r)
    return uniq[:12]


def plot(d):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.ticker import MultipleLocator
        node = G.parse(d.get("expr"))
        node2 = G.parse(d.get("expr2")) if str(d.get("expr2") or "").strip() else None
        unit = _unit(d)
        x0 = G.parse_number(d.get("x_min"), "x min")
        x1 = G.parse_number(d.get("x_max"), "x max")
        if x0 >= x1:
            raise GErr("x min must be less than x max.")

        def opt(k, label):
            v = d.get(k)
            if v in (None, ""):
                return None
            return G.parse_number(v, label)
        y0, y1 = opt("y_min", "y min"), opt("y_max", "y max")
        if y0 is not None and y1 is not None and y0 >= y1:
            raise GErr("y min must be less than y max.")
        xsc, ysc = opt("x_scale", "x scale"), opt("y_scale", "y scale")
        if (xsc is not None and xsc <= 0) or (ysc is not None and ysc <= 0):
            raise GErr("A scale (gridline spacing) must be a positive number.")
        trig = G.has_trig(node) or (node2 is not None and G.has_trig(node2))
        pole = G.has_pole(node) or (node2 is not None and G.has_pole(node2))
        xs = np.linspace(x0, x1, 3000)

        def fvals(nd):
            v = np.asarray(G.evaluate(nd, xs, unit), dtype=float)
            if v.shape != xs.shape:
                v = np.full_like(xs, float(v))
            v = np.where(np.isfinite(v) & (np.abs(v) < 1e6), v, np.nan)
            # break the curve across asymptotes
            if pole:
                dv = np.abs(np.diff(v))
                fin = v[np.isfinite(v)]
                scale = (np.percentile(np.abs(fin), 90) if fin.size else 1.0) + 1.0
                jump = np.where((dv > 6 * scale) & (np.sign(v[:-1]) != np.sign(v[1:])))[0]
                v[jump] = np.nan
            return v
        y1v = fvals(node)
        y2v = fvals(node2) if node2 is not None else None
        fig, ax = plt.subplots(figsize=(7, 5))
        COL1, COL2 = "#4f46e5", "#e11d48"
        ax.plot(xs, y1v, color=COL1, lw=2.2, label="y = " + G.fmt(node))
        if y2v is not None:
            ax.plot(xs, y2v, color=COL2, lw=2.2, label="y = " + G.fmt(node2))
        mark = str(d.get("mark") or "") in ("1", "true", "True", "on")
        if mark:
            try:
                st = G.parse_number(d.get("mark_step") or d.get("step") or "1", "Step")
                mx = _xs(x0, x1, st)[:80]
                mv = np.asarray([float(G.evaluate(node, v, unit)) for v in mx])
                ok = np.isfinite(mv) & (np.abs(mv) < 1e6)
                ax.scatter(np.array(mx)[ok], mv[ok], s=34, color=COL1, edgecolor="white", zorder=5, label="points from the table")
            except GErr:
                pass
        inter = None
        if node2 is not None:
            def h(a):
                return np.asarray(G.evaluate(node, a, unit), dtype=float) - np.asarray(G.evaluate(node2, a, unit), dtype=float)
            rts = _roots(h, x0, x1)
            pts = []
            for r in rts:
                yv = float(G.evaluate(node, r, unit))
                if math.isfinite(yv) and abs(yv) < 1e6:
                    pts.append((r, yv))
            if pts:
                ax.scatter([p[0] for p in pts], [p[1] for p in pts], color="black", zorder=6, s=46, label="Intersection")
                for px, py in pts:
                    ax.annotate(f"({_fmtnum(px, 2).replace(MINUS, '-')}, {_fmtnum(py, 2).replace(MINUS, '-')})", (px, py), xytext=(6, 8), textcoords="offset points", fontsize=8, fontweight="bold")
                inter = ", ".join(f"({_fmtnum(px, 2)}, {_fmtnum(py, 2)})" for px, py in pts)
            else:
                inter = "the two graphs do not cross in this range"
        ax.set_xlim(x0, x1)
        if y0 is not None or y1 is not None:
            lo, hi = ax.get_ylim()
            ax.set_ylim(y0 if y0 is not None else lo, y1 if y1 is not None else hi)
        elif pole:
            allv = np.concatenate([y1v[np.isfinite(y1v)]] + ([y2v[np.isfinite(y2v)]] if y2v is not None else []))
            if allv.size:
                lo, hi = np.percentile(allv, 3), np.percentile(allv, 97)
                pad = (hi - lo) * 0.25 + 0.5
                ax.set_ylim(min(lo - pad, -1), max(hi + pad, 1))
        if xsc:
            ax.xaxis.set_major_locator(MultipleLocator(xsc))
        elif trig and unit == "deg":
            ax.xaxis.set_major_locator(MultipleLocator(_nice_step(x1 - x0)))
        elif trig and unit == "rad":
            ax.xaxis.set_major_locator(MultipleLocator(math.pi / 2))
            ax.set_xticklabels([])
            ticks = np.arange(math.ceil(x0 / (math.pi / 2) - 1e-9), math.floor(x1 / (math.pi / 2) + 1e-9) + 1)
            ax.set_xticks([t * math.pi / 2 for t in ticks])
            ax.set_xticklabels([_xlabel(t * math.pi / 2, "rad") if t else "0" for t in ticks])
        if ysc:
            ax.yaxis.set_major_locator(MultipleLocator(ysc))
        ax.axhline(0, color="#475569", lw=1)
        ax.axvline(0, color="#475569", lw=1)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend(fontsize=9, loc="best")
        ax.set_xlabel("x (degrees)" if (trig and unit == "deg") else ("x (radians)" if trig else "x"))
        ax.set_ylabel("y")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
        plt.close(fig)
        img = base64.b64encode(buf.getvalue()).decode("ascii")
        text = "<b>Plotted:</b> y = " + G.fmt(node) + ("; &nbsp;y = " + G.fmt(node2) if node2 is not None else "")
        if trig:
            text += f" &nbsp;(angles in {_angle_unit_text(unit)})"
        return _ok([], {"image": img, "intersection": inter, "text": text})
    except GErr as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not plot: {e}")
