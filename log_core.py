"""Core helpers for the Logarithms topic (pure Python, no sympy).

* a small parser for expressions such as  2log_3(9) + log(x-1),  log_(1/2)(4),  ln(e^2),  2^(x+1)
* a pretty printer that produces the small HTML the app allows
* exact "which power?" tools based on prime factorisation
"""
import math
import re
from fractions import Fraction
from math import gcd, isqrt

MINUS = "&minus;"


class LogErr(Exception):
    """A friendly, HTML-safe message for the student."""


class NeedValue(LogErr):
    pass


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ------------------------------------------------------------ numbers ----

def fmtq(q):
    """Fraction -> '5', '0.25', '2/3' (HTML minus sign)"""
    q = Fraction(q)
    neg = q < 0
    a = abs(q)
    if a.denominator == 1:
        s = str(a.numerator)
    else:
        d = a.denominator
        while d % 2 == 0:
            d //= 2
        while d % 5 == 0:
            d //= 5
        if d == 1 and a.denominator <= 10 ** 6:
            from decimal import Decimal, localcontext
            with localcontext() as c:
                c.prec = 60
                s = format(Decimal(a.numerator) / Decimal(a.denominator), "f")
        else:
            s = f"{a.numerator}/{a.denominator}"
    return (MINUS if neg else "") + s


def sig(x, n=4):
    """float -> text with n significant figures (no sci notation)"""
    x = float(x)
    if x == 0:
        return "0"
    if not math.isfinite(x):
        return "undefined"
    e = math.floor(math.log10(abs(x)))
    dp = max(n - 1 - e, 0)
    r = round(x, dp)
    s = f"{r:.{dp}f}"
    return s.replace("-", MINUS)


def dp_(x, p=4):
    s = f"{round(float(x), p):.{p}f}"
    return s.replace("-", MINUS) if s.startswith("-") else s


def factor_int(n):
    """prime factorisation of a positive int (trial division; None if too big)"""
    if n <= 0:
        return None
    if n > 10 ** 14:
        return None
    out = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            out[d] = out.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


def vec_of(q):
    """positive Fraction -> {prime: int exponent} (None if too big / not positive)"""
    q = Fraction(q)
    if q <= 0:
        return None
    a = factor_int(q.numerator)
    b = factor_int(q.denominator)
    if a is None or b is None:
        return None
    v = dict(a)
    for p, e in b.items():
        v[p] = v.get(p, 0) - e
    return {p: e for p, e in v.items() if e}


def vec_mul(a, b, k=1):
    out = dict(a)
    for p, e in b.items():
        out[p] = out.get(p, 0) + k * e
    return {p: e for p, e in out.items() if e}


def vec_scale(a, k):
    return {p: e * Fraction(k) for p, e in a.items() if e * Fraction(k)}


def vec_to_q(v):
    """vector with all-integer exponents -> Fraction (None otherwise)"""
    out = Fraction(1)
    for p, e in v.items():
        e = Fraction(e)
        if e.denominator != 1:
            return None
        if abs(e) > 400:
            return None
        out *= Fraction(p) ** int(e)
    return out


def exact_log(a, b):
    """exact rational r with b**r == a, for positive Fractions (b != 1); None if there is none"""
    a, b = Fraction(a), Fraction(b)
    if a == 1:
        return Fraction(0)
    va, vb = vec_of(a), vec_of(b)
    if va is None or vb is None or not vb:
        return None
    if set(va) != set(vb):
        return None
    r = None
    for p in vb:
        t = Fraction(va[p], vb[p])
        if r is None:
            r = t
        elif r != t:
            return None
    return r


def vec_exact_log(va, vb):
    """same, but for (possibly fractional-exponent) vectors"""
    if not va:
        return Fraction(0)
    if not vb or set(va) != set(vb):
        return None
    r = None
    for p in vb:
        t = Fraction(va[p]) / Fraction(vb[p])
        if r is None:
            r = t
        elif r != t:
            return None
    return r


