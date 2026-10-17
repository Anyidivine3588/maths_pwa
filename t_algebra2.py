"""Algebra tools: polynomial long & synthetic division, remainder/factor theorem, factorising and expanding,
change of subject, roots of quadratics (nature, sum and product, forming equations) and means."""
import math
from fractions import Fraction

import topics
from tcommon import UErr, fm, num, field, select, guard, _ok, _fail
from log_core import LogErr, parse, real_roots, P1, sig, fmtq
from mpoly import (MP, parse_poly, from_node, to_coeffs, from_coeffs, divmod_poly, br, mono_text)

MINUS = "&minus;"
TIMES = "&times;"


def HL(s):
    return f"<span class='hl'>{s}</span>"


def q_(x):
    """Fraction -> text (integer, p/q) with HTML minus"""
    x = Fraction(x)
    return (str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}").replace("-", MINUS)


def ptxt(c, v):
    return from_coeffs(c, v).text()


def one_var(*polys):
    vs = set()
    for p in polys:
        vs |= set(p.vars())
    if len(vs) > 1:
        raise UErr("Use only one letter (like x) in these polynomials. I found: " + ", ".join(sorted(vs)) + ".")
    return next(iter(vs)) if vs else "x"


def wrap(fn):
    def w(d):
        try:
            return fn(d)
        except (UErr, LogErr) as e:
            return _fail(str(e))
    w.__name__ = fn.__name__
    return w


def cell(c, e, v, first=False, show_sign=True):
    """one table cell for coefficient c at power e"""
    c = Fraction(c)
    if c == 0:
        return ""
    mag = abs(c)
    body = ("" if (mag == 1 and e > 0) else q_(mag)) + (v if e == 1 else (f"{v}<sup>{e}</sup>" if e > 1 else ""))
    return (MINUS if c < 0 else ("" if first or not show_sign else "+")) + body


def grid(rows, degs, v, label_w=None, cls="stat-table"):
    html = f"<table class='{cls}'>"
    for kind, label, data in rows:
        html += "<tr>"
        html += f"<th style='text-align:right'>{label}</th>"
        for j, e in enumerate(degs):
            c = data.get(e)
            if kind == "head":
                html += f"<th>{(v + '<sup>' + str(e) + '</sup>') if e > 1 else (v if e == 1 else '')}{'' if e else 'number'}</th>"
            else:
                txt = cell(c, e, v, first=True) if c is not None else ""
                if kind == "quot" and c is not None:
                    txt = f"<b>{txt}</b>"
                html += f"<td style='text-align:right'>{txt}</td>"
        html += "</tr>"
    return html + "</table>"


# ===================================================================== long & synthetic division
@wrap
def longdiv(d):
    P = parse_poly(d.get("p"))
    Dv = parse_poly(d.get("dv"))
    v = one_var(P, Dv)
    if Dv.is_zero():
        raise UErr("You cannot divide by zero. Type the divisor, for example x - 2.")
    pc, dc = to_coeffs(P, v), to_coeffs(Dv, v)
    pdeg, ddeg = len(pc) - 1, len(dc) - 1
    method = d.get("method", "long")
    steps = [f"<b>Divide</b> {HL(P.text())} <b>by</b> {HL(Dv.text())}.",
             f"<b>What we are doing:</b> just like dividing numbers (long division), we find a <b>quotient</b> Q and a <b>remainder</b> R so that <b>dividend = divisor &times; Q + R</b>, where R has a smaller power than the divisor."]
    if pdeg < ddeg:
        steps.append(f"The divisor has a higher power ({v}<sup>{ddeg}</sup>) than the dividend ({v}<sup>{pdeg}</sup>), so it cannot be divided: the quotient is 0 and the remainder is the whole polynomial.")
        return _ok(steps, f"<b>Q = 0, R = {P.text()}</b>")
    if method == "synth" and ddeg == 1:
        return synthetic(P, Dv, pc, dc, v, steps)
    if method == "synth":
        steps.append("<i>Synthetic division only works for a divisor like (x &minus; a). Using long division instead.</i>")
    # ---- long division
    n = pdeg
    degs = list(range(n, -1, -1))
    steps.append(f"<b>Before we start:</b> write both in <b>descending powers</b> of {v} and put in a 0 for any missing power (like 0{v}<sup>2</sup>) so every power has its own place.")
    cur = {i: pc[i] for i in range(len(pc))}
    q = {}
    rows = [("head", "", {}), ("quot", "Quotient", q), ("row", f"<b>{Dv.text()}</b> &#10073;", dict(cur))]
    rem = list(pc)
    rnd = 0
    while len(rem) - 1 >= ddeg and any(rem):
        while rem and rem[-1] == 0:
            rem.pop()
        if len(rem) - 1 < ddeg:
            break
        rnd += 1
        k = len(rem) - 1 - ddeg
        lt = rem[-1]
        dl = dc[-1]
        f = lt / dl
        q[k] = f
        prod = {k + i: f * dc[i] for i in range(len(dc))}
        new = list(rem)
        for e, c in prod.items():
            new[e] -= c
        while new and new[-1] == 0:
            new.pop()
        lead_txt = cell(lt, len(rem) - 1, v, first=True)
        dlead = cell(dl, ddeg, v, first=True)
        qt = cell(f, k, v, first=True)
        prod_txt = from_coeffs([prod.get(i, Fraction(0)) for i in range(max(prod) + 1)], v).text()
        steps.append(
            f"<b>Round {rnd}.</b><br>"
            f"&bull; <b>Divide the first terms:</b> {lead_txt} &divide; {dlead} = {HL(qt or '1')}. Write it on the top line (the quotient).<br>"
            f"&bull; <b>Multiply</b> {qt or '1'} by the <i>whole</i> divisor: {qt or '1'}({Dv.text()}) = {prod_txt}.<br>"
            f"&bull; <b>Subtract</b> this from what is left (change every sign and add; be careful with the minus signs): ({from_coeffs(rem, v).text()}) &minus; ({prod_txt}) = {from_coeffs(new, v).text() if new else '0'}.")
        rows.append(("row", "subtract", dict(prod)))
        rows.append(("row", "gives", {i: new[i] for i in range(len(new))} if new else {}))
        rem = new
        if rnd > 40:
            break
    Qc = [q.get(i, Fraction(0)) for i in range(max(q) + 1)] if q else [Fraction(0)]
    steps.append(f"<b>Stop</b> when what is left has a smaller power than the divisor. What is left is the <b>remainder</b>.")
    Q = from_coeffs(Qc, v)
    R = from_coeffs(rem, v)
    steps.append("<b>The working laid out like the long division you know:</b>" + grid(rows, degs, v))
    steps.append(f"<b>Quotient</b> Q = {HL(Q.text())} &nbsp; <b>Remainder</b> R = {HL(R.text())}")
    chk = Dv * Q + R
    steps.append(f"<b>Check:</b> divisor &times; Q + R = ({Dv.text()})({Q.text()}) + {br(R) if not R.is_zero() else '0'} = {chk.text()} {'&check; (this is the dividend)' if chk == P else '(mismatch!)'}")
    if R.is_zero():
        steps.append(f"<b>The remainder is 0</b>, so the division is exact: ({Dv.text()}) is a <b>factor</b> of {P.text()}, and {P.text()} = ({Dv.text()})({Q.text()}).")
        return _ok(steps, f"<b>Q = {Q.text()}, R = 0</b> &nbsp;(exact: {P.text()} = ({Dv.text()})({Q.text()}))")
    steps.append(f"So {P.text()} = ({Dv.text()})({Q.text()}) + {br(R)}")
    return _ok(steps, f"<b>Q = {Q.text()}, R = {R.text()}</b>")


def synthetic(P, Dv, pc, dc, v, steps):
    a_, b_ = dc[1], dc[0]
    root = -b_ / a_
    steps.append(f"<b>Synthetic division (a quick short-cut)</b> works when the divisor is linear. Write the divisor as ({v} &minus; r): {Dv.text()} = 0 gives {v} = {q_(root)}, so r = <b>{q_(root)}</b>.")
    top = list(reversed(pc))
    mid = [Fraction(0)]
    bot = [top[0]]
    for i in range(1, len(top)):
        mid.append(bot[-1] * root)
        bot.append(top[i] + mid[-1])
    html = "<table class='stat-table'><tr><th>r = " + q_(root) + "</th>" + "".join(f"<td style='text-align:right'>{q_(c)}</td>" for c in top) + "</tr>"
    html += "<tr><th>multiply by r</th><td></td>" + "".join(f"<td style='text-align:right'>{q_(c)}</td>" for c in mid[1:]) + "</tr>"
    html += "<tr><th>add down</th>" + "".join(f"<td style='text-align:right'><b>{q_(c)}</b></td>" for c in bot) + "</tr></table>"
    steps.append("<b>How to fill the table:</b> (1) write the coefficients of the dividend in a row (put 0 for missing powers); (2) bring the first one straight down; (3) multiply it by r and write the answer under the next coefficient; (4) add the column; (5) repeat until the end. The last number is the <b>remainder</b>; the numbers before it are the coefficients of the quotient.")
    steps.append(html)
    qc = bot[:-1]
    Qp = from_coeffs(list(reversed(qc)), v)
    R = bot[-1]
    if a_ != 1:
        steps.append(f"Because the divisor is {Dv.text()} (the number in front of {v} is {q_(a_)}, not 1), divide the quotient by {q_(a_)}: Q = ({Qp.text()}) &divide; {q_(a_)} = {from_coeffs(list(reversed([c / a_ for c in qc])), v).text()}. The remainder stays {q_(R)}.")
        Qp = from_coeffs(list(reversed([c / a_ for c in qc])), v)
    steps.append(f"<b>Quotient</b> Q = {HL(Qp.text())}, <b>remainder</b> R = {HL(q_(R))}")
    chk = Dv * Qp + MP.const(R)
    steps.append(f"<b>Check:</b> ({Dv.text()})({Qp.text()}) + {q_(R)} = {chk.text()} {'&check;' if chk == P else '(mismatch!)'}")
    if R == 0:
        steps.append(f"The remainder is 0, so ({Dv.text()}) is a factor.")
    return _ok(steps, f"<b>Q = {Qp.text()}, R = {q_(R)}</b>")


# ===================================================================== remainder / factor theorem
def lin_root(dv_text, v="x"):
    """linear divisor text -> (a, b, root) for a*v + b"""
    Dv = parse_poly(dv_text)
    if Dv.deg_in(v) != 1 or any(w != v for w in Dv.vars()):
        raise UErr(f"The divisor must be linear in {v}, like {v} - 2 or 2{v} + 1.")
    a, b = Dv.coeff_in(v, 1).const_value(), Dv.coeff_in(v, 0).const_value()
    return a, b, -b / a, Dv


