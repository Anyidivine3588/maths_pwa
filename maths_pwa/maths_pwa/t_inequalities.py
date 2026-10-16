"""Inequalities: linear, compound, quadratic/rational (sign table), region graphs, linear programming."""
import base64
import io
import math
import re
from fractions import Fraction
import topics
import poly as P
from tcommon import *
from frac_numeric import _ok, _fail

INF = float("inf")
OPS = {"<": "<", "<=": "&le;", ">": ">", ">=": "&ge;"}
FLIP = {"<": ">", "<=": ">=", ">": "<", ">=": "<="}


def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _b64(fig):
    plt = _mpl()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


# ----------------------------------------------------------------- parsing --

def _clean(s):
    s = P.normalise(s or "")
    s = s.replace("≤", "<=").replace("≥", ">=").replace("=<", "<=").replace("=>", ">=").replace("≠", "!=")
    return s


def _split_rel(text):
    parts = re.split(r"(<=|>=|<|>)", _clean(text))
    if len(parts) < 3 or len(parts) > 5:
        raise UErr("Write an inequality using &lt;, &gt;, &le; (&lt;=) or &ge; (&gt;=), for example 2x - 3 &gt; 7.")
    exprs = [p.strip() for p in parts[0::2]]
    ops = parts[1::2]
    if any(e == "" for e in exprs):
        raise UErr("Something is missing next to the inequality sign.")
    return exprs, ops


def _pp(text, label="expression"):
    try:
        return P.parse_poly(text)
    except P.ParseError as e:
        raise UErr(str(e))
    except Exception:
        raise UErr(f"I could not read the {label} '{esc(text)}'.")


def _rf(text):
    try:
        return P.ast_eval(P.parse_ast(text))
    except P.ParseError as e:
        raise UErr(str(e))
    except (RecursionError, ValueError, OverflowError):
        raise UErr("That expression is too complicated for me.")


def _ptxt(p):
    return P.poly_str(p) if not p.is_zero() else "0"


# --------------------------------------------------------------- intervals --
# interval = (lo, hi, lo_incl, hi_incl, lo_txt, hi_txt)   lo/hi floats

def pt_txt(x):
    if isinstance(x, Fraction):
        return fr(x)
    return fm(Fraction(x).limit_denominator(10 ** 6), 3)


def mk(lo, hi, li, hi_i):
    return (float(lo) if lo is not None else -INF, float(hi) if hi is not None else INF, li, hi_i,
            pt_txt(lo) if lo is not None else "&minus;&infin;", pt_txt(hi) if hi is not None else "&infin;")


def _ival_one(x, op, val):
    """x op val"""
    if op == "<":
        return [mk(None, val, False, False)]
    if op == "<=":
        return [mk(None, val, False, True)]
    if op == ">":
        return [mk(val, None, False, False)]
    return [mk(val, None, True, False)]


def intersect(A, B):
    out = []
    for a in A:
        for b in B:
            lo, li, lt = (a[0], a[2], a[4]) if (a[0], not a[2]) > (b[0], not b[2]) else (b[0], b[2], b[4])
            if a[0] == b[0]:
                li = a[2] and b[2]
                lt = a[4]
            hi, hi_i, ht = (a[1], a[3], a[5]) if (a[1], a[3]) < (b[1], b[3]) else (b[1], b[3], b[5])
            if a[1] == b[1]:
                hi_i = a[3] and b[3]
                ht = a[5]
            if lo < hi or (lo == hi and li and hi_i):
                out.append((lo, hi, li, hi_i, lt, ht))
    return normalise(out)


def union(A, B):
    return normalise(list(A) + list(B))


def normalise(iv):
    iv = sorted(iv, key=lambda t: (t[0], not t[2]))
    out = []
    for t in iv:
        if out:
            p = out[-1]
            if t[0] < p[1] or (t[0] == p[1] and (t[2] or p[3])):
                if t[1] > p[1] or (t[1] == p[1] and t[3]):
                    out[-1] = (p[0], t[1], p[2], t[3], p[4], t[5])
                continue
        out.append(t)
    return out


def set_words(iv, v="x"):
    if not iv:
        return "no solution (the empty set)"
    parts = []
    for lo, hi, li, hi_i, lt, ht in iv:
        if lo == -INF and hi == INF:
            parts.append(f"{v} can be any real number")
        elif lo == -INF:
            parts.append(f"{v} {OPS['<=' if hi_i else '<']} {ht}")
        elif hi == INF:
            parts.append(f"{v} {OPS['>=' if li else '>']} {lt}")
        elif lo == hi:
            parts.append(f"{v} = {lt}")
        else:
            parts.append(f"{lt} {OPS['<=' if li else '<']} {v} {OPS['<=' if hi_i else '<']} {ht}")
    return " &nbsp;or&nbsp; ".join(parts)


def interval_words(iv):
    if not iv:
        return "&empty;"
    parts = []
    for lo, hi, li, hi_i, lt, ht in iv:
        if lo == hi:
            parts.append("{" + lt + "}")
        else:
            parts.append(("[" if li else "(") + lt + ", " + ht + ("]" if hi_i else ")"))
    return " &cup; ".join(parts)


def int_list(iv, domain):
    if domain == "real":
        return None
    lo_allowed = {"int": -10 ** 9, "nat": 1, "whole": 0}[domain]
    vals = []
    inf = False
    for lo, hi, li, hi_i, _, _ in iv:
        a = lo_allowed if lo == -INF else max(lo_allowed, math.floor(lo) + (0 if li and lo == math.floor(lo) else 1))
        if lo != -INF and lo == math.floor(lo) and li:
            a = max(lo_allowed, int(lo))
        elif lo != -INF:
            a = max(lo_allowed, math.floor(lo) + 1)
        if hi == INF:
            inf = True
            b = a + 4
        else:
            b = math.floor(hi) if (hi_i or hi != math.floor(hi)) else math.floor(hi) - 1
        if lo == -INF and domain == "int":
            inf = True
            a = b - 4
        if b - a > 60 and hi != INF and lo != -INF:
            return "too many to list"
        for k in range(int(a), int(b) + 1):
            vals.append(k)
    vals = sorted(set(vals))
    return vals, inf


