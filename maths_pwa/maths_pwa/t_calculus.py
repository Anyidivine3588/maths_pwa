"""Calculus for WAEC / NECO / JAMB: differentiation, integration, tangents, turning points, area, volume, rates."""
import base64
import io
import math
from fractions import Fraction
import topics
from calc_core import *
from calc_core import MINUS as M_, _exp_txt, ps_plain
from tcommon import field, select, guard as _g0, UErr, num, fm, fr, FR, esc, _ok, _fail, table, TIMES
import numpy as np


def guard(fn):
    inner = _g0(fn)

    def wrapped(d):
        try:
            return inner(d)
        except CErr as e:
            return _fail(str(e))
        except (RecursionError, OverflowError, ZeroDivisionError, ValueError):
            return _fail("That could not be worked out. Please check the expression and the numbers.")
    wrapped.__name__ = fn.__name__
    return wrapped

HL = lambda s: f"<span class='hl'>{s}</span>"


def _parse(text, var=None):
    try:
        return parse(text, var)
    except CErr as e:
        raise UErr(str(e))
    except RecursionError:
        raise UErr("That expression is too complicated.")


def _num_txt(x, p=4):
    """exact Fraction -> stacked; float -> decimals"""
    if isinstance(x, Fraction):
        return fr(x)
    return fm(Fraction(x).limit_denominator(10 ** 9), p)


def _val(n, x):
    try:
        return ast_value(n, x)
    except CErr as e:
        raise UErr(str(e))
    except (OverflowError, ValueError, ZeroDivisionError):
        raise UErr("That value cannot be calculated (division by zero or not a real number).")


def _fx(v):
    """text for f(x)-style variable print"""
    return v


def _f_text(fn_name, v):
    return f"{fn_name}({v})"


# -------------------------------------------------------------- differentiate --

def _term_explain(sign, t, v, fn):
    """one narrated block for one top-level term"""
    s = "" if sign > 0 else ""
    ps = to_ps(t)
    ttxt = show(t, v)
    if not has_var(t):
        return f"The term {ttxt} is just a number (a constant). A constant does not change, so its derivative is <b>0</b>.", ZERO
    if ps is not None and ps.is_monomial():
        (p, c), = ps.t.items()
        dres = ps_str(PS({p - 1: c * p}), v) if p != 0 else "0"
        if p == 1:
            return f"{ttxt}: the power of {v} is 1, so the derivative is just the number in front: <b>{fm(c, 6) if c.denominator == 1 else fr(c)}</b>.", D(t)
        pt = _exp_txt(p)
        return (f"<b>Power rule</b> on {ttxt}: multiply by the power ({pt}), then reduce the power by 1 ({pt} &minus; 1 = {_exp_txt(p - 1)}). "
                f"{fr(c) if c != 1 else ''}{'&times;' if c != 1 else ''}{pt} {v}<sup>{_exp_txt(p - 1)}</sup> = <b>{dres}</b>"), D(t)
    k = t[0]
    d = D(t)
    dtxt = show(d, v)
    if k == "mul" and has_var(t[1]) and has_var(t[2]):
        u, w = t[1], t[2]
        return (f"<b>Product rule</b> on {ttxt}. Let u = {show(u, v)} and w = {show(w, v)}. Then u' = {show(D(u), v)} and w' = {show(D(w), v)}. "
                f"The rule is (uw)' = u'w + uw'. So the derivative is <b>{dtxt}</b>."), d
    if k == "div" and has_var(t[2]):
        u, w = t[1], t[2]
        return (f"<b>Quotient rule</b> on {ttxt}. Let u (top) = {show(u, v)} and w (bottom) = {show(w, v)}. Then u' = {show(D(u), v)} and w' = {show(D(w), v)}. "
                f"The rule is (u/w)' = {FR('u&prime;w &minus; uw&prime;', 'w<sup>2</sup>')}. So the derivative is <b>{dtxt}</b>."), d
    if k == "mul" and (not has_var(t[1]) or not has_var(t[2])):
        c, rest = (t[1], t[2]) if not has_var(t[1]) else (t[2], t[1])
        sub_expl, _ = _term_explain(1, rest, v, fn)
        return f"The number {show(c, v)} in front stays; differentiate the rest. {sub_expl} Multiply by {show(c, v)}: <b>{dtxt}</b>.", d
    if k == "neg":
        sub_expl, _ = _term_explain(1, t[1], v, fn)
        return f"A minus sign in front stays. {sub_expl} Result: <b>{dtxt}</b>.", d
    if k == "div" and not has_var(t[2]):
        sub_expl, _ = _term_explain(1, t[1], v, fn)
        return f"Dividing by the number {show(t[2], v)} is the same as multiplying by its reciprocal. {sub_expl} Result: <b>{dtxt}</b>.", d
    if k == "pow":
        base, e = t[1], t[2]
        if not has_var(e):
            return (f"<b>Chain rule (function of a function)</b> on {ttxt}: the 'inside' is u = {show(base, v)}, so u' = {show(D(base), v)}. "
                    f"Rule: d/d{v}(u<sup>n</sup>) = n u<sup>n&minus;1</sup> &times; u'. Here n = {show(e, v)}. Result: <b>{dtxt}</b>."), d
        return (f"<b>Rule for e<sup>u</sup></b> on {ttxt}: the derivative of e<sup>u</sup> is e<sup>u</sup> &times; u' (the exponent's own derivative is u' = {show(D(e), v)}). "
                f"Result: <b>{dtxt}</b>."), d
    if k == "fn":
        f, u = t[1], t[2]
        rules = {"sin": "d/dx sin(u) = cos(u) &times; u'", "cos": "d/dx cos(u) = &minus;sin(u) &times; u'",
                 "tan": "d/dx tan(u) = sec<sup>2</sup>(u) &times; u' = u' / cos<sup>2</sup>(u)", "ln": "d/dx ln(u) = u' / u",
                 "sqrt": "&radic;u = u<sup>1/2</sup>, then use the power rule with the chain rule"}
        return (f"<b>Chain rule</b> on {ttxt}: {rules[f].replace('d/dx', 'd/d' + v)}, where u = {show(u, v)} and u' = {show(D(u), v)}. "
                f"Result: <b>{dtxt}</b>."), d
    return f"Differentiate {ttxt} to get <b>{dtxt}</b>.", d