def primitive_root(q):
    """q>0, != 1 -> (u, m) with u > 1 an integer-exponent 'smallest' base and q == u**m (m integer)"""
    v = vec_of(q)
    if not v:
        return None
    g = 0
    for e in v.values():
        g = gcd(g, abs(e))
    u = {p: e // g for p, e in v.items()}
    uq = vec_to_q(u)
    if uq is None:
        return None
    if uq < 1:
        return 1 / uq, -g
    return uq, g


# ----------------------------------------------------------- tokenizer/parser ----

MAXLEN = 140


def normalise(s, plain=False):
    s = str(s or "")
    if plain:
        s = s.replace("π", " pi ")
    for ch in ("‒", "–", "—", "―", "−", "‐"):
        s = s.replace(ch, "-")
    s = s.replace("×", "*").replace("÷", "/").replace("·", "*").replace("√", "sqrt")
    sup = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}
    for k, v in sup.items():
        s = s.replace(k, "^" + v)
    sub = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9"}
    for k, v in sub.items():
        s = s.replace(k, "_" + v if False else v)
    s = s.replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")")
    return s.strip() if plain else s.strip().lower()


_NUM = re.compile(r"\d+(?:\.\d+)?|\.\d+")


class Parser:
    def __init__(self, text, plain=False):
        self.plain = plain
        s = normalise(text, plain)
        if not s:
            raise LogErr("Please type something first.")
        if len(s) > MAXLEN:
            raise LogErr("That is too long. Please use a shorter expression.")
        if s.count("(") != s.count(")"):
            raise LogErr("The brackets do not match: check that every ( has a ).")
        _okc = r"[^0-9a-zA-Z+\-*/^().,_\s=]" if plain else r"[^0-9a-z+\-*/^().,_\s=]"
        if re.search(_okc, s):
            bad = re.search(_okc, s).group()
            raise LogErr(f"I could not understand the symbol &lsquo;{esc(bad)}&rsquo;.")
        self.s = s
        self.i = 0
        self.depth = 0

    # -- helpers
    def ws(self):
        while self.i < len(self.s) and self.s[self.i] == " ":
            self.i += 1

    def peek(self):
        self.ws()
        return self.s[self.i] if self.i < len(self.s) else None

    def eat(self, ch):
        if self.peek() == ch:
            self.i += 1
            return True
        return False

    def parse(self):
        e = self.expr()
        if self.peek() is not None:
            raise LogErr(f"I could not understand &lsquo;{esc(self.s[self.i:self.i + 8])}&rsquo;. Use * between things you multiply, and brackets around each log's inside.")
        return e

    # -- grammar
    def expr(self):
        left = self.term()
        while self.peek() in ("+", "-"):
            op = self.s[self.i]
            self.i += 1
            right = self.term()
            left = ("add" if op == "+" else "sub", left, right)
        return left

    def starts_factor(self):
        c = self.peek()
        return c is not None and (c == "(" or c.isalpha())

    def term(self):
        left = self.unary()
        while True:
            c = self.peek()
            if c == "*":
                self.i += 1
                left = ("mul", left, self.unary())
            elif c == "/":
                self.i += 1
                left = ("div", left, self.unary())
            elif self.starts_factor():
                left = ("mul", left, self.power())
            else:
                break
        return left

    def unary(self):
        c = self.peek()
        if c == "-":
            self.i += 1
            return ("neg", self.unary())
        if c == "+":
            self.i += 1
            return self.unary()
        return self.power()

    def power(self):
        base = self.atom()
        if self.peek() == "^":
            self.i += 1
            neg = False
            if self.peek() == "-":
                self.i += 1
                neg = True
            elif self.peek() == "+":
                self.i += 1
            ex = self.power_operand()
            if neg:
                ex = ("neg", ex)
            return ("pow", base, ex)
        return base

    def power_operand(self):
        # exponent: a number, letter, bracket or function, itself possibly raised (right associative)
        return self.power()

    def number(self):
        self.ws()
        m = _NUM.match(self.s, self.i)
        if not m:
            raise LogErr("I expected a number here.")
        self.i = m.end()
        return Fraction(m.group())

    def paren(self):
        if not self.eat("("):
            raise LogErr("I expected a bracket ( here. Write the log's inside in brackets, like log(100).")
        self.depth += 1
        if self.depth > 10:
            raise LogErr("Too many brackets inside brackets.")
        e = self.expr()
        if not self.eat(")"):
            raise LogErr("A bracket is not closed.")
        self.depth -= 1
        return e

    def simple_operand(self):
        """argument without brackets: log 100, log x, sqrt 2"""
        self.ws()
        c = self.peek()
        if c == "(":
            return self.paren()
        if c is not None and (c.isdigit() or c == "."):
            return ("num", self.number())
        if c is not None and c.isalpha():
            return self.atom()
        if re.search(r"sqrt\s*$", self.s[:self.i]):
            raise LogErr("The square root sign needs a number after it, like &radic;50 or &radic;(x + 5).")
        if re.search(r"\bln?\s*$|log\w*\s*$", self.s[:self.i]):
            raise LogErr("The log needs something to take the log of, like log(100).")
        raise LogErr("Something is missing here: I expected a number or a bracket after what you typed (for example after +, &minus;, &times; or &divide;).")

    def base_spec(self):
        c = self.s[self.i] if self.i < len(self.s) else None
        if c == "(":
            return self.paren()
        if c is not None and (c.isdigit() or c == "."):
            return ("num", self.number())
        if c is not None and c.isalpha():
            self.i += 1
            return ("const", "e") if c == "e" else ("var", c)
        raise LogErr("After log_ write the base, like log_2(8) or log_(1/2)(4).")

    def atom(self):
        self.ws()
        if self.i >= len(self.s):
            raise LogErr("The expression ends too early. Check for a missing number or bracket.")
        c = self.s[self.i]
        if c == "(":
            return self.paren()
        if c.isdigit() or c == ".":
            return ("num", self.number())
        if c.isalpha():
            m = re.match(r"[A-Za-z]+" if self.plain else r"[a-z]+", self.s[self.i:])
            word = m.group()
            if self.plain:
                if word.startswith("sqrt"):
                    self.i += 4
                    return ("sqrt", self.simple_operand())
                if word == "pi":
                    self.i += 2
                    return ("const", "pi")
                self.i += 1
                return ("var", c)
            if word.startswith("log") or word.startswith("lg"):
                k = 3 if word.startswith("log") else 2
                self.i += k
                base = None
                if self.i < len(self.s) and self.s[self.i] == "_":
                    self.i += 1
                    base = self.base_spec()
                else:
                    m2 = re.match(r"(\d+(?:\.\d+)?)(?=\s*\()", self.s[self.i:])
                    if m2:
                        base = ("num", self.number())
                arg = self.simple_operand()
                return ("log", arg, base)
            if word.startswith("ln"):
                self.i += 2
                return ("log", self.simple_operand(), ("const", "e"))
            if word.startswith("sqrt"):
                self.i += 4
                return ("sqrt", self.simple_operand())
            self.i += 1
            return ("const", "e") if c == "e" else ("var", c)
        raise LogErr(f"I could not understand &lsquo;{esc(c)}&rsquo; here.")


