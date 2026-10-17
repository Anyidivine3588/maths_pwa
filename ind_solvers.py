"""Indices (laws of indices) engine: pure Python, exact arithmetic, step-by-step working."""
import math
from fractions import Fraction

from log_core import (LogErr, parse, pp, fmtq, sig, variables, ev_exact, vec_of, vec_to_q,
                      contains_var_in_exponent, real_roots, to_poly, P1, MINUS)
from log_solvers import _ok, _fail, guard, HL
import log_solvers

LETTER_E = "e"


# ------------------------------------------------------------------ linear forms (indices)
def lin_const(q):
    return {"": Fraction(q)} if q != 0 else {}


def lin_add(a, b, k=1):
    out = dict(a)
    for key, v in b.items():
        out[key] = out.get(key, Fraction(0)) + k * v
        if out[key] == 0:
            del out[key]
    return out


def lin_scale(a, k):
    k = Fraction(k)
    return {key: v * k for key, v in a.items() if v * k != 0}


def lin_mul(a, b):
    if set(a) <= {""}:
        return lin_scale(b, a.get("", Fraction(0)))
    if set(b) <= {""}:
        return lin_scale(a, b.get("", Fraction(0)))
    raise LogErr("An index that is a letter times another letter is too complicated for this tool.")


def lin_is_const(a):
    return set(a) <= {""}


def lin_text(a, plain_zero="0"):
    if not a:
        return plain_zero
    parts = []
    keys = sorted(k for k in a if k) + ([""] if "" in a else [])
    for key in keys:
        v = a[key]
        mag = abs(v)
        if key:
            body = ("" if mag == 1 else fmtq(mag)) + key
        else:
            body = fmtq(mag)
        if not parts:
            parts.append((MINUS if v < 0 else "") + body)
        else:
            parts.append(("&minus; " if v < 0 else "+ ") + body)
    return " ".join(parts)


def lin_of(node):
    k = node[0]
    if k == "num":
        return lin_const(node[1])
    if k == "var":
        return {node[1]: Fraction(1)}
    if k == "const":
        return {LETTER_E: Fraction(1)}
    if k == "neg":
        return lin_scale(lin_of(node[1]), -1)
    if k == "add":
        return lin_add(lin_of(node[1]), lin_of(node[2]))
    if k == "sub":
        return lin_add(lin_of(node[1]), lin_of(node[2]), -1)
    if k == "mul":
        return lin_mul(lin_of(node[1]), lin_of(node[2]))
    if k == "div":
        d = lin_of(node[2])
        if not lin_is_const(d) or not d:
            raise LogErr("An index can only be divided by a plain number, like x/2.")
        return lin_scale(lin_of(node[1]), 1 / d[""])
    raise LogErr("I could not understand that index. Use numbers, fractions or letters like 3, &minus;2, 1/2, m + n.")


def ix(a):
    """index as sup text (brackets when it has several terms)"""
    t = lin_text(a)
    return t


def qtext(q):
    q = Fraction(q)
    if q.denominator == 1:
        return fmtq(q)
    return f"{MINUS if q < 0 else ''}{abs(q.numerator)}/{q.denominator}"


def idx(a):
    """index text for <sup>: fractions as p/q"""
    if lin_is_const(a):
        return qtext(a.get("", Fraction(0)))
    return lin_text(a)


# ------------------------------------------------------------------ radical monomials
def render_rat_rad(coef, rad):
    """coef Fraction, rad {prime: fractional exponent in (0,1)} -> text"""
    groups = {}
    for p, e in rad.items():
        d = Fraction(e).denominator
        groups.setdefault(d, 1)
    # build each root: d-th root of prod p^(e*d)
    rtxt = ""
    for d in sorted(groups):
        n = 1
        for p, e in rad.items():
            if Fraction(e).denominator == d:
                n *= p ** int(Fraction(e) * d)
        sym = "&radic;" if d == 2 else ("&#8731;" if d == 3 else ("&#8732;" if d == 4 else f"<sup>{d}</sup>&radic;"))
        rtxt += sym + (str(n) if n < 1000 else f"({n})")
    if not rad:
        return qtext(coef)
    c = Fraction(coef)
    sign = MINUS if c < 0 else ""
    c = abs(c)
    if c == 1:
        return sign + rtxt
    if c.denominator == 1:
        return f"{sign}{c.numerator}{rtxt}"
    return f"{sign}{c.numerator if c.numerator != 1 else ''}{rtxt}/{c.denominator}"


def split_vec(vec):
    """prime vector with Fraction exponents -> (rational Fraction, radical dict)"""
    q = Fraction(1)
    rad = {}
    for p, e in vec.items():
        e = Fraction(e)
        fl = math.floor(e)
        r = e - fl
        if abs(fl) > 300:
            raise LogErr("That number is far too large for this tool.")
        q *= Fraction(p) ** fl
        if r:
            rad[p] = r
    return q, rad


def vec_float(vec):
    return math.exp(sum(float(e) * math.log(p) for p, e in vec.items())) if vec else 1.0


def bigtext(q):
    q = Fraction(q)
    if q.denominator == 1 and len(str(abs(q.numerator))) <= 18:
        return fmtq(q)
    if q.denominator != 1 and len(str(q.numerator)) <= 18 and len(str(q.denominator)) <= 18:
        return qtext(q)
    return f"{sig(float(q), 4)} (about)"


