"""
Statistics & Probability for WAEC / NECO / JAMB (pure Python + matplotlib).
Every solver returns {"ok", "steps", "result", "error"}; chart solvers return
result = {"image": base64-png, "text": html}.
"""
import re
import io
import base64
import math
from fractions import Fraction
from math import comb, perm, factorial, floor, sqrt
from itertools import product

from frac_numeric import (sfrac, _ok, _fail, esc, FR, fr, table, MUL, DIV, MINUS,
                          split_list, dec_str)

MAX_ROWS = 400


# ------------------------------------------------------------ formatting ---

def fmt(x, d=4):
    x = float(x)
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    s = f"{x:.{d}f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-", "-0") else "0"


def fmt2(x):
    return f"{float(x):.2f}"


def sup(e):
    return f"<sup>{e}</sup>"


def parse_nums(text, label="numbers"):
    parts = [p for p in re.split(r"[,;\s]+", str(text).strip()) if p]
    if not parts:
        raise ValueError(f"Please type some {label}, separated by commas.")
    out = []
    for p in parts:
        try:
            out.append(sfrac(p))
        except (ValueError, ZeroDivisionError):
            raise ValueError(f"&lsquo;{esc(p)}&rsquo; is not a number.")
    if len(out) > 500:
        raise ValueError("Please use 500 numbers or fewer.")
    return out


def to_f(x):
    return float(x)


def _fig_to_b64(fig):
    import matplotlib.pyplot as plt
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


# --------------------------------------------------------- ungrouped -------

def _quantile_sorted(data, p):
    """(n+1) position method with linear interpolation. returns (pos, value)"""
    n = len(data)
    pos = p * (n + 1)
    if pos <= 1:
        return pos, data[0]
    if pos >= n:
        return pos, data[-1]
    lo = floor(pos)
    fracp = pos - lo
    return pos, data[lo - 1] + fracp * (data[lo] - data[lo - 1])


