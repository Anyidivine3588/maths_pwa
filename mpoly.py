"""Small multivariate polynomial algebra with exact Fractions, parsed from the shared expression parser."""
import math
from fractions import Fraction

from log_core import LogErr, parse, fmtq, variables, MINUS

MAXDEG = 12


class MP:
    """polynomial: {((var, exp), ...sorted): Fraction}"""
    __slots__ = ("t",)

    def __init__(self, t=None):
        self.t = {m: Fraction(c) for m, c in (t or {}).items() if c != 0}

    # ---- constructors
    @staticmethod
    def const(c):
        return MP({(): Fraction(c)})

    @staticmethod
    def var(v):
        return MP({((v, 1),): Fraction(1)})

    @staticmethod
    def mono(c, d):
        return MP({tuple(sorted((v, e) for v, e in d.items() if e)): Fraction(c)})

    # ---- arithmetic
    def __add__(self, o):
        out = dict(self.t)
        for m, c in o.t.items():
            out[m] = out.get(m, 0) + c
        return MP(out)

    def __neg__(self):
        return MP({m: -c for m, c in self.t.items()})

    def __sub__(self, o):
        return self + (-o)

    def scale(self, k):
        k = Fraction(k)
        return MP({m: c * k for m, c in self.t.items()})

    def __mul__(self, o):
        out = {}
        for m1, c1 in self.t.items():
            for m2, c2 in o.t.items():
                d = dict(m1)
                for v, e in m2:
                    d[v] = d.get(v, 0) + e
                if sum(d.values()) > 40:
                    raise LogErr("That expression is too big for this tool.")
                key = tuple(sorted(d.items()))
                out[key] = out.get(key, 0) + c1 * c2
        return MP(out)

    def __pow__(self, n):
        if n < 0 or n > MAXDEG:
            raise LogErr("Powers must be whole numbers from 0 to %d here." % MAXDEG)
        r = MP.const(1)
        for _ in range(n):
            r = r * self
        return r

    def __eq__(self, o):
        return isinstance(o, MP) and self.t == o.t

    def __hash__(self):
        return hash(tuple(sorted(self.t.items())))

    # ---- inspection
    def is_zero(self):
        return not self.t

    def is_const(self):
        return all(m == () for m in self.t)

    def const_value(self):
        return self.t.get((), Fraction(0))

    def vars(self):
        return sorted({v for m in self.t for v, _ in m})

    def deg_in(self, v):
        return max((dict(m).get(v, 0) for m in self.t), default=0)

    def total_deg(self):
        return max((sum(e for _, e in m) for m in self.t), default=0)

    def coeff_in(self, v, k):
        """coefficient of v**k as an MP in the other variables"""
        out = {}
        for m, c in self.t.items():
            d = dict(m)
            if d.get(v, 0) == k:
                d.pop(v, None)
                out[tuple(sorted(d.items()))] = c
        return MP(out)

    def subs(self, v, q):
        """substitute MP q for variable v"""
        res = MP()
        for m, c in self.t.items():
            d = dict(m)
            e = d.pop(v, 0)
            base = MP({tuple(sorted(d.items())): c})
            res = res + (base * (q ** e) if e else base)
        return res

    def eval(self, vals):
        tot = Fraction(0)
        for m, c in self.t.items():
            x = c
            for v, e in m:
                x *= Fraction(vals[v]) ** e
            tot += x
        return tot

    def terms_sorted(self):
        vs = self.vars()

        def key(item):
            m = dict(item[0])
            return (-sum(m.values()),) + tuple(-m.get(v, 0) for v in vs)
        return sorted(self.t.items(), key=key)

    def monomial_content(self):
        """(gcd of |coefs| as Fraction-free integer or Fraction, {var: min exp})"""
        ex = None
        for m in self.t:
            d = dict(m)
            ex = d if ex is None else {v: min(ex.get(v, 0), d.get(v, 0)) for v in set(ex) | set(d)}
        return {v: e for v, e in (ex or {}).items() if e}

    def int_content(self):
        """positive gcd of coefficients after clearing denominators: returns Fraction g so self/g has coprime integer coefs"""
        cs = list(self.t.values())
        if not cs:
            return Fraction(1)
        L = 1
        for c in cs:
            L = L * c.denominator // math.gcd(L, c.denominator)
        g = 0
        for c in cs:
            g = math.gcd(g, int(c * L))
        return Fraction(g, L)

    def div_mono(self, c, d):
        out = {}
        for m, k in self.t.items():
            dd = dict(m)
            for v, e in d.items():
                dd[v] = dd.get(v, 0) - e
                if dd[v] < 0:
                    raise LogErr("internal: bad monomial division")
            out[tuple(sorted((v, e) for v, e in dd.items() if e))] = k / Fraction(c)
        return MP(out)

    # ---- text
    def text(self, plain_first_sign=False):
        if not self.t:
            return "0"
        out = ""
        for i, (m, c) in enumerate(self.terms_sorted()):
            body = mono_text(m)
            mag = abs(c)
            if body == "":
                s = fmtq(mag)
            else:
                s = ("" if mag == 1 else fmtq(mag)) + body
            if i == 0:
                out += (MINUS if c < 0 else "") + s
            else:
                out += (f" {MINUS} " if c < 0 else " + ") + s
        return out


