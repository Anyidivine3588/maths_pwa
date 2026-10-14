"""Shared machinery for the Angles topic (pure Python, no sympy).

  * Lin / parse_lin    : a tiny parser for angle expressions such as 50, 2x or 3x+10
  * solve_eq           : solves a linear equation in x and explains every move
  * solve_angles       : applies the angle rules of a figure (relations), works out the
                         unknown angles and writes the working step by step
"""
import re
from fractions import Fraction

from tcommon import UErr, fm, exact_or_dec, esc, sfrac

DEG = "&deg;"
MINUS = "&minus;"
TIMES = "&times;"


def HL(s):
    return f"<span class='hl'>{s}</span>"


def nm(v, p=4):
    return fm(v, p).replace("-", MINUS)


# ----------------------------------------------------------------- expressions ---

class Lin:
    """a*x + b with exact fractions"""
    __slots__ = ("a", "b")

    def __init__(self, a=0, b=0):
        self.a = Fraction(a)
        self.b = Fraction(b)

    def __add__(self, o):
        return Lin(self.a + o.a, self.b + o.b)

    def __sub__(self, o):
        return Lin(self.a - o.a, self.b - o.b)

    def scale(self, k):
        k = Fraction(k)
        return Lin(self.a * k, self.b * k)

    def at(self, x):
        return self.a * x + self.b

    def const(self):
        return self.a == 0


def xterm(c):
    c = Fraction(c)
    if c == 1:
        return "x"
    if c == -1:
        return MINUS + "x"
    if c.denominator == 1:
        return nm(c) + "x"
    n_ = "x" if c.numerator == 1 else (MINUS + "x" if c.numerator == -1 else f"{nm(c.numerator)}x")
    return f"{n_}/{c.denominator}"


def lin_str(L, plain=False):
    parts = ""
    if L.a != 0:
        parts = xterm(L.a)
    if L.b != 0 or L.a == 0:
        if parts:
            parts += (" + " if L.b > 0 else " &minus; ") + fm(abs(L.b), 4)
        else:
            parts = nm(L.b)
    if plain:
        parts = parts.replace("&minus;", "−")
    return parts


def dstr(L):
    """a value inside working: 50° or (2x + 10)"""
    if L.a == 0:
        return f"{nm(L.b)}{DEG}"
    return f"({lin_str(L)})"


def _bad(raw, label):
    return UErr(f"{label}: I can't read '{esc(raw)}'. Use numbers and the letter x only, like 50, 2x or 3x+10.")


def parse_lin(text, label="the angle"):
    raw = text or ""
    s = (raw.strip().replace("−", "-").replace("–", "-").replace("×", "*").replace("÷", "/")
         .replace("°", "").replace("&deg;", "").replace("º", ""))
    if s == "":
        raise UErr(f"Please fill in {label}.")
    if len(s) > 40:
        raise UErr(f"{label}: that is too long. Keep it short, like 3x+10.")
    toks = []
    for m in re.finditer(r"\s*(?:(\d+(?:\.\d+)?)|([xX])|([()+\-*/])|(\S))", s):
        if m.group(4):
            raise _bad(raw, label)
        if m.group(1):
            if len(m.group(1)) > 12:
                raise UErr(f"{label}: that number is too long.")
            toks.append(("n", sfrac(m.group(1))))
        elif m.group(2):
            toks.append(("x", None))
        elif m.group(3):
            toks.append((m.group(3), None))
    pos = [0]
    depth = [0]

    def peek():
        return toks[pos[0]][0] if pos[0] < len(toks) else None

    def take():
        if pos[0] >= len(toks):
            raise _bad(raw, label)
        t = toks[pos[0]]
        pos[0] += 1
        return t

    def mul(v, w):
        if v.a != 0 and w.a != 0:
            raise UErr(f"{label}: x times x is not allowed here. Use simple things like 3x+10.")
        return Lin(v.a * w.b + v.b * w.a, v.b * w.b)

    def div(v, w):
        if w.a != 0:
            raise UErr(f"{label}: you cannot divide by x here.")
        if w.b == 0:
            raise UErr(f"{label}: you cannot divide by 0.")
        return Lin(v.a / w.b, v.b / w.b)

    def atom():
        kind, val = take()
        if kind == "n":
            return Lin(0, val)
        if kind == "x":
            return Lin(1, 0)
        if kind == "(":
            depth[0] += 1
            if depth[0] > 6:
                raise _bad(raw, label)
            v = expr()
            if peek() != ")":
                raise _bad(raw, label)
            take()
            depth[0] -= 1
            return v
        raise _bad(raw, label)

    def factor():
        p = peek()
        if p in ("+", "-"):
            take()
            v = factor()
            return v if p == "+" else Lin() - v
        return atom()

    def term():
        v = factor()
        while True:
            p = peek()
            if p == "*":
                take()
                v = mul(v, factor())
            elif p == "/":
                take()
                v = div(v, factor())
            elif p in ("x", "("):
                v = mul(v, factor())
            else:
                return v

    def expr():
        v = term()
        while peek() in ("+", "-"):
            op = take()[0]
            w = term()
            v = v + w if op == "+" else v - w
        return v

    v = expr()
    if pos[0] != len(toks):
        raise _bad(raw, label)
    return v