def stats_ungrouped(values, freq="", want="all"):
    try:
        xs = parse_nums(values, "values")
        steps = []
        if str(freq).strip():
            fs_ = parse_nums(freq, "frequencies")
            if len(fs_) != len(xs):
                return _fail(f"You typed {len(xs)} values but {len(fs_)} frequencies - they must match one for one.")
            if any(f < 0 or f.denominator != 1 for f in fs_):
                return _fail("Frequencies must be whole numbers (0, 1, 2, ...).")
            fs_ = [int(f) for f in fs_]
            pairs = sorted(zip(xs, fs_), key=lambda t: t[0])
        else:
            cnt = {}
            for x in xs:
                cnt[x] = cnt.get(x, 0) + 1
            pairs = sorted(cnt.items())
            fs_ = None
        N = sum(f for _, f in pairs)
        if N == 0:
            return _fail("The frequencies add up to zero.")
        if N > 100000:
            return _fail("That is too many observations for this solver.")
        data = []
        for x, f in pairs:
            data.extend([x] * f)
        n = len(data)
        # frequency table
        cf, run = [], 0
        for x, f in pairs:
            run += f
            cf.append(run)
        sum_fx = sum(x * f for x, f in pairs)
        mean = sum_fx / N
        steps.append(f"Number of observations: n = &Sigma;f = {N}")
        if fs_ is not None or any(f > 1 for _, f in pairs):
            rows = [[fmt(x), f, fmt(x * f), c] for (x, f), c in zip(pairs, cf)]
            rows.append(["", f"&Sigma;f = {N}", f"&Sigma;fx = {fmt(sum_fx)}", ""])
            steps.append("Frequency table:" + table(rows, ["x", "f", "fx", "cumulative f"]))
        else:
            steps.append("Arrange the data in order (smallest to largest): " + ", ".join(fmt(x) for x in data))
        res = []
        W = want
        # MEAN
        if W in ("all", "mean"):
            if fs_ is not None or any(f > 1 for _, f in pairs):
                steps.append(f"<b>Mean</b> = {FR('&Sigma;fx', '&Sigma;f')} = {FR(fmt(sum_fx), N)} = {fmt(mean)}")
            else:
                steps.append(f"<b>Mean</b> = {FR('sum of all the values', 'number of values')} = {FR(fmt(sum_fx), N)} = {fmt(mean)}")
            res.append(f"Mean = {fmt(mean)}")
        # MEDIAN
        if W in ("all", "median"):
            if n % 2:
                mid = data[n // 2]
                steps.append(f"<b>Median</b> (middle value): n = {n} is odd, so the median is the {(n + 1) // 2}th value = {fmt(mid)}")
            else:
                a, b = data[n // 2 - 1], data[n // 2]
                mid = (a + b) / 2
                steps.append(f"<b>Median</b>: n = {n} is even, so take the average of the {n // 2}th and {n // 2 + 1}th values: "
                             f"({fmt(a)} + {fmt(b)}) {DIV} 2 = {fmt(mid)}")
            res.append(f"Median = {fmt(mid)}")
        # MODE
        if W in ("all", "mode"):
            mx = max(f for _, f in pairs)
            modes = [x for x, f in pairs if f == mx]
            if mx == 1 and len(pairs) == len(data):
                steps.append("<b>Mode</b> (most frequent value): every value occurs once, so there is <b>no mode</b>.")
                res.append("Mode: none")
            else:
                steps.append(f"<b>Mode</b> (most frequent value): the highest frequency is {mx}, which belongs to "
                             f"{', '.join(fmt(m) for m in modes)}.")
                lab = {1: "", 2: " (bimodal)"}.get(len(modes), " (multimodal)")
                res.append(f"Mode = {', '.join(fmt(m) for m in modes)}{lab}")
        # RANGE
        if W in ("all", "range"):
            rg = data[-1] - data[0]
            steps.append(f"<b>Range</b> = highest {MINUS} lowest = {fmt(data[-1])} {MINUS} {fmt(data[0])} = {fmt(rg)}")
            res.append(f"Range = {fmt(rg)}")
        # QUARTILES
        if W in ("all", "quartiles"):
            p1, q1 = _quantile_sorted(data, Fraction(1, 4))
            p2, q2 = _quantile_sorted(data, Fraction(1, 2))
            p3, q3 = _quantile_sorted(data, Fraction(3, 4))
            steps.append("<b>Quartiles</b> split the ordered data into four equal parts. "
                         f"Q<sub>1</sub> is at position (n+1)/4 = {fmt(p1)}, Q<sub>2</sub> (the median) at (n+1)/2 = {fmt(p2)}, "
                         f"Q<sub>3</sub> at 3(n+1)/4 = {fmt(p3)}. (If a position is not whole, go part of the way between two values.)")
            steps.append(f"Q<sub>1</sub> = {fmt(q1)}, &nbsp; Q<sub>3</sub> = {fmt(q3)}")
            steps.append(f"<b>Interquartile range</b> = Q<sub>3</sub> {MINUS} Q<sub>1</sub> = {fmt(q3)} {MINUS} {fmt(q1)} = {fmt(q3 - q1)}")
            steps.append(f"<b>Semi-interquartile (quartile) deviation</b> = {FR('Q<sub>3</sub> &minus; Q<sub>1</sub>', 2)} = {fmt((q3 - q1) / 2)}")
            res.append(f"Q1 = {fmt(q1)}, Q3 = {fmt(q3)}, IQR = {fmt(q3 - q1)}")
        # VARIANCE / SD / MEAN DEVIATION
        if W in ("all", "sd", "variance"):
            rows = []
            ssd = Fraction(0)
            sad = Fraction(0)
            single = fs_ is None and all(f == 1 for _, f in pairs)
            for x, f in pairs:
                dv = x - mean
                ssd += f * dv * dv
                sad += f * abs(dv)
                if single:
                    rows.append([fmt(x), fmt(dv), fmt(dv * dv)])
                else:
                    rows.append([fmt(x), f, fmt(dv), fmt(dv * dv), fmt(f * dv * dv)])
            var = ssd / N
            sd = sqrt(var)
            if len(pairs) <= 25:
                if single:
                    rows.append(["", "", f"&Sigma;(x&minus;x&#772;)<sup>2</sup> = {fmt(ssd)}"])
                    steps.append(f"<b>Variance and standard deviation</b> (mean = {fmt(mean)}):" +
                                 table(rows, ["x", "x &minus; mean", "(x &minus; mean)<sup>2</sup>"]))
                else:
                    rows.append(["", f"&Sigma;f = {N}", "", "", f"&Sigma;f(x&minus;x&#772;)<sup>2</sup> = {fmt(ssd)}"])
                    steps.append(f"<b>Variance and standard deviation</b> (mean = {fmt(mean)}):" +
                                 table(rows, ["x", "f", "x &minus; mean", "(x &minus; mean)<sup>2</sup>", "f(x &minus; mean)<sup>2</sup>"]))
            else:
                steps.append(f"Sum of squared deviations = {fmt(ssd)}")
            steps.append(f"<b>Variance</b> = {FR('&Sigma;f(x &minus; x&#772;)<sup>2</sup>', '&Sigma;f')} = {FR(fmt(ssd), N)} = {fmt(var)}")
            steps.append(f"<b>Standard deviation</b> = &radic;variance = &radic;{fmt(var)} = {fmt(sd)} (to 2 d.p.: {fmt2(sd)})")
            sumsq = sum(x * x * f for x, f in pairs)
            steps.append(f"<i>Check with the other formula:</i> variance = {FR('&Sigma;fx<sup>2</sup>', '&Sigma;f')} {MINUS} (mean)<sup>2</sup> = "
                         f"{FR(fmt(sumsq), N)} {MINUS} {fmt(mean)}<sup>2</sup> = {fmt(sumsq / N - mean * mean)}")
            md = sad / N
            steps.append(f"<b>Mean deviation</b> = {FR('&Sigma;f|x &minus; mean|', '&Sigma;f')} = {FR(fmt(sad), N)} = {fmt(md)}")
            res.append(f"Variance = {fmt(var)}, Standard deviation = {fmt(sd)}, Mean deviation = {fmt(md)}")
        return _ok(steps, "<br>".join(res))
    except ValueError as e:
        return _fail(str(e))


# ------------------------------------------------------------ grouped ------

_CLASS_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*(?:-|to|–)\s*(-?\d+(?:\.\d+)?)\s*$", re.I)


def parse_classes(text):
    parts = [p.strip() for p in re.split(r"[,;\n]+", str(text)) if p.strip()]
    if len(parts) < 2:
        raise ValueError("Please give at least two class intervals, e.g. 1-10, 11-20, 21-30.")
    cl = []
    for p in parts:
        m = _CLASS_RE.match(p)
        if not m:
            raise ValueError(f"I could not read the class &lsquo;{esc(p)}&rsquo;. Write classes like 10-19 (lower - upper).")
        lo, hi = Fraction(m.group(1)), Fraction(m.group(2))
        if hi <= lo:
            raise ValueError(f"In the class &lsquo;{esc(p)}&rsquo; the second number must be bigger than the first.")
        cl.append((lo, hi, p))
    for i in range(1, len(cl)):
        if cl[i][0] < cl[i - 1][1]:
            raise ValueError("The classes must go in order from smallest to largest, without overlapping.")
    gaps = [cl[i][0] - cl[i - 1][1] for i in range(1, len(cl))]
    if len(set(gaps)) != 1:
        raise ValueError("The gap between neighbouring classes must be the same all the way down (e.g. 1-5, 6-10, 11-15).")
    g = gaps[0]
    half = g / 2
    out = []
    for lo, hi, p in cl:
        out.append({"label": p, "lo": lo, "hi": hi, "LB": lo - half, "UB": hi + half})
    for c in out:
        c["mid"] = (c["LB"] + c["UB"]) / 2
        c["w"] = c["UB"] - c["LB"]
    return out, g


def _grouped_setup(classes, freq):
    cl, gap = parse_classes(classes)
    fs_ = parse_nums(freq, "frequencies")
    if len(fs_) != len(cl):
        raise ValueError(f"You typed {len(cl)} classes but {len(fs_)} frequencies - they must match one for one.")
    if any(f < 0 or f.denominator != 1 for f in fs_):
        raise ValueError("Frequencies must be whole numbers.")
    fs_ = [int(f) for f in fs_]
    run = 0
    for c, f in zip(cl, fs_):
        c["f"] = f
        run += f
        c["cf"] = run
    N = run
    if N == 0:
        raise ValueError("The frequencies add up to zero.")
    return cl, gap, N


def _q_grouped(cl, N, frac):
    """class containing the frac*N-th item; returns dict"""
    target = N * frac
    prev = 0
    for i, c in enumerate(cl):
        if c["cf"] >= target and c["f"] > 0:
            F = prev
            val = c["LB"] + (target - F) / c["f"] * c["w"]
            return {"i": i, "c": c, "target": target, "F": F, "val": val}
        prev = c["cf"]
    c = cl[-1]
    return {"i": len(cl) - 1, "c": c, "target": target, "F": N - c["f"], "val": c["UB"]}


def stats_grouped(classes, freq, want="all", assumed="", percentile=""):
    try:
        cl, gap, N = _grouped_setup(classes, freq)
        steps = []
        res = []
        W = want
        # table
        if gap != 0:
            steps.append(f"The classes have a gap of {fmt(gap)} between them, so the <b>class boundaries</b> are found by "
                         f"going {fmt(gap / 2)} below each lower limit and {fmt(gap / 2)} above each upper limit.")
        rows = []
        sfx = Fraction(0)
        for c in cl:
            sfx += c["f"] * c["mid"]
            rows.append([esc(c["label"]), f"{fmt(c['LB'])} &ndash; {fmt(c['UB'])}", fmt(c["mid"]), c["f"], c["cf"], fmt(c["f"] * c["mid"])])
        rows.append(["", "", "", f"&Sigma;f = {N}", "", f"&Sigma;fx = {fmt(sfx)}"])
        steps.append("<b>Frequency table</b> (x = class mid-point = (lower boundary + upper boundary) &divide; 2):" +
                     table(rows, ["Class", "Class boundaries", "Mid-point x", "f", "Cumulative f", "fx"]))
        # mean
        if W in ("all", "mean", "sd"):
            mean = sfx / N
            if W in ("all", "mean"):
                steps.append(f"<b>Mean</b> = {FR('&Sigma;fx', '&Sigma;f')} = {FR(fmt(sfx), N)} = {fmt(mean)}")
                res.append(f"Mean = {fmt(mean)}")
                # assumed mean method
                try:
                    A = sfrac(assumed) if str(assumed).strip() else max(cl, key=lambda c: c["f"])["mid"]
                except ValueError:
                    return _fail("The assumed mean must be a number.")
                sfd = sum(c["f"] * (c["mid"] - A) for c in cl)
                steps.append(f"<i>Using an assumed mean A = {fmt(A)} (a mid-point near the middle):</i> d = x {MINUS} A, "
                             f"mean = A + {FR('&Sigma;fd', '&Sigma;f')} = {fmt(A)} + {FR(fmt(sfd), N)} = {fmt(A + sfd / N)}")
        # median / quartiles / percentile
        def q_steps(name, frac, sym):
            q = _q_grouped(cl, N, frac)
            c = q["c"]
            steps.append(f"<b>{name}</b>: it is the {fmt(q['target'])}th value ({sym}N = {fmt(frac * N)}). "
                         f"Look in the cumulative column: the first class with cumulative f at least {fmt(q['target'])} is "
                         f"<b>{esc(c['label'])}</b> (boundaries {fmt(c['LB'])} &ndash; {fmt(c['UB'])}).")
            steps.append(f"{name} = L + {FR(f'{sym}N {MINUS} F', 'f')} {MUL} c &nbsp;where L = {fmt(c['LB'])} (lower boundary of the class), "
                         f"F = {q['F']} (cumulative f before the class), f = {c['f']} (frequency of the class), c = {fmt(c['w'])} (class width)")
            steps.append(f"= {fmt(c['LB'])} + {FR(f'{fmt(q['target'])} {MINUS} {q['F']}', c['f'])} {MUL} {fmt(c['w'])} = <b>{fmt(q['val'])}</b>")
            return q
        if W in ("all", "median"):
            q = q_steps("Median", Fraction(1, 2), "&frac12;")
            res.append(f"Median = {fmt(q['val'])}")
        # mode
        if W in ("all", "mode"):
            mx = max(c["f"] for c in cl)
            i = next(k for k, c in enumerate(cl) if c["f"] == mx)
            c = cl[i]
            fp = cl[i - 1]["f"] if i > 0 else 0
            fn = cl[i + 1]["f"] if i < len(cl) - 1 else 0
            d1, d2 = c["f"] - fp, c["f"] - fn
            steps.append(f"<b>Mode</b>: the modal class is the class with the highest frequency ({mx}): <b>{esc(c['label'])}</b>.")
            steps.append(f"Mode = L + {FR('d<sub>1</sub>', 'd<sub>1</sub> + d<sub>2</sub>')} {MUL} c &nbsp;where L = {fmt(c['LB'])}, "
                         f"d<sub>1</sub> = {c['f']} {MINUS} {fp} = {d1} (modal f minus the f before), "
                         f"d<sub>2</sub> = {c['f']} {MINUS} {fn} = {d2} (modal f minus the f after), c = {fmt(c['w'])}")
            if d1 + d2 == 0:
                steps.append("d<sub>1</sub> + d<sub>2</sub> is 0, so the formula cannot be used here.")
            else:
                mode = c["LB"] + Fraction(d1, d1 + d2) * c["w"]
                steps.append(f"= {fmt(c['LB'])} + {FR(d1, f'{d1} + {d2}')} {MUL} {fmt(c['w'])} = <b>{fmt(mode)}</b>")
                res.append(f"Mode = {fmt(mode)}")
        # quartiles
        if W in ("all", "quartiles"):
            q1 = q_steps("Lower quartile Q<sub>1</sub>", Fraction(1, 4), "&frac14;")
            q3 = q_steps("Upper quartile Q<sub>3</sub>", Fraction(3, 4), "&frac34;")
            iqr = q3["val"] - q1["val"]
            steps.append(f"<b>Interquartile range</b> = Q<sub>3</sub> {MINUS} Q<sub>1</sub> = {fmt(q3['val'])} {MINUS} {fmt(q1['val'])} = {fmt(iqr)}")
            steps.append(f"<b>Semi-interquartile range</b> = {FR('Q<sub>3</sub> &minus; Q<sub>1</sub>', 2)} = {fmt(iqr / 2)}")
            res.append(f"Q1 = {fmt(q1['val'])}, Q3 = {fmt(q3['val'])}, IQR = {fmt(iqr)}")
        # percentile
        if str(percentile).strip():
            try:
                pv = sfrac(percentile)
            except ValueError:
                return _fail("The percentile must be a number between 1 and 99.")
            if not (0 < pv < 100):
                return _fail("The percentile must be between 1 and 99.")
            q = q_steps(f"{fmt(pv)}th percentile", pv / 100, f"{fmt(pv)}/100 &times; ")
            res.append(f"{fmt(pv)}th percentile = {fmt(q['val'])}")
        # SD
        if W in ("all", "sd"):
            try:
                A = sfrac(assumed) if str(assumed).strip() else max(cl, key=lambda c: c["f"])["mid"]
            except ValueError:
                return _fail("The assumed mean must be a number.")
            rows = []
            sfd = sfd2 = Fraction(0)
            for c in cl:
                d = c["mid"] - A
                sfd += c["f"] * d
                sfd2 += c["f"] * d * d
                rows.append([esc(c["label"]), fmt(c["mid"]), c["f"], fmt(d), fmt(c["f"] * d), fmt(d * d), fmt(c["f"] * d * d)])
            rows.append(["", "", f"&Sigma;f = {N}", "", f"&Sigma;fd = {fmt(sfd)}", "", f"&Sigma;fd<sup>2</sup> = {fmt(sfd2)}"])
            steps.append(f"<b>Variance and standard deviation</b> using an assumed mean A = {fmt(A)} (d = x {MINUS} A):" +
                         table(rows, ["Class", "x", "f", "d = x &minus; A", "fd", "d<sup>2</sup>", "fd<sup>2</sup>"]))
            var = sfd2 / N - (sfd / N) ** 2
            steps.append(f"<b>Variance</b> = {FR('&Sigma;fd<sup>2</sup>', '&Sigma;f')} {MINUS} ({FR('&Sigma;fd', '&Sigma;f')})<sup>2</sup> = "
                         f"{FR(fmt(sfd2), N)} {MINUS} ({FR(fmt(sfd), N)})<sup>2</sup> = {fmt(sfd2 / N)} {MINUS} {fmt((sfd / N) ** 2)} = {fmt(var)}")
            sd = sqrt(var)
            steps.append(f"<b>Standard deviation</b> = &radic;variance = &radic;{fmt(var)} = {fmt(sd)} (to 2 d.p.: {fmt2(sd)})")
            res.append(f"Variance = {fmt(var)}, Standard deviation = {fmt(sd)}")
        return _ok(steps, "<br>".join(res))
    except ValueError as e:
        return _fail(str(e))


# -------------------------------------------------------------- charts -----

def _monotone_curve(xs, ys, n=200):
    import numpy as np
    xs, ys = np.array(xs, float), np.array(ys, float)
    h = np.diff(xs)
    dl = np.diff(ys) / h
    m = np.zeros(len(xs))
    m[0], m[-1] = dl[0], dl[-1]
    for i in range(1, len(xs) - 1):
        m[i] = 0 if dl[i - 1] * dl[i] <= 0 else 2 / (1 / dl[i - 1] + 1 / dl[i])
    t = np.linspace(xs[0], xs[-1], n)
    out = []
    for x in t:
        i = min(max(np.searchsorted(xs, x) - 1, 0), len(xs) - 2)
        s = (x - xs[i]) / h[i]
        h00 = 2 * s ** 3 - 3 * s ** 2 + 1
        h10 = s ** 3 - 2 * s ** 2 + s
        h01 = -2 * s ** 3 + 3 * s ** 2
        h11 = s ** 3 - s ** 2
        out.append(h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1])
    return t, out


def _ogive_read_x(bounds, cfs, y):
    """x for a given cumulative frequency y (linear interpolation)"""
    for i in range(1, len(bounds)):
        if cfs[i] >= y:
            if cfs[i] == cfs[i - 1]:
                return bounds[i]
            return bounds[i - 1] + (y - cfs[i - 1]) / (cfs[i] - cfs[i - 1]) * (bounds[i] - bounds[i - 1])
    return bounds[-1]


def _ogive_read_y(bounds, cfs, x):
    if x <= bounds[0]:
        return cfs[0]
    for i in range(1, len(bounds)):
        if bounds[i] >= x:
            return cfs[i - 1] + (x - bounds[i - 1]) / (bounds[i] - bounds[i - 1]) * (cfs[i] - cfs[i - 1])
    return cfs[-1]


def stats_chart(kind, classes="", freq="", labels="", values="", title="", read_value="", read_percentile=""):
    try:
        plt = _mpl()
        steps, text = [], ""
        if kind in ("histogram", "polygon", "ogive"):
            cl, gap, N = _grouped_setup(classes, freq)
            widths = {c["w"] for c in cl}
            equal = len(widths) == 1
            fig, ax = plt.subplots(figsize=(7.2, 4.8))
            ttl = esc(title) if title else ""
            if kind == "histogram":
                rows = []
                for c in cl:
                    h = c["f"] if equal else float(c["f"] / c["w"])
                    ax.bar(float(c["LB"]), h, width=float(c["w"]), align="edge", color="#93c5fd", edgecolor="#1e3a8a")
                    ax.text(float(c["mid"]), h, fmt(h), ha="center", va="bottom", fontsize=8)
                    rows.append([esc(c["label"]), f"{fmt(c['LB'])} &ndash; {fmt(c['UB'])}", fmt(c["w"]), c["f"],
                                 fmt(c["f"] / c["w"], 3)])
                ax.set_ylabel("Frequency" if equal else "Frequency density")
                ax.set_xlabel("Class boundaries")
                ax.set_xticks([float(c["LB"]) for c in cl] + [float(cl[-1]["UB"])])
                steps.append("A histogram has <b>no gaps</b> between the bars, so draw each bar from its lower class boundary to its upper class boundary.")
                if equal:
                    steps.append("All the class widths are equal, so the bar height is simply the frequency.")
                    # graphical mode construction
                    i = max(range(len(cl)), key=lambda k: cl[k]["f"])
                    c = cl[i]
                    fp = cl[i - 1]["f"] if i > 0 else 0
                    fn = cl[i + 1]["f"] if i < len(cl) - 1 else 0
                    d1, d2 = c["f"] - fp, c["f"] - fn
                    if d1 + d2 > 0:
                        L, w = float(c["LB"]), float(c["w"])
                        t = d1 / (d1 + d2)
                        mx = L + t * w
                        my = fp + t * d1
                        ax.plot([L, L + w], [fp, c["f"]], color="#dc2626", lw=1.2)
                        ax.plot([L, L + w], [c["f"], fn], color="#dc2626", lw=1.2)
                        ax.plot([mx, mx], [0, my], color="#dc2626", ls="--", lw=1.2)
                        ax.text(mx, max(cl_f for cl_f in [c2["f"] for c2 in cl]) * 0.04, f"mode \u2248 {mx:.2f}", ha="center",
                                color="#dc2626", fontsize=9, bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1.5})
                        steps.append("<b>Finding the mode from the histogram:</b> in the tallest (modal) bar, join its top-<i>left</i> corner to the "
                                     "top-<i>left</i> corner of the bar after it, and its top-<i>right</i> corner to the top-<i>right</i> corner of the "
                                     "bar before it. Where the two lines cross, drop a line to the x-axis (shown in red). "
                                     f"That reading is the mode ≈ {mx:.2f}.")
                else:
                    steps.append("The class widths are <b>not equal</b>, so the bar height must be the <b>frequency density</b> = frequency &divide; class width.")
                text = table(rows, ["Class", "Boundaries", "Class width", "Frequency", "Frequency density"])
            elif kind == "polygon":
                mids = [float(cl[0]["LB"] - cl[0]["w"] / 2 + cl[0]["w"] / 2 * 0)]
                xs = [float(cl[0]["mid"] - cl[0]["w"])] + [float(c["mid"]) for c in cl] + [float(cl[-1]["mid"] + cl[-1]["w"])]
                ys = [0] + [c["f"] for c in cl] + [0]
                for c in cl:
                    ax.bar(float(c["LB"]), c["f"], width=float(c["w"]), align="edge", color="#e0f2fe", edgecolor="#bae6fd")
                ax.plot(xs, ys, "o-", color="#1d4ed8")
                for x_, y_ in zip(xs[1:-1], ys[1:-1]):
                    ax.text(x_, y_, str(y_), ha="center", va="bottom", fontsize=8)
                ax.set_xlabel("Class mid-points")
                ax.set_ylabel("Frequency")
                steps.append("Find the <b>mid-point</b> of each class and plot it against the frequency (a dot).")
                steps.append("Join the dots with straight lines. Close the polygon by adding one empty class at each end "
                             f"(mid-points {fmt(cl[0]['mid'] - cl[0]['w'])} and {fmt(cl[-1]['mid'] + cl[-1]['w'])}, frequency 0) so it touches the x-axis.")
                text = table([[esc(c["label"]), fmt(c["mid"]), c["f"]] for c in cl], ["Class", "Mid-point", "Frequency"])
            else:
                bounds = [float(cl[0]["LB"])] + [float(c["UB"]) for c in cl]
                cfs = [0] + [c["cf"] for c in cl]
                tx, ty = _monotone_curve(bounds, cfs) if len(bounds) > 2 else (bounds, cfs)
                ax.plot(tx, ty, color="#1d4ed8", lw=1.6)
                ax.plot(bounds, cfs, "o", color="#1e3a8a")
                for b, cf in zip(bounds, cfs):
                    ax.text(b, cf, str(cf), ha="right", va="bottom", fontsize=8)
                ax.set_xlabel("Upper class boundaries")
                ax.set_ylabel("Cumulative frequency")
                ax.set_ylim(0, N * 1.08)
                steps.append("An <b>ogive</b> (cumulative frequency curve) is plotted against the <b>upper class boundaries</b>.")
                steps.append(f"Start at the lower boundary of the first class ({fmt(cl[0]['LB'])}) with cumulative frequency 0, "
                             "then plot each upper boundary against its cumulative frequency, and join the points with a smooth curve.")
                rows = [["(start)", fmt(cl[0]['LB']), 0]] + [[esc(c["label"]), fmt(c["UB"]), c["cf"]] for c in cl]
                text = table(rows, ["Class", "Upper boundary", "Cumulative frequency"])
                reads = []
                for name, fr_ in (("Q<sub>1</sub> (N/4)", Fraction(1, 4)), ("Median (N/2)", Fraction(1, 2)), ("Q<sub>3</sub> (3N/4)", Fraction(3, 4))):
                    yy = float(N * fr_)
                    xx = _ogive_read_x(bounds, cfs, yy)
                    ax.plot([bounds[0], xx], [yy, yy], "--", color="#dc2626", lw=1)
                    ax.plot([xx, xx], [0, yy], "--", color="#dc2626", lw=1)
                    ax.text(xx, 0, f"{xx:.1f}", color="#dc2626", ha="center", va="top", fontsize=8)
                    reads.append((name, yy, xx))
                steps.append("<b>Reading values from the ogive:</b> go up the vertical axis to the cumulative frequency, across to the curve, then down to the horizontal axis.")
                for name, yy, xx in reads:
                    steps.append(f"{name} = {fmt(yy)}th value &rarr; read {fmt2(xx)}")
                text += "<br>" + "<br>".join(f"{n} = {fmt(y_)}th value &rarr; ≈ {x_:.2f}" for n, y_, x_ in reads)
                iqr = reads[2][2] - reads[0][2]
                text += f"<br>Interquartile range ≈ {iqr:.2f}"
                if str(read_value).strip():
                    xv = float(sfrac(read_value))
                    yv = _ogive_read_y(bounds, cfs, xv)
                    ax.plot([xv, xv], [0, yv], ":", color="#16a34a", lw=1.4)
                    ax.plot([bounds[0], xv], [yv, yv], ":", color="#16a34a", lw=1.4)
                    steps.append(f"At x = {fmt(xv)} the curve gives cumulative frequency ≈ {yv:.1f}: about {yv:.0f} observations are below {fmt(xv)} "
                                 f"and about {N - yv:.0f} are above it.")
                    text += f"<br>Below {fmt(xv)}: ≈ {yv:.0f}; above {fmt(xv)}: ≈ {N - yv:.0f}"
                if str(read_percentile).strip():
                    pv = float(sfrac(read_percentile))
                    yy = N * pv / 100
                    xx = _ogive_read_x(bounds, cfs, yy)
                    ax.plot([bounds[0], xx], [yy, yy], ":", color="#16a34a", lw=1.4)
                    ax.plot([xx, xx], [0, yy], ":", color="#16a34a", lw=1.4)
                    steps.append(f"{fmt(pv)}th percentile = {fmt(yy)}th value &rarr; read ≈ {xx:.2f}")
                    text += f"<br>{fmt(pv)}th percentile ≈ {xx:.2f}"
            ax.grid(alpha=0.25)
            if title:
                ax.set_title(title)
            return _ok(steps, {"image": _fig_to_b64(fig), "text": text})
        if kind in ("bar", "pie"):
            labs = [l.strip() for l in re.split(r"[,;\n]+", str(labels)) if l.strip()]
            vals = parse_nums(values, "values")
            if len(labs) != len(vals):
                return _fail(f"You typed {len(labs)} labels but {len(vals)} values - they must match one for one.")
            if len(labs) < 2:
                return _fail("Please give at least two items.")
            if any(v < 0 for v in vals):
                return _fail("Values cannot be negative.")
            total = sum(vals)
            if total == 0:
                return _fail("The values add up to zero.")
            fig, ax = plt.subplots(figsize=(6.6, 4.8))
            colors = ["#60a5fa", "#fbbf24", "#34d399", "#f87171", "#a78bfa", "#fb923c", "#22d3ee", "#f472b6", "#a3e635", "#94a3b8"]
            if kind == "bar":
                ax.bar(range(len(labs)), [float(v) for v in vals], color=colors[0], edgecolor="#1e3a8a", width=0.6)
                ax.set_xticks(range(len(labs)))
                ax.set_xticklabels(labs, rotation=0 if len(labs) < 7 else 30)
                for i, v in enumerate(vals):
                    ax.text(i, float(v), fmt(v), ha="center", va="bottom", fontsize=9)
                ax.set_ylabel("Frequency")
                ax.grid(axis="y", alpha=0.25)
                steps.append("A bar chart has <b>gaps between the bars</b>; every bar has the <b>same width</b> and the height shows the frequency.")
                steps.append("Choose a sensible scale for the vertical axis so the tallest bar fits.")
                text = table([[esc(l), fmt(v)] for l, v in zip(labs, vals)], ["Item", "Frequency"])
            else:
                angles = [v / total * 360 for v in vals]
                ax.pie([float(v) for v in vals], labels=labs, colors=colors[:len(labs)] * 2,
                       autopct=lambda p: f"{p:.1f}%", startangle=90, counterclock=False,
                       wedgeprops={"edgecolor": "white"})
                ax.axis("equal")
                steps.append(f"Total = {fmt(total)}")
                steps.append("Angle of each sector = " + FR("item", "total") + f" {MUL} 360&deg;")
                rows = []
                for l, v, a in zip(labs, vals, angles):
                    steps.append(f"{esc(l)}: {FR(fmt(v), fmt(total))} {MUL} 360&deg; = {fmt(a, 2)}&deg;")
                    rows.append([esc(l), fmt(v), f"{fmt(a, 2)}&deg;", f"{fmt(v / total * 100, 2)}%"])
                rows.append(["Total", fmt(total), "360&deg;", "100%"])
                steps.append("Check: the angles must add up to 360&deg;. Use a protractor to draw each sector.")
                text = table(rows, ["Item", "Frequency", "Angle", "Percentage"])
            if title:
                ax.set_title(title)
            return _ok(steps, {"image": _fig_to_b64(fig), "text": text})
        if kind == "stemleaf":
            xs = parse_nums(values, "values")
            if any(x.denominator != 1 for x in xs):
                return _fail("Stem-and-leaf works with whole numbers. Round your data first.")
            data = sorted(int(x) for x in xs)
            stems = {}
            for v in data:
                s, l = divmod(abs(v), 10)
                stems.setdefault(s, []).append(l)
            lo, hi = min(stems), max(stems)
            rows = []
            for s in range(lo, hi + 1):
                leaves = sorted(stems.get(s, []))
                rows.append([f"<b>{s}</b>", " ".join(map(str, leaves))])
            steps.append("Arrange the data in order. The <b>stem</b> is the tens digit (the digits before the last one) and the <b>leaf</b> is the units digit.")
            steps.append("Write each stem once, in a column, and put each leaf beside its stem in order, with equal spacing.")
            steps.append(f"Key: 3 | 4 means 34. (Here, {rows[0][0]} | {rows[0][1].split()[0] if rows[0][1] else '0'} means "
                         f"{lo}{rows[0][1].split()[0] if rows[0][1] else '0'}.)")
            return _ok(steps, table(rows, ["Stem", "Leaves"]) + f"<br>n = {len(data)}")
        return _fail("Unknown chart type.")
    except ValueError as e:
        return _fail(str(e))


