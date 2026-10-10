"""Variation: direct, inverse, joint, partial, percentage change.  Pure Python."""
import re
from fractions import Fraction
import numpy as np
import topics
from frac_numeric import sfrac, fr, FR, esc, dec_str, _ok, _fail

MINUS = "&minus;"
_NAME = re.compile(r"^[A-Za-z]$")


class VErr(Exception):
    pass


# ---------------------------------------------------------------- helpers ---

def _num(s, label, allow_blank=False):
    s = (s or "").strip().replace("−", "-")
    if s == "":
        if allow_blank:
            return None
        raise VErr(f"Please fill in {label}.")
    m = re.fullmatch(r"([+-]?\d{1,15}(?:\.\d{1,10})?)\s*/\s*(\d{1,15}(?:\.\d{1,10})?)", s)
    try:
        if m:
            d = sfrac(m.group(2))
            if d == 0:
                raise VErr(f"{label}: the bottom of a fraction cannot be 0.")
            return sfrac(m.group(1)) / d
        return sfrac(s)
    except VErr:
        raise
    except Exception:
        raise VErr(f"{label}: '{esc(s)}' is not a number. Use things like 12, 2.5 or 3/4.")


def _name(s, default):
    s = (s or "").strip() or default
    if not _NAME.match(s):
        raise VErr("Variable names must be single letters, for example y, x or z.")
    return s


def _exp(s, label, allow_blank=False):
    e = _num(s, label, allow_blank)
    if e is None:
        return None
    if abs(e) > 12 or e.denominator > 12:
        raise VErr(f"{label}: use a power between -12 and 12 (like 2, 3, 1/2).")
    return e


def _iroot(n, k):
    if n < 0:
        return None
    r = round(n ** (1.0 / k))
    for c in (r - 1, r, r + 1):
        if c >= 0 and c ** k == n:
            return c
    return None


def pw(v, e):
    """v ** e for Fractions; exact when possible, else float."""
    v = Fraction(v)
    e = Fraction(e)
    if e == 0:
        return Fraction(1)
    if v == 0:
        if e < 0:
            raise VErr("Cannot divide by zero: a value of 0 gives 1/0 here.")
        return Fraction(0)
    if e.denominator == 1:
        n = int(e)
        return v ** n
    if v < 0 and e.denominator % 2 == 0:
        raise VErr("A negative number has no real square root (or other even root).")
    q, p = e.denominator, e.numerator
    sign = -1 if v < 0 else 1
    a = _iroot(abs(v.numerator), q)
    b = _iroot(v.denominator, q)
    if a is not None and b is not None:
        base = Fraction(sign * a, b)
        return base ** p
    return float(sign * abs(float(v)) ** (1.0 / q)) ** p


def show(x):
    if isinstance(x, float):
        return dec_str(Fraction(x).limit_denominator(10 ** 9), 4)
    return fr(x)


def _plain(x):
    if isinstance(x, float):
        return dec_str(Fraction(x).limit_denominator(10 ** 9), 4)
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def _ehtml(e):
    e = Fraction(e)
    return str(e.numerator) if e.denominator == 1 else f"{e.numerator}/{e.denominator}"


def vpow(v, e):
    e = abs(Fraction(e))
    return v if e == 1 else f"{v}<sup>{_ehtml(e)}</sup>"


def rel_expr(parts, k="k"):
    """parts: [(var, exponent)] -> k x^2 / z as HTML."""
    num = [vpow(v, e) for v, e in parts if e > 0]
    den = [vpow(v, e) for v, e in parts if e < 0]
    n = "".join(num) if num else ""
    if den:
        d = "".join(den)
        return f"{k}{FR(n or '1', d)}" if k != "" else FR(n or "1", d)
    return f"{k}{n}"


def prop_expr(parts):
    num = [vpow(v, e) for v, e in parts if e > 0]
    den = [vpow(v, e) for v, e in parts if e < 0]
    n = "".join(num)
    if den:
        return FR(n or "1", "".join(den))
    return n


def _word(var, e):
    e = Fraction(e)
    direct = e > 0
    a = abs(e)
    names = {Fraction(1): "", Fraction(2): "the square of ", Fraction(3): "the cube of ",
             Fraction(1, 2): "the square root of "}
    pre = names.get(a, f"the {_ehtml(a)} power of ")
    return ("directly" if direct else "inversely"), f"{pre}{var}"


