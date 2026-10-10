"""
Fractions topic - letters (algebraic fractions).  Pure Python on top of poly.py.
"""
import re
from fractions import Fraction
from math import gcd, lcm, isqrt
from functools import reduce

from poly import (Poly, RF, ParseError, parse_ast, ast_eval, parse_poly,
                  split_terms, factor, primitive, poly_str, factors_str,
                  lcm_hcf_polys, normalise)
from frac_numeric import (_ok, _fail, esc, FR, fr, table, MUL, DIV, MINUS,
                          split_list, dec_str)


# ------------------------------------------------------------- display -----

def _fac_html(const, facs):
    return factors_str(const, facs)


def ff_make(n, d):
    """simplify n/d: return dict(const_n, const_d, num=[(P,e)], den=[(P,e)],
    cancelled=[(P,e)])"""
    cn, fn_ = factor(n)
    cd, fd_ = factor(d)
    dn, dd = dict(fn_), dict(fd_)
    cancelled = []
    for f in list(dn):
        if f in dd:
            m = min(dn[f], dd[f])
            cancelled.append((f, m))
            dn[f] -= m
            dd[f] -= m
    num = [(f, e) for f, e in fn_ if dn.get(f, 0) > 0]
    num = [(f, dn[f]) for f, _ in num]
    den = [(f, dd[f]) for f, _ in fd_ if dd.get(f, 0) > 0]
    c = Fraction(cn) / Fraction(cd)
    return {"c": c, "num": num, "den": den, "cancelled": cancelled}


def ff_html(ff, expand_num=False):
    c = ff["c"]
    cn, cd = c.numerator, c.denominator
    if expand_num:
        p = Poly.const(cn)
        for f, e in ff["num"]:
            p = p * (f ** e)
        num_html = poly_str(p)
    else:
        num_html = factors_str(Fraction(cn), ff["num"])
    if not ff["den"] and cd == 1:
        return num_html
    den_html = factors_str(Fraction(cd), ff["den"]) if (ff["den"] or cd != 1) else "1"
    return FR(num_html, den_html)


def ff_den_is_one(ff):
    return not ff["den"] and ff["c"].denominator == 1


def _paren(p):
    s = poly_str(p)
    return f"({s})" if len(p.t) > 1 else s


def _expanded_num(ff):
    p = Poly.const(ff["c"].numerator)
    for f, e in ff["num"]:
        p = p * (f ** e)
    return p


def _expanded_den(ff):
    p = Poly.const(ff["c"].denominator)
    for f, e in ff["den"]:
        p = p * (f ** e)
    return p


def _factor_notes(poly, label):
    notes = []
    c, fs = factor(poly, notes)
    s = f"{label} = {poly_str(poly)}"
    if len(fs) == 0 or (len(fs) == 1 and fs[0][1] == 1 and fs[0][0] == primitive(poly)[1] and c in (1, -1) and False):
        pass
    fac = factors_str(c, fs)
    line = f"{s} &nbsp;&rarr;&nbsp; {fac}"
    why = []
    if poly.is_const():
        return line, []
    if len(poly.t) == 1:
        return f"{s} (a single term - split into its prime factors and letters)", []
    # why: common factor?
    _, prim = primitive(poly)
    me = prim.monomial_exponents()
    ints_gcd = abs(primitive(poly)[0])
    if me or ints_gcd not in (1,):
        bits = []
        if ints_gcd not in (1,):
            bits.append(str(ints_gcd.numerator) if ints_gcd.denominator == 1 else fr(ints_gcd))
        for v, e in sorted(me.items()):
            bits.append(f"{v}<sup>{e}</sup>" if e > 1 else v)
        if bits:
            why.append("take out the common factor " + "".join(bits))
    why += notes
    if len(fs) == 1 and fs[0][1] == 1 and not why and len(fs[0][0].t) > 1:
        why.append("it cannot be factorised any further")
    return line, why


def factor_steps(poly, label):
    line, why = _factor_notes(poly, label)
    out = [line]
    if why:
        out.append("<i>(" + "; ".join(why) + ")</i>")
    return out


def _restrictions(dens):
    """values of the single variable that make a denominator zero"""
    vals = {}
    for d in dens:
        _, fs = factor(d)
        for f, _e in fs:
            vs = f.vars()
            if len(vs) == 1 and f.degree_in(vs[0]) == 1:
                co = f.to_uni(vs[0])
                vals[(vs[0], -co[0] / co[1])] = True
    out = []
    for (v, r) in sorted(vals, key=lambda t: (t[0], t[1])):
        out.append(f"{v} &ne; {fr(r)}")
    return out