def int_text(iv, domain):
    r = int_list(iv, domain)
    if r is None:
        return ""
    if r == "too many to list":
        return "<br>There are too many whole-number solutions to list."
    vals, inf = r
    name = {"int": "integers", "nat": "natural numbers", "whole": "whole numbers"}[domain]
    if not vals:
        return f"<br>There are no {name} in the solution."
    txt = ", ".join(str(v) for v in vals) + (", ..." if inf else "")
    pre = "..., " if (inf and iv and iv[0][0] == -INF) else ""
    return f"<br>Solution in {name}: {{ {pre if pre else ''}{txt if not pre else ', '.join(str(v) for v in vals)} }}" if not pre else f"<br>Solution in {name}: {{ ..., {', '.join(str(v) for v in vals)} }}"


# --------------------------------------------------------------- number line --

def numberline(iv, var="x", extra_pts=()):
    plt = _mpl()
    pts = []
    for lo, hi, *_ in iv:
        for v in (lo, hi):
            if abs(v) != INF:
                pts.append(v)
    pts += list(extra_pts)
    if not pts:
        pts = [0]
    mn, mx = min(pts), max(pts)
    span = max(mx - mn, 2.0)
    a, b = math.floor(mn - span * 0.5 - 1), math.ceil(mx + span * 0.5 + 1)
    step = 1 if b - a <= 20 else max(1, round((b - a) / 14))
    fig, ax = plt.subplots(figsize=(8, 1.7))
    ax.axhline(0, color="#374151", lw=1.6, zorder=1)
    ax.annotate("", xy=(b + 0.3, 0), xytext=(b, 0), arrowprops=dict(arrowstyle="->", color="#374151", lw=1.6))
    ax.annotate("", xy=(a - 0.3, 0), xytext=(a, 0), arrowprops=dict(arrowstyle="->", color="#374151", lw=1.6))
    for t in range(int(a), int(b) + 1, int(step)):
        ax.plot([t, t], [-0.08, 0.08], color="#374151", lw=1.2)
        ax.text(t, -0.28, str(t), ha="center", va="top", fontsize=9)
    for lo, hi, li, hi_i, lt, ht in iv:
        x0 = a - 0.3 if lo == -INF else lo
        x1 = b + 0.3 if hi == INF else hi
        ax.plot([x0, x1], [0, 0], color="#4f46e5", lw=5, solid_capstyle="butt", zorder=2, alpha=.85)
        if lo == -INF:
            ax.annotate("", xy=(a - 0.3, 0), xytext=(a + 0.6, 0), arrowprops=dict(arrowstyle="-|>", color="#4f46e5", lw=2.5))
        if hi == INF:
            ax.annotate("", xy=(b + 0.3, 0), xytext=(b - 0.6, 0), arrowprops=dict(arrowstyle="-|>", color="#4f46e5", lw=2.5))
        for v, incl in ((lo, li), (hi, hi_i)):
            if abs(v) != INF:
                ax.plot([v], [0], "o", ms=11, mfc="#4f46e5" if incl else "white", mec="#4f46e5", mew=2.2, zorder=3)
                if v != int(v) or v < a or v > b:
                    ax.text(v, 0.22, f"{v:.3g}", ha="center", fontsize=9, color="#4f46e5")
    ax.set_xlim(a - 0.8, b + 0.8)
    ax.set_ylim(-0.7, 0.6)
    ax.axis("off")
    ax.text(b + 0.7, 0.18, var, fontsize=12, style="italic", ha="right")
    return _b64(fig)


# -------------------------------------------------------------- linear solver --

def _lin_parts(L, R, var):
    """returns (a1,b1,a2,b2): L=a1 v+b1, R=a2 v+b2"""
    def co(p):
        if p.total_degree() > 1:
            raise UErr("This has a squared (or higher) term, so use the 'Quadratic &amp; fractions' tab for it.")
        a = Fraction(0)
        b = Fraction(0)
        for k, c in p.t.items():
            if k == ():
                b += c
            else:
                a += c
        return a, b
    a1, b1 = co(L)
    a2, b2 = co(R)
    return a1, b1, a2, b2


def _xt(a, v):
    """coefficient*variable text"""
    if a == 1:
        return v
    if a == -1:
        return MINUS + v
    return fm(a, 6) + v


def _lin_expr(a, b, v):
    out = ""
    if a != 0:
        out += (MINUS if a < 0 else "") + ("" if abs(a) == 1 else fm(abs(a), 6)) + v
    if b != 0:
        if out:
            out += f" {MINUS if b < 0 else '+'} {fm(abs(b), 6)}"
        else:
            out = (MINUS if b < 0 else "") + fm(abs(b), 6)
    return out or "0"


