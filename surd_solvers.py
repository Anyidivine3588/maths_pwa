"""Surds engine (WAEC / NECO / JAMB): exact arithmetic on sums of radical monomials,
with detailed, child-friendly working. Pure Python."""
import math
import re
from fractions import Fraction

from log_core import (LogErr, parse, fmtq, sig, variables, ev_exact, vec_of, vec_to_q, to_poly, P1,
                      real_roots, pp, MINUS)
from log_solvers import _ok, _fail, guard, HL, solve_poly_steps
from ind_solvers import render_rat_rad, split_vec, qtext, vec_float, ipp

TIMES = " &times; "


# ====================================================================== exact radical sums
# value = {key: coef}, key = tuple(sorted((prime, Fraction r))) with 0 < r < 1   (key () = rational part)
def key_vec(key):
    return {p: r for p, r in key}


def mono_vec(coef, key):
    """prime vector of |coef| * radical"""
    v = vec_of(abs(coef))
    if v is None:
        raise LogErr("A number in your expression is too large for this tool.")
    out = dict(v)
    for p, r in key:
        out[p] = out.get(p, 0) + r
    return {p: e for p, e in out.items() if e}


def mul_mono(a, b):
    """(coef, key) x (coef, key) -> (coef, key)"""
    ca, ka = a
    cb, kb = b
    vec = {}
    for p, r in ka:
        vec[p] = vec.get(p, 0) + r
    for p, r in kb:
        vec[p] = vec.get(p, 0) + r
    q, rad = split_vec(vec)
    return ca * cb * q, tuple(sorted(rad.items()))


def inv_mono(a):
    c, k = a
    if c == 0:
        raise LogErr("You cannot divide by zero.")
    vec = {p: -r for p, r in k}
    q, rad = split_vec(vec)
    return (1 / c) * q, tuple(sorted(rad.items()))


class Sx:
    def __init__(self, d=None):
        self.d = {k: Fraction(c) for k, c in (d or {}).items() if c != 0}

    @staticmethod
    def q(x):
        return Sx({(): Fraction(x)})

    @staticmethod
    def rad(coef, vec):
        q, rad = split_vec(vec)
        return Sx({tuple(sorted(rad.items())): Fraction(coef) * q})

    def terms(self):
        return sorted(self.d.items(), key=lambda kv: (len(kv[0]) > 0, _kval(kv[0])))

    def __add__(self, o):
        out = dict(self.d)
        for k, c in o.d.items():
            out[k] = out.get(k, 0) + c
        return Sx(out)

    def __neg__(self):
        return Sx({k: -c for k, c in self.d.items()})

    def __sub__(self, o):
        return self + (-o)

    def __mul__(self, o):
        out = {}
        for ka, ca in self.d.items():
            for kb, cb in o.d.items():
                c, k = mul_mono((ca, ka), (cb, kb))
                out[k] = out.get(k, 0) + c
        return Sx(out)

    def scale(self, q):
        return Sx({k: c * Fraction(q) for k, c in self.d.items()})

    def is_zero(self):
        return not self.d

    def is_rational(self):
        return all(k == () for k in self.d)

    def rational(self):
        return self.d.get((), Fraction(0))

    def float(self):
        return sum(float(c) * vec_float(key_vec(k)) for k, c in self.d.items())

    def single(self):
        if len(self.d) == 1:
            k, c = next(iter(self.d.items()))
            return c, k
        return None


def _kval(key):
    return vec_float(key_vec(key)) if key else 0.0


def term_text(c, k):
    return render_rat_rad(c, key_vec(k)) if k else qtext(c)


def sx_text(S):
    if S.is_zero():
        return "0"
    ts = S.terms()
    dens = [c.denominator for _k, c in ts]
    if len(ts) > 1 and any(d > 1 for d in dens):
        L = 1
        for d in dens:
            L = L * d // math.gcd(L, d)
        inner = ""
        for i, (k, c) in enumerate(ts):
            cc = c * L
            t_ = term_text(abs(cc), k)
            inner += (MINUS if cc < 0 else "") + t_ if i == 0 else (" &minus; " if cc < 0 else " + ") + t_
        return f"({inner})/{L}"
    out = ""
    for i, (k, c) in enumerate(S.terms()):
        t = term_text(abs(c), k)
        if i == 0:
            out += (MINUS if c < 0 else "") + t
        else:
            out += (" &minus; " if c < 0 else " + ") + t
    return out


def term_br(c, k):
    t = term_text(c, k)
    return f"({t})" if c < 0 else t


def sx_float_note(S, given=True):
    return sig(S.float(), 4)


GIVEN = {2: 1.414, 3: 1.732, 5: 2.236, 6: 2.449, 7: 2.646}


# ====================================================================== radical simplification narration
def is_square_free_int(n):
    v = vec_of(Fraction(n))
    return v is not None and all(e == 1 for e in v.values())


def factor_text(n):
    v = vec_of(Fraction(n)) or {}
    parts = []
    for p, e in sorted(v.items()):
        parts += [str(p)] * int(e)
    return TIMES.join(parts) if parts else "1"


def root_word(k):
    return {2: "square root", 3: "cube root", 4: "fourth root", 5: "fifth root"}.get(k, f"{k}th root")


def rootsym(k):
    return "&radic;" if k == 2 else ("&#8731;" if k == 3 else ("&#8732;" if k == 4 else f"<sup>{k}</sup>&radic;"))


def rt(k, n):
    n = str(n)
    return f"{rootsym(k)}{n if (len(n) < 4 and '/' not in n and '.' not in n) else '(' + n + ')'}"


def leaf_label(lf, kk, arg):
    a = ev_exact(arg)
    return rt(kk, qtext(a)) if a is not None else ipp(lf)


