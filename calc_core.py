"""Tiny symbolic engine for school calculus (pure Python).

AST nodes (tuples):  ('num',Fraction) ('var',) ('const','e'|'pi') ('neg',a) ('add',a,b) ('sub',a,b)
('mul',a,b) ('div',a,b) ('pow',a,b) ('fn',name,a)    name in sin cos tan ln exp sqrt
PS = sum of c * v^p with Fraction powers (dict p -> c).
"""
import math
import re
from fractions import Fraction

MINUS = "&minus;"
FUNCS = {"sin", "cos", "tan", "ln", "sqrt", "exp", "log"}


class CErr(Exception):
    pass


# ----------------------------------------------------------------- parser ---

def _norm(s):
    s = str(s).strip()
    for ch in ("‒", "–", "—", "−", "‐"):
        s = s.replace(ch, "-")
    s = s.replace("×", "*").replace("÷", "/").replace("·", "*").replace("π", "pi")
    sup = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}
    out = ""
    for ch in s:
        out += ("^" + sup[ch]) if ch in sup else ch
    s = out.replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")")
    return s


_TOK = re.compile(r"\s*(\d+\.\d+|\d+|[A-Za-z]+|[-+*/^()])")


def tokenize(s):
    s = _norm(s)
    if len(s) > 200:
        raise CErr("That expression is too long.")
    toks = []
    pos = 0
    while pos < len(s):
        m = _TOK.match(s, pos)
        if not m:
            if s[pos:].strip() == "":
                break
            raise CErr(f"I could not understand the character '{s[pos:].strip()[0]}'.")
        toks.append(m.group(1))
        pos = m.end()
    return toks


def parse(text, var=None):
    """returns (ast, variable letter)"""
    toks = tokenize(text)
    if not toks:
        raise CErr("Please type an expression.")
    # split identifiers: sinx -> sin x (only when letters are all known function+var)  keep simple
    letters = set()
    cleaned = []
    for t in toks:
        if t.isalpha():
            low = t.lower()
            if low in FUNCS or low in ("pi", "e"):
                cleaned.append(low)
                continue
            if len(t) > 1:
                # split into single letters (xy -> x y) or function glued: sinx
                done = False
                for f in FUNCS:
                    if low.startswith(f) and len(low) > len(f) and low[len(f):].isalpha() and len(low[len(f):]) == 1:
                        cleaned += [f, low[len(f):]]
                        letters.add(low[len(f):])
                        done = True
                        break
                if not done:
                    for ch in low:
                        cleaned.append(ch)
                        letters.add(ch)
            else:
                cleaned.append(low)
                letters.add(low)
        else:
            cleaned.append(t)
    letters -= {"e"} if len(letters - {"e"}) >= 1 else set()
    if var is None:
        if len(letters) > 1:
            raise CErr("Use only one letter (like x) in the expression, plus numbers.")
        var = next(iter(letters)) if letters else "x"
    elif letters - {var}:
        raise CErr(f"Use only the letter {var} in the expression.")
    toks = cleaned
    i = [0]

    def peek():
        return toks[i[0]] if i[0] < len(toks) else None

    def eat():
        t = toks[i[0]]
        i[0] += 1
        return t

    def is_start(t):
        return t is not None and (t[0].isdigit() or t.isalpha() or t == "(")

    def expr():
        a = term()
        while peek() in ("+", "-"):
            op = eat()
            b = term()
            a = ("add", a, b) if op == "+" else ("sub", a, b)
        return a

    def term():
        a = unary()
        while True:
            t = peek()
            if t in ("*", "/"):
                eat()
                b = unary()
                a = ("mul", a, b) if t == "*" else ("div", a, b)
            elif is_start(t):
                b = power()
                a = ("mul", a, b)
            else:
                return a

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
            if peek() == "-":
                eat()
                e = ("neg", power_arg())
            else:
                e = power_arg()
            base = ("pow", base, fold(e))
        return base

    def power_arg():
        if peek() == "(":
            eat()
            e = expr()
            if peek() != ")":
                raise CErr("A bracket is not closed.")
            eat()
            return e
        t = peek()
        if t is not None and (t[0].isdigit()):
            eat()
            return ("num", Fraction(t))
        if t is not None and t.isalpha():
            return atom()
        raise CErr("I expected a number or bracket after ^.")

    def atom():
        t = peek()
        if t is None:
            raise CErr("The expression ends too soon.")
        if t[0].isdigit():
            eat()
            if len(t) > 16:
                raise CErr("Numbers that long are not allowed.")
            return ("num", Fraction(t))
        if t == "(":
            eat()
            e = expr()
            if peek() != ")":
                raise CErr("A bracket is not closed.")
            eat()
            return e
        if t.isalpha():
            eat()
            if t in FUNCS:
                if peek() == "(":
                    eat()
                    a = expr()
                    if peek() != ")":
                        raise CErr("A bracket is not closed.")
                    eat()
                else:
                    # juxtaposed argument like sin 2x
                    a = power()
                    while is_start(peek()) and peek() != "(" or (peek() == "(" and False):
                        a = ("mul", a, power())
                name = "ln" if t == "log" else t
                if t == "exp":
                    return ("pow", ("const", "e"), a)
                return ("fn", name, a)
            if t == "pi":
                return ("const", "pi")
            if t == "e" and var != "e":
                return ("const", "e")
            if t == var:
                return ("var",)
            raise CErr(f"I do not know what '{t}' is.")
        raise CErr(f"Unexpected '{t}'.")

    ast = expr()
    ast = fold(ast)
    if i[0] != len(toks):
        raise CErr(f"I could not read the part starting at '{toks[i[0]]}'.")
    return ast, var