# ----------------------------------------------------- factorise ----------

def alg_factorise(expr):
    try:
        p = parse_poly(expr)
        if p.is_zero():
            return _fail("Type an expression like x^2 - 9 or 6x^2 + 11x - 10.")
        notes = []
        c, fs = factor(p, notes)
        steps = factor_steps(p, "Expression")
        res = factors_str(c, fs)
        if len(fs) == 1 and fs[0][1] == 1 and c in (1, -1) and len(fs[0][0].t) > 1:
            steps.append("This expression cannot be factorised any further with whole numbers.")
        else:
            # check by expansion
            prod = Poly.const(c)
            for f, e in fs:
                prod = prod * (f ** e)
            steps.append(f"<b>Check by expanding:</b> {res} = {poly_str(prod)} &#10003;")
        return _ok(steps, res)
    except ParseError as e:
        return _fail(str(e))


# ----------------------------------------------------- LCM / HCF ----------

def alg_lcm_hcf(text, want="both"):
    try:
        parts = split_list(text)
        if len(parts) < 2:
            return _fail("Give two or more expressions separated by commas, e.g. 12a^2b, 18ab^3.")
        if len(parts) > 5:
            return _fail("Please use five expressions or fewer.")
        polys = [parse_poly(p) for p in parts]
        steps = ["<b>Step 1.</b> Factorise each expression completely."]
        infos = []
        for src, p in zip(parts, polys):
            steps += factor_steps(p, esc(src))
            infos.append(factor(p))
        ints = []
        for c, _ in infos:
            if c.denominator != 1:
                return _fail("Use whole-number coefficients, please.")
            ints.append(abs(c.numerator))
        _, hf, lf, _ = lcm_hcf_polys(polys)
        res = []
        hnum = reduce(gcd, ints)
        lnum = reduce(lcm, ints)
        if want in ("hcf", "both"):
            steps.append("<b>HCF</b> = (HCF of the numbers) &times; (every letter / bracket that is in <b>all</b> the expressions, "
                         "each with its <b>lowest</b> power).")
            steps.append(f"HCF of the numbers {', '.join(map(str, ints))} = {hnum}")
            h = factors_str(Fraction(hnum), hf)
            steps.append(f"HCF = {h}")
            res.append(f"HCF = {h}")
        if want in ("lcm", "both"):
            steps.append("<b>LCM</b> = (LCM of the numbers) &times; (every letter / bracket that appears in <b>any</b> expression, "
                         "each with its <b>highest</b> power).")
            steps.append(f"LCM of the numbers {', '.join(map(str, ints))} = {lnum}")
            l = factors_str(Fraction(lnum), lf)
            steps.append(f"LCM = {l}")
            res.append(f"LCM = {l}")
        return _ok(steps, "<br>".join(res))
    except ParseError as e:
        return _fail(str(e))


# ------------------------------------------------ polynomial division ------

def _poly_long_div(num, den, v):
    nc, dc = num.to_uni(v), den.to_uni(v)
    q = [Fraction(0)] * max(1, len(nc) - len(dc) + 1)
    r = list(nc)
    while len(r) >= len(dc) and any(r):
        k = len(r) - len(dc)
        f = r[-1] / dc[-1]
        q[k] = f
        for i, c in enumerate(dc):
            r[i + k] -= f * c
        r.pop()
        while r and r[-1] == 0:
            r.pop()
    return Poly.from_uni(q, v), Poly.from_uni(r, v) if r else Poly()


