"""Function parser for the Graphs topic (pure Python + numpy; no sympy).

Understands things students really type:
    x^2 - 2x - 3      sinx      sin x      sin^2 x      sin(^2)x      sin²x
    3sinx - 4cos^3x   sin(2x+30)   2sin 2x cos x   tan x   1/x   2^x   e^x   sqrt(x)   |x| as abs(x)
"""
import math
import re

import numpy as np


class GErr(Exception):
    pass


FUNCS = ["cosec", "csc", "sqrt", "sin", "cos", "tan", "sec", "cot", "abs", "exp", "log", "ln"]
SUP = {"²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "¹": "1", "⁰": "0"}
MAXLEN = 200


def tokenize(s):
    s = str(s or "")
    if len(s) > MAXLEN:
        raise GErr("That expression is too long.")
    s = s.replace("−", "-").replace("–", "-").replace("×", "*").replace("÷", "/").replace("√", "sqrt").replace("π", "pi").replace("·", "*")
    s = s.replace("°", "").replace("degrees", "").replace("deg", "")
    out = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch.isspace():
            i += 1
        elif ch in SUP:
            j = i
            digs = ""
            while j < n and s[j] in SUP:
                digs += SUP[s[j]]
                j += 1
            out.append(("op", "^"))
            out.append(("num", float(digs)))
            i = j
        elif ch.isdigit() or (ch == "." and i + 1 < n and s[i + 1].isdigit()):
            m = re.match(r"\d*\.?\d+(?:[eE](?![a-zA-Z])[+-]?\d+)?|\d+\.", s[i:])
            txt = m.group(0)
            out.append(("num", float(txt)))
            i += len(txt)
        elif ch.isalpha():
            low = s[i:].lower()
            for f in FUNCS:
                if low.startswith(f):
                    out.append(("func", {"csc": "cosec"}.get(f, f)))
                    i += len(f)
                    break
            else:
                if low.startswith("pi"):
                    out.append(("const", "pi"))
                    i += 2
                elif ch in "xX":
                    out.append(("var", "x"))
                    i += 1
                elif ch in "eE":
                    out.append(("const", "e"))
                    i += 1
                else:
                    raise GErr(f"I can only use the letter x, but I found '{ch}'. Write functions like sin x, cos x, tan x, x^2 ...")
        elif ch in "+-*/^()":
            out.append(("op", ch))
            i += 1
        elif ch == "|":
            out.append(("op", "|"))
            i += 1
        else:
            raise GErr(f"I could not understand the symbol '{ch}'.")
    return out


class Parser:
    def __init__(self, toks):
        self.t = toks
        self.i = 0
        self.depth = 0

    def peek(self, k=0):
        return self.t[self.i + k] if self.i + k < len(self.t) else (None, None)

    def eat(self):
        tk = self.t[self.i]
        self.i += 1
        return tk

    def isop(self, v, k=0):
        t = self.peek(k)
        return t[0] == "op" and t[1] == v

    def starts_atom(self):
        t = self.peek()
        if t[0] in ("num", "var", "const", "func"):
            return True
        return t[0] == "op" and t[1] in ("(", "|")

    def expr(self):
        node = self.term()
        while self.isop("+") or self.isop("-"):
            op = self.eat()[1]
            r = self.term()
            node = ("add" if op == "+" else "sub", node, r)
        return node

    def term(self):
        node = self.unary()
        while True:
            if self.isop("*"):
                self.eat()
                node = ("mul", node, self.unary())
            elif self.isop("/"):
                self.eat()
                node = ("div", node, self.unary())
            elif self.starts_atom():
                node = ("mul", node, self.unary_noSign())
            else:
                return node

    def unary(self):
        if self.isop("-"):
            self.eat()
            return ("neg", self.unary())
        if self.isop("+"):
            self.eat()
            return self.unary()
        return self.power()

    def unary_noSign(self):
        return self.power()

    def power(self):
        base = self.atom()
        if self.isop("^"):
            self.eat()
            ex = self.exponent()
            return ("pow", base, ex)
        return base

    def exponent(self):
        if self.isop("-"):
            self.eat()
            return ("neg", self.exponent())
        if self.isop("+"):
            self.eat()
            return self.exponent()
        if self.isop("("):
            self.eat()
            e = self.expr()
            self.close()
            return e
        t = self.peek()
        if t[0] == "num":
            self.eat()
            return ("num", t[1])
        if t[0] in ("var", "const"):
            self.eat()
            return (t[0], t[1])
        raise GErr("A power sign ^ needs a number after it, like x^2.")

    def close(self):
        if not self.isop(")"):
            raise GErr("A bracket was opened but not closed. Check your brackets ( ).")
        self.eat()

    def atom(self):
        t = self.peek()
        if t[0] == "num":
            self.eat()
            return ("num", t[1])
        if t[0] == "var":
            self.eat()
            return ("var", "x")
        if t[0] == "const":
            self.eat()
            return ("const", t[1])
        if t[0] == "func":
            return self.func()
        if self.isop("("):
            self.depth += 1
            if self.depth > 30:
                raise GErr("Too many brackets inside brackets.")
            self.eat()
            e = self.expr()
            self.close()
            self.depth -= 1
            return e
        if self.isop("|"):
            self.eat()
            e = self.expr()
            if not self.isop("|"):
                raise GErr("A | sign was opened but not closed.")
            self.eat()
            return ("abs", e)
        if t[0] is None:
            raise GErr("The expression ends too early. Something is missing after the last sign.")
        raise GErr(f"I did not expect '{t[1]}' there.")

    def func(self):
        name = self.eat()[1]
        power = None
        if self.isop("^"):
            self.eat()
            power = self.exponent()
        elif self.isop("(") and self.isop("^", 1):
            self.eat()
            self.eat()
            power = self.exponent()
            self.close()
        # argument
        if self.isop("("):
            self.depth += 1
            if self.depth > 30:
                raise GErr("Too many brackets inside brackets.")
            self.eat()
            arg = self.expr()
            self.close()
            self.depth -= 1
        else:
            arg = self.bare_arg(name)
        node = (name, arg)
        if power is not None:
            node = ("pow", node, power)
        return node

    def bare_arg(self, name):
        """sin x, sin 2x, sin 30, sin x^2, sin pi x : number and/or x/pi, with optional power on x"""
        parts = []
        t = self.peek()
        if t[0] == "num":
            self.eat()
            parts.append(("num", t[1]))
            t = self.peek()
        if t[0] in ("var", "const"):
            self.eat()
            a = (t[0], t[1] if t[0] == "const" else "x")
            if self.isop("^"):
                self.eat()
                a = ("pow", a, self.exponent())
            parts.append(a)
        if not parts:
            raise GErr(f"{name} needs an angle after it, for example {name} x, {name} 2x or {name}(x + 30).")
        node = parts[0]
        for p in parts[1:]:
            node = ("mul", node, p)
        return node


def clean_function_text(s):
    """allow y = ..., f(x) = ..., or lhs = rhs"""
    s = str(s or "").strip()
    if not s:
        raise GErr("Please type the function first, for example x^2 - 2x - 3 or 3sin x - 4cos^3 x.")
    if s.count("=") > 1:
        raise GErr("Use only one = sign.")
    if "=" in s:
        lhs, rhs = s.split("=", 1)
        key = lhs.strip().lower().replace(" ", "")
        if key in ("y", "f(x)", "g(x)", "f", "g", "fx", "gx", "h(x)"):
            return rhs.strip()
        return f"({lhs.strip()}) - ({rhs.strip()})"
    return s


def parse(text):
    toks = tokenize(clean_function_text(text))
    p = Parser(toks)
    node = p.expr()
    if p.i < len(toks):
        t = toks[p.i]
        if t == ("op", ")"):
            raise GErr("There is a closing bracket ) without an opening one.")
        raise GErr(f"I could not read the part starting at '{t[1]}'. Check the signs between the terms.")
    return node


def parse_number(text, label="the number"):
    """x min, x max, step: numbers, fractions, or things like pi/6, 2pi"""
    s = str(text if text is not None else "").strip()
    if s == "":
        raise GErr(f"Please fill in {label}.")
    try:
        node = parse(s)
    except GErr:
        raise GErr(f"{label}: '{s}' is not a number. Use things like 30, -2.5, 3/4 or pi/6.")
    if _has_x(node):
        raise GErr(f"{label} must be a number, without x.")
    v = float(evaluate(node, 0.0, "rad"))
    if not math.isfinite(v):
        raise GErr(f"{label} is not a valid number.")
    return v


def _has_x(n):
    if n[0] == "var":
        return True
    if n[0] in ("num", "const"):
        return False
    return any(_has_x(c) for c in n[1:] if isinstance(c, tuple))


def has_trig(node):
    if node[0] in ("sin", "cos", "tan", "sec", "cosec", "cot"):
        return True
    if node[0] in ("num", "var", "const"):
        return False
    return any(has_trig(c) for c in node[1:] if isinstance(c, tuple))


def has_pole(node):
    """may blow up (tan, sec, cosec, cot, division by something with x)"""
    if node[0] in ("tan", "sec", "cosec", "cot"):
        return True
    if node[0] == "div" and _has_x(node[2]):
        return True
    if node[0] == "pow" and node[2][0] == "neg":
        return True
    if node[0] in ("num", "var", "const"):
        return False
    return any(has_pole(c) for c in node[1:] if isinstance(c, tuple))


def evaluate(node, xv, unit="deg"):
    """evaluate for a number or numpy array x. Trig functions use degrees when unit == 'deg'."""
    k = node[0]
    with np.errstate(all="ignore"):
        if k == "num":
            return node[1] + 0.0 * xv if not np.isscalar(xv) else node[1]
        if k == "var":
            return xv
        if k == "const":
            return math.pi if node[1] == "pi" else math.e
        if k == "neg":
            return -evaluate(node[1], xv, unit)
        if k in ("add", "sub", "mul", "div"):
            a = evaluate(node[1], xv, unit)
            b = evaluate(node[2], xv, unit)
            if k == "add":
                return a + b
            if k == "sub":
                return a - b
            if k == "mul":
                return a * b
            return np.divide(a, b) if not (np.isscalar(a) and np.isscalar(b)) else (a / b if b != 0 else float("nan"))
        if k == "pow":
            a = evaluate(node[1], xv, unit)
            b = evaluate(node[2], xv, unit)
            if np.isscalar(a) and np.isscalar(b):
                try:
                    r = a ** b
                    return float(r.real) if isinstance(r, complex) else r
                except (ZeroDivisionError, OverflowError, ValueError):
                    return float("nan")
            a = np.asarray(a, dtype=float)
            b = np.asarray(b, dtype=float)
            # real roots of negative numbers for odd-root exponents like x^(1/3)
            r = np.power(a, b)
            return r
        a = evaluate(node[1], xv, unit)
        arr = a
        if k in ("sin", "cos", "tan", "sec", "cosec", "cot"):
            rad = np.radians(arr) if unit == "deg" else arr
            if k == "sin":
                return np.sin(rad)
            if k == "cos":
                return np.cos(rad)
            if k == "tan":
                return np.tan(rad)
            if k == "sec":
                return 1.0 / np.cos(rad)
            if k == "cosec":
                return 1.0 / np.sin(rad)
            return 1.0 / np.tan(rad)
        if k == "sqrt":
            return np.sqrt(arr)
        if k == "abs":
            return np.abs(arr)
        if k == "exp":
            return np.exp(arr)
        if k == "ln":
            return np.log(arr)
        if k == "log":
            return np.log10(arr)
    raise GErr("Unsupported function.")


# ------------------------------------------------------------------ pretty printing (plain unicode)
SUPD = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def _num(v):
    if abs(v - round(v)) < 1e-12:
        return str(int(round(v)))
    return f"{v:.6g}"


PREC = {"add": 1, "sub": 1, "neg": 2, "mul": 3, "div": 3, "pow": 4}


def fmt(node, parent=0):
    k = node[0]
    if k == "num":
        return _num(node[1])
    if k == "var":
        return "x"
    if k == "const":
        return "π" if node[1] == "pi" else "e"
    if k == "neg":
        s = "−" + fmt(node[1], 2)
        return f"({s})" if parent > 2 else s
    if k in ("add", "sub"):
        s = fmt(node[1], 1) + (" + " if k == "add" else " − ") + fmt(node[2], 2)
        return f"({s})" if parent > 1 else s
    if k == "mul":
        a, b = node[1], node[2]
        sa, sb = fmt(a, 3), fmt(b, 3)
        if a[0] == "num" and (b[0] in ("var", "const") or b[0] == "pow" and b[1][0] in ("var", "const")):
            s = sa + sb
        elif a[0] == "num" and b[0] in ("sin", "cos", "tan", "sec", "cosec", "cot", "sqrt", "abs", "ln", "log", "exp", "pow"):
            s = sa + " " + sb
        elif b[0] in ("sin", "cos", "tan", "sec", "cosec", "cot", "sqrt") or (b[0] == "pow" and b[1][0] in ("sin", "cos", "tan", "sec", "cosec", "cot")):
            s = sa + " " + sb
        elif a[0] == "var" and b[0] == "var":
            s = sa + sb
        else:
            s = sa + " × " + sb if not (b[0] in ("add", "sub")) else sa + "(" + fmt(b) + ")"
        return f"({s})" if parent > 3 else s
    if k == "div":
        s = fmt(node[1], 3) + "/" + fmt(node[2], 4)
        return f"({s})" if parent > 3 else s
    if k == "pow":
        base, ex = node[1], node[2]
        if base[0] in ("sin", "cos", "tan", "sec", "cosec", "cot") and ex[0] == "num" and ex[1] == int(ex[1]) and 0 <= ex[1] <= 9:
            return base[0] + _num(ex[1]).translate(SUPD) + _arg(base[1])
        bs = fmt(base, 5) if base[0] in ("var", "const", "num") or base[0] in ("sin", "cos", "tan", "sec", "cosec", "cot", "sqrt", "abs") else "(" + fmt(base) + ")"
        if base[0] == "num" and base[1] < 0:
            bs = "(" + bs + ")"
        if ex[0] == "num" and ex[1] == int(ex[1]) and 0 <= ex[1] <= 9:
            return bs + _num(ex[1]).translate(SUPD)
        if ex[0] == "neg" and ex[1][0] == "num" and ex[1][1] == int(ex[1][1]) and ex[1][1] <= 9:
            return bs + ("-" + _num(ex[1][1])).translate(SUPD)
        if ex[0] in ("var", "const"):
            return bs + "^" + fmt(ex)
        return bs + "^(" + fmt(ex) + ")"
    # functions
    if k == "sqrt":
        a = node[1]
        return "\u221a" + (fmt(a) if a[0] in ("var", "const") or (a[0] == "num" and a[1] >= 0) else "(" + fmt(a) + ")")
    return k + _arg(node[1])


def _arg(a):
    if a[0] == "var" or (a[0] == "num" and a[1] >= 0) or a[0] == "const":
        return " " + fmt(a)
    if a[0] == "mul" and a[1][0] == "num" and a[2][0] in ("var",) and a[1][1] >= 0:
        return " " + fmt(a)
    return "(" + fmt(a) + ")"


def terms(node):
    """flatten top-level + and - into [(sign, node)]"""
    out = []

    def go(n, sg):
        if n[0] == "add":
            go(n[1], sg)
            go(n[2], sg)
        elif n[0] == "sub":
            go(n[1], sg)
            go(n[2], -sg)
        elif n[0] == "neg":
            go(n[1], -sg)
        else:
            out.append((sg, n))
    go(node, 1)
    return out