def parse(text, plain=False):
    """plain=True: algebra mode (letters keep their case, e is an ordinary letter, pi/π is a constant, no log or ln)"""
    return Parser(text, plain).parse()


# ------------------------------------------------------------- AST helpers ----

def variables(node, out=None):
    out = set() if out is None else out
    k = node[0]
    if k == "var":
        out.add(node[1])
    elif k in ("neg", "sqrt"):
        variables(node[1], out)
    elif k in ("add", "sub", "mul", "div", "pow"):
        variables(node[1], out)
        variables(node[2], out)
    elif k == "log":
        variables(node[1], out)
        if node[2] is not None:
            variables(node[2], out)
    return out


def has_log(node):
    k = node[0]
    if k == "log":
        return True
    if k in ("neg", "sqrt"):
        return has_log(node[1])
    if k in ("add", "sub", "mul", "div", "pow"):
        return has_log(node[1]) or has_log(node[2])
    return False


def logs_in(node, out=None):
    out = [] if out is None else out
    k = node[0]
    if k == "log":
        out.append(node)
        logs_in(node[1], out)
    elif k in ("neg", "sqrt"):
        logs_in(node[1], out)
    elif k in ("add", "sub", "mul", "div", "pow"):
        logs_in(node[1], out)
        logs_in(node[2], out)
    return out


