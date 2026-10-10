"""
Small exact polynomial engine (pure Python, no sympy) used by the Fractions
topic for algebraic fractions: parsing, arithmetic, factorising, LCM / HCF.

Polynomials have rational (Fraction) coefficients and any number of single-
letter variables.  Factorising handles: common numeric/monomial factors,
difference of two squares, trinomials and cubics with rational roots (single
variable), homogeneous two-variable trinomials, even-power substitution
(x^4 - 5x^2 + 4) and grouping of four terms (ax + ay + bx + by).
"""
import re
from fractions import Fraction
from math import gcd, isqrt
from itertools import product


# --------------------------------------------------------------- Poly ------

def _key(items):
    return tuple(sorted((v, e) for v, e in items if e))


class Poly:
    __slots__ = ("t",)

    def __init__(self, t=None):
        self.t = {k: Fraction(c) for k, c in (t or {}).items() if c != 0}

    # constructors
    @staticmethod
    def const(c):
        return Poly({(): Fraction(c)}) if c != 0 else Poly()

    @staticmethod
    def var(v, e=1):
        return Poly({((v, e),): Fraction(1)})

    # basics
    def is_zero(self):
        return not self.t

    def is_const(self):
        return all(k == () for k in self.t)

    def const_value(self):
        return self.t.get((), Fraction(0))

    def vars(self):
        s = set()
        for k in self.t:
            for v, _ in k:
                s.add(v)
        return sorted(s)

    def total_degree(self):
        return max((sum(e for _, e in k) for k in self.t), default=0)

    def degree_in(self, v):
        return max((dict(k).get(v, 0) for k in self.t), default=0)

    def __eq__(self, other):
        return isinstance(other, Poly) and self.t == other.t

    def __hash__(self):
        return hash(frozenset(self.t.items()))

    def copy(self):
        return Poly(dict(self.t))

    # arithmetic
    def __add__(self, o):
        if not isinstance(o, Poly):
            o = Poly.const(o)
        r = dict(self.t)
        for k, c in o.t.items():
            r[k] = r.get(k, Fraction(0)) + c
        return Poly(r)

    __radd__ = __add__

    def __neg__(self):
        return Poly({k: -c for k, c in self.t.items()})

    def __sub__(self, o):
        if not isinstance(o, Poly):
            o = Poly.const(o)
        return self + (-o)

    def __rsub__(self, o):
        return Poly.const(o) - self

    def __mul__(self, o):
        if not isinstance(o, Poly):
            o = Poly.const(o)
        r = {}
        for k1, c1 in self.t.items():
            for k2, c2 in o.t.items():
                d = dict(k1)
                for v, e in k2:
                    d[v] = d.get(v, 0) + e
                k = _key(d.items())
                r[k] = r.get(k, Fraction(0)) + c1 * c2
        return Poly(r)

    __rmul__ = __mul__

    def __pow__(self, n):
        res = Poly.const(1)
        for _ in range(n):
            res = res * self
        return res

    def scale(self, c):
        return Poly({k: v * c for k, v in self.t.items()})

    def subs_const(self, v, val):
        """Replace variable v by a Fraction value."""
        r = Poly()
        for k, c in self.t.items():
            d = dict(k)
            e = d.pop(v, 0)
            r = r + Poly({_key(d.items()): c * (Fraction(val) ** e)})
        return r

    def eval_at(self, v, val):
        r = self.subs_const(v, val)
        return r.const_value() if r.is_const() else None

    # univariate helpers
    def to_uni(self, v):
        """coefficient list low->high (assumes only variable v present)."""
        deg = self.degree_in(v)
        co = [Fraction(0)] * (deg + 1)
        for k, c in self.t.items():
            co[dict(k).get(v, 0)] += c
        return co

    @staticmethod
    def from_uni(co, v):
        return Poly({_key([(v, i)]): c for i, c in enumerate(co) if c != 0})

    def lead_key(self):
        vs = self.vars()
        best = None
        for k in self.t:
            d = dict(k)
            sig = (sum(d.values()), tuple(d.get(v, 0) for v in vs))
            if best is None or sig > best[0]:
                best = (sig, k)
        return best[1] if best else ()

    def lead_coeff(self):
        return self.t[self.lead_key()] if self.t else Fraction(0)

    def monomial_exponents(self):
        """min exponent of each variable across all terms."""
        vs = self.vars()
        res = {}
        for v in vs:
            res[v] = min(dict(k).get(v, 0) for k in self.t)
        return {v: e for v, e in res.items() if e}