# ------------------------------------------------------------------ explain a numeric power
def explain_power(a, e):
    """a: positive Fraction, e: Fraction. Returns (steps, vec) with vec = prime vector of the value."""
    a, e = Fraction(a), Fraction(e)
    steps = []
    base = qtext(a) if a.denominator == 1 else f"({qtext(a)})"
    head = f"{base}<sup>{qtext(e)}</sup>"
    if a == 1:
        return [f"{head} = 1 (1 to any power is 1)"], {}
    if e == 0:
        return [f"{head} = <b>1</b> (any number except 0, raised to the power 0, is 1)"], {}
    va = vec_of(a)
    if va is None:
        raise LogErr("That number is too large for me to break into prime factors.")
    if e < 0:
        pos = -e
        flip = Fraction(1) / a
        if a.denominator == 1:
            steps.append(f"<b>Negative index means &ldquo;flip&rdquo;:</b> {head} = 1/{base}<sup>{qtext(pos)}</sup>")
        else:
            steps.append(f"<b>Negative index means &ldquo;flip the fraction&rdquo;:</b> {head} = {qtext(flip) if flip.denominator == 1 else '(' + qtext(flip) + ')'}<sup>{qtext(pos)}</sup>")
        sub, vec = explain_power(flip if a.denominator != 1 else a, pos)
        if a.denominator == 1:
            steps += sub
            steps.append(f"So {head} = 1/{bigtext(vec_to_q(vec)) if vec_to_q(vec) is not None else '...'}" if vec_to_q(vec) is not None else f"So {head} = 1/(...)")
            return steps, {p: -x for p, x in vec.items()}
        steps += sub
        return steps, vec
    if e.denominator == 1:
        n = int(e)
        val = a ** n
        if n == 1:
            return [f"{head} = {qtext(a)}"], va
        if n <= 6 and a.denominator == 1 and a < 1000:
            rep = " &times; ".join([qtext(a)] * n)
            steps.append(f"{head} means {qtext(a)} is multiplied by itself {n} times: {rep} = <b>{bigtext(val)}</b>")
        elif a.denominator != 1 and n <= 6:
            rep = " &times; ".join([f"{qtext(a)}"] * n)
            steps.append(f"{head} = {rep} = <b>{bigtext(val)}</b> (top and bottom are each multiplied: ({a.numerator})<sup>{n}</sup>/({a.denominator})<sup>{n}</sup>)")
        else:
            steps.append(f"{head} = <b>{bigtext(val)}</b>")
        return steps, vec_scale_(va, e)
    p_, q_ = e.numerator, e.denominator
    rootname = {2: "square root", 3: "cube root", 4: "fourth root", 5: "fifth root"}.get(q_, f"{q_}th root")
    steps.append(f"<b>A fractional index is a root and a power:</b> the bottom number ({q_}) is the root, the top number ({p_}) is the power. {head} = ({rootname} of {qtext(a)})<sup>{p_}</sup>")
    vr = vec_scale_(va, Fraction(1, q_))
    rq, rad = split_vec(vr)
    if not rad:
        fac = " &times; ".join(f"{p}" for p, k in sorted(va.items()) for _ in range(abs(int(k)))) if all(Fraction(k).denominator == 1 for k in va.values()) else ""
        if a.denominator == 1:
            steps.append(f"The {rootname} of {a.numerator}: {a.numerator} = {fac if fac else a.numerator}, so the {rootname} is <b>{qtext(rq)}</b> (because {qtext(rq)}<sup>{q_}</sup> = {qtext(a)}).")
        else:
            steps.append(f"The {rootname} of {qtext(a)} is <b>{qtext(rq)}</b> (because {qtext(rq)}<sup>{q_}</sup> = {qtext(a)}).")
        val = rq ** p_
        steps.append(f"Now raise to the power {p_}: {qtext(rq)}<sup>{p_}</sup> = <b>{bigtext(val)}</b>")
        return steps, vec_scale_(va, e)
    full = vec_scale_(va, e)
    rq2, rad2 = split_vec(full)
    txt = render_rat_rad(rq2, rad2)
    steps.append(f"The {rootname} of {qtext(a)} is not a whole number, so the answer stays as a root: {head} = <b>{txt}</b> &asymp; {sig(vec_float(full), 4)}")
    return steps, full


def vec_scale_(v, k):
    return {p: Fraction(x) * Fraction(k) for p, x in v.items() if Fraction(x) * Fraction(k) != 0}


def ipp(node, prec=0):
    k = node[0]
    if k == "pow":
        b = node[1]
        bs = ipp(b, 4) if b[0] in ("var", "const", "sqrt") or (b[0] == "num" and b[1] >= 0 and b[1].denominator == 1) else f"({ipp(b)})"
        try:
            e = idx(lin_of(node[2]))
        except LogErr:
            e = ipp(node[2])
        return f"{bs}<sup>{e}</sup>"
    if k == "neg":
        s_ = MINUS + ipp(node[1], 3)
        return f"({s_})" if prec > 1 else s_
    if k in ("add", "sub"):
        s_ = f"{ipp(node[1], 1)} {'+' if k == 'add' else MINUS} {ipp(node[2], 2 if k == 'sub' else 1)}"
        return f"({s_})" if prec > 1 else s_
    if k == "div":
        s_ = f"{ipp(node[1], 2)}/{ipp(node[2], 3)}"
        return f"({s_})" if prec > 2 else s_
    if k == "mul":
        a, b = node[1], node[2]
        simple = lambda n: n[0] in ("var", "const") or (n[0] == "pow" and n[1][0] in ("var", "const"))
        pa, pb = ipp(a, 2), ipp(b, 2)
        if (a[0] == "num" and simple(b)) or (a[0] in ("var", "const") and simple(b)) or (simple(a) and b[0] in ("add", "sub")) or (a[0] in ("add", "sub") and b[0] in ("add", "sub")):
            s_ = pa + (ipp(b, 3) if b[0] in ("add", "sub") else pb)
        else:
            s_ = f"{pa} &times; {pb}"
        return f"({s_})" if prec > 2 else s_
    if k == "sqrt":
        a = node[1]
        return f"&radic;{ipp(a)}" if a[0] in ("num", "var") else f"&radic;({ipp(a)})"
    return pp(node, prec)