def solve_linear(Ltxt, op, Rtxt, steps, n=1):
    """returns (intervals, var)"""
    Lp, Rp = _pp(Ltxt), _pp(Rtxt)
    vs = sorted(set(Lp.vars()) | set(Rp.vars()))
    if len(vs) > 1:
        raise UErr("Use only one letter (like x) in this tab.")
    v = vs[0] if vs else "x"
    a1, b1, a2, b2 = _lin_parts(Lp, Rp, v)
    steps.append(f"<b>Step 1 - Simplify each side</b> (open brackets, collect like terms): "
                 f"left = {_lin_expr(a1, b1, v)}, right = {_lin_expr(a2, b2, v)}")
    steps.append(f"So the inequality is: {_lin_expr(a1, b1, v)} {OPS[op]} {_lin_expr(a2, b2, v)}")
    A = a1 - a2
    B = b2 - b1
    if a2 != 0:
        steps.append(f"<b>Step 2 - Get the {v}'s on the left.</b> Subtract {_xt(a2, v) if a2 > 0 else _lin_expr(a2, 0, v)} from both sides "
                     f"(the sign of the inequality stays the same when you add or subtract): {_lin_expr(A, b1, v)} {OPS[op]} {fm(b2, 6)}")
    if b1 != 0:
        steps.append(f"<b>Step 3 - Get the numbers on the right.</b> {'Subtract' if b1 > 0 else 'Add'} {fm(abs(b1), 6)} on both sides: "
                     f"{_lin_expr(A, 0, v)} {OPS[op]} {fm(B, 6)}")
    if A == 0:
        true = {"<": 0 < B, "<=": 0 <= B, ">": 0 > B, ">=": 0 >= B}[op]
        steps.append(f"The {v}'s have cancelled: 0 {OPS[op]} {fm(B, 6)} is {'TRUE' if true else 'FALSE'}.")
        steps.append("So " + ("every number works." if true else "no number works."))
        return ([mk(None, None, False, False)] if true else []), v
    newop = op
    if A != 1:
        if A < 0:
            newop = FLIP[op]
            steps.append(f"<b>Step 4 - Divide both sides by {fm(A, 6)}.</b> It is a <b>NEGATIVE</b> number, so the inequality sign must be "
                         f"<b>REVERSED</b>: {OPS[op]} becomes {OPS[newop]}.")
        else:
            steps.append(f"<b>Step 4 - Divide both sides by {fm(A, 6)}</b> (positive, so the sign stays the same).")
    val = B / A
    steps.append(f"<span class='hl'>{v} {OPS[newop]} {fr(val)}</span>" + ("" if val.denominator == 1 else f" &nbsp;({fm(val, 4)})"))
    return _ival_one(v, newop, val), v


# ---------------------------------------------------------------- linear tab --

@guard
def linear(d):
    text = (d.get("ineq") or "").strip()
    if not text or len(text) > 200:
        raise UErr("Type an inequality, for example 2x - 3 > 7.")
    domain = d.get("domain", "real")
    steps = []
    low = _clean(text)
    sub = re.split(r"\s+(and|or)\s+", low, flags=re.I)
    if len(sub) > 1:
        if len(sub) > 5:
            raise UErr("Please use at most three inequalities joined by and / or.")
        ivs = []
        joiners = [s.lower() for s in sub[1::2]]
        for i, s in enumerate(sub[0::2], 1):
            ex, ops = _split_rel(s)
            if len(ops) != 1:
                raise UErr("Write each part with one inequality sign when you join them with and / or.")
            steps.append(f"<b>Part {i}:</b> {esc(s)}")
            iv, var = solve_linear(ex[0], ops[0], ex[1], steps)
            ivs.append(iv)
        res = ivs[0]
        for j, iv in zip(joiners, ivs[1:]):
            if j == "and":
                steps.append("<b>'and'</b> means BOTH must be true: keep only the part where the solutions overlap (intersection).")
                res = intersect(res, iv)
            else:
                steps.append("<b>'or'</b> means EITHER can be true: put the solutions together (union).")
                res = union(res, iv)
        return _final(steps, res, var, domain)
    ex, ops = _split_rel(text)
    if len(ops) == 1:
        iv, var = solve_linear(ex[0], ops[0], ex[1], steps)
        return _final(steps, iv, var, domain)
    if len(ops) == 2:
        # compound  e1 op1 e2 op2 e3
        p1, p2, p3 = _pp(ex[0]), _pp(ex[1]), _pp(ex[2])
        vs = sorted(set(p1.vars()) | set(p2.vars()) | set(p3.vars()))
        if len(vs) > 1:
            raise UErr("Use only one letter (like x).")
        v = vs[0] if vs else "x"
        steps.append(f"<b>This is a compound inequality</b> (two signs). It means BOTH {esc(ex[0])} {OPS[ops[0]]} {esc(ex[1])} AND {esc(ex[1])} {OPS[ops[1]]} {esc(ex[2])} are true.")
        if p1.is_const() and p3.is_const() and not p2.is_const() and p2.total_degree() == 1:
            a, b = _lin_parts(p2, Poly0(), v)[:2]
            lo, hi = p1.const_value(), p3.const_value()
            o1, o2 = ops
            steps.append(f"<b>Method - work on all three parts at once.</b> The middle is {_lin_expr(a, b, v)}.")
            if b != 0:
                steps.append(f"{'Subtract' if b > 0 else 'Add'} {fm(abs(b), 6)} from ALL THREE parts: {fm(lo - b, 6)} {OPS[o1]} {_lin_expr(a, 0, v)} {OPS[o2]} {fm(hi - b, 6)}")
            lo2, hi2 = (lo - b), (hi - b)
            if a != 1:
                if a < 0:
                    steps.append(f"Divide ALL THREE parts by {fm(a, 6)}. It is negative, so reverse BOTH signs <b>and</b> swap the ends.")
                    lo2, hi2, o1, o2 = hi2 / a, lo2 / a, FLIP[o2], FLIP[o1]
                else:
                    steps.append(f"Divide ALL THREE parts by {fm(a, 6)} (positive, signs stay).")
                    lo2, hi2 = lo2 / a, hi2 / a
            steps.append(f"<span class='hl'>{fr(lo2)} {OPS[o1]} {v} {OPS[o2]} {fr(hi2)}</span>")
            if lo2 > hi2 or (lo2 == hi2 and not (o1 == "<=" and o2 == "<=")):
                res = []
            else:
                res = [mk(lo2, hi2, o1 == "<=", o2 == "<=")]
            return _final(steps, res, v, domain)
        steps.append("<b>Solve the first inequality:</b>")
        i1, _ = solve_linear(ex[0], ops[0], ex[1], steps)
        steps.append("<b>Solve the second inequality:</b>")
        i2, _ = solve_linear(ex[1], ops[1], ex[2], steps)
        steps.append("<b>Both must be true</b>, so keep the overlap of the two solutions.")
        return _final(steps, intersect(i1, i2), v, domain)
    raise UErr("Too many inequality signs. Use at most two, like -3 < 2x + 1 &le; 7.")