def contains_var_in_exponent(node, v):
    k = node[0]
    if k == "pow":
        if v in variables(node[2]):
            return True
        return contains_var_in_exponent(node[1], v) or contains_var_in_exponent(node[2], v)
    if k in ("neg", "sqrt"):
        return contains_var_in_exponent(node[1], v)
    if k in ("add", "sub", "mul", "div"):
        return contains_var_in_exponent(node[1], v) or contains_var_in_exponent(node[2], v)
    if k == "log":
        return contains_var_in_exponent(node[1], v)
    return False


# ------------------------------------------------------------- printing ----

def _is_num(n):
    return n[0] == "num"


def pp(node, prec=0):
    k = node[0]
    if k == "num":
        s = fmtq(node[1])
        return s
    if k == "var":
        return node[1]
    if k == "const":
        return "e"
    if k == "neg":
        s = MINUS + pp(node[1], 3)
        return f"({s})" if prec > 1 else s
    if k == "add":
        s = f"{pp(node[1], 1)} + {pp(node[2], 1)}"
        return f"({s})" if prec > 1 else s
    if k == "sub":
        s = f"{pp(node[1], 1)} {MINUS} {pp(node[2], 2)}"
        return f"({s})" if prec > 1 else s
    if k == "mul":
        a, b = node[1], node[2]
        pa, pb = pp(a, 2), pp(b, 2)
        simple = lambda n: n[0] in ("var", "const") or (n[0] == "pow" and n[1][0] in ("var", "const")) or n[0] == "log"
        if (a[0] == "num" and (simple(b) or b[0] in ("add", "sub", "sqrt"))) or (a[0] in ("var", "const") and simple(b)) \
                or (a[0] in ("add", "sub") and b[0] in ("add", "sub")) or (simple(a) and b[0] in ("add", "sub")):
            s = pa + pp(b, 3 if b[0] in ("add", "sub") else 2)
        else:
            s = f"{pa} &times; {pb}"
        return f"({s})" if prec > 2 else s
    if k == "div":
        s = f"{pp(node[1], 2)}/{pp(node[2], 3)}"
        return f"({s})" if prec > 2 else s
    if k == "pow":
        b = node[1]
        bs = pp(b, 4) if b[0] in ("var", "const", "log", "sqrt") or (b[0] == "num" and b[1] >= 0 and b[1].denominator == 1) else f"({pp(b)})"
        return f"{bs}<sup>{pp(node[2])}</sup>"
    if k == "sqrt":
        a = node[1]
        if a[0] in ("num", "var"):
            return f"&radic;{pp(a)}"
        return f"&radic;({pp(a)})"
    if k == "log":
        return log_name(node[2]) + f"({pp(node[1])})"
    raise LogErr("Cannot display this expression.")


def log_name(base):
    if base is None or (base[0] == "num" and base[1] == 10):
        return "log"
    if base[0] == "const":
        return "ln"
    return f"log<sub>{pp(base)}</sub>"


def base_val(base):
    """base node (None = 10) -> Fraction, 'e', or None (variable)"""
    if base is None:
        return Fraction(10)
    if base[0] == "const":
        return "e"
    return None


# --------------------------------------------------------- numeric evaluation ----