# ------------------------------------------------------------------ flattening an expression
class Flat:
    def __init__(self):
        self.facs = []        # (kind, key, lin exponent): kind 'p' prime int, 'v' letter
        self.sign = 1
        self.flags = set()
        self.zero = False

    def add(self, kind, key, ex):
        self.facs.append((kind, key, ex))


def flatten(node, mult, F):
    k = node[0]
    if k == "num":
        q = node[1]
        if q == 0:
            F.zero = True
            F.flags.add("zero")
            F.add("zero", 0, mult)
            return
        if q < 0:
            _neg(F, mult)
            q = -q
        vec = vec_of(q)
        if vec is None:
            raise LogErr("A number in your expression is too large for this tool.")
        if q.denominator != 1:
            F.flags.add("fraction")
        for p, e in vec.items():
            F.add("p", p, lin_scale(mult, e))
        return
    if k == "var":
        F.add("v", node[1], mult)
        return
    if k == "const":
        F.add("v", LETTER_E, mult)
        return
    if k == "neg":
        _neg(F, mult)
        flatten(node[1], mult, F)
        return
    if k == "mul":
        flatten(node[1], mult, F)
        flatten(node[2], mult, F)
        return
    if k == "div":
        F.flags.add("division")
        flatten(node[1], mult, F)
        flatten(node[2], lin_scale(mult, -1), F)
        return
    if k == "sqrt":
        F.flags.add("root")
        flatten(node[1], lin_mul(mult, lin_const(Fraction(1, 2))), F)
        return
    if k == "pow":
        e = lin_of(node[2])
        if node[1][0] not in ("num", "var", "const"):
            F.flags.add("bracket")
        if node[1][0] == "pow":
            F.flags.add("powpow")
        if node[1][0] in ("mul", "div"):
            F.flags.add("prodpow")
        if e and any(c < 0 for c in e.values()) and lin_is_const(e):
            F.flags.add("negative")
        if not lin_is_const(e):
            F.flags.add("letters")
        flatten(node[1], lin_mul(mult, e), F)
        return
    if k in ("add", "sub"):
        if variables(node):
            raise LogErr("There is a plus or minus sign inside this expression, with letters. I can multiply, divide and raise to powers, but I cannot combine a sum like (x + 1) with other terms. Simplify each bracket separately or expand it first.")
        v = ev_exact(node)
        if v is None:
            raise LogErr("I could not work out the numbers in that bracket exactly.")
        flatten(("num", v), mult, F)
        return
    raise LogErr("I can only simplify products, quotients and powers here (no logs).")


def _neg(F, mult):
    if lin_is_const(mult):
        m = mult.get("", Fraction(0))
        if m.denominator == 1:
            if int(m) % 2:
                F.sign = -F.sign
            return
        if m.denominator % 2 == 1:
            if m.numerator % 2:
                F.sign = -F.sign
            return
        raise LogErr("A negative number cannot be raised to a power like 1/2 (even root): it has no real answer.")
    raise LogErr("A negative base with a letter in the index is too complicated for this tool.")


def prime_rewrite(node):
    """replace composite numbers/fractions by prime powers so the working is visible"""
    k = node[0]
    if k == "num":
        q = node[1]
        if q.denominator != 1 or q < 4:
            if q.denominator == 1:
                return node
            a = prime_rewrite(("num", Fraction(q.numerator)))
            b = prime_rewrite(("num", Fraction(q.denominator)))
            return ("div", a, b)
        vec = vec_of(q)
        if vec is None or (len(vec) == 1 and list(vec.values())[0] == 1):
            return node
        parts = [("pow", ("num", Fraction(p)), ("num", Fraction(e))) if e != 1 else ("num", Fraction(p)) for p, e in sorted(vec.items())]
        out = parts[0]
        for x in parts[1:]:
            out = ("mul", out, x)
        return out
    if k in ("neg", "sqrt"):
        return (k, prime_rewrite(node[1]))
    if k in ("add", "sub", "mul", "div"):
        return (k, prime_rewrite(node[1]), prime_rewrite(node[2]))
    if k == "pow":
        return ("pow", prime_rewrite(node[1]), node[2])
    return node


def _num_leaves(node, out):
    k = node[0]
    if k == "num":
        out.append(node[1])
    elif k in ("neg", "sqrt"):
        _num_leaves(node[1], out)
    elif k in ("add", "sub", "mul", "div"):
        _num_leaves(node[1], out)
        _num_leaves(node[2], out)
    elif k == "pow":
        _num_leaves(node[1], out)
    return out


def _fac_text(kind, key, ex, brackets=True):
    b = str(key) if kind in ("p", "v") else "0"
    if lin_is_const(ex) and ex.get("", 1) == 1 and len(ex) == 1:
        return b
    return f"{b}<sup>{idx(ex)}</sup>"