def _first_principles(ps, v):
    steps = []
    steps.append(f"<b>First principles:</b> f'({v}) = lim<sub>h&rarr;0</sub> {FR('f(' + v + ' + h) &minus; f(' + v + ')', 'h')}.")
    out = PS()
    lines = []
    for p, c in sorted(ps.t.items(), reverse=True):
        if p.denominator != 1 or p < 0:
            raise UErr("First principles here works for polynomials (whole-number powers 0, 1, 2, 3...).")
        p = int(p)
        if p == 0:
            lines.append(f"A constant {fm(c, 4)}: f({v} + h) &minus; f({v}) = 0, so its derivative is 0.")
            continue
        terms = []
        for k in range(1, p + 1):
            coef = math.comb(p, k)
            terms.append((f"{coef}" if coef != 1 else "") + (f"{v}<sup>{p - k}</sup>" if p - k > 1 else (v if p - k == 1 else "")) + (f"h<sup>{k}</sup>" if k > 1 else "h"))
        lines.append(f"For {fm(c, 4)}{v}<sup>{p}</sup>: ({v}+h)<sup>{p}</sup> &minus; {v}<sup>{p}</sup> = {' + '.join(terms)}. "
                     f"Divide by h: {' + '.join(t.replace('h<sup>', 'h<sup>').rsplit('h', 1)[0] if False else t for t in terms)} &rarr; every term except the first still has an h, so as h &rarr; 0 only <b>{p}{v}<sup>{p - 1}</sup></b> is left. Times {fm(c, 4)}: {fm(c * p, 4)}{v}<sup>{p - 1}</sup>")
        out = out + PS({p - 1: c * p})
    steps.append("<br>".join(lines))
    return steps, out


@guard
def differentiate(d):
    text = (d.get("f") or "").strip()
    a, v = _parse(text)
    kind = d.get("kind", "first")
    steps = []
    ps = to_ps(a)
    steps.append(f"<b>The function:</b> y = {show(a, v)}")
    if kind == "first_p":
        if ps is None:
            raise UErr("First principles works for polynomials like 3x^2 - 5x + 1.")
        st, res = _first_principles(ps, v)
        steps += st
        return _ok(steps, f"<b>dy/d{v} = {ps_str(res, v)}</b>")
    if ps is not None and any(k.denominator != 1 or k < 0 for k in ps.t) and show(a, v) != ps_str(ps, v):
        pass
    if ps is not None and ps_str(ps, v) != pr(a, v):
        steps.append(f"<b>Step 1 - Rewrite</b> so every term looks like (number) &times; {v}<sup>power</sup> (roots become fractional powers: &radic;{v} = {v}<sup>1/2</sup>; "
                     f"{FR('1', v)} = {v}<sup>&minus;1</sup>; {FR('1', v + '<sup>2</sup>')} = {v}<sup>&minus;2</sup>): y = {ps_str(ps, v)}")
        a0 = a
    terms = flat_terms(a)
    # use PS terms when whole function is PS (cleaner narration)
    if ps is not None:
        tl = [(1 if c > 0 else -1, ("mul", ("num", abs(c)), power(("var",), N(p))) if p != 0 else ("num", abs(c))) for p, c in sorted(ps.t.items(), reverse=True)]
        # rebuild simple terms: c*x^p
        simple = []
        for p, c in sorted(ps.t.items(), reverse=True):
            node = ("num", c) if p == 0 else (power(("var",), N(p)) if c == 1 else mul(N(c), power(("var",), N(p))))
            simple.append((1, node))
        terms = simple
    steps.append(f"<b>Step 2 - Differentiate term by term.</b> d/d{v} means 'how fast it changes'. "
                 "<b>Power rule:</b> d/d" + v + f"({v}<sup>n</sup>) = n{v}<sup>n&minus;1</sup> (bring the power down in front, then take 1 off the power). "
                 "The derivative of a number on its own is 0.")
    pieces = []
    for sign, t in terms:
        txt, dt = _term_explain(sign, t, v, None)
        steps.append(("" if sign > 0 else f"(term is subtracted) ") + txt)
        pieces.append((sign, dt))
    total = ZERO
    for sign, dt in pieces:
        total = add(total, dt) if sign > 0 else sub(total, dt)
    dres = D(a)
    steps.append(f"<b>Step 3 - Put the pieces together.</b> dy/d{v} = <span class='hl'>{show(dres, v)}</span>")
    res = f"<b>dy/d{v} = f'({v}) = {show(dres, v)}</b>"
    if kind == "second":
        d2 = D(dres)
        steps.append(f"<b>Step 4 - Differentiate again</b> to get the second derivative: d<sup>2</sup>y/d{v}<sup>2</sup> = <span class='hl'>{show(d2, v)}</span>")
        res = f"<b>dy/d{v} = {show(dres, v)}<br>d<sup>2</sup>y/d{v}<sup>2</sup> = {show(d2, v)}</b>"
    if kind == "at":
        x0 = num(d.get("at"), f"the value of {v}")
        val = _val(dres, x0)
        steps.append(f"<b>Step 4 - Put {v} = {fm(x0, 6)} into the derivative</b> to get the gradient there: f'({fm(x0, 6)}) = {HL(_num_txt(val))}")
        res = f"<b>f'({fm(x0, 6)}) = {_num_txt(val)}</b> (the gradient of the curve at {v} = {fm(x0, 6)})"
    return _ok(steps, res)


# ----------------------------------------------------------------- integration --

class Anti:
    """antiderivative as list of (coef, kind, a, b, extra) pieces + PS"""

    def __init__(self):
        self.ps = PS()
        self.lcoef = Fraction(0)          # coefficient of ln|x|
        self.extra = []                   # (coef, text, func(x)->float)

    def at(self, x):
        x = Fraction(x) if not isinstance(x, float) else x
        val = self.ps.eval_x(x) if isinstance(x, Fraction) else self.ps.eval_f(x)
        fl = 0.0
        exact = isinstance(val, Fraction)
        if self.lcoef:
            if x <= 0 and not isinstance(x, float) or (isinstance(x, float) and x <= 0):
                raise UErr("ln needs a positive number here, check the limits.")
            fl += float(self.lcoef) * math.log(float(x))
            exact = False
        for c, tx, f in self.extra:
            fl += float(c) * f(float(x))
            exact = False
        if exact:
            return val
        return float(val) + fl

    def text(self, v):
        parts = []
        if self.ps.t:
            parts.append(ps_str(self.ps, v))
        if self.lcoef:
            parts.append((fr(self.lcoef) if self.lcoef != 1 else "") + f"ln|{v}|")
        for c, tx, f in self.extra:
            cc = Fraction(c)
            parts.append(((fr(cc) if abs(cc) != 1 else ("" if cc > 0 else M_)) if cc != 1 else "") + tx)
        if not parts:
            return "0"
        out = parts[0]
        for p in parts[1:]:
            out += (" " + (M_ + " " + p[len(M_):] if p.startswith(M_) else "+ " + p))
        return out