def fold(n):
    """fold constant numeric subtrees into a single num node when exact"""
    k = n[0]
    if k in ("num", "var", "const"):
        return n
    if k == "neg":
        a = fold(n[1])
        return ("num", -a[1]) if a[0] == "num" else ("neg", a)
    if k == "fn":
        return ("fn", n[1], fold(n[2]))
    a, b = fold(n[1]), fold(n[2])
    if a[0] == "num" and b[0] == "num":
        x, y = a[1], b[1]
        if k == "add":
            return ("num", x + y)
        if k == "sub":
            return ("num", x - y)
        if k == "mul":
            return ("num", x * y)
        if k == "div" and y != 0:
            return ("num", x / y)
        if k == "pow" and y.denominator == 1 and abs(y) <= 12 and not (x == 0 and y < 0):
            return ("num", x ** int(y))
    return (k, a, b)


# ------------------------------------------------------ smart constructors ---

def N(v):
    return ("num", Fraction(v))


ZERO, ONE = N(0), N(1)


def is_num(n):
    return n[0] == "num"


def add(a, b):
    if is_num(a) and is_num(b):
        return N(a[1] + b[1])
    if a == ZERO:
        return b
    if b == ZERO:
        return a
    return ("add", a, b)


def sub(a, b):
    if is_num(a) and is_num(b):
        return N(a[1] - b[1])
    if b == ZERO:
        return a
    if a == ZERO:
        return neg(b)
    return ("sub", a, b)


def neg(a):
    if is_num(a):
        return N(-a[1])
    if a[0] == "neg":
        return a[1]
    return ("neg", a)


def _mfactors(n):
    if n[0] == "mul":
        return _mfactors(n[1]) + _mfactors(n[2])
    return [n]


def mul(a, b):
    if is_num(a) and is_num(b):
        return N(a[1] * b[1])
    if a == ZERO or b == ZERO:
        return ZERO
    if a == ONE:
        return b
    if b == ONE:
        return a
    if is_num(a) and a[1] == -1:
        return neg(b)
    if is_num(b) and b[1] == -1:
        return neg(a)
    fs = _mfactors(a) + _mfactors(b)
    c = Fraction(1)
    rest = []
    for f in fs:
        if f[0] == "num":
            c *= f[1]
        elif f[0] == "neg" and True:
            c *= -1
            rest.append(f[1])
        else:
            rest.append(f)
    if c == 0:
        return ZERO
    out = None
    for f in rest:
        out = f if out is None else ("mul", out, f)
    if out is None:
        return N(c)
    if c == 1:
        return out
    if c == -1:
        return ("neg", out)
    return ("mul", N(c), out)


def div(a, b):
    if is_num(b):
        if b[1] == 0:
            raise CErr("Division by zero.")
        if is_num(a):
            return N(a[1] / b[1])
        if b[1] == 1:
            return a
    if a == ZERO:
        return ZERO
    return ("div", a, b)


def power(a, b):
    if is_num(b):
        if b[1] == 0:
            return ONE
        if b[1] == 1:
            return a
        if is_num(a) and b[1].denominator == 1 and abs(b[1]) <= 12:
            return N(a[1] ** int(b[1]))
    return ("pow", a, b)