def primitive(p):
    """Return (scalar, q) with p = scalar*q, q integer-coefficient, gcd 1,
    positive leading coefficient."""
    if p.is_zero():
        return Fraction(0), p
    from math import lcm
    den = 1
    for c in p.t.values():
        den = lcm(den, c.denominator)
    ints = {k: int(c * den) for k, c in p.t.items()}
    g = 0
    for c in ints.values():
        g = gcd(g, abs(c))
    q = Poly({k: Fraction(c, g) for k, c in ints.items()})
    s = Fraction(g, den)
    if q.lead_coeff() < 0:
        q = -q
        s = -s
    return s, q


# ------------------------------------------------------------ printing -----

def _sup(e):
    return f"<sup>{e}</sup>" if e != 1 else ""


def _mono_str(key):
    return "".join(f"{v}{_sup(e)}" for v, e in key)


def _order_terms(p):
    vs = p.vars()
    items = []
    for k, c in p.t.items():
        d = dict(k)
        sig = (sum(d.values()), tuple(d.get(v, 0) for v in vs))
        items.append((sig, k, c))
    items.sort(key=lambda t: t[0], reverse=True)
    return [(k, c) for _, k, c in items]


def poly_str(p):
    if p.is_zero():
        return "0"
    out = ""
    first = True
    for k, c in _order_terms(p):
        sign = "-" if c < 0 else "+"
        a = abs(c)
        mono = _mono_str(k)
        if a.denominator != 1:
            cs = f"({a.numerator}/{a.denominator})"
        else:
            cs = str(a.numerator)
        if mono:
            body = mono if a == 1 else cs + mono
        else:
            body = cs
        if first:
            out = ("&minus;" if sign == "-" else "") + body
            first = False
        else:
            out += f" {'&minus;' if sign == '-' else '+'} {body}"
    return out


def factors_str(const, factors):
    """const: Fraction; factors: list of (Poly, exp).  Returns HTML."""
    parts = []
    for p, e in factors:
        s = poly_str(p)
        if len(p.t) > 1:
            s = f"({s})"
        parts.append(s + _sup(e))
    body = "".join(parts)
    c = const
    if c.denominator != 1:
        # only used internally; fall back
        cs = f"({c.numerator}/{c.denominator})"
    else:
        cs = str(abs(c.numerator))
    neg = c < 0
    if not body:
        return ("&minus;" if neg else "") + cs
    if abs(c) == 1:
        return ("&minus;" if neg else "") + body
    return ("&minus;" if neg else "") + cs + body


# ------------------------------------------------------------ factoring ----

class TooBig(Exception):
    pass