def Poly0():
    return P.Poly()


def _final(steps, iv, var, domain):
    img = numberline(iv, var)
    txt = (f"<b>Solution:</b> {set_words(iv, var)}<br>Interval notation: {interval_words(iv)}"
           f"<br>Set notation: {{ {var} : {set_words(iv, var)} }}" + int_text(iv, domain))
    steps.append("<b>Show it on a number line.</b> An open circle (&#9675;) means the number is NOT included (&lt; or &gt;); "
                 "a filled circle (&#9679;) means it IS included (&le; or &ge;).")
    return _ok(steps, {"image": img, "text": txt})


# ------------------------------------------------------- quadratic / rational --

def _real_roots(poly_obj, v):
    """list of (value Fraction|float, multiplicity) distinct real roots of a primitive factor"""
    co = poly_obj.to_uni(v)
    deg = len(co) - 1
    if deg == 1:
        return [Fraction(-co[0], 1) / co[1]]
    import numpy as np
    r = np.roots([float(c) for c in reversed(co)])
    out = []
    for z in r:
        if abs(z.imag) < 1e-9:
            val = float(z.real)
            fv = Fraction(val).limit_denominator(1000)
            out.append(fv if abs(float(fv) - val) < 1e-9 and poly_obj.eval_at(v, fv) == 0 else val)
    return out


def _sign_fmt(s):
    return "+" if s > 0 else ("&minus;" if s < 0 else "0")


def _peval(p, v, x):
    co = p.to_uni(v)
    r = 0.0
    for c in reversed(co):
        r = r * float(x) + float(c)
    return r


@guard
def quad(d):
    text = (d.get("ineq") or "").strip()
    domain = d.get("domain", "real")
    if not text or len(text) > 200:
        raise UErr("Type an inequality, for example x^2 - 5x + 6 < 0   or   (x-1)/(x+2) >= 0")
    ex, ops = _split_rel(text)
    if len(ops) != 1:
        raise UErr("Use exactly one inequality sign here.")
    op = ops[0]
    rl, rr = _rf(ex[0]), _rf(ex[1])
    diff = rl - rr
    vs = sorted(set(diff.n.vars()) | set(diff.d.vars()) | set(rl.n.vars()) | set(rr.n.vars()))
    if len(vs) > 1:
        raise UErr("Use only one letter (like x).")
    if not vs:
        raise UErr("There is no letter in your inequality.")
    v = vs[0]
    N, D = diff.n, diff.d
    if N.is_zero():
        raise UErr("Both sides are equal, so the difference is always 0.")
    steps = []
    steps.append(f"<b>Step 1 - Move everything to the left</b> so the right side is 0: "
                 f"{'(' + _ptxt(N) + ')/(' + _ptxt(D) + ')' if not D.is_const() else _ptxt(N)} {OPS[op]} 0")
    if D.is_const():
        N = N.scale(1 / D.const_value()) if D.const_value() > 0 else N.scale(1 / D.const_value())
        if D.const_value() < 0:
            op = FLIP[op]
        D = P.Poly.const(1)
    if N.degree_in(v) > 8 or D.degree_in(v) > 8:
        raise UErr("That expression is too high a degree for this solver.")
    notes = []
    try:
        cn, fn = P.factor(N, notes)
        cd, fd = P.factor(D, notes) if not D.is_const() else (D.const_value(), [])
    except P.TooBig:
        raise UErr("The numbers are too big to factorise here.")
    # collect critical points
    crit = {}   # key float -> (value, kind set, txt)
    facs = []
    for kind, lst in (("num", fn), ("den", fd)):
        for f, e in lst:
            if f.is_const():
                continue
            roots = _real_roots(f, v)
            facs.append((kind, f, e, roots))
            for r in roots:
                key = round(float(r), 9)
                ent = crit.setdefault(key, {"val": r, "kinds": set()})
                ent["kinds"].add(kind)
                if isinstance(r, Fraction):
                    ent["val"] = r
    fac_txt = []
    if not D.is_const():
        fac_txt.append(f"numerator: {P.factors_str(cn, fn) if fn else _ptxt(N)}")
        fac_txt.append(f"denominator: {P.factors_str(cd, fd) if fd else _ptxt(D)}")
    else:
        fac_txt.append(f"{P.factors_str(cn, fn) if fn else _ptxt(N)}")
    steps.append("<b>Step 2 - Factorise.</b> " + "; ".join(fac_txt))
    if not crit:
        s = (1 if cn > 0 else -1)
        for kind, f, e, roots in facs:
            s *= (1 if _peval(f, v, 0) > 0 else -1) ** e * (1 if kind == "num" else 1)
        sg = s
        ok = (sg > 0 and op in (">", ">=")) or (sg < 0 and op in ("<", "<="))
        steps.append(f"There are no real values that make any factor zero, so the expression is always "
                     f"{'positive' if sg > 0 else 'negative'}.")
        res = [mk(None, None, False, False)] if ok else []
        return _final2(steps, res, v, domain, [])
    keys = sorted(crit)
    pts = [crit[k]["val"] for k in keys]
    steps.append("<b>Step 3 - Critical points</b> (where a factor is 0): " + ", ".join(f"{v} = {pt_txt(p)}" for p in pts)
                 + (". Points that make the <i>bottom</i> zero are never allowed (you cannot divide by 0)." if fd else "."))
    # test points
    fl = [float(p) for p in pts]
    tests = [fl[0] - 1] + [(fl[i] + fl[i + 1]) / 2 for i in range(len(fl) - 1)] + [fl[-1] + 1]
    seg_sign = []
    rows = []
    cols = []
    labels = []
    for i in range(len(fl) + 1):
        lo = "&minus;&infin;" if i == 0 else pt_txt(pts[i - 1])
        hi = "&infin;" if i == len(fl) else pt_txt(pts[i])
        labels.append(f"{lo} to {hi}")
    head = ["Factor"] + [f"{v} in<br>{l}" for l in labels]
    fr_rows = []
    sgn_tot = [1 if cn > 0 else -1] * (len(fl) + 1)
    for kind, f, e, roots in facs:
        row = [("(" + _ptxt(f) + ")" + (f"<sup>{e}</sup>" if e > 1 else "")) + ("" if kind == "num" else " (bottom)")]
        for i, t in enumerate(tests):
            val = _peval(f, v, t)
            s = 1 if val > 0 else -1
            s = s ** e
            sgn_tot[i] *= s
            row.append(_sign_fmt(s))
        fr_rows.append(row)
    if cn < 0:
        fr_rows.append(["constant " + fm(cn)] + [_sign_fmt(-1)] * (len(fl) + 1))
    fr_rows.append(["<b>Whole expression</b>"] + [f"<b>{_sign_fmt(s)}</b>" for s in sgn_tot])
    steps.append("<b>Step 4 - Sign table.</b> The critical points cut the number line into sections. Pick a test number in each section and write the sign (+ or &minus;) of every factor; multiply the signs to get the sign of the whole expression.")
    steps.append(table(fr_rows, head))
    want_pos = op in (">", ">=")
    incl = op in ("<=", ">=")
    steps.append(f"<b>Step 5 - Choose the sections.</b> We want the expression {OPS[op]} 0, so take the sections marked <b>{'+' if want_pos else MINUS}</b>"
                 + (f", and include the zero points of the top (because of {OPS[op]})." if incl else " (the critical points themselves are NOT included because the sign is strict)."))
    segs = []   # alternating interval, point, interval...
    n = len(fl)
    ivs = []
    for i in range(n + 1):
        keep = (sgn_tot[i] > 0) if want_pos else (sgn_tot[i] < 0)
        lo = pts[i - 1] if i > 0 else None
        hi = pts[i] if i < n else None
        segs.append(("iv", keep, lo, hi))
        if i < n:
            kinds = crit[keys[i]]["kinds"]
            allowed = incl and ("num" in kinds) and ("den" not in kinds)
            segs.append(("pt", allowed, pts[i], pts[i]))
    cur = None
    out = []
    for kind, keep, lo, hi in segs:
        if keep:
            if kind == "iv":
                if cur is None:
                    cur = [lo, hi, False, False]
                    if lo is None:
                        cur[2] = False
                else:
                    cur[1] = hi
                cur[3] = False
            else:
                if cur is None:
                    cur = [lo, hi, True, True]
                else:
                    cur[3] = True
                    cur[1] = hi
        else:
            if cur is not None:
                out.append(cur)
                cur = None
    if cur is not None:
        out.append(cur)
    # fix flags: interval starting right after a kept point already merged
    res = []
    for lo, hi, li, hi_i in out:
        res.append(mk(lo, hi, li if lo is not None else False, hi_i if hi is not None else False))
    # rebuild inclusion precisely
    res2 = []
    kept_pts = {round(float(s[2]), 9) for s in segs if s[0] == "pt" and s[1]}
    for lo, hi, li, hi_i, lt, ht in res:
        li2 = (lo != -INF) and (round(lo, 9) in kept_pts)
        hi2 = (hi != INF) and (round(hi, 9) in kept_pts)
        res2.append((lo, hi, li2, hi2, lt, ht))
    return _final2(steps, normalise(res2), v, domain, fl)