def has_var(n):
    k = n[0]
    if k == "var":
        return True
    if k in ("num", "const"):
        return False
    return any(has_var(c) for c in n[1:] if isinstance(c, tuple))


# ---------------------------------------------------------------------- PS ---

class PS:
    __slots__ = ("t",)

    def __init__(self, t=None):
        self.t = {Fraction(k): Fraction(v) for k, v in (t or {}).items() if v != 0}

    @staticmethod
    def const(c):
        return PS({0: c})

    def __add__(self, o):
        r = dict(self.t)
        for k, v in o.t.items():
            r[k] = r.get(k, 0) + v
        return PS(r)

    def __neg__(self):
        return PS({k: -v for k, v in self.t.items()})

    def __sub__(self, o):
        return self + (-o)

    def __mul__(self, o):
        r = {}
        for k1, v1 in self.t.items():
            for k2, v2 in o.t.items():
                r[k1 + k2] = r.get(k1 + k2, 0) + v1 * v2
        if len(r) > 80:
            raise CErr("That expression is too long to expand.")
        return PS(r)

    def scale(self, c):
        return PS({k: v * c for k, v in self.t.items()})

    def deriv(self):
        return PS({k - 1: v * k for k, v in self.t.items() if k != 0})

    def integ(self):
        """returns (PS, log coefficient)"""
        r = {}
        lc = Fraction(0)
        for k, v in self.t.items():
            if k == -1:
                lc += v
            else:
                r[k + 1] = v / (k + 1)
        return PS(r), lc

    def is_poly(self):
        return all(k.denominator == 1 and k >= 0 for k in self.t)

    def degree(self):
        return max(self.t) if self.t else 0

    def is_monomial(self):
        return len(self.t) == 1

    def eval_f(self, x):
        s = 0.0
        for k, v in self.t.items():
            if x == 0 and k < 0:
                raise CErr("That would need division by zero.")
            if x < 0 and k.denominator != 1:
                raise CErr("A root of a negative number is not real.")
            s += float(v) * (float(x) ** float(k))
        return s

    def eval_x(self, x):
        """exact Fraction if possible else float"""
        x = Fraction(x)
        total = Fraction(0)
        exact = True
        fl = 0.0
        for k, v in self.t.items():
            if x == 0 and k < 0:
                raise CErr("That would need division by zero.")
            if k.denominator == 1:
                total += v * x ** int(k)
            else:
                r = _root_pow(x, k)
                if r is None:
                    exact = False
                    if x < 0:
                        raise CErr("A root of a negative number is not real.")
                    fl += float(v) * float(x) ** float(k)
                else:
                    total += v * r
        return total if exact else float(total) + fl


def _iroot(n, k):
    if n < 0:
        return None
    r = round(n ** (1.0 / k)) if n < 10 ** 300 else None
    if r is None:
        return None
    for c in (r - 1, r, r + 1):
        if c >= 0 and c ** k == n:
            return c
    return None


def _root_pow(x, k):
    q, p = k.denominator, k.numerator
    if x < 0:
        return None
    a, b = _iroot(x.numerator, q), _iroot(x.denominator, q)
    if a is None or b is None:
        return None
    return Fraction(a, b) ** p


def to_ps(n):
    """AST -> PS or None"""
    k = n[0]
    if k == "num":
        return PS.const(n[1])
    if k == "var":
        return PS({1: 1})
    if k == "const":
        return None
    if k == "neg":
        a = to_ps(n[1])
        return -a if a is not None else None
    if k in ("add", "sub", "mul"):
        a, b = to_ps(n[1]), to_ps(n[2])
        if a is None or b is None:
            return None
        return a + b if k == "add" else (a - b if k == "sub" else a * b)
    if k == "div":
        a, b = to_ps(n[1]), to_ps(n[2])
        if a is None or b is None or not b.is_monomial():
            return None
        (e, c), = b.t.items()
        return PS({kk - e: vv / c for kk, vv in a.t.items()})
    if k == "pow":
        if not is_num(n[2]):
            if n[2][0] == "neg" and is_num(n[2][1]):
                e = -n[2][1][1]
            else:
                return None
        else:
            e = n[2][1]
        if n[2][0] == "neg" and is_num(n[2][1]):
            e = -n[2][1][1]
        a = to_ps(n[1])
        if a is None:
            return None
        if a.is_monomial():
            (kk, c), = a.t.items()
            if e.denominator == 1:
                return PS({kk * e: c ** int(e)}) if (abs(e) <= 40) else None
            if c == 1:
                return PS({kk * e: 1})
            r = _root_pow(c, e) if c > 0 else None
            return PS({kk * e: r}) if r is not None else None
        if e.denominator == 1 and 0 <= e <= 12:
            r = PS.const(1)
            for _ in range(int(e)):
                r = r * a
            return r
        return None
    if k == "fn" and n[1] == "sqrt":
        return to_ps(("pow", n[2], N(Fraction(1, 2))))
    return None