# --------------------------------------------------------- general solver ---

def general(d):
    try:
        y = _name(d.get("yname"), "y")
        x = _name(d.get("xname"), "x")
        z = _name(d.get("zname"), "z") if (d.get("ez") or "").strip() else None
        names = [y, x] + ([z] if z else [])
        if len(set(names)) != len(names):
            raise VErr("Use a different letter for each quantity.")
        ex = _exp(d.get("ex"), "the power of " + x)
        if ex == 0:
            raise VErr("The power cannot be 0, that would mean " + y + " does not depend on " + x + ".")
        ez = _exp(d.get("ez"), "the power of " + (z or "z"), allow_blank=True) if z else None
        if ez == 0:
            raise VErr("The power cannot be 0.")
        vals1 = {y: _num(d.get("y1"), f"the first value of {y}"),
                 x: _num(d.get("x1"), f"the first value of {x}")}
        if z:
            vals1[z] = _num(d.get("z1"), f"the first value of {z}")
        vals2 = {y: _num(d.get("y2"), "", True), x: _num(d.get("x2"), "", True)}
        if z:
            vals2[z] = _num(d.get("z2"), "", True)
        blanks = [n for n in names if vals2[n] is None]
        if len(blanks) != 1:
            raise VErr("Leave exactly ONE of the second-row boxes empty. That is the quantity you want to find.")
        target = blanks[0]
        parts = [(x, ex)] + ([(z, ez)] if z else [])
        exps = {x: ex, z: ez} if z else {x: ex}

        steps = []
        # 1 translate
        words = []
        for v, e in parts:
            how, w = _word(v, e)
            words.append(f"{how} as {w}")
        sentence = f"{y} varies " + " and ".join(words)
        steps.append(f"<b>Step 1 - Read the sentence.</b> We are told: <i>{sentence}</i>.")
        steps.append(f"<b>Step 2 - Write it with the 'varies as' sign.</b> {y} &prop; {prop_expr(parts)}. "
                     "(Quantities on the bottom of a fraction are the ones that vary <i>inversely</i>.)")
        steps.append(f"<b>Step 3 - Change &prop; into = by adding the constant k.</b> {y} = {rel_expr(parts)}")
        # 4 find k
        for v in names:
            if vals1[v] == 0 and v in exps and exps[v] < 0:
                raise VErr("A value of 0 cannot be used for an inverse quantity.")
        den_val = Fraction(1)
        sub_bits = []
        for v, e in parts:
            p = pw(vals1[v], e)
            den_val = den_val * p if not isinstance(p, float) and not isinstance(den_val, float) else float(den_val) * float(p)
            sub_bits.append(f"{show(vals1[v])}" + ("" if abs(e) == 1 else f"<sup>{_ehtml(abs(e))}</sup>"))
        # substitute
        n_s = "&times;".join(f"({show(vals1[v])})" + ("" if abs(e) == 1 else f"<sup>{_ehtml(abs(e))}</sup>")
                            for v, e in parts if e > 0)
        d_s = "&times;".join(f"({show(vals1[v])})" + ("" if abs(e) == 1 else f"<sup>{_ehtml(abs(e))}</sup>")
                            for v, e in parts if e < 0)
        rhs = FR(n_s or "1", d_s) if d_s else n_s
        steps.append(f"<b>Step 4 - Use the first set of values to find k.</b> Put {y} = {show(vals1[y])}, "
                     + ", ".join(f"{v} = {show(vals1[v])}" for v, _ in parts)
                     + f" into {y} = {rel_expr(parts)}:<br>{show(vals1[y])} = k &times; {rhs}")
        # value of the x/z part
        part_val = Fraction(1)
        for v, e in parts:
            pv = pw(vals1[v], e)
            part_val = (float(part_val) * float(pv)) if isinstance(pv, float) or isinstance(part_val, float) else part_val * pv
        if part_val == 0:
            raise VErr("These values make the first row give 0, so k cannot be found. Check your numbers.")
        k = vals1[y] / part_val
        steps.append(f"Work out the number: k &times; {show(part_val)} = {show(vals1[y])}")
        steps.append(f"Divide both sides by {show(part_val)}: <span class='hl'>k = {show(k)}</span>")
        steps.append(f"<b>Step 5 - Write the law (formula) with k filled in.</b> "
                     f"<span class='hl'>{y} = {rel_expr(parts, show(k) if not (isinstance(k, Fraction) and k == 1) else '')}</span>")
        # 6 new values
        known2 = [n for n in names if n != target]
        steps.append("<b>Step 6 - Use the second set of values.</b> We now know "
                     + ", ".join(f"{n} = {show(vals2[n])}" for n in known2) + f" and we want <b>{target}</b>.")
        if target == y:
            for v, e in parts:
                if e < 0 and vals2[v] == 0:
                    raise VErr("A value of 0 cannot be used for an inverse quantity.")
            pv = Fraction(1)
            for v, e in parts:
                p = pw(vals2[v], e)
                pv = float(pv) * float(p) if isinstance(p, float) or isinstance(pv, float) else pv * p
            n_s = "&times;".join(f"({show(vals2[v])})" + ("" if abs(e) == 1 else f"<sup>{_ehtml(abs(e))}</sup>")
                                for v, e in parts if e > 0)
            d_s = "&times;".join(f"({show(vals2[v])})" + ("" if abs(e) == 1 else f"<sup>{_ehtml(abs(e))}</sup>")
                                for v, e in parts if e < 0)
            rhs = FR(n_s or "1", d_s) if d_s else n_s
            ans = k * pv if not isinstance(pv, float) and not isinstance(k, float) else float(k) * float(pv)
            steps.append(f"{y} = {show(k)} &times; {rhs}")
            steps.append(f"{y} = {show(ans)}")
        else:
            e_t = exps[target]
            other = [(v, e) for v, e in parts if v != target]
            rest = Fraction(1)
            for v, e in other:
                if e < 0 and vals2[v] == 0:
                    raise VErr("A value of 0 cannot be used for an inverse quantity.")
                p = pw(vals2[v], e)
                rest = float(rest) * float(p) if isinstance(p, float) or isinstance(rest, float) else rest * p
            n_s = "&times;".join(f"({show(vals2[v])})" + ("" if abs(e) == 1 else f"<sup>{_ehtml(abs(e))}</sup>")
                                for v, e in other if e > 0)
            d_s = "&times;".join(f"({show(vals2[v])})" + ("" if abs(e) == 1 else f"<sup>{_ehtml(abs(e))}</sup>")
                                for v, e in other if e < 0)
            tpart = vpow(target, e_t)
            tfull = (tpart if e_t > 0 else FR("1", tpart))
            other_s = (FR(n_s or "1", d_s) if d_s else n_s)
            steps.append(f"{show(vals2[y])} = {show(k)} &times; {tfull}" + (f" &times; {other_s}" if other else ""))
            coef = k * rest if not isinstance(rest, float) and not isinstance(k, float) else float(k) * float(rest)
            if coef == 0:
                raise VErr("The numbers give a coefficient of 0, so " + target + " cannot be found.")
            if other:
                steps.append(f"Multiply the numbers together: {show(vals2[y])} = {show(coef)} &times; {tfull}")
            # isolate target power
            ytarget = vals2[y]
            if e_t > 0:
                tp = (ytarget / coef) if not isinstance(coef, float) else float(ytarget) / coef
                steps.append(f"Divide both sides by {show(coef)}: {vpow(target, e_t)} = {show(tp)}")
            else:
                if ytarget == 0:
                    raise VErr("With an inverse relationship, the answer would need 0 on the left, which is not possible.")
                tp = (coef / ytarget) if not isinstance(coef, float) else coef / float(ytarget)
                steps.append(f"Multiply both sides by {vpow(target, e_t)} and divide by {show(vals2[y])}: "
                             f"{vpow(target, e_t)} = {show(tp)}")
            ae = abs(e_t)
            if ae == 1:
                ans = tp
            else:
                inv = 1 / ae
                nm = {Fraction(2): "square root", Fraction(3): "cube root"}.get(ae)
                if ae.denominator == 1 and nm:
                    steps.append(f"To get {target} on its own, take the {nm} of both sides: "
                                 f"{target} = {'&radic;' if ae == 2 else '&sup3;&radic;'}({show(tp)})")
                else:
                    steps.append(f"To get {target} on its own, raise both sides to the power {_ehtml(inv)}: "
                                 f"{target} = ({show(tp)})<sup>{_ehtml(inv)}</sup>")
                if isinstance(tp, float):
                    tp = float(tp)
                ans = pw(tp, inv) if not isinstance(tp, float) else (tp ** float(inv) if tp >= 0 else None)
                if ans is None:
                    raise VErr("That would need the root of a negative number. Check the values.")
                if ae.denominator == 1 and ae == 2 and ans != 0:
                    steps.append(f"(Taking the square root gives &plusmn;, but a physical quantity here is taken as positive.)")
            steps.append(f"{target} = {show(ans)}")
        result = f"<b>{target} = {show(ans)}</b>"
        if isinstance(ans, Fraction) and ans.denominator != 1:
            result += f" &nbsp;(= {dec_str(ans, 4)})"
        result += f"<br><small>Law of variation: {y} = {rel_expr(parts, show(k) if not (isinstance(k, Fraction) and k == 1) else '')}</small>"
        return _ok(steps, result)
    except VErr as e:
        return _fail(str(e))