@guard
def evaluate(expr_str):
    expr_str = (expr_str or "").strip()
    if not expr_str:
        raise LogErr("Please type an expression, for example <b>2^3 * 2^-5</b> or <b>(x^2)^3 / x^4</b>.")
    if "=" in expr_str:
        raise LogErr("That has an = sign, so it is an equation. Use the <b>Solve for x</b> tab for it.")
    node = parse(expr_str)
    # top-level sum / difference of separate terms
    terms = _split_terms(node)
    if len(terms) > 1:
        return _evaluate_sum(node, terms)
    steps, text, _m = _evaluate_product(node, show_header=True)
    return _ok(steps, text)


def _split_terms(node, sign=1, out=None):
    out = [] if out is None else out
    if node[0] == "add":
        _split_terms(node[1], sign, out)
        _split_terms(node[2], sign, out)
    elif node[0] == "sub":
        _split_terms(node[1], sign, out)
        _split_terms(node[2], -sign, out)
    else:
        out.append((sign, node))
    return out


def _evaluate_sum(node, terms):
    steps = [f"<b>Expression:</b> {ipp(node)}", "This has several terms joined by + or &minus;. Simplify each term on its own first, then combine terms that are alike."]
    monos = []
    for i, (sg, t) in enumerate(terms, 1):
        sub_steps, text, mono = _evaluate_product(t, show_header=False, quiet=True)
        steps.append(f"<b>Term {i}:</b> {ipp(t)} = {HL(text)}")
        monos.append((sg, mono))
    # combine
    groups = {}
    order = []
    letmap = {}
    for sg, (coef, rad, lets) in monos:
        lk = tuple(sorted((x, tuple(sorted(e.items()))) for x, e in lets.items()))
        key = (tuple(sorted(rad.items())), lk)
        letmap[key] = lets
        if key not in groups:
            groups[key] = Fraction(0)
            order.append(key)
        groups[key] += sg * coef
    pieces = []
    for key in order:
        c = groups[key]
        if c == 0:
            continue
        rad = dict(key[0])
        lets = letmap[key]
        pieces.append(mono_text(c, rad, lets))
    if not pieces:
        return _ok(steps + ["The terms cancel each other out."], "0")
    out = pieces[0]
    for p in pieces[1:]:
        out += (" &minus; " + p[len(MINUS):]) if p.startswith(MINUS) else " + " + p
    if len(pieces) < len(terms):
        steps.append("Add the terms that are alike (same letters and same roots) and keep the rest.")
    steps.append(f"<b>Answer:</b> {HL(out)}")
    vals = _numeric_value(groups, order)
    return _ok(steps, out)


def _numeric_value(groups, order):
    return None


def mono_text(coef, rad, lets):
    """rational coef, radical dict, letters {x: lin exponent (const)} -> text with positive indices"""
    num, den = [], []
    for x, e in sorted(lets.items()):
        if e == 0:
            continue
        if lin_is_const(e):
            ev = e.get("", Fraction(0))
            (num if ev > 0 else den).append(_fac_text("v", x, lin_const(abs(ev))))
        else:
            num.append(_fac_text("v", x, e))
    c = Fraction(coef)
    base = render_rat_rad(abs(c), rad) if (rad or abs(c) != 1) else ""
    if not num and not den:
        return (MINUS if c < 0 else "") + (base or "1")
    top = (base if base else "") + "".join(num)
    if not top:
        top = "1"
    s = top if not den else f"{top}/" + ("(" + "".join(den) + ")" if len(den) > 1 else "".join(den))
    return (MINUS if c < 0 else "") + s