def _final2(steps, iv, v, domain, extra):
    txt = (f"<b>Solution:</b> {set_words(iv, v)}<br>Interval notation: {interval_words(iv)}" + int_text(iv, domain))
    steps.append("<b>Step 6 - Write the answer and draw it on the number line.</b>")
    return _ok(steps, {"image": numberline(iv, v, extra), "text": txt})


# ---------------------------------------------------------------- region / LP --

def parse_constraints(text, maxn=8):
    items = [t.strip() for t in re.split(r"[;\n]+|,(?![^()]*\))", text or "") if t.strip()]
    if not items:
        raise UErr("Type the inequalities separated by commas, for example: y > 2x - 1, x + y <= 6, x >= 0, y >= 0")
    if len(items) > maxn:
        raise UErr(f"Please use at most {maxn} inequalities.")
    out = []
    for it in items:
        ex, ops = _split_rel(it)
        if len(ops) != 1:
            raise UErr(f"Use one inequality sign in each: '{esc(it)}'.")
        Lp, Rp = _pp(ex[0]), _pp(ex[1])
        p = Lp - Rp
        if any(vv not in ("x", "y") for vv in p.vars()):
            raise UErr("Use only the letters x and y.")
        if p.total_degree() > 1:
            raise UErr(f"'{esc(it)}' is not a straight-line inequality (no squares or products of x and y).")
        a = b = c = Fraction(0)
        for k, co in p.t.items():
            if k == ():
                c += co
            else:
                (vv, e), = k
                if vv == "x":
                    a += co
                else:
                    b += co
        if a == 0 and b == 0:
            raise UErr(f"'{esc(it)}' has no x or y in it.")
        out.append({"a": a, "b": b, "k": -c, "op": ops[0], "txt": it})
    return out


def _sat(c, x, y, strict_ok=True):
    v = c["a"] * x + c["b"] * y - c["k"]
    return {"<": v <= 0, "<=": v <= 0, ">": v >= 0, ">=": v >= 0}[c["op"]]


def vertices(cs):
    pts = []
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            a1, b1, k1 = cs[i]["a"], cs[i]["b"], cs[i]["k"]
            a2, b2, k2 = cs[j]["a"], cs[j]["b"], cs[j]["k"]
            det = a1 * b2 - a2 * b1
            if det == 0:
                continue
            x = (k1 * b2 - k2 * b1) / det
            y = (a1 * k2 - a2 * k1) / det
            if all(_sat(c, x, y) for c in cs):
                if (x, y) not in pts:
                    pts.append((x, y))
    return pts


