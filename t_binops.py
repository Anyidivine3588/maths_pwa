"""Binary operations (exact, symbolic) and modular arithmetic."""
import math
import re
from fractions import Fraction
import numpy as np
import topics
import poly as P
from tcommon import field, select, guard, UErr, num, pos, fm, fr, FR, esc, table, _ok, _fail, TIMES, MINUS

HL = lambda s: f"<span class='hl'>{s}</span>"
OPSYM = "@"


# ------------------------------------------------------------- polynomial helpers --

def _pt(p, v=None):
    return P.poly_str(p) if not p.is_zero() else "0"


def _rename(p, mp):
    out = P.Poly()
    for k, c in p.t.items():
        key = P._key([(mp.get(v, v), e) for v, e in k])
        out = out + P.Poly({key: c})
    return out


def _sub(p, mp):
    """substitute variables by Polys (mp: name->Poly)"""
    out = P.Poly()
    for k, c in p.t.items():
        term = P.Poly.const(c)
        for v, e in k:
            term = term * (mp[v] ** e)
        out = out + term
    return out


def parse_op(text):
    s = (text or "").strip()
    if not s or len(s) > 150:
        raise UErr("Type the rule, for example: a * b = a + b - ab")
    s = P.normalise(s)
    m = re.match(r"^\s*([A-Za-z])\s*[*@#∘⊕⊗★○□∗o]\s*([A-Za-z])\s*=\s*(.+)$", s)
    lv = None
    if m:
        lv = (m.group(1), m.group(2))
        body = m.group(3)
    else:
        body = s.split("=")[-1] if "=" in s else s
    try:
        p = P.parse_poly(body)
    except P.ParseError as e:
        raise UErr(str(e))
    vs = p.vars()
    if lv is None:
        if len(vs) == 0:
            raise UErr("The rule must use letters for the two numbers, like a + b - ab.")
        if len(vs) > 2:
            raise UErr("Use only two letters in the rule.")
        lv = (vs[0], vs[1] if len(vs) > 1 else ("b" if vs[0] != "b" else "a"))
    if lv[0] == lv[1]:
        raise UErr("Use two different letters on the left, like a * b.")
    if not set(vs) <= set(lv):
        raise UErr(f"The rule uses a letter that is not in {lv[0]} * {lv[1]}.")
    f = _rename(p, {lv[0]: "a", lv[1]: "b"})
    if f.total_degree() > 6:
        raise UErr("That rule is too high a degree for this solver.")
    return f, lv


def apply(f, A, B):
    return _sub(f, {"a": A, "b": B})


def fstr(f, L="a", R="b"):
    return _pt(_rename(f, {"a": L, "b": R}))


def _roots(p, v):
    """real roots of univariate Poly"""
    co = p.to_uni(v)
    while co and co[-1] == 0:
        co.pop()
    deg = len(co) - 1
    if deg <= 0:
        return None if all(c == 0 for c in co) else []
    if deg == 1:
        return [-co[0] / co[1]]
    r = np.roots([float(c) for c in reversed(co)])
    out = []
    for z in r:
        if abs(z.imag) < 1e-8:
            val = float(z.real)
            fv = Fraction(val).limit_denominator(2000)
            ok = abs(float(fv) - val) < 1e-9 and sum(c * fv ** i for i, c in enumerate(co)) == 0
            out.append(fv if ok else round(val, 6))
    res = []
    for x in out:
        if not any(abs(float(x) - float(y)) < 1e-7 for y in res):
            res.append(x)
    return sorted(res, key=float)


def _show(x):
    return fr(x) if isinstance(x, Fraction) else fm(Fraction(x).limit_denominator(10 ** 6), 4)


# -------------------------------------------------------------- evaluate / solve --

def _parse_expr(text, f):
    """expression with @ operation, + - * / ^ and brackets; unknown x; returns Poly in x"""
    s = P.normalise(text).replace("∘", "@").replace("⊕", "@").replace("⊗", "@").replace("★", "@").replace("#", "@")
    s = s.replace("*", "*")
    toks = re.findall(r"\d+\.\d+|\d+|[A-Za-z]|[@+\-*/^()]", s)
    if "".join(toks) != re.sub(r"\s+", "", s):
        raise UErr("I could not read that. Use numbers, x, brackets and @ for the operation, for example (2 @ x) @ 3.")
    i = [0]

    def peek():
        return toks[i[0]] if i[0] < len(toks) else None

    def eat():
        t = toks[i[0]]
        i[0] += 1
        return t

    def e_at():
        a = e_add()
        while peek() == "@":
            eat()
            b = e_add()
            a = apply(f, a, b)
        return a

    def e_add():
        a = e_mul()
        while peek() in ("+", "-"):
            op = eat()
            b = e_mul()
            a = a + b if op == "+" else a - b
        return a

    def e_mul():
        a = e_un()
        while peek() in ("*", "/") or (peek() is not None and (peek()[0].isdigit() or peek().isalpha() or peek() == "(")):
            if peek() in ("*", "/"):
                op = eat()
                b = e_un()
                if op == "/":
                    if not b.is_const() or b.is_zero():
                        raise UErr("Division is only allowed by a number here.")
                    a = a.scale(1 / b.const_value())
                else:
                    a = a * b
            else:
                a = a * e_un()
        return a

    def e_un():
        if peek() == "-":
            eat()
            return -e_un()
        return e_pow()

    def e_pow():
        b = e_atom()
        if peek() == "^":
            eat()
            k = e_atom()
            if not k.is_const() or k.const_value().denominator != 1 or not 0 <= k.const_value() <= 8:
                raise UErr("Powers must be whole numbers from 0 to 8.")
            b = b ** int(k.const_value())
        return b

    def e_atom():
        t = peek()
        if t is None:
            raise UErr("The expression ends too soon.")
        if t == "(":
            eat()
            v = e_at()
            if peek() != ")":
                raise UErr("A bracket is not closed.")
            eat()
            return v
        eat()
        if t[0].isdigit():
            return P.Poly.const(Fraction(t))
        if t.isalpha():
            return P.Poly.var(t.lower())
        raise UErr(f"Unexpected '{t}'.")
    r = e_at()
    if i[0] != len(toks):
        raise UErr("I could not read the whole expression.")
    return r