def parse_opt(text, label="the angle"):
    """blank -> None, otherwise a Lin"""
    if (text or "").strip() == "":
        return None
    return parse_lin(text, label)


# --------------------------------------------------------------- linear equation ---

def solve_eq(L, R, raw=None, relation=None):
    """Solve L = R for x. Returns (x, steps)."""
    steps = []
    if raw:
        steps.append(f"Put the angles into the rule{(' <b>' + relation + '</b>') if relation else ''}: <b>{raw}</b>")
        if raw.replace(" ", "") != f"{lin_str(L)} = {lin_str(R)}".replace(" ", ""):
            steps.append(f"Tidy up (add the x's together and the plain numbers together): <b>{lin_str(L)} = {lin_str(R)}</b>")
    else:
        steps.append(f"Write the equation: <b>{lin_str(L)} = {lin_str(R)}</b>")
    da = L.a - R.a
    db = R.b - L.b
    if da == 0:
        raise UErr("The x's cancel out, so I cannot find x from this. Please check the angles you typed.")
    if da < 0:
        L, R = R, L
        da, db = -da, -db
    if R.a != 0 or L.b != 0:
        left = xterm(L.a) if L.a != 0 else "0"
        if R.a != 0:
            left += (" &minus; " + xterm(R.a)) if R.a > 0 else (" + " + xterm(-R.a))
        right = nm(R.b)
        if L.b != 0:
            right += (" &minus; " + nm(L.b)) if L.b > 0 else (" + " + nm(-L.b))
        steps.append("Get all the x's on one side and all the plain numbers on the other side "
                     "(a number that jumps across the = sign changes its sign): "
                     f"<b>{left} = {right}</b>")
        steps.append(f"Simplify: <b>{xterm(da)} = {nm(db)}</b>")
    x = db / da
    xs = nm(x) if x.denominator == 1 else exact_or_dec(x, 3)
    if da != 1:
        steps.append(f"Divide both sides by {nm(da)} to get x on its own: <b>x = {nm(db)} &divide; {nm(da)} = {HL(xs)}</b>")
    else:
        steps.append(f"So <b>x = {HL(xs)}</b>")
    return x, steps


def sub_str(L, x):
    """3x+10 with x=30 -> '3 × 30 + 10'"""
    out = ""
    if L.a != 0:
        if L.a == 1:
            out = nm(x)
        elif L.a == -1:
            out = MINUS + (nm(x) if x >= 0 else "(" + nm(x) + ")")
        else:
            out = f"{nm(L.a)} {TIMES} {nm(x) if x >= 0 else '(' + nm(x) + ')'}"
    if L.b != 0:
        out += (" + " if L.b > 0 else " &minus; ") + fm(abs(L.b), 4) if out else nm(L.b)
    return out or "0"


# ------------------------------------------------------------------- relations ---

class Rel:
    def __init__(self, kind, names=None, coef=None, total=0, why="", text=None, fmt=None):
        self.kind = kind
        self.coef = coef or {}
        self.names = list(names) if names is not None else list(self.coef.keys())
        self.total = Fraction(total)
        self.why = why
        self.text = text
        self.fmt = fmt


def eq(names, why):
    return Rel("eq", names=names, why=why)


def fix(names, total, why):
    return Rel("fix", names=names, total=total, why=why)


def summ(names, total, why, text=None):
    return Rel("lin", coef={n: Fraction(1) for n in names}, total=total, why=why, text=text)