# ------------------------------------------------------------- partial ------

PRESETS = {
    "c_x": (0, 1, "a constant and the variable"),
    "c_x2": (0, 2, "a constant and the square"),
    "x_x2": (1, 2, "the variable and its square"),
    "x_invx": (1, -1, "the variable and its inverse"),
    "c_invx": (0, -1, "a constant and the inverse"),
    "x2_invx": (2, -1, "the square and the inverse"),
}


def _co(c, n):
    c = Fraction(c)
    if c == 1:
        return n
    if c == 0:
        return "0"
    return f"{show(c)}{n}"


def _term_html(coef_name, x, p):
    p = Fraction(p)
    if p == 0:
        return coef_name
    if p == 1:
        return f"{coef_name}{x}"
    if p > 0:
        return f"{coef_name}{x}<sup>{_ehtml(p)}</sup>"
    if p == -1:
        return f"{coef_name}{FR('1', x)}" if False else f"{FR(coef_name, x)}"
    return FR(coef_name, f"{x}<sup>{_ehtml(-p)}</sup>")


def _tv(x, p):
    return pw(x, p)


def partial(d):
    try:
        y = _name(d.get("yname"), "y")
        x = _name(d.get("xname"), "x")
        if y == x:
            raise VErr("Use different letters for the two quantities.")
        kind = d.get("kind", "c_x")
        if kind == "custom":
            p1 = _exp(d.get("p1"), "the first power")
            p2 = _exp(d.get("p2"), "the second power")
            if p1.denominator != 1 or p2.denominator != 1:
                raise VErr("For partial variation use whole-number powers like 0, 1, 2 or -1.")
        else:
            p1, p2 = [Fraction(v) for v in PRESETS[kind][:2]]
        if p1 == p2:
            raise VErr("The two parts must be different powers.")
        x1, y1 = _num(d.get("x1"), f"the first {x}"), _num(d.get("y1"), f"the first {y}")
        x2, y2 = _num(d.get("x2"), f"the second {x}"), _num(d.get("y2"), f"the second {y}")
        qx = _num(d.get("qx"), "", True)
        qy = _num(d.get("qy"), "", True)
        if (qx is None) == (qy is None):
            raise VErr(f"For the question, fill in either {x} (to find {y}) or {y} (to find {x}), but not both.")
        c1 = [_tv(x1, p1), _tv(x2, p1)]
        c2 = [_tv(x1, p2), _tv(x2, p2)]
        steps = []
        A, B = "A", "B"
        t1 = _term_html("A", x, p1)
        t2 = _term_html("B", x, p2)
        d1 = "a constant" if p1 == 0 else "proportional to " + prop_expr([(x, p1)])
        d2 = "a constant" if p2 == 0 else "proportional to " + prop_expr([(x, p2)])
        steps.append(f"<b>Step 1 - Split the variation into its two parts.</b> {y} is made of two parts: "
                     f"one part is {d1} and the other part is {d2}.")
        steps.append(f"<b>Step 2 - Write the formula with two constants.</b> "
                     f"{y} = {t1} + {t2}"
                     + (" &nbsp;(a constant part is just a plain number, A or B)" if 0 in (p1, p2) else ""))

        def eq(i, xv, yv):
            a = c1[i]
            b = c2[i]
            return f"{_co(a, 'A')} + {_co(b, 'B')} = {show(yv)}"
        steps.append(f"<b>Step 3 - Use each pair of values to make an equation.</b><br>"
                     f"When {x} = {show(x1)}, {y} = {show(y1)}: &nbsp; (1) {eq(0, x1, y1)}<br>"
                     f"When {x} = {show(x2)}, {y} = {show(y2)}: &nbsp; (2) {eq(1, x2, y2)}")
        a1, b1, a2, b2 = [Fraction(v) for v in (c1[0], c2[0], c1[1], c2[1])]
        det = a1 * b2 - a2 * b1
        if det == 0:
            raise VErr("These two pairs of values do not give a single answer (the equations are the same). Use different values.")
        steps.append(f"<b>Step 4 - Solve the two equations together (elimination).</b> "
                     f"Multiply (1) by {show(a2)} and (2) by {show(a1)} so the A terms match:<br>"
                     f"(1)&times;{show(a2)}: &nbsp;{_co(a1 * a2, 'A')} + {_co(b1 * a2, 'B')} = {show(y1 * a2)}<br>"
                     f"(2)&times;{show(a1)}: &nbsp;{_co(a1 * a2, 'A')} + {_co(b2 * a1, 'B')} = {show(y2 * a1)}")
        Bv = (y2 * a1 - y1 * a2) / det
        steps.append(f"Subtract: {_co(b2 * a1 - b1 * a2, 'B')} = {show(y2 * a1 - y1 * a2)}, so "
                     f"<span class='hl'>B = {show(Bv)}</span>")
        Av = (y1 - b1 * Bv) / a1 if a1 != 0 else (y2 - b2 * Bv) / a2
        steps.append(f"Put B = {show(Bv)} back into (1): {_co(a1, 'A')} + {show(b1 * Bv)} = {show(y1)}, "
                     f"so <span class='hl'>A = {show(Av)}</span>")

        def coef_t(c, p):
            return show(c)
        formula = f"{y} = {_term_html(show(Av), x, p1) if p1 != 0 else show(Av)} + {_term_html(show(Bv), x, p2) if p2 != 0 else show(Bv)}"
        steps.append(f"<b>Step 5 - Write the full formula.</b> <span class='hl'>{formula}</span>")
        if qx is not None:
            if qx == 0 and (p1 < 0 or p2 < 0):
                raise VErr("A value of 0 cannot be used for an inverse part.")
            yv = Av * pw(qx, p1) + Bv * pw(qx, p2)
            steps.append(f"<b>Step 6 - Find {y} when {x} = {show(qx)}.</b><br>{y} = {show(Av)}&times;({show(pw(qx, p1))}) "
                         f"+ {show(Bv)}&times;({show(pw(qx, p2))}) = {show(yv)}")
            res = f"<b>{y} = {show(yv)}</b>" + (f" &nbsp;(= {dec_str(yv, 4)})" if yv.denominator != 1 else "")
            return _ok(steps, res + f"<br><small>{formula}</small>")
        # find x for given y
        m = -min(p1, p2, Fraction(0))
        m = int(m)
        deg = int(max(p1, p2)) + m
        coeffs = [Fraction(0)] * (deg + 1)  # index = power
        coeffs[int(p1) + m] += Av
        coeffs[int(p2) + m] += Bv
        coeffs[m] -= qy
        steps.append(f"<b>Step 6 - Find {x} when {y} = {show(qy)}.</b><br>Put it in the formula: "
                     f"{show(qy)} = {show(Av)}&times;{x}<sup>{_ehtml(p1)}</sup> + {show(Bv)}&times;{x}<sup>{_ehtml(p2)}</sup>"
                     .replace(f"<sup>{_ehtml(p1)}</sup>", "" if p1 == 1 else f"<sup>{_ehtml(p1)}</sup>")
                     if p1 != 0 else f"<b>Step 6 - Find {x} when {y} = {show(qy)}.</b>")
        if m:
            steps.append(f"Multiply every term by {x}{'' if m == 1 else f'<sup>{m}</sup>'} to remove the fractions.")
        while len(coeffs) > 1 and coeffs[-1] == 0:
            coeffs.pop()
        poly_terms = []
        for pwr in range(len(coeffs) - 1, -1, -1):
            c = coeffs[pwr]
            if c == 0:
                continue
            sgn = (MINUS if c < 0 else "+")
            body = show(abs(c)) + ("" if pwr == 0 else (x if pwr == 1 else f"{x}<sup>{pwr}</sup>"))
            poly_terms.append((sgn, body))
        txt = ""
        for i, (s, b) in enumerate(poly_terms):
            txt += (b if i == 0 and s == "+" else f"{MINUS if s == MINUS else '+'} {b}" if i else f"{MINUS}{b}") + " "
        steps.append(f"This gives: {txt.strip()} = 0")
        if len(coeffs) == 1:
            raise VErr("No value of " + x + " fits.")
        if len(coeffs) == 2:
            roots = [-coeffs[0] / coeffs[1]]
            steps.append(f"This is a straight-line (linear) equation, so {x} = {show(roots[0])}")
        else:
            rts = np.roots([float(c) for c in reversed(coeffs)])
            roots = []
            for r in rts:
                if abs(r.imag) < 1e-9:
                    v = Fraction(r.real).limit_denominator(1000)
                    roots.append(v if abs(float(v) - r.real) < 1e-9 else float(round(r.real, 6)))
            roots = sorted(set(roots))
            if not roots:
                raise VErr("There is no real value of " + x + " that gives that " + y + ".")
            steps.append(f"Solving this equation gives {x} = " + " or ".join(show(r) for r in roots)
                         + ". (Reject any answer that does not make sense in the question, for example a negative length.)")
        good = [r for r in roots if r > 0] or roots
        good = good[:3]
        res = " or ".join(f"<b>{x} = {show(r)}</b>" for r in good)
        return _ok(steps, res + f"<br><small>{formula}</small>")
    except VErr as e:
        return _fail(str(e))