@guard
def evaluate(d):
    f, lv = parse_op(d.get("op"))
    L, R = lv
    steps = [f"<b>The rule:</b> {L} * {R} = {_pt(f)} (the star is just a name for this special operation; wherever you see {L} * {R}, use this rule)."]
    expr = (d.get("expr") or "").strip()
    if not expr:
        raise UErr("Type what to work out, for example 3 @ 4 or (2 @ 3) @ 5. Use @ for the new operation.")
    poly = _parse_expr(expr, f)
    vs = poly.vars()
    if vs:
        steps.append(f"Working out {esc(expr)} gives an expression in {', '.join(vs)}: {_pt(poly)}.")
        return _ok(steps, f"<b>{_pt(poly)}</b>")
    # narrate step by step for nested ops on numbers
    s = P.normalise(expr)
    steps.append("<b>How:</b> replace "
                 f"the first number with {L} and the second with {R} in the rule, then calculate. Do the bracket first.")

    def trace(text):
        m = re.search(r"\(([^()]*@[^()]*)\)", text)
        t_ = text
        out = []
        while True:
            m = re.search(r"\(([^()@]*)\)", t_)
            m2 = re.search(r"\(([^()]*@[^()]*)\)", t_)
            if not m2:
                break
            inner = m2.group(1)
            val = _parse_expr(inner, f).const_value()
            out.append(f"({inner.strip()}) = {fm(val, 6)}")
            t_ = t_[:m2.start()] + fm(val, 6) + t_[m2.end():]
        return out, t_
    lines, rest = trace(s)
    for ln in lines:
        steps.append("Bracket: " + ln)
    parts = [x.strip() for x in rest.split("@")]
    if len(parts) == 2:
        a_, b_ = _parse_expr(parts[0], f).const_value(), _parse_expr(parts[1], f).const_value()
        sub_txt = _pt(_rename(f, {"a": f"({fm(a_, 6)})", "b": f"({fm(b_, 6)})"})) if False else None
        steps.append(f"Put {L} = {fm(a_, 6)} and {R} = {fm(b_, 6)} into {_pt(f)}: " + _subst_text(f, a_, b_, L, R) + f" = {HL(fm(poly.const_value(), 6))}")
    return _ok(steps, f"<b>{esc(expr)} = {fr(poly.const_value())}</b>" + ("" if poly.const_value().denominator == 1 else f" (= {fm(poly.const_value(), 4)})"))


def _subst_text(f, a, b, L, R):
    """readable substitution of numbers into polynomial f(a,b)"""
    out = ""
    for k in sorted(f.t, key=lambda k: (-sum(e for _, e in k), k)):
        c = f.t[k]
        facs = []
        for v, e in k:
            val = a if v == "a" else b
            facs.append(f"({fm(val, 6)})" + (f"<sup>{e}</sup>" if e > 1 else ""))
        body = "".join(facs) if facs else ""
        mag = abs(c)
        t = (fm(mag, 6) + ("&times;" + body if body else "")) if (mag != 1 or not body) else body
        out += (f" {MINUS if c < 0 else '+'} " if out else (MINUS if c < 0 else "")) + t
    return out or "0"