def _divisors(n):
    n = abs(n)
    if n > 10 ** 9:
        raise TooBig()
    ds = []
    i = 1
    while i * i <= n:
        if n % i == 0:
            ds.append(i)
            if i != n // i:
                ds.append(n // i)
        i += 1
    return ds


def _is_square_frac(c):
    c = abs(c)
    a, b = c.numerator, c.denominator
    ra, rb = isqrt(a), isqrt(b)
    if ra * ra == a and rb * rb == b:
        return Fraction(ra, rb)
    return None


def _synth_div(co, r):
    """divide poly (low->high) by (x - r); return quotient (low->high), remainder"""
    n = len(co) - 1
    hi = list(reversed(co))
    q = [hi[0]]
    for c in hi[1:]:
        q.append(c + q[-1] * r)
    rem = q.pop()
    return list(reversed(q)), rem


def _uni_split(p, v, notes):
    """Split a univariate primitive poly into >=2 factors, or None."""
    co = p.to_uni(v)
    deg = len(co) - 1
    if deg < 2:
        return None
    # even-power substitution (x^4 - 5x^2 + 4 etc.)
    if deg % 2 == 0 and all(co[i] == 0 for i in range(1, deg + 1, 2)):
        ycoef = [co[i] for i in range(0, deg + 1, 2)]
        yp = Poly.from_uni(ycoef, "_y")
        s, y_prim = primitive(yp)
        ys = _uni_split(y_prim, "_y", [])
        if ys:
            res = []
            for f in ys:
                fc = f.to_uni("_y")
                res.append(Poly.from_uni(
                    [c for c in sum(([c, Fraction(0)] for c in fc), [])][:-1] if False else
                    _expand_even(fc), v))
            notes.append("treat x² as a single letter, factorise, then put x² back".replace("x", v))
            return res
    # rational roots
    try:
        return _rational_root_split(co, v)
    except TooBig:
        return None


def _rational_root_split(co, v):
    ints = co
    from math import lcm
    den = 1
    for c in ints:
        den = lcm(den, c.denominator)
    ic = [int(c * den) for c in ints]
    a0, an = ic[0], ic[-1]
    if a0 == 0:
        return None
    found = []
    cur = list(co)
    changed = True
    while changed and len(cur) > 2:
        changed = False
        den2 = 1
        for c in cur:
            den2 = lcm(den2, c.denominator)
        cc = [int(c * den2) for c in cur]
        if cc[0] == 0:
            break
        cands = set()
        for pn in _divisors(cc[0]):
            for qd in _divisors(cc[-1]):
                cands.add(Fraction(pn, qd))
                cands.add(Fraction(-pn, qd))
        for r in sorted(cands, key=lambda z: (abs(z), z)):
            val = Fraction(0)
            for c in reversed(cur):
                val = val * r + c
            if val == 0:
                found.append(r)
                cur, _ = _synth_div(cur, r)
                changed = True
                break
    if not found:
        return None
    facs = []
    for r in found:
        lin = Poly.from_uni([-r, Fraction(1)], v)
        facs.append(primitive(lin)[1])
    rest = Poly.from_uni(cur, v)
    if not rest.is_const():
        facs.append(primitive(rest)[1])
    if len(facs) < 2:
        return None
    return facs


def _expand_even(fc):
    """coefficients in y=x^2 (low->high) -> coefficients in x (low->high)."""
    out = []
    for i, c in enumerate(fc):
        out.append(c)
        if i != len(fc) - 1:
            out.append(Fraction(0))
    return out


def _diff_squares(p):
    if len(p.t) != 2:
        return None
    (k1, c1), (k2, c2) = list(p.t.items())
    if (c1 > 0) == (c2 > 0):
        return None
    s1, s2 = _is_square_frac(c1), _is_square_frac(c2)
    if s1 is None or s2 is None:
        return None
    for k in (k1, k2):
        if any(e % 2 for _, e in k):
            return None
    def root(k, s):
        return Poly({_key([(v, e // 2) for v, e in k]): s})
    a, b = root(k1, s1), root(k2, s2)
    return [primitive(a - b)[1], primitive(a + b)[1]]


def _homogeneous_split(p, notes):
    vs = p.vars()
    if len(vs) != 2:
        return None
    degs = {sum(e for _, e in k) for k in p.t}
    if len(degs) != 1:
        return None
    d = degs.pop()
    if d < 2:
        return None
    u, w = vs
    g = p.subs_const(w, 1)
    if g.vars() != [u] and not g.is_const():
        return None
    gs = primitive(g)[1]
    facs = _uni_split(gs, u, [])
    if not facs:
        return None
    res = []
    for f in facs:
        co = f.to_uni(u)
        fd = len(co) - 1
        h = Poly({_key([(u, i), (w, fd - i)]): c for i, c in enumerate(co) if c != 0})
        res.append(primitive(h)[1])
    return res


def _grouping(p):
    if len(p.t) != 4:
        return None
    terms = [Poly({k: c}) for k, c in p.t.items()]
    pairings = [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]

    def pull(tp):
        """take out common monomial & numeric factor from a 2-term poly (sign-free)"""
        a = tp.t
        ks = list(a.keys())
        me = tp.monomial_exponents()
        mono = Poly({_key(me.items()): Fraction(1)})
        ints = [abs(c) for c in a.values()]
        from math import lcm
        den = 1
        for c in ints:
            den = lcm(den, c.denominator)
        g = 0
        for c in ints:
            g = gcd(g, int(c * den))
        gnum = Fraction(g, den)
        head = mono.scale(gnum)
        rest = Poly({_key([(v, e - me.get(v, 0)) for v, e in k]): c / gnum for k, c in a.items()})
        return head, rest

    for (i, j), (k, l) in pairings:
        p1 = terms[i] + terms[j]
        p2 = terms[k] + terms[l]
        h1, r1 = pull(p1)
        h2, r2 = pull(p2)
        for s1 in (1, -1):
            rr1 = r1.scale(s1)
            hh1 = h1.scale(s1)
            for s2 in (1, -1):
                rr2 = r2.scale(s2)
                hh2 = h2.scale(s2)
                if rr1 == rr2 and not rr1.is_const():
                    first = hh1 + hh2
                    if first.is_zero() or first.is_const() and False:
                        continue
                    return [primitive(first)[1], primitive(rr1)[1]]
    return None


def _split(p, notes):
    vs = p.vars()
    if len(vs) == 1:
        r = _uni_split(p, vs[0], notes)
        if r:
            return r
    if len(vs) >= 1:
        r = _diff_squares(p)
        if r:
            notes.append("difference of two squares: a² − b² = (a − b)(a + b)")
            return r
    if len(vs) == 2:
        r = _homogeneous_split(p, notes)
        if r:
            notes.append("trinomial in two letters")
            return r
    r = _grouping(p)
    if r:
        notes.append("factorise by grouping")
        return r
    return None


def factor(p, notes=None):
    """Return (const, [(Poly, exp), ...]).  Factors are primitive, positive
    leading coefficient, and listed with monomial letters first."""
    if notes is None:
        notes = []
    if p.is_zero():
        return Fraction(0), []
    s, q = primitive(p)
    out = {}

    def add(f, e=1):
        out[f] = out.get(f, 0) + e

    # monomial part
    me = q.monomial_exponents()
    if me:
        rest = Poly({_key([(v, e - me.get(v, 0)) for v, e in k]): c for k, c in q.t.items()})
        for v, e in sorted(me.items()):
            add(Poly.var(v), e)
        q = rest
    elif False:
        pass

    def rec(poly):
        if poly.is_const():
            return
        sp = _split(poly, notes)
        if not sp:
            add(poly)
            return
        for f in sp:
            # a split factor may itself have a monomial part
            _, g = primitive(f)
            m2 = g.monomial_exponents()
            if m2:
                rest = Poly({_key([(v, e - m2.get(v, 0)) for v, e in k]): c for k, c in g.t.items()})
                for v, e in sorted(m2.items()):
                    add(Poly.var(v), e)
                g = rest
            rec(g)

    rec(q)
    facs = list(out.items())
    # order: single letters first, then by degree, then text
    facs.sort(key=lambda fe: (0 if len(fe[0].t) == 1 and fe[0].total_degree() == 1 and fe[0].const_value() == 0 and list(fe[0].t.values())[0] == 1 else 1,
                              fe[0].total_degree(), poly_str(fe[0])))
    prod = Poly.const(1)
    for f, e in facs:
        prod = prod * (f ** e)
    const = p.lead_coeff() / prod.lead_coeff() if not prod.is_zero() else Fraction(1)
    return const, facs


def factor_dict(p):
    c, fs = factor(p)
    return c, {f: e for f, e in fs}


def lcm_hcf_polys(polys):
    """Return (hcf_const, hcf_factors, lcm_const, lcm_factors, per_poly_info)"""
    infos = [factor(p) for p in polys]
    from math import lcm as mlcm
    # numeric content: integer parts of constants
    ints = []
    for c, _ in infos:
        ints.append(abs(c))
    allf = {}
    for _, fs in infos:
        for f, _e in fs:
            allf[f] = True
    hf, lf = [], []
    for f in allf:
        exps = [dict(fs).get(f, 0) for _, fs in infos]
        if min(exps) > 0:
            hf.append((f, min(exps)))
        lf.append((f, max(exps)))
    order = lambda fe: (fe[0].total_degree(), poly_str(fe[0]))
    hf.sort(key=lambda fe: (0 if len(fe[0].t) == 1 else 1,) + order(fe))
    lf.sort(key=lambda fe: (0 if len(fe[0].t) == 1 else 1,) + order(fe))
    return ints, hf, lf, infos


# -------------------------------------------------------------- parsing ----

class ParseError(Exception):
    pass


def normalise(s):
    s = str(s)
    for ch in ("‒", "–", "—", "―", "−", "‐"):
        s = s.replace(ch, "-")
    s = s.replace("×", "*").replace("÷", "/").replace("·", "*")
    sup = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
           "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}
    for k, v in sup.items():
        s = s.replace(k, "^" + v)
    s = s.replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")")
    return s.strip()


_TOK = re.compile(r"\s*(\d+\.\d+|\d+|[A-Za-z]|[-+*/^()])")


def tokenize(s):
    s = normalise(s)
    toks = []
    pos = 0
    while pos < len(s):
        m = _TOK.match(s, pos)
        if not m:
            if s[pos:].strip() == "":
                break
            raise ParseError(f"I could not understand the character &lsquo;{_esc(s[pos:].strip()[0])}&rsquo;.")
        toks.append(m.group(1))
        pos = m.end()
    return toks


def _esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class RF:
    """unsimplified rational function n/d (Poly / Poly)"""
    __slots__ = ("n", "d")

    def __init__(self, n, d=None):
        self.n = n
        self.d = d if d is not None else Poly.const(1)
        if self.d.is_zero():
            raise ParseError("Division by zero in the expression.")

    def __add__(self, o):
        return RF(self.n * o.d + o.n * self.d, self.d * o.d)

    def __sub__(self, o):
        return RF(self.n * o.d - o.n * self.d, self.d * o.d)

    def __mul__(self, o):
        return RF(self.n * o.n, self.d * o.d)

    def __truediv__(self, o):
        if o.n.is_zero():
            raise ParseError("Division by zero in the expression.")
        return RF(self.n * o.d, self.d * o.n)

    def __neg__(self):
        return RF(-self.n, self.d)

    def inv(self):
        return RF(Poly.const(1), Poly.const(1)) / self

    def __pow__(self, k):
        r = RF(Poly.const(1))
        base = self if k >= 0 else self.inv()
        for _ in range(abs(k)):
            r = r * base
        return r


class Node:
    """AST node: ('num',Fraction) ('var',str) ('neg',n) ('add',a,b) ('sub',a,b)
    ('mul',a,b) ('div',a,b) ('pow',a,int)"""


def parse_ast(text):
    toks = tokenize(text)
    if not toks:
        raise ParseError("Please type an expression.")
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def eat():
        t = toks[pos[0]]
        pos[0] += 1
        return t

    def expr():
        left = term()
        while peek() in ("+", "-"):
            op = eat()
            right = term()
            left = ("add" if op == "+" else "sub", left, right)
        return left

    def starts_factor(t):
        return t is not None and (t == "(" or t[0].isalnum())

    def term():
        left = unary()
        while True:
            t = peek()
            if t == "*":
                eat()
                left = ("mul", left, unary())
            elif t == "/":
                eat()
                left = ("div", left, unary())
            elif starts_factor(t):
                left = ("mul", left, power())  # implicit multiplication
            else:
                break
        return left

    def unary():
        if peek() == "-":
            eat()
            return ("neg", unary())
        if peek() == "+":
            eat()
            return unary()
        return power()

    def power():
        base = atom()
        if peek() == "^":
            eat()
            neg = False
            if peek() == "-":
                eat()
                neg = True
            elif peek() == "+":
                eat()
            t = peek()
            if t == "(":
                eat()
                neg2 = False
                if peek() == "-":
                    eat()
                    neg2 = True
                t = eat()
                if not t.isdigit():
                    raise ParseError("Powers must be whole numbers here.")
                if peek() != ")":
                    raise ParseError("Powers must be whole numbers here.")
                eat()
                k = int(t) * (-1 if (neg ^ neg2) else 1)
            else:
                if t is None or not t.isdigit():
                    raise ParseError("Powers must be whole numbers here.")
                eat()
                k = int(t) * (-1 if neg else 1)
            if abs(k) > 12:
                raise ParseError("That power is too large for this solver.")
            return ("pow", base, k)
        return base

    def atom():
        t = peek()
        if t is None:
            raise ParseError("The expression ends too early - check for a missing number or bracket.")
        if t == "(":
            eat()
            e = expr()
            if peek() != ")":
                raise ParseError("A bracket is not closed.")
            eat()
            return e
        if t[0].isdigit():
            eat()
            return ("num", Fraction(t))
        if t.isalpha():
            eat()
            return ("var", t)
        raise ParseError(f"Unexpected &lsquo;{_esc(t)}&rsquo; in the expression.")

    ast = expr()
    if pos[0] != len(toks):
        raise ParseError(f"I could not understand &lsquo;{_esc(toks[pos[0]])}&rsquo;. Use * between things you multiply and brackets for denominators.")
    return ast


def ast_eval(node):
    k = node[0]
    if k == "num":
        return RF(Poly.const(node[1]))
    if k == "var":
        return RF(Poly.var(node[1]))
    if k == "neg":
        return -ast_eval(node[1])
    if k == "add":
        return ast_eval(node[1]) + ast_eval(node[2])
    if k == "sub":
        return ast_eval(node[1]) - ast_eval(node[2])
    if k == "mul":
        return ast_eval(node[1]) * ast_eval(node[2])
    if k == "div":
        return ast_eval(node[1]) / ast_eval(node[2])
    if k == "pow":
        return ast_eval(node[1]) ** node[2]
    raise ParseError("Unsupported expression.")


def parse_poly(text):
    rf = ast_eval(parse_ast(text))
    if rf.d.is_const():
        return rf.n.scale(1 / rf.d.const_value())
    raise ParseError("This should be a polynomial (no division by letters).")


def split_terms(node):
    """Flatten top-level + / - into [(sign, node)]"""
    if node[0] == "add":
        return split_terms(node[1]) + split_terms(node[2])
    if node[0] == "sub":
        return split_terms(node[1]) + [(-s, n) for s, n in split_terms(node[2])]
    return [(1, node)]