# ----------------------------------------------------------------- printing ---

def _fmt_num(c):
    c = Fraction(c)
    if c.denominator == 1:
        return str(abs(c.numerator))
    return f'<span class="frac"><span class="fn">{abs(c.numerator)}</span><span class="fd">{c.denominator}</span></span>'


def _exp_txt(p):
    p = Fraction(p)
    s = str(abs(p.numerator)) if p.denominator == 1 else f"{abs(p.numerator)}/{p.denominator}"
    return (MINUS if p < 0 else "") + s


def ps_str(ps, v="x", sort=True):
    if not ps.t:
        return "0"
    out = ""
    for k in sorted(ps.t, reverse=True):
        c = ps.t[k]
        a = abs(c)
        if k == 0:
            body = _fmt_num(a)
        else:
            vv = v if k == 1 else f"{v}<sup>{_exp_txt(k)}</sup>"
            body = (_fmt_num(a) if a != 1 else "") + vv
        if not out:
            out = (MINUS if c < 0 else "") + body
        else:
            out += f" {MINUS if c < 0 else '+'} {body}"
    return out


def fr_stack(n, d):
    return f'<span class="frac"><span class="fn">{n}</span><span class="fd">{d}</span></span>'


def pr(n, v="x", prec=0):
    k = n[0]
    if k == "num":
        c = n[1]
        s = _fmt_num(c)
        return (MINUS + s) if c < 0 else s
    if k == "var":
        return v
    if k == "const":
        return "e" if n[1] == "e" else "&pi;"
    if k == "neg":
        s = MINUS + pr(n[1], v, 3)
        return f"({s})" if prec > 1 else s
    if k == "add" and n[2][0] == "neg":
        s = pr(n[1], v, 1) + f" {MINUS} " + pr(n[2][1], v, 2)
        return f"({s})" if prec > 1 else s
    if k in ("add", "sub"):
        s = pr(n[1], v, 1) + (" + " if k == "add" else f" {MINUS} ") + pr(n[2], v, 2 if k == "sub" else 1)
        return f"({s})" if prec > 1 else s
    if k == "mul":
        a, b = n[1], n[2]
        sa = pr(a, v, 2)
        sb = pr(b, v, 2)
        if is_num(a) and not is_num(b) and b[0] not in ("neg",):
            s = sa + sb
        elif is_num(b) and not is_num(a):
            s = sb + sa
        elif is_num(a) and is_num(b):
            s = f"{sa} &times; {sb}"
        else:
            s = sa + sb if (b[0] in ("pow", "fn", "var", "add", "sub") and a[0] != "num") or a[0] == "num" else sa + sb
        return f"({s})" if prec > 2 else s
    if k == "div":
        den = to_ps(n[2])
        ds = ps_str(den, v) if (den is not None and den.is_monomial()) else pr(n[2], v, 0)
        return fr_stack(show(n[1], v), ds)
    if k == "pow":
        b = pr(n[1], v, 4)
        e = n[2]
        if is_num(e):
            et = _exp_txt(e[1])
        else:
            et = pr(e, v, 0)
        if n[1][0] in ("num", "var", "const", "fn") and not (n[1][0] == "num" and n[1][1] < 0):
            return f"{b}<sup>{et}</sup>"
        return f"({pr(n[1], v, 0)})<sup>{et}</sup>"
    if k == "fn":
        return f"{n[1]}({pr(n[2], v, 0)})"
    return "?"


def show(n, v="x"):
    ps = to_ps(n)
    if ps is not None:
        return ps_str(ps, v)
    return pr(n, v)


# ------------------------------------------------------- differentiation ---