@guard
def solve_eq(d):
    f, lv = parse_op(d.get("op"))
    steps = [f"<b>The rule:</b> {lv[0]} * {lv[1]} = {_pt(f)}."]
    eq = (d.get("eq") or "").strip()
    if eq.count("=") != 1:
        raise UErr("Type an equation with one = sign, for example x @ 3 = 11 (use @ for the new operation).")
    L_, R_ = eq.split("=")
    pl, pr_ = _parse_expr(L_, f), _parse_expr(R_, f)
    vs = sorted(set(pl.vars()) | set(pr_.vars()))
    if len(vs) != 1:
        raise UErr("Use exactly one unknown letter (like x).")
    v = vs[0]
    steps.append(f"<b>Step 1 - Use the rule on the left side:</b> {esc(L_.strip())} becomes {_pt(pl)}.")
    if not pr_.is_const() or True:
        steps.append(f"Right side: {_pt(pr_)}")
    h = pl - pr_
    steps.append(f"<b>Step 2 - Make the equation equal to 0:</b> {_pt(h)} = 0")
    roots = _roots(h, v)
    if roots is None:
        raise UErr("This equation is true for every value (or has no unknown left).")
    if not roots:
        steps.append("No real number satisfies this equation.")
        return _ok(steps, "<b>No solution</b>")
    deg = h.degree_in(v)
    if deg == 1:
        co = h.to_uni(v)
        steps.append(f"<b>Step 3 - Solve:</b> {fm(co[1], 6)}{v} = {fm(-co[0], 6)}, so {v} = {HL(_show(roots[0]))}")
    else:
        steps.append(f"<b>Step 3 - Solve</b> the equation of degree {deg} (factorise, or use the quadratic formula): {v} = " + " or ".join(_show(r) for r in roots))
    return _ok(steps, "<b>" + ", &nbsp; ".join(f"{v} = {_show(r)}" for r in roots) + "</b>")


# ------------------------------------------------------------------- properties --

def _int_vals(f, a, b):
    return apply(f, P.Poly.const(a), P.Poly.const(b)).const_value()