# ------------------------------------------------------- percentage change --

def pct_change(d):
    try:
        y = _name(d.get("yname"), "y")
        x = _name(d.get("xname"), "x")
        z = _name(d.get("zname"), "z") if (d.get("ez") or "").strip() else None
        names = [y, x] + ([z] if z else [])
        if len(set(names)) != len(names):
            raise VErr("Use a different letter for each quantity.")
        ex = _exp(d.get("ex"), "the power of " + x)
        ez = _exp(d.get("ez"), "the power of " + (z or "z"), True) if z else None
        px = _num(d.get("px"), f"the % change in {x}")
        pz = _num(d.get("pz"), f"the % change in {z}") if z else None
        parts = [(x, ex, px)] + ([(z, ez, pz)] if z else [])
        steps = [f"<b>Step 1 - Write the relationship.</b> {y} &prop; {prop_expr([(v, e) for v, e, _ in parts])}, "
                 f"so {y} = {rel_expr([(v, e) for v, e, _ in parts])}."]
        steps.append("<b>Step 2 - Turn each % change into a multiplier.</b> New amount = (1 + change/100) &times; old amount. "
                     "An increase of 20% means &times;1.2, a decrease of 20% means &times;0.8.")
        total = Fraction(1)
        notes = []
        for v, e, p in parts:
            mult = 1 + p / 100
            if mult <= 0:
                raise VErr("A decrease of 100% or more is not allowed here.")
            note = f"{v} {'increases' if p >= 0 else 'decreases'} by {_plain(abs(p))}%, multiplier = 1 {'+' if p >= 0 else MINUS} {_plain(abs(p) / 100)} = {show(mult)}"
            notes.append(note)
        steps.append("<br>".join(notes))
        facts = []
        for v, e, p in parts:
            mult = 1 + p / 100
            f = pw(mult, e)
            facts.append(f"({show(mult)})" + ("" if e == 1 else f"<sup>{_ehtml(e)}</sup>") + f" = {show(f)}")
            total = float(total) * float(f) if isinstance(f, float) or isinstance(total, float) else total * f
        steps.append(f"<b>Step 3 - Apply each power.</b> Because {y} = k{prop_expr([(v, e) for v, e, _ in parts]) if all(e > 0 for _, e, _ in parts) else '...'} "
                     "the multipliers are raised to the same powers:<br>" + "<br>".join(facts))
        steps.append(f"<b>Step 4 - Multiply them to get the multiplier for {y}.</b> {show(total)}")
        chg = (total - 1) * 100
        steps.append(f"<b>Step 5 - Turn the multiplier back into a % change.</b> ({show(total)} &minus; 1) &times; 100 = {show(chg) if not isinstance(chg, float) else dec_str(Fraction(chg).limit_denominator(10**6), 2)}%")
        c = Fraction(chg).limit_denominator(10 ** 6)
        word = "increases" if c >= 0 else "decreases"
        val = abs(c)
        res = f"<b>{y} {word} by {dec_str(val, 2)}%</b>"
        return _ok(steps, res)
    except VErr as e:
        return _fail(str(e))