def _linear(arg, v):
    ps = to_ps(arg)
    if ps is None or any(k not in (0, 1) for k in ps.t) or 1 not in ps.t:
        return None
    return ps.t.get(Fraction(1), Fraction(0)), ps.t.get(Fraction(0), Fraction(0))


def _split_const(t):
    """strip numeric multiplier: returns (Fraction c, core)"""
    c = Fraction(1)
    while True:
        k = t[0]
        if k == "neg":
            c = -c
            t = t[1]
        elif k == "mul" and t[1][0] == "num":
            c *= t[1][1]
            t = t[2]
        elif k == "mul" and t[2][0] == "num":
            c *= t[2][1]
            t = t[1]
        elif k == "div" and t[2][0] == "num" and t[2][1] != 0:
            c /= t[2][1]
            t = t[1]
        else:
            return c, t


def antiderivative(a, v, steps=None):
    A = Anti()
    ps_all = to_ps(a)
    if ps_all is not None:
        if steps is not None:
            if ps_str(ps_all, v) != pr(a, v):
                steps.append(f"<b>Rewrite</b> as a sum of (number) &times; {v}<sup>power</sup> terms (expand brackets, roots to fractional powers, fractions to negative powers): {ps_str(ps_all, v)}")
            steps.append("<b>Power rule for integration:</b> &int; " + f"{v}<sup>n</sup> d{v} = {FR(v + '<sup>n+1</sup>', 'n + 1')} (add 1 to the power, then divide by the NEW power). "
                         f"The exception is {v}<sup>&minus;1</sup>, which integrates to ln|{v}|. Add the constant <b>c</b> at the end for an indefinite integral.")
            for p, c in sorted(ps_all.t.items(), reverse=True):
                if p == -1:
                    steps.append(f"{fr(c) if c != 1 else ''}{v}<sup>&minus;1</sup> &rarr; {fr(c) if c != 1 else ''}ln|{v}|")
                else:
                    np_ = p + 1
                    steps.append(f"{(fr(c) if c != 1 else '') + (v if p == 1 else v + '<sup>' + _exp_txt(p) + '</sup>') if p != 0 else fr(c)} &rarr; "
                                 f"{FR((fr(c) if c != 1 else '') + v + '<sup>' + _exp_txt(np_) + '</sup>', _exp_txt(np_))} = {ps_str(PS({np_: c / np_}), v)}")
        P, lc = ps_all.integ()
        A.ps = P
        A.lcoef = lc
        return A
    for sign, t in flat_terms(a):
        c, core = _split_const(t)
        c *= sign
        tp = to_ps(core)
        if tp is not None:
            P, lc = tp.scale(c).integ()
            A.ps = A.ps + P
            A.lcoef += lc
            if steps is not None:
                steps.append(f"{show(t, v)} &rarr; power rule &rarr; {ps_str(P, v)}")
            continue
        k = core[0]
        handled = False
        if k == "fn":
            f, u = core[1], core[2]
            lin = _linear(u, v)
            if lin:
                aa, bb = lin
                ut = show(u, v)
                coef = c / aa
                if f == "sin":
                    A.extra.append((-coef, f"cos({ut})", lambda x, aa=aa, bb=bb: math.cos(float(aa) * x + float(bb))))
                    note = f"&int;sin(u) = &minus;cos(u)"
                elif f == "cos":
                    A.extra.append((coef, f"sin({ut})", lambda x, aa=aa, bb=bb: math.sin(float(aa) * x + float(bb))))
                    note = "&int;cos(u) = sin(u)"
                elif f == "tan":
                    A.extra.append((-coef, f"ln|cos({ut})|", lambda x, aa=aa, bb=bb: math.log(abs(math.cos(float(aa) * x + float(bb))))))
                    note = "&int;tan(u) = &minus;ln|cos(u)|"
                elif f == "ln":
                    raise UErr("Integrating ln needs integration by parts, which is outside this solver.")
                else:
                    P, lc = to_ps(("pow", u, N(Fraction(1, 2)))), None
                    handled = False
                    note = None
                if note:
                    if steps is not None:
                        steps.append(f"{show(t, v)}: {note}, and because the inside is {ut} (a straight line) we also divide by its number in front of {v}, which is {fm(aa, 6)}.")
                    handled = True
        elif k == "pow":
            base, e = core[1], core[2]
            if base == ("const", "e") and not has_var(e) is False:
                lin = _linear(e, v)
                if lin:
                    aa, bb = lin
                    A.extra.append((c / aa, f"e<sup>{show(e, v)}</sup>", lambda x, aa=aa, bb=bb: math.exp(float(aa) * x + float(bb))))
                    if steps is not None:
                        steps.append(f"{show(t, v)}: &int;e<sup>u</sup> = e<sup>u</sup>; the inside {show(e, v)} is a straight line, so divide by {fm(aa, 6)}.")
                    handled = True
            elif not has_var(e):
                en = e[1] if is_num(e) else (-e[1][1] if e[0] == "neg" and is_num(e[1]) else None)
                lin = _linear(base, v)
                if lin and en is not None:
                    aa, bb = lin
                    if en == -1:
                        A.extra.append((c / aa, f"ln|{show(base, v)}|", lambda x, aa=aa, bb=bb: math.log(abs(float(aa) * x + float(bb)))))
                    else:
                        coef = c / (aa * (en + 1))
                        A.extra.append((coef, f"({show(base, v)})<sup>{_exp_txt(en + 1)}</sup>", lambda x, aa=aa, bb=bb, en=en: (float(aa) * x + float(bb)) ** float(en + 1)))
                    if steps is not None:
                        steps.append(f"{show(t, v)}: reverse of the chain rule: add 1 to the power, divide by the new power AND by the number in front of {v} inside the bracket ({fm(aa, 6)}).")
                    handled = True
        elif k == "div":
            num_, den = core[1], core[2]
            if not has_var(num_):
                lin = _linear(den, v)
                if lin:
                    aa, bb = lin
                    cc = c * ev(num_, 0)
                    cc = Fraction(cc).limit_denominator(10 ** 6) if not is_num(num_) else c * num_[1]
                    A.extra.append((cc / aa, f"ln|{show(den, v)}|", lambda x, aa=aa, bb=bb: math.log(abs(float(aa) * x + float(bb)))))
                    if steps is not None:
                        steps.append(f"{show(t, v)}: {FR('1', 'u')} integrates to ln|u|; divide by the number in front of {v} ({fm(aa, 6)}).")
                    handled = True
        if not handled:
            raise UErr(f"I cannot integrate '{show(t, v)}' with the methods here. Try expanding brackets first, or use a form like (ax+b)^n, sin(ax+b), cos(ax+b), e^(ax+b) or 1/(ax+b).")
    return A