def ev_vec(node):
    """positive 'radical monomial' as {prime: Fraction exponent}, or None"""
    k = node[0]
    if k == "num":
        v = vec_of(node[1])
        return v
    if k == "sqrt":
        v = ev_vec(node[1])
        return None if v is None else vec_scale(v, Fraction(1, 2))
    if k == "mul":
        a, b = ev_vec(node[1]), ev_vec(node[2])
        return None if a is None or b is None else vec_mul(a, b)
    if k == "div":
        a, b = ev_vec(node[1]), ev_vec(node[2])
        return None if a is None or b is None else vec_mul(a, b, -1)
    if k == "pow":
        a = ev_vec(node[1])
        e = ev_exact(node[2])
        if a is None or e is None or abs(e) > 60:
            return None
        return vec_scale(a, e)
    if k in ("add", "sub", "neg"):
        q = ev_exact(node)
        if q is None or q <= 0:
            return None
        return vec_of(q)
    return None


def ev_exact(node):
    """exact Fraction value of a number-only expression (None if not rational)"""
    k = node[0]
    if k == "num":
        return node[1]
    if k == "neg":
        a = ev_exact(node[1])
        return None if a is None else -a
    if k in ("add", "sub", "mul", "div"):
        a, b = ev_exact(node[1]), ev_exact(node[2])
        if a is None or b is None:
            return None
        if k == "add":
            return a + b
        if k == "sub":
            return a - b
        if k == "mul":
            return a * b
        if b == 0:
            raise LogErr("That divides by zero.")
        return a / b
    if k in ("pow", "sqrt"):
        if k == "pow":
            e = ev_exact(node[2])
            a0 = ev_exact(node[1])
            if a0 is not None and e is not None and e.denominator == 1 and abs(e) <= 60:
                if a0 == 0 and e < 0:
                    raise LogErr("That divides by zero.")
                return a0 ** int(e)
        v = ev_vec(node)
        if v is None:
            return None
        return vec_to_q(v)
    return None


def ev_float(node, subs=None):
    k = node[0]
    if k == "num":
        return float(node[1])
    if k == "const":
        return math.e
    if k == "var":
        if subs and node[1] in subs:
            return float(subs[node[1]])
        raise NeedValue("This contains a letter, so it has no single number value yet.")
    if k == "neg":
        return -ev_float(node[1], subs)
    if k == "add":
        return ev_float(node[1], subs) + ev_float(node[2], subs)
    if k == "sub":
        return ev_float(node[1], subs) - ev_float(node[2], subs)
    if k == "mul":
        return ev_float(node[1], subs) * ev_float(node[2], subs)
    if k == "div":
        d = ev_float(node[2], subs)
        if d == 0:
            raise LogErr("That divides by zero.")
        return ev_float(node[1], subs) / d
    if k == "pow":
        a, e = ev_float(node[1], subs), ev_float(node[2], subs)
        try:
            r = a ** e
        except (ZeroDivisionError, OverflowError):
            raise LogErr("That number is too big or divides by zero.")
        if isinstance(r, complex):
            raise LogErr("That would need the root of a negative number.")
        return r
    if k == "sqrt":
        a = ev_float(node[1], subs)
        if a < 0:
            raise LogErr("You cannot take the square root of a negative number here.")
        return math.sqrt(a)
    if k == "log":
        a = ev_float(node[1], subs)
        b = math.e if (node[2] is not None and node[2][0] == "const") else (10.0 if node[2] is None else ev_float(node[2], subs))
        if a <= 0:
            raise LogErr("A logarithm only exists for a positive number.")
        if b <= 0 or b == 1:
            raise LogErr("A logarithm base must be positive and not 1.")
        return math.log(a) / math.log(b)
    raise LogErr("Cannot work this out.")


# --------------------------------------------------------- small polynomials ----