# ----------------------------------------------------------------- spec -----

def _f(name, label, ph="", **kw):
    return dict(name=name, label=label, placeholder=ph, type="text", half=True, **kw)


_POW = [("1", "1  (directly / plain)"), ("2", "2  (square)"), ("3", "3  (cube)"), ("1/2", "1/2  (square root)"),
        ("-1", "&minus;1  (inversely)"), ("-2", "&minus;2  (inversely as the square)"),
        ("-3", "&minus;3  (inversely as the cube)"), ("-1/2", "&minus;1/2  (inversely as the square root)")]

SPEC = {
    "title": "Variation",
    "intro": "Direct, inverse, joint and partial variation, worked out step by step.",
    "tabs": [
        {"id": "vg", "label": "Direct / Inverse / Joint", "title": "Find the constant and the unknown",
         "endpoint": "general",
         "hint": "Example: <i>y varies directly as the square of x and inversely as z. When x = 2 and z = 4, y = 6. Find y when x = 3 and z = 9.</i> "
                 "Choose the powers, enter the first row of values, then the second row <b>leaving one box empty</b> (the one you want).",
         "fields": [
             _f("yname", "Letter for the answer (y)", "y"),
             _f("xname", "First quantity (x)", "x"),
             dict(name="ex", label="Power of the first quantity", type="select", options=_POW, half=True),
             _f("zname", "Second quantity (z), optional", "z"),
             dict(name="ez", label="Power of the second quantity (choose 'none' for no second quantity)", type="select",
                  options=[("", "none"), ] + _POW, half=True),
             _f("y1", "First row: y =", "6"),
             _f("x1", "First row: x =", "2"),
             _f("z1", "First row: z =", "4", show_if={"ez": [v for v, _ in _POW]}),
             _f("y2", "Second row: y =  (leave empty to find it)", ""),
             _f("x2", "Second row: x =  (leave empty to find it)", "3"),
             _f("z2", "Second row: z =  (leave empty to find it)", "9", show_if={"ez": [v for v, _ in _POW]}),
         ]},
        {"id": "vp", "label": "Partial variation", "title": "Partial variation",
         "endpoint": "partial",
         "hint": "Example: <i>y is partly constant and partly varies as x. When x = 2, y = 11 and when x = 5, y = 20. Find y when x = 10.</i>",
         "fields": [
             _f("yname", "Letter for the answer (y)", "y"),
             _f("xname", "Quantity it varies with (x)", "x"),
             dict(name="kind", label="y is partly...", type="select", half=True,
                  options=[(k, "&hellip; " + v[2]) for k, v in PRESETS.items()] + [("custom", "Other powers (type them)")]),
             _f("p1", "Power of the first part", "1", show_if={"kind": "custom"}),
             _f("p2", "Power of the second part", "2", show_if={"kind": "custom"}),
             _f("x1", "First pair: x =", "2"), _f("y1", "First pair: y =", "11"),
             _f("x2", "Second pair: x =", "5"), _f("y2", "Second pair: y =", "20"),
             _f("qx", "Question: when x = (to find y)", "10"),
             _f("qy", "Question: when y = (to find x)", ""),
         ]},
        {"id": "vc", "label": "% change", "title": "Percentage change in a varying quantity",
         "endpoint": "pct",
         "hint": "Example: <i>y varies as the square of x. If x increases by 20%, by what % does y change?</i> "
                 "Type a negative number for a decrease.",
         "fields": [
             _f("yname", "Letter for the answer (y)", "y"),
             _f("xname", "First quantity (x)", "x"),
             dict(name="ex", label="Power of the first quantity", type="select", options=_POW, half=True),
             _f("px", "% change in the first quantity", "20"),
             _f("zname", "Second quantity (optional)", "z"),
             dict(name="ez", label="Power of the second quantity", type="select",
                  options=[("", "none")] + _POW, half=True),
             _f("pz", "% change in the second quantity", "-10", show_if={"ez": [v for v, _ in _POW]}),
         ]},
    ],
}

topics.register("variation", SPEC, {"general": general, "partial": partial, "pct": pct_change})