def leaf_steps(N, k, detailed):
    """explain the k-th root of rational N>0.  Returns list of step strings."""
    N = Fraction(N)
    steps = []
    if N.denominator != 1:
        a, b = N.numerator, N.denominator
        steps.append(f"The root of a fraction is the root of the top over the root of the bottom: {rt(k, qtext(N))} = {rt(k, a)} / {rt(k, b)}")
        steps += leaf_steps(Fraction(a), k, detailed)
        steps += leaf_steps(Fraction(b), k, detailed)
        return steps
    n = N.numerator
    v = vec_of(N)
    if n == 1:
        return [f"{rt(k, 1)} = 1"]
    big = 1
    for p, e in v.items():
        big *= p ** (k * (e // k))
    rest = n // big
    root_out = round(big ** (1 / k))
    sw = root_word(k)
    if detailed:
        steps.append(f"<b>Break {n} into prime factors:</b> {n} = {factor_text(n)}")
    if big == 1:
        steps.append(f"{rt(k, n)} is already in its simplest form: {n} has no factor that is a perfect {'square' if k == 2 else 'cube' if k == 3 else str(k) + 'th power'}, so nothing can come out of the root.")
        return steps
    if detailed:
        if k == 2:
            steps.append("A square root <i>pairs up</i> equal factors: each pair comes out of the root as a single number.")
        else:
            steps.append(f"A {sw} takes out equal groups of {k}: each group of {k} equal factors comes out as a single number.")
    pf = f"{big} &times; {rest}" if rest != 1 else f"{big}"
    steps.append(f"<b>Find the largest perfect {'square' if k == 2 else 'cube' if k == 3 else str(k) + 'th power'} that divides {n}:</b> {n} = {pf}"
                 + (f" (because {root_out}<sup>{k}</sup> = {big})" if True else ""))
    if rest != 1:
        steps.append(f"{rt(k, n)} = {rt(k, big)} &times; {rt(k, rest)} = {root_out} &times; {rt(k, rest)} = {HL(str(root_out) + rt(k, rest))}")
    else:
        steps.append(f"{rt(k, n)} = {HL(str(root_out))}")
    return steps


# ====================================================================== evaluation with narration
class Ctx:
    def __init__(self, detailed=False):
        self.steps = []
        self.detailed = detailed
        self.simplified_leaves = set()


def _leaf_nodes(node, out):
    k = node[0]
    if k == "sqrt":
        if not variables(node[1]):
            out.append((node, 2, node[1]))
        return out
    if k == "pow":
        if not variables(node[1]) and not variables(node[2]):
            e = ev_exact(node[2])
            if e is not None and e.denominator != 1:
                out.append((node, e.denominator, node[1]))
                return out
        _leaf_nodes(node[1], out)
        return out
    if k in ("neg",):
        _leaf_nodes(node[1], out)
    elif k in ("add", "sub", "mul", "div"):
        _leaf_nodes(node[1], out)
        _leaf_nodes(node[2], out)
    return out


def prepass(node, ctx):
    """narrate the simplification of every individual radical in the expression"""
    leaves = _leaf_nodes(node, [])
    seen = set()
    lines = []
    single = len(leaves) == 1 and (node[0] in ("sqrt", "pow") or (node[0] == "neg" and node[1][0] in ("sqrt", "pow")) or (node[0] in ("mul", "div")))
    single = len(leaves) == 1 and node[0] in ("sqrt", "pow")
    for lf, kk, arg in leaves:
        key = ipp(lf)
        if key in seen:
            continue
        seen.add(key)
        try:
            S = ev(lf, Ctx())
        except LogErr:
            continue
        argv = ev_exact(arg)
        if argv is None:
            continue
        old = leaf_label(lf, kk, arg)
        new = sx_text(S)
        if ctx.detailed:
            sub = leaf_steps(argv, kk, True)
            if new == old and not single:
                continue
            ctx.steps.append(f"<b>Simplify {old}:</b><br>" + "<br>".join(sub))
        else:
            if new != old:
                lines.append(_brief(lf, kk, argv, new))
    if lines:
        ctx.steps.append("<b>Simplify each surd first</b> (take out any perfect squares):<br>" + "<br>".join(lines))


def _brief(lf, kk, argv, new):
    old = rt(kk, qtext(argv))
    if isinstance(argv, Fraction) and argv.denominator == 1:
        n = argv.numerator
        v = vec_of(argv)
        big = 1
        for p, e in v.items():
            big *= p ** (kk * (e // kk))
        rest = n // big
        if big > 1 and rest > 1:
            return f"{old} = {rt(kk, big)} &times; {rt(kk, rest)} = {new}"
        if big > 1:
            return f"{old} = {new}"
    return f"{old} = {new}"


def ev(node, ctx):
    """node -> Sx (exact), narrating in ctx.steps"""
    k = node[0]
    if k == "num":
        return Sx.q(node[1])
    if k == "var":
        raise LogErr("There is a letter in this expression. Use the <b>Solve an equation</b> tab for equations with x.")
    if k == "const":
        raise LogErr("I can only work with whole numbers, fractions and roots here.")
    if k == "neg":
        return -ev(node[1], ctx)
    if k in ("add", "sub"):
        return ev_sum(node, ctx)
    if k == "mul":
        return ev_mul(node, ctx)
    if k == "div":
        return ev_div(node, ctx)
    if k == "sqrt":
        return sx_root(ev(node[1], Ctx()), 2, ctx)
    if k == "pow":
        return ev_pow(node, ctx)
    raise LogErr("I can only simplify numbers and roots here (no logs).")


def sx_root(S, kk, ctx):
    if S.is_zero():
        return Sx()
    one = S.single()
    if one:
        c, key = one
        if c < 0:
            raise LogErr("The root of a negative number is not a real number, so the expression has no real value.")
        vec = mono_vec(c, key)
        v2 = {p: e / kk for p, e in vec.items()}
        return Sx.rad(1, v2)
    if kk == 2:
        d = denest(S)
        if d is not None:
            if ctx is not None:
                ctx.steps.append(f"<b>Square root of a sum:</b> &radic;({sx_text(S)}) is <i>not</i> &radic;a + &radic;b in general. Here it can be written as a perfect square: ({sx_text(d)})<sup>2</sup> = {sx_text(d * d)}, so &radic;({sx_text(S)}) = {HL(sx_text(d))}")
            return d
    raise LogErr(f"I cannot simplify the root of a sum like &radic;({sx_text(S)}). Remember &radic;(a + b) is <b>not</b> &radic;a + &radic;b. If you meant to square or multiply first, use brackets.")


def denest(S):
    """sqrt(a + b sqrt c) as p + q sqrt c when possible"""
    if len(S.d) != 2 or () not in S.d:
        return None
    a = S.d[()]
    (k, b), = [(k, c) for k, c in S.d.items() if k != ()]
    if len(k) < 1 or any(r != Fraction(1, 2) for _, r in k):
        return None
    c = vec_to_q({p: 2 * r for p, r in k})
    disc = a * a - b * b * c
    if disc < 0:
        return None
    s = _rat_sqrt(disc)
    if s is None:
        return None
    for sg in (1, -1):
        x = (a + sg * s) / 2
        if x < 0:
            continue
        y = b / (2 * _rat_sqrt(x)) if _rat_sqrt(x) not in (None, 0) else None
        if y is not None:
            cand = Sx.q(_rat_sqrt(x)) + Sx({k: y})
            if (cand * cand - S).is_zero():
                return cand
    return None


def _rat_sqrt(q):
    q = Fraction(q)
    if q < 0:
        return None
    n, d = math.isqrt(q.numerator), math.isqrt(q.denominator)
    if n * n == q.numerator and d * d == q.denominator:
        return Fraction(n, d)
    return None


def ev_sum(node, ctx):
    terms = []
    _flat(node, 1, terms)
    vals = []
    for sg, t in terms:
        v = ev(t, ctx)
        vals.append((sg, v))
    total = Sx()
    for sg, v in vals:
        total = total + (v if sg > 0 else -v)
    # narrate merges
    groups = {}
    order = []
    for sg, v in vals:
        for key, c in v.d.items():
            groups.setdefault(key, []).append(sg * c)
            if key not in order:
                order.append(key)
    merged = [key for key in order if len(groups[key]) > 1]
    if merged:
        lines = []
        for key in sorted(merged, key=lambda kk: (len(kk) > 0, _kval(kk))):
            cs = groups[key]
            unit = "" if key == () else render_rat_rad(Fraction(1), key_vec(key))
            parts = ""
            for i, c in enumerate(cs):
                body = term_text(abs(c), key)
                parts += (MINUS if c < 0 else "") + body if i == 0 else (" &minus; " if c < 0 else " + ") + body
            if key == ():
                lines.append(f"<b>numbers:</b> {parts} = {qtext(sum(cs))}")
            else:
                coefs = ""
                for i, c in enumerate(cs):
                    t = qtext(abs(c))
                    coefs += (MINUS if c < 0 else "") + t if i == 0 else (" &minus; " if c < 0 else " + ") + t
                tot = sum(cs)
                lines.append(f"<b>{unit} terms</b> (like surds &mdash; same number under the root, so we add the numbers in front): {parts} = ({coefs}){unit} = {term_text(tot, key) if tot != 0 else '0'}")
        ctx.steps.append("<b>Collect like terms</b> (only surds with the <i>same</i> root can be added or subtracted):<br>" + "<br>".join(lines))
    elif len(terms) > 1 and len(total.d) > 1 and node is getattr(ctx, "top", None):
        ctx.steps.append("The surds are all different (different numbers under the roots), so they <b>cannot</b> be added together. The answer stays as a sum.")
    return total


def _flat(node, sign, out):
    if node[0] == "add":
        _flat(node[1], sign, out)
        _flat(node[2], sign, out)
    elif node[0] == "sub":
        _flat(node[1], sign, out)
        _flat(node[2], -sign, out)
    else:
        out.append((sign, node))


def _flat_mul(node, out):
    if node[0] == "mul":
        _flat_mul(node[1], out)
        _flat_mul(node[2], out)
    else:
        out.append(node)


def ev_mul(node, ctx):
    factors = []
    _flat_mul(node, factors)
    acc = ev(factors[0], ctx)
    for f in factors[1:]:
        b = ev(f, ctx)
        acc = narrate_mul(acc, b, ctx, factors_text=(ipp(factors[0]) if False else None))
    return acc


def _sum_text_from(S):
    return sx_text(S)


def narrate_mul(A, B, ctx, factors_text=None):
    ta, tb = A.terms(), B.terms()
    if A.is_zero() or B.is_zero():
        return Sx()
    # rational x anything: scalar multiplication, no narration
    if A.is_rational() and len(ta) == 1 and abs(ta[0][1]) == 1 and False:
        return B.scale(ta[0][1])
    if len(ta) == 1 and len(tb) == 1:
        (ka, ca), (kb, cb) = ta[0], tb[0]
        c, k = mul_mono((ca, ka), (cb, kb))
        if ka or kb:
            ctx.steps.append(_mono_mul_text(ca, ka, cb, kb, c, k))
        return Sx({k: c})
    # same expression squared -> identity
    prods = []
    for ka, ca in ta:
        for kb, cb in tb:
            c, k = mul_mono((ca, ka), (cb, kb))
            prods.append((ka, ca, kb, cb, c, k))
    res = Sx()
    for *_x, c, k in prods:
        res = res + Sx({k: c})
    if (A - B).is_zero() and len(ta) == 2:
        (k1, c1), (k2, c2) = ta
        s1, s2 = Sx({k1: c1}), Sx({k2: c2})
        sq1, sq2 = s1 * s1, s2 * s2
        cross = (s1 * s2).scale(2)
        ctx.steps.append(
            f"<b>Square of a bracket:</b> (a + b)<sup>2</sup> = a<sup>2</sup> + 2ab + b<sup>2</sup>, with a = {term_text(c1, k1)} and b = {term_br(c2, k2)}:<br>"
            f"a<sup>2</sup> = ({term_text(c1, k1)})<sup>2</sup> = {sx_text(sq1)}<br>"
            f"2ab = 2 &times; {term_text(c1, k1)} &times; {term_br(c2, k2)} = {sx_text(cross)}<br>"
            f"b<sup>2</sup> = ({term_text(c2, k2)})<sup>2</sup> = {sx_text(sq2)}<br>"
            f"Add them: {sx_text(sq1)} {('+ ' + sx_text(cross)) if not sx_text(cross).startswith(MINUS) else '&minus; ' + sx_text(cross)[len(MINUS):]} {('+ ' + sx_text(sq2)) if not sx_text(sq2).startswith(MINUS) else '&minus; ' + sx_text(sq2)[len(MINUS):]} = {HL(sx_text(res))}")
        return res
    # conjugates
    if len(ta) == 2 and len(tb) == 2 and set(k for k, _ in ta) == set(k for k, _ in tb):
        (a1, b1), (a2, b2) = ta
        (c1, d1), (c2, d2) = tb
        if (a1 == c1 and a2 == c2 and b1 == d1 and b2 == -d2) or (a1 == c1 and a2 == c2 and b1 == -d1 and b2 == d2):
            ctx.steps.append(
                f"<b>Difference of two squares:</b> these brackets are <i>conjugates</i> (same terms, opposite sign in the middle), so (a + b)(a &minus; b) = a<sup>2</sup> &minus; b<sup>2</sup>. "
                f"Here a<sup>2</sup> = {sx_text(Sx({a1: b1}) * Sx({a1: b1}))} and b<sup>2</sup> = {sx_text(Sx({a2: b2}) * Sx({a2: b2}))}, giving {HL(sx_text(res))}"
                f" &nbsp;(the middle terms cancel, so no root is left).")
            return res
    # general expansion
    lines = []
    firsts = 0
    for ka, ca, kb, cb, c, k in prods:
        lines.append(f"{term_br(ca, ka)} &times; {term_br(cb, kb)} = {term_text(c, k) if c >= 0 else MINUS + term_text(-c, k)}")
    how = "Multiply <b>every term</b> in the first bracket by <b>every term</b> in the second bracket (FOIL: First, Outer, Inner, Last):" if len(ta) == 2 and len(tb) == 2 else "Multiply every term inside the brackets:"
    ctx.steps.append(f"<b>Expand the brackets.</b> {how}<br>" + "<br>".join(lines))
    allt = "".join((" &minus; " if c < 0 else " + ") + term_text(abs(c), k) if i else (MINUS if c < 0 else "") + term_text(abs(c), k) for i, (*_y, c, k) in enumerate(prods))
    # collection narrated in ev_sum-like way
    groups = {}
    for *_y, c, k in prods:
        groups.setdefault(k, []).append(c)
    if any(len(v) > 1 for v in groups.values()):
        ctx.steps.append(f"Put the answers together: {allt}")
        lines2 = []
        for key in sorted(groups, key=lambda kk: (len(kk) > 0, _kval(kk))):
            cs = groups[key]
            if len(cs) > 1:
                unit = render_rat_rad(Fraction(1), key_vec(key)) if key else ""
                parts = ""
                for i, c in enumerate(cs):
                    parts += (MINUS if c < 0 else "") + qtext(abs(c)) if i == 0 else (" &minus; " if c < 0 else " + ") + qtext(abs(c))
                tot = sum(cs)
                if key == ():
                    lines2.append(f"numbers: {parts} = {qtext(tot)}")
                else:
                    lines2.append(f"{unit} terms: ({parts}){unit} = {term_text(tot, key) if tot else '0'}")
        ctx.steps.append("<b>Collect like terms:</b><br>" + "<br>".join(lines2) + f"<br>Result: {HL(sx_text(res))}")
    else:
        ctx.steps.append(f"Result: {HL(sx_text(res))}")
    return res


def _mono_mul_text(ca, ka, cb, kb, c, k):
    out = []
    if ca != 1 or cb != 1:
        if ca != 1 and cb != 1:
            out.append(f"Multiply the numbers in front: {qtext(ca)} &times; {qtext(cb)} = {qtext(ca * cb)}")
    ra = render_rat_rad(Fraction(1), key_vec(ka)) if ka else None
    rb = render_rat_rad(Fraction(1), key_vec(kb)) if kb else None
    if ra and rb:
        vec = {}
        for p, r in list(ka) + list(kb):
            vec[p] = vec.get(p, 0) + r
        q, rad = split_vec(vec)
        merged_n = vec_to_q({p: 2 * e for p, e in vec.items()}) if all(Fraction(e).denominator <= 2 for e in vec.values()) else None
        if all(Fraction(r).denominator == 2 for _, r in list(ka) + list(kb)) and merged_n is not None:
            out.append(f"Multiply the roots (&radic;a &times; &radic;b = &radic;(a &times; b)): {ra} &times; {rb} = &radic;({qtext(merged_n)}) = {render_rat_rad(q, rad) if rad or q != 1 else qtext(q)}")
        else:
            out.append(f"Multiply the roots: {ra} &times; {rb} = {render_rat_rad(q, rad) if rad or q != 1 else qtext(q)}")
    elif ra or rb:
        pass
    final = f"{term_br(ca, ka)} &times; {term_br(cb, kb)} = {HL(term_text(c, k) if c >= 0 else MINUS + term_text(-c, k))}"
    return "<b>Multiply:</b> " + ("; ".join(out) + ". " if out else "") + final


def ev_pow(node, ctx):
    ex = ev_exact(node[2]) if not variables(node[2]) else None
    if ex is None:
        raise LogErr("The power must be a plain number like 2 or 1/3.")
    if ex.denominator != 1:
        # root of base
        base = ev(node[1], Ctx())
        one = base.single()
        if one and one[0] > 0:
            vec = mono_vec(one[0], one[1])
            return Sx.rad(1, {p: e * ex for p, e in vec.items()})
        if ex == Fraction(1, 2):
            return sx_root(base, 2, ctx)
        raise LogErr("I can only take fractional powers of a single positive number here.")
    n = int(ex)
    base = ev(node[1], ctx)
    if n == 0:
        return Sx.q(1)
    if n < 0:
        base = inv_sx(base, ctx)
        n = -n
    if n > 6:
        raise LogErr("That power is too big for this tool (use 6 or less).")
    if n == 1:
        return base
    acc = base
    if len(base.d) == 1 and (list(base.d)[0] != () or True):
        (k, c), = base.d.items()
        if k:
            res = base
            for _ in range(n - 1):
                res = res * base
            ctx.steps.append(f"<b>Power of a surd:</b> raise <i>both</i> the number in front and the root: ({term_text(c, k)})<sup>{n}</sup> = {qtext(c)}<sup>{n}</sup> &times; ({render_rat_rad(Fraction(1), key_vec(k))})<sup>{n}</sup> = {qtext(c ** n)} &times; {sx_text(Sx.rad(1, mono_vec(1, k)) * Sx.q(1) if False else _pw(k, n))} = {HL(sx_text(res))}")
            return res
        return base * Sx.q(1) if False else Sx.q(c ** n)
    for i in range(n - 1):
        acc = narrate_mul(acc, base, ctx)
    return acc


def _pw(k, n):
    s = Sx({k: Fraction(1)})
    r = s
    for _ in range(n - 1):
        r = r * s
    return r


def inv_sx(S, ctx):
    one = S.single()
    if one:
        c, k = one
        return Sx({inv_mono((c, k))[1]: inv_mono((c, k))[0]})
    raise LogErr("A negative power of a sum is not supported; write it as a fraction instead.")


def ev_div(node, ctx):
    A = ev(node[1], ctx)
    D = ev(node[2], ctx)
    if D.is_zero():
        raise LogErr("You cannot divide by zero.")
    return rationalise(A, D, ctx, top=node[1], bottom=node[2])


def _ordered_text(tl):
    out = ""
    for i, (sg, v) in enumerate(tl):
        body = sx_text(v if v.float() >= 0 else -v)
        neg = (sg < 0) != (v.float() < 0)
        if i == 0:
            out += (MINUS if neg else "") + body
        else:
            out += (" &minus; " if neg else " + ") + body
    return out


def rationalise(A, D, ctx, top=None, bottom=None):
    """A / D with D possibly irrational. Returns Sx."""
    if D.is_rational():
        q = D.rational()
        res = A.scale(1 / q)
        return res
    one = D.single()
    if one:
        c, k = one
        # multiply top and bottom by M where radical*M is rational
        vec = key_vec(k)
        M = {p: 1 - r for p, r in vec.items()}
        Msx = Sx.rad(1, M)
        ntext = render_rat_rad(Fraction(1), M)
        den = Sx({k: c}) * Msx
        num = A * Msx
        ctx.steps.append(
            f"<b>Rationalise the denominator</b> (remove the root from the bottom). The bottom is {term_text(c, k)}. "
            f"Multiply the top <i>and</i> the bottom by {ntext} &mdash; this does not change the value, because {ntext}/{ntext} = 1. "
            f"On the bottom: {term_br(c, k)} &times; {ntext} = {qtext(den.rational())} (a root times itself loses its root sign).<br>"
            f"On the top: ({sx_text(A)}) &times; {ntext} = {sx_text(num)}")
        res = num.scale(1 / den.rational())
        if den.rational() != 1:
            ctx.steps.append(f"So {HL(sx_text(num) + ' / ' + qtext(den.rational()))} &nbsp;&rarr;&nbsp; divide every term on top by {qtext(den.rational())}: {HL(sx_text(res))}")
        return res
    # binomial / multi-term denominator: conjugates
    num, den = A, D
    typed = None
    if bottom is not None:
        fl = []
        _flat(bottom, 1, fl)
        if len(fl) >= 2:
            typed = [(sg, ev(t_, Ctx())) for sg, t_ in fl]
            if not (sum((v if sg > 0 else -v for sg, v in typed), Sx()) - D).is_zero():
                typed = None
    for rounds in range(4):
        if den.is_rational():
            break
        if rounds == 0 and typed:
            tl = [(sg, v) for sg, v in typed]
            tl[-1] = (-tl[-1][0], tl[-1][1])
            conj = sum((v if sg > 0 else -v for sg, v in tl), Sx())
            den_txt = ipp(bottom)
            conj_txt = _ordered_text(tl)
            two = [(v if sg > 0 else -v) for sg, v in typed] if len(typed) == 2 else None
        else:
            ts = den.terms()
            flip_key = [k for k, _ in ts if k][-1]
            conj = Sx({k: (-c if k == flip_key else c) for k, c in den.d.items()})
            den_txt = sx_text(den)
            conj_txt = sx_text(conj)
            two = None
            if len(ts) == 2:
                two = [Sx({k: c}) for k, c in ts]
        newden = den * conj
        ctx.steps.append(
            f"<b>Rationalise using the conjugate.</b> The bottom is {den_txt}. Its <i>conjugate</i> is the same terms with the sign of the last term changed: {HL(conj_txt)}. "
            f"Multiply the top <i>and</i> the bottom by the conjugate (this does not change the value).")
        if two:
            s1, s2 = (two[0], two[1]) if rounds == 0 and typed else (two[0], two[1])
            s2a = s2 if (s2.float() >= 0) else -s2
            sq1, sq2 = s1 * s1, s2a * s2a
            ctx.steps.append(
                f"<b>Bottom:</b> (a + b)(a &minus; b) = a<sup>2</sup> &minus; b<sup>2</sup>. Here a = {sx_text(s1)} and b = {sx_text(s2a)}, so a<sup>2</sup> = {sx_text(sq1)} and b<sup>2</sup> = {sx_text(sq2)}: "
                f"{sx_text(sq1)} &minus; {sx_text(sq2) if not sq2.rational() or sq2.rational() >= 0 else '(' + sx_text(sq2) + ')'} = {HL(sx_text(newden))}")
        else:
            ctx.steps.append(f"<b>Bottom:</b> ({den_txt})({conj_txt}) = {HL(sx_text(newden))}")
        sub = Ctx()
        newnum = narrate_mul(num, conj, sub)
        top_txt = ipp(top) if (rounds == 0 and top is not None) else sx_text(num)
        ctx.steps.append(f"<b>Top:</b> multiply out ({top_txt}) &times; ({conj_txt}):")
        ctx.steps.extend(sub.steps)
        num, den = newnum, newden
    if not den.is_rational():
        raise LogErr("This denominator is too complicated to rationalise with this tool.")
    q = den.rational()
    res = num.scale(1 / q)
    if q != 1:
        ctx.steps.append(f"Now the bottom is the whole number {qtext(q)}. Divide every term on top by {qtext(q) if q > 0 else '(' + qtext(q) + ')'}: ({sx_text(num)}) &divide; {qtext(q) if q > 0 else '(' + qtext(q) + ')'} = {HL(sx_text(res))}")
    return res


# ====================================================================== public functions
def _preprocess(text):
    text = str(text or "").strip()
    if not text:
        raise LogErr("Please type an expression, for example <b>&radic;50</b> or <b>(2 + &radic;3)(4 &minus; &radic;3)</b>.")
    t = re.sub(r"\broot\s*\(", "sqrt(", text)
    t = t.replace("∛", "cbrt").replace("∜", "qrt4")
    for name, k in (("cbrt", 3), ("qrt4", 4)):
        while name in t:
            i = t.index(name)
            j = i + len(name)
            while j < len(t) and t[j] == " ":
                j += 1
            if j < len(t) and t[j] == "(":
                depth, m = 0, j
                while m < len(t):
                    depth += (t[m] == "(") - (t[m] == ")")
                    if depth == 0:
                        break
                    m += 1
                arg = t[j:m + 1]
                t = t[:i] + f"({arg})^(1/{k})" + t[m + 1:]
            else:
                m = j
                while m < len(t) and (t[m].isdigit() or t[m] == "."):
                    m += 1
                t = t[:i] + f"({t[j:m]})^(1/{k})" + t[m:]
    t = re.sub(r"\bcbrt\b", "cbrt", t)
    return t


def _final(S, ctx, src_node, extra=True):
    txt = sx_text(S)
    steps = ctx.steps
    if S.is_rational() or S.is_zero():
        return steps, txt
    if extra:
        approx = sig(S.float(), 4)
        steps.append(f"<b>Answer:</b> {HL(txt)} &nbsp;(&asymp; {approx})")
        # calculator-style with the usual given values
        radicands = set()
        for k, _c in S.d.items():
            for p, r in k:
                radicands.add(p)
        if radicands and all(p in GIVEN for p in radicands) and all(len(k) == 1 and k[0][1] == Fraction(1, 2) for k in S.d if k):
            subs = ", ".join(f"&radic;{p} = {GIVEN[p]}" for p in sorted(radicands))
            val = 0.0
            for k, c in S.d.items():
                if k == ():
                    val += float(c)
                else:
                    p = k[0][0]
                    val += float(c) * GIVEN[p]
            steps.append(f"<b>If the question gives {subs}</b> (as WAEC/JAMB often do), substitute: {txt} = {sig(val, 4)}")
    return steps, txt


@guard
def simplify(expr):
    text = _preprocess(expr)
    node = parse(text)
    ctx = Ctx(detailed=True)
    ctx.steps.append(f"<b>Expression:</b> {ipp(node)}")
    ctx.top = node
    prepass(node, ctx)
    S = ev(node, ctx)
    ctx.steps, txt = _final(S, ctx, node)
    if S.is_rational() or S.is_zero():
        ctx.steps.append(f"<b>Answer:</b> {HL(txt)}")
    return _ok(ctx.steps, txt + (f" &asymp; {sig(S.float(), 4)}" if not S.is_rational() and len(S.d) == 1 else ""))


@guard
def arithmetic(expr):
    text = _preprocess(expr)
    node = parse(text)
    ctx = Ctx(detailed=False)
    ctx.steps.append(f"<b>Expression:</b> {ipp(node)}")
    ctx.top = node
    prepass(node, ctx)
    S = ev(node, ctx)
    ctx.steps, txt = _final(S, ctx, node)
    if S.is_rational() or S.is_zero():
        ctx.steps.append(f"<b>Answer:</b> {HL(txt)}")
    return _ok(ctx.steps, txt + (f" &asymp; {sig(S.float(), 4)}" if not S.is_rational() and len(S.d) == 1 else ""))


@guard
def rationalise_expr(expr):
    text = _preprocess(expr)
    node = parse(text)
    if node[0] != "div":
        # maybe a sum of fractions or something else: just evaluate with narration
        return arithmetic(expr)
    ctx = Ctx(detailed=False)
    ctx.steps.append(f"<b>Expression:</b> {ipp(node)}")
    ctx.top = node
    ctx.steps.append("<b>Rationalising</b> means rewriting the fraction so that there is <i>no root on the bottom</i>. A fraction with a surd on the bottom is not considered fully simplified in WAEC/NECO/JAMB.")
    prepass(node, ctx)
    S = ev(node, ctx)
    ctx.steps, txt = _final(S, ctx, node)
    # a + b sqrt c form
    if len(S.d) == 2 and () in S.d:
        (k, b), = [(k, c) for k, c in S.d.items() if k != ()]
        a = S.d[()]
        ctx.steps.append(f"<b>In the form p + q&radic;r:</b> p = {qtext(a)}, q = {qtext(b)}, r = {qtext(vec_to_q({pp_: 2 * rr for pp_, rr in k}) if all(Fraction(rr).denominator == 2 for _, rr in k) else 0) if all(Fraction(rr).denominator == 2 for _, rr in k) else '?'}. (Useful when the question says &ldquo;express in the form p + q&radic;r&rdquo; or &ldquo;find p and q&rdquo;.)")
    elif S.is_rational() or S.is_zero():
        ctx.steps.append(f"<b>Answer:</b> {HL(txt)}")
    return _ok(ctx.steps, txt)


# ====================================================================== equations with roots
def _has_sqrt(node):
    k = node[0]
    if k == "sqrt":
        return True
    if k in ("neg",):
        return _has_sqrt(node[1])
    if k in ("add", "sub", "mul", "div", "pow"):
        return _has_sqrt(node[1]) or _has_sqrt(node[2])
    return False


def _split_rad(node, v):
    """node -> (P1 polynomial part, [(k Fraction, R P1)])"""
    k = node[0]
    if not _has_sqrt(node):
        return to_poly(node, v), []
    if k == "sqrt":
        R = to_poly(node[1], v) if not _has_sqrt(node[1]) else None
        if R is None:
            raise LogErr("A root inside another root is too complicated for this tool.")
        if R.deg() == 0:
            return P1.const(0), [(math.sqrt(float(R.c[0])) if False else Fraction(1), R)]
        return P1.const(0), [(Fraction(1), R)]
    if k == "neg":
        P, rs = _split_rad(node[1], v)
        return -P, [(-c, R) for c, R in rs]
    if k in ("add", "sub"):
        P1_, r1 = _split_rad(node[1], v)
        P2_, r2 = _split_rad(node[2], v)
        if k == "sub":
            return P1_ - P2_, r1 + [(-c, R) for c, R in r2]
        return P1_ + P2_, r1 + r2
    if k == "mul":
        for a, b in ((node[1], node[2]), (node[2], node[1])):
            if not _has_sqrt(a) and not variables(a):
                c = ev_exact(a)
                if c is None:
                    break
                P, rs = _split_rad(b, v)
                return P.scale(c), [(cc * c, R) for cc, R in rs]
        if node[1][0] == "sqrt" and node[2] == node[1]:
            return to_poly(node[1][1], v), []
        raise LogErr("I can handle a root multiplied by a number (like 3&radic;x), but not a root multiplied by x or by another root here.")
    if k == "div":
        d = ev_exact(node[2]) if not variables(node[2]) else None
        if d:
            P, rs = _split_rad(node[1], v)
            return P.scale(1 / d), [(c / d, R) for c, R in rs]
        raise LogErr("A root on the bottom of a fraction is too complicated here: multiply through by the bottom first.")
    if k == "pow":
        e = ev_exact(node[2]) if not variables(node[2]) else None
        if e == 2 and node[1][0] == "sqrt":
            return to_poly(node[1][1], v), []
    raise LogErr("I could not understand how the roots appear in this equation.")


def _merge_rads(rs):
    out = []
    for c, R in rs:
        for i, (c2, R2) in enumerate(out):
            if R2.c == R.c:
                out[i] = (c2 + c, R2)
                break
        else:
            out.append((c, R))
    return [(c, R) for c, R in out if c != 0]


def _pt(P, v):
    return P.text(v)


def _eval_side(node, v, x):
    from log_core import ev_float
    return ev_float(node, {v: x})


@guard
def solve_equation(expr):
    expr = str(expr or "").strip()
    if not expr:
        raise LogErr("Please type an equation, for example <b>&radic;(x+5) &minus; &radic;(x&minus;4) = 1</b>.")
    if expr.count("=") != 1:
        raise LogErr("Please give one equation with exactly one = sign.")
    ls, rs_ = expr.split("=")
    if not ls.strip() or not rs_.strip():
        raise LogErr("One side of the = sign is empty. Write something on both sides.")
    lhs, rhs = parse(_preprocess(ls)), parse(_preprocess(rs_))
    letters = variables(lhs) | variables(rhs)
    if not letters:
        raise LogErr("There is no unknown letter in this equation. Write the unknown as <b>x</b>.")
    if len(letters) > 1:
        raise LogErr("I can only solve for one unknown letter at a time (like x). I found: " + ", ".join(sorted(letters)) + ".")
    v = next(iter(letters))
    if not (_has_sqrt(lhs) or _has_sqrt(rhs)):
        raise LogErr("There is no square root of the unknown in this equation. For ordinary equations use the Algebra section.")
    Pl, rl = _split_rad(lhs, v)
    Pr, rr = _split_rad(rhs, v)
    P = Pl - Pr
    rads = _merge_rads(rl + [(-c, R) for c, R in rr])
    steps = [f"<b>Equation:</b> {pp(lhs)} = {pp(rhs)}",
             "<b>Square-root equations:</b> the plan is (1) get a root on its own on one side, (2) <i>square both sides</i> to remove the root, (3) solve the equation that is left, and (4) <b>always check</b> every answer in the original equation, because squaring can create answers that do not really work."]
    if not rads:
        raise LogErr("The roots cancel out, so this is an ordinary equation. Use the Algebra section.")
    # domain note
    steps.append("<b>Remember:</b> a square root only exists when the number inside is zero or positive, so we need " + " and ".join(f"{_pt(R, v)} &ge; 0" for c, R in rads) + ".")
    cands = []
    if len(rads) == 1:
        c, R = rads[0]
        # quadratic in sqrt(x)?
        if R.c == [0, 1] and P.deg() <= 1 and P.deg() >= 0 and abs(c) is not None and P.deg() == 1:
            y = "y"
            steps.append(f"<b>A quicker way:</b> let y = &radic;{v}, so y<sup>2</sup> = {v}. The equation becomes a quadratic in y: "
                         f"{HL(P1([P.c[0], c, P.c[1]]).text('y') + ' = 0')}  (note y must be 0 or positive).")
            Ey = P1([P.c[0], c, P.c[1]])
            roots = solve_poly_steps(Ey, "y", steps, "the equation in y", show_std=False)
            for ex, fl, txt in roots:
                if fl < -1e-9:
                    steps.append(f"y = {txt} is <b>rejected</b>: y = &radic;{v} can never be negative.")
                else:
                    xv = fl * fl
                    xq = ex * ex if ex is not None else None
                    steps.append(f"y = {txt}: {v} = y<sup>2</sup> = {qtext(xq) if xq is not None else sig(xv, 5)}")
                    cands.append((xq, xv))
        else:
            # isolate: c*sqrt(R) = -P
            steps.append(f"<b>Step 1 &ndash; get the root on its own:</b> {HL((qtext(c) if c != 1 else '') + '&radic;(' + _pt(R, v) + ') = ' + _pt(-P, v))}")
            if c != 1:
                steps.append(f"(We square the whole of each side, so the number {qtext(c)} in front of the root is squared too: {qtext(c)}<sup>2</sup> = {qtext(c * c)}.)")
            S = -P
            lhsq = R.scale(c * c)
            steps.append(f"<b>Step 2 &ndash; square both sides.</b> The root disappears on the left: ({(qtext(c) if c != 1 else '')}&radic;({_pt(R, v)}))<sup>2</sup> = {_pt(lhsq, v)}. "
                         f"On the right we must square the <b>whole bracket</b> (not each term separately): ({_pt(S, v)})<sup>2</sup> = {_pt(S * S, v)}.")
            steps.append(f"So {HL(_pt(lhsq, v) + ' = ' + _pt(S * S, v))}")
            E = S * S - lhsq
            roots = solve_poly_steps(E, v, steps, "the equation")
            for ex, fl, txt in roots:
                cands.append((ex, fl))
    elif len(rads) == 2:
        (c1, R1), (c2, R2) = rads
        Q = -P
        steps.append(f"<b>Step 1 &ndash; get one root on its own:</b> {HL((qtext(c1) if c1 != 1 else '') + '&radic;(' + _pt(R1, v) + ') = ' + _pt(Q, v) + (' + ' if c2 * -1 > 0 else ' &minus; ') + (qtext(abs(c2)) if abs(c2) != 1 else '') + '&radic;(' + _pt(R2, v) + ')')}")
        # c1^2 R1 = Q^2 - 2 c2 Q sqrt(R2) + c2^2 R2
        G = Q * Q + R2.scale(c2 * c2) - R1.scale(c1 * c1)
        steps.append(f"<b>Step 2 &ndash; square both sides</b> (square the whole right-hand side: (a &minus; b)<sup>2</sup> = a<sup>2</sup> &minus; 2ab + b<sup>2</sup>): "
                     f"{_pt(R1.scale(c1 * c1), v)} = ({_pt(Q, v)})<sup>2</sup> {'+' if -2 * c2 >= 0 else '&minus;'} 2{(qtext(abs(c2)) if abs(c2) != 1 else '')}({_pt(Q, v)})&radic;({_pt(R2, v)}) + {_pt(R2.scale(c2 * c2), v)}")
        lhs_expl = f"A root is still left. Get it alone again: {HL(_pt(Q.scale(2 * c2) if Q.deg() > 0 else P1.const(2 * c2 * Q.c[0] if Q.c else 0), v) + ('' if Q.deg() == 0 else '') + '&radic;(' + _pt(R2, v) + ') = ' + _pt(G, v))}"
        steps.append(lhs_expl)
        if Q.deg() == 0:
            coef = 2 * c2 * (Q.c[0] if Q.c else 0)
            if coef == 0:
                steps.append("The root has disappeared. Now solve what is left.")
                E = G
                roots = solve_poly_steps(E, v, steps, "the equation")
            else:
                rhs_poly = G.scale(1 / coef)
                steps.append(f"Divide both sides by {qtext(coef)}: {HL('&radic;(' + _pt(R2, v) + ') = ' + _pt(rhs_poly, v))}")
                steps.append(f"<b>Step 3 &ndash; square both sides again:</b> {_pt(R2, v)} = ({_pt(rhs_poly, v)})<sup>2</sup> = {_pt(rhs_poly * rhs_poly, v)}")
                E = rhs_poly * rhs_poly - R2
                roots = solve_poly_steps(E, v, steps, "the equation")
        else:
            steps.append(f"<b>Step 3 &ndash; square both sides again:</b> {_pt(R2.scale(4 * c2 * c2), v)} &times; ({_pt(Q, v)})<sup>2</sup>-type expansion: ({_pt(Q.scale(2 * c2), v)})<sup>2</sup> &times; ({_pt(R2, v)}) = ({_pt(G, v)})<sup>2</sup>")
            E = (Q * Q * R2).scale(4 * c2 * c2) - G * G
            roots = solve_poly_steps(E, v, steps, "the equation")
        for ex, fl, txt in roots:
            cands.append((ex, fl))
    else:
        raise LogErr("I can solve equations with one or two square roots. This one has more.")
    if not cands:
        return _ok(steps + ["There is no real value to check, so there is <b>no solution</b>."], "No solution")
    # check table
    rows, good = [], []
    for ex, fl in cands:
        xv = float(ex) if ex is not None else fl
        try:
            lv, rv = _eval_side(lhs, v, xv), _eval_side(rhs, v, xv)
            ok = abs(lv - rv) < 1e-7 * max(1, abs(lv), abs(rv))
        except LogErr:
            lv = rv = None
            ok = False
        except (ValueError, ZeroDivisionError):
            lv = rv = None
            ok = False
        label = f"{v} = {qtext(ex) if ex is not None else sig(fl, 4)}"
        if lv is None:
            rows.append((label, "a root of a negative number", "&#10007; <b>reject</b>"))
        else:
            rows.append((label, f"left = {_cl(lv)}, right = {_cl(rv)}", "&check; accept" if ok else "&#10007; <b>reject</b> (the two sides are not equal)"))
        if ok:
            good.append((ex, fl))
    steps.append("<b>Step 4 &ndash; CHECK each answer in the ORIGINAL equation</b> (squaring can produce false answers):")
    steps.append("<table class='stat-table'><tr><th>Answer</th><th>Putting it in</th><th>Verdict</th></tr>" + "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows) + "</table>")
    if not good:
        return _ok(steps + ["Every candidate fails the check, so there is <b>no solution</b>."], "No solution")
    out = []
    for ex, fl in good:
        out.append(f"{v} = {qtext(ex)}" if ex is not None else f"{v} &asymp; {sig(fl, 4)}")
    return _ok(steps, ", &nbsp; ".join(out))


def _cl(x):
    return fmtq(Fraction(round(x))) if abs(x - round(x)) < 1e-9 else sig(x, 5)