@guard
def integrate(d):
    a, v = _parse(d.get("f"))
    kind = d.get("kind", "indef")
    steps = [f"<b>The function:</b> {show(a, v)}"]
    A = antiderivative(a, v, steps)
    if kind == "indef":
        txt = A.text(v)
        steps.append(f"<b>Add the constant of integration c</b> (the derivative of any constant is 0, so it could have been there): {HL(txt + ' + c')}")
        return _ok(steps, f"<b>&int; ({show(a, v)}) d{v} = {txt} + c</b>")
    lo, hi = num(d.get("lo"), "the lower limit"), num(d.get("hi"), "the upper limit")
    txt = A.text(v)
    steps.append(f"<b>Definite integral:</b> no constant c is needed. Integral = [{txt}] from {fm(lo, 6)} to {fm(hi, 6)}.")
    try:
        Fh, Fl = A.at(hi), A.at(lo)
    except CErr as e:
        raise UErr(str(e))
    steps.append(f"<b>Put in the upper limit {fm(hi, 6)}:</b> {_num_txt(Fh)}. &nbsp;<b>Put in the lower limit {fm(lo, 6)}:</b> {_num_txt(Fl)}.")
    res = Fh - Fl
    steps.append(f"<b>Subtract (upper &minus; lower):</b> {_num_txt(Fh)} &minus; ({_num_txt(Fl)}) = {HL(_num_txt(res))}")
    return _ok(steps, f"<b>&int;<sub>{fm(lo, 4)}</sub><sup>{fm(hi, 4)}</sup> = {_num_txt(res)}</b>")


# ------------------------------------------------------------ plotting helper ---

def _plot(curves, pts=(), lines=(), shade=None, xr=None, title=None, labels=True):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    xs0, xs1 = xr
    X = np.linspace(xs0, xs1, 600)
    ymin, ymax = 1e18, -1e18
    cols = ["#2563eb", "#dc2626", "#059669", "#7c3aed"]
    for i, (ast, lab) in enumerate(curves):
        Y = []
        for x in X:
            try:
                y = ev(ast, float(x))
                if isinstance(y, complex) or abs(y) > 1e4 or y != y:
                    y = float("nan")
            except Exception:
                y = float("nan")
            Y.append(y)
        Y = np.array(Y, dtype=float)
        ax.plot(X, Y, color=cols[i % 4], lw=2.2, label=lab)
        fin = Y[np.isfinite(Y)]
        if len(fin):
            ymin, ymax = min(ymin, fin.min()), max(ymax, fin.max())
        if shade and i < len(shade):
            a, b, lower = shade[i]
            m = (X >= a) & (X <= b)
            base = np.zeros_like(X) if lower is None else lower(X)
            ax.fill_between(X[m], base[m], Y[m], color=cols[i % 4], alpha=0.25)
    for (x, y, lab) in pts:
        ax.plot([x], [y], "o", color="#111827", ms=7, zorder=5)
        ax.annotate(lab, (x, y), textcoords="offset points", xytext=(7, 7), fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=.85))
    if ymin > ymax:
        ymin, ymax = -1, 1
    pad = (ymax - ymin) * 0.12 + 0.5
    for (m, c0, lab, col) in lines:
        ax.plot(X, m * X + c0, color=col, lw=1.8, ls="--", label=lab)
    ax.set_xlim(xs0, xs1)
    lo_y, hi_y = ymin - pad, ymax + pad
    ax.set_ylim(lo_y, hi_y)
    ax.axhline(0, color="#111827", lw=1)
    ax.axvline(0, color="#111827", lw=1)
    ax.grid(True, alpha=.3)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if title:
        ax.set_title(title)
    ax.legend(loc="best", fontsize=9)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


# --------------------------------------------------------------- tangent/normal --