def subst_text(P, v, r):
    """p(r) = term by term"""
    terms = P.terms_sorted()
    rr = q_(r) if r.denominator == 1 and r >= 0 else f"({q_(r)})"
    parts, vals = [], []
    for m, c in terms:
        e = dict(m).get(v, 0)
        val = c * r ** e
        vals.append(val)
        mag = abs(c)
        body = (q_(mag) + (" " if False else "")) if (mag != 1 or e == 0) else ""
        if e == 0:
            piece = q_(mag)
        else:
            piece = (q_(mag) + TIMES if mag != 1 else "") + f"{rr}" + (f"<sup>{e}</sup>" if e > 1 else "")
        parts.append((c < 0, piece))
    expr = ""
    for i, (neg, piece) in enumerate(parts):
        expr += (MINUS if neg else "") + piece if i == 0 else (f" {MINUS} " if neg else " + ") + piece
    nums = ""
    for i, val in enumerate(vals):
        nums += (MINUS if val < 0 else "") + q_(abs(val)) if i == 0 else (f" {MINUS} " if val < 0 else " + ") + q_(abs(val))
    return expr, nums, sum(vals, Fraction(0))


@wrap
def theorem(d):
    P = parse_poly(d.get("p"))
    letters = [w for w in P.vars() if w != "x"]
    conds = []
    for i in (1, 2):
        dv = (d.get(f"d{i}") or "").strip()
        rv = (d.get(f"r{i}") or "").strip()
        if dv:
            a, b, r, Dv = lin_root(dv)
            conds.append((Dv, a, b, r, rv))
    if not conds:
        raise UErr("Type a divisor like x - 2 (or 2x + 1).")
    if "x" not in P.vars() and not letters:
        raise UErr("The polynomial must contain x.")
    steps = [f"<b>Polynomial:</b> p(x) = {HL(P.text())}",
             "<b>Remainder theorem:</b> when p(x) is divided by (x &minus; a), the remainder is simply <b>p(a)</b> &mdash; just put x = a into the polynomial. If the divisor is (ax + b), use x = &minus;b/a.",
             "<b>Factor theorem:</b> (x &minus; a) is a factor of p(x) exactly when the remainder p(a) = 0."]
    if not letters:
        res = []
        for Dv, a, b, r, rv in conds:
            steps.append(f"<b>Divisor</b> {Dv.text()}: it is zero when x = {HL(q_(r))}, so the remainder is p({q_(r)}).")
            expr, nums, val = subst_text(P, "x", r)
            steps.append(f"p({q_(r)}) = {expr}<br>= {nums} = {HL(q_(val))}")
            if val == 0:
                steps.append(f"The remainder is <b>0</b>, so <b>({Dv.text()}) IS a factor</b> of p(x).")
                res.append(f"remainder = 0, ({Dv.text()}) is a factor")
            else:
                steps.append(f"The remainder is {q_(val)}, not 0, so ({Dv.text()}) is <b>not</b> a factor.")
                res.append(f"remainder = {q_(val)}")
        return _ok(steps, "<b>" + "; ".join(res) + "</b>")
    # unknown letters
    if len(letters) > 2:
        raise UErr("I can find up to two unknown letters (for example a and b). I found: " + ", ".join(letters) + ".")
    eqs = []
    for Dv, a, b, r, rv in conds:
        target = Fraction(0) if rv == "" else num(rv, "the remainder")
        label = "is a factor (remainder 0)" if rv == "" else f"leaves remainder {q_(target)}"
        steps.append(f"<b>Condition:</b> dividing by ({Dv.text()}) {label}. Put x = {HL(q_(r))}:")
        pv = P.subs("x", MP.const(r))
        steps.append(f"p({q_(r)}) = {pv.text()}")
        eq = pv - MP.const(target)
        steps.append(f"This must equal {q_(target)}: {HL(pv.text() + ' = ' + q_(target))}" + (f" &nbsp;i.e. {eq.text()} = 0" if target != 0 else ""))
        eqs.append(eq)
    if len(letters) == 1:
        u = letters[0]
        if len(eqs) > 1:
            steps.append("Only one letter is unknown, so one equation is enough (the other should agree).")
        eq = eqs[0]
        cs = [eq.coeff_in(u, i).const_value() for i in range(eq.deg_in(u) + 1)]
        if eq.deg_in(u) == 1:
            a1, c0 = cs[1], cs[0]
            ans = -c0 / a1
            steps.append(f"<b>Solve:</b> {q_(a1) if a1 != 1 else ''}{u} {'+' if c0 >= 0 else MINUS} {q_(abs(c0))} = 0 &rarr; {q_(a1) if a1 != 1 else ''}{u} = {q_(-c0)} &rarr; {HL(u + ' = ' + q_(ans))}")
            # show polynomial
            final = P.subs(u, MP.const(ans))
            steps.append(f"<b>So the polynomial is</b> p(x) = {final.text()}")
            return _ok(steps, f"<b>{u} = {q_(ans)}</b>")
        if eq.deg_in(u) == 2:
            E = P1(cs)
            roots = real_roots(E)
            steps.append(f"<b>Solve the quadratic in {u}:</b> {eq.text()} = 0")
            res = ", ".join(f"{u} = {r[2]}" + ("" if r[0] is not None else f" &asymp; {sig(r[1], 4)}") for r in roots) or "no real value"
            return _ok(steps, f"<b>{res}</b>")
        raise UErr("The unknown letter appears with a power higher than 2; this tool cannot solve that.")
    # two unknowns: need two equations
    if len(eqs) < 2:
        raise UErr("There are two unknown letters, so I need two conditions. Fill in the second divisor (and remainder) too.")
    u, w = letters
    def lin(eq):
        return eq.coeff_in(u, 1).const_value(), eq.coeff_in(w, 1).const_value(), eq.const_value()
    for eq in eqs:
        if eq.deg_in(u) > 1 or eq.deg_in(w) > 1 or any(len(m) > 1 and dict(m).get(u) and dict(m).get(w) for m in eq.t):
            raise UErr("The unknown letters must appear to the power 1 only (no u&times;w terms).")
    (a1, b1, c1), (a2, b2, c2) = lin(eqs[0]), lin(eqs[1])
    steps.append(f"<b>Two equations in {u} and {w}:</b><br>({1}) {eqs[0].text()} = 0<br>({2}) {eqs[1].text()} = 0")
    det = a1 * b2 - a2 * b1
    if det == 0:
        raise UErr("These two conditions do not give a single answer (the equations are not independent).")
    U = (-c1 * b2 + c2 * b1) / det
    W = (-a1 * c2 + a2 * c1) / det
    steps.append(f"<b>Solve them together</b> (elimination or substitution): {HL(u + ' = ' + q_(U))} and {HL(w + ' = ' + q_(W))}.")
    chk = [eq.subs(u, MP.const(U)).subs(w, MP.const(W)) for eq in eqs]
    steps.append("<b>Check:</b> putting both values back makes both equations 0 " + ("&check;" if all(c.is_zero() for c in chk) else "(mismatch!)"))
    final = P.subs(u, MP.const(U)).subs(w, MP.const(W))
    steps.append(f"<b>So the polynomial is</b> p(x) = {final.text()}")
    return _ok(steps, f"<b>{u} = {q_(U)}, {w} = {q_(W)}</b>")


# ===================================================================== expanding brackets
def _flat_mul(node, out):
    if node[0] == "mul":
        _flat_mul(node[1], out)
        _flat_mul(node[2], out)
    else:
        out.append(node)


def _mono_str(m):
    return mono_text(m)


def _prod_line(A, B):
    """term-by-term products of two MPs -> (lines, result MP)"""
    lines = []
    res = MP()
    for ma, ca in A.terms_sorted():
        for mb, cb in B.terms_sorted():
            t = MP({ma: ca}) * MP({mb: cb})
            res = res + t
            ta, tb = MP({ma: ca}), MP({mb: cb})
            lines.append(f"({ta.text()}) &times; ({tb.text()}) = {t.text()}")
    return lines, res


def _expand_steps(factors, steps):
    cur = factors[0]
    for nxt in factors[1:]:
        if len(cur.t) == 1 or len(nxt.t) == 1:
            lines, res = _prod_line(cur, nxt)
            if len(cur.t) == 1 and len(nxt.t) == 1:
                steps.append(f"({cur.text()})({nxt.text()}) = {HL(res.text())}")
            else:
                steps.append(f"<b>Multiply each term inside the bracket by the term outside:</b> {br(cur)}{br(nxt)}<br>" + "<br>".join(lines) + f"<br>= {HL(res.text())}")
        elif cur == nxt and len(cur.t) == 2:
            (m1, c1), (m2, c2) = cur.terms_sorted()
            a, b = MP({m1: c1}), MP({m2: c2})
            sq = a * a + (a * b).scale(2) + b * b
            steps.append(f"<b>Square of a bracket:</b> (a + b)<sup>2</sup> = a<sup>2</sup> + 2ab + b<sup>2</sup>. Here a = {a.text()}, b = {b.text() if c2 > 0 else '(' + b.text() + ')'}:<br>"
                         f"a<sup>2</sup> = {(a * a).text()}; 2ab = {(a * b).scale(2).text()}; b<sup>2</sup> = {(b * b).text()}<br>= {HL(sq.text())}")
            res = sq
        else:
            lines, res = _prod_line(cur, nxt)
            how = "(FOIL: First, Outer, Inner, Last)" if len(cur.t) == 2 and len(nxt.t) == 2 else ""
            steps.append(f"<b>Multiply every term in the first bracket by every term in the second {how}:</b> ({cur.text()})({nxt.text()})<br>" + "<br>".join(lines))
            allt = MP()
            raw = ""
            for ma, ca in cur.terms_sorted():
                for mb, cb in nxt.terms_sorted():
                    t = MP({ma: ca}) * MP({mb: cb})
                    ((m_, c_),) = t.t.items()
                    seg = (q_(abs(c_)) if (abs(c_) != 1 or not m_) else "") + mono_text(m_)
                    raw += (f" {MINUS} " if c_ < 0 else (" + " if raw else "")) + seg if raw else ((MINUS if c_ < 0 else "") + seg)
            steps.append(f"<b>Put them together:</b> {raw}<br><b>Collect like terms</b> (terms with exactly the same letters and powers): {HL(res.text())}")
        cur = res
    return cur