@guard
def properties(d):
    f, lv = parse_op(d.get("op"))
    L, R = lv
    which = d.get("which", "all")
    domain = d.get("dom", "R")
    steps = [f"<b>The rule:</b> {L} * {R} = {_pt(f)}."]
    out = []
    A, B, C = P.Poly.var("a"), P.Poly.var("b"), P.Poly.var("c")
    # closure
    if which in ("all", "closure"):
        dn = {"R": "real numbers", "Q": "rational numbers", "Z": "integers", "N": "natural numbers {1, 2, 3, ...}", "W": "whole numbers {0, 1, 2, ...}"}[domain]
        steps.append(f"<b>Closure on the {dn}.</b> The set is <i>closed</i> if every time you combine two members you get a member again.")
        closed = True
        why = ""
        if domain in ("R", "Q"):
            why = f"{L} * {R} is made only by adding, subtracting and multiplying numbers, so the answer is always a {'real' if domain == 'R' else 'rational'} number: <b>closed</b>."
        else:
            lo = 1 if domain == "N" else 0 if domain == "W" else -6
            bad = None
            for x in range(lo, lo + 13):
                for y in range(lo, lo + 13):
                    v = _int_vals(f, x, y)
                    if v.denominator != 1 or (domain == "N" and v < 1) or (domain == "W" and v < 0):
                        bad = (x, y, v)
                        break
                if bad:
                    break
            closed = bad is None
            if bad:
                why = f"Counter-example: {bad[0]} * {bad[1]} = {fm(bad[2], 4)}, which is not in the set: <b>not closed</b>."
            else:
                why = f"Trying many pairs always gave a member of the set, and the rule has {'whole-number' if all(c.denominator == 1 for c in f.t.values()) else 'fractional'} coefficients: <b>closed</b>."
        steps.append(why)
        out.append(f"Closure on {dn}: {'yes' if closed else 'no'}")
    # commutative
    if which in ("all", "comm"):
        swapped = apply(f, B, A)
        steps.append(f"<b>Commutative?</b> Is {L} * {R} = {R} * {L} for all values? Work out {R} * {L} by swapping the letters in the rule.")
        steps.append(f"{L} * {R} = {_pt(f)}; &nbsp; {R} * {L} = {fstr(f, R, L) if False else _pt(_rename(f, {'a': 'b', 'b': 'a'}))}")
        comm = (swapped == _rename(f, {"a": "a", "b": "b"})) if False else (f == _rename(f, {"a": "b", "b": "a"}))
        steps.append("They are " + ("the <b>same</b>, so the operation IS commutative." if comm else "<b>different</b>, so the operation is NOT commutative."))
        if not comm:
            for x, y in ((1, 2), (2, 3), (0, 1), (3, 5)):
                v1, v2 = _int_vals(f, x, y), _int_vals(f, y, x)
                if v1 != v2:
                    steps.append(f"Counter-example: {x} * {y} = {fm(v1, 4)} but {y} * {x} = {fm(v2, 4)}.")
                    break
        out.append(f"Commutative: {'yes' if comm else 'no'}")
    # associative
    if which in ("all", "assoc"):
        left = apply(f, apply(f, A, B), C)
        right = apply(f, A, apply(f, B, C))
        steps.append("<b>Associative?</b> Is (a * b) * c = a * (b * c)? Work out each side with the rule.")
        steps.append(f"(a * b) * c = {_pt(left)}<br>a * (b * c) = {_pt(right)}")
        assoc = left == right
        steps.append("They are " + ("the <b>same</b>, so the operation IS associative." if assoc else "<b>different</b>, so the operation is NOT associative."))
        if not assoc:
            for x, y, z in ((1, 2, 3), (2, 3, 4), (0, 1, 2), (1, 1, 2)):
                v1 = _int_vals(f, _int_vals(f, x, y), z)
                v2 = _int_vals(f, x, _int_vals(f, y, z))
                if v1 != v2:
                    steps.append(f"Counter-example: ({x} * {y}) * {z} = {fm(v1, 4)} but {x} * ({y} * {z}) = {fm(v2, 4)}.")
                    break
        out.append(f"Associative: {'yes' if assoc else 'no'}")
    # identity
    ident = None
    if which in ("all", "identity", "inverse"):
        E = P.Poly.var("e")
        h = apply(f, A, E) - A
        steps.append(f"<b>Identity element e:</b> a number e such that a * e = a for every a. Put b = e in the rule: a * e = {_pt(_rename(f, {'a': 'a', 'b': 'e'}))}, and make it equal to a.")
        eqn = _pt(h)
        steps.append(f"{_pt(_rename(f, {'a': 'a', 'b': 'e'}))} = a &rarr; {eqn} = 0. This must be true for EVERY a, so every group of terms in a must be 0 (collect the terms in a).")
        # coefficients of powers of a (as polys in e)
        by = {}
        for k, c in h.t.items():
            dk = dict(k)
            pa = dk.pop("a", 0)
            by.setdefault(pa, P.Poly())
            by[pa] = by[pa] + P.Poly({P._key(dk.items()): c})
        cand = None
        for pa in sorted(by):
            co = by[pa]
            rts = _roots(co, "e") if not co.is_zero() else None
            if rts is None:
                continue
            steps.append(f"Terms with a<sup>{pa}</sup>: {_pt(co)} = 0" + (f" &rarr; e = {', '.join(_show(r) for r in rts) if rts else 'impossible'}"))
            cand = set(rts) if cand is None else cand & set(rts)
            if cand is not None and not cand:
                break
        if cand:
            e0 = sorted(cand, key=float)[0]
            if isinstance(e0, float):
                e0 = Fraction(e0).limit_denominator(10 ** 6)
            left_ok = apply(f, P.Poly.const(e0), A) == A
            ident = e0
            steps.append(f"So e = {HL(_show(e0))}. Check: a * {_show(e0)} = a " + ("and also " + _show(e0) + " * a = a, so it works on both sides &#10003;" if left_ok else "but " + _show(e0) + " * a is not always a, so there is no two-sided identity."))
            if not left_ok:
                ident = None
        else:
            steps.append("No single number e works for every a, so there is <b>no identity element</b>.")
        out.append("Identity: " + (_show(ident) if ident is not None else "none"))
    if which in ("all", "inverse"):
        if ident is None:
            steps.append("<b>Inverse:</b> inverses only make sense when there is an identity element. Since there is none, there are no inverses.")
            out.append("Inverses: none (no identity)")
        else:
            X = P.Poly.var("x")
            hh = apply(f, A, X) - P.Poly.const(ident)
            steps.append(f"<b>Inverse of a:</b> a number x such that a * x = e = {_show(ident)}. Put b = x in the rule and set it equal to {_show(ident)}: {_pt(apply(f, A, X))} = {_show(ident)}")
            dx = hh.degree_in("x")
            if dx == 1:
                c1 = P.Poly()
                c0 = P.Poly()
                for k, c in hh.t.items():
                    dk = dict(k)
                    px = dk.pop("x", 0)
                    t = P.Poly({P._key(dk.items()): c})
                    if px == 1:
                        c1 = c1 + t
                    else:
                        c0 = c0 + t
                steps.append(f"Collect the x terms: x({_pt(c1)}) + ({_pt(c0)}) = 0")
                if c1.is_const():
                    steps.append(f"x = {_pt(-c0.scale(1 / c1.const_value()))}")
                else:
                    steps.append(f"x = {FR(_pt(-c0), _pt(c1))}")
                bad = _roots(c1, "a") if not c1.is_const() else []
                note = ""
                if bad:
                    note = " The element(s) a = " + ", ".join(_show(r) for r in bad) + " have no inverse (the bottom would be 0)."
                    steps.append(f"The bottom {_pt(c1)} cannot be 0:" + note)
                out.append(f"Inverse of a: {_pt(-c0.scale(1 / c1.const_value()))}" if c1.is_const() else f"Inverse of a: ({_pt(-c0)}) / ({_pt(c1)})")
                res_inv = f"inverse of a = {FR(_pt(-c0), _pt(c1))}"
            else:
                steps.append("The equation for x is not a straight line in x, so work out the inverse of each specific element by solving it (use the 'Solve an equation' tab).")
                out.append("Inverse: solve for specific elements")
    if not out:
        raise UErr("Choose a property.")
    return _ok(steps, "<b>" + "<br>".join(out) + "</b>")


# ---------------------------------------------------------------- finite tables --