def alg_types(expr):
    """proper / improper algebraic fractions"""
    try:
        rf = ast_eval(parse_ast(expr))
        if rf.d.is_const():
            return _fail("Write a fraction with letters in the denominator, e.g. (x^2+3x+5)/(x+1).")
        ff = ff_make(rf.n, rf.d)
        n, d = _expanded_num(ff), _expanded_den(ff)
        vs = sorted(set(n.vars()) | set(d.vars()))
        steps = [f"The fraction is {FR(poly_str(rf.n), poly_str(rf.d))}"]
        if len(vs) != 1:
            return _fail("For proper / improper classification please use one letter, e.g. x.")
        v = vs[0]
        dn, dd = n.degree_in(v), d.degree_in(v)
        steps.append(f"Highest power of {v} on top: {dn}. Highest power of {v} at the bottom: {dd}.")
        if dn < dd:
            steps.append("The top has a <b>lower</b> power than the bottom, so it is a <b>proper</b> algebraic fraction "
                         "(like a proper fraction 3/4).")
            return _ok(steps, f"{FR(poly_str(n), poly_str(d))} is a proper algebraic fraction.")
        steps.append("The top has the <b>same or a higher</b> power than the bottom, so it is an <b>improper</b> algebraic fraction "
                     "(like 7/3). To write it as a 'mixed' form, divide the top by the bottom (long division).")
        q, r = _poly_long_div(n, d, v)
        steps.append(f"Divide {poly_str(n)} by {poly_str(d)}:")
        steps.append(f"Quotient (whole part) = {poly_str(q)}")
        steps.append(f"Remainder = {poly_str(r) if not r.is_zero() else '0'}")
        steps.append("Improper fraction = quotient + remainder/divisor.")
        if r.is_zero():
            res = poly_str(q)
        else:
            res = f"{poly_str(q)} + {FR(poly_str(r), poly_str(d))}"
        steps.append(f"{FR(poly_str(n), poly_str(d))} = {res}")
        return _ok(steps, res)
    except ParseError as e:
        return _fail(str(e))


# ----------------------------------------------------- expression ---------

def _is_rational(node):
    return "div" in _flat_ops(node)


def _flat_ops(node):
    ops = {node[0]}
    for ch in node[1:]:
        if isinstance(ch, tuple):
            ops |= _flat_ops(ch)
    return ops


def _has_fraction_division(node):
    """True when a fraction is divided by another fraction (a / (b/c)) or (a/b) / (c/d)."""
    if node[0] == "div":
        return _is_rational(node[1]) or _is_rational(node[2]) or True if _is_rational(node[2]) else _is_rational(node[1])
    return any(_has_fraction_division(ch) for ch in node[1:] if isinstance(ch, tuple))


def _term_rf(node):
    return ast_eval(node)


def _lcd_from(dens):
    """dens: list of ff-denominators [(c_den, [(P,e)])]. returns (Lconst, dict)"""
    L = {}
    lc = 1
    for cd, facs in dens:
        lc = lcm(lc, cd)
        for f, e in facs:
            L[f] = max(L.get(f, 0), e)
    return lc, L