@wrap
def expand(d):
    txt = d.get("e")
    node = parse(str(txt or "").strip(), plain=True)
    fs = []
    _flat_mul(node, fs)
    facs = []
    for f in fs:
        if f[0] == "pow":
            e = from_node(f[2])
            if e.is_const() and e.const_value().denominator == 1 and 2 <= e.const_value() <= 5:
                base = from_node(f[1])
                facs += [base] * int(e.const_value())
                continue
        facs.append(from_node(f))
    steps = [f"<b>Expand</b> (remove the brackets): {HL(node_text(txt))}"]
    if len(facs) == 1:
        steps.append("There are no brackets to multiply out. Just collecting terms:")
        res = facs[0]
    else:
        res = _expand_steps(facs, steps)
    steps.append(f"<b>Answer:</b> {HL(res.text())}")
    return _ok(steps, f"<b>{res.text()}</b>")


def node_text(t):
    return str(t).strip().replace("*", "").replace("^", "").replace("-", MINUS) if False else str(t).strip()


# ===================================================================== factorising
def _isq(n):
    n = Fraction(n)
    if n < 0:
        return None
    a, b = math.isqrt(n.numerator), math.isqrt(n.denominator)
    return Fraction(a, b) if a * a == n.numerator and b * b == n.denominator else None


def _icube(n):
    n = Fraction(n)
    sg = -1 if n < 0 else 1
    n = abs(n)
    a, b = round(n.numerator ** (1 / 3)), round(n.denominator ** (1 / 3))
    for aa in (a - 1, a, a + 1):
        for bb in (b - 1, b, b + 1):
            if aa > 0 and bb > 0 and aa ** 3 == n.numerator and bb ** 3 == n.denominator:
                return sg * Fraction(aa, bb)
    return None


def _mono_pow_root(m, k):
    """monomial exponents divisible by k -> root monomial dict or None"""
    out = {}
    for v, e in m:
        if e % k:
            return None
        out[v] = e // k
    return out


def _lead(p):
    return p.terms_sorted()[0]


def _norm(p):
    """make leading coefficient positive: returns (sign, p)"""
    return (-1, -p) if _lead(p)[1] < 0 else (1, p)


def _rational_roots(P, v):
    cs = to_coeffs(P, v)
    while cs and cs[-1] == 0:
        cs.pop()
    # integer coefficients
    L = 1
    for c in cs:
        L = L * c.denominator // math.gcd(L, c.denominator)
    ic = [int(c * L) for c in cs]
    lo = ic[0]
    if lo == 0:
        return [Fraction(0)]
    hi = ic[-1]
    def divs(n):
        n = abs(n)
        return [k for k in range(1, min(n, 2000) + 1) if n % k == 0] if n else [1]
    cand = []
    for p_ in divs(lo):
        for q in divs(hi):
            for s in (1, -1):
                f = Fraction(s * p_, q)
                if f not in cand:
                    cand.append(f)
    cand.sort(key=lambda f: (abs(f.numerator) + abs(f.denominator), -f))
    return cand