@guard
def table_op(d):
    els = [t for t in re.split(r"[,\s]+", (d.get("set") or "").strip()) if t]
    if not 2 <= len(els) <= 12:
        raise UErr("Give between 2 and 12 elements, separated by commas, like 0, 1, 2, 3.")
    vals = []
    for t in els:
        x = num(t, "an element")
        if x.denominator != 1:
            raise UErr("Use whole-number elements here.")
        vals.append(int(x))
    if len(set(vals)) != len(vals):
        raise UErr("Each element should appear once.")
    f, lv = parse_op(d.get("op"))
    n = (d.get("mod") or "").strip()
    mod = int(num(n, "the modulus")) if n else None
    if mod is not None and not 2 <= mod <= 1000:
        raise UErr("The modulus must be between 2 and 1000.")

    def op(x, y):
        v = _int_vals(f, x, y)
        if v.denominator != 1:
            return None
        v = int(v)
        return v % mod if mod else v
    steps = [f"<b>The rule:</b> {lv[0]} * {lv[1]} = {_pt(f)}" + (f", then take the remainder on division by {mod}." if mod else ".")]
    steps.append("<b>Build the table:</b> row element on the left * column element on top.")
    rows = []
    T = {}
    for x in vals:
        row = []
        for y in vals:
            v = op(x, y)
            T[(x, y)] = v
            row.append("?" if v is None else str(v))
        rows.append([f"<b>{x}</b>"] + row)
    steps.append(table(rows, ["*"] + [f"<b>{y}</b>" for y in vals]))
    S = set(vals)
    closed = all(T[(x, y)] in S for x in vals for y in vals)
    steps.append("<b>Closed?</b> " + ("Every entry in the table is in the set, so it IS closed." if closed else
                                      "Some entries are NOT in the set (e.g. " + next(f"{x} * {y} = {T[(x, y)]}" for x in vals for y in vals if T[(x, y)] not in S) + "), so it is NOT closed."))
    out = [f"Closed: {'yes' if closed else 'no'}"]
    comm = all(T[(x, y)] == T[(y, x)] for x in vals for y in vals)
    steps.append("<b>Commutative?</b> " + ("The table is a mirror image across the main diagonal, so YES." if comm else "The table is not symmetrical, so NO."))
    out.append(f"Commutative: {'yes' if comm else 'no'}")
    ident = None
    if closed:
        for e in vals:
            if all(T[(e, x)] == x and T[(x, e)] == x for x in vals):
                ident = e
        steps.append("<b>Identity?</b> Look for a row that is the same as the top row AND a column that is the same as the left column. " + (f"The identity is <b>{ident}</b>." if ident is not None else "There is none."))
        out.append(f"Identity: {ident if ident is not None else 'none'}")
        if ident is not None:
            inv = []
            for x in vals:
                ys = [y for y in vals if T[(x, y)] == ident and T[(y, x)] == ident]
                inv.append(f"{x}: " + (str(ys[0]) if ys else "none"))
            steps.append(f"<b>Inverses:</b> find where {ident} appears in each row. " + "; ".join(inv))
            out.append("Inverses &rarr; " + "; ".join(inv))
        assoc = all(T[(T[(x, y)], z)] == T[(x, T[(y, z)])] for x in vals for y in vals for z in vals)
        steps.append("<b>Associative?</b> Checking every (x * y) * z against x * (y * z): " + ("always equal, YES." if assoc else "not always equal, NO."))
        out.append(f"Associative: {'yes' if assoc else 'no'}")
    return _ok(steps, "<b>" + "<br>".join(out) + "</b>")


# ================================================================= modular ===

def _int(v, label, lo=-10 ** 12, hi=10 ** 12):
    x = num(v, label)
    if x.denominator != 1 or not lo <= x <= hi:
        raise UErr(f"{label} must be a whole number (not too large).")
    return int(x)


def ext_euclid_table(a, n):
    rows = []
    r0, r1 = n, a
    s0, s1 = 0, 1
    while r1:
        q = r0 // r1
        rows.append([str(r0), str(r1), str(q), str(s0), str(s1)])
        r0, r1 = r1, r0 - q * r1
        s0, s1 = s1, s0 - q * s1
    return rows, r0, s0