# ---------------------------------------------------------- mean problems --

def _lin(tok):
    """parse 'k', '2k', 'k+3', '2k-1', '5' -> (a, b) meaning a*k + b"""
    t = tok.replace(" ", "").lower()
    m = re.fullmatch(r"([+-]?\d*)k(?:([+-]\d+))?", t)
    if m:
        a = m.group(1)
        a = 1 if a in ("", "+") else -1 if a == "-" else int(a)
        b = int(m.group(2)) if m.group(2) else 0
        return Fraction(a), Fraction(b)
    m = re.fullmatch(r"([+-]?\d+)([+-]\d*)k", t)
    if m:
        b = int(m.group(1))
        a = m.group(2)
        a = 1 if a == "+" else -1 if a == "-" else int(a)
        return Fraction(a), Fraction(b)
    return Fraction(0), sfrac(t)


def _lin_str(a, b):
    out = ""
    if a != 0:
        out += ("" if a == 1 else MINUS if a == -1 else fmt(a)) + "k" if a > 0 or a == -1 else f"{MINUS}{fmt(-a)}k"
    if b != 0:
        if out:
            out += f" {'+' if b > 0 else MINUS} {fmt(abs(b))}"
        else:
            out = fmt(b)
    return out or "0"


def mean_problem(kind, **kw):
    try:
        if kind == "missing-value":
            toks = [t for t in re.split(r"[,;\s]+", str(kw.get("values", "")).strip()) if t]
            known, unknown = [], 0
            for t in toks:
                if t.lower() in ("x", "?"):
                    unknown += 1
                else:
                    known.append(sfrac(t))
            if unknown != 1:
                return _fail("Write exactly one x for the missing value, e.g. 5, 8, x, 12, 6.")
            mean = sfrac(kw.get("mean", ""))
            n = len(known) + 1
            S = sum(known)
            steps = [f"There are {n} numbers, so n = {n}.",
                     f"mean = {FR('sum of the numbers', 'n')} &nbsp;&rarr;&nbsp; {fmt(mean)} = {FR(f'{fmt(S)} + x', n)}",
                     f"Multiply both sides by {n}: {fmt(mean * n)} = {fmt(S)} + x",
                     f"x = {fmt(mean * n)} {MINUS} {fmt(S)} = {fmt(mean * n - S)}"]
            return _ok(steps, f"x = {fmt(mean * n - S)}")
        if kind == "missing-freq":
            xs = parse_nums(kw.get("values", ""), "values")
            toks = [t for t in re.split(r"[,;]+", str(kw.get("freqs", "")).strip()) if t.strip()]
            if len(xs) != len(toks):
                return _fail("The number of values and frequencies must match. Write the unknown frequency as k (or 2k, k+1 ...).")
            mean = sfrac(kw.get("mean", ""))
            lins = [_lin(t) for t in toks]
            if sum(1 for a, _ in lins if a != 0) == 0:
                return _fail("Write the unknown frequency as k, e.g. 3, 5, k, 4.")
            sa = sum(a for a, _ in lins)
            sb = sum(b for _, b in lins)
            fa = sum(x * a for x, (a, _) in zip(xs, lins))
            fb = sum(x * b for x, (_, b) in zip(xs, lins))
            rows = [[fmt(x), _lin_str(a, b), _lin_str(x * a, x * b)] for x, (a, b) in zip(xs, lins)]
            rows.append(["", f"&Sigma;f = {_lin_str(sa, sb)}", f"&Sigma;fx = {_lin_str(fa, fb)}"])
            steps = ["Make a table and find &Sigma;f and &Sigma;fx (they will contain k):" + table(rows, ["x", "f", "fx"]),
                     f"mean = {FR('&Sigma;fx', '&Sigma;f')} &nbsp;&rarr;&nbsp; {fmt(mean)} = {FR(_lin_str(fa, fb), _lin_str(sa, sb))}",
                     f"Multiply both sides by ({_lin_str(sa, sb)}): {fmt(mean)}({_lin_str(sa, sb)}) = {_lin_str(fa, fb)}"]
            L = _lin_str(mean * sa, mean * sb)
            steps.append(f"{L} = {_lin_str(fa, fb)}")
            den = mean * sa - fa
            if den == 0:
                return _fail("No value of k works here (the k terms cancel out). Please check the numbers in the question.")
            k = (fb - mean * sb) / den
            steps.append(f"Collect the k terms on one side: ({fmt(mean * sa)} {MINUS} {fmt(fa)})k = {fmt(fb)} {MINUS} {fmt(mean * sb)}")
            steps.append(f"{fmt(den)}k = {fmt(fb - mean * sb)} &nbsp;&rarr;&nbsp; k = {fmt(k)}")
            if k < 0 or k.denominator != 1:
                steps.append("(A frequency should be a whole number - check the question's numbers.)")
            return _ok(steps, f"k = {fmt(k)}")
        if kind == "combined":
            n1, m1 = sfrac(kw["n1"]), sfrac(kw["m1"])
            n2, m2 = sfrac(kw["n2"]), sfrac(kw["m2"])
            if n1 + n2 == 0:
                return _fail("The numbers of items cannot both be zero.")
            steps = ["Total of group 1 = n<sub>1</sub> &times; mean<sub>1</sub> = " f"{fmt(n1)} {MUL} {fmt(m1)} = {fmt(n1 * m1)}",
                     f"Total of group 2 = {fmt(n2)} {MUL} {fmt(m2)} = {fmt(n2 * m2)}",
                     f"Combined mean = {FR('total of both groups', 'total number of items')} = {FR(f'{fmt(n1 * m1)} + {fmt(n2 * m2)}', f'{fmt(n1)} + {fmt(n2)}')}",
                     f"= {FR(fmt(n1 * m1 + n2 * m2), fmt(n1 + n2))} = {fmt((n1 * m1 + n2 * m2) / (n1 + n2))}"]
            return _ok(steps, f"Combined mean = {fmt((n1 * m1 + n2 * m2) / (n1 + n2))}")
        if kind == "add-remove":
            n, m, v = sfrac(kw["n"]), sfrac(kw["mean"]), sfrac(kw["value"])
            add = str(kw.get("action", "add")) != "remove"
            S = n * m
            steps = [f"Original total = n {MUL} mean = {fmt(n)} {MUL} {fmt(m)} = {fmt(S)}"]
            if add:
                S2, n2 = S + v, n + 1
                steps.append(f"Add {fmt(v)}: new total = {fmt(S)} + {fmt(v)} = {fmt(S2)}; new number of items = {fmt(n2)}")
            else:
                S2, n2 = S - v, n - 1
                if n2 <= 0:
                    return _fail("You cannot remove the only item.")
                steps.append(f"Remove {fmt(v)}: new total = {fmt(S)} {MINUS} {fmt(v)} = {fmt(S2)}; new number of items = {fmt(n2)}")
            steps.append(f"New mean = {FR(fmt(S2), fmt(n2))} = {fmt(S2 / n2)}")
            return _ok(steps, f"New mean = {fmt(S2 / n2)}")
        if kind == "weighted":
            xs = parse_nums(kw.get("values", ""), "values")
            ws = parse_nums(kw.get("weights", ""), "weights")
            if len(xs) != len(ws):
                return _fail("The number of values and weights must match.")
            sw = sum(ws)
            if sw == 0:
                return _fail("The weights add up to zero.")
            swx = sum(x * w for x, w in zip(xs, ws))
            rows = [[fmt(x), fmt(w), fmt(x * w)] for x, w in zip(xs, ws)]
            rows.append(["", f"&Sigma;w = {fmt(sw)}", f"&Sigma;wx = {fmt(swx)}"])
            steps = ["Multiply each value by its weight:" + table(rows, ["x", "weight w", "w &times; x"]),
                     f"Weighted mean = {FR('&Sigma;wx', '&Sigma;w')} = {FR(fmt(swx), fmt(sw))} = {fmt(swx / sw)}"]
            return _ok(steps, f"Weighted mean = {fmt(swx / sw)}")
        return _fail("Unknown problem type.")
    except (ValueError, KeyError, ZeroDivisionError):
        return _fail("Please check the numbers you typed - something could not be read.")