def _evaluate_product(node, show_header=True, quiet=False):
    steps = []
    if show_header:
        steps.append(f"<b>Expression:</b> {ipp(node)}")
    if node[0] == "pow" and not quiet:
        a_ = ev_exact(node[1]) if not variables(node[1]) else None
        try:
            e_ = lin_of(node[2])
        except LogErr:
            e_ = None
        if a_ is not None and a_ > 0 and e_ is not None and lin_is_const(e_):
            sub, vec = explain_power(a_, e_.get("", Fraction(0)))
            q_, r_ = split_vec(vec)
            txt = render_rat_rad(q_, r_)
            steps += sub
            steps.append(f"<b>Answer:</b> {HL(txt)}" + (f" &asymp; {sig(vec_float(vec), 4)}" if r_ else ""))
            return steps, txt + (f" &asymp; {sig(vec_float(vec), 4)}" if r_ else ""), (q_, r_, {})
    leaves = _num_leaves(node, [])
    comp = [q for q in leaves if q.denominator != 1 or (q > 3 and not _is_prime_(int(q)))]
    if comp and not quiet:
        re_ = prime_rewrite(node)
        if ipp(re_) != ipp(node):
            steps.append("<b>Write every number as a power of a prime</b> (so that equal bases can be spotted):<br>" + HL(ipp(re_)))
    F = Flat()
    flatten(node, lin_const(1), F)
    if F.zero:
        # zero base
        ex = [e for k_, key, e in F.facs if k_ == "zero"]
        for e in ex:
            if not lin_is_const(e) or e.get("", 0) <= 0:
                raise LogErr("0 raised to a power of zero or less is not defined (0<sup>0</sup> is undefined and 0<sup>&minus;n</sup> would mean dividing by 0).")
        steps.append("0 raised to any positive power is 0.")
        return steps, "0", (Fraction(0), {}, {})
    if not quiet:
        if "division" in F.flags:
            steps.append("<b>Division:</b> a &divide; b<sup>n</sup> = a &times; b<sup>&minus;n</sup>, so dividing by a power means we <i>subtract</i> its index.")
        if F.flags & {"bracket", "powpow", "prodpow"}:
            steps.append("<b>Brackets with a power outside:</b> (a<sup>m</sup>)<sup>n</sup> = a<sup>mn</sup> (multiply the indices) and (ab)<sup>n</sup> = a<sup>n</sup>b<sup>n</sup> (the power goes to <i>every</i> factor inside).")
        if "root" in F.flags:
            steps.append("<b>Square root:</b> &radic;a = a<sup>1/2</sup>, so we halve the index.")
        if F.flags & {"division", "bracket", "powpow", "prodpow", "root"}:
            flat = " &times; ".join(_fac_text(k_, key, e) for k_, key, e in F.facs if k_ != "zero")
            steps.append(f"After removing brackets and division, every factor is a base with an index: {HL(flat)}" + (f" &nbsp;(with an overall minus sign)" if F.sign < 0 else ""))
    # group
    groups = {}
    order = []
    for k_, key, e in F.facs:
        gk = (k_, key)
        if gk not in groups:
            groups[gk] = []
            order.append(gk)
        groups[gk].append(e)
    totals = {}
    lines = []
    for gk in order:
        es = groups[gk]
        tot = {}
        for e in es:
            tot = lin_add(tot, e)
        totals[gk] = tot
        if len(es) > 1:
            parts = " + ".join(f"({idx(e)})" if (len(lin_text(e)) > 1 and ("&minus;" in lin_text(e) or " " in lin_text(e))) else idx(e) for e in es)
            lines.append(f"{gk[1]}: {parts} = {idx(tot)}")
    if lines and not quiet:
        steps.append("<b>Same base, so add the indices</b> (a<sup>m</sup> &times; a<sup>n</sup> = a<sup>m+n</sup>):<br>" + "<br>".join(lines))
    # build monomial
    prime_vec = {}
    lets = {}
    for (k_, key), tot in totals.items():
        if k_ == "p":
            if not lin_is_const(tot):
                lets[str(key)] = tot
            elif tot:
                prime_vec[key] = tot.get("", Fraction(0))
        elif k_ == "v":
            if tot:
                lets[key] = tot
    if F.sign < 0 and any(not lin_is_const(t) for t in lets.values()):
        pass
    coef, rad = split_vec(prime_vec)
    coef = coef * F.sign
    # explain numeric powers
    numeric_primes = sorted(prime_vec)
    if not quiet and numeric_primes:
        bits = []
        for p in numeric_primes:
            e = prime_vec[p]
            if e != 1:
                sub, _v = explain_power(Fraction(p), e)
                bits += sub
        simple = len(numeric_primes) == 1 and prime_vec[numeric_primes[0]] > 0 and prime_vec[numeric_primes[0]].denominator == 1 and len(bits) == 1 and not lets
        if bits:
            steps.append("<b>Work out each power:</b><br>" + "<br>".join(bits))
        if len(numeric_primes) > 1:
            pieces = " &times; ".join(f"{p}<sup>{qtext(prime_vec[p])}</sup>" for p in numeric_primes)
            steps.append(f"Multiply the parts together: {pieces} = {HL(render_rat_rad(coef, rad) if not lets else render_rat_rad(abs(coef), rad))}")
    if not quiet and lets:
        negs = [x for x, e in lets.items() if lin_is_const(e) and e.get("", 0) < 0]
        if negs:
            steps.append("<b>Make the indices positive</b> (a<sup>&minus;n</sup> = 1/a<sup>n</sup>): " + ", ".join(
                f"{x}<sup>{idx(lets[x])}</sup> = 1/{x}<sup>{idx(lin_scale(lets[x], -1))}</sup>" for x in negs))
        zeros = [k_ for k_ in totals if totals[k_] == {} and k_[0] == "v"]
        if zeros:
            steps.append("A letter with index 0 equals 1 (a<sup>0</sup> = 1), so it disappears: " + ", ".join(f"{k_[1]}<sup>0</sup> = 1" for k_ in zeros))
    text = mono_text(coef, rad, lets)
    if not quiet:
        approx = ""
        if rad:
            approx = f" &asymp; {sig(float(coef) * vec_float({p: e for p, e in rad.items()}), 4)}"
        elif not lets and coef.denominator != 1:
            q = fmtq(coef)
            approx = f" = {q}" if "/" not in q else (f" = {sig(float(coef), 4)}" if abs(coef.numerator) < 10 ** 9 else "")
        steps.append(f"<b>Answer:</b> {HL(text)}{approx}")
    return steps, text + (f" &asymp; {sig(float(coef) * vec_float(rad), 4)}" if (rad and not lets and not quiet) else ""), (coef, rad, lets)


def _is_prime_(n):
    if n < 2:
        return False
    for d in range(2, int(n ** 0.5) + 1):
        if n % d == 0:
            return False
    return True