def D(n):
    k = n[0]
    if k in ("num", "const"):
        return ZERO
    if k == "var":
        return ONE
    if k == "neg":
        return neg(D(n[1]))
    if k == "add":
        return add(D(n[1]), D(n[2]))
    if k == "sub":
        return sub(D(n[1]), D(n[2]))
    if k == "mul":
        a, b = n[1], n[2]
        if not has_var(a):
            return mul(a, D(b))
        if not has_var(b):
            return mul(D(a), b)
        return add(mul(D(a), b), mul(a, D(b)))
    if k == "div":
        a, b = n[1], n[2]
        if not has_var(b):
            return div(D(a), b)
        return div(sub(mul(D(a), b), mul(a, D(b))), power(b, N(2)))
    if k == "pow":
        a, e = n[1], n[2]
        if not has_var(e):
            ee = e
            if is_num(e):
                m = mul(e, power(a, N(e[1] - 1)))
            elif e[0] == "neg" and is_num(e[1]):
                m = mul(N(-e[1][1]), power(a, N(-e[1][1] - 1)))
            else:
                m = mul(e, power(a, sub(e, ONE)))
            return mul(m, D(a)) if a != ("var",) else m
        if a == ("const", "e"):
            return mul(n, D(e))
        if not has_var(a):
            raise CErr("I can only differentiate numbers raised to x if the base is e.")
        raise CErr("I cannot differentiate when x is in both the base and the power.")
    if k == "fn":
        f, u = n[1], n[2]
        du = D(u)
        if f == "sin":
            r = ("fn", "cos", u)
        elif f == "cos":
            r = neg(("fn", "sin", u))
        elif f == "tan":
            r = div(ONE, power(("fn", "cos", u), N(2)))
        elif f == "ln":
            return div(du, u)
        elif f == "sqrt":
            return D(power(u, N(Fraction(1, 2))))
        else:
            raise CErr("Unsupported function.")
        return mul(r, du) if du != ONE else r
    raise CErr("Cannot differentiate this.")


def flat_terms(n, sign=1):
    k = n[0]
    if k == "add":
        return flat_terms(n[1], sign) + flat_terms(n[2], sign)
    if k == "sub":
        return flat_terms(n[1], sign) + flat_terms(n[2], -sign)
    if k == "neg":
        return flat_terms(n[1], -sign)
    return [(sign, n)]


def ev(n, x):
    k = n[0]
    if k == "num":
        return float(n[1])
    if k == "var":
        return x
    if k == "const":
        return math.e if n[1] == "e" else math.pi
    if k == "neg":
        return -ev(n[1], x)
    a = ev(n[1], x) if k != "fn" else None
    if k == "add":
        return a + ev(n[2], x)
    if k == "sub":
        return a - ev(n[2], x)
    if k == "mul":
        return a * ev(n[2], x)
    if k == "div":
        b = ev(n[2], x)
        if b == 0:
            raise CErr("Division by zero.")
        return a / b
    if k == "pow":
        b = ev(n[2], x)
        if a < 0 and b != int(b):
            raise CErr("Not a real number.")
        if a == 0 and b < 0:
            raise CErr("Division by zero.")
        return a ** b
    if k == "fn":
        u = ev(n[2], x)
        f = n[1]
        if f == "sin":
            return math.sin(u)
        if f == "cos":
            return math.cos(u)
        if f == "tan":
            return math.tan(u)
        if f == "ln":
            if u <= 0:
                raise CErr("ln needs a positive number.")
            return math.log(u)
        if f == "sqrt":
            if u < 0:
                raise CErr("Square root of a negative number.")
            return math.sqrt(u)
    raise CErr("Cannot evaluate.")


def ast_value(n, x):
    """exact if PS-convertible else float"""
    ps = to_ps(n)
    if ps is not None:
        try:
            return ps.eval_x(x)
        except CErr:
            raise
    return ev(n, float(x))


def ps_plain(ps, v="x"):
    """parseable plain-text form of a PS"""
    if not ps.t:
        return "0"
    out = []
    for k in sorted(ps.t, reverse=True):
        c = ps.t[k]
        cs = f"({c.numerator}/{c.denominator})" if c.denominator != 1 else str(c.numerator)
        if k == 0:
            out.append(f"({cs})")
        else:
            pw_ = f"{v}^({k.numerator}/{k.denominator})" if k.denominator != 1 else (v if k == 1 else f"{v}^{k.numerator}")
            out.append(f"{cs}*{pw_}")
    return " + ".join(out)