# ---------------------------------------------------------- probability ----

def _pfrac(s, label="probability"):
    t = str(s).strip().replace("%", "")
    pct = "%" in str(s)
    try:
        m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", t)
        v = Fraction(m.group(1)) / Fraction(m.group(2)) if m else sfrac(t)
    except (ValueError, ZeroDivisionError):
        raise ValueError(f"Please type {label} as a fraction (3/8), decimal (0.375) or percentage (37.5%).")
    if pct:
        v /= 100
    if not (0 <= v <= 1):
        raise ValueError(f"A probability must be between 0 and 1 - check {label}.")
    return v


def prob_simple(favourable, total):
    try:
        f, t = sfrac(favourable), sfrac(total)
        if f.denominator != 1 or t.denominator != 1 or t <= 0 or f < 0 or f > t:
            return _fail("Use whole numbers, with the favourable outcomes not more than the total outcomes.")
        p = f / t
        steps = [f"Probability = {FR('number of favourable outcomes', 'total number of possible outcomes')}",
                 f"P = {FR(int(f), int(t))} = {fr(p)}",
                 f"As a decimal: {fmt(p)} &nbsp;|&nbsp; as a percentage: {fmt(p * 100)}%",
                 f"Probability of it <b>not</b> happening = 1 {MINUS} {fr(p)} = {fr(1 - p)}"]
        return _ok(steps, f"P = {fr(p)}")
    except ValueError:
        return _fail("Please type whole numbers.")