@guard
def modular(d):
    k = d.get("kind", "reduce")
    steps = []
    if k == "reduce":
        a = _int(d.get("a"), "the number")
        n = _int(d.get("n"), "the modulus", 2, 10 ** 12)
        q, r = divmod(a, n)
        steps.append(f"<b>Idea:</b> 'a mod n' means the remainder when a is divided by n (always from 0 to n &minus; 1).")
        steps.append(f"{a} &divide; {n}: {a} = {n} &times; ({q}) + {r}" + (" (for a negative number, go DOWN to the nearest multiple, so the remainder stays positive)" if a < 0 else ""))
        steps.append(f"So {a} &equiv; {HL(str(r))} (mod {n}).")
        return _ok(steps, f"<b>{a} mod {n} = {r}</b>")
    if k == "expr":
        text = (d.get("e") or "").strip()
        m = re.split(r"\bmod\b|\(mod\s*|≡|=\s*\d*\s*\(mod", text, flags=re.I)
        mm = re.match(r"^(.*?)\s*(?:\(?\s*mod\s*)(\d+)\s*\)?\s*$", text, flags=re.I)
        if not mm:
            raise UErr("Type the sum followed by mod and the modulus, for example (3 * 5 + 7) mod 4.")
        body, n = mm.group(1), int(mm.group(2))
        if not 2 <= n <= 10 ** 9:
            raise UErr("The modulus must be 2 or more.")
        try:
            val = P.parse_poly(body)
        except P.ParseError as e:
            raise UErr(str(e))
        if not val.is_const() or val.const_value().denominator != 1:
            raise UErr("Use whole numbers with + - * ^ and brackets (no letters, no division).")
        v = int(val.const_value())
        steps.append(f"<b>Step 1 - Work out the sum as an ordinary number:</b> {esc(body.strip())} = {v}")
        q, r = divmod(v, n)
        steps.append(f"<b>Step 2 - Divide by {n} and keep the remainder:</b> {v} = {n} &times; {q} + {r}")
        steps.append("(Shortcut: you may take the remainder after each step instead, because (a + b) mod n = ((a mod n) + (b mod n)) mod n and the same for &times;.)")
        return _ok(steps, f"<b>{esc(body.strip())} &equiv; {r} (mod {n})</b>")
    if k == "power":
        a = _int(d.get("a"), "the base", -10 ** 9, 10 ** 9)
        e = _int(d.get("e"), "the power", 0, 10 ** 12)
        n = _int(d.get("n"), "the modulus", 2, 10 ** 9)
        steps.append(f"<b>Find {a}<sup>{e}</sup> mod {n}</b> without working out the huge number.")
        a0 = a % n
        steps.append(f"<b>Step 1.</b> Reduce the base: {a} &equiv; {a0} (mod {n}).")
        seen = {}
        seq = []
        cur = 1
        i = 0
        while i <= 600:
            if cur in seen and i > 0:
                break
            seen[cur] = i
            seq.append(cur)
            cur = cur * a0 % n
            i += 1
        # seq[i] = a0^i mod n ; find cycle
        if cur in seen and seen[cur] is not None and i <= 600:
            start = seen[cur]
            period = i - start
            steps.append(f"<b>Step 2 - Look for a pattern</b> in the remainders of {a0}<sup>1</sup>, {a0}<sup>2</sup>, {a0}<sup>3</sup>, ... mod {n}: "
                         + ", ".join(str(x) for x in seq[1:min(len(seq), 16)] + ([cur] if len(seq) < 16 else [])) + " ...")
            steps.append(f"The remainders repeat: after the power {start + period - 1 if start else period} the pattern starts again (cycle length {period}).")
            if e < start:
                r = pow(a0, e, n)
                steps.append(f"The power {e} is before the cycle repeats, so just read it off: {HL(str(r))}.")
            else:
                idx = (e - start) % period + start
                steps.append(f"<b>Step 3.</b> Position in the cycle: {e} mod {period} " + (f"(taking the power from {start}) " if start else "") + f"&rarr; use power {idx}, remainder = {HL(str(pow(a0, idx, n)))}.")
            r = pow(a0, e, n)
        else:
            steps.append("<b>Step 2 - Repeated squaring</b> (the pattern is long, so square and reduce at each step):")
            bits = bin(e)[2:]
            rows = []
            res_ = 1
            base = a0
            for i, bch in enumerate(reversed(bits)):
                rows.append([str(i), f"{a0}<sup>{2 ** i}</sup> &equiv; {base}", bch])
                if bch == "1":
                    res_ = res_ * base % n
                base = base * base % n
            steps.append(table(rows[:40], ["i", "square", "bit"]))
            steps.append(f"Multiply the squares whose bit is 1 (the binary of {e} is {bits}), reducing mod {n} each time.")
            r = pow(a0, e, n)
        steps.append(f"<b>Answer:</b> {a}<sup>{e}</sup> &equiv; {r} (mod {n}).")
        return _ok(steps, f"<b>{a}<sup>{e}</sup> mod {n} = {r}</b>")
    if k == "linear":
        a = _int(d.get("a"), "a", -10 ** 9, 10 ** 9)
        b = _int(d.get("b"), "b", -10 ** 9, 10 ** 9)
        n = _int(d.get("n"), "the modulus", 2, 10 ** 6)
        steps.append(f"<b>Solve</b> {a}x &equiv; {b} (mod {n}): find all x from 0 to {n - 1} such that {a}x leaves the same remainder as {b} when divided by {n}.")
        a %= n
        b %= n
        steps.append(f"<b>Step 1 - Reduce:</b> {a}x &equiv; {b} (mod {n}).")
        g = math.gcd(a, n)
        steps.append(f"<b>Step 2 - HCF of {a} and {n}</b> = {g}. A solution exists only if this HCF divides {b}: {b} &divide; {g} = {fm(Fraction(b, g), 4)} " + ("(yes)" if b % g == 0 else "(no)"))
        if b % g:
            return _ok(steps + ["It does not divide, so there is <b>no solution</b>."], "<b>No solution</b>")
        a2, b2, n2 = a // g, b // g, n // g
        if g > 1:
            steps.append(f"Divide everything by {g}: {a2}x &equiv; {b2} (mod {n2}).")
        if n2 == 1:
            sols = list(range(n))
            return _ok(steps + [f"Every number works."], f"<b>All x from 0 to {n - 1}</b>")
        # inverse of a2 mod n2
        inv = pow(a2, -1, n2)
        rows, _, _ = ext_euclid_table(a2, n2)
        steps.append(f"<b>Step 3 - Find the inverse of {a2} mod {n2}</b> (the number that multiplies with {a2} to give 1 mod {n2}). Try the multiples: " +
                     ", ".join(f"{a2}&times;{t} = {a2 * t} &equiv; {a2 * t % n2}" for t in range(1, min(n2, 14) + 1) if True)[:600] + f". So the inverse is <b>{inv}</b> ({a2} &times; {inv} = {a2 * inv} = {a2 * inv // n2}&times;{n2} + 1).")
        x0 = inv * b2 % n2
        steps.append(f"<b>Step 4 - Multiply both sides by {inv}:</b> x &equiv; {inv} &times; {b2} = {inv * b2} &equiv; {HL(str(x0))} (mod {n2}).")
        sols = [x0 + n2 * t for t in range(g)]
        steps.append(f"<b>Step 5 - List the solutions</b> between 0 and {n - 1}: x = {x0}" + (f" + {n2}t, i.e. " + ", ".join(map(str, sols)) if g > 1 else "") + ".")
        steps.append("Check: " + "; ".join(f"{a}&times;{x} = {a * x} &equiv; {a * x % n}" for x in sols[:4]))
        return _ok(steps, f"<b>x &equiv; {', '.join(map(str, sols))} (mod {n})</b>")
    if k == "days":
        names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        s = int(d.get("start", "0"))
        t = _int(d.get("k"), "the number of days", -10 ** 9, 10 ** 9)
        steps.append("<b>Idea:</b> the days of the week repeat every 7 days, so work modulo 7. Number the days: " + ", ".join(f"{nm} = {i}" for i, nm in enumerate(names)) + ".")
        steps.append(f"Start: {names[s]} = {s}. {abs(t)} days {'later' if t >= 0 else 'earlier'}: {s} {'+' if t >= 0 else '&minus;'} {abs(t)} = {s + t}.")
        q, r = divmod(s + t, 7)
        steps.append(f"{s + t} &divide; 7: remainder {r} (so it is {r} days into the week after whole weeks are removed).")
        steps.append(f"Day number {r} = <b>{names[r]}</b>.")
        return _ok(steps, f"<b>{abs(t)} days {'after' if t >= 0 else 'before'} {names[s]} is {names[r]}</b>")
    if k == "clock":
        h = _int(d.get("a"), "the starting hour", 0, 24)
        t = _int(d.get("k"), "the number of hours", -10 ** 9, 10 ** 9)
        mod = int(d.get("mod", "12"))
        steps.append(f"<b>Idea:</b> on a {mod}-hour clock the times repeat every {mod} hours, so work modulo {mod}.")
        v = h + t
        r = v % mod
        shown = r if (mod == 24 or r != 0) else 12
        steps.append(f"{h} {'+' if t >= 0 else '&minus;'} {abs(t)} = {v}; {v} &divide; {mod} leaves remainder {r}" + (f" (on a 12-hour clock a remainder of 0 is read as 12)" if mod == 12 and r == 0 else "") + ".")
        return _ok(steps, f"<b>The time is {shown} o'clock{' (24-hour clock)' if mod == 24 else ''}</b>")
    if k == "crt":
        eqs = re.findall(r"(\d+)\s*(?:mod|\(mod)\s*(\d+)", (d.get("e") or ""), flags=re.I)
        if not 2 <= len(eqs) <= 4:
            raise UErr("Type 2 to 4 congruences like: x = 2 mod 3, x = 3 mod 5")
        cons = [(int(a) % int(m), int(m)) for a, m in eqs]
        if any(m < 2 for _, m in cons):
            raise UErr("Each modulus must be 2 or more.")
        L = 1
        for _, m in cons:
            L = L * m // math.gcd(L, m)
        if L > 10 ** 7:
            raise UErr("The numbers are too large for the listing method here.")
        steps.append("<b>Method (list and match):</b> list the numbers that fit the biggest modulus first, and test the others.")
        cons.sort(key=lambda c: -c[1])
        a0, m0 = cons[0]
        cands = []
        x = a0
        found = None
        steps.append(f"x &equiv; {a0} (mod {m0}): x = " + ", ".join(str(a0 + m0 * t) for t in range(6)) + ", ...")
        while x < L + a0 + 1:
            if all(x % m == a for a, m in cons):
                found = x
                break
            x += m0
        if found is None:
            return _ok(steps + ["No number satisfies all the congruences (they clash)."], "<b>No solution</b>")
        for a, m in cons[1:]:
            steps.append(f"Test against x &equiv; {a} (mod {m}): " + f"{found} &divide; {m} leaves remainder {found % m} &#10003;")
        steps.append(f"The smallest solution is {HL(str(found))}; all solutions are x = {found} + {L}t (t = 0, 1, 2, ...).")
        return _ok(steps, f"<b>x = {found} + {L}t</b>")
    if k == "mtable":
        n = _int(d.get("n"), "the modulus", 2, 12)
        op = d.get("op", "+")
        sym = "+" if op == "+" else "&times;"
        steps.append(f"<b>Table of {'addition' if op == '+' else 'multiplication'} modulo {n}:</b> each entry is (row {sym} column), then take the remainder on division by {n}.")
        els = list(range(n))
        rows = [[f"<b>{x}</b>"] + [str((x + y) % n if op == "+" else (x * y) % n) for y in els] for x in els]
        steps.append(table(rows, [sym] + [f"<b>{y}</b>" for y in els]))
        ident = 0 if op == "+" else 1
        inv = []
        for x in els:
            ys = [y for y in els if ((x + y) % n if op == "+" else (x * y) % n) == ident]
            inv.append(f"{x}: " + (", ".join(map(str, ys)) if ys else "none"))
        steps.append(f"<b>Identity:</b> {ident}. <b>Inverses</b> (the element that gives {ident} with it): " + "; ".join(inv))
        if op != "+":
            steps.append(f"Elements with no inverse share a factor with {n}." + (f" Since {n} is prime, every non-zero element has an inverse." if all(n % p for p in range(2, int(n ** 0.5) + 1)) else ""))
        return _ok(steps, f"<b>Identity = {ident}</b>; inverses: " + "; ".join(inv))
    raise UErr("Choose a type of problem.")