def _eqn_html(c, mathtext=False):
    a, b, k = c["a"], c["b"], c["k"]
    parts = []
    if a != 0:
        parts.append((MINUS if a < 0 else "") + ("" if abs(a) == 1 else fm(abs(a), 4)) + "x")
    if b != 0:
        s = ("" if abs(b) == 1 else fm(abs(b), 4)) + "y"
        parts.append((f" {MINUS if b < 0 else '+'} " + s) if parts else ((MINUS if b < 0 else "") + s))
    return "".join(parts) + f" = {fm(k, 4)}"


def _line_steps(cs, steps):
    for i, c in enumerate(cs, 1):
        a, b, k = c["a"], c["b"], c["k"]
        solid = c["op"] in ("<=", ">=")
        s = f"<b>Inequality {i}: {esc(c['txt'])}</b><br>Boundary line: {_eqn_html(c)}. "
        pts = []
        if b != 0 and a != 0:
            pts.append(f"when x = 0, y = {fr(k / b)}; when y = 0, x = {fr(k / a)}")
            s += "Two points to draw it: " + pts[0] + ". "
        elif b == 0:
            s += f"This is a vertical line x = {fr(k / a)}. "
        else:
            s += f"This is a horizontal line y = {fr(k / b)}. "
        s += ("Because of " + OPS[c["op"]] + ", draw the line <b>solid</b> (points on the line are allowed). " if solid
              else "Because of " + OPS[c["op"]] + ", draw the line <b>dashed</b> (points on the line are NOT allowed). ")
        tp = None
        for cand in ((0, 0), (1, 0), (0, 1), (1, 1), (2, 1), (-1, 3)):
            if a * cand[0] + b * cand[1] != k:
                tp = cand
                break
        val = a * tp[0] + b * tp[1]
        true = {"<": val < k, "<=": val <= k, ">": val > k, ">=": val >= k}[c["op"]]
        s += (f"<b>Test point ({tp[0]}, {tp[1]}):</b> {fm(val, 4)} {OPS[c['op']]} {fm(k, 4)} is <b>{'TRUE' if true else 'FALSE'}</b>, "
              f"so the wanted side is the side {'WITH' if true else 'AWAY FROM'} the point ({tp[0]}, {tp[1]}).")
        steps.append(s)


def draw_region(cs, verts, shade="unwanted", obj=None, best=None, int_pts=None):
    plt = _mpl()
    import numpy as np
    xs = [0.0] + [float(v[0]) for v in verts]
    ys = [0.0] + [float(v[1]) for v in verts]
    for c in cs:
        a, b, k = float(c["a"]), float(c["b"]), float(c["k"])
        if a != 0:
            xs.append(k / a)
        if b != 0:
            ys.append(k / b)
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    sx, sy = max(x1 - x0, 4), max(y1 - y0, 4)
    x0, x1, y0, y1 = x0 - 0.2 * sx - 0.5, x1 + 0.25 * sx + 0.5, y0 - 0.2 * sy - 0.5, y1 + 0.25 * sy + 0.5
    # make the window a little more square
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    X, Y = np.meshgrid(np.linspace(x0, x1, 500), np.linspace(y0, y1, 500))
    feas = np.ones_like(X, dtype=bool)
    for c in cs:
        v = float(c["a"]) * X + float(c["b"]) * Y - float(c["k"])
        feas &= (v <= 1e-9) if c["op"] in ("<", "<=") else (v >= -1e-9)
    import matplotlib
    if shade == "unwanted":
        with matplotlib.rc_context({"hatch.color": "#dc2626", "hatch.linewidth": 0.8}):
            ax.contourf(X, Y, (~feas).astype(float), levels=[0.5, 1.5], colors="none", hatches=["///"])
        ax.contourf(X, Y, (~feas).astype(float), levels=[0.5, 1.5], colors=["#fecaca"], alpha=0.35)
    else:
        ax.contourf(X, Y, feas.astype(float), levels=[0.5, 1.5], colors=["#a5b4fc"], alpha=0.55)
    ax.axhline(0, color="#111827", lw=1.2)
    ax.axvline(0, color="#111827", lw=1.2)
    palette = ["#2563eb", "#059669", "#d97706", "#7c3aed", "#db2777", "#0891b2", "#65a30d", "#dc2626"]
    for i, c in enumerate(cs):
        a, b, k = float(c["a"]), float(c["b"]), float(c["k"])
        ls = "-" if c["op"] in ("<=", ">=") else "--"
        col = palette[i % len(palette)]
        lab = f"({i + 1}) " + _plain_eq(c)
        if b == 0:
            ax.axvline(k / a, color=col, ls=ls, lw=2, label=lab)
        elif a == 0:
            ax.axhline(k / b, color=col, ls=ls, lw=2, label=lab)
        else:
            xx = np.array([x0, x1])
            ax.plot(xx, (k - a * xx) / b, color=col, ls=ls, lw=2, label=lab)
    for (vx, vy) in verts:
        ax.plot([float(vx)], [float(vy)], "o", color="#111827", ms=6, zorder=5)
        ax.annotate(f"({fm(vx, 2)}, {fm(vy, 2)})", (float(vx), float(vy)), textcoords="offset points", xytext=(6, 6), fontsize=8.5,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=.8))
    if int_pts:
        ax.plot([p[0] for p in int_pts], [p[1] for p in int_pts], ".", color="#1d4ed8", ms=6, zorder=4)
    if obj is not None and best is not None:
        oa, ob = float(obj[0]), float(obj[1])
        z = oa * float(best[0]) + ob * float(best[1])
        if ob != 0:
            xx = np.array([x0, x1])
            ax.plot(xx, (z - oa * xx) / ob, color="#111827", ls=":", lw=2, label="objective line through the best point")
        elif oa != 0:
            ax.axvline(z / oa, color="#111827", ls=":", lw=2)
        ax.plot([float(best[0])], [float(best[1])], "*", color="#f59e0b", ms=16, mec="#111827", zorder=6)
    # label wanted region R
    ptsf = X[feas], Y[feas]
    if len(ptsf[0]) > 20:
        ax.text(float(np.mean(ptsf[0])), float(np.mean(ptsf[1])), "R", fontsize=20, fontweight="bold", ha="center", va="center", color="#1e3a8a",
                bbox=dict(boxstyle="circle,pad=0.25", fc="white", ec="#1e3a8a"))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True, alpha=.25)
    ax.set_aspect("auto")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=8.5, frameon=False)
    return _b64(fig)


