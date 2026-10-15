"""Number bases: conversion, arithmetic (column working), unknown base.  Pure Python."""
import re
from fractions import Fraction
from math import isqrt
import topics
from frac_numeric import fr, esc, dec_str, table, _ok, _fail

DIG = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
MINUS = "&minus;"
MAXINT = 40       # digits
MAXFRAC = 20


class BErr(Exception):
    pass


def sub(s, b):
    return f"{s}<sub>{b}</sub>"


def _base(v, label):
    try:
        b = int(str(v).strip())
    except Exception:
        raise BErr(f"{label}: please choose a whole number between 2 and 36.")
    if not 2 <= b <= 36:
        raise BErr(f"{label}: the base must be between 2 and 36.")
    return b


def parse_in_base(text, b):
    """'-12.4' in base b -> (sign, int_digits list, frac_digits list)."""
    s = (text or "").strip().upper().replace("−", "-").replace(" ", "")
    if not s:
        raise BErr("Please type a number.")
    sign = 1
    if s[0] in "+-":
        sign = -1 if s[0] == "-" else 1
        s = s[1:]
    if s.count(".") > 1 or not s or s == ".":
        raise BErr(f"'{esc(text)}' is not a valid number.")
    ip, _, fp = s.partition(".")
    if len(ip) > MAXINT or len(fp) > MAXFRAC:
        raise BErr("That number is too long. Use at most 40 digits before and 20 after the point.")
    for ch in ip + fp:
        if ch not in DIG:
            raise BErr(f"'{esc(ch)}' is not a digit.")
        if DIG.index(ch) >= b:
            raise BErr(f"The digit {ch} cannot appear in base {b}: base {b} only uses the digits "
                       f"{', '.join(DIG[:b]) if b <= 12 else DIG[0] + ' to ' + DIG[b - 1]}.")
    return sign, [DIG.index(c) for c in ip] or [0], [DIG.index(c) for c in fp]


def to_value(sign, ip, fp, b):
    v = Fraction(0)
    for d in ip:
        v = v * b + d
    f = Fraction(0)
    for i, d in enumerate(fp, 1):
        f += Fraction(d, b ** i)
    return sign * (v + f)


def int_to_base(n, b):
    if n == 0:
        return "0"
    out = []
    while n:
        n, r = divmod(n, b)
        out.append(DIG[r])
    return "".join(reversed(out))


def frac_to_base(f, b, maxd=8):
    """fraction 0<=f<1 -> (digits string, exact?)"""
    out = []
    seen = 0
    while f and len(out) < maxd:
        f *= b
        d = int(f)
        out.append(DIG[d])
        f -= d
    return "".join(out), f == 0


def value_to_str(v, b, maxd=8):
    neg = v < 0
    v = abs(v)
    ip = int(v)
    fpart = v - ip
    s = int_to_base(ip, b)
    exact = True
    if fpart:
        fs, exact = frac_to_base(fpart, b, maxd)
        s += "." + fs
    return ("-" if neg else "") + s, exact


def _expand(ip, fp, b):
    """expanded-form lines for number in base b"""
    terms = []
    n = len(ip)
    for i, d in enumerate(ip):
        p = n - 1 - i
        terms.append((d, p))
    for i, d in enumerate(fp, 1):
        terms.append((d, -i))
    return terms


def _digit_txt(d):
    return str(d) if d < 10 else f"{DIG[d]}({d})"


# ----------------------------------------------------------------- convert --