def prob_combined(pa, pb, relation="independent", pab=""):
    try:
        a, b = _pfrac(pa, "P(A)"), _pfrac(pb, "P(B)")
        steps = [f"P(A) = {fr(a)}, &nbsp; P(B) = {fr(b)}"]
        if relation == "independent":
            both = a * b
            steps.append("<b>Independent events</b> (one does not affect the other): P(A and B) = P(A) &times; P(B)")
            steps.append(f"P(A and B) = {fr(a)} {MUL} {fr(b)} = {fr(both)}")
        elif relation == "exclusive":
            both = Fraction(0)
            steps.append("<b>Mutually exclusive events</b> (they cannot happen together): P(A and B) = 0")
        else:
            if not str(pab).strip():
                return _fail("For events that are neither independent nor exclusive, please give P(A and B).")
            both = _pfrac(pab, "P(A and B)")
            steps.append(f"P(A and B) = {fr(both)} (given)")
        either = a + b - both
        if either > 1:
            return _fail("These probabilities are not possible together (P(A or B) would be more than 1).")
        steps.append(f"<b>P(A or B)</b> = P(A) + P(B) {MINUS} P(A and B) = {fr(a)} + {fr(b)} {MINUS} {fr(both)} = {fr(either)}")
        steps.append(f"<b>P(neither A nor B)</b> = 1 {MINUS} P(A or B) = 1 {MINUS} {fr(either)} = {fr(1 - either)}")
        steps.append(f"<b>P(A only)</b> = P(A) {MINUS} P(A and B) = {fr(a - both)}; &nbsp; <b>P(B only)</b> = {fr(b - both)}")
        steps.append(f"<b>P(A not happening)</b> = 1 {MINUS} {fr(a)} = {fr(1 - a)}")
        res = f"P(A and B) = {fr(both)}<br>P(A or B) = {fr(either)}"
        return _ok(steps, res)
    except ValueError as e:
        return _fail(str(e))