def _plain_eq(c):
    a, b, k = c["a"], c["b"], c["k"]
    s = ""
    if a != 0:
        s += ("-" if a < 0 else "") + ("" if abs(a) == 1 else fm(abs(a), 3)) + "x"
    if b != 0:
        t = ("" if abs(b) == 1 else fm(abs(b), 3)) + "y"
        s += (f" {'-' if b < 0 else '+'} " + t) if s else (("-" if b < 0 else "") + t)
    sym = {"<": "<", "<=": "≤", ">": ">", ">=": "≥"}[c["op"]]
    return f"{s} {sym} {fm(k, 3)}"


def _int_points(cs, verts):
    if len(verts) < 3:
        return None
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    # bounded check: region bounded if all vertices lie in box and region within polygon -- test by sampling a box ring
    import itertools
    big = 1000
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        if all(_sat(c, xs[0] + dx * big, ys[0] + dy * big) for c in cs):
            return None
    pts = []
    for x in range(math.floor(min(xs)), math.ceil(max(xs)) + 1):
        for y in range(math.floor(min(ys)), math.ceil(max(ys)) + 1):
            if all(_strict_ok(c, x, y) for c in cs):
                pts.append((x, y))
    return pts


def _strict_ok(c, x, y):
    v = c["a"] * x + c["b"] * y - c["k"]
    return {"<": v < 0, "<=": v <= 0, ">": v > 0, ">=": v >= 0}[c["op"]]


@guard
def region(d):
    cs = parse_constraints(d.get("cons"))
    shade = d.get("shade", "unwanted")
    steps = ["<b>Idea:</b> every inequality is a straight line with one side wanted. We draw each line (dashed for &lt; and &gt;, solid for &le; and &ge;), "
             "use a test point to find the wanted side, and shade away the unwanted sides so the wanted region R is left clear."]
    _line_steps(cs, steps)
    verts = vertices(cs)
    steps.append(f"<b>Shading.</b> " + ("Shade (hatch) the UNWANTED side of each line. The region left unshaded and labelled <b>R</b> satisfies all the inequalities at once."
                                       if shade == "unwanted" else "Shade the WANTED side of each line. The region where all the shading overlaps, labelled <b>R</b>, satisfies every inequality."))
    ip = None
    if d.get("ints") == "yes":
        ip = _int_points(cs, verts)
    if verts:
        steps.append("<b>Corner points</b> of R (where two boundary lines meet and all the inequalities are satisfied): "
                     + ", ".join(f"({fr(x)}, {fr(y)})" for x, y in verts))
    else:
        steps.append("The lines do not enclose a corner here, so R is either unbounded in a strip/half-plane or empty. Check the picture.")
    if d.get("ints") == "yes":
        if ip is None:
            steps.append("The region is not enclosed, so there are infinitely many points to list.")
        elif len(ip) > 80:
            steps.append(f"There are {len(ip)} points with whole-number coordinates, too many to list; they are marked in blue.")
        else:
            steps.append("<b>Points with whole-number coordinates inside R</b> (marked with blue dots; strict inequalities exclude points on dashed lines): "
                         + (", ".join(f"({x}, {y})" for x, y in ip) if ip else "none") + f". That is {len(ip)} point{'s' if len(ip) != 1 else ''}.")
    img = draw_region(cs, verts, shade, int_pts=ip if ip and len(ip) <= 400 else None)
    txt = ("<b>Corner points:</b> " + ", ".join(f"({fr(x)}, {fr(y)})" for x, y in verts)) if verts else "No enclosed region found."
    return _ok(steps, {"image": img, "text": txt})