# ------------------------------------------------------------------ the three laws tabs
_LAWS = {
    "multiply": ("a<sup>m</sup> &times; a<sup>n</sup> = a<sup>m + n</sup>", "same base: <b>add</b> the indices", lambda m, n: lin_add(m, n), "+"),
    "divide": ("a<sup>m</sup> &divide; a<sup>n</sup> = a<sup>m &minus; n</sup>", "same base: <b>subtract</b> the indices", lambda m, n: lin_add(m, n, -1), "&minus;"),
    "power": ("(a<sup>m</sup>)<sup>n</sup> = a<sup>m &times; n</sup>", "a power of a power: <b>multiply</b> the indices", lambda m, n: lin_mul(m, n), "&times;"),
}


def _read_index(text, label):
    text = (text if text is not None else "")
    text = str(text).strip()
    if not text:
        raise LogErr(f"Please type {label}.")
    return lin_of(parse(text))


def _wrap(a):
    t = idx(a)
    return f"({t})" if (not lin_is_const(a) and len(a) > 1) or (lin_is_const(a) and a.get('', 0) < 0) else t


@guard
def law(kind, base_txt, m_txt, n_txt):
    base_txt = str(base_txt or "").strip()
    if not base_txt:
        raise LogErr("Please type the base (a), for example <b>2</b>, <b>3/4</b> or <b>x</b>.")
    base = parse(base_txt)
    m = _read_index(m_txt, "the first index (m)")
    n = _read_index(n_txt, "the second index (n)")
    if kind == "divide" and ev_exact(base) == 0:
        raise LogErr("You cannot divide by 0, so the base cannot be 0 in a division.")
    stmt, why, op, sym = _LAWS[kind]
    b = pp(base, 4)
    bb = b if base[0] in ("num", "var") and not (base[0] == "num" and (base[1] < 0 or base[1].denominator != 1)) else f"({pp(base)})"
    if kind == "multiply":
        lhs = f"{bb}<sup>{idx(m)}</sup> &times; {bb}<sup>{idx(n)}</sup>"
    elif kind == "divide":
        lhs = f"{bb}<sup>{idx(m)}</sup> &divide; {bb}<sup>{idx(n)}</sup>"
    else:
        lhs = f"({bb}<sup>{idx(m)}</sup>)<sup>{idx(n)}</sup>"
    steps = [f"<b>The law:</b> {stmt} &nbsp;&mdash; {why}.",
             f"<b>Your numbers:</b> a = {pp(base)}, m = {idx(m)}, n = {idx(n)}.",
             f"<b>Write it out:</b> {lhs}"]
    if kind == "power" and not (lin_is_const(m) or lin_is_const(n)):
        raise LogErr("In (a<sup>m</sup>)<sup>n</sup>, at least one of m and n must be a plain number.")
    tot = op(m, n)
    work = f"{_wrap(m)} {sym} {_wrap(n)}"
    steps.append(f"<b>Apply the law</b> ({why.split(':')[0]}): the new index is {work} = <b>{idx(tot)}</b>")
    ptxt = bb if tot == lin_const(1) else f"{bb}<sup>{idx(tot)}</sup>"
    if kind in ("multiply", "divide") and lin_is_const(m) and lin_is_const(n):
        mv, nv = m.get("", Fraction(0)), n.get("", Fraction(0))
        if mv.denominator == 1 and nv.denominator == 1 and 0 < mv <= 6 and 0 < nv <= 6:
            ones = lambda c: " &times; ".join([b] * int(c))
            if kind == "multiply":
                steps.append(f"<b>Why this works:</b> ({ones(mv)}) &times; ({ones(nv)}) &mdash; altogether {b} appears {int(mv + nv)} times, so it is {b}<sup>{int(mv + nv)}</sup>.")
            elif mv > nv:
                steps.append(f"<b>Why this works:</b> {b}<sup>{int(mv)}</sup> &divide; {b}<sup>{int(nv)}</sup> = ({ones(mv)}) &divide; ({ones(nv)}). {int(nv)} of the {b}'s on the bottom cancel {int(nv)} on the top, leaving {int(mv - nv)}.")
    steps.append(f"So {lhs} = {HL(ptxt)}")
    result = ptxt
    if base[0] == "num" or ev_exact(base) is not None:
        a = ev_exact(base)
        if lin_is_const(tot):
            e = tot.get("", Fraction(0))
            if a is None:
                raise LogErr("I could not work out that base.")
            if a == 0:
                if e > 0:
                    steps.append("0 raised to a positive power is 0.")
                    return _ok(steps, f"{ptxt} = 0")
                raise LogErr("0 raised to a power of zero or less is not defined.")
            if a < 0 and e.denominator != 1:
                raise LogErr("A negative base with a fractional index has no real answer.")
            neg = a < 0 and e.denominator == 1 and int(e) % 2 == 1
            aa = abs(a)
            sub, vec = explain_power(aa, e)
            steps.append("<b>Now work out the value:</b>")
            steps += sub
            qv, radv = split_vec(vec)
            res = render_rat_rad(-qv if neg else qv, radv)
            if a < 0 and e.denominator == 1:
                steps.append(f"(The base is negative: an <b>{'odd' if neg else 'even'}</b> power gives a {'negative' if neg else 'positive'} answer.)")
            result = f"{ptxt} = {res}" + (f" &asymp; {sig(vec_float(vec) * (-1 if neg else 1), 4)}" if radv else "")
    return _ok(steps, result)


def law_multiply(base, m, n):
    return law("multiply", base, m, n)


def law_divide(base, m, n):
    return law("divide", base, m, n)


def law_power(base, m, n):
    return law("power", base, m, n)