class Fx:
    """factoriser with narration"""

    def __init__(self):
        self.steps = []

    def say(self, s):
        self.steps.append(s)

    def common(self, p):
        g = p.int_content()
        mono = p.monomial_content()
        return g, mono

    def split(self, p, depth=0):
        """return list of irreducible-ish factors (MP) whose product is p (up to a constant that is folded in by caller)"""
        if len(p.t) == 1 or p.total_deg() <= 1:
            return [p]
        nt = len(p.t)
        vs = p.vars()
        if nt == 2:
            r = self.two_terms(p)
            if r:
                return r
        if nt == 3:
            r = self.three_terms(p)
            if r:
                return r
        if nt == 4:
            r = self.grouping(p)
            if r:
                return r
        if len(vs) == 1 and p.deg_in(vs[0]) >= 3:
            r = self.root_search(p, vs[0])
            if r:
                return r
        if len(vs) == 1 and p.deg_in(vs[0]) == 2 and nt in (2, 3):
            pass
        return [p]

    def recurse(self, facs):
        out = []
        for f in facs:
            if len(f.t) == 1 or f.total_deg() <= 1:
                out.append(f)
                continue
            sub = self.split_primitive(f)
            out += sub
        return out

    def split_primitive(self, f):
        s, f2 = _norm(f)
        parts = self.split(f2)
        if len(parts) == 1:
            return [f]
        res = self.recurse(parts)
        return res

    # ---- two terms
    def two_terms(self, p):
        (m1, c1), (m2, c2) = p.terms_sorted()
        # difference of two squares
        if (c1 > 0) != (c2 > 0):
            pos_m, pos_c, neg_m, neg_c = (m1, c1, m2, c2) if c1 > 0 else (m2, c2, m1, c1)
            ra, rb = _isq(pos_c), _isq(-neg_c)
            ma, mb = _mono_pow_root(pos_m, 2), _mono_pow_root(neg_m, 2)
            if ra is not None and rb is not None and ma is not None and mb is not None:
                a = MP.mono(ra, ma)
                b = MP.mono(rb, mb)
                self.say(f"<b>Difference of two squares:</b> a<sup>2</sup> &minus; b<sup>2</sup> = (a + b)(a &minus; b). Write each term as a square: {p.text()} = ({a.text()})<sup>2</sup> &minus; ({b.text()})<sup>2</sup>, so a = {a.text()} and b = {b.text()}. "
                         f"Answer: ({(a + b).text()})({(a - b).text()}).")
                return [a + b, a - b]
        # sum / difference of cubes
        a3, b3 = _icube(c1), _icube(c2)
        ma, mb = _mono_pow_root(m1, 3), _mono_pow_root(m2, 3)
        if a3 is not None and b3 is not None and ma is not None and mb is not None:
            a = MP.mono(a3, ma)
            b = MP.mono(b3, mb)
            # p = a^3 + b^3 with b signed
            sumc = (a + b)
            quad = a * a - a * b + b * b
            name = "Sum" if b3 > 0 else "Difference"
            bb = MP.mono(abs(b3), mb)
            self.say(f"<b>{name} of two cubes:</b> a<sup>3</sup> + b<sup>3</sup> = (a + b)(a<sup>2</sup> &minus; ab + b<sup>2</sup>) and a<sup>3</sup> &minus; b<sup>3</sup> = (a &minus; b)(a<sup>2</sup> + ab + b<sup>2</sup>). "
                     f"Here {p.text()} = ({a.text()})<sup>3</sup> {'+' if b3 > 0 else MINUS} ({bb.text()})<sup>3</sup>, so a = {a.text()}, b = {bb.text()}. Answer: ({sumc.text()})({quad.text()}).")
            return [sumc, quad]
        # x^4 - 16 style handled by squares above (even powers); x^n - c with n multiple of 2 handled
        return None

    # ---- three terms
    def three_terms(self, p):
        T = p.terms_sorted()
        # perfect square trinomial: a^2 +- 2ab + b^2
        sq = []
        for m, c in T:
            r, mm = _isq(c), _mono_pow_root(m, 2)
            sq.append((r is not None and c > 0 and mm is not None, r, mm))
        for mid in range(3):
            others = [i for i in range(3) if i != mid]
            if all(sq[i][0] for i in others):
                a = MP.mono(sq[others[0]][1], sq[others[0]][2])
                b = MP.mono(sq[others[1]][1], sq[others[1]][2])
                cross = (a * b).scale(2)
                for sgn in (1, -1):
                    cand = MP({T[mid][0]: T[mid][1]})
                    if (cross.scale(sgn)) == cand:
                        word = "+" if sgn > 0 else MINUS
                        self.say(f"<b>Perfect square:</b> a<sup>2</sup> {word} 2ab + b<sup>2</sup> = (a {word} b)<sup>2</sup>. The first and last terms are squares: a = {a.text()}, b = {b.text()}. "
                                 f"Check the middle term: 2ab = 2 &times; {a.text()} &times; {b.text()} = {cross.text()}. "
                                 f"So {p.text()} = ({(a + b.scale(sgn)).text()})<sup>2</sup>.")
                        f = a + b.scale(sgn)
                        return [f, f]
        # quadratic trinomial a u^2 + b u v + c v^2
        vs = p.vars()
        if len(vs) == 1:
            x = vs[0]
            if p.deg_in(x) == 2 and all(dict(m).get(x, 0) <= 2 for m, _ in T):
                a, b, c = (p.coeff_in(x, i).const_value() for i in (2, 1, 0))
                if a and c:
                    return self.quad(a, b, c, x, None, p)
        if len(vs) == 2:
            x, y = vs
            if all(sum(e for _, e in m) == 2 for m, _ in T) and p.deg_in(x) == 2 and p.deg_in(y) == 2:
                a = p.coeff_in(x, 2).const_value()
                b = p.coeff_in(x, 1).coeff_in(y, 1).const_value()
                c = p.coeff_in(y, 2).const_value()
                return self.quad(a, b, c, x, y, p)
        return None

    def quad(self, a, b, c, x, y, p):
        ia, ib, ic = int(a), int(b), int(c)
        if (a, b, c) != (ia, ib, ic):
            return None
        ac = ia * ic
        found = None
        for m in range(-abs(ac) - abs(ib) - 1, abs(ac) + abs(ib) + 2):
            if m == 0 or ac % m:
                continue
            n = ac // m
            if m + n == ib:
                found = (m, n)
                break
        yv = y or "1"
        xs = lambda k: (x if k == 1 else f"{x}<sup>{k}</sup>")
        if not found:
            self.say(f"<b>Quadratic trinomial:</b> {p.text()}. Look for two whole numbers that multiply to a&times;c = {ia}&times;{ic} = {ac} and add to b = {ib}. There are <b>none</b>, so this does not factorise over whole numbers. "
                     f"(The discriminant b<sup>2</sup> &minus; 4ac = {ib * ib - 4 * ia * ic} is not a perfect square.)")
            return None
        m, n = found
        mm = f"{'+' if m > 0 else MINUS}{abs(m) if abs(m) != 1 else ''}"
        nn = f"{'+' if n > 0 else MINUS}{abs(n) if abs(n) != 1 else ''}"
        X = MP.var(x)
        Y = MP.var(y) if y else MP.const(1)
        # group: (a x^2 + m x y) + (n x y + c y^2)
        g1 = MP.const(ia) * X * X + MP.const(m) * X * Y
        g2 = MP.const(n) * X * Y + MP.const(ic) * Y * Y
        # factor each group
        c1 = math.gcd(abs(ia), abs(m))
        c2 = math.gcd(abs(n), abs(ic))
        # first group: common factor c1*x ; second: c2*y (sign chosen so brackets match)
        f1 = MP.const(c1) * X
        r1 = MP.const(ia // c1) * X + MP.const(m // c1) * Y
        s2 = 1
        f2 = MP.const(c2 * s2) * Y
        r2 = MP.const(n // (c2 * s2)) * X + MP.const(ic // (c2 * s2)) * Y
        if r2 != r1:
            s2 = -1
            f2 = MP.const(c2 * s2) * Y
            r2 = MP.const(n // (c2 * s2)) * X + MP.const(ic // (c2 * s2)) * Y
        if r1 != r2 and r1 != -r2:
            # try the other order of m,n
            m, n = n, m
            g1 = MP.const(ia) * X * X + MP.const(m) * X * Y
            g2 = MP.const(n) * X * Y + MP.const(ic) * Y * Y
            c1 = math.gcd(abs(ia), abs(m))
            c2 = math.gcd(abs(n), abs(ic))
            f1 = MP.const(c1) * X
            r1 = MP.const(ia // c1) * X + MP.const(m // c1) * Y
            f2 = MP.const(c2) * Y
            r2 = MP.const(n // c2) * X + MP.const(ic // c2) * Y
            if r2 != r1:
                f2 = MP.const(-c2) * Y
                r2 = MP.const(-(n // c2)) * X + MP.const(-(ic // c2)) * Y
        pair = (f1 + f2, r1)
        if r1 != r2:
            pair = (f1 + f2, r1)
        mm = f"{'+' if m > 0 else MINUS} {abs(m)}"
        nn = f"{'+' if n > 0 else MINUS} {abs(n)}"
        mid = f"{x}{y}" if y else x
        self.say(f"<b>Quadratic trinomial (split the middle term).</b> {p.text()} has a = {ia}, b = {ib}, c = {ic}.<br>"
                 f"&bull; Multiply a &times; c = {ia} &times; {ic} = <b>{ac}</b>.<br>"
                 f"&bull; Find two numbers that <b>multiply to {ac}</b> and <b>add to {ib}</b>: they are <b>{m}</b> and <b>{n}</b> (check: {m} &times; {n} = {m * n}, {m} + {n} = {m + n}).<br>"
                 f"&bull; Split the middle term: {MP.const(ia) * X * X} ".replace("<", "<") if False else
                 f"<b>{p.text()}</b><br>"
                 f"&bull; Split the middle term {ib}{mid} into {m}{mid} and {n}{mid}: {(g1 + g2).text()}<br>"
                 f"&bull; Group in pairs and take out the common factor of each pair: ({g1.text()}) + ({g2.text()}) = {(f1).text()}({r1.text()}) {'+' if f2.t and _lead(f2)[1] > 0 else '&minus;'} {(f2 if _lead(f2)[1] > 0 else -f2).text()}({(r2 if _lead(f2)[1] > 0 else -r2).text() if False else r2.text()})<br>"
                 f"&bull; The bracket ({r1.text()}) is common, so take it out: ({r1.text()})({(f1 + f2).text()}).")
        return [r1, f1 + f2]

    # ---- four terms
    def grouping(self, p):
        T = p.terms_sorted()
        idx = [(0, 1, 2, 3), (0, 2, 1, 3), (0, 3, 1, 2)]
        for i, j, k, l in idx:
            A = MP({T[i][0]: T[i][1]}) + MP({T[j][0]: T[j][1]})
            B = MP({T[k][0]: T[k][1]}) + MP({T[l][0]: T[l][1]})
            ga, ma = A.int_content(), A.monomial_content()
            gb, mb = B.int_content(), B.monomial_content()
            fa = MP.mono(ga, ma)
            fb = MP.mono(gb, mb)
            ra = A.div_mono(ga, ma)
            rb = B.div_mono(gb, mb)
            for sgn in (1, -1):
                if ra == rb.scale(sgn):
                    fb2 = fb.scale(sgn)
                    self.say(f"<b>Factorising by grouping (4 terms).</b> Put the terms in two pairs and take the common factor out of each pair:<br>"
                             f"({A.text()}) + ({B.text()}) = {br(fa)}({ra.text()}) {'+' if sgn > 0 else '+'} {br(fb2)}({ra.text()})<br>"
                             f"The bracket ({ra.text()}) appears in both parts, so take it out as a common factor: ({ra.text()})({(fa + fb2).text()}).")
                    return [ra, fa + fb2]
        return None

    # ---- search for rational roots (factor theorem)
    def root_search(self, p, x):
        trials = []
        P = to_coeffs(p, x)
        for r in _rational_roots(p, x):
            val = p.eval({x: r})
            trials.append((r, val))
            if val == 0:
                lines = ", ".join(f"p({q_(t)}) = {q_(v)}" for t, v in trials[-6:])
                f = MP.var(x).scale(r.denominator) - MP.const(r.numerator)
                q, rem = divmod_poly(P, to_coeffs(f, x))
                Q = from_coeffs(q, x)
                self.say(f"<b>Use the factor theorem.</b> Try small numbers that divide the last number ({q_(P[0])}) (and fractions with the first number): {lines}. "
                         f"<b>p({q_(r)}) = 0</b>, so <b>({f.text()}) is a factor</b>. Divide p({x}) by ({f.text()}) (long or synthetic division) to get the other factor: ({Q.text()}).")
                return [f, Q]
        return None


def _final_form(const, facs):
    """list of MP -> text with powers"""
    counts = []
    for f in facs:
        for i, (g, n) in enumerate(counts):
            if g == f or g == -f:
                counts[i] = (g, n + 1)
                break
        else:
            counts.append((f, 1))
    out = ""
    for g, n in counts:
        out += f"({g.text()})" + (f"<sup>{n}</sup>" if n > 1 else "")
    return out


def factorise_poly(P):
    """returns (steps, text, ok)"""
    fx = Fx()
    if P.is_zero():
        raise UErr("Zero cannot be factorised.")
    g = P.int_content()
    mono = P.monomial_content()
    # sign: take out -1 if leading term negative and (all terms negative or we have a common factor anyway)
    cf = MP.mono(g, mono)
    steps = fx.steps
    work = P
    const = Fraction(1)
    prefix = []
    if g != 1 or mono:
        rest = P.div_mono(g, mono)
        name = []
        if g != 1:
            name.append(f"the HCF of the numbers is {q_(g)}")
        if mono:
            name.append("the common letters are " + mono_text(tuple(sorted(mono.items()))))
        fx.say(f"<b>Step 1 &ndash; look for a common factor in every term:</b> {', '.join(name)}. Take it out and divide each term by it: {P.text()} = {HL(br(cf) if len(cf.t) > 1 else cf.text())}({rest.text()}).")
        prefix.append(cf)
        work = rest
    else:
        fx.say("<b>Step 1 &ndash; look for a common factor in every term:</b> there is none (apart from 1).")
    if len(work.t) > 1 and _lead(work)[1] < 0 and all(c < 0 for c in work.t.values()):
        fx.say(f"All terms are negative, so take out &minus;1 as well: {work.text()} = &minus;({(-work).text()}).")
        prefix.append(MP.const(-1))
        work = -work
    elif len(work.t) > 1 and _lead(work)[1] < 0 and len(work.t) == 3 and not prefix and False:
        pass
    if len(work.t) == 1 or work.total_deg() <= 1:
        facs = [work] if not (len(work.t) == 1 and work.is_const()) else []
    else:
        sub = fx.split(work)
        facs = fx.recurse(sub) if len(sub) > 1 else sub
        if len(sub) == 1 and len(work.t) > 1:
            fx.say(f"<b>{work.text()}</b> cannot be factorised any further using whole numbers.")
    out_facs = []
    for pf in prefix:
        out_facs.append(pf)
    # build final text
    consts = [f for f in out_facs if f.is_const()]
    c0 = Fraction(1)
    for c in consts:
        c0 *= c.const_value()
    pref_mono = [f for f in out_facs if not f.is_const()]
    txt = ""
    if pref_mono:
        pm = pref_mono[0]
        pm = pm.scale(c0) if True else pm
        txt += pm.text() if len(pm.t) == 1 else f"{pm.text()}"
    elif c0 != 1:
        txt += q_(c0) if c0 != -1 else MINUS
    # factors with signs normalised to positive leading terms
    norm = []
    sign = Fraction(1)
    for f in facs:
        if f.is_const():
            sign *= f.const_value()
            continue
        s, ff = _norm(f)
        sign *= s
        norm.append(ff)
    if sign < 0 and pref_mono:
        txt = MINUS + txt if not txt.startswith(MINUS) else txt[len(MINUS):]
    elif sign < 0:
        txt = (MINUS if not txt else (txt[len(MINUS):] if txt.startswith(MINUS) else MINUS + txt))
    elif sign != 1:
        txt = (txt if txt else "") + q_(sign)
    text = txt + _final_form(None, norm)
    # verify
    prod = MP.const(1)
    for f in prefix:
        prod = prod * f
    for f in facs:
        prod = prod * f
    ok = prod == P
    return steps, text or P.text(), ok, P


@wrap
def factorise(d):
    P = parse_poly(d.get("e"))
    if P.total_deg() > 10:
        raise UErr("That is too high a power for this tool.")
    steps, text, ok, _P = factorise_poly(P)
    head = [f"<b>Factorise</b> {HL(P.text())}. <b>Factorising</b> means writing an expression as a product (brackets multiplied together)."]
    steps = head + steps
    steps.append(f"<b>Answer:</b> {HL(text)}")
    chk = parse_poly(text.replace("&minus;", "-").replace("<sup>", "^").replace("</sup>", "")) if True else None
    if chk == P:
        steps.append("<b>Check by expanding:</b> multiplying the brackets back out gives " + P.text() + " &check;")
    elif not ok:
        steps.append("<i>(The check did not match exactly &mdash; please double-check the question.)</i>")
    return _ok(steps, f"<b>{P.text()} = {text}</b>")


# ===================================================================== change of subject
from log_core import pp as _pp


def _pi(node):
    if node[0] == "const":
        return ("var", "π")
    if node[0] in ("num", "var"):
        return node
    return (node[0],) + tuple(_pi(c) if isinstance(c, tuple) else c for c in node[1:])


def pn(node):
    return _pp(_pi(node))


def _has(node, v):
    if node[0] == "var":
        return node[1] == v
    if node[0] in ("num", "const"):
        return False
    return any(_has(c, v) for c in node[1:] if isinstance(c, tuple))


def _count(node, v):
    if node[0] == "var":
        return 1 if node[1] == v else 0
    if node[0] in ("num", "const"):
        return 0
    return sum(_count(c, v) for c in node[1:] if isinstance(c, tuple))


def _rat(node):
    """AST -> (num MP, den MP)"""
    k = node[0]
    one = MP.const(1)
    if k in ("num", "var", "const"):
        return from_node(node), one
    if k == "neg":
        n, d = _rat(node[1])
        return -n, d
    if k in ("add", "sub"):
        n1, d1 = _rat(node[1])
        n2, d2 = _rat(node[2])
        n2 = n2 if k == "add" else -n2
        return n1 * d2 + n2 * d1, d1 * d2
    if k == "mul":
        n1, d1 = _rat(node[1])
        n2, d2 = _rat(node[2])
        return n1 * n2, d1 * d2
    if k == "div":
        n1, d1 = _rat(node[1])
        n2, d2 = _rat(node[2])
        return n1 * d2, d1 * n2
    if k == "pow":
        e = from_node(node[2])
        if e.is_const() and e.const_value().denominator == 1 and 0 <= e.const_value() <= 6:
            n, d = _rat(node[1])
            return n ** int(e.const_value()), d ** int(e.const_value())
    raise LogErr("nope")


def _mulN(a, b):
    return ("mul", a, b)


@wrap
def subject(d):
    s = str(d.get("f") or "").strip()
    v = str(d.get("v") or "").strip()
    if s.count("=") != 1:
        raise UErr("Write the formula with one equals sign, for example  v = u + a*t")
    if not v or len(v) != 1 or not v.isalpha():
        raise UErr("Type the single letter you want as the new subject, for example t.")
    lt, rt = s.split("=")
    L = parse(lt.strip(), plain=True)
    R = parse(rt.strip(), plain=True)
    cl, cr = _count(L, v), _count(R, v)
    if cl + cr == 0:
        raise UErr(f"The letter {v} does not appear in the formula.")
    steps = [f"<b>Make {HL(v)} the subject</b> of {HL(pn(L) + ' = ' + pn(R))}. "
             f"This means: rearrange so that {v} stands alone on one side, like {v} = ... Whatever you do to one side, do the same to the other side."]
    if cl + cr == 1:
        if cr:
            L, R = R, L
            steps.append(f"Swap the sides so that {v} is on the left: {HL(pn(L) + ' = ' + pn(R))}")
        A, B = L, R
        guard_n = 0
        while not (A[0] == "var" and A[1] == v):
            guard_n += 1
            if guard_n > 12:
                raise UErr("This formula is too complicated for this tool.")
            k = A[0]
            if k == "add":
                x, y = A[1], A[2]
                if _has(x, v):
                    B, A = ("sub", B, y), x
                    why = f"{v} is joined by + {pn(y)}, so <b>subtract {pn(y)}</b> from both sides"
                else:
                    B, A = ("sub", B, x), y
                    why = f"subtract {pn(x)} from both sides"
            elif k == "sub":
                x, y = A[1], A[2]
                if _has(x, v):
                    B, A = ("add", B, y), x
                    why = f"{pn(y)} is being subtracted, so <b>add {pn(y)}</b> to both sides"
                else:
                    B, A = ("sub", x, B), y
                    why = f"the part with {v} is being subtracted from {pn(x)}. Move it across: add it to both sides, then subtract {pn(B[2])}... (equivalently {v}-part = {pn(x)} &minus; the other side)"
            elif k == "neg":
                B, A = ("neg", B), A[1]
                why = "multiply both sides by &minus;1 (change every sign)"
            elif k == "mul":
                x, y = A[1], A[2]
                keep, other = (x, y) if _has(x, v) else (y, x)
                B, A = ("div", B, other), keep
                why = f"{v} is multiplied by {pn(other)}, so <b>divide both sides by {pn(other)}</b>"
            elif k == "div":
                x, y = A[1], A[2]
                if _has(x, v):
                    B, A = ("mul", B, y), x
                    why = f"{v}-part is divided by {pn(y)}, so <b>multiply both sides by {pn(y)}</b>"
                else:
                    # x / y' = B  ->  y' = x / B
                    B, A = ("div", x, B), y
                    why = f"{v} is in the bottom. Multiply both sides by the bottom, then divide both sides by {pn(B[2])}: this swaps the top and the bottom"
            elif k == "pow":
                e = from_node(A[2])
                if not (e.is_const() and e.const_value().denominator == 1 and e.const_value() >= 2):
                    raise UErr("I can only handle whole-number powers like 2 or 3 on the letter.")
                n = int(e.const_value())
                if n == 2:
                    B, A = ("sqrt", B), A[1]
                    why = "take the <b>square root</b> of both sides (undo the square). Remember the answer can be + or &minus;; we keep the positive value when the letter is a length"
                else:
                    B, A = ("pow", B, ("div", ("num", Fraction(1)), ("num", Fraction(n)))), A[1]
                    why = f"take the <b>{n}th root</b> of both sides (undo the power {n})"
                    # nicer: cube root symbol
                    if n == 3:
                        B = ("cbrt", B[1]) if False else B
            elif k == "sqrt":
                B, A = ("pow", B, ("num", Fraction(2))), A[1]
                why = "<b>square both sides</b> to remove the square root"
            else:
                raise UErr("I cannot undo that operation yet.")
            steps.append(f"<b>{why[0].upper() + why[1:]}:</b> {HL(pn(A) + ' = ' + pn(B))}")
        ans = pn(B)
        steps.append(f"<b>Answer:</b> {HL(v + ' = ' + ans)}")
        return _ok(steps, f"<b>{v} = {ans}</b>")
    # the letter appears more than once -> clear fractions, collect, factorise
    try:
        nl, dl = _rat(L)
        nr, dr = _rat(R)
    except LogErr:
        raise UErr(f"{v} appears more than once and the formula has roots or other hard parts. Try to simplify it first.")
    G = nl * dr - nr * dl
    steps.append("<b>Step 1 &ndash; clear all fractions.</b> Multiply both sides by every bottom (denominator) so that no fractions remain.")
    if not (dl.is_const() and dr.is_const()):
        steps.append(f"Cross-multiply: ({nl.text()}) &times; ({dr.text()}) = ({nr.text()}) &times; ({dl.text()})")
    lhs, rhs = nl * dr, nr * dl
    steps.append(f"<b>Step 2 &ndash; expand the brackets:</b> {HL(lhs.text() + ' = ' + rhs.text())}")
    if G.deg_in(v) != 1:
        raise UErr(f"After clearing fractions, {v} appears with a power higher than 1, so it cannot be made the subject by simple factorising.")
    # collect: terms with v on the left, rest on right
    withv = [(m, c) for m, c in G.t.items() if dict(m).get(v, 0)]
    without = [(m, c) for m, c in G.t.items() if not dict(m).get(v, 0)]
    Wv, Wo = MP(dict(withv)), MP(dict(without))
    steps.append(f"<b>Step 3 &ndash; collect.</b> Move all terms containing {v} to one side and everything else to the other side (changing the sign of any term you move across): {HL(Wv.text() + ' = ' + (-Wo).text())}")
    cf = Wv.coeff_in(v, 1)
    steps.append(f"<b>Step 4 &ndash; factorise.</b> Take {v} out as a common factor: {HL(v + br(cf) + ' = ' + (-Wo).text())}")
    steps.append(f"<b>Step 5 &ndash; divide both sides</b> by {br(cf)} to leave {v} alone:")
    top = -Wo
    # reduce common integer factors / sign for neatness
    if cf.is_zero():
        raise UErr("That formula cannot be solved for this letter.")
    if _lead(cf)[1] < 0:
        top, cf = -top, -cf
    ans = (f"({top.text()})/({cf.text()})" if len(top.t) > 1 else f"{top.text()}/({cf.text()})") if len(cf.t) > 1 else f"{br(top)}/{cf.text()}"
    if cf.is_const() and cf.const_value() == 1:
        ans = top.text()
    steps.append(f"<b>Answer:</b> {HL(v + ' = ' + ans)}")
    return _ok(steps, f"<b>{v} = {ans}</b>")


# ===================================================================== roots of quadratics
def _quad_coeffs(txt, need_numeric=True):
    P = parse_poly(txt)
    if "x" not in P.vars() and P.vars():
        raise UErr("Write the quadratic using the letter x, for example  x^2 - 5x + 6")
    if P.deg_in("x") != 2:
        raise UErr("That is not a quadratic: the highest power of x must be 2. Example: 2x^2 - 7x + 3")
    a, b, c = (P.coeff_in("x", i) for i in (2, 1, 0))
    if need_numeric and not (a.is_const() and b.is_const() and c.is_const()):
        raise UErr("Use only numbers and x here (no other letters).")
    return P, a, b, c


def _sqrt_q(q):
    q = Fraction(q)
    if q < 0:
        return None
    r = _isq(q)
    return r


def _qs(x):
    return q_(x)


def _surd_text(q):
    q = Fraction(q)
    r = _isq(q)
    if r is not None:
        return q_(r)
    return f"&radic;{q_(q)}" if q.denominator == 1 else f"&radic;({q_(q)})"


EXPRS = {
    "a2b2": "α² + β²", "a3b3": "α³ + β³", "inv": "1/α + 1/β", "diffsq": "(α − β)²", "diff": "|α − β|",
    "ratio": "α/β + β/α", "ab_sum": "α²β + αβ²", "a4b4": "α⁴ + β⁴",
}


@wrap
def roots_sp(d):
    P, a, b, c = _quad_coeffs(d.get("q"))
    a, b, c = a.const_value(), b.const_value(), c.const_value()
    S, Pr = -b / a, c / a
    steps = [f"<b>Quadratic:</b> {HL(P.text() + ' = 0')}. Compare with ax<sup>2</sup> + bx + c = 0: a = {q_(a)}, b = {q_(b)}, c = {q_(c)}. Call the two roots <b>&alpha;</b> and <b>&beta;</b>.",
             f"<b>Sum of roots</b> = &minus;b/a = &minus;({q_(b)})/{q_(a)} = {HL(q_(S))}",
             f"<b>Product of roots</b> = c/a = {q_(c)}/{q_(a)} = {HL(q_(Pr))}",
             "<i>Why it works:</i> if the roots are &alpha; and &beta;, then (x &minus; &alpha;)(x &minus; &beta;) = x<sup>2</sup> &minus; (&alpha; + &beta;)x + &alpha;&beta;, and this is the same quadratic divided by a."]
    disc = b * b - 4 * a * c
    if disc >= 0:
        if _isq(disc) is not None:
            r1, r2 = (-b + _isq(disc)) / (2 * a), (-b - _isq(disc)) / (2 * a)
            steps.append(f"<i>(Check: the roots are {q_(r1)} and {q_(r2)}. Their sum is {q_(r1 + r2)} and product {q_(r1 * r2)} &check;)</i>")
        else:
            steps.append("<i>(The roots are irrational, but the sum and product are still whole numbers or fractions.)</i>")
    else:
        steps.append("<i>(The roots are not real numbers, but the sum and product formulas still hold.)</i>")
    ex = d.get("expr", "a2b2")
    res = f"sum = {q_(S)}, product = {q_(Pr)}"
    if ex in EXPRS and d.get("show", "yes") != "no":
        s2 = S * S - 2 * Pr
        steps.append(f"<b>Now find {EXPRS[ex]}.</b> We write it using only (&alpha;+&beta;) and &alpha;&beta;, because we know these.")
        if ex == "a2b2":
            val = s2
            steps.append(f"&alpha;<sup>2</sup> + &beta;<sup>2</sup> = (&alpha;+&beta;)<sup>2</sup> &minus; 2&alpha;&beta; = ({q_(S)})<sup>2</sup> &minus; 2({q_(Pr)}) = {q_(S * S)} &minus; ({q_(2 * Pr)}) = {HL(q_(val))}")
        elif ex == "a3b3":
            val = S ** 3 - 3 * Pr * S
            steps.append(f"&alpha;<sup>3</sup> + &beta;<sup>3</sup> = (&alpha;+&beta;)<sup>3</sup> &minus; 3&alpha;&beta;(&alpha;+&beta;) = ({q_(S)})<sup>3</sup> &minus; 3({q_(Pr)})({q_(S)}) = {q_(S ** 3)} &minus; ({q_(3 * Pr * S)}) = {HL(q_(val))}")
        elif ex == "inv":
            if Pr == 0:
                raise UErr("The product is 0, so one root is 0 and 1/root does not exist.")
            val = S / Pr
            steps.append(f"1/&alpha; + 1/&beta; = (&beta; + &alpha;)/(&alpha;&beta;) = ({q_(S)})/({q_(Pr)}) = {HL(q_(val))}")
        elif ex == "diffsq":
            val = S * S - 4 * Pr
            steps.append(f"(&alpha; &minus; &beta;)<sup>2</sup> = (&alpha;+&beta;)<sup>2</sup> &minus; 4&alpha;&beta; = ({q_(S)})<sup>2</sup> &minus; 4({q_(Pr)}) = {HL(q_(val))}")
        elif ex == "diff":
            v2 = S * S - 4 * Pr
            steps.append(f"(&alpha; &minus; &beta;)<sup>2</sup> = (&alpha;+&beta;)<sup>2</sup> &minus; 4&alpha;&beta; = {q_(S * S)} &minus; ({q_(4 * Pr)}) = {q_(v2)}")
            if v2 < 0:
                raise UErr("(α−β)² is negative, so the roots are not real and |α−β| is not a real number.")
            steps.append(f"Take the square root: |&alpha; &minus; &beta;| = {HL(_surd_text(v2))}" + ("" if _isq(v2) else f" &asymp; {float(v2) ** 0.5:.4g}"))
            res = f"|α − β| = {_surd_text(v2)}"
            return _ok(steps, "<b>" + res + "</b>")
        elif ex == "ratio":
            if Pr == 0:
                raise UErr("The product is 0, so one root is 0 and the fraction is undefined.")
            val = s2 / Pr
            steps.append(f"&alpha;/&beta; + &beta;/&alpha; = (&alpha;<sup>2</sup> + &beta;<sup>2</sup>)/(&alpha;&beta;). First &alpha;<sup>2</sup>+&beta;<sup>2</sup> = (&alpha;+&beta;)<sup>2</sup> &minus; 2&alpha;&beta; = {q_(s2)}. Then {q_(s2)}/({q_(Pr)}) = {HL(q_(val))}")
        elif ex == "ab_sum":
            val = Pr * S
            steps.append(f"&alpha;<sup>2</sup>&beta; + &alpha;&beta;<sup>2</sup> = &alpha;&beta;(&alpha; + &beta;) = ({q_(Pr)})({q_(S)}) = {HL(q_(val))}")
        else:
            val = s2 * s2 - 2 * Pr * Pr
            steps.append(f"&alpha;<sup>4</sup> + &beta;<sup>4</sup> = (&alpha;<sup>2</sup>+&beta;<sup>2</sup>)<sup>2</sup> &minus; 2(&alpha;&beta;)<sup>2</sup>. First &alpha;<sup>2</sup>+&beta;<sup>2</sup> = {q_(s2)}. Then ({q_(s2)})<sup>2</sup> &minus; 2({q_(Pr)})<sup>2</sup> = {HL(q_(val))}")
        res = f"{EXPRS[ex]} = {q_(val)}"
    return _ok(steps, "<b>" + res + "</b>")


def _solve_quad_in_k(A, B, C):
    """roots of A k^2 + B k + C = 0 as (text list, floats) or None"""
    A, B, C = Fraction(A), Fraction(B), Fraction(C)
    if A == 0:
        if B == 0:
            return []
        return [(-C / B, q_(-C / B))]
    D = B * B - 4 * A * C
    if D < 0:
        return []
    r = _isq(D)
    if r is not None:
        x1, x2 = (-B - r) / (2 * A), (-B + r) / (2 * A)
        out = sorted({x1, x2})
        return [(x, q_(x)) for x in out]
    f1, f2 = (-float(B) - float(D) ** .5) / (2 * float(A)), (-float(B) + float(D) ** .5) / (2 * float(A))
    return [(min(f1, f2), "%.4g" % min(f1, f2)), (max(f1, f2), "%.4g" % max(f1, f2))]


@wrap
def roots_nature(d):
    P, a, b, c = _quad_coeffs(d.get("q"), need_numeric=False)
    params = sorted(set(P.vars()) - {"x"})
    if len(params) > 1:
        raise UErr("Use at most one unknown letter besides x (for example k).")
    steps = [f"<b>Quadratic:</b> {HL(P.text() + ' = 0')}. Compare with ax<sup>2</sup> + bx + c = 0: a = {a.text()}, b = {b.text()}, c = {c.text()}.",
             "<b>The discriminant</b> is D = b<sup>2</sup> &minus; 4ac. It tells us the <b>nature</b> of the roots without solving:<br>"
             "&bull; D &gt; 0: two real, different (distinct) roots<br>&bull; D = 0: two real, equal roots (a repeated root; the graph touches the x-axis)<br>"
             "&bull; D &lt; 0: no real roots (the graph does not meet the x-axis)<br>&bull; D &ge; 0: real roots"]
    D = b * b - a * c.scale(4) if False else (b * b - (a * c).scale(4))
    steps.append(f"<b>Calculate D:</b> D = ({b.text()})<sup>2</sup> &minus; 4({br(a)})({br(c)}) = {HL(D.text())}")
    if not params:
        dv = D.const_value()
        word = "two real and different roots" if dv > 0 else ("two real and equal roots" if dv == 0 else "no real roots")
        steps.append(f"D = {q_(dv)} is {'greater than 0' if dv > 0 else ('equal to 0' if dv == 0 else 'less than 0')}, so the quadratic has <b>{word}</b>.")
        return _ok(steps, f"<b>D = {q_(dv)}: {word}</b>")
    k = params[0]
    if D.deg_in(k) > 2:
        raise UErr("D is too complicated in " + k + " for this tool.")
    cond = d.get("cond", "distinct")
    if a.deg_in(k) >= 1 and cond != "none_extra":
        steps.append(f"<i>Note: because the coefficient of x<sup>2</sup> contains {k}, remember {k} must not make a = 0, otherwise it is not a quadratic.</i>")
    A, B, C = (D.coeff_in(k, i).const_value() for i in (2, 1, 0))
    names = {"distinct": ("two real and different roots", ">"), "equal": ("equal roots", "="), "none": ("no real roots", "<"), "real": ("real roots", "≥")}
    nm, rel = names[cond]
    rel_h = {">": "&gt;", "=": "=", "<": "&lt;", "≥": "&ge;"}[rel]
    steps.append(f"<b>Condition for {nm}:</b> D {rel_h} 0, that is {HL(D.text() + ' ' + rel_h + ' 0')}")
    rts = _solve_quad_in_k(A, B, C)
    if rel == "=":
        if not rts:
            steps.append("This has no solution, so there is no value that gives equal roots.")
            return _ok(steps, "<b>No value of " + k + " works</b>")
        vals = " or ".join(f"{k} = {t}" for _, t in rts)
        steps.append(f"Solve {D.text()} = 0" + (" (a quadratic in " + k + ": factorise or use the formula)" if A != 0 else "") + f": {HL(vals)}")
        return _ok(steps, f"<b>{vals}</b>")
    if A == 0:
        if B == 0:
            ok = (C > 0 if rel in (">",) else (C < 0 if rel == "<" else C >= 0))
            return _ok(steps, "<b>" + ("True for every " + k if ok else "No value of " + k + " works") + "</b>")
        thr = -C / B
        up = (B > 0) == (rel in (">", "≥"))
        sym = ("≥" if rel == "≥" else (">" if rel == ">" else "<"))
        sgn = (">" if up else "<")
        if rel == "≥":
            sgn = "≥" if up else "≤"
        t = {">": "&gt;", "<": "&lt;", "≥": "&ge;", "≤": "&le;"}[sgn]
        steps.append(f"Solve the inequality (it is linear in {k}): {B and ''}{HL(k + ' ' + t + ' ' + q_(thr))}" + (" (dividing by a negative number reverses the inequality sign)" if B < 0 else ""))
        return _ok(steps, f"<b>{k} {t} {q_(thr)}</b>")
    # quadratic inequality in k
    if not rts:
        pos = A > 0
        ok = (pos if rel in (">", "≥") else not pos)
        steps.append(f"The expression {D.text()} has no real zeros, so it is always {'positive' if pos else 'negative'}.")
        return _ok(steps, "<b>" + ("True for every real " + k if ok else "No value of " + k + " works") + "</b>")
    xs = [t for _, t in rts]
    lo, hi = rts[0][1], rts[-1][1]
    steps.append(f"First find where D = 0: {HL(' or '.join(f'{k} = {t}' for t in xs))}. These split the number line into regions; the graph of D against {k} is a {'U-shape (opens upward)' if A > 0 else 'n-shape (opens downward)'}.")
    outside = (A > 0) == (rel in (">", "≥"))
    eq = "≥" if rel == "≥" else ">"
    eqs = "≤" if rel == "≥" else "<"
    h = {">": "&gt;", "<": "&lt;", "≥": "&ge;", "≤": "&le;"}
    if len(rts) == 1:
        ans = f"{k} is any real number" if outside else "no value"
    elif outside:
        ans = f"{k} {h[eqs]} {lo} or {k} {h[eq]} {hi}"
    else:
        ans = f"{lo} {h[eqs]} {k} {h[eqs]} {hi}"
    steps.append(f"Reading the shape: D {rel_h} 0 {'outside' if outside else 'between'} the two zeros. {HL(ans)}")
    return _ok(steps, f"<b>{ans}</b>")


@wrap
def roots_relation(d):
    P, a, b, c = _quad_coeffs(d.get("q"), need_numeric=False)
    params = sorted(set(P.vars()) - {"x"})
    if len(params) != 1:
        raise UErr("Put one unknown letter (like k) in the quadratic. Example: x^2 + 3x + k")
    k = params[0]
    rel = d.get("rel", "mult")
    m = Fraction(str(num(d.get("m", "2"), "multiplier")).replace(" ", "")) if rel == "mult" else None
    S, Pr = -b, c
    steps = [f"<b>Quadratic:</b> {HL(P.text() + ' = 0')} with roots &alpha; and &beta;. Sum &alpha;+&beta; = &minus;b/a and product &alpha;&beta; = c/a. Here a = {a.text()}, b = {b.text()}, c = {c.text()}."]
    if not a.is_const():
        raise UErr("Keep the coefficient of x² a plain number (put the letter in the x or the number term).")
    av = a.const_value()
    S = (-b).scale(1 / av)
    Pr = c.scale(1 / av)
    steps.append(f"Sum = {HL(S.text())}; Product = {HL(Pr.text())}")
    if rel == "mult":
        mm = m
        # beta = m alpha : S = (1+m) alpha ; P = m alpha^2 -> m S^2 = (1+m)^2 P
        eqn = (S * S).scale(mm) - Pr.scale((1 + mm) ** 2)
        steps.append(f"<b>One root is {q_(mm)} times the other:</b> let &beta; = {q_(mm)}&alpha;. Then &alpha;+&beta; = {q_(1 + mm)}&alpha; and &alpha;&beta; = {q_(mm)}&alpha;<sup>2</sup>.<br>"
                     f"From the first, &alpha; = (sum)/{q_(1 + mm)}. Put this in the second: product = {q_(mm)} &times; (sum)<sup>2</sup>/{q_(1 + mm)}<sup>2</sup>, so {q_(mm)}(sum)<sup>2</sup> = {q_((1 + mm) ** 2)}(product).")
        steps.append(f"Substitute: {q_(mm)}({S.text()})<sup>2</sup> = {q_((1 + mm) ** 2)}({Pr.text()}) &rArr; {HL(eqn.text() + ' = 0')}")
    elif rel == "recip":
        eqn = Pr - MP.const(1)
        steps.append(f"<b>One root is the reciprocal of the other:</b> &beta; = 1/&alpha;, so &alpha;&beta; = 1. Product = 1: {Pr.text()} = 1 &rArr; {HL(eqn.text() + ' = 0')}")
    elif rel == "neg":
        eqn = S
        steps.append(f"<b>The roots are opposites</b> (&beta; = &minus;&alpha;), so the sum is 0: {HL(S.text() + ' = 0')}")
    elif rel == "equal_roots":
        eqn = b * b - (a * c).scale(4)
        steps.append(f"<b>Equal roots:</b> D = 0: {HL(eqn.text() + ' = 0')}")
    else:
        dd = Fraction(str(num(d.get("m", "2"), "difference")))
        eqn = S * S - Pr.scale(4) - MP.const(dd * dd)
        steps.append(f"<b>The roots differ by {q_(dd)}:</b> (&alpha;&minus;&beta;)<sup>2</sup> = {q_(dd * dd)}, and (&alpha;&minus;&beta;)<sup>2</sup> = (&alpha;+&beta;)<sup>2</sup> &minus; 4&alpha;&beta;. So ({S.text()})<sup>2</sup> &minus; 4({Pr.text()}) = {q_(dd * dd)} &rArr; {HL(eqn.text() + ' = 0')}")
    if eqn.is_zero():
        raise UErr("That condition is always true for this quadratic.")
    if eqn.deg_in(k) == 0:
        raise UErr(f"The condition does not involve {k}, so it cannot be used to find {k}.")
    deg = eqn.deg_in(k)
    cs = [eqn.coeff_in(k, i).const_value() for i in range(deg + 1)]
    if deg > 2:
        raise UErr("The equation in " + k + " is too hard for this tool (power above 2).")
    if deg == 2:
        rr = _solve_quad_in_k(cs[2], cs[1], cs[0])
        sols = [t for _, t in rr]
        steps.append(f"Solve for {k}: " + (" or ".join(f"{k} = {t}" for t in sols) if sols else "there are no real values."))
    else:
        val = -cs[0] / cs[1]
        sols = [q_(val)]
        steps.append(f"Solve for {k}: {HL(k + ' = ' + q_(val))}")
    if rel in ("mult", "recip", "neg") and sols:
        steps.append("<i>Tip: put each value back into the quadratic and check that the roots really have the stated relationship.</i>")
    res = " or ".join(f"{k} = {t}" for t in sols) if sols else "no real value"
    return _ok(steps, f"<b>{res}</b>")


def _scaled_quad(S, Pr):
    """x^2 - Sx + P = 0 cleared of fractions -> (A,B,C) ints"""
    L = S.denominator * Pr.denominator // math.gcd(S.denominator, Pr.denominator)
    return L, -S * L, Pr * L


def _quad_text(A, B, C):
    return MP({(("x", 2),): Fraction(A), (("x", 1),): Fraction(B), (): Fraction(C)}).text() + " = 0"


@wrap
def roots_form(d):
    mode = d.get("mode", "two")
    steps = []
    if mode == "two":
        r1 = Fraction(str(num(d.get("r1"), "first root")))
        r2 = Fraction(str(num(d.get("r2"), "second root")))
        S, Pr = r1 + r2, r1 * r2
        steps.append(f"<b>Roots given:</b> {q_(r1)} and {q_(r2)}. A quadratic with roots &alpha; and &beta; is x<sup>2</sup> &minus; (&alpha;+&beta;)x + &alpha;&beta; = 0 (because (x&minus;&alpha;)(x&minus;&beta;) = 0).")
    elif mode == "sp":
        S = Fraction(str(num(d.get("s"), "sum")))
        Pr = Fraction(str(num(d.get("p"), "product")))
        steps.append(f"<b>Sum = {q_(S)}, product = {q_(Pr)}.</b> The quadratic is x<sup>2</sup> &minus; (sum)x + (product) = 0.")
    else:
        P, a, b, c = _quad_coeffs(d.get("q"))
        a, b, c = a.const_value(), b.const_value(), c.const_value()
        s0, p0 = -b / a, c / a
        t = d.get("how", "mul")
        m = Fraction(str(num(d.get("m", "2"), "number")))
        steps.append(f"<b>Given:</b> {HL(P.text() + ' = 0')} with roots &alpha; and &beta;. Sum = &minus;b/a = {q_(s0)}, product = c/a = {q_(p0)}.")
        if t == "mul":
            S, Pr = m * s0, m * m * p0
            steps.append(f"<b>New roots {q_(m)}&alpha; and {q_(m)}&beta;:</b> new sum = {q_(m)}(&alpha;+&beta;) = {q_(S)}; new product = {q_(m)}<sup>2</sup>&alpha;&beta; = {q_(Pr)}.")
        elif t == "add":
            S, Pr = s0 + 2 * m, p0 + m * s0 + m * m
            steps.append(f"<b>New roots &alpha;+{q_(m)} and &beta;+{q_(m)}:</b> new sum = (&alpha;+&beta;) + 2({q_(m)}) = {q_(S)}; new product = (&alpha;+{q_(m)})(&beta;+{q_(m)}) = &alpha;&beta; + {q_(m)}(&alpha;+&beta;) + {q_(m)}<sup>2</sup> = {q_(Pr)}.")
        elif t == "rec":
            if p0 == 0:
                raise UErr("One root is 0, so its reciprocal does not exist.")
            S, Pr = s0 / p0, 1 / p0
            steps.append(f"<b>New roots 1/&alpha; and 1/&beta;:</b> new sum = (&alpha;+&beta;)/(&alpha;&beta;) = {q_(S)}; new product = 1/(&alpha;&beta;) = {q_(Pr)}.")
        elif t == "sq":
            S, Pr = s0 * s0 - 2 * p0, p0 * p0
            steps.append(f"<b>New roots &alpha;<sup>2</sup> and &beta;<sup>2</sup>:</b> new sum = (&alpha;+&beta;)<sup>2</sup> &minus; 2&alpha;&beta; = {q_(S)}; new product = (&alpha;&beta;)<sup>2</sup> = {q_(Pr)}.")
        else:
            S, Pr = -s0, p0
            steps.append(f"<b>New roots &minus;&alpha; and &minus;&beta;:</b> new sum = &minus;(&alpha;+&beta;) = {q_(S)}; new product = &alpha;&beta; = {q_(Pr)}.")
    steps.append(f"<b>Write x<sup>2</sup> &minus; (sum)x + (product) = 0:</b> x<sup>2</sup> &minus; ({q_(S)})x + ({q_(Pr)}) = 0")
    A, B, C = _scaled_quad(S, Pr)
    ans = _quad_text(A, B, C)
    if A != 1:
        steps.append(f"Multiply through by {A} to remove fractions: {HL(ans)}")
    else:
        steps.append(f"Simplify: {HL(ans)}")
    return _ok(steps, f"<b>{ans}</b>")


# ===================================================================== means
def _nums(txt, lo=1, hi=12):
    parts = [p for p in str(txt or "").replace(";", ",").replace(" ", ",").split(",") if p.strip()]
    if not (lo <= len(parts) <= hi):
        raise UErr(f"Give between {lo} and {hi} numbers separated by commas, for example 4, 9, 16.")
    out = []
    for p in parts:
        try:
            out.append(Fraction(p.strip().replace("−", "-")))
        except (ValueError, ZeroDivisionError):
            raise UErr(f"I could not read '{p}' as a number.")
    return out


def _root_text(q, n):
    """nth root of positive Fraction as text with decimal fallback"""
    q = Fraction(q)
    neg = q < 0
    a = abs(q)
    num_, den_ = round(a.numerator ** (1 / n)), round(a.denominator ** (1 / n))
    for i in (num_ - 1, num_, num_ + 1):
        for j in (den_ - 1, den_, den_ + 1):
            if i > 0 and j > 0 and i ** n == a.numerator and j ** n == a.denominator:
                return (MINUS if neg else "") + q_(Fraction(i, j)), True, float(Fraction(i, j))
    val = float(a) ** (1 / n)
    return f"{n if n > 2 else ''}&radic;({q_(a)}) &asymp; {val:.4g}", False, val


@wrap
def means(d):
    mode = d.get("mode", "am")
    if mode == "am":
        xs = _nums(d.get("nums"), 2, 12)
        n, tot = len(xs), sum(xs)
        steps = [f"<b>Arithmetic mean (the ordinary average):</b> add all the numbers, then divide by how many there are.",
                 f"Sum = {' + '.join(q_(x) for x in xs)} = {q_(tot)}", f"Count = {n}", f"Mean = {q_(tot)} &divide; {n} = {HL(q_(tot / n))}"]
        return _ok(steps, f"<b>Arithmetic mean = {q_(tot / n)}</b>")
    if mode == "gm":
        xs = _nums(d.get("nums"), 2, 8)
        if any(x <= 0 for x in xs):
            raise UErr("The geometric mean needs positive numbers.")
        n = len(xs)
        pr = Fraction(1)
        for x in xs:
            pr *= x
        txt, exact, val = _root_text(pr, n)
        steps = [f"<b>Geometric mean:</b> multiply all the numbers, then take the {n}{'nd' if n == 2 else ('rd' if n == 3 else 'th')} root ({'square root' if n == 2 else 'root of order ' + str(n)}) of the product.",
                 f"Product = {' &times; '.join(q_(x) for x in xs)} = {q_(pr)}", f"Geometric mean = {n}-th root of {q_(pr)} = {HL(txt)}"]
        return _ok(steps, f"<b>Geometric mean = {txt}</b>")
    a = Fraction(str(num(d.get("a"), "first number")))
    b = Fraction(str(num(d.get("b"), "last number")))
    n = int(num(d.get("n", "3"), "how many means"))
    if not 1 <= n <= 10:
        raise UErr("Insert between 1 and 10 means.")
    if mode == "ins_am":
        diff = (b - a) / (n + 1)
        terms = [a + i * diff for i in range(n + 2)]
        steps = [f"<b>Insert {n} arithmetic mean{'s' if n > 1 else ''} between {q_(a)} and {q_(b)}.</b> This means a sequence (an A.P.) with first term {q_(a)} and last term {q_(b)}, with {n} terms in between. In total there are {n + 2} terms.",
                 f"The last term is the ({n + 2})th term: T<sub>{n + 2}</sub> = a + ({n + 2} &minus; 1)d = {q_(a)} + {n + 1}d = {q_(b)}",
                 f"So {n + 1}d = {q_(b)} &minus; {q_(a)} = {q_(b - a)}, and d = {q_(b - a)}/{n + 1} = {HL(q_(diff))}",
                 "Add d each time: " + ", ".join(q_(t) for t in terms)]
        return _ok(steps, "<b>" + ", ".join(q_(t) for t in terms[1:-1]) + "</b>")
    if a <= 0 and b <= 0 or a * b <= 0:
        raise UErr("Both numbers must have the same sign (and not be zero) to insert geometric means.")
    ratio_pow = b / a
    r_txt, exact, rv = _root_text(ratio_pow, n + 1)
    steps = [f"<b>Insert {n} geometric mean{'s' if n > 1 else ''} between {q_(a)} and {q_(b)}.</b> This means a sequence (a G.P.) with first term {q_(a)}, last term {q_(b)}, and {n} terms in between. In total {n + 2} terms.",
             f"The last term is the ({n + 2})th term: T<sub>{n + 2}</sub> = ar<sup>{n + 1}</sup> = {q_(a)} &times; r<sup>{n + 1}</sup> = {q_(b)}",
             f"So r<sup>{n + 1}</sup> = {q_(b)}/{q_(a)} = {q_(ratio_pow)}"]
    if not exact:
        steps.append(f"r = {r_txt} (this ratio is not a nice number, so the means are decimals).")
        terms = [float(a) * rv ** i for i in range(n + 2)]
        steps.append("Multiply by r each time: " + ", ".join("%.4g" % t for t in terms))
        return _ok(steps, "<b>" + ", ".join("%.4g" % t for t in terms[1:-1]) + "</b>")
    r = Fraction(r_txt.replace(MINUS, "-")) if "/" in r_txt or r_txt.replace(MINUS, "").isdigit() else None
    r = Fraction(rv).limit_denominator(10 ** 6)
    note = ""
    if (n + 1) % 2 == 0:
        note = f" (since {n + 1} is even, r could also be &minus;{q_(r)} when the two end numbers have the same sign; we use the positive ratio)"
    steps.append(f"Take the {n + 1}-th root: r = {HL(q_(r))}{note}")
    terms = [a * r ** i for i in range(n + 2)]
    steps.append("Multiply by r each time: " + ", ".join(q_(t) for t in terms))
    return _ok(steps, "<b>" + ", ".join(q_(t) for t in terms[1:-1]) + "</b>")


# ===================================================================== spec
SPEC = {
    "title": "Algebra Tools",
    "intro": "Polynomial long division, remainder and factor theorems, expanding and factorising, changing the subject of a formula, "
             "roots of quadratic equations and means. Every step is explained slowly. Write powers with ^ (for example <b>x^2</b>) and multiplication by just joining letters (<b>3x</b>, <b>ab</b>).",
    "tabs": [
        {"id": "ld", "label": "Long division", "title": "Divide one polynomial by another", "endpoint": "longdiv",
         "hint": "Type the dividend (top) and the divisor. Missing powers are handled for you. Choose <b>synthetic division</b> only when the divisor looks like <b>x &minus; a</b> (or ax &minus; b).",
         "fields": [field("p", "Polynomial to be divided", "2x^4 - 3x^3 + x - 5", wide=True, half=False),
                    field("dv", "Divisor", "x^2 + x - 1", wide=True, half=False),
                    select("method", "Method", [("long", "Long division"), ("synth", "Synthetic division (x &minus; a)")], wide=True)], "button": "Divide"},
        {"id": "th", "label": "Remainder & factor theorem", "title": "Remainder theorem, factor theorem and unknown coefficients", "endpoint": "theorem",
         "hint": "<b>Remainder theorem:</b> the remainder when p(x) is divided by (x &minus; a) is p(a). <b>Factor theorem:</b> (x &minus; a) is a factor exactly when p(a) = 0. "
                 "Fill one divisor to find the remainder. To find unknown letters (like k, or a and b), also give the remainder you are told (type 0 if it is a factor).",
         "fields": [field("p", "Polynomial p(x)", "x^3 + a x^2 + b x - 6", wide=True, half=False),
                    field("d1", "Divisor 1", "x - 1"), field("r1", "Remainder 1 (empty if unknown)", "0"),
                    field("d2", "Divisor 2 (optional)", "x + 2"), field("r2", "Remainder 2", "-12")], "button": "Use the theorem"},
        {"id": "fa", "label": "Factorise", "title": "Factorise an expression", "endpoint": "factorise",
         "hint": "Works for common factors, difference of two squares, perfect squares, quadratic trinomials (also with two letters like x^2+5xy+6y^2), grouping, sum/difference of cubes and cubic or higher polynomials.",
         "fields": [field("e", "Expression", "6x^2 + x - 2", wide=True, half=False)], "button": "Factorise"},
        {"id": "ex", "label": "Expand", "title": "Expand brackets", "endpoint": "expand",
         "fields": [field("e", "Expression with brackets", "(2x - 1)(3x + 4)", wide=True, half=False)], "button": "Expand"},
        {"id": "cs", "label": "Change of subject", "title": "Make a letter the subject of a formula", "endpoint": "subject",
         "hint": "Write the formula with one = sign. Use * for multiply if you like. You can use pi, sqrt( ), powers and fractions.",
         "fields": [field("f", "Formula", "T = 2*pi*sqrt(l/g)", wide=True, half=False),
                    field("v", "New subject (one letter)", "l", maxlength=1)], "button": "Make it the subject"},
        {"id": "rs", "label": "Sum & product of roots", "title": "Sum, product and symmetric expressions of the roots", "endpoint": "roots_sp",
         "fields": [field("q", "Quadratic (= 0)", "2x^2 - 5x + 1", wide=True, half=False),
                    select("expr", "Find", [(k, v) for k, v in EXPRS.items()], wide=True)], "button": "Find"},
        {"id": "rn", "label": "Nature of roots", "title": "Nature of roots using the discriminant", "endpoint": "roots_nature",
         "hint": "Put an unknown letter like <b>k</b> in the quadratic to find the values of k for a given condition. Without k you just get the nature of the roots.",
         "fields": [field("q", "Quadratic (= 0)", "x^2 + k x + 9", wide=True, half=False),
                    select("cond", "Condition", [("distinct", "two real different roots"), ("equal", "equal roots"), ("none", "no real roots"), ("real", "real roots")], wide=True)], "button": "Find"},
        {"id": "rr", "label": "Relation between roots", "title": "Find k when the roots are related", "endpoint": "roots_relation",
         "fields": [field("q", "Quadratic with k (= 0)", "x^2 - 6x + k", wide=True, half=False),
                    select("rel", "The roots are such that", [("mult", "one root is m times the other"), ("recip", "one is the reciprocal of the other"), ("neg", "they are opposites (sum 0)"), ("diff", "they differ by m"), ("equal_roots", "they are equal")], wide=True),
                    field("m", "m", "2", show_if={"rel": ["mult", "diff"]})], "button": "Find k"},
        {"id": "rf", "label": "Form an equation", "title": "Form a quadratic equation from roots", "endpoint": "roots_form",
         "fields": [select("mode", "I know", [("two", "the two roots"), ("sp", "the sum and product"), ("tr", "a quadratic and want one with new roots")], wide=True),
                    field("r1", "Root 1", "2/3", show_if={"mode": "two"}), field("r2", "Root 2", "-4", show_if={"mode": "two"}),
                    field("s", "Sum of roots", "5", show_if={"mode": "sp"}), field("p", "Product of roots", "6", show_if={"mode": "sp"}),
                    field("q", "Original quadratic", "x^2 - 3x + 1", wide=True, half=False, show_if={"mode": "tr"}),
                    select("how", "New roots are", [("mul", "m&alpha; and m&beta;"), ("add", "&alpha;+m and &beta;+m"), ("rec", "1/&alpha; and 1/&beta;"), ("sq", "&alpha;&sup2; and &beta;&sup2;"), ("neg", "&minus;&alpha; and &minus;&beta;")], show_if={"mode": "tr"}),
                    field("m", "m", "2", show_if={"mode": "tr"})], "button": "Form the equation"},
        {"id": "mn", "label": "Means", "title": "Arithmetic and geometric means", "endpoint": "means",
         "fields": [select("mode", "What do you want", [("am", "Arithmetic mean of numbers"), ("gm", "Geometric mean of numbers"), ("ins_am", "Insert arithmetic means (A.P.)"), ("ins_gm", "Insert geometric means (G.P.)")], wide=True),
                    field("nums", "Numbers (commas)", "4, 9", wide=True, half=False, show_if={"mode": ["am", "gm"]}),
                    field("a", "First number", "2", show_if={"mode": ["ins_am", "ins_gm"]}), field("b", "Last number", "17", show_if={"mode": ["ins_am", "ins_gm"]}),
                    field("n", "How many means to insert", "4", show_if={"mode": ["ins_am", "ins_gm"]})], "button": "Calculate"},
    ],
}

topics.register("algebra2", SPEC, {"longdiv": longdiv, "theorem": theorem, "factorise": factorise, "expand": expand, "subject": subject,
                                    "roots_sp": roots_sp, "roots_nature": roots_nature, "roots_relation": roots_relation,
                                    "roots_form": roots_form, "means": means})