def _tree_png(items, probs_first, second_probs, labels, replace):
    plt = _mpl()
    k = len(items)
    fig, ax = plt.subplots(figsize=(7.4, 1.1 * k * k * 0.6 + 2))
    ax.axis("off")
    ys1 = [(k - 1 - i) * k + (k - 1) / 2 for i in range(k)]
    root = (0, (k * k - 1) / 2)
    for i, nm in enumerate(items):
        ax.plot([root[0], 1], [root[1], ys1[i]], color="#334155")
        ax.text(0.5, (root[1] + ys1[i]) / 2 + 0.12, str(probs_first[i]), fontsize=8, ha="center", color="#1d4ed8")
        ax.text(1.02, ys1[i], nm, va="center", fontsize=9, weight="bold")
        for j, nm2 in enumerate(items):
            y2 = (k - 1 - i) * k + (k - 1 - j)
            ax.plot([1.35, 2.2], [ys1[i], y2], color="#334155")
            ax.text(1.8, (ys1[i] + y2) / 2 + 0.1, str(second_probs[i][j]), fontsize=8, ha="center", color="#1d4ed8")
            ax.text(2.25, y2, f"{nm},{nm2}  =  {labels[i][j]}", va="center", fontsize=8)
    ax.text(-0.02, root[1], "start", ha="right", va="center", fontsize=8)
    ax.set_xlim(-0.2, 3.6)
    ax.set_ylim(-0.8, k * k - 0.2)
    ax.set_title("Tree diagram (" + ("with" if replace else "without") + " replacement)", fontsize=10)
    return _fig_to_b64(fig)