# ------------------------------------------------------------------ solving (letter in the base or in the power)
def _lin_poly(node, v):
    """node in v -> (m, n) if it is m*v + n (m != 0), else None"""
    try:
        P = to_poly(node, v)
    except LogErr:
        return None
    if P.deg() != 1:
        return None
    return P.c[1], (P.c[0] if P.c else Fraction(0))


def _extract(node, v):
    """c * L**p with L linear in v -> (c, L, p) or None"""
    k = node[0]
    if v not in variables(node):
        return None
    if _lin_poly(node, v) is not None:
        return Fraction(1), node, Fraction(1)
    if k == "pow":
        e = ev_exact(node[2]) if not variables(node[2]) else None
        if e is None:
            return None
        inner = _extract(node[1], v)
        if inner is None:
            return None
        c, L, p = inner
        if c != 1:
            return None
        return Fraction(1), L, p * e
    if k == "sqrt":
        inner = _extract(node[1], v)
        if inner is None or inner[0] != 1:
            return None
        return Fraction(1), inner[1], inner[2] / 2
    if k == "neg":
        r = _extract(node[1], v)
        return None if r is None else (-r[0], r[1], r[2])
    if k == "mul":
        a, b = node[1], node[2]
        ca = ev_exact(a) if not variables(a) else None
        cb = ev_exact(b) if not variables(b) else None
        if ca is not None:
            r = _extract(b, v)
            return None if r is None else (ca * r[0], r[1], r[2])
        if cb is not None:
            r = _extract(a, v)
            return None if r is None else (cb * r[0], r[1], r[2])
        return None
    if k == "div":
        a, b = node[1], node[2]
        if not variables(b):
            d = ev_exact(b)
            r = _extract(a, v)
            return None if (r is None or not d) else (r[0] / d, r[1], r[2])
        if not variables(a):
            c = ev_exact(a)
            r = _extract(b, v)
            if r is None or r[0] != 1 or c is None:
                return None
            return c, r[1], -r[2]
    return None


def _root_text(S, num, den):
    """exact value of |S|**(num/den), S>0 Fraction -> (text, float, exactFractionOrNone)"""
    vec = vec_of(S)
    if vec is None:
        return sig(float(S) ** (num / den), 5), float(S) ** (num / den), None
    v2 = {p: Fraction(e) * Fraction(num, den) for p, e in vec.items()}
    q, rad = split_vec(v2)
    return render_rat_rad(q, rad), vec_float(v2), (q if not rad else None)


@guard
def solve_equation(expr_str):
    expr_str = (expr_str or "").strip()
    if not expr_str:
        raise LogErr("Please type an equation, for example <b>2^(x+1) = 16</b> or <b>x^(3/2) = 8</b>.")
    if expr_str.count("=") != 1:
        raise LogErr("Please give one equation with exactly one = sign, e.g. <b>2^(x+1) = 16</b>.")
    ls, rs = expr_str.split("=")
    if not ls.strip() or not rs.strip():
        raise LogErr("One side of the = sign is empty. Write something on both sides.")
    lhs, rhs = parse(ls), parse(rs)
    letters = variables(lhs) | variables(rhs)
    if not letters:
        raise LogErr("There is no unknown letter in this equation. Write the unknown as <b>x</b>.")
    if len(letters) > 1:
        raise LogErr("I can only solve for one unknown letter at a time (like x). I found: " + ", ".join(sorted(letters)) + ".")
    v = next(iter(letters))
    for a_, b_txt in ((lhs, rs), (rhs, ls)):
        if a_ == ("var", v) and not variables(parse(b_txt)):
            r_ = evaluate(b_txt)
            if r_["ok"]:
                val = r_["result"].split(" &asymp; ")[0]
                return _ok([f"<b>The unknown is already alone</b>, so we only need to work out the right-hand side:"] + r_["steps"], f"{v} = {val}")
    if contains_var_in_exponent(lhs, v) or contains_var_in_exponent(rhs, v):
        return log_solvers.solve_equation(expr_str)
    return _solve_base(lhs, rhs, v)