def mono_text(m):
    s = ""
    for v, e in m:
        s += v if e == 1 else f"{v}<sup>{e}</sup>"
    return s


def br(p):
    """text of p, in brackets when it has more than one term"""
    return f"({p.text()})" if len(p.t) > 1 else p.text()


def from_node(node):
    k = node[0]
    if k == "num":
        return MP.const(node[1])
    if k == "var":
        return MP.var(node[1])
    if k == "const":
        return MP.var("π")
    if k == "neg":
        return -from_node(node[1])
    if k == "add":
        return from_node(node[1]) + from_node(node[2])
    if k == "sub":
        return from_node(node[1]) - from_node(node[2])
    if k == "mul":
        return from_node(node[1]) * from_node(node[2])
    if k == "div":
        d = from_node(node[2])
        if not d.is_const() or d.is_zero():
            raise LogErr("I can only divide by a plain number here.")
        return from_node(node[1]).scale(1 / d.const_value())
    if k == "pow":
        e = from_node(node[2])
        if not e.is_const() or e.const_value().denominator != 1 or e.const_value() < 0:
            raise LogErr("Powers must be whole numbers like 2 or 3 here.")
        return from_node(node[1]) ** int(e.const_value())
    raise LogErr("This kind of expression is not supported here (use +, &minus;, &times;, powers and brackets).")


def parse_poly(text, allow_vars=None):
    node = parse(str(text or "").strip(), plain=True)
    p = from_node(node)
    if allow_vars is not None:
        bad = [v for v in p.vars() if v not in allow_vars]
        if bad:
            raise LogErr(f"I found the letter '{bad[0]}' but expected only: {', '.join(allow_vars)}.")
    return p


# ---------------------------------------------------------------------- one-variable helpers
def to_coeffs(p, v):
    """MP in one variable v (numbers only otherwise) -> list of Fractions, low to high degree"""
    if any(w != v for w in p.vars()):
        raise LogErr(f"Only the letter {v} is allowed here.")
    d = p.deg_in(v)
    return [p.coeff_in(v, i).const_value() for i in range(d + 1)]


def from_coeffs(c, v):
    out = MP()
    for i, a in enumerate(c):
        if a:
            out = out + MP({((v, i),) if i else (): Fraction(a)})
    return out


def divmod_poly(n, d):
    """lists low->high.  returns (q, r)"""
    n = list(n)
    while n and n[-1] == 0:
        n.pop()
    d = list(d)
    while d and d[-1] == 0:
        d.pop()
    if not d:
        raise LogErr("You cannot divide by zero.")
    q = [Fraction(0)] * max(len(n) - len(d) + 1, 1)
    r = list(n)
    while len(r) >= len(d) and r:
        k = len(r) - len(d)
        f = r[-1] / d[-1]
        q[k] = f
        for i, a in enumerate(d):
            r[k + i] -= f * a
        while r and r[-1] == 0:
            r.pop()
    return q, r