def _mult_poly(lc, L, cd, facs):
    d = dict(facs)
    p = Poly.const(lc // cd)
    for f, e in L.items():
        k = e - d.get(f, 0)
        if k > 0:
            p = p * (f ** k)
    return p


def _lcd_html(lc, L):
    fl = sorted(L.items(), key=lambda fe: (0 if len(fe[0].t) == 1 else 1, fe[0].total_degree(), poly_str(fe[0])))
    return factors_str(Fraction(lc), fl)


def _combine_sum(terms, steps, orig_dens):
    """terms: list of (sign, RF).  Narrate + return (num Poly, lc, L)"""
    ffs = []
    for s, rf in terms:
        ff = ff_make(rf.n, rf.d)
        if s < 0:
            ff["c"] = -ff["c"]
        ffs.append(ff)
    steps.append("<b>Step 1.</b> Write each term as a fraction (whole terms have denominator 1) and simplify each if possible:")
    disp = ""
    for i, (f, (s_, _rf)) in enumerate(zip(ffs, terms)):
        g = dict(f)
        if s_ < 0:
            g["c"] = -g["c"]
        h = ff_html(g)
        if i == 0:
            disp += (MINUS if s_ < 0 else "") + h
        else:
            disp += f" &nbsp;{MINUS if s_ < 0 else '+'}&nbsp; " + h
    steps.append(disp)
    dens = [(f["c"].denominator, f["den"]) for f in ffs]
    if all(not d[1] and d[0] == 1 for d in dens):
        total = Poly()
        for f in ffs:
            total = total + _expanded_num(f)
        return total, 1, {}
    steps.append("<b>Step 2.</b> Find the LCM of the denominators (this is the common denominator).")
    for f in ffs:
        cd = f["c"].denominator
        if f["den"] or cd != 1:
            steps.append(f"Denominator: {factors_str(Fraction(cd), f['den'])}")
    lc, L = _lcd_from(dens)
    steps.append(f"LCM of the denominators = {_lcd_html(lc, L)}")
    steps.append("<b>Step 3.</b> Change each fraction to the common denominator: multiply top and bottom by what is missing.")
    total = Poly()
    pieces = []
    for f in ffs:
        cd = f["c"].denominator
        m = _mult_poly(lc, L, cd, f["den"])
        newn = _expanded_num(f) * m
        total = total + newn
        mtxt = poly_str(m)
        if m == Poly.const(1):
            steps.append(f"{ff_html(f)} already has the common denominator: numerator = {poly_str(newn)}")
        else:
            steps.append(f"{ff_html(f)} = {FR(f'({poly_str(_expanded_num(f))}) {MUL} ({mtxt})' if len(_expanded_num(f).t) > 1 and len(m.t) > 1 else f'{_paren(_expanded_num(f))}{MUL if False else ' '}{_paren(m)}', _lcd_html(lc, L))}"
                         f" = {FR(poly_str(newn), _lcd_html(lc, L))}")
        pieces.append(newn)
    steps.append("<b>Step 4.</b> Add (or subtract) the numerators over the common denominator:")
    joined = ""
    for i, (f, p) in enumerate(zip(ffs, pieces)):
        t = f"({poly_str(p)})" if len(p.t) > 1 or True else poly_str(p)
        joined += (" + " if i else "") + t
    steps.append(f"{FR(joined, _lcd_html(lc, L))} = {FR(poly_str(total), _lcd_html(lc, L))}")
    return total, lc, L


def alg_expression(expr):
    """simplify / add / subtract / multiply / divide algebraic fractions"""
    try:
        ast = parse_ast(expr)
        rf = ast_eval(ast)
        steps = []
        top_terms = split_terms(ast)
        # collect original denominators for restrictions
        dens = []

        def collect(node):
            if node[0] == "div":
                dens.append(ast_eval(node[2]).n)
            for ch in node[1:]:
                if isinstance(ch, tuple):
                    collect(ch)
        collect(ast)

        if len(top_terms) >= 2 and _is_rational(ast):
            terms = [(s, ast_eval(n)) for s, n in top_terms]
            total, lc, L = _combine_sum(terms, steps, dens)
            den_poly = Poly.const(lc)
            for f, e in L.items():
                den_poly = den_poly * (f ** e)
            ff = ff_make(total, den_poly) if not total.is_zero() else None
            if ff is None:
                steps.append("The numerator is 0, so the whole expression is 0.")
                return _ok(steps, "0")
            steps.append("<b>Step 5.</b> Simplify: factorise the numerator and see if anything cancels with the denominator.")
            steps += factor_steps(total, "Numerator")
            if ff["cancelled"]:
                steps.append("Cancel: " + ", ".join(_paren(f) + (f"<sup>{e}</sup>" if e > 1 else "") for f, e in ff["cancelled"]))
            else:
                steps.append("Nothing cancels, so this is already in its simplest form.")
            ans = ff_html(ff, expand_num=not ff["cancelled"])
            steps.append(f"Answer: {ans}")
            r = _restrictions(dens)
            if r:
                steps.append(f"(Not allowed: {', '.join(r)} - they make a denominator zero.)")
            return _ok(steps, ans)

        # product / quotient / single fraction
        steps.append("<b>Step 1.</b> Factorise every numerator and denominator.")
        # flatten product chain
        nums, dns = [], []

        def flat(node, inv=False):
            k = node[0]
            if k == "mul":
                flat(node[1], inv)
                flat(node[2], inv)
            elif k == "div":
                flat(node[1], inv)
                flat(node[2], not inv)
            else:
                r_ = ast_eval(node)
                if inv:
                    r_ = r_.inv()
                    # inv() of RF returns RF(d, n) effectively
                nums.append(r_.n)
                dns.append(r_.d)
        flat(ast)
        if _has_fraction_division(ast):
            steps.append("Dividing by a fraction is the same as multiplying by its upside-down fraction (its reciprocal).")
        shown = []
        for n_, d_ in zip(nums, dns):
            shown.append(FR(poly_str(n_), poly_str(d_)) if not d_.is_const() or d_.const_value() != 1 else poly_str(n_))
        if len(shown) > 1:
            steps.append((" &times; ".join(shown)))
        for n_, d_ in zip(nums, dns):
            steps += factor_steps(n_, "Top") if not n_.is_const() else []
            if not d_.is_const():
                steps += factor_steps(d_, "Bottom")
        bigN, bigD = Poly.const(1), Poly.const(1)
        for n_ in nums:
            bigN = bigN * n_
        for d_ in dns:
            bigD = bigD * d_
        ff = ff_make(bigN, bigD)
        steps.append("<b>Step 2.</b> Multiply across, writing everything in factorised form, then cancel factors that are on the top <b>and</b> the bottom.")
        cn, fn_ = factor(bigN)
        cd, fd_ = factor(bigD)
        steps.append(f"{FR(factors_str(cn, fn_), factors_str(cd, fd_))}")
        if ff["cancelled"]:
            steps.append("Cancel: " + ", ".join(_paren(f) + (f"<sup>{e}</sup>" if e > 1 else "") for f, e in ff["cancelled"])
                         + (f" and the numbers (ratio {fr(ff['c'])})" if ff['c'] not in (1, -1) else ""))
        else:
            steps.append("Nothing cancels between the top and the bottom.")
        ans = ff_html(ff)
        steps.append(f"Answer: {ans}")
        exp = ff_html(ff, expand_num=True)
        if exp != ans and len(ff["num"]) > 0:
            steps.append(f"(Numerator multiplied out: {exp})")
        r = _restrictions(dens)
        if r:
            steps.append(f"(Not allowed: {', '.join(r)} - they make a denominator zero.)")
        steps = [s for s in steps if s]
        return _ok(steps, ans)
    except ParseError as e:
        return _fail(str(e))
    except RecursionError:
        return _fail("That expression is too complicated for this solver.")


# --------------------------------------------------------- solving ---------

def fmt_int(n):
    return str(n).replace('-', MINUS)


def _simp_surd(n):
    """sqrt(n) -> (k, m) with sqrt(n)=k*sqrt(m)"""
    k, m = 1, n
    f = 2
    while f * f <= m:
        while m % (f * f) == 0:
            k *= f
            m //= f * f
        f += 1
    return k, m


def _solve_quadratic(a, b, c, v, steps):
    """a,b,c Fractions; narrate and return list of solution strings + Fractions/None"""
    # integer-ise
    den = lcm(a.denominator, b.denominator, c.denominator)
    a, b, c = a * den, b * den, c * den
    g = gcd(gcd(int(abs(a)), int(abs(b))), int(abs(c))) or 1
    a, b, c = a / g, b / g, c / g
    if a < 0:
        a, b, c = -a, -b, -c
    A, B, C = int(a), int(b), int(c)
    D = B * B - 4 * A * C
    # try factorising
    p = Poly.from_uni([Fraction(C), Fraction(B), Fraction(A)], v)
    cc, fs = factor(p)
    lin = [f for f, e in fs if f.degree_in(v) == 1]
    if len(fs) >= 1 and all(f.degree_in(v) == 1 for f, _ in fs) and sum(e for _, e in fs) == 2:
        steps.append(f"Factorise: {factors_str(cc, fs)} = 0")
        roots = []
        for f, e in fs:
            co = f.to_uni(v)
            r = -co[0] / co[1]
            steps.append(f"{poly_str(f)} = 0 &nbsp;&rarr;&nbsp; {v} = {fr(r)}")
            roots.append(r)
        return roots
    steps.append(f"This does not factorise nicely, so use the quadratic formula. Here a = {A}, b = {B}, c = {C}.")
    steps.append(f"{v} = {FR(f'{MINUS}b &plusmn; &radic;(b<sup>2</sup> {MINUS} 4ac)', '2a')}")
    steps.append(f"b<sup>2</sup> {MINUS} 4ac = ({B})<sup>2</sup> {MINUS} 4({A})({C}) = {D}")
    if D < 0:
        steps.append("The number under the square root is negative, so there are <b>no real solutions</b>.")
        return []
    r = isqrt(D)
    if r * r == D:
        x1, x2 = Fraction(-B + r, 2 * A), Fraction(-B - r, 2 * A)
        steps.append(f"&radic;{D} = {r}")
        steps.append(f"{v} = {FR(f'{-B} + {r}', 2 * A)} = {fr(x1)} &nbsp;or&nbsp; {v} = {FR(f'{-B} {MINUS} {r}', 2 * A)} = {fr(x2)}")
        return [x1, x2]
    k, m = _simp_surd(D) if D <= 10 ** 12 else (1, D)
    root_txt = f"{k}&radic;{m}" if k > 1 else f"&radic;{m}"
    steps.append(f"&radic;{D} = {root_txt}")
    steps.append(f"{v} = {FR(f'{fmt_int(-B)} &plusmn; {root_txt}' if B else f'&plusmn; {root_txt}', 2 * A)}")
    # cancel any number common to the whole top and the bottom
    g = gcd(gcd(abs(B), k), 2 * A)
    B2, k2, den = B // g, k // g, (2 * A) // g
    if g > 1:
        steps.append(f"Divide the top and bottom by {g}:")
    rt = f"{k2}&radic;{m}" if k2 > 1 else f"&radic;{m}"
    plus_t = f"{fmt_int(-B2)} + {rt}" if B2 else rt
    minus_t = f"{fmt_int(-B2)} {MINUS} {rt}" if B2 else f"{MINUS}{rt}"
    d1 = (-B + D ** 0.5) / (2 * A)
    d2 = (-B - D ** 0.5) / (2 * A)

    def one(t):
        return t if den == 1 else FR(t, den)
    steps.append(f"{v} = {one(plus_t)} &nbsp;or&nbsp; {v} = {one(minus_t)}")
    steps.append(f"As decimals: {v} = {d1:.3f} or {v} = {d2:.3f}")
    return [("surd", one(plus_t), d1), ("surd", one(minus_t), d2)]


def alg_solve(equation, var=None):
    """Solve an equation containing algebraic fractions (or change the subject)"""
    try:
        eq = normalise(equation)
        if eq.count("=") != 1:
            return _fail("Type an equation with one '=' sign, e.g. x/2 + x/3 = 5 or (x+1)/(x-2) = 3.")
        ls, rs = [t.strip() for t in eq.split("=")]
        if not ls or not rs:
            return _fail("Both sides of the equation need something on them.")
        la, ra = parse_ast(ls), parse_ast(rs)
        letters = sorted(set(re.findall(r"[A-Za-z]", eq)))
        if not letters:
            return _fail("There is no letter to solve for.")
        if var:
            var = var.strip()[:1]
            if var not in letters:
                return _fail(f"The letter {esc(var)} is not in the equation.")
        else:
            var = "x" if "x" in letters else letters[0]
        steps = [f"Solve for <b>{var}</b>: {esc(ls)} = {esc(rs)}"]
        lterms = [(s, ast_eval(n)) for s, n in split_terms(la)]
        rterms = [(s, ast_eval(n)) for s, n in split_terms(ra)]
        allterms = lterms + rterms
        ffs = []
        for s, rf in allterms:
            f = ff_make(rf.n, rf.d)
            if s < 0:
                f["c"] = -f["c"]
            ffs.append(f)
        dens = [(f["c"].denominator, f["den"]) for f in ffs]
        lc, L = _lcd_from(dens)
        has_den = any(d[1] or d[0] != 1 for d in dens)
        if has_den:
            steps.append("<b>Step 1.</b> Find the LCM of all the denominators.")
            steps.append(f"LCM = {_lcd_html(lc, L)}")
            steps.append("<b>Step 2.</b> Multiply <b>every</b> term (both sides) by the LCM so the fractions disappear:")
        else:
            steps.append("There are no fractions to clear, so go straight to collecting terms.")
        sides = [0, 0]
        polys = []
        lh, rh = Poly(), Poly()
        for i, (f, (s, rf)) in enumerate(zip(ffs, allterms)):
            m = _mult_poly(lc, L, f["c"].denominator, f["den"])
            newp = _expanded_num(f) * m
            polys.append(newp)
            if i < len(lterms):
                lh = lh + newp
            else:
                rh = rh + newp
        if has_den:
            mult_txt = _lcd_html(lc, L)
            def side_txt(ps):
                return " + ".join(f"({poly_str(p)})" if len(p.t) > 1 else poly_str(p) for p in ps).replace("+ (&minus;", "&minus; (") if ps else "0"
            steps.append(f"Each term {MUL} LCM: {side_txt(polys[:len(lterms)])} = {side_txt(polys[len(lterms):])}")
        steps.append(f"Multiply out and tidy: {poly_str(lh)} = {poly_str(rh)}")
        eqp = lh - rh
        if eqp.is_zero():
            return _ok(steps, "This is true for every value (except any that make a denominator zero).")
        steps.append(f"<b>Step 3.</b> Move everything to one side: {poly_str(eqp)} = 0")
        deg = eqp.degree_in(var)
        if deg == 0:
            return _ok(steps, "There is no solution (the equation is never true).")
        others = [l for l in eqp.vars() if l != var]
        excl = _restrictions([f["den"] and _expanded_den(f) or Poly.const(1) for f in ffs])
        sols = []
        if deg == 1:
            # a*var + b = 0
            a = Poly(); b = Poly()
            for k, c in eqp.t.items():
                d = dict(k)
                e = d.pop(var, 0)
                part = Poly({tuple(sorted(d.items())): c})
                if e == 1:
                    a = a + part
                else:
                    b = b + part
            if not a.is_const() or a.const_value() not in (1, -1):
                acoef = _paren(a) if len(a.t) > 1 else poly_str(a)
                steps.append(f"Collect the {var} terms: {acoef}{var} = {poly_str(-b)}")
                steps.append(f"Divide both sides by {acoef}:")
            elif a.const_value() == 1:
                steps.append(f"Collect the {var} terms: {var} = {poly_str(-b)}")
            else:
                steps.append(f"Collect the {var} terms: {MINUS}{var} = {poly_str(-b)}")
                steps.append(f"Multiply both sides by {MINUS}1 (change every sign):")
            ff = ff_make(-b, a)
            ans_txt = ff_html(ff)
            steps.append(f"{var} = {ans_txt}")
            sols.append((None, ans_txt, ff, others))
            if not others:
                r = (-b.const_value()) / a.const_value()
                sols = [(r, fr(r), None, [])]
        elif deg == 2 and not others:
            co = eqp.to_uni(var)
            steps.append("It is a quadratic equation (the highest power is 2), so factorise or use the formula.")
            roots = _solve_quadratic(co[2], co[1], co[0], var, steps)
            for r in roots:
                if isinstance(r, tuple):
                    sols.append((None, r[1], r[2], []))
                else:
                    sols.append((r, fr(r), None, []))
        else:
            if others:
                return _fail("This solver can change the subject of a formula only when the letter appears to the first power. "
                             "Try a simpler formula or tell me which letter to solve for.")
            co = eqp.to_uni(var)
            c, fs = factor(eqp)
            lin = [f for f, e in fs if f.degree_in(var) == 1]
            steps.append(f"Factorise: {factors_str(c, fs)} = 0")
            for f in lin:
                cf = f.to_uni(var)
                r = -cf[0] / cf[1]
                steps.append(f"{poly_str(f)} = 0 &nbsp;&rarr;&nbsp; {var} = {fr(r)}")
                sols.append((r, fr(r), None, []))
            if not lin:
                return _fail("I could not find whole-number or fractional solutions for this higher-power equation.")
        # check restrictions
        good = []
        for r, txt, ff, oth in sols:
            bad = False
            if r is not None and isinstance(r, Fraction):
                for f in ffs:
                    dpoly = _expanded_den(f)
                    if dpoly.vars() == [var] or (dpoly.vars() and set(dpoly.vars()) <= {var}):
                        if dpoly.eval_at(var, r) == 0:
                            bad = True
            if bad:
                steps.append(f"<b>Check:</b> {var} = {txt} makes a denominator zero, so it is <b>rejected</b> (extraneous).")
            else:
                good.append((r, txt))
        if not good:
            return _ok(steps, "No valid solution.")
        if excl and has_den:
            steps.append(f"(Remember the values that are not allowed: {', '.join(excl)}.)")
        # verification for numeric single solutions
        for r, txt in good:
            if isinstance(r, Fraction) and not others:
                try:
                    lv = sum((s * (ast_eval(n).n.eval_at(var, r) / ast_eval(n).d.eval_at(var, r))) for s, n in split_terms(la))
                    rv = sum((s * (ast_eval(n).n.eval_at(var, r) / ast_eval(n).d.eval_at(var, r))) for s, n in split_terms(ra))
                    if lv == rv:
                        steps.append(f"<b>Check:</b> put {var} = {txt} back: left side = {fr(lv)}, right side = {fr(rv)} &#10003;")
                except (TypeError, ZeroDivisionError):
                    pass
        res = " &nbsp;or&nbsp; ".join(f"{var} = {t}" for _, t in good)
        return _ok(steps, res)
    except ParseError as e:
        return _fail(str(e))