@guard
def lp(d):
    cs = parse_constraints(d.get("cons"))
    obj_txt = (d.get("obj") or "").strip()
    op = _pp(obj_txt) if obj_txt else None
    if op is None or any(vv not in ("x", "y") for vv in op.vars()) or op.total_degree() != 1 or not op.vars():
        raise UErr("Write the thing to maximise or minimise using x and y, for example 3x + 2y or 50x + 80y.")
    oa = oc = ob = Fraction(0)
    for k, co in op.t.items():
        if k == ():
            oc += co
        else:
            (vv, e), = k
            if vv == "x":
                oa += co
            else:
                ob += co
    goal = d.get("goal", "max")
    whole = d.get("whole") == "yes"
    steps = ["<b>Step 1 - Write down the inequalities</b> (the constraints) and the quantity to " + ("maximise" if goal == "max" else "minimise")
             + f": <b>{esc(obj_txt)}</b>. (If you are turning a word problem into inequalities: let x and y be the unknown amounts, and write one inequality for each limit, plus x &ge; 0 and y &ge; 0 if they cannot be negative.)"]
    _line_steps(cs, steps)
    verts = vertices(cs)
    if not verts:
        raise UErr("I could not find any corner points. The constraints may have no common region, or the region has no corners. Check the inequalities.")
    # unbounded direction check
    rays = []
    for c in cs:
        rays += [(-c["b"], c["a"]), (c["b"], -c["a"])]
    rays += [(1, 0), (-1, 0), (0, 1), (0, -1)]
    unb = []
    for r in rays:
        if all((c["a"] * r[0] + c["b"] * r[1] <= 0) if c["op"] in ("<", "<=") else (c["a"] * r[0] + c["b"] * r[1] >= 0) for c in cs):
            unb.append(r)
    sign = 1 if goal == "max" else -1
    for r in unb:
        if sign * (oa * r[0] + ob * r[1]) > 0:
            raise UErr(("The region goes on forever in a direction that keeps increasing" if goal == "max" else "The region goes on forever in a direction that keeps decreasing")
                       + " your quantity, so there is no " + ("maximum" if goal == "max" else "minimum") + ". Check that you have all the constraints.")
    steps.append("<b>Step 2 - Draw the feasible region R</b> (the region satisfying every inequality) and find its corner points: "
                 + ", ".join(f"({fr(x)}, {fr(y)})" for x, y in verts) + ".")
    steps.append("<b>Step 3 - The best answer is always at a corner point</b> of R. Put each corner into the expression:")
    rows = []
    vals = []
    for x, y in verts:
        z = oa * x + ob * y + oc
        vals.append(z)
        rows.append([f"({fm(x, 4)}, {fm(y, 4)})", f"{fm(oa)}&times;{fm(x, 4)} + {fm(ob)}&times;{fm(y, 4)}" + (f" + {fm(oc)}" if oc else ""), fm(z, 4)])
    steps.append(table(rows, ["Corner", "Calculation", "Value"]))
    bestv = max(vals) if goal == "max" else min(vals)
    best = verts[vals.index(bestv)]
    steps.append(f"<b>Step 4 - Choose.</b> The {'largest' if goal == 'max' else 'smallest'} value is <span class='hl'>{fm(bestv, 4)}</span> at ({fr(best[0])}, {fr(best[1])}).")
    answer = f"<b>{'Maximum' if goal == 'max' else 'Minimum'} value = {fm(bestv, 4)}</b> when x = {fm(best[0], 4)} and y = {fm(best[1], 4)}"
    ip = None
    if whole:
        ip = _int_points(cs, verts)
        if ip is None or not ip:
            steps.append("<b>Whole numbers needed:</b> I could not list whole-number points in this region.")
        else:
            cand = [(oa * x + ob * y + oc, x, y) for x, y in ip]
            bz = max(cand) if goal == "max" else min(cand)
            steps.append(f"<b>Whole numbers needed.</b> The corner point may not have whole-number coordinates. Check the whole-number points inside R (blue dots): the best is "
                         f"x = {bz[1]}, y = {bz[2]} giving <span class='hl'>{fm(bz[0], 4)}</span>.")
            answer = f"<b>With whole numbers: {'maximum' if goal == 'max' else 'minimum'} = {fm(bz[0], 4)}</b> when x = {bz[1]} and y = {bz[2]}"
            best = (Fraction(bz[1]), Fraction(bz[2]))
    img = draw_region(cs, verts, "wanted", obj=(oa, ob), best=best, int_pts=ip if ip and len(ip) <= 400 else None)
    return _ok(steps, {"image": img, "text": answer})


# ---------------------------------------------------------------------- spec --

_DOM = select("domain", "Which numbers is x allowed to be?", [("real", "any real number"), ("int", "integers (..., -1, 0, 1, ...)"),
                                                                  ("nat", "natural numbers (1, 2, 3, ...)"), ("whole", "whole numbers (0, 1, 2, ...)")])

SPEC = {
    "title": "Inequalities",
    "intro": "Linear and quadratic inequalities with number lines, region graphs and linear programming.",
    "tabs": [
        {"id": "il", "label": "Linear & compound", "title": "Linear and compound inequalities", "endpoint": "linear",
         "hint": "Examples: <i>2x - 3 &gt; 7</i> &nbsp; <i>5 - 2x &lt;= 9</i> &nbsp; <i>-3 &lt; 2x + 1 &lt;= 7</i> &nbsp; <i>x + 2 &gt; 5 or 2x &lt; -4</i> &nbsp; "
                 "Use &lt;=, &gt;= for &le;, &ge; (you can also paste &le; and &ge;).",
         "fields": [field("ineq", "Inequality", "-3 < 2x + 1 <= 7", wide=True, half=False), dict(_DOM)]},
        {"id": "iq", "label": "Quadratic & fractions", "title": "Quadratic and rational inequalities", "endpoint": "quad",
         "hint": "Examples: <i>x^2 - 5x + 6 &lt; 0</i> &nbsp; <i>(x-1)(x+2) &gt;= 0</i> &nbsp; <i>(x-1)/(x+2) &lt;= 0</i> &nbsp; <i>x^2 &gt; 9</i>. "
                 "Solved with a sign table.",
         "fields": [field("ineq", "Inequality", "x^2 - 5x + 6 < 0", wide=True, half=False), dict(_DOM)]},
        {"id": "ir", "label": "Region graph", "title": "Graph of inequalities in x and y", "endpoint": "region",
         "hint": "Separate the inequalities with commas. Example: <i>y &gt; 2x - 1, x + y &lt;= 6, x &gt;= 0, y &gt;= 0</i>",
         "fields": [field("cons", "Inequalities", "y > 2x - 1, x + y <= 6, x >= 0, y >= 0", wide=True, half=False),
                    select("shade", "Shading", [("unwanted", "shade the UNWANTED region (WAEC style)"), ("wanted", "shade the WANTED region")]),
                    select("ints", "List points with whole-number coordinates?", [("no", "no"), ("yes", "yes")])]},
        {"id": "ip", "label": "Linear programming", "title": "Linear programming", "endpoint": "lp",
         "hint": "Example: maximise <i>50x + 80y</i> subject to <i>x + y &lt;= 20, x + 2y &lt;= 30, x &gt;= 0, y &gt;= 0</i>.",
         "fields": [field("obj", "Quantity to maximise or minimise", "50x + 80y"),
                    select("goal", "Goal", [("max", "maximise"), ("min", "minimise")]),
                    field("cons", "Constraints (separate with commas)", "x + y <= 20, x + 2y <= 30, x >= 0, y >= 0", wide=True, half=False),
                    select("whole", "Must x and y be whole numbers?", [("no", "no"), ("yes", "yes")])]},
    ],
}

topics.register("inequalities", SPEC, {"linear": linear, "quad": quad, "region": region, "lp": lp})