class P1:
    """univariate polynomial with Fraction coefficients (ascending)"""
    __slots__ = ("c",)

    def __init__(self, c=None):
        c = [Fraction(x) for x in (c or [])]
        while c and c[-1] == 0:
            c.pop()
        self.c = c

    @staticmethod
    def const(v):
        return P1([v])

    @staticmethod
    def x():
        return P1([0, 1])

    def deg(self):
        return len(self.c) - 1 if self.c else -1

    def is_zero(self):
        return not self.c

    def __add__(self, o):
        n = max(len(self.c), len(o.c))
        return P1([(self.c[i] if i < len(self.c) else 0) + (o.c[i] if i < len(o.c) else 0) for i in range(n)])

    def __neg__(self):
        return P1([-a for a in self.c])

    def __sub__(self, o):
        return self + (-o)

    def __mul__(self, o):
        if not self.c or not o.c:
            return P1()
        r = [Fraction(0)] * (len(self.c) + len(o.c) - 1)
        for i, a in enumerate(self.c):
            for j, b in enumerate(o.c):
                r[i + j] += a * b
        return P1(r)

    def scale(self, k):
        return P1([a * Fraction(k) for a in self.c])

    def __pow__(self, n):
        r = P1([1])
        for _ in range(n):
            r = r * self
        return r

    def at(self, v):
        r = Fraction(0) if isinstance(v, Fraction) else 0.0
        for a in reversed(self.c):
            r = r * v + a
        return r

    def lead(self):
        return self.c[-1] if self.c else Fraction(0)

    def text(self, var="x"):
        if not self.c:
            return "0"
        out = ""
        for d in range(len(self.c) - 1, -1, -1):
            a = self.c[d]
            if a == 0:
                continue
            mag = abs(a)
            if d == 0:
                body = fmtq(mag)
            else:
                co = "" if mag == 1 else fmtq(mag)
                body = co + var + (f"<sup>{d}</sup>" if d > 1 else "")
            if not out:
                out = (MINUS if a < 0 else "") + body
            else:
                out += f" {MINUS if a < 0 else '+'} {body}"
        return out


def to_poly(node, v, sub=None):
    """AST -> P1 in variable v (division by numbers only, whole-number powers).
    sub = {node: P1} lets a chosen sub-expression (like log x) stand for a new unknown."""
    if sub and node in sub:
        return sub[node]
    k = node[0]
    if k == "num":
        return P1.const(node[1])
    if k == "var":
        if node[1] == v:
            return P1.x()
        raise LogErr(f"I found another letter (&lsquo;{esc(node[1])}&rsquo;). Use only one unknown, like x.")
    if k == "const":
        raise LogErr("The number e cannot be used inside this part of the equation.")
    if k == "neg":
        return -to_poly(node[1], v, sub)
    if k == "add":
        return to_poly(node[1], v, sub) + to_poly(node[2], v, sub)
    if k == "sub":
        return to_poly(node[1], v, sub) - to_poly(node[2], v, sub)
    if k == "mul":
        return to_poly(node[1], v, sub) * to_poly(node[2], v, sub)
    if k == "div":
        d = to_poly(node[2], v, sub)
        if d.deg() != 0:
            raise LogErr("I can only divide by plain numbers inside a logarithm here.")
        return to_poly(node[1], v, sub).scale(1 / d.c[0])
    if k == "pow":
        e = ev_exact(node[2]) if not variables(node[2]) else None
        if e is None or e.denominator != 1 or e < 0 or e > 6:
            raise LogErr("Powers inside the equation must be small whole numbers (like x^2).")
        return to_poly(node[1], v, sub) ** int(e)
    raise LogErr("This kind of expression is not supported inside a logarithm here.")