def _solve_base(lhs, rhs, v):
    if v in variables(rhs) and v in variables(lhs):
        raise LogErr("The unknown is on both sides. Please move everything with the unknown to one side first, e.g. write x^2 = 2x as x^2 - 2x = 0 (that is a quadratic: use the Algebra section).")
    if v in variables(rhs):
        lhs, rhs = rhs, lhs
    R = ev_exact(rhs)
    if R is None:
        raise LogErr("The other side should be a plain number (a fraction is fine).")
    ex = _extract(lhs, v)
    if ex is None:
        raise LogErr("I can solve equations like <b>x^2 = 16</b>, <b>x^(3/2) = 8</b>, <b>x^(-2) = 1/9</b>, <b>(x+1)^2 = 25</b> or <b>2x^3 = 54</b>: one power of the unknown (or of a bracket with the unknown) equal to a number.")
    c, L, p = ex
    steps = [f"<b>Equation:</b> {ipp(lhs)} = {qtext(R)}",
             "<b>An index equation with the unknown in the base:</b> the plan is to get the power on its own, then undo the power by raising both sides to the <i>reciprocal</i> power."]
    if p == 1 and _lin_poly(lhs, v) is not None:
        raise LogErr("That is just a linear equation (no power). Use the Algebra section.")
    S = R
    if c != 1:
        S = R / c
        steps.append(f"<b>Divide both sides by {qtext(c)}</b> to get the power alone: {ipp(L) if p == 1 else (ipp(L) + '<sup>' + qtext(p) + '</sup>')} = {qtext(R)} &divide; {qtext(c)} = <b>{qtext(S)}</b>")
    Lb = ipp(L)
    Lb_ = Lb if L[0] in ("var",) else f"({Lb})"
    if S == 0:
        if p < 0:
            return _ok(steps + ["A negative power can never equal 0 (1/anything is not 0), so there is <b>no solution</b>."], "No solution")
        steps.append(f"Only 0 raised to a positive power gives 0, so {Lb} = 0.")
        mn = _lin_poly(L, v)
        xv = -mn[1] / mn[0]
        return _ok(steps, f"{v} = {qtext(xv)}")
    if p < 0:
        steps.append(f"<b>Negative index means flip:</b> {Lb_}<sup>{qtext(p)}</sup> = 1/{Lb_}<sup>{qtext(-p)}</sup>. So 1/{Lb_}<sup>{qtext(-p)}</sup> = {qtext(S)}, and flipping both sides: {Lb_}<sup>{qtext(-p)}</sup> = {qtext(1 / S)}")
        S = 1 / S
        p = -p
    a, b = p.numerator, p.denominator
    pw = f"<sup>{qtext(p)}</sup>" if p != 1 else ""
    mn = _lin_poly(L, v)
    m, n = mn
    sols = []
    note = ""
    recip = Fraction(b, a)
    if a % 2 == 0:
        if S < 0:
            return _ok(steps + [f"{Lb_}{pw} equals a number raised to an <b>even</b> power (top number {a} is even), which can never be negative. So {Lb_}{pw} = {qtext(S)} has <b>no real solution</b>."], "No solution")
        signs = [1, -1]
        note = f"The top number ({a}) is even, so the sign of {Lb} is lost when the power is taken (for example (+4)<sup>2</sup> and (&minus;4)<sup>2</sup> are both 16). That is why there are <b>two</b> answers, + and &minus;."
    elif b % 2 == 0:
        if S < 0:
            return _ok(steps + [f"{Lb_}{pw} involves an <b>even root</b> (bottom number {b}), which is never negative. So {qtext(S)} is impossible: <b>no solution</b>."], "No solution")
        signs = [1]
        note = f"The bottom number ({b}) is even (a square root-type power), so {Lb} must be positive: only the positive answer is allowed."
    else:
        signs = [1 if S > 0 else -1]
    rtxt, rfl, rex = _root_text(abs(S), b, a)
    if p == 1:
        steps.append(f"The power is already gone: {Lb} = {qtext(S)}.")
        if a % 2 == 1 and b == 1:
            pass
    else:
        e_txt = qtext(recip)
        steps.append(f"<b>Raise both sides to the power {e_txt}</b> (the reciprocal of {qtext(p)}), because ({Lb_}<sup>{qtext(p)}</sup>)<sup>{e_txt}</sup> = {Lb_}<sup>{qtext(p)} &times; {e_txt}</sup> = {Lb_}<sup>1</sup>:")
        steps.append(f"{Lb} = {'&plusmn;' if len(signs) == 2 else ('' if signs[0] > 0 else MINUS)}{qtext(abs(S)) if recip.denominator != 1 or True else ''}<sup>{e_txt}</sup>")
        sub, vecv = explain_power(abs(S), recip)
        steps += sub
    if note:
        steps.append(note)
    out = []
    for sg in signs:
        Lv = sg * rfl
        Lq = sg * rex if rex is not None else None
        xv = (Lv - float(n)) / float(m)
        if Lq is not None:
            xq = (Lq - n) / m
            if (m != 1 or n != 0):
                steps.append(f"{Lb} = {qtext(Lq)} &nbsp;&rarr;&nbsp; solve the little equation: {v} = ({qtext(Lq)} {MINUS if n > 0 else '+'} {qtext(abs(n)) if n != 0 else '0'}) &divide; {qtext(m)} = <b>{qtext(xq)}</b>" if n != 0 else f"{Lb} = {qtext(Lq)} &nbsp;&rarr;&nbsp; {v} = {qtext(Lq)} &divide; {qtext(m)} = <b>{qtext(xq)}</b>")
            out.append((f"{v} = {qtext(xq)}", float(xq)))
        else:
            if m == 1 and n == 0:
                out.append((f"{v} = {MINUS if sg < 0 else ''}{rtxt} &asymp; {sig(xv, 4)}", xv))
            else:
                out.append((f"{v} &asymp; {sig(xv, 4)}", xv))
                steps.append(f"{Lb} = {MINUS if sg < 0 else ''}{rtxt} &asymp; {sig(Lv, 5)} &nbsp;&rarr;&nbsp; {v} &asymp; {sig(xv, 4)}")
    # check
    chk = []
    for txt, xv in out:
        try:
            lv = ev_float_(lhs, v, xv)
            if abs(lv - float(R)) < 1e-6 * max(1, abs(float(R))):
                chk.append(f"{v} = {_cl(xv)}: {_cl(lv)} &check;")
        except Exception:
            pass
    if chk:
        steps.append("<b>Check by putting back into the original equation:</b> " + "; ".join(chk))
    return _ok(steps, ", &nbsp; ".join(t for t, _ in out) if len(out) > 1 else out[0][0])


def _cl(x):
    return fmtq(Fraction(round(x))) if abs(x - round(x)) < 1e-9 else sig(x, 5)


def ev_float_(node, v, xv):
    from log_core import ev_float
    return ev_float(node, {v: xv})