def prob_draw(items_text, draws=2, replacement="no", sequence=""):
    try:
        items = []
        for p in split_list(items_text):
            m = re.fullmatch(r"(.+?)\s*[:=]\s*(\d+)", p)
            if not m:
                return _fail("Write the items like red:5, blue:3, green:2 (name : how many).")
            items.append((m.group(1).strip(), int(m.group(2))))
        if len(items) < 1 or len(items) > 4:
            return _fail("Please use between one and four different kinds of items.")
        names = [n for n, _ in items]
        if len(set(n.lower() for n in names)) != len(names):
            return _fail("Each kind of item needs a different name.")
        counts = [c for _, c in items]
        T = sum(counts)
        if T < 2 or T > 200:
            return _fail("Use between 2 and 200 items in total.")
        draws = int(draws)
        if draws not in (1, 2, 3):
            return _fail("This solver handles 1, 2 or 3 draws.")
        repl = str(replacement).lower() in ("yes", "true", "with", "1")
        if not repl and draws > T:
            return _fail("You cannot draw more items than there are.")
        steps = [f"Total number of items = {' + '.join(map(str, counts))} = {T}"]
        for n, c in items:
            steps.append(f"P({esc(n)}) on the first draw = {FR(c, T)}" + (f" = {fr(Fraction(c, T))}" if Fraction(c, T).denominator != T else ""))
        steps.append("With replacement: the item is put back, so the probabilities <b>stay the same</b> on every draw." if repl else
                     "Without replacement: the item is <b>not</b> put back, so the total (and the number of that colour) <b>goes down</b> for the next draw.")
        k = len(items)
        outcomes = {}
        for seq in product(range(k), repeat=draws):
            rem = list(counts)
            tot = T
            p = Fraction(1)
            for idx in seq:
                if rem[idx] <= 0:
                    p = Fraction(0)
                    break
                p *= Fraction(rem[idx], tot)
                if not repl:
                    rem[idx] -= 1
                    tot -= 1
            outcomes[seq] = p
        # sequences table
        if len(outcomes) <= 16:
            rows = []
            for seq, p in outcomes.items():
                if p == 0:
                    continue
                if draws == 2:
                    i, j = seq
                    c1 = Fraction(counts[i], T)
                    if repl:
                        c2 = Fraction(counts[j], T)
                    else:
                        c2 = Fraction(counts[j] - (1 if i == j else 0), T - 1)
                    rows.append([", ".join(esc(names[s]) for s in seq), f"{fr(c1)} {MUL} {fr(c2)}", fr(p)])
                else:
                    rows.append([", ".join(esc(names[s]) for s in seq), "", fr(p)])
            steps.append("<b>All the possible outcomes</b> (multiply along the branches of the tree):" + table(rows, ["Outcome", "Working", "Probability"]))
        total_check = sum(outcomes.values())
        steps.append(f"Check: all the probabilities add up to {fr(total_check)} (it must be 1).")
        res = []
        if k >= 2:
            same = sum(p for seq, p in outcomes.items() if len(set(seq)) == 1)
            diff = 1 - same
            steps.append(f"<b>P(all the same kind)</b> = add the outcomes that are all alike = {fr(same)}")
            steps.append(f"<b>P(not all the same)</b> = 1 {MINUS} {fr(same)} = {fr(diff)}")
            res.append(f"P(all same) = {fr(same)}, P(not all same) = {fr(diff)}")
        for ni, n in enumerate(names):
            atl = sum(p for seq, p in outcomes.items() if ni in seq)
            allk = outcomes.get(tuple([ni] * draws), Fraction(0))
            steps.append(f"<b>P(at least one {esc(n)})</b> = 1 {MINUS} P(no {esc(n)}) = {fr(atl)}; "
                         f"<b>P(all {esc(n)})</b> = {fr(allk)}")
            res.append(f"P(at least one {esc(n)}) = {fr(atl)}")
        if str(sequence).strip():
            seqn = [s.strip() for s in re.split(r"[,;>]+", str(sequence)) if s.strip()]
            lowmap = {n.lower(): i for i, n in enumerate(names)}
            if len(seqn) != draws or any(s.lower() not in lowmap for s in seqn):
                return _fail(f"Your event must list {draws} item name(s) from your list, e.g. {', '.join(names[:draws] if draws <= k else names)}.")
            idx = tuple(lowmap[s.lower()] for s in seqn)
            ps = outcomes[idx]
            steps.append(f"<b>P({' then '.join(esc(s) for s in seqn)})</b> (in that order) = {fr(ps)}")
            res.append(f"P({' then '.join(esc(s) for s in seqn)}) = {fr(ps)}")
            if len(set(idx)) > 1:
                anyo = sum(p for seq, p in outcomes.items() if sorted(seq) == sorted(idx))
                steps.append(f"<b>P(the same items in any order)</b> = add the orders: {fr(anyo)}")
                res.append(f"P(any order) = {fr(anyo)}")
        out = {"ok": True, "steps": steps, "result": "<br>".join(res), "error": None}
        if draws == 2 and k <= 4:
            probs_first = [fr(Fraction(counts[i], T)).replace("&minus;", "-") for i in range(k)]
            sec = []
            lab = []
            for i in range(k):
                row, lrow = [], []
                for j in range(k):
                    c2 = Fraction(counts[j] - (0 if repl else (1 if i == j else 0)), T if repl else T - 1)
                    row.append(_plain(c2))
                    lrow.append(_plain(outcomes[(i, j)]))
                sec.append(row)
                lab.append(lrow)
            first = [_plain(Fraction(counts[i], T)) for i in range(k)]
            out["result"] = {"image": _tree_png(names, first, sec, lab, repl), "text": "<br>".join(res)}
        return out
    except (ValueError, KeyError) as e:
        return _fail(str(e) or "Please check what you typed.")


def _plain(x):
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def prob_dice_coins(kind, event="", value="", n="2"):
    try:
        if kind == "one-die":
            v = int(value) if str(value).strip() else 0
            S = [1, 2, 3, 4, 5, 6]
            ev = {
                "even": [s for s in S if s % 2 == 0], "odd": [s for s in S if s % 2], "prime": [2, 3, 5],
                "greater": [s for s in S if s > v], "less": [s for s in S if s < v],
                "multiple": [s for s in S if v and s % v == 0], "equal": [s for s in S if s == v],
            }.get(event)
            if ev is None:
                return _fail("Choose an event.")
            nm = {"even": "an even number", "odd": "an odd number", "prime": "a prime number",
                  "greater": f"a number greater than {v}", "less": f"a number less than {v}",
                  "multiple": f"a multiple of {v}", "equal": f"the number {v}"}[event]
            steps = ["Sample space (all the possible outcomes of one throw) = {1, 2, 3, 4, 5, 6}, so there are 6 outcomes.",
                     f"Outcomes giving {nm}: {{{', '.join(map(str, ev)) or 'none'}}} &nbsp;&rarr;&nbsp; {len(ev)} outcome(s)",
                     f"P = {FR(len(ev), 6)} = {fr(Fraction(len(ev), 6))}"]
            return _ok(steps, f"P({nm}) = {fr(Fraction(len(ev), 6))}")
        if kind == "two-dice":
            v = int(value) if str(value).strip() else 0
            tests = {
                "sum-equal": (lambda a, b: a + b == v, f"the sum is {v}"),
                "sum-greater": (lambda a, b: a + b > v, f"the sum is greater than {v}"),
                "sum-less": (lambda a, b: a + b < v, f"the sum is less than {v}"),
                "product-equal": (lambda a, b: a * b == v, f"the product is {v}"),
                "doubles": (lambda a, b: a == b, "both dice show the same number (a double)"),
                "sum-even": (lambda a, b: (a + b) % 2 == 0, "the sum is even"),
                "sum-prime": (lambda a, b: (a + b) in (2, 3, 5, 7, 11), "the sum is a prime number"),
            }
            if event not in tests:
                return _fail("Choose an event.")
            fn, nm = tests[event]
            fav = [(a, b) for a in range(1, 7) for b in range(1, 7) if fn(a, b)]
            hdr = ["1st \\ 2nd"] + [str(b) for b in range(1, 7)]
            rows = []
            for a in range(1, 7):
                row = [f"<b>{a}</b>"]
                for b in range(1, 7):
                    mark = f"({a},{b})"
                    row.append(f'<span class="hl">{mark}</span>' if fn(a, b) else mark)
                rows.append(row)
            steps = ["When two dice are thrown there are 6 &times; 6 = <b>36</b> equally likely outcomes (sample space):" + table(rows, hdr),
                     f"Outcomes where {nm} (highlighted): {len(fav)}",
                     "They are: " + ", ".join(f"({a},{b})" for a, b in fav) if fav else "There are no such outcomes.",
                     f"P = {FR(len(fav), 36)} = {fr(Fraction(len(fav), 36))}"]
            return _ok(steps, f"P({nm}) = {fr(Fraction(len(fav), 36))}")
        if kind == "coins":
            nn = int(n)
            if not (1 <= nn <= 12):
                return _fail("Use between 1 and 12 coins.")
            k = int(value) if str(value).strip() else 0
            if k < 0 or k > nn:
                return _fail(f"The number of heads must be between 0 and {nn}.")
            tot = 2 ** nn
            if event == "exactly":
                fav = comb(nn, k)
                nm = f"exactly {k} head(s)"
            elif event == "atleast":
                fav = sum(comb(nn, j) for j in range(k, nn + 1))
                nm = f"at least {k} head(s)"
            else:
                fav = sum(comb(nn, j) for j in range(0, k + 1))
                nm = f"at most {k} head(s)"
            steps = [f"Tossing {nn} coin(s): each shows H or T, so there are 2<sup>{nn}</sup> = {tot} equally likely outcomes.",
                     "Number of ways of getting j heads = <sup>n</sup>C<sub>j</sub> (choose which coins are heads):",
                     ", ".join(f"{j} head(s): {comb(nn, j)}" for j in range(nn + 1)),
                     f"Ways to get {nm} = {fav}",
                     f"P = {FR(fav, tot)} = {fr(Fraction(fav, tot))}"]
            return _ok(steps, f"P({nm}) = {fr(Fraction(fav, tot))}")
        return _fail("Unknown experiment.")
    except (ValueError, KeyError):
        return _fail("Please check the numbers you typed.")