def convert(d):
    try:
        fb = _base(d.get("frm"), "From base")
        tb = _base(d.get("to"), "To base")
        sign, ip, fp = parse_in_base(d.get("num"), fb)
        steps = []
        orig = ("-" if sign < 0 else "") + "".join(DIG[x] for x in ip) + ("." + "".join(DIG[x] for x in fp) if fp else "")
        steps.append(f"<b>Goal:</b> change {sub(orig, fb)} into base {tb}.")
        if fb == tb:
            return _ok(steps + ["The two bases are the same, so nothing changes."], f"<b>{sub(orig, tb)}</b>")
        direct = (not fp) and ((fb in (2, 4, 8, 16) and tb in (2, 4, 8, 16)) and
                               (fb == 2 or tb == 2 or {fb, tb} == {4, 8} or False))
        # --- to base 10
        val = to_value(sign, ip, fp, fb)
        if fb != 10:
            terms = _expand(ip, fp, fb)
            steps.append(f"<b>Step 1 - Change to base 10.</b> Each digit has a place value: the places go "
                         f"{fb}<sup>0</sup>, {fb}<sup>1</sup>, {fb}<sup>2</sup> ... from the right"
                         + (f", and after the point {fb}<sup>&minus;1</sup>, {fb}<sup>&minus;2</sup> ..." if fp else "") + ".")
            ex = " + ".join(f"{_digit_txt(dg)}&times;{fb}<sup>{p if p >= 0 else MINUS + str(-p)}</sup>" for dg, p in terms)
            steps.append(f"Expand: {ex}")
            nums = " + ".join(f"{dg}&times;{fr(Fraction(fb) ** p)}" if p < 0 else f"{dg}&times;{fb ** p}" for dg, p in terms)
            steps.append(f"Work out each power: {nums}")
            prods = " + ".join(fr(dg * Fraction(fb) ** p) for dg, p in terms)
            steps.append(f"Multiply: {prods}")
            steps.append(f"Add up: <span class='hl'>{sub(orig, fb)} = {fr(val)}{'' if val.denominator == 1 else ' = ' + dec_str(val, 6)}<sub>10</sub></span>" if val.denominator != 1 else f"Add up: <span class='hl'>{sub(orig, fb)} = {sub(str(val), 10)}</span>")
        else:
            steps.append("The number is already in base 10, so we can start dividing straight away.")
        if tb == 10:
            res = value_to_str(val, 10, 12)[0]
            return _ok(steps, f"<b>{sub(orig, fb)} = {sub(res if val.denominator == 1 else dec_str(val, 6), 10)}</b>")
        # --- from base 10
        av = abs(val)
        n = int(av)
        f = av - n
        stepno = 2 if fb != 10 else 1
        steps.append(f"<b>Step {stepno} - Change from base 10 to base {tb}.</b>")
        if n == 0:
            steps.append("The whole part is 0, so it stays 0.")
        else:
            rows = []
            m = n
            while m:
                q, r = divmod(m, tb)
                rows.append([f"{tb} &#10073; {m}", str(q), f"{DIG[r]}" + (f" ({r})" if r > 9 else "")])
                m = q
            steps.append(f"Divide the whole part {n} by {tb} again and again, writing the remainder each time, until the quotient is 0:")
            steps.append(table(rows, ["Divide", "Quotient", "Remainder"]))
            steps.append(f"Read the remainders from <b>bottom to top</b>: <span class='hl'>{int_to_base(n, tb)}</span>")
        fs = ""
        if f:
            steps.append(f"Now the fraction part {fr(f)}: multiply by {tb} again and again, each time writing down the whole-number part and keeping the rest.")
            rows = []
            g = f
            out = []
            for _ in range(8):
                if g == 0:
                    break
                g *= tb
                dg = int(g)
                rows.append([f"{fr(g - dg + dg) if False else dec_str(g, 6)}", f"{DIG[dg]}"])
                out.append(DIG[dg])
                g -= dg
            lines = []
            g = f
            tr = []
            for _ in range(8):
                if g == 0:
                    break
                prod = g * tb
                dg = int(prod)
                tr.append([f"{dec_str(g, 6)} &times; {tb}", dec_str(prod, 6), DIG[dg] + (f" ({dg})" if dg > 9 else "")])
                g = prod - dg
            steps.append(table(tr, ["Multiply", "Result", "Whole part"]))
            fs = "".join(DIG[int(0)] for _ in []) or "".join(r[2][0] for r in tr)
            if g:
                steps.append("The fraction never finishes (it keeps repeating), so we stop after 8 places and the answer is approximate.")
            steps.append(f"Read the whole parts from <b>top to bottom</b>: <span class='hl'>.{fs}</span>")
        ans = ("-" if sign < 0 else "") + int_to_base(n, tb) + ("." + fs if fs else "")
        approx = f and (value_to_str(abs(val), tb, 8)[1] is False)
        extra = ""
        if direct:
            extra = ""
        if fb == 2 and tb in (4, 8, 16) and not fp:
            k = {4: 2, 8: 3, 16: 4}[tb]
            s = "".join(DIG[x] for x in ip)
            padded = s.zfill(-(-len(s) // k) * k)
            groups = [padded[i:i + k] for i in range(0, len(padded), k)]
            steps.append(f"<b>Shortcut check:</b> for binary &rarr; base {tb}, group the digits in {k}s from the right: "
                         + " ".join(groups) + " &rarr; " + " ".join(DIG[int(g, 2)] for g in groups) + f" = {int_to_base(n, tb)}")
        if tb == 2 and fb in (4, 8, 16) and not fp:
            k = {4: 2, 8: 3, 16: 4}[fb]
            s = "".join(DIG[x] for x in ip)
            steps.append(f"<b>Shortcut check:</b> write each base-{fb} digit as {k} binary digits: "
                         + " ".join(f"{DIG[x]}&rarr;{format(x, 'b').zfill(k)}" for x in ip))
        return _ok(steps, f"<b>{sub(orig, fb)} = {sub(ans, tb)}</b>" + (" (approximately)" if approx else ""))
    except BErr as e:
        return _fail(str(e))


# -------------------------------------------------------------- arithmetic --

def _col_add(a, b, base):
    la, lb = len(a), len(b)
    n = max(la, lb)
    a = [0] * (n - la) + a
    b = [0] * (n - lb) + b
    carry = 0
    lines = []
    out = []
    names = ["units", "next place"]
    for i in range(n - 1, -1, -1):
        s = a[i] + b[i] + carry
        q, r = divmod(s, base)
        pos = n - 1 - i
        lines.append(f"Column {pos + 1} (from the right): {a[i]} + {b[i]}" + (f" + {carry} (carried)" if carry else "")
                     + f" = {s}. In base {base}, {s} = {q}&times;{base} + {r}, so write <b>{DIG[r]}</b>"
                     + (f" and carry <b>{q}</b>." if q else "."))
        out.append(DIG[r])
        carry = q
    if carry:
        lines.append(f"Bring down the last carry: <b>{DIG[carry]}</b>.")
        out.append(DIG[carry])
    return "".join(reversed(out)), lines


def _col_sub(a, b, base):
    la, lb = len(a), len(b)
    n = max(la, lb)
    a = [0] * (n - la) + a
    b = [0] * (n - lb) + b
    borrow = 0
    lines = []
    out = []
    for i in range(n - 1, -1, -1):
        top = a[i] - borrow
        pos = n - 1 - i
        if top < b[i]:
            lines.append(f"Column {pos + 1}: {top if borrow else a[i]}" + (f" (after lending 1)" if borrow else "")
                         + f" is smaller than {b[i]}, so borrow 1 from the next column. "
                         f"That 1 is worth {base} here, so {top} + {base} = {top + base}; then {top + base} &minus; {b[i]} = {top + base - b[i]}. Write <b>{DIG[top + base - b[i]]}</b>.")
            out.append(DIG[top + base - b[i]])
            borrow = 1
        else:
            lines.append(f"Column {pos + 1}: {top}" + (" (after lending 1)" if borrow else "") + f" &minus; {b[i]} = {top - b[i]}. Write <b>{DIG[top - b[i]]}</b>.")
            out.append(DIG[top - b[i]])
            borrow = 0
    return ("".join(reversed(out)).lstrip("0") or "0"), lines


def arithmetic(d):
    try:
        b = _base(d.get("base"), "Base")
        op = d.get("op", "+")
        s1, i1, f1 = parse_in_base(d.get("a"), b)
        s2, i2, f2 = parse_in_base(d.get("b"), b)
        A = to_value(s1, i1, f1, b)
        B = to_value(s2, i2, f2, b)
        ta = ("-" if s1 < 0 else "") + "".join(DIG[x] for x in i1) + ("." + "".join(DIG[x] for x in f1) if f1 else "")
        tb_ = ("-" if s2 < 0 else "") + "".join(DIG[x] for x in i2) + ("." + "".join(DIG[x] for x in f2) if f2 else "")
        sym = {"+": "+", "-": MINUS, "*": "&times;", "/": "&divide;"}.get(op)
        if sym is None:
            raise BErr("Choose an operation.")
        steps = [f"<b>Question:</b> {sub(ta, b)} {sym} {sub(tb_, b)}, answer in base {b}."]
        simple = not f1 and not f2 and s1 > 0 and s2 > 0
        if simple and op in "+-":
            if op == "+":
                res, lines = _col_add(i1, i2, b)
                steps.append(f"<b>Method 1 - Column method (like ordinary addition, but we carry when we reach {b}).</b>")
            else:
                big, small = (i1, i2) if A >= B else (i2, i1)
                res, lines = _col_sub(big, small, b)
                steps.append(f"<b>Method 1 - Column method (like ordinary subtraction, but a borrowed 1 is worth {b}).</b>")
                if A < B:
                    steps.append(f"The second number is bigger, so work out the bigger minus the smaller and put a minus sign in front.")
            steps.append("<br>".join(lines))
            if op == "-" and A < B:
                res = "-" + res
            steps.append(f"Answer by columns: <span class='hl'>{sub(res, b)}</span>")
        steps.append(f"<b>{'Method 2 - ' if simple and op in '+-' else 'Method - '}Change to base 10, work it out, change back.</b>")
        steps.append(f"{sub(ta, b)} = {fr(A)}<sub>10</sub> and {sub(tb_, b)} = {fr(B)}<sub>10</sub>")
        if op == "+":
            r = A + B
        elif op == "-":
            r = A - B
        elif op == "*":
            r = A * B
        else:
            if B == 0:
                raise BErr("You cannot divide by zero.")
            r = A / B
        steps.append(f"In base 10: {fr(A)} {sym} {fr(B)} = {fr(r)}")
        res10 = value_to_str(r, b, 8)
        if r.denominator == 1 or (r.denominator != 1 and not (f1 or f2) and op == "/"):
            pass
        n = int(abs(r))
        if r.denominator == 1:
            rows = []
            m = n
            while m:
                q, rm = divmod(m, b)
                rows.append([f"{b} &#10073; {m}", str(q), DIG[rm]])
                m = q
            if n and b != 10:
                steps.append(f"Change {abs(int(r))} back to base {b} by repeated division by {b}:")
                steps.append(table(rows, ["Divide", "Quotient", "Remainder"]))
                steps.append(f"Read the remainders upward: {int_to_base(n, b)}")
        else:
            if op == "/" and simple:
                qq, rr = divmod(A, B)
                steps.append(f"Division does not come out exactly. As whole-number division: quotient {int(qq)}, remainder {int(rr)}, "
                             f"i.e. {sub(int_to_base(int(qq), b), b)} remainder {sub(int_to_base(int(rr), b), b)}.")
            steps.append("The answer has a fraction part; convert the whole part by division and the fraction part by multiplication (see the Convert tab).")
        out = res10[0]
        tail = "" if res10[1] else " (approximately, the digits go on)"
        return _ok(steps, f"<b>{sub(ta, b)} {sym} {sub(tb_, b)} = {sub(out, b)}</b>{tail}")
    except BErr as e:
        return _fail(str(e))


# ---------------------------------------------------------- unknown base ---

def _padd(p, q, s=1):
    n = max(len(p), len(q))
    r = [0] * n
    for i, c in enumerate(p):
        r[i] += c
    for i, c in enumerate(q):
        r[i] += s * c
    while len(r) > 1 and r[-1] == 0:
        r.pop()
    return r


def _pmul(p, q):
    r = [0] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        for j, c in enumerate(q):
            r[i + j] += a * c
    return r


_TOK = re.compile(r"^([0-9A-Za-z]+)(?:_(x|X|\d+))?$")


def _parse_side(text, info):
    t = text.replace(" ", "").replace("−", "-").replace("×", "*").replace("x_", "X_")
    if not t:
        raise BErr("Something is missing on one side of the = sign.")
    # split into signed terms
    terms = re.findall(r"[+-]?[^+-]+", t)
    if "".join(terms) != t:
        raise BErr("I couldn't read that expression. Example: 123_x + 45_x = 100_10")
    total = [0]
    for term in terms:
        sgn = 1
        if term[0] in "+-":
            sgn = -1 if term[0] == "-" else 1
            term = term[1:]
        poly = [1]
        for fac in term.split("*"):
            m = _TOK.match(fac)
            if not m:
                raise BErr(f"I couldn't read '{esc(fac)}'. Write numbers like 123_x (base x) or 45_8 (base 8) or just 45 (base 10).")
            digs, bs = m.group(1).upper(), m.group(2)
            if len(digs) > 12:
                raise BErr("Numbers are too long here.")
            if bs and bs.lower() == "x":
                for ch in digs:
                    if ch not in DIG:
                        raise BErr(f"'{esc(ch)}' is not a digit.")
                dv = [DIG.index(c) for c in digs]
                info["maxd"] = max(info["maxd"], max(dv))
                info["uses_x"] = True
                p = [0] * len(dv)
                for i, dg in enumerate(reversed(dv)):
                    p[i] = dg
            else:
                base = int(bs) if bs else 10
                if not 2 <= base <= 36:
                    raise BErr("Fixed bases must be between 2 and 36.")
                val = 0
                for ch in digs:
                    if ch not in DIG or DIG.index(ch) >= base:
                        raise BErr(f"'{esc(ch)}' is not allowed in base {base}.")
                    val = val * base + DIG.index(ch)
                p = [val]
            poly = _pmul(poly, p)
        total = _padd(total, [sgn * c for c in poly])
    return total


def _ptxt(p, v="x"):
    out = ""
    for k in range(len(p) - 1, -1, -1):
        c = p[k]
        if c == 0:
            continue
        a = abs(c)
        body = (str(a) if (a != 1 or k == 0) else "") + ("" if k == 0 else (v if k == 1 else f"{v}<sup>{k}</sup>"))
        if not out:
            out = (MINUS if c < 0 else "") + body
        else:
            out += f" {MINUS if c < 0 else '+'} {body}"
    return out or "0"


def unknown(d):
    try:
        eq = (d.get("eq") or "").strip()
        if eq.count("=") != 1 or len(eq) > 120:
            raise BErr("Type an equation with one = sign, for example: 34_x + 25_x = 61_x   or   123_x = 38")
        L, R = eq.split("=")
        info = {"maxd": 0, "uses_x": False}
        steps = []
        pl, pr = _parse_side(L, info), _parse_side(R, info)
        if not info["uses_x"]:
            raise BErr("Mark the unknown base with _x, for example 123_x.")
        steps.append(f"<b>Step 1 - Turn each number into base 10 using x for the base.</b> A number like 123<sub>x</sub> means "
                     f"1&times;x<sup>2</sup> + 2&times;x + 3. Numbers written in another base are changed to ordinary numbers.")
        steps.append(f"Left side = <b>{_ptxt(pl)}</b><br>Right side = <b>{_ptxt(pr)}</b>")
        poly = _padd(pl, pr, -1)
        steps.append(f"<b>Step 2 - Move everything to one side.</b> {_ptxt(poly)} = 0")
        if poly == [0]:
            raise BErr("This is true for every base, so there is no single answer.")
        lo = max(2, info["maxd"] + 1)
        steps.append(f"<b>Step 3 - Remember the rule for a base.</b> A base must be a whole number and bigger than every digit used. "
                     f"The largest digit used is {DIG[info['maxd']]}, so x must be at least {lo}.")
        deg = len(poly) - 1
        cands = []
        if deg == 0:
            raise BErr("There is no base that makes this true.")
        if deg == 1:
            r = Fraction(-poly[0], poly[1])
            steps.append(f"<b>Step 4 - Solve.</b> {_ptxt(poly)} = 0 &rarr; x = {fr(r)}")
            cands = [r]
        elif deg == 2:
            a, b_, c = poly[2], poly[1], poly[0]
            disc = b_ * b_ - 4 * a * c
            steps.append(f"<b>Step 4 - Solve the quadratic</b> with a = {a}, b = {b_}, c = {c}. "
                         f"Discriminant b<sup>2</sup> &minus; 4ac = {b_ * b_} &minus; ({4 * a * c}) = {disc}.")
            if disc < 0:
                raise BErr("No real base satisfies this equation.")
            sq = isqrt(disc)
            if sq * sq == disc:
                r1, r2 = Fraction(-b_ + sq, 2 * a), Fraction(-b_ - sq, 2 * a)
                steps.append(f"&radic;{disc} = {sq}, so x = ({-b_} &plusmn; {sq}) / {2 * a}: x = {fr(r1)} or x = {fr(r2)}")
                cands = sorted({r1, r2})
            else:
                steps.append(f"{disc} is not a perfect square, so x is not a whole number.")
        else:
            steps.append("<b>Step 4 - Try the possible bases</b> one at a time (this equation is above a quadratic):")
            rows = []
            for bb in range(lo, 37):
                val = sum(c * bb ** k for k, c in enumerate(poly))
                rows.append([str(bb), str(val), "&#10003;" if val == 0 else ""])
                if val == 0:
                    cands.append(Fraction(bb))
            steps.append(table(rows[:20], ["x", "Value of left &minus; right", ""]))
        good = [c for c in cands if c.denominator == 1 and lo <= c <= 36]
        for c in cands:
            if c not in good:
                why = "not a whole number" if c.denominator != 1 else (f"smaller than {lo}, but the base must be bigger than every digit" if c < lo else "too large")
                steps.append(f"x = {fr(c)} is rejected: it is {why}.")
        if not good:
            raise BErr("No valid base satisfies this equation. Check the digits and the equation.")
        x = int(good[0])
        # check
        steps.append(f"<b>Step 5 - Check.</b> Put x = {x} back: left = {sum(c * x ** k for k, c in enumerate(pl))}, "
                     f"right = {sum(c * x ** k for k, c in enumerate(pr))}. They match.")
        return _ok(steps, f"<b>x = {x}</b>  &nbsp;(the numbers are in base {x})")
    except BErr as e:
        return _fail(str(e))


# ------------------------------------------------------------------ spec ---

def _f(name, label, ph="", **kw):
    d = dict(name=name, label=label, placeholder=ph, type="text", half=True)
    d.update(kw)
    return d


_BASES = [(str(i), str(i)) for i in range(2, 37)]


def _bsel(name, label, default):
    opts = [(str(i), f"base {i}") for i in range(2, 37)]
    opts.sort(key=lambda o: 0 if o[0] == default else 1)
    return dict(name=name, label=label, type="select", options=opts, half=True)


SPEC = {
    "title": "Number Bases",
    "intro": "Convert between bases, add, subtract, multiply and divide in any base, and find an unknown base.",
    "tabs": [
        {"id": "bc", "label": "Convert", "title": "Convert a number from one base to another",
         "endpoint": "convert",
         "hint": "For bases above 10 use letters: A = 10, B = 11, C = 12 ... Decimal points (like 101.01) are fine.",
         "fields": [_f("num", "Number", "257"), _bsel("frm", "From", "8"), _bsel("to", "To", "2")]},
        {"id": "ba", "label": "Add / subtract / multiply / divide", "title": "Calculate in a number base",
         "endpoint": "arith",
         "hint": "Both numbers must be written in the chosen base, for example 1101 + 111 in base 2.",
         "fields": [_f("a", "First number", "1101"),
                    dict(name="op", label="Operation", type="select", half=True,
                         options=[("+", "+  add"), ("-", "&minus;  subtract"), ("*", "&times;  multiply"), ("/", "&divide;  divide")]),
                    _f("b", "Second number", "111"), _bsel("base", "Base", "2")]},
        {"id": "bu", "label": "Find the unknown base", "title": "Find an unknown base",
         "endpoint": "unknown",
         "hint": "Write the unknown base as <b>_x</b>. Examples: <i>34_x + 25_x = 61_x</i>, <i>123_x = 38</i>, "
                 "<i>101_2 * 12_x = 50</i>. A number with no base is in base 10; <i>45_8</i> means 45 in base 8.",
         "fields": [_f("eq", "Equation", "34_x + 25_x = 61_x", wide=True, half=False)]},
    ],
}

topics.register("bases", SPEC, {"convert": convert, "arith": arithmetic, "unknown": unknown})