# ----------------------------------------------------------------------- spec ---

def _f(name, label, ph="", **kw):
    return field(name, label, ph, **kw)


_OP = _f("op", "The rule (use letters a, b)", "a * b = a + b - 2ab", wide=True, half=False)

SPEC = {
    "title": "Binary Operations & Modular Arithmetic",
    "intro": "Work with a made-up operation such as <i>a * b = a + b &minus; ab</i>, and with remainders (modular arithmetic).",
    "tabs": [
        {"id": "bo", "label": "Evaluate / solve", "title": "Work out and solve with a binary operation", "endpoint": "solve",
         "hint": "Write the new operation with <b>@</b> in your question. Examples: <i>3 @ 4</i>, <i>(2 @ 3) @ 5</i>, or an equation like <i>x @ 3 = 11</i>.",
         "fields": [_OP, _f("eq", "Question or equation", "x @ 3 = 11", wide=True, half=False)]},
        {"id": "bp", "label": "Properties", "title": "Closure, commutative, associative, identity, inverse", "endpoint": "props",
         "fields": [_OP,
                    select("which", "Check", [("all", "all properties"), ("closure", "closure"), ("comm", "commutative"), ("assoc", "associative"),
                                              ("identity", "identity element"), ("inverse", "inverse")], wide=True),
                    select("dom", "Set of numbers", [("R", "real numbers"), ("Q", "rational numbers"), ("Z", "integers"), ("W", "whole numbers"), ("N", "natural numbers")], show_if={"which": ["all", "closure"]})]},
        {"id": "bt", "label": "Table of a finite set", "title": "Operation table for a finite set", "endpoint": "table",
         "fields": [_f("set", "Elements (comma separated)", "0, 1, 2, 3", wide=True, half=False),
                    _f("op", "The rule (letters a, b)", "a * b = a + b", wide=True, half=False),
                    _f("mod", "Take remainder mod (optional)", "4")]},
        {"id": "bm", "label": "Modular arithmetic", "title": "Modular arithmetic (remainders)", "endpoint": "modular",
         "fields": [select("kind", "What do you want to do?", [("reduce", "reduce a number mod n"), ("expr", "work out a sum mod n"), ("power", "a large power mod n"),
                                                               ("linear", "solve ax &equiv; b (mod n)"), ("crt", "several congruences together"),
                                                               ("days", "days of the week"), ("clock", "clock time"), ("mtable", "addition / multiplication table mod n")], wide=True),
                    _f("a", "Number", "47", show_if={"kind": ["reduce", "power", "linear"]}),
                    _f("a", "Starting hour", "9", show_if={"kind": "clock"}),
                    _f("e", "Sum, e.g. (3*5 + 7) mod 4", "(3*5 + 7) mod 4", wide=True, half=False, show_if={"kind": "expr"}),
                    _f("e", "Congruences", "x = 2 mod 3, x = 3 mod 5", wide=True, half=False, show_if={"kind": "crt"}),
                    _f("e", "Power", "100", show_if={"kind": "power"}),
                    _f("b", "b", "6", show_if={"kind": "linear"}),
                    _f("n", "Modulus n", "7", show_if={"kind": ["reduce", "power", "linear", "mtable"]}),
                    select("start", "Starting day", [(str(i), n) for i, n in enumerate(["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])], show_if={"kind": "days"}),
                    _f("k", "Number of days / hours (negative = earlier)", "100", show_if={"kind": ["days", "clock"]}),
                    select("mod", "Clock", [("12", "12-hour clock"), ("24", "24-hour clock")], show_if={"kind": "clock"}),
                    select("op", "Table of", [("+", "addition"), ("*", "multiplication")], show_if={"kind": "mtable"})]},
    ],
}


def _dispatch_solve(d):
    expr = (d.get("eq") or "")
    if "=" in expr:
        return solve_eq({"op": d.get("op"), "eq": expr})
    return evaluate({"op": d.get("op"), "expr": expr})


topics.register("binops", SPEC, {"solve": _dispatch_solve, "props": properties, "table": table_op, "modular": modular})