def real_roots(p):
    """roots of P1 up to degree 4 (rational roots peeled off first). -> list of (Fraction|None, float, text)"""
    c = p.c
    if len(c) <= 1:
        return []
    roots = []
    cur = P1(c)
    # peel rational roots (rational root theorem)
    while cur.deg() > 2:
        found = None
        # clear denominators
        den = 1
        for a in cur.c:
            den = den * a.denominator // gcd(den, a.denominator)
        ints = [int(a * den) for a in cur.c]
        a0, an = abs(ints[0]), abs(ints[-1])
        if a0 == 0:
            found = Fraction(0)
        else:
            if a0 > 10 ** 8 or an > 10 ** 8:
                raise LogErr("The numbers are too big for me to solve this.")
            divs0 = [d for d in range(1, isqrt(a0) + 1) if a0 % d == 0]
            divs0 = sorted(set(divs0 + [a0 // d for d in divs0]))
            divsn = [d for d in range(1, isqrt(an) + 1) if an % d == 0]
            divsn = sorted(set(divsn + [an // d for d in divsn]))
            for pp_ in divs0:
                for qq in divsn:
                    for sgn in (1, -1):
                        r = Fraction(sgn * pp_, qq)
                        if cur.at(r) == 0:
                            found = r
                            break
                    if found is not None:
                        break
                if found is not None:
                    break
        if found is None:
            raise LogErr("This equation is too hard to solve by hand (it needs a cubic or quartic formula). Check that you typed it correctly.")
        roots.append((found, float(found), fmtq(found)))
        # synthetic division
        co = cur.c[::-1]
        out = [co[0]]
        for a in co[1:]:
            out.append(a + out[-1] * found)
        cur = P1(out[:-1][::-1])
    if cur.deg() == 2:
        a, b, cc = cur.c[2], cur.c[1], cur.c[0]
        D = b * b - 4 * a * cc
        if D >= 0:
            ex, _ = _sqrt_exact(D)
            if ex is not None:
                for s in (-1, 1):
                    r = (-b + s * ex) / (2 * a)
                    roots.append((r, float(r), fmtq(r)))
            else:
                sd = math.sqrt(float(D))
                for s in (-1, 1):
                    f = (-float(b) + s * sd) / (2 * float(a))
                    roots.append((None, f, surd_text(-b / (2 * a), D, 2 * a, s)))
    elif cur.deg() == 1:
        r = -cur.c[0] / cur.c[1]
        roots.append((r, float(r), fmtq(r)))
    uniq = []
    for r in roots:
        if not any(abs(r[1] - u[1]) < 1e-12 for u in uniq):
            uniq.append(r)
    return sorted(uniq, key=lambda t: t[1])


def _sqrt_exact(q):
    q = Fraction(q)
    if q < 0:
        return None, None
    p, d = q.numerator, q.denominator
    ip, idd = isqrt(p), isqrt(d)
    if ip * ip == p and idd * idd == d:
        r = Fraction(ip, idd)
        return r, float(r)
    return None, math.sqrt(float(q))


def _split_square(n):
    """positive int n -> (s, t) with n == s*s*t, t square-free (t may stay big if factoring fails)"""
    f = factor_int(n)
    if f is None:
        return 1, n
    sq, rest = 1, 1
    for p, e in f.items():
        sq *= p ** (e // 2)
        rest *= p ** (e % 2)
    return sq, rest


def surd_text(r, D, twoa, sign):
    """x = r + sign * sqrt(D)/twoa  ->  'a + b&radic;t' style text (D positive, non-square Fraction)"""
    D = Fraction(D)
    # sqrt(p/q) = sqrt(p*q)/q
    pq = D.numerator * D.denominator
    s, t = _split_square(pq)
    k = Fraction(s, D.denominator) / Fraction(twoa)      # coefficient of sqrt(t)
    r = Fraction(r)
    den = r.denominator * k.denominator // gcd(r.denominator, k.denominator)
    R, K = r * den, k * den
    from math import gcd as _g
    g = _g(_g(abs(R.numerator), abs(K.numerator)), den) or 1
    R, K, den = R / g, K / g, Fraction(den, g)
    sgn_k = sign * (1 if K > 0 else -1)
    Kabs = abs(K)
    kt = ("" if Kabs == 1 else fmtq(Kabs)) + f"&radic;{t}"
    if R == 0:
        body = ("" if sgn_k > 0 else MINUS) + kt
    else:
        body = f"{fmtq(R)} {'+' if sgn_k > 0 else MINUS} {kt}"
    if den != 1:
        return f"({body})/{fmtq(den)}" if R != 0 or Kabs != 1 else f"{body}/{fmtq(den)}"
    return body