@guard
def tangent(d):
    a, v = _parse(d.get("f"), "x")
    x0 = num(d.get("at"), "the x-value")
    steps = [f"<b>The curve:</b> y = {show(a, v)}, at x = {fm(x0, 6)}."]
    y0 = _val(a, x0)
    steps.append(f"<b>Step 1 - Find the y-value of the point.</b> Put x = {fm(x0, 6)} into y: y = {_num_txt(y0)}. The point is ({fm(x0, 6)}, {_num_txt(y0)}).")
    da = D(a)
    steps.append(f"<b>Step 2 - Differentiate</b> to get the gradient function: dy/dx = {show(da, v)}")
    m = _val(da, x0)
    steps.append(f"<b>Step 3 - Gradient of the tangent</b> (put x = {fm(x0, 6)} into dy/dx): m = {HL(_num_txt(m))}")
    exact = isinstance(m, Fraction) and isinstance(y0, Fraction)
    if exact:
        c0 = y0 - m * x0
        steps.append(f"<b>Step 4 - Equation of the tangent.</b> Use y &minus; y<sub>1</sub> = m(x &minus; x<sub>1</sub>): y &minus; {_num_txt(y0)} = {_num_txt(m)}(x &minus; {fm(x0, 6)})")
        steps.append(f"Expand and tidy: y = {_num_txt(m)}x + {_num_txt(c0)}  &rarr; {HL('y = ' + (fr(m) if m != 1 else '') + 'x ' + (('+ ' + fr(c0)) if c0 >= 0 else (M_ + ' ' + fr(-c0))) if m != 0 else 'y = ' + fr(c0))}")
        res = (f"<b>Tangent: y = {_num_txt(c0)}</b>" if m == 0 else
               f"<b>Tangent: y = {_num_txt(m)}x {'+' if c0 >= 0 else M_} {_num_txt(abs(c0))}</b>")
        if m == 0:
            nres = f"<b>Normal: x = {fm(x0, 6)}</b> (a vertical line, because the tangent is horizontal)"
            steps.append("<b>Step 5 - The normal</b> is at right angles to the tangent. The tangent is horizontal, so the normal is the vertical line x = " + fm(x0, 6))
            mn = None
        else:
            mn = -1 / m
            cn = y0 - mn * x0
            steps.append(f"<b>Step 5 - The normal</b> is at right angles to the tangent, so its gradient is the negative reciprocal: m<sub>n</sub> = &minus;1/m = {HL(_num_txt(mn))}.")
            steps.append(f"Equation of the normal: y &minus; {_num_txt(y0)} = {_num_txt(mn)}(x &minus; {fm(x0, 6)}) &rarr; y = {_num_txt(mn)}x {'+' if cn >= 0 else M_} {_num_txt(abs(cn))}")
            nres = f"<b>Normal: y = {_num_txt(mn)}x {'+' if cn >= 0 else M_} {_num_txt(abs(cn))}</b>"
    else:
        c0 = float(y0) - float(m) * float(x0)
        res = f"<b>Tangent: y = {float(m):.4g}x + {c0:.4g}</b>"
        steps.append(f"<b>Step 4 - Tangent:</b> y &minus; y<sub>1</sub> = m(x &minus; x<sub>1</sub>) gives y = {float(m):.4g}x + {c0:.4g} (decimals because the numbers are not exact).")
        mn = None if float(m) == 0 else -1 / float(m)
        cn = None if mn is None else float(y0) - mn * float(x0)
        nres = "<b>Normal: " + (f"y = {mn:.4g}x + {cn:.4g}" if mn is not None else f"x = {float(x0):.4g}") + "</b>"
    span = max(abs(float(x0)) * 1.0, 3)
    xr = (float(x0) - span, float(x0) + span)
    lines = [(float(m), float(y0) - float(m) * float(x0), "tangent", "#d97706")]
    if mn is not None:
        lines.append((float(mn), float(y0) - float(mn) * float(x0), "normal", "#059669"))
    img = _plot([(a, f"y = {pr(a, v)}".replace("<sup>", "^").replace("</sup>", "").replace("&minus;", "-").replace("&times;", "*"))],
                pts=[(float(x0), float(y0), f"({fm(x0, 4)}, {float(y0):.4g})")], lines=lines, xr=xr)
    return _ok(steps, {"image": img, "text": res + "<br>" + nres})


# ---------------------------------------------------------------- turning points --

def _poly_roots(ps):
    """real roots of a PS (scaled to polynomial); list of Fraction|float"""
    t = dict(ps.t)
    if not t:
        return None
    if any(k.denominator != 1 for k in t):
        raise UErr("Turning points here need whole-number powers (like x^3 - 3x + 1 or x + 4/x).")
    shift = -min(min(t), 0)
    co = {int(k + shift): c for k, c in t.items()}
    deg = max(co)
    arr = [float(co.get(i, 0)) for i in range(deg, -1, -1)]
    # drop trailing zeros roots at 0
    zero = co.get(0, 0) == 0
    roots = []
    r = np.roots(arr) if deg > 0 else []
    for z in r:
        if abs(z.imag) < 1e-7:
            val = float(z.real)
            fv = Fraction(val).limit_denominator(1000)
            ok = abs(float(fv) - val) < 1e-9 and sum(c * fv ** k for k, c in co.items()) == 0
            roots.append(fv if ok else round(val, 8))
    out = []
    for r_ in roots:
        if not any(abs(float(r_) - float(o)) < 1e-7 for o in out):
            out.append(r_)
    if shift:
        out = [r_ for r_ in out if abs(float(r_)) > 1e-12]   # x = 0 is not allowed when there were negative powers
    return sorted(out, key=float)


@guard
def turning(d):
    a, v = _parse(d.get("f"), "x")
    steps = [f"<b>The curve:</b> y = {show(a, v)}"]
    da = D(a)
    dps = to_ps(da)
    if dps is None:
        raise UErr("This solver finds turning points of polynomials and power expressions like x^3 - 3x or x + 4/x.")
    steps.append(f"<b>Step 1 - Differentiate:</b> dy/dx = {show(da, v)}")
    steps.append("<b>Step 2 - At a turning point the gradient is zero</b> (the curve is momentarily flat), so solve dy/dx = 0.")
    if any(k < 0 for k in dps.t):
        sh = -min(dps.t)
        steps.append(f"Multiply every term by {v}{'' if sh == 1 else '<sup>' + _exp_txt(sh) + '</sup>'} to clear the negative powers: "
                     f"{ps_str(PS({k + sh: c for k, c in dps.t.items()}), v)} = 0 (remember {v} cannot be 0 here).")
    roots = _poly_roots(dps)
    if not roots:
        steps.append("There is no value of x that makes the gradient 0, so the curve has <b>no turning points</b> (it keeps going up, or keeps going down).")
        xr = (-5, 5)
        img = _plot([(a, "y")], xr=xr)
        return _ok(steps, {"image": img, "text": "<b>No turning points.</b>"})
    steps.append("Solving gives x = " + ", ".join(_num_txt(r) for r in roots) + ".")
    d2 = D(da)
    steps.append(f"<b>Step 3 - Second derivative</b> (to decide maximum or minimum): d<sup>2</sup>y/dx<sup>2</sup> = {show(d2, v)}. "
                 "Rule: if it is <b>positive</b> the curve is a valley (<b>minimum</b>); if <b>negative</b> it is a hill (<b>maximum</b>); if zero, check the gradient on both sides.")
    pts = []
    txt = []
    for r in roots:
        try:
            y = _val(a, r)
            s2 = _val(d2, r)
        except UErr:
            continue
        s2f = float(s2)
        if abs(s2f) < 1e-9:
            # sign test on gradient
            xl, xr_ = float(r) - 0.01, float(r) + 0.01
            gl, gr = ev(da, xl), ev(da, xr_)
            nat = "maximum" if gl > 0 > gr else "minimum" if gl < 0 < gr else "point of inflexion"
            why = f"the second derivative is 0, so test the gradient either side: it goes from {'+' if gl > 0 else M_} to {'+' if gr > 0 else M_}"
        else:
            nat = "minimum" if s2f > 0 else "maximum"
            why = f"second derivative = {_num_txt(s2)} which is {'positive' if s2f > 0 else 'negative'}"
        steps.append(f"<b>At x = {_num_txt(r)}:</b> y = {_num_txt(y)}; {why} &rarr; <b>{nat}</b> at ({_num_txt(r)}, {_num_txt(y)}).")
        pts.append((float(r), float(y), f"{nat}\n({fm(Fraction(float(r)).limit_denominator(1000), 3)}, {float(y):.3g})"))
        txt.append(f"{nat} at ({_num_txt(r)}, {_num_txt(y)})")
    xs = [p[0] for p in pts]
    span = max(max(xs) - min(xs), 2)
    xr = (min(xs) - span * 0.7 - 1, max(xs) + span * 0.7 + 1)
    img = _plot([(a, "y = f(x)")], pts=pts, xr=xr)
    # intervals
    if len(roots) >= 1 and all(isinstance(r, (Fraction, float)) for r in roots):
        parts = []
        bounds = [-INF_] + [float(r) for r in roots] + [INF_]
        for i in range(len(bounds) - 1):
            mid = (bounds[i] + bounds[i + 1]) / 2 if abs(bounds[i]) != INF_ and abs(bounds[i + 1]) != INF_ else (bounds[i + 1] - 1 if abs(bounds[i]) == INF_ else bounds[i] + 1)
            try:
                g = ev(da, mid)
            except Exception:
                continue
            lo = "&minus;&infin;" if bounds[i] == -INF_ else _num_txt(roots[i - 1])
            hi = "&infin;" if bounds[i + 1] == INF_ else _num_txt(roots[i])
            parts.append(f"from {lo} to {hi} the gradient is {'positive (curve rising)' if g > 0 else 'negative (curve falling)'}")
        steps.append("<b>Where is the curve rising or falling?</b> " + "; ".join(parts) + ".")
    return _ok(steps, {"image": img, "text": "<b>" + "<br>".join(txt) + "</b>"})