# -------------------------------------------------- permutations etc. ------

def _prod_expansion(n, r):
    return f" {MUL} ".join(str(n - i) for i in range(r))


def perm_comb(kind, n="", r=""):
    try:
        nn = int(str(n).strip())
        if nn < 0 or nn > 100:
            return _fail("Use a whole number n between 0 and 100.")
        if kind == "factorial":
            f = factorial(nn)
            steps = [f"n! means n {MUL} (n&minus;1) {MUL} (n&minus;2) {MUL} ... {MUL} 2 {MUL} 1"]
            if 1 < nn <= 15:
                steps.append(f"{nn}! = {' &times; '.join(str(nn - i) for i in range(nn))} = {f}")
            else:
                steps.append(f"{nn}! = {f}")
            steps.append("(Remember: 0! = 1.)")
            return _ok(steps, f"{nn}! = {f}")
        if kind == "circular":
            if nn < 1:
                return _fail("Use at least 1 object.")
            f = factorial(nn - 1)
            steps = ["Arranging n different objects around a circle: fix one object (rotations look the same), arrange the rest in a line.",
                     f"Number of ways = (n &minus; 1)! = ({nn} &minus; 1)! = {nn - 1}! = {f}"]
            return _ok(steps, f"{f} ways")
        rr = int(str(r).strip())
        if rr < 0 or rr > nn:
            return _fail("r must be between 0 and n (you cannot choose more than there are).")
        if kind == "perm":
            v = perm(nn, rr)
            steps = [f"A <b>permutation</b> counts arrangements where <b>order matters</b>.",
                     f"<sup>n</sup>P<sub>r</sub> = {FR('n!', '(n &minus; r)!')} &nbsp;with n = {nn}, r = {rr}",
                     f"<sup>{nn}</sup>P<sub>{rr}</sub> = {FR(f'{nn}!', f'{nn - rr}!')}"]
            if 1 <= rr <= 12:
                steps.append(f"= {_prod_expansion(nn, rr)} (multiply {rr} number{'s' if rr != 1 else ''}, starting from {nn} and going down)")
            steps.append(f"= {v}")
            return _ok(steps, f"<sup>{nn}</sup>P<sub>{rr}</sub> = {v}")
        if kind == "comb":
            v = comb(nn, rr)
            steps = ["A <b>combination</b> counts selections where <b>order does not matter</b> (choosing a group).",
                     f"<sup>n</sup>C<sub>r</sub> = {FR('n!', 'r!(n &minus; r)!')} &nbsp;with n = {nn}, r = {rr}",
                     f"<sup>{nn}</sup>C<sub>{rr}</sub> = {FR(f'{nn}!', f'{rr}! {MUL} {nn - rr}!')}"]
            if 1 <= rr <= 12:
                bot = f" {MUL} ".join(str(rr - i) for i in range(rr))
                steps.append(f"= {FR(_prod_expansion(nn, rr), bot)}")
            steps.append(f"= {v}")
            if rr != nn - rr:
                steps.append(f"(Shortcut check: <sup>{nn}</sup>C<sub>{rr}</sub> = <sup>{nn}</sup>C<sub>{nn - rr}</sub> = {comb(nn, nn - rr)})")
            return _ok(steps, f"<sup>{nn}</sup>C<sub>{rr}</sub> = {v}")
        return _fail("Unknown type.")
    except ValueError:
        return _fail("Please type whole numbers for n and r.")


def arrangements(word, condition="none", letters=""):
    try:
        w = re.sub(r"[^A-Za-z]", "", str(word)).upper()
        if len(w) < 2 or len(w) > 15:
            return _fail("Type a word with 2 to 15 letters.")
        n = len(w)
        cnt = {}
        for ch in w:
            cnt[ch] = cnt.get(ch, 0) + 1
        reps = {ch: c for ch, c in cnt.items() if c > 1}
        steps = [f"The word <b>{w}</b> has n = {n} letters."]
        if reps:
            steps.append("Repeated letters: " + ", ".join(f"{ch} appears {c} times" for ch, c in reps.items()) +
                         ". Swapping identical letters gives nothing new, so we divide by the factorial of each repeat.")
        else:
            steps.append("All the letters are different.")
        den = 1
        for c in reps.values():
            den *= factorial(c)
        base = factorial(n) // den
        denstr = " &times; ".join(f"{c}!" for c in reps.values())
        if condition == "none":
            if reps:
                steps.append(f"Arrangements = {FR(f'{n}!', denstr)} = {FR(factorial(n), den)} = {base}")
            else:
                steps.append(f"Arrangements = {n}! = {base}")
            return _ok(steps, f"{base} arrangements")
        if condition == "together":
            grp = re.sub(r"[^A-Za-z]", "", str(letters).upper())
            if str(letters).strip().lower() == "vowels":
                grp = "AEIOU"
            gl = [ch for ch in w if ch in grp]
            if not gl:
                return _fail("None of those letters are in the word.")
            others = [ch for ch in w if ch not in grp]
            g = len(gl)
            units = len(others) + 1
            ocnt, gcnt = {}, {}
            for ch in others:
                ocnt[ch] = ocnt.get(ch, 0) + 1
            for ch in gl:
                gcnt[ch] = gcnt.get(ch, 0) + 1
            od = 1
            for c in ocnt.values():
                od *= factorial(c)
            gd = 1
            for c in gcnt.values():
                gd *= factorial(c)
            outer = factorial(units) // od
            inner = factorial(g) // gd
            steps.append(f"The letters to keep together are {', '.join(sorted(set(gl)))} ({g} letters in {w}). Tie them into <b>one block</b>.")
            steps.append(f"Now arrange {units} things: the block and the other {len(others)} letters ({''.join(others) or 'none'}).")
            steps.append(f"Ways to arrange these {units} things = {units}!" + (f" &divide; ({' &times; '.join(f'{c}!' for c in ocnt.values() if c > 1)})" if any(c > 1 for c in ocnt.values()) else "") + f" = {outer}")
            steps.append(f"Ways to arrange the {g} letters <i>inside</i> the block = {g}!" + (f" &divide; ({' &times; '.join(f'{c}!' for c in gcnt.values() if c > 1)})" if any(c > 1 for c in gcnt.values()) else "") + f" = {inner}")
            steps.append(f"Total = {outer} &times; {inner} = {outer * inner}")
            return _ok(steps, f"{outer * inner} arrangements")
        if condition in ("starts", "ends"):
            ch = re.sub(r"[^A-Za-z]", "", str(letters).upper())[:1]
            if not ch or ch not in cnt:
                return _fail("Choose a letter that is in the word.")
            rest = dict(cnt)
            rest[ch] -= 1
            d2 = 1
            for c in rest.values():
                d2 *= factorial(c)
            v = factorial(n - 1) // d2
            steps.append(f"Fix {ch} at the {'beginning' if condition == 'starts' else 'end'}. Arrange the other {n - 1} letters.")
            rep2 = {k: c for k, c in rest.items() if c > 1}
            if rep2:
                steps.append(f"Ways = {FR(f'{n - 1}!', ' &times; '.join(f'{c}!' for c in rep2.values()))} = {v}")
            else:
                steps.append(f"Ways = {n - 1}! = {v}")
            return _ok(steps, f"{v} arrangements")
        return _fail("Unknown condition.")
    except ValueError:
        return _fail("Please check what you typed.")