def lin(coef, total, why, text, fmt=None):
    return Rel("lin", coef={k: Fraction(v) for k, v in coef.items()}, total=total, why=why, text=text, fmt=fmt)


def _rel_text(r, nice):
    if r.text:
        return r.text
    if r.kind == "eq":
        return " = ".join(nice[n] for n in r.names)
    if r.kind == "fix":
        return f"each of {', '.join(nice[n] for n in r.names)} = {nm(r.total)}{DEG}"
    return ""


def _triples(r, val):
    """(lhs, rhs) pairs that must be equal for relation r"""
    if r.kind == "eq":
        return [(val[r.names[0]], val[n]) for n in r.names[1:]]
    if r.kind == "fix":
        return [(val[n], Lin(0, r.total)) for n in r.names]
    lhs = Lin()
    for n, c in r.coef.items():
        lhs = lhs + val[n].scale(c)
    return [(lhs, Lin(0, r.total))]


def solve_angles(names, nice, given, rels, maxang=180, what="figure"):
    """Work out every angle.

    names  : angle names in order, e.g. ["A", "B", "C"]
    nice   : name -> text used in the working (e.g. "angle A")
    given  : name -> Lin or None (None = to find)
    rels   : list of Rel
    Returns dict(vals, x, steps, kinds, exprs)
    """
    steps = []
    val = {n: given[n] for n in names if given.get(n) is not None}
    told = []
    for n in names:
        if n in val:
            told.append(f"{nice[n]} = {nm(val[n].b) + DEG if val[n].a == 0 else lin_str(val[n])}")
        else:
            told.append(f"{nice[n]} = ? (we must find it)")
    steps.append("<b>What the question tells us:</b> " + "; &nbsp;".join(told))

    parent = {n: n for n in names}

    def find(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    for r in rels:
        if r.kind == "eq":
            for m in r.names[1:]:
                parent[find(m)] = find(r.names[0])

    for _ in range(25):
        changed = False
        for r in rels:
            if r.kind == "fix":
                new = [n for n in r.names if n not in val]
                if new:
                    for n in new:
                        val[n] = Lin(0, r.total)
                    steps.append(f"{', '.join(nice[n] for n in new)} = {HL(nm(r.total) + DEG)} &nbsp;({r.why})")
                    changed = True
            elif r.kind == "eq":
                known = [n for n in r.names if n in val]
                unk = [n for n in r.names if n not in val]
                if known and unk:
                    src = known[0]
                    for n in unk:
                        val[n] = val[src]
                    res = val[src]
                    shown = HL(nm(res.b) + DEG) if res.a == 0 else lin_str(res)
                    steps.append(f"{', '.join(nice[n] for n in unk)} = {nice[src]} = {shown} &nbsp;({r.why})")
                    changed = True
            else:
                unk = [n for n in r.coef if n not in val]
                if not unk:
                    continue
                roots = {find(n) for n in unk}
                if len(roots) != 1:
                    continue
                k = sum(r.coef[n] for n in unk)
                if k == 0:
                    continue
                rest = Lin(0, r.total)
                kn = [n for n in r.coef if n in val]
                for n in kn:
                    rest = rest - val[n].scale(r.coef[n])
                g = rest.scale(1 / k)
                members = [m for m in names if find(m) == next(iter(roots)) and m not in val]
                allone = all(c == 1 for c in r.coef.values())
                tot = nm(r.total) + DEG
                if len(unk) == 1 and allone:
                    u = unk[0]
                    joined = " + ".join(dstr(val[n]) for n in kn)
                    if not kn:
                        s = f"{nice[u]} = {tot}"
                    elif len(kn) == 1:
                        s = f"{nice[u]} = {tot} &minus; {joined}"
                    else:
                        s = f"{nice[u]} = {tot} &minus; ({joined})"
                    shown = HL(nm(g.b) + DEG) if g.a == 0 else lin_str(g)
                    steps.append(f"{s} = {shown} &nbsp;({r.why})")
                elif len(unk) > 1 and allone:
                    joined = " + ".join(dstr(val[n]) for n in kn)
                    left = f"{tot} &minus; ({joined})" if len(kn) > 1 else (f"{tot} &minus; {joined}" if kn else tot)
                    shown = HL(nm(g.b) + DEG) if g.a == 0 else lin_str(g)
                    names_txt = " and ".join(nice[n] for n in unk)
                    steps.append(f"{names_txt} are equal, so share what is left equally: ({left}) &divide; {len(unk)} = {shown} each &nbsp;({r.why})")
                else:
                    u = unk[0]
                    shown = HL(nm(g.b) + DEG) if g.a == 0 else lin_str(g)
                    if r.fmt:
                        steps.append(r.fmt(u, val, g) + f" = {shown} &nbsp;({r.why})")
                    else:
                        steps.append(f"Using <b>{r.text}</b>: {nice[u]} = {shown} &nbsp;({r.why})")
                for m in members:
                    val[m] = g
                changed = True
        if not changed:
            break

    missing = [n for n in names if n not in val]
    if missing:
        raise UErr(f"Not enough information to find {nice[missing[0]]}. Give at least one more angle (a number or an expression with x).")

    xval = None
    for r in rels:
        pair = None
        for lhs, rhs in _triples(r, val):
            d = lhs - rhs
            if d.a != 0 or d.b != 0:
                pair = (lhs, rhs, d)
                break
        if pair is None:
            continue
        lhs, rhs, d = pair
        if d.a == 0:
            raise UErr("These angles cannot all be right: " + (_rel_text(r, nice) or "the rule") +
                       f" is not true for them (they are out by {nm(abs(d.b))}{DEG}). Check the numbers you typed.")
        rt = _rel_text(r, nice)
        if r.kind == "lin":
            parts = []
            for n, c in r.coef.items():
                t = dstr(val[n]) if val[n].a != 0 else nm(val[n].b)
                parts.append((c, t))
            raw = ""
            for i, (c, t) in enumerate(parts):
                if c == 1:
                    raw += (" + " if i else "") + t
                elif c == -1:
                    raw += " &minus; " + t if i else MINUS + t
                else:
                    raw += (" + " if i else "") + f"{nm(c)}({t})"
            raw += f" = {nm(r.total)}"
        else:
            raw = f"{dstr(lhs) if lhs.a != 0 else nm(lhs.b)} = {dstr(rhs) if rhs.a != 0 else nm(rhs.b)}"
        xval, s2 = solve_eq(lhs, rhs, raw=raw, relation=rt or None)
        steps.extend(s2)
        break

    if xval is None:
        if any(v.a != 0 for v in val.values()):
            raise UErr("I can see an x but there is not enough information to find it. Give another angle or relationship.")
    else:
        lines = []
        for n in names:
            v = val[n]
            if v.a != 0:
                lines.append(f"{nice[n]} = {lin_str(v)} = {sub_str(v, xval)} = <b>{nm(v.at(xval))}{DEG}</b>")
        if lines:
            steps.append(f"Now put x = {nm(xval) if xval.denominator == 1 else fm(xval, 3)} back into each angle:<br>" + "<br>".join(lines))

    vals = {n: val[n].at(xval) if xval is not None else val[n].b for n in names}
    for n in names:
        if not (0 < vals[n] < maxang):
            extra = f" (with x = {fm(xval, 3)})" if xval is not None else ""
            raise UErr(f"{nice[n][0].upper() + nice[n][1:]} works out as {nm(vals[n])}{DEG}{extra}, which is not possible in a {what}. Please check the numbers.")
    # final numeric check of every rule
    for r in rels:
        for lhs, rhs in _triples(r, {n: Lin(0, vals[n]) for n in names}):
            if lhs.b != rhs.b:
                raise UErr("The angles you typed cannot all be correct together. Please check them.")
    kinds = {}
    for n in names:
        g = given.get(n)
        kinds[n] = "found" if g is None else ("expr" if g.a != 0 else "given")
    return {"vals": vals, "x": xval, "steps": steps, "kinds": kinds, "exprs": val}


def answer_html(res, names, nice, title="Answer"):
    """tidy answer line"""
    bits = []
    if res["x"] is not None:
        x = res["x"]
        bits.append(f"x = {nm(x) if x.denominator == 1 else exact_or_dec(x, 3)}")
    for n in names:
        bits.append(f"{nice[n]} = {nm(res['vals'][n])}{DEG}")
    return "<b>" + " &nbsp;|&nbsp; ".join(bits) + "</b>"


def need_int(s, label, lo, hi):
    from tcommon import num
    v = num(s, label)
    if v.denominator != 1 or not (lo <= v <= hi):
        raise UErr(f"{label} must be a whole number from {lo} to {hi}.")
    return int(v)