INF_ = float("inf")


# --------------------------------------------------------------------- area/volume --

def _need_ps(a, what):
    ps = to_ps(a)
    if ps is None:
        raise UErr(f"For {what}, use a polynomial or power expression like x^2 + 1, 4 - x^2 or sqrt(x).")
    return ps


def _roots_in(ps, lo, hi):
    """real roots of PS inside (lo, hi) (polynomial only)"""
    try:
        rs = _poly_roots(ps)
    except UErr:
        rs = []
    if rs is None:
        return []
    return [r for r in rs if lo < float(r) < hi]


@guard
def area(d):
    kind = d.get("kind", "under")
    a, v = _parse(d.get("f"), "x")
    ps = _need_ps(a, "area")
    if kind == "between":
        b, _ = _parse(d.get("g"), "x")
        psb = _need_ps(b, "area")
        h = ps - psb
        steps = [f"<b>Upper/lower curves:</b> y = {show(a, v)} and y = {show(b, v)}"]
        cross = _poly_roots(h) or []
        lo_s, hi_s = (d.get("lo") or "").strip(), (d.get("hi") or "").strip()
        if lo_s and hi_s:
            lo, hi = num(lo_s, "the lower limit"), num(hi_s, "the upper limit")
            steps.append(f"<b>Limits given:</b> from x = {fm(lo, 6)} to x = {fm(hi, 6)}.")
        else:
            if len(cross) < 2:
                raise UErr("The two curves do not cross twice, so please give the limits (from x = ... to x = ...).")
            lo, hi = Fraction(cross[0]) if isinstance(cross[0], Fraction) else cross[0], Fraction(cross[-1]) if isinstance(cross[-1], Fraction) else cross[-1]
            steps.append(f"<b>Step 1 - Find where the curves meet</b>: set the two equal, {show(a, v)} = {show(b, v)}, i.e. {ps_str(h, v)} = 0. This gives x = "
                         + ", ".join(_num_txt(r) for r in cross) + f". Use x = {_num_txt(lo)} and x = {_num_txt(hi)} as the limits.")
    else:
        steps = [f"<b>The curve:</b> y = {show(a, v)}"]
        lo, hi = num(d.get("lo"), "the lower limit"), num(d.get("hi"), "the upper limit")
        h = ps
        steps.append(f"<b>Area under the curve</b> between x = {fm(lo, 6)} and x = {fm(hi, 6)}: Area = &int; y dx.")
    if float(hi) <= float(lo):
        raise UErr("The upper limit must be bigger than the lower limit.")
    H = PS(h.t)
    steps.append(f"<b>Area = &int; (upper curve &minus; lower curve) dx</b> = &int; ({ps_str(H, v)}) dx" if kind == "between"
                 else f"<b>Integrate:</b> &int; ({ps_str(H, v)}) dx")
    A = Anti()
    P, lc = H.integ()
    A.ps, A.lcoef = P, lc
    steps.append(f"Integral = [{A.text(v)}]")
    cuts = [r for r in _roots_in(H, float(lo), float(hi))]
    pieces = [lo] + cuts + [hi]
    total = 0
    rows = []
    for i in range(len(pieces) - 1):
        l, r = pieces[i], pieces[i + 1]
        try:
            val = A.at(r) - A.at(l)
        except CErr as e:
            raise UErr(str(e))
        rows.append((l, r, val))
        total = total + abs(val)
    if len(rows) > 1:
        steps.append("<b>The curve crosses the x-axis inside the limits</b>, so area above and below must be found separately and each taken as a positive size:")
    for l, r, val in rows:
        steps.append(f"From {_num_txt(l)} to {_num_txt(r)}: [{A.text(v)}] = {_num_txt(A.at(r))} &minus; ({_num_txt(A.at(l))}) = {_num_txt(val)}"
                     + (f" &rarr; area {_num_txt(abs(val))} (below the axis, so make it positive)" if val < 0 else ""))
    if len(rows) > 1:
        steps.append(f"Add the sizes: {HL(_num_txt(total))}")
    else:
        steps.append(f"<b>Area = {HL(_num_txt(abs(total)))}</b> square units" + ("" if rows[0][2] >= 0 else " (the integral was negative because the region is below the axis; area is its positive size)"))
    xr = (float(lo) - 0.6 * (float(hi) - float(lo)) - 0.5, float(hi) + 0.6 * (float(hi) - float(lo)) + 0.5)
    curves = [(a, "y = " + pr(a, v).replace("<sup>", "^").replace("</sup>", "").replace("&minus;", "-"))]
    shade = [(float(lo), float(hi), None)]
    if kind == "between":
        curves.append((b, "y = " + pr(b, v).replace("<sup>", "^").replace("</sup>", "").replace("&minus;", "-")))
        shade = [(float(lo), float(hi), (lambda X, b=b: np.array([ev(b, float(x)) for x in X])))]
    img = _plot(curves, shade=shade, xr=xr)
    return _ok(steps, {"image": img, "text": f"<b>Area = {_num_txt(total)} square units</b>" + (f" &nbsp;(&asymp; {fm(Fraction(float(total)).limit_denominator(10**6), 4)})" if isinstance(total, Fraction) and total.denominator != 1 else "")})


@guard
def volume(d):
    a, v = _parse(d.get("f"), "x")
    ps = _need_ps(a, "volume of revolution")
    lo, hi = num(d.get("lo"), "the lower limit"), num(d.get("hi"), "the upper limit")
    if hi <= lo:
        raise UErr("The upper limit must be bigger than the lower limit.")
    steps = [f"<b>The curve:</b> y = {show(a, v)}, rotated 360&deg; about the x-axis from x = {fm(lo, 6)} to x = {fm(hi, 6)}."]
    steps.append("<b>Formula:</b> Volume = &pi; &int; y<sup>2</sup> dx (imagine slicing the solid into thin discs of radius y).")
    y2 = ps * ps
    steps.append(f"<b>Step 1 - Square y:</b> y<sup>2</sup> = ({ps_str(ps, v)})<sup>2</sup> = {ps_str(y2, v)}")
    A = Anti()
    P, lc = y2.integ()
    A.ps, A.lcoef = P, lc
    steps.append(f"<b>Step 2 - Integrate:</b> [{A.text(v)}]")
    try:
        Fh, Fl = A.at(hi), A.at(lo)
    except CErr as e:
        raise UErr(str(e))
    steps.append(f"<b>Step 3 - Limits:</b> {_num_txt(Fh)} &minus; ({_num_txt(Fl)}) = {_num_txt(Fh - Fl)}")
    val = Fh - Fl
    if isinstance(val, Fraction):
        res = f"{fr(val)}&pi;" if val.denominator != 1 else f"{val.numerator}&pi;"
        steps.append(f"<b>Step 4 - Multiply by &pi;:</b> Volume = {HL(res)} cubic units &asymp; {float(val) * math.pi:.4f} (using &pi; = 3.1416).")
    else:
        res = f"{float(val):.4f}&pi;"
        steps.append(f"<b>Step 4:</b> Volume = {float(val):.4f}&pi; &asymp; {float(val) * math.pi:.4f}")
    xr = (float(lo) - 0.5 * (float(hi) - float(lo)) - 0.3, float(hi) + 0.5 * (float(hi) - float(lo)) + 0.3)
    img = _plot([(a, "y = " + pr(a, v).replace("<sup>", "^").replace("</sup>", "").replace("&minus;", "-"))], shade=[(float(lo), float(hi), None)], xr=xr)
    return _ok(steps, {"image": img, "text": f"<b>Volume = {res} cubic units</b>"})


# ------------------------------------------------------------------- rates / motion --

@guard
def rates(d):
    kind = d.get("kind", "motion_s")
    if kind == "related":
        a, v = _parse(d.get("f"), None)
        x0 = num(d.get("at"), f"the value of {v}")
        rate = num(d.get("rate"), f"the rate d{v}/dt")
        steps = [f"<b>Relationship:</b> y = {show(a, v)}. We know how fast {v} changes: d{v}/dt = {fm(rate, 6)}. We want how fast y changes, dy/dt, when {v} = {fm(x0, 6)}."]
        steps.append(f"<b>Chain rule for rates:</b> dy/dt = dy/d{v} &times; d{v}/dt.")
        da = D(a)
        steps.append(f"<b>Step 1 - Differentiate y with respect to {v}:</b> dy/d{v} = {show(da, v)}")
        g = _val(da, x0)
        steps.append(f"<b>Step 2 - Put {v} = {fm(x0, 6)}:</b> dy/d{v} = {_num_txt(g)}")
        r = g * rate if not isinstance(g, float) else g * float(rate)
        steps.append(f"<b>Step 3 - Multiply:</b> dy/dt = {_num_txt(g)} &times; {fm(rate, 6)} = {HL(_num_txt(r))}")
        return _ok(steps, f"<b>dy/dt = {_num_txt(r)}</b> ({'increasing' if float(r) > 0 else 'decreasing' if float(r) < 0 else 'not changing'})")
    a, v = _parse(d.get("f"), "t")
    t0 = num(d.get("at"), "the time t", blank=True)
    steps = []
    if kind == "motion_s":
        s = a
        steps.append(f"<b>Displacement:</b> s = {show(s, v)} (distance from a fixed point at time t).")
        vel = D(s)
        steps.append(f"<b>Velocity = rate of change of displacement:</b> v = ds/dt = {show(vel, v)}")
        acc = D(vel)
        steps.append(f"<b>Acceleration = rate of change of velocity:</b> a = dv/dt = {show(acc, v)}")
    elif kind == "motion_v":
        vel = a
        s0 = num(d.get("s0") or "0", "the starting displacement")
        steps.append(f"<b>Velocity:</b> v = {show(vel, v)}")
        acc = D(vel)
        steps.append(f"<b>Acceleration</b> = dv/dt = {show(acc, v)}")
        A = antiderivative(vel, v)
        c = s0 - A.at(0)
        steps.append(f"<b>Displacement</b> = &int; v dt = {A.text(v)} + c. When t = 0, s = {fm(s0, 6)}, so c = {_num_txt(c)}.")
        s = None
        s_txt = A.text(v) + (f" + {_num_txt(c)}" if c != 0 else "")
        steps.append(f"So s = {HL(s_txt)}")
    else:
        acc = a
        v0 = num(d.get("v0") or "0", "the starting velocity")
        s0 = num(d.get("s0") or "0", "the starting displacement")
        steps.append(f"<b>Acceleration:</b> a = {show(acc, v)}")
        A1 = antiderivative(acc, v)
        c1 = v0 - A1.at(0)
        steps.append(f"<b>Velocity</b> = &int; a dt = {A1.text(v)} + c<sub>1</sub>; when t = 0, v = {fm(v0, 6)} so c<sub>1</sub> = {_num_txt(c1)}.")
        vel_ps = (A1.ps + PS.const(c1)) if isinstance(c1, Fraction) else None
        if vel_ps is None or A1.lcoef or A1.extra:
            raise UErr("For velocity and displacement from acceleration, use polynomial expressions in t.")
        vel = ("poly", vel_ps)
        steps.append(f"v = {HL(ps_str(vel_ps, v))}")
        A2 = antiderivative(parse(ps_plain(vel_ps, v), v)[0], v)
        c2 = s0 - A2.at(0)
        steps.append(f"<b>Displacement</b> = &int; v dt = {A2.text(v)} + c<sub>2</sub>; when t = 0, s = {fm(s0, 6)} so c<sub>2</sub> = {_num_txt(c2)}.")
        s_ps = A2.ps + PS.const(c2)
        steps.append(f"s = {HL(ps_str(s_ps, v))}")
        s = ("poly", s_ps)
        vel = parse(ps_plain(vel_ps, v), v)[0]
        s = parse(ps_plain(s_ps, v), v)[0]
    out = []
    if t0 is not None:
        if kind == "motion_v":
            sv = A.at(t0) + c
        else:
            sv = _val(s, t0)
        vv = _val(vel, t0)
        aa = _val(acc, t0)
        steps.append(f"<b>At t = {fm(t0, 6)}:</b> s = {_num_txt(sv)}, v = {_num_txt(vv)}, a = {_num_txt(aa)}.")
        out.append(f"At t = {fm(t0, 6)}: s = {_num_txt(sv)}, v = {_num_txt(vv)}, a = {_num_txt(aa)}")
    vps = to_ps(vel) if vel[0] != "poly" else vel[1]
    if vps is not None:
        try:
            rs = [r for r in (_poly_roots(vps) or []) if float(r) >= 0]
        except UErr:
            rs = []
        if rs:
            steps.append(f"<b>When is the particle at rest?</b> Set v = 0: t = " + ", ".join(_num_txt(r) for r in rs) + " (only t &ge; 0 makes sense).")
            out.append("At rest when t = " + ", ".join(_num_txt(r) for r in rs))
    return _ok(steps, "<b>" + "<br>".join(out) + "</b>" if out else "<b>Done</b>")


# ------------------------------------------------------------------------ spec ---

SPEC = {
    "title": "Calculus",
    "intro": "Differentiation, integration, tangents, turning points, areas, volumes and rates of change. "
             "Type powers with ^ (x^2), roots as sqrt(x) or x^(1/2), fractions with /. Trig and e^x work too: sin(2x), e^(3x), ln(x).",
    "tabs": [
        {"id": "cd", "label": "Differentiate", "title": "Differentiation", "endpoint": "diff",
         "hint": "Examples: <i>3x^2 - 5x + 7</i> &nbsp; <i>(2x+1)^3</i> &nbsp; <i>x^2(x+1)</i> &nbsp; <i>(x+1)/(x-1)</i> &nbsp; <i>2x^3 - 4/x + sqrt(x)</i> &nbsp; <i>sin(2x)</i>",
         "fields": [field("f", "y =", "3x^2 - 5x + 7", wide=True, half=False),
                    select("kind", "Find", [("first", "dy/dx"), ("second", "dy/dx and d&sup2;y/dx&sup2;"), ("at", "the gradient at a point"),
                                            ("first_p", "dy/dx from first principles (polynomials)")], wide=True),
                    field("at", "x =", "2", show_if={"kind": "at"})]},
        {"id": "ci", "label": "Integrate", "title": "Integration", "endpoint": "integ",
         "hint": "Examples: <i>3x^2 + 4x - 1</i> &nbsp; <i>(2x+1)^3</i> &nbsp; <i>1/x^2</i> &nbsp; <i>sqrt(x)</i> &nbsp; <i>cos(3x)</i> &nbsp; <i>e^(2x)</i>",
         "fields": [field("f", "Integrate", "3x^2 + 4x - 1", wide=True, half=False),
                    select("kind", "Type", [("indef", "indefinite (with + c)"), ("def", "definite (with limits)")], wide=True),
                    field("lo", "Lower limit", "1", show_if={"kind": "def"}), field("hi", "Upper limit", "3", show_if={"kind": "def"})]},
        {"id": "ct", "label": "Tangent & normal", "title": "Tangent and normal to a curve", "endpoint": "tangent",
         "fields": [field("f", "Curve y =", "x^2 - 3x + 2", wide=True, half=False), field("at", "at x =", "3")]},
        {"id": "cp", "label": "Turning points", "title": "Turning points, maximum and minimum", "endpoint": "turning",
         "fields": [field("f", "Curve y =", "x^3 - 3x + 1", wide=True, half=False)]},
        {"id": "ca", "label": "Area", "title": "Area under a curve or between curves", "endpoint": "area",
         "fields": [select("kind", "Find the area", [("under", "between a curve and the x-axis"), ("between", "between two curves")], wide=True),
                    field("f", "Curve y =  (the upper curve if two)", "x^2", wide=True, half=False),
                    field("g", "Second curve y =", "x", show_if={"kind": "between"}),
                    field("lo", "from x =  (leave empty to use where the curves meet)", "0"), field("hi", "to x =", "3")]},
        {"id": "cv", "label": "Volume of revolution", "title": "Volume when a curve is rotated about the x-axis", "endpoint": "volume",
         "fields": [field("f", "Curve y =", "x^2", wide=True, half=False), field("lo", "from x =", "0"), field("hi", "to x =", "2")]},
        {"id": "cr", "label": "Rates & motion", "title": "Rates of change and motion", "endpoint": "rates",
         "hint": "For motion use the letter t (time).",
         "fields": [select("kind", "Type of problem", [("motion_s", "I know the displacement s(t)"), ("motion_v", "I know the velocity v(t)"),
                                                       ("motion_a", "I know the acceleration a(t)"), ("related", "Related rates: dy/dt from dx/dt")], wide=True),
                    field("f", "Expression (in t, or in x for related rates)", "t^3 - 6t^2 + 9t", wide=True, half=False),
                    field("s0", "Displacement at t = 0", "0", show_if={"kind": ["motion_v", "motion_a"]}),
                    field("v0", "Velocity at t = 0", "0", show_if={"kind": "motion_a"}),
                    field("at", "Find at time t =  (optional)", "2", show_if={"kind": ["motion_s", "motion_v", "motion_a"]}),
                    field("at", "when x = ", "4", show_if={"kind": "related"}),
                    field("rate", "dx/dt =", "3", show_if={"kind": "related"})]},
    ],
}

topics.register("calculus", SPEC, {"diff": differentiate, "integ": integrate, "tangent": tangent, "turning": turning,
                                     "area": area, "volume": volume, "rates": rates})
