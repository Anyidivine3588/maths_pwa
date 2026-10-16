"""Logarithm tools with fully explained working (pure Python, no sympy).

Every function returns the same dict the rest of the app uses:
    {"ok": bool, "steps": [html...], "result": html, "error": text}
"""
import math
from fractions import Fraction

from log_core import *   # noqa: F401,F403
from log_core import (LogErr, NeedValue, MINUS, esc, fmtq, sig, dp_, parse, pp, log_name, variables, has_log, logs_in,
                      ev_exact, ev_vec, ev_float, vec_exact_log, vec_of, vec_mul, vec_scale, vec_to_q, exact_log,
                      primitive_root, P1, to_poly, real_roots, base_val, contains_var_in_exponent, factor_int)


def _ok(steps, result):
    return {"steps": steps, "result": result, "ok": True, "error": None}


def _fail(msg):
    return {"steps": [], "result": None, "ok": False, "error": msg}


def guard(fn):
    def wrapped(*a, **k):
        try:
            return fn(*a, **k)
        except LogErr as e:
            return _fail(str(e))
        except RecursionError:
            return _fail("That expression is too complicated for me. Please simplify it.")
        except (OverflowError, ValueError, ZeroDivisionError):
            return _fail("Those numbers are too big or do not work together. Please check them.")
    wrapped.__name__ = fn.__name__
    return wrapped


def HL(s):
    return f"<span class='hl'>{s}</span>"


def qtxt(v):
    """Fraction/float -> text"""
    if isinstance(v, Fraction):
        return fmtq(v)
    return sig(v, 5)


def ordinal_root(q):
    return {2: "square root", 3: "cube root", 4: "fourth root", 5: "fifth root"}.get(q, f"{q}th root")


def power_text(base_txt, r):
    return f"{base_txt}<sup>{fmtq(r)}</sup>"


# =========================================================== one logarithm ====

def _num(node, what):
    """float value of a number-only node, raising friendly errors"""
    try:
        return ev_float(node)
    except NeedValue:
        raise


def explain_log(node):
    """node = ('log', arg, base). -> (value Fraction|float, steps list, brief text)"""
    arg, base = node[1], node[2]
    bnode = base if base is not None else ("num", Fraction(10))
    bs, As = pp(bnode), pp(arg)
    L = f"{log_name(base)}({As})"
    vs = variables(arg) | (variables(base) if base is not None else set())
    steps = []
    # ---- letters: only the special identities can be evaluated
    if vs:
        if arg == bnode:
            steps.append(f"The base and the number are the same ({bs}). Any number to the power 1 is itself ({bs}<sup>1</sup> = {bs}), so {HL(L + ' = 1')}.")
            return Fraction(1), steps, f"{L} = 1"
        if arg == ("num", Fraction(1)):
            steps.append(f"Any number (except 0) to the power 0 is 1, so {HL(L + ' = 0')}.")
            return Fraction(0), steps, f"{L} = 0"
        if arg[0] == "pow" and arg[1] == bnode and not variables(arg[2]):
            k = ev_exact(arg[2])
            if k is not None:
                steps.append(f"{As} is {bs} to the power {fmtq(k)}, so the power we need is {fmtq(k)}: {HL(L + ' = ' + fmtq(k))}.")
                return k, steps, f"{L} = {fmtq(k)}"
        raise NeedValue("This log has a letter in it, so it has no single number as an answer. "
                        "To expand or combine it, use the <b>Laws of Logarithms</b> tab; to find x, use <b>Solve an Equation</b>.")
    # ---- natural log
    if base is not None and base[0] == "const":
        a = ev_float(arg)
        if a <= 0:
            raise LogErr(_neg_msg("e", As, a))
        steps.append(f"<b>ln</b> means log to the base <b>e</b> (e is a special number, about 2.718).")
        if arg == ("const", "e"):
            steps.append(f"e<sup>1</sup> = e, so {HL('ln(e) = 1')}.")
            return Fraction(1), steps, "ln(e) = 1"
        if arg == ("num", Fraction(1)):
            steps.append(f"e<sup>0</sup> = 1, so {HL('ln(1) = 0')}.")
            return Fraction(0), steps, "ln(1) = 0"
        if arg[0] == "pow" and arg[1] == ("const", "e") and ev_exact(arg[2]) is not None:
            k = ev_exact(arg[2])
            steps.append(f"The number is e to the power {fmtq(k)}, so {HL('ln = ' + fmtq(k))}.")
            return k, steps, f"{L} = {fmtq(k)}"
        v = math.log(a)
        steps.append(f"This is not a neat power of e, so use a calculator (the <b>ln</b> button): {HL(L + ' &asymp; ' + sig(v, 4))}.")
        return v, steps, f"{L} &asymp; {sig(v, 4)}"
    # ---- numbers
    a, b = ev_float(arg), ev_float(bnode)
    if b <= 0:
        raise LogErr("The base of a logarithm must be a <b>positive</b> number. A base like " + bs + " is not allowed.")
    if b == 1:
        raise LogErr("The base of a logarithm cannot be 1, because 1 to any power is always 1, so it can never give other numbers.")
    if a <= 0:
        raise LogErr(_neg_msg(bs, As, a))
    steps.append(f"<b>What does it mean?</b> {L} asks: <i>to what power must we raise {bs} to get {As}?</i> In symbols: {bs}<sup>?</sup> = {As}.")
    va, vb = ev_vec(arg), ev_vec(bnode)
    r = vec_exact_log(va, vb) if (va is not None and vb is not None) else None
    if r is not None:
        qa, qb = ev_exact(arg), ev_exact(bnode)
        if r.denominator == 1:
            k = int(r)
            if k == 0:
                steps.append(f"Any number (except 0) to the power 0 is 1, so {bs}<sup>0</sup> = 1.")
            elif k == 1:
                steps.append(f"{bs}<sup>1</sup> = {bs}, so the power needed is 1.")
            elif 1 < k <= 6 and qb is not None and qb.denominator == 1:
                steps.append(f"Multiply {bs} by itself {k} times: " + " &times; ".join([bs] * k) + f" = {As}.")
            elif k < 0 and qb is not None and 1 <= -k <= 6:
                steps.append(f"A negative power means 'one over': {bs}<sup>{MINUS}{-k}</sup> = 1/{bs}<sup>{-k}</sup> = 1/({' &times; '.join([bs] * -k)}) = {As}.")
            else:
                steps.append(f"{bs}<sup>{fmtq(r)}</sup> = {As}.")
            steps.append(f"So {bs}<sup>{fmtq(r)}</sup> = {As}, therefore {HL(L + ' = ' + fmtq(r))}.")
            return r, steps, f"{L} = {fmtq(r)}"
        # fractional answer: try writing both as powers of one smaller number
        pr = primitive_root(qb) if qb is not None else None
        done = False
        if pr is not None and qa is not None:
            u, m = pr
            n = r * m
            if n.denominator == 1 and u != qb and u != qa:
                us = fmtq(u)
                steps.append(f"<b>Trick: write both numbers as powers of the same small number {us}.</b> {bs} = {us}<sup>{m}</sup> and {As} = {us}<sup>{int(n)}</sup>.")
                steps.append(f"So ({us}<sup>{m}</sup>)<sup>?</sup> = {us}<sup>{int(n)}</sup>. Multiplying the powers: {us}<sup>{m} &times; ?</sup> = {us}<sup>{int(n)}</sup>.")
                steps.append(f"The bases match, so the powers must match: {m} &times; ? = {int(n)}, so ? = {HL(fmtq(r))}.")
                done = True
        if not done:
            p_, q_ = r.numerator, r.denominator
            if p_ == 1 and q_ in (2, 3, 4, 5):
                steps.append(f"{As} is the <b>{ordinal_root(q_)}</b> of {bs}, and a {ordinal_root(q_)} is the power 1/{q_}.")
            else:
                steps.append(f"{bs}<sup>{fmtq(r)}</sup> = {As}.")
        steps.append(f"So {HL(L + ' = ' + fmtq(r))} (as a decimal: {sig(float(r), 4)}).")
        return r, steps, f"{L} = {fmtq(r)}"
    # ---- not a neat answer: change of base
    la, lb = math.log10(a), math.log10(b)
    val = la / lb
    steps.append(f"There is no neat whole-number or simple-fraction power that works, so we use a <b>calculator</b> and the <b>change of base</b> rule: log<sub>b</sub>(a) = lg(a) &divide; lg(b), where lg means log to base 10.")
    steps.append(f"lg({As}) = {dp_(la, 4)} &nbsp; and &nbsp; lg({bs}) = {dp_(lb, 4)}")
    steps.append(f"{L} = {dp_(la, 4)} &divide; {dp_(lb, 4)} = {HL('&asymp; ' + sig(val, 4))}")
    if b > 1 and abs(val) < 40:
        k1 = math.floor(val)
        if 0 <= k1 and b ** (k1 + 1) < 1e12 and k1 <= 12:
            steps.append(f"<b>Sense check:</b> {bs}<sup>{k1}</sup> = {fmtq(Fraction(b).limit_denominator(10 ** 6) ** k1)} and {bs}<sup>{k1 + 1}</sup> = {fmtq(Fraction(b).limit_denominator(10 ** 6) ** (k1 + 1))}. "
                         f"{As} lies between them, so the answer should be between {k1} and {k1 + 1}. &check;")
    return val, steps, f"{L} &asymp; {sig(val, 4)}"


def _neg_msg(bs, As, a):
    return (f"<b>log of {'zero' if a == 0 else 'a negative number'} does not exist.</b> A positive base ({bs}) raised to any power always gives a positive answer, "
            f"so no power can ever give {As}. The number inside a log must be bigger than 0.")


def _atoms(node, out=None):
    out = [] if out is None else out
    for lg in logs_in(node):
        if lg not in out:
            out.append(lg)
    return out


def _subst_eval(node, vals):
    """evaluate node with log nodes replaced by their values (Fraction or float)"""
    k = node[0]
    if k == "log":
        return vals[node]
    if k == "num":
        return node[1]
    if k == "const":
        return math.e
    if k == "neg":
        a = _subst_eval(node[1], vals)
        return -a
    if k in ("add", "sub", "mul", "div"):
        a, b = _subst_eval(node[1], vals), _subst_eval(node[2], vals)
        if not (isinstance(a, Fraction) and isinstance(b, Fraction)):
            a, b = float(a), float(b)
        if k == "add":
            return a + b
        if k == "sub":
            return a - b
        if k == "mul":
            return a * b
        if b == 0:
            raise LogErr("That divides by zero.")
        return a / b
    if k == "pow":
        a, e = _subst_eval(node[1], vals), _subst_eval(node[2], vals)
        if isinstance(a, Fraction) and isinstance(e, Fraction) and e.denominator == 1 and abs(e) <= 60:
            return a ** int(e)
        r = float(a) ** float(e)
        if isinstance(r, complex):
            raise LogErr("That needs the root of a negative number.")
        return r
    if k == "sqrt":
        a = _subst_eval(node[1], vals)
        if a < 0:
            raise LogErr("You cannot take the square root of a negative number here.")
        if isinstance(a, Fraction):
            v = ev_vec(("num", a))
            if v is not None:
                q = vec_to_q(vec_scale(v, Fraction(1, 2)))
                if q is not None:
                    return q
        return math.sqrt(float(a))
    raise LogErr("I cannot work this out.")


def _val_node(v):
    return ("num", v) if isinstance(v, Fraction) else ("flt", v)


def _pp_vals(node, vals):
    """print node with log atoms replaced by their numeric values"""
    k = node[0]
    if k == "log":
        v = vals[node]
        return qtxt(v) if isinstance(v, Fraction) else sig(v, 4)
    if k in ("add", "sub"):
        a, b = _pp_vals(node[1], vals), _pp_vals(node[2], vals)
        return f"{a} {'+' if k == 'add' else MINUS} {b}"
    if k == "mul":
        return f"{_pp_vals(node[1], vals)} &times; {_pp_vals(node[2], vals)}"
    if k == "div":
        return f"{_pp_vals(node[1], vals)} &divide; {_pp_vals(node[2], vals)}"
    if k == "neg":
        return f"{MINUS}{_pp_vals(node[1], vals)}"
    return pp(node)


@guard
def evaluate(expr, base=None):
    expr = (expr or "").strip()
    if not expr:
        return _fail("Please type a logarithm first, for example log_2(8).")
    if "=" in expr:
        return _fail("That has an = sign, so it is an equation. Use the <b>Solve an Equation</b> tab for it.")
    if base not in (None, "") and "log" not in expr.lower() and "ln" not in expr.lower():
        # old style: expression is just the number, base given separately
        expr = f"log_({base})({expr})"
    node = parse(expr)
    if not has_log(node):
        return _fail("I could not find a logarithm in that. Write it like <b>log_2(8)</b>, <b>log(100)</b> or <b>ln(e)</b>.")
    atoms = _atoms(node)
    if node[0] == "log":
        val, steps, brief = explain_log(node)
        res = qtxt(val) if isinstance(val, Fraction) else "&asymp; " + sig(val, 4)
        if isinstance(val, Fraction) and "/" in res:
            res += f" &nbsp;(= {sig(float(val), 4)})"
        return _ok(steps, f"{pp(node)} = {res}")
    steps = ["<b>Work out each logarithm first</b>, then do the arithmetic."]
    vals = {}
    for a in atoms:
        v, st, brief = explain_log(a)
        vals[a] = v
        steps.append(brief + "<br><small>" + " ".join(st[1:] if len(st) > 1 else st) + "</small>")
    steps.append(f"<b>Put the values in:</b> {_pp_vals(node, vals)}")
    total = _subst_eval(node, vals)
    res = qtxt(total) if isinstance(total, Fraction) else "&asymp; " + sig(total, 4)
    if isinstance(total, Fraction) and "/" in res:
        res += f" &nbsp;(= {sig(float(total), 4)})"
    steps.append(f"<b>Answer:</b> {HL(res)}")
    return _ok(steps, f"{pp(node)} = {res}")


# ============================================================ change of base ====

def _num_input(text, label):
    text = (text or "").strip()
    if not text:
        raise LogErr(f"Please fill in {label}.")
    if text.lower() in ("e",):
        return ("const", "e"), "e", math.e, None
    n = parse(text)
    if variables(n):
        raise LogErr(f"{label} must be a number, not a letter.")
    fl = ev_float(n)
    return n, pp(n), fl, ev_exact(n)


@guard
def change_of_base(value, from_base, to_base=10):
    na, sa, a, qa = _num_input(value, "the number (a)")
    nb, sb, b, qb = _num_input(from_base, "the original base (b)")
    if str(to_base).strip() in ("", "None"):
        to_base = "10"
    nc, sc, c, qc = _num_input(str(to_base), "the new base (c)")
    if a <= 0:
        raise LogErr(_neg_msg(sb, sa, a))
    if b <= 0 or b == 1:
        raise LogErr("The original base must be positive and not 1.")
    if c <= 0 or c == 1:
        raise LogErr("The new base must be positive and not 1.")
    cname = "ln" if nc == ("const", "e") else (f"log<sub>{sc}</sub>")
    steps = [
        "<b>Change of base rule:</b> log<sub>b</sub>(a) = log<sub>c</sub>(a) &divide; log<sub>c</sub>(b). "
        "It lets you rewrite a log in <i>any base you like</i>, usually base 10 or e, because those are on your calculator.",
        f"Here a = {sa}, b = {sb}, new base c = {sc}.",
        f"log<sub>{sb}</sub>({sa}) = {cname}({sa}) &divide; {cname}({sb})",
    ]
    la, lb = math.log(a) / math.log(c), math.log(b) / math.log(c)
    steps.append(f"{cname}({sa}) = {dp_(la, 4)} &nbsp; and &nbsp; {cname}({sb}) = {dp_(lb, 4)}")
    val = math.log(a) / math.log(b)
    r = exact_log(qa, qb) if (qa is not None and qb is not None and qa > 0 and qb > 0) else None
    steps.append(f"Divide: {dp_(la, 4)} &divide; {dp_(lb, 4)} = {HL(fmtq(r) if (r is not None and r.denominator == 1) else sig(val, 5))}")
    if r is not None:
        steps.append(f"<b>Neat answer:</b> {sb}<sup>{fmtq(r)}</sup> = {sa}, so exactly log<sub>{sb}</sub>({sa}) = {HL(fmtq(r))}.")
    if r is not None and r.denominator == 1:
        steps.append(f"<b>Check:</b> {sb}<sup>{fmtq(r)}</sup> = {sa}. &check;")
    else:
        steps.append(f"<b>Check:</b> {sb}<sup>{sig(val, 5)}</sup> &asymp; {sig(b ** val, 4)}, which is {sa}. &check;")
    res = fmtq(r) + (f" (= {sig(val, 5)})" if "/" in fmtq(r) else "") if r is not None else "&asymp; " + sig(val, 5)
    return _ok(steps, f"log<sub>{sb}</sub>({sa}) = {res}")


# ====================================================== laws of logarithms ====

TAB4 = {2: 0.3010, 3: 0.4771, 5: 0.6990, 7: 0.8451, 11: 1.0414, 13: 1.1139}


def lg_tab(p):
    """4-figure 'table' value of lg(p)"""
    return TAB4.get(p, round(math.log10(p), 4))


def _domain_msg():
    return "The number inside a log must be <b>positive</b>. A minus sign in front makes it negative, and log of a negative number does not exist."


def _merge(fs):
    out = {}
    order = []
    for at, e in fs:
        if at not in out:
            out[at] = Fraction(0)
            order.append(at)
        out[at] += Fraction(e)
    return [(at, out[at]) for at in order if out[at] != 0]


def arg_factors(node):
    k = node[0]
    if k == "num":
        q = node[1]
        if q == 0:
            raise LogErr("<b>log of zero does not exist.</b> No power of a positive base ever gives 0.")
        if q < 0:
            raise LogErr(_domain_msg())
        v = vec_of(q)
        if v is None:
            return [(node, Fraction(1))]
        return [(("num", Fraction(p)), Fraction(e)) for p, e in sorted(v.items())]
    if k == "mul":
        return _merge(arg_factors(node[1]) + arg_factors(node[2]))
    if k == "div":
        return _merge(arg_factors(node[1]) + [(at, -e) for at, e in arg_factors(node[2])])
    if k == "pow":
        if variables(node[2]):
            return [(node, Fraction(1))]
        e = ev_exact(node[2])
        if e is None:
            return [(node, Fraction(1))]
        return _merge([(at, ex * e) for at, ex in arg_factors(node[1])])
    if k == "sqrt":
        return _merge([(at, ex / 2) for at, ex in arg_factors(node[1])])
    if k == "neg":
        raise LogErr(_domain_msg())
    return [(node, Fraction(1))]


def build_arg(factors):
    """[(atom, exp)] -> AST (numbers multiplied together)"""
    q = Fraction(1)
    num, den = [], []
    for at, e in factors:
        if at[0] == "num" and e.denominator == 1 and abs(e) <= 60:
            q *= at[1] ** int(e)
            continue
        part = at if abs(e) == 1 else ("pow", at, ("num", abs(e)))
        (num if e > 0 else den).append(part)
    if q != 1 or not num:
        if q.denominator != 1 and not num and not den:
            return ("div", ("num", Fraction(q.numerator)), ("num", Fraction(q.denominator)))
        if q.denominator != 1:
            if q.numerator != 1 or not num:
                num.insert(0, ("num", Fraction(q.numerator)))
            den.insert(0, ("num", Fraction(q.denominator)))
        else:
            num.insert(0, ("num", q))

    def prod(ps):
        r = ps[0]
        for p in ps[1:]:
            r = ("mul", r, p)
        return r
    n = prod(num) if num else ("num", Fraction(1))
    if den:
        return ("div", n, prod(den))
    return n


def lin_logs(node):
    """node -> (terms [[coef, lognode]], const Fraction) for a sum of numeric multiples of logs"""
    k = node[0]
    if k == "log":
        return [[Fraction(1), node]], Fraction(0)
    if not has_log(node):
        q = ev_exact(node) if not variables(node) else None
        if q is None:
            raise LogErr("I can only combine logs with plain numbers. Check the parts of your expression that are not logs.")
        return [], q
    if k == "neg":
        t, c = lin_logs(node[1])
        return [[-a, l] for a, l in t], -c
    if k in ("add", "sub"):
        t1, c1 = lin_logs(node[1])
        t2, c2 = lin_logs(node[2])
        sg = 1 if k == "add" else -1
        return t1 + [[sg * a, l] for a, l in t2], c1 + sg * c2
    if k == "mul":
        l1, l2 = has_log(node[1]), has_log(node[2])
        if l1 and l2:
            raise LogErr("Two logs multiplied together cannot be simplified with the laws of logarithms. "
                         "Remember: log(a) &times; log(b) is <b>not</b> log(a + b) or log(ab). The laws only work on log(a&times;b) or log(a) + log(b).")
        if l1:
            t, c = lin_logs(node[1])
            f = ev_exact(node[2]) if not variables(node[2]) else None
        else:
            t, c = lin_logs(node[2])
            f = ev_exact(node[1]) if not variables(node[1]) else None
        if f is None:
            raise LogErr("A log can only be multiplied by a plain number here (like 3log x).")
        return [[a * f, l] for a, l in t], c * f
    if k == "div":
        if has_log(node[2]):
            raise LogErr("<b>log(a) &divide; log(b) is NOT the same as log(a/b)</b> or log(a) &minus; log(b). "
                         "The laws of logarithms cannot simplify a division of two logs. "
                         "(If both are logs to the same base you may use the change of base rule instead.)")
        d = ev_exact(node[2]) if not variables(node[2]) else None
        if d is None or d == 0:
            raise LogErr("A log can only be divided by a plain number here.")
        t, c = lin_logs(node[1])
        return [[a / d, l] for a, l in t], c / d
    if k == "pow":
        raise LogErr("A power of a log, like (log x)<sup>2</sup>, cannot be simplified with the laws of logarithms. "
                     "Only the <i>inside</i> of a log can have powers: log(x<sup>2</sup>) = 2log(x).")
    raise LogErr("I could not apply the laws of logarithms to that.")


def merge_terms(terms):
    out = []
    for a, l in terms:
        for t in out:
            if t[1] == l:
                t[0] += a
                break
        else:
            out.append([a, l])
    return [t for t in out if t[0] != 0]


def lin_text(terms, base, const=None):
    parts = []
    nm = log_name(base)
    for a, at in terms:
        mag = abs(a)
        co = "" if mag == 1 else fmtq(mag) + " "
        inner = pp(at)
        body = f"{co}{nm}({inner})"
        if not parts:
            parts.append((MINUS if a < 0 else "") + body)
        else:
            parts.append(f" {MINUS if a < 0 else '+'} {body}")
    if const:
        parts.append(f" {'+' if const > 0 else MINUS} {fmtq(abs(const))}" if parts else fmtq(const))
    return "".join(parts) or "0"


def _same_base(a, b):
    na = ("num", Fraction(10)) if a is None else a
    nb = ("num", Fraction(10)) if b is None else b
    return na == nb


def _is_numeric_atom(at):
    return at[0] == "num"


@guard
def laws(expr):
    expr = (expr or "").strip()
    if not expr:
        return _fail("Please type a logarithm expression, for example log(x*y) or 2log3 + log4.")
    if "=" in expr:
        return _fail("That has an = sign, so it is an equation. Use the <b>Solve an Equation</b> tab for it.")
    node = parse(expr)
    if not has_log(node):
        return _fail("I could not find a logarithm. Write it like <b>log(x*y)</b> or <b>2log3 + log4</b>.")
    terms, const = lin_logs(node)
    terms = merge_terms(terms)
    if not terms:
        return _ok([f"Expression: {pp(node)}"], f"= {fmtq(const)}")
    base0 = terms[0][1][2]
    for a, l in terms:
        if not _same_base(l[2], base0):
            return _fail("These logs have <b>different bases</b>, so the laws of logarithms cannot combine them. "
                         "First change them to the same base (use the <b>Change of Base</b> tab).")
    bnode = ("num", Fraction(10)) if base0 is None else base0
    single = len(terms) == 1 and terms[0][0] == 1 and const == 0
    nm = log_name(base0)
    steps = [f"<b>Your expression:</b> {pp(node)}"]
    LAWS = {"prod": "<b>Product law:</b> log(a &times; b) = log(a) + log(b)",
            "quot": "<b>Quotient law:</b> log(a &divide; b) = log(a) &minus; log(b)",
            "pow": "<b>Power law:</b> log(a<sup>n</sup>) = n &times; log(a)"}
    if single:
        lg = terms[0][1]
        arg = lg[1]
        # neat numeric answer?
        if not variables(arg) and not variables(base0 or ("num", 1)):
            a_f, b_f = ev_float(arg), ev_float(bnode)
            if base0 is None or base0[0] != "const":
                va, vb = ev_vec(arg), ev_vec(bnode)
                r = vec_exact_log(va, vb) if (va is not None and vb is not None) else None
                if r is not None:
                    v, st, brief = explain_log(lg)
                    return _ok(["<b>This one is a neat number</b>, so no expanding is needed:"] + st, f"{pp(lg)} = {fmtq(r)}")
        fs = arg_factors(arg)
        if len(fs) == 1 and fs[0][1] == 1 and fs[0][0] == arg:
            steps.append("The number inside the log is a single piece (not a product, quotient or power), so the laws cannot expand it any further.")
            if not variables(arg) and ev_float(arg) > 0:
                bf = ev_float(bnode)
                steps.append(f"Its value: {pp(lg)} &asymp; {sig(math.log(ev_float(arg)) / math.log(bf), 4)} (calculator).")
            return _ok(steps, f"{pp(lg)} cannot be expanded further")
        used = []
        # describe how the inside is built
        numeric = all(_is_numeric_atom(at) for at, e in fs) and not variables(arg)
        if numeric:
            q = ev_exact(arg)
            if q is not None:
                txt = " &times; ".join(f"{fmtq(at[1])}" + (f"<sup>{fmtq(e)}</sup>" if e != 1 else "") for at, e in fs if e > 0) or "1"
                dn = " &times; ".join(f"{fmtq(at[1])}" + (f"<sup>{fmtq(-e)}</sup>" if e != -1 else "") for at, e in fs if e < 0)
                steps.append(f"<b>Write {pp(arg)} using prime factors</b> (smallest building blocks): {pp(arg)} = {txt}" + (f" &divide; ({dn})" if dn else ""))
        else:
            steps.append(f"<b>Look at the inside:</b> {pp(arg)}. Find the products, divisions and powers.")
        pos = [(at, e) for at, e in fs if e > 0]
        neg = [(at, -e) for at, e in fs if e < 0]
        if len(pos) > 1 or len(neg) > 1:
            used.append("prod")
        if neg:
            used.append("quot")
        if any(abs(e) != 1 for at, e in fs):
            used.append("pow")
        if used:
            steps.append("<b>Laws used:</b><br>" + "<br>".join(LAWS[u] for u in ["prod", "quot", "pow"] if u in used))
        # stage 1: separate logs, with powers still inside
        def one(at, e):
            return at if e == 1 else ("pow", at, ("num", Fraction(e)))
        sep = " ".join(("" if i == 0 else ("+" if e > 0 else MINUS)) + (f" {nm}({pp(one(at, abs(e)))})" if i else (f"{MINUS if e < 0 else ''}{nm}({pp(one(at, abs(e)))})")) for i, (at, e) in enumerate(fs))
        sep = sep.replace("  ", " ")
        if len(fs) > 1 or any(abs(e) != 1 for at, e in fs):
            steps.append(f"<b>Split it up:</b> {sep}")
        const_part = Fraction(0)
        res_terms = []
        for at, e in fs:
            if at == bnode:
                const_part += e
            else:
                res_terms.append([e, at])
        if any(abs(e) != 1 for at, e in fs) or const_part:
            steps.append(f"<b>Bring the powers to the front{' (and use log<sub>b</sub>(b) = 1)' if const_part else ''}:</b> {HL(lin_text(res_terms, base0, const_part))}")
        # numeric evaluation
        if numeric and (base0 is None):
            parts, total, rows = [], 0.0, []
            for at, e in fs:
                p = int(at[1])
                val = lg_tab(p)
                src = "standard value" if p in TAB4 else "calculator / log table"
                rows.append(f"lg({p}) = {val:.4f} ({src})")
                total += float(e) * val
            steps.append("<b>Use the known values:</b><br>" + "<br>".join(rows))
            ex = ""
            for i, (at, e) in enumerate(fs):
                t1 = (f"{fmtq(abs(e))} &times; " if abs(e) != 1 else "") + f"{lg_tab(int(at[1])):.4f}"
                ex += (("" if e > 0 else MINUS) + t1) if i == 0 else (f" {'+' if e > 0 else MINUS} {t1}")
            tot_s = f"{total:.4f}".replace("-", MINUS)
            steps.append(f"{pp(lg)} = {ex} = {HL(tot_s)}")
            return _ok(steps, f"{pp(lg)} = {lin_text(res_terms, base0)} = {tot_s}")
        if numeric:
            qf = ev_float(arg)
            bf = ev_float(bnode)
            steps.append(f"On a calculator: {pp(lg)} &asymp; {sig(math.log(qf) / math.log(bf), 4)}")
        return _ok(steps, f"{pp(lg)} = {lin_text(res_terms, base0, const_part)}")
    # ----------------------------------------------------------- combine
    steps.append("<b>Goal:</b> squash everything into <b>one single log</b>. All the logs have the same base" +
                 (f" ({pp(bnode)})" if base0 is not None else " (base 10)") + ", so we may combine them.")
    laws_used = []
    if any(a != 1 and a != -1 for a, l in terms):
        laws_used.append("pow")
    pos = [t for t in terms if t[0] > 0]
    neg = [t for t in terms if t[0] < 0]
    if len(terms) + (1 if const else 0) > 1:
        if len(pos) + (1 if const > 0 else 0) > 1:
            laws_used.append("prod")
        if neg or const < 0:
            laws_used.append("quot")
    if const:
        laws_used.append("const")
    CL = {"const": "<b>A plain number is a log too:</b> k = k &times; log<sub>b</sub>(b) = log<sub>b</sub>(b<sup>k</sup>) (because log<sub>b</sub>(b) = 1)."}
    steps.append("<b>Laws used:</b><br>" + "<br>".join((LAWS | CL)[u] for u in ["pow", "prod", "quot", "const"] if u in laws_used))
    # stage 1: powers inside
    inner = []   # (sign, argnode)
    shown = []
    for a, l in terms:
        arg = l[1]
        m = abs(a)
        if m == 1:
            inner.append((1 if a > 0 else -1, arg, arg))
            shown.append((a, arg, arg))
        else:
            q = ev_exact(arg) if not variables(arg) else None
            if q is not None and m.denominator == 1 and abs(m) < 40 and q > 0:
                newarg = ("num", q ** int(m))
            else:
                newarg = ("pow", arg, ("num", m))
            inner.append((1 if a > 0 else -1, newarg, arg))
            shown.append((a, arg, newarg))
    if any(abs(a) != 1 for a, l in terms):
        txts = []
        for a, arg, newarg in shown:
            if abs(a) != 1:
                txts.append(f"{fmtq(abs(a))}{nm}({pp(arg)}) = {nm}({pp(('pow', arg, ('num', abs(a))))})" + (f" = {nm}({pp(newarg)})" if newarg[0] == "num" else ""))
        steps.append("<b>Power law</b> (move each number in front back inside as a power):<br>" + "<br>".join(txts))
    if const:
        k = const
        kq = Fraction(k)
        bq = ev_exact(bnode) if not variables(bnode) else None
        if bq is not None and kq.denominator == 1 and abs(kq) < 40:
            cnode = ("num", bq ** int(abs(kq)))
            steps.append(f"<b>Turn the number {fmtq(abs(kq))} into a log:</b> {fmtq(abs(kq))} = {nm}({pp(bnode)}<sup>{fmtq(abs(kq))}</sup>) = {nm}({pp(cnode)})")
        else:
            cnode = ("pow", bnode, ("num", abs(kq)))
            steps.append(f"<b>Turn the number {fmtq(abs(kq))} into a log:</b> {fmtq(abs(kq))} = {nm}({pp(cnode)})")
        inner.append((1 if k > 0 else -1, cnode, cnode))
    # stage 2: product / quotient
    fnum, fden = [], []
    for sgn, nd, _ in inner:
        for at, e in arg_factors(nd):
            (fnum if sgn > 0 else fden).append((at, e))
    allf = _merge(fnum + [(at, -e) for at, e in fden])
    top = [nd for sgn, nd, _ in inner if sgn > 0]
    bot = [nd for sgn, nd, _ in inner if sgn < 0]

    def prodtxt(nds):
        return " &times; ".join(pp(n, 3) for n in nds)
    if len(inner) > 1:
        if bot:
            steps.append(f"<b>Product and quotient laws</b> (added logs multiply, subtracted logs divide): {nm}(({prodtxt(top) if top else '1'}) &divide; ({prodtxt(bot)}))")
        else:
            steps.append(f"<b>Product law</b> (added logs multiply): {nm}({prodtxt(top)})")
    final_arg = build_arg(allf)
    steps.append(f"<b>Simplify the inside:</b> {HL(nm + '(' + pp(final_arg) + ')')}")
    res = f"{nm}({pp(final_arg)})"
    if not variables(final_arg) and (base0 is None or base0[0] != "const"):
        q = ev_exact(final_arg)
        if q is not None and q > 0:
            r = exact_log(q, ev_exact(bnode)) if ev_exact(bnode) not in (None, 1) else None
            if r is not None:
                steps.append(f"<b>Neat finish:</b> {pp(bnode)}<sup>{fmtq(r)}</sup> = {fmtq(q)}, so {res} = {HL(fmtq(r))}.")
                res += f" = {fmtq(r)}"
            else:
                val = math.log(float(q)) / math.log(ev_float(bnode))
                steps.append(f"On a calculator: {res} &asymp; {sig(val, 4)}")
    return _ok(steps, res)


# ============================================================ equations ====

def _pos_ok(val, exact):
    return val > 0 if exact else val > 1e-9


def _val_text(x, exact):
    return fmtq(x) if exact else sig(x, 4)


def _root_line(r):
    """(Fraction|None, float, text) -> 'x = ...' pieces"""
    ex, fl, txt = r
    if ex is not None:
        return txt + ("" if ex.denominator == 1 or "/" in txt else ""), fl
    return txt, fl


def _fmt_root(r, v="x"):
    ex, fl, txt = r
    if ex is not None:
        s = f"{v} = {txt}"
        if ex.denominator != 1 and "/" in txt:
            s += f" (= {sig(fl, 4)})"
        return s
    if txt == "1":
        return f"{v} = 1"
    if txt == "~":
        return f"{v} &asymp; {sig(fl, 4)}"
    return f"{v} = {txt} &asymp; {sig(fl, 4)}"


def solve_poly_steps(E, v, steps, label="the equation", show_std=True):
    """show how a polynomial equation E = 0 (deg <= 4) is solved; returns root tuples"""
    d = E.deg()
    if show_std:
        steps.append(f"<b>Rearrange to get {label} in standard form:</b> {HL(E.text(v) + ' = 0')}")
    if d == 0:
        return []
    if d == 1:
        a, b = E.c[1], E.c[0]
        steps.append(f"Solve the simple equation: {fmtq(a) if a != 1 else ''}{v} = {fmtq(-b)}" + (f", so {v} = {fmtq(-b)} &divide; {fmtq(a)} = {fmtq(-b / a)}" if a != 1 else ""))
        return real_roots(E)
    roots = real_roots(E)
    if d == 2:
        a, b, c = E.c[2], E.c[1], E.c[0]
        D = b * b - 4 * a * c
        rat = [r for r in roots if r[0] is not None]
        if len(rat) == len(roots) and roots and all(abs(r[0].numerator) < 10 ** 7 for r in rat):
            fac = " ".join(f"({v} {MINUS if r[0] > 0 else '+'} {fmtq(abs(r[0]))})" if r[0] != 0 else v for r in roots) if len(roots) == 2 else \
                (f"({v} {MINUS if roots[0][0] > 0 else '+'} {fmtq(abs(roots[0][0]))})<sup>2</sup>" if roots[0][0] != 0 else f"{v}<sup>2</sup>")
            steps.append(f"<b>Factorise</b> (or use the formula): {HL((fmtq(a) + ' ' if a != 1 else '') + fac + ' = 0')}. "
                         f"Each bracket can be zero: " + " or ".join(f"{v} = {fmtq(r[0])}" for r in roots) + ".")
        else:
            steps.append(f"<b>Use the quadratic formula</b> {v} = (&minus;b &plusmn; &radic;(b<sup>2</sup> &minus; 4ac)) &divide; 2a with a = {fmtq(a)}, b = {fmtq(b)}, c = {fmtq(c)}: "
                         f"b<sup>2</sup> &minus; 4ac = {fmtq(D)}" + ("" if D >= 0 else " which is negative, so there are no real answers."))
            for r in roots:
                steps.append(_fmt_root(r, v))
    else:
        steps.append("This needs a factor-theorem search. Trying values that divide the last number, the roots found are: " + ", ".join(_fmt_root(r, v) for r in roots))
    return roots


def _domain_table(root, args, v, steps_rows):
    """returns True if every log argument stays positive. Adds a text row."""
    ex, fl, txt = root
    parts, ok = [], True
    for a in args:
        poly = to_poly(a, v)
        val = poly.at(ex) if ex is not None else poly.at(fl)
        good = _pos_ok(val, ex is not None)
        ok = ok and good
        parts.append(f"{pp(a)} = {_val_text(val, ex is not None)} " + ("&check;" if good else "&#10007;"))
    steps_rows.append((f"{v} = {txt}" + ("" if ex is not None else f" &asymp; {sig(fl, 4)}"), "<br>".join(parts), "accept" if ok else "<b>reject</b> (log of a number that is not positive)"))
    return ok


def _t_of(base, k):
    """T = base**k as Fraction (exact if possible), plus flag exact"""
    if base == "e":
        return Fraction(math.exp(float(k))).limit_denominator(10 ** 9), False
    vb = vec_of(base)
    q = vec_to_q(vec_scale(vb, k)) if vb is not None else None
    if q is not None:
        return q, True
    return Fraction(float(base) ** float(k)).limit_denominator(10 ** 9), False


def _common_bases(bases):
    """bases: list of (None|node). Returns (b0 node, {index: Fraction ratio}) so log_bj f = log_b0 f / ratio_j, or None"""
    nodes = [("num", Fraction(10)) if b is None else b for b in bases]
    uniq = []
    for n_ in nodes:
        if n_ not in uniq:
            uniq.append(n_)
    if len(uniq) == 1:
        return uniq[0], {}
    if any(n_[0] == "const" for n_ in uniq):
        return None
    vals = [ev_exact(n_) for n_ in uniq]
    if any(q is None or q <= 0 or q == 1 for q in vals):
        return None
    for i, cand in enumerate(vals):
        rs = [exact_log(q, cand) for q in vals]
        if all(r is not None and r != 0 for r in rs):
            return uniq[i], {uniq[j]: rs[j] for j in range(len(uniq))}
    return None


def _quad_in_log(lhs, rhs, v, base):
    """equation that is a polynomial in L = log_b(x) (degree >= 2)"""
    Lnode = ("log", ("var", v), base)
    E = to_poly(lhs, v, {Lnode: P1.x()}) - to_poly(rhs, v, {Lnode: P1.x()})
    return E


@guard
def solve_equation(expr):
    expr = (expr or "").strip()
    if not expr:
        return _fail("Please type an equation first, for example log_2(x) = 5.")
    if expr.count("=") != 1:
        return _fail("Please give one equation with exactly one = sign, e.g. <b>log_2(x) = 5</b> or <b>2^x = 5</b>.")
    ls, rs = expr.split("=")
    if not ls.strip() or not rs.strip():
        return _fail("One side of the = sign is empty. Write something on both sides, like <b>log_2(x) = 5</b>.")
    lhs, rhs = parse(ls), parse(rs)
    letters = variables(lhs) | variables(rhs)
    if not letters:
        return _fail("I could not find an unknown letter (like x) in that equation.")
    if len(letters) > 1:
        return _fail("I can only solve for <b>one</b> unknown letter at a time (like x). I found: " + ", ".join(sorted(letters)) + ".")
    v = next(iter(letters))
    steps = [f"<b>Equation:</b> {pp(lhs)} = {pp(rhs)}"]
    for a_, b_, text_ in ((lhs, rhs, rs), (rhs, lhs, ls)):
        if a_ == ("var", v) and not variables(b_) and has_log(b_):
            res = evaluate(text_)
            if res["ok"]:
                val = res["result"].split(" = ", 1)[-1]
                return _ok(steps + ["<b>This is already solved for " + v + "</b>; we only need to work out the log:"] + res["steps"], f"{v} = {val}")
    logs = logs_in(lhs) + logs_in(rhs)
    if any(variables(l[2]) for l in logs if l[2] is not None):
        return _solve_var_base(lhs, rhs, v, steps)
    if any(variables(l[1]) for l in logs):
        return _solve_log_eq(lhs, rhs, v, steps)
    if contains_var_in_exponent(lhs, v) or contains_var_in_exponent(rhs, v):
        return _solve_exponential(lhs, rhs, v, steps)
    return _fail("This equation does not have the unknown inside a logarithm or in a power, so it is not a logarithm/index equation. "
                 "Try the Algebra solvers for it.")


# ----------------------------------------------------------- log equations ----

def _solve_log_eq(lhs, rhs, v, steps):
    logs = _atoms(lhs) + [a for a in _atoms(rhs) if a not in _atoms(lhs)]
    # ---- polynomial in log x (like (log x)^2 - 3 log x + 2 = 0)
    plain_x = all(l[1] == ("var", v) for l in logs)
    bases = [l[2] for l in logs]
    if plain_x and len({repr(b) for b in bases}) == 1:
        try:
            E = _quad_in_log(lhs, rhs, v, bases[0])
        except LogErr:
            E = None
        if E is not None and E.deg() >= 2:
            nm = log_name(bases[0])
            steps.append(f"<b>Spot the pattern:</b> {nm}({v}) appears on its own and also squared. Give it a new name to make it easier: "
                         f"let <b>y = {nm}({v})</b>.")
            roots = solve_poly_steps(E, "y", steps, "the equation in y")
            if not roots:
                return _ok(steps, "No real solution")
            bn = ("num", Fraction(10)) if bases[0] is None else bases[0]
            bq = ev_exact(bn) if bn[0] != "const" else "e"
            answers = []
            for r in roots:
                ex, fl, txt = r
                if bq == "e":
                    xv = math.exp(fl)
                    steps.append(f"y = {txt} means {nm}({v}) = {txt}, so {v} = e<sup>{txt}</sup> &asymp; {sig(xv, 4)}.")
                    answers.append(f"{v} &asymp; {sig(xv, 4)}")
                    continue
                if ex is not None:
                    T, exact = _t_of(bq, ex)
                    if exact:
                        steps.append(f"y = {txt} means {nm}({v}) = {txt}. Change to index form (log form &harr; power form): {v} = {fmtq(bq)}<sup>{txt}</sup> = {HL(fmtq(T))}.")
                        answers.append(f"{v} = {fmtq(T)}")
                        continue
                xv = float(bq) ** fl
                steps.append(f"y = {txt} means {nm}({v}) = {txt}, so {v} = {fmtq(bq)}<sup>{txt}</sup> &asymp; {HL(sig(xv, 4))}.")
                answers.append(f"{v} &asymp; {sig(xv, 4)}")
            steps.append(f"Every answer is positive, so each {v} is allowed inside the log. &check;")
            return _ok(steps, ", &nbsp; ".join(answers))
    # ---- sum of logs
    terms, const = lin_logs(("sub", lhs, rhs))
    terms = merge_terms(terms)
    if not terms:
        return _fail("The logs cancel out completely, so there is nothing to solve for.")
    originals = [l for a, l in terms]
    k = -const
    # same base
    cb = _common_bases([l[2] for a, l in terms])
    if cb is None:
        return _fail("The logs use <b>different bases</b> that are not powers of one another. Change them to the same base first (see the Change of Base tab).")
    b0, ratios = cb
    new_terms = []
    if ratios:
        steps.append(f"<b>The bases are different, so change them all to base {pp(b0)}</b> using log<sub>b</sub>(a) = log<sub>{pp(b0)}</sub>(a) &divide; log<sub>{pp(b0)}</sub>(b):")
        for a, l in terms:
            bj = ("num", Fraction(10)) if l[2] is None else l[2]
            r = ratios[bj]
            if bj == b0:
                new_terms.append([a, l[1]])
            else:
                steps.append(f"log<sub>{pp(bj)}</sub>({pp(l[1])}) = log<sub>{pp(b0)}</sub>({pp(l[1])}) &divide; {fmtq(r)} (because log<sub>{pp(b0)}</sub>({pp(bj)}) = {fmtq(r)})")
                new_terms.append([a / r, l[1]])
    else:
        new_terms = [[a, l[1]] for a, l in terms]
    new_terms = [[a, f] for a, f in new_terms]
    base_node = b0
    isE = base_node[0] == "const"
    nm = "ln" if isE else (f"log<sub>{pp(base_node)}</sub>" if base_node != ("num", Fraction(10)) else "log")
    bq = "e" if isE else ev_exact(base_node)
    if (not isE and (bq is None or bq <= 0 or bq == 1)):
        return _fail("The base of the logs must be a positive number other than 1.")
    # collect on left
    try:
        _, cl = lin_logs(lhs) if has_log(lhs) else ([], Fraction(0))
    except LogErr:
        cl = Fraction(0)
    if has_log(rhs) or cl != 0:
        steps.append(f"<b>Collect all the logs on the left and the plain numbers on the right:</b> " +
                     f"{lin_text([[a, f] for a, f in new_terms], base=(None if base_node == ("num", Fraction(10)) else base_node))} = {fmtq(k)}")
    # clear fractions
    lcm = 1
    for a, f in new_terms:
        lcm = lcm * a.denominator // math.gcd(lcm, a.denominator)
    lcm = lcm * k.denominator // math.gcd(lcm, k.denominator)
    if lcm != 1:
        steps.append(f"<b>Multiply every term by {lcm}</b> to clear the fractions.")
        new_terms = [[a * lcm, f] for a, f in new_terms]
        k = k * lcm
    if any(abs(a) > 8 for a, f in new_terms):
        return _fail("The numbers in front of the logs are too large for me to work with. Please check the equation.")
    # power law
    if any(abs(a) != 1 for a, f in new_terms):
        steps.append("<b>Power law</b> (move the number in front of each log up as a power): " + " ".join(
            (("" if i == 0 else ("+ " if a > 0 else f"{MINUS} ")) + (f"{MINUS}" if (i == 0 and a < 0) else "") + f"{nm}({pp(f if abs(a) == 1 else ('pow', f, ('num', abs(a))))})") for i, (a, f) in enumerate(new_terms)) + f" = {fmtq(k)}")
    pos = [f if a == 1 else ("pow", f, ("num", a)) for a, f in new_terms if a > 0]
    neg = [f if a == -1 else ("pow", f, ("num", -a)) for a, f in new_terms if a < 0]
    prodtxt = lambda ns: " &times; ".join(pp(x, 3) for x in ns)
    Nn = pos[0] if pos else ("num", Fraction(1))
    for x_ in pos[1:]:
        Nn = ("mul", Nn, x_)
    Dn = None
    if neg:
        Dn = neg[0]
        for x_ in neg[1:]:
            Dn = ("mul", Dn, x_)
    if len(new_terms) > 1:
        inside = pp(("div", Nn, Dn)) if neg else pp(Nn)
        steps.append(f"<b>Product / quotient laws</b> (added logs multiply, subtracted logs divide): {nm}({inside}) = {fmtq(k)}")
    ep = "1" if k == 0 else ("e" if k == 1 else f"e<sup>{fmtq(k)}</sup>")
    argtxt = pp(("div", Nn, Dn)) if Dn is not None else pp(Nn)
    steps.append(f"<b>Change to index (power) form:</b> {nm}(N) = k means N = {'e' if isE else fmtq(bq)}<sup>k</sup>. So {HL(argtxt + ' = ' + (ep if isE else fmtq(bq) + '<sup>' + fmtq(k) + '</sup>'))}")
    T, exact = _t_of(bq, k)
    if exact:
        steps.append(f"{'e' if isE else fmtq(bq)}<sup>{fmtq(k)}</sup> = {fmtq(T)}")
    else:
        steps.append(f"{ep if isE else fmtq(bq) + '<sup>' + fmtq(k) + '</sup>'} &asymp; {sig(float(T), 6)} (use a calculator)")
    PN = to_poly(Nn, v)
    PD = to_poly(Dn, v) if Dn is not None else P1.const(1)
    shown = []
    if pos and (len(pos) > 1 or pos[0][0] in ("pow", "mul", "add", "sub")) and PN.deg() >= 1 and (len(pos) > 1 or pos[0][0] in ("pow", "mul")):
        shown.append(f"{pp(Nn)} = {PN.text(v)}")
    if Dn is not None and (len(neg) > 1 or Dn[0] in ("pow", "mul")) and PD.deg() >= 1:
        shown.append(f"{pp(Dn)} = {PD.text(v)}")
    shown = [t for t in shown if t.split(" = ")[0] != t.split(" = ")[1]]
    if shown:
        steps.append("<b>Multiply out the brackets:</b><br>" + "<br>".join(shown))
    if Dn is not None:
        steps.append(f"<b>Clear the denominator</b> (multiply both sides by {pp(Dn)}): {PN.text(v)} = {fmtq(T) if exact else sig(float(T), 6)} &times; ({PD.text(v)})")
    E = PN - PD.scale(T)
    if E.deg() == 0:
        if E.is_zero():
            return _ok(steps + ["Both sides are always equal, so this is true for every x that keeps the logs defined."], "True for every x where the logs are defined")
        return _ok(steps + ["The x terms cancel and the numbers do not match, so the equation can never be true."], "No solution")
    if isE and Dn is None and PN.c == [0, 1] and E.deg() == 1:
        roots = [(None, float(T), ep)]
        steps.append(f"So {v} = {ep} &asymp; {sig(float(T), 5)}")
    else:
        roots = solve_poly_steps(E, v, steps)
        if isE:
            roots = [(None, r[1], "~") for r in roots]
    if not roots:
        return _ok(steps + ["There are no real solutions."], "No solution")
    # domain check
    args = []
    for a, l in terms:
        if l[1] not in args:
            args.append(l[1])
    args = [a for a in args]
    rows = []
    good = []
    for r in roots:
        if _domain_table(r, originals_args(originals), v, rows):
            good.append(r)
    steps.append("<b>Check every answer</b> (the number inside a log must be <b>positive</b>, so a value that makes it zero or negative is rejected):")
    steps.append("<table class='stat-table'><tr><th>Answer</th><th>Inside the logs</th><th>Verdict</th></tr>" + "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows) + "</table>")
    if not good:
        return _ok(steps + ["Every candidate answer is rejected, so there is <b>no solution</b>."], "No solution (every candidate makes a log undefined)")
    # numeric verification
    try:
        r0 = good[0]
        lv = ev_float(lhs, {v: r0[1]})
        rv = ev_float(rhs, {v: r0[1]})
        if abs(lv - rv) < 1e-6 * max(1, abs(lv)):
            steps.append(f"<b>Substitute back</b> {v} = {sig(r0[1], 4)}: left side &asymp; {sig(lv, 4)}, right side &asymp; {sig(rv, 4)}. They match. &check;")
    except LogErr:
        pass
    return _ok(steps, ", &nbsp; ".join(_fmt_root(r, v) for r in good))


def originals_args(logs):
    out = []
    for l in logs:
        if l[1] not in out:
            out.append(l[1])
    return out


def _solve_var_base(lhs, rhs, v, steps):
    terms, const = lin_logs(("sub", lhs, rhs))
    terms = merge_terms(terms)
    if len(terms) != 1 or not variables(terms[0][1][2] or ("num", 1)) or variables(terms[0][1][1]):
        return _fail("When the <b>base</b> is the unknown, I can solve one log like <b>log_x(8) = 3</b>. Please write the equation in that form.")
    c, lg = terms[0]
    A = lg[1]
    if lg[2] != ("var", v):
        return _fail("The base should be just the letter (like log_x(8) = 3).")
    kk = -const / c
    Aq = ev_exact(A)
    if Aq is None or Aq <= 0:
        return _fail("The number inside the log must be a positive number.")
    steps.append(f"<b>Isolate the log:</b> log<sub>{v}</sub>({pp(A)}) = {fmtq(kk)}")
    if kk == 0:
        return _fail(f"log<sub>{v}</sub>({pp(A)}) = 0 would need {pp(A)} = 1, so it is not a normal equation for {v}.")
    steps.append(f"<b>Change to index (power) form:</b> log<sub>b</sub>(N) = k means b<sup>k</sup> = N. So {HL(v + '<sup>' + fmtq(kk) + '</sup> = ' + pp(A))}")
    inv = 1 / kk
    va = vec_of(Aq)
    xq = vec_to_q(vec_scale(va, inv)) if va is not None else None
    if xq is not None:
        steps.append(f"To undo the power {fmtq(kk)}, raise both sides to the power 1/({fmtq(kk)}) = {fmtq(inv)}: {v} = {pp(A)}<sup>{fmtq(inv)}</sup> = {HL(fmtq(xq))}")
        xv = float(xq)
        txt = fmtq(xq)
    else:
        xv = float(Aq) ** float(inv)
        steps.append(f"{v} = {pp(A)}<sup>{fmtq(inv)}</sup> &asymp; {HL(sig(xv, 4))} (calculator)")
        txt = "&asymp; " + sig(xv, 4)
    if xv <= 0 or abs(xv - 1) < 1e-12:
        return _ok(steps + [f"But a base must be positive and not 1, so {v} = {txt} is <b>rejected</b>."], "No solution")
    steps.append(f"<b>Check:</b> the base {v} = {sig(xv, 4)} is positive and not 1, so it is allowed. &check;")
    return _ok(steps, f"{v} = {txt}")


# ------------------------------------------------------ exponential equations ----

class _T:
    """coef * B**(m*x + n)   (B None => plain number)"""
    __slots__ = ("coef", "B", "m", "n", "parts", "note")

    def __init__(self, coef, B=None, m=Fraction(0), n=Fraction(0), parts=None, note=None):
        self.coef, self.B, self.m, self.n = Fraction(coef), B, Fraction(m), Fraction(n)
        self.parts, self.note = parts, note


def _neg_T(t):
    return _T(-t.coef, t.B, t.m, t.n, t.parts, t.note)


def _scale_T(t, c):
    return _T(t.coef * c, t.B, t.m, t.n, t.parts, t.note)


def _parts(t):
    return t.parts or [(t.B, t.m, t.n)]


def _mul_T(a, b):
    """product of two terms that each carry the unknown"""
    if a.B is None:
        return _scale_T(b, a.coef)
    if b.B is None:
        return _scale_T(a, b.coef)
    if "e" in (a.B, b.B):
        if a.B == b.B:
            return _T(a.coef * b.coef, "e", a.m + b.m, a.n + b.n, _parts(a) + _parts(b))
        raise LogErr("Mixing e with another base in a product is too hard for this solver.")
    r = exact_log(b.B, a.B)
    if r is not None:
        return _T(a.coef * b.coef, a.B, a.m + r * b.m, a.n + r * b.n, _parts(a) + _parts(b))
    if a.m == b.m and a.m != 0:
        Tq1, e1 = _t_of(a.B, a.n)
        Tq2, e2 = _t_of(b.B, b.n)
        if e1 and e2:
            note = f"{fmtq(a.B)}<sup>{_lin(a.m, a.n, 'x')}</sup> &times; {fmtq(b.B)}<sup>{_lin(b.m, b.n, 'x')}</sup> = ({fmtq(a.B)} &times; {fmtq(b.B)})<sup>{_lin(a.m, 0, 'x')}</sup> &times; {fmtq(Tq1 * Tq2)} = {fmtq(a.B * b.B)}<sup>{_lin(a.m, 0, 'x')}</sup> &times; {fmtq(Tq1 * Tq2)}"
            return _T(a.coef * b.coef * Tq1 * Tq2, a.B * b.B, a.m, 0, None, note)
    raise LogErr("I can multiply powers with the unknown when their bases are powers of the same number (like 9<sup>x</sup> &times; 3<sup>x+1</sup>) or when the powers match (like 2<sup>x</sup> &times; 3<sup>x</sup>).")


def _exp_terms(node, v):
    k = node[0]
    if k == "num":
        return [_T(node[1])]
    if k == "neg":
        return [_neg_T(t) for t in _exp_terms(node[1], v)]
    if k in ("add", "sub"):
        a = _exp_terms(node[1], v)
        b = _exp_terms(node[2], v)
        if k == "sub":
            b = [_neg_T(t) for t in b]
        return a + b
    if k == "mul":
        va, vb = variables(node[1]), variables(node[2])
        if va and vb:
            A_ = _exp_terms(node[1], v)
            B_ = _exp_terms(node[2], v)
            return [_mul_T(a_, b_) for a_ in A_ for b_ in B_]
        if va:
            c = ev_exact(node[2])
            ts = _exp_terms(node[1], v)
        else:
            c = ev_exact(node[1])
            ts = _exp_terms(node[2], v)
        if c is None:
            raise LogErr("I can multiply a power only by a plain number here.")
        return [_scale_T(t, c) for t in ts]
    if k == "div":
        if variables(node[2]):
            ts = _exp_terms(node[2], v)
            if len(ts) != 1 or ts[0].B is None:
                raise LogErr("I can only divide by a single power of a number here.")
            t = ts[0]
            rec = _T(1 / t.coef, t.B, -t.m, -t.n, [(b_, -m_, -n_) for b_, m_, n_ in _parts(t)])
            if variables(node[1]):
                return [_mul_T(a_, rec) for a_ in _exp_terms(node[1], v)]
            c = ev_exact(node[1])
            if c is None:
                raise LogErr("I can only divide a plain number by a power here.")
            return [_scale_T(rec, c)]
        d = ev_exact(node[2])
        if d is None or d == 0:
            raise LogErr("I can only divide by plain numbers here.")
        return [_scale_T(t, 1 / d) for t in _exp_terms(node[1], v)]
    if k == "pow":
        if variables(node[2]):
            if variables(node[1]):
                raise LogErr("An unknown in both the base and the power is too hard for this solver.")
            fac = Fraction(1)
            bn = node[1]
            if bn[0] == "sqrt":
                bn, fac = bn[1], Fraction(1, 2)
            elif bn[0] == "pow" and not variables(bn[2]) and ev_exact(bn[2]) is not None:
                bn, fac = bn[1], ev_exact(bn[2])
            if bn == ("const", "e"):
                B = "e"
            else:
                B = ev_exact(bn)
                if B is None or B <= 0 or B == 1:
                    raise LogErr("The base of the power must be a positive number other than 1.")
            P = to_poly(node[2], v)
            if P.deg() > 1:
                raise LogErr("The power must be a simple expression like x, 2x or x + 1.")
            return [_T(1, B, fac * (P.c[1] if P.deg() == 1 else 0), fac * (P.c[0] if P.c else 0))]
        q = ev_exact(node)
        if q is None:
            raise LogErr("I could not work out the plain-number power in your equation.")
        return [_T(q)]
    if k == "sqrt":
        q = ev_exact(node)
        if q is None:
            raise LogErr("I could not work out the root in your equation.")
        return [_T(q)]
    if k == "var":
        raise LogErr("Mixing a plain x with a power of x (like 2<sup>x</sup> = x + 1) is too hard for this solver.")
    raise LogErr("I could not understand that part of the equation.")


def _lg4(q):
    return round(math.log10(float(q)), 4)


def _solve_exponential(lhs, rhs, v, steps):
    tl = _exp_terms(lhs, v)
    tr = _exp_terms(rhs, v)
    terms = tl + [_neg_T(t) for t in tr]
    const0 = Fraction(0)
    var_terms = []
    for t in terms:
        if t.B is None or t.m == 0:
            if t.B is None:
                const0 += t.coef
            else:
                q = _t_of(t.B, t.n)
                if not q[1]:
                    raise LogErr("That number power is not a neat number, so I cannot continue.")
                const0 += t.coef * q[0]
        else:
            var_terms.append(t)
    if not var_terms:
        raise LogErr("The unknown cancelled out of the powers.")
    Bs = [p_[0] for t in var_terms for p_ in _parts(t)]
    steps.append("<b>An index (exponential) equation:</b> the unknown is in the power. The plan: write all the powers with the <b>same base</b>, or use logs.")
    # ---- common base
    uniqB = []
    for b in Bs:
        if b not in uniqB:
            uniqB.append(b)
    u, rmap = None, {}
    if all(b == "e" for b in uniqB):
        u, rmap = "e", {"e": Fraction(1)}
    elif "e" not in uniqB:
        for cand in uniqB:
            pr = primitive_root(cand)
            if pr is None:
                continue
            u0 = pr[0]
            rs = {b: exact_log(b, u0) for b in uniqB}
            if all(r is not None and r.denominator == 1 for r in rs.values()):
                u, rmap = u0, rs
                break
    if u is None:
        return _fallback_two_bases(var_terms, const0, v, steps)
    us = "e" if u == "e" else fmtq(u)
    # rewrite each term
    rows = []
    M, kap = [], []
    for t in var_terms:
        if t.note and not t.parts:
            rows.append(t.note)
        prs = _parts(t)
        Mj = sum((rmap[p_[0]] * p_[1] for p_ in prs), Fraction(0))
        Nj = sum((rmap[p_[0]] * p_[2] for p_ in prs), Fraction(0))
        if u == "e":
            kq, ex = Fraction(t.coef), True
        else:
            Tq, ex = _t_of(u, Nj)
            kq = t.coef * Tq
        if not ex:
            return _fallback_two_bases(var_terms, const0, v, steps)
        M.append(Mj)
        kap.append(kq)
        if u != "e":
            for pb, pm, pn in prs:
                if pb != u:
                    rr = rmap[pb]
                    rows.append(f"{fmtq(pb)}<sup>{_lin(pm, pn, v)}</sup> = ({us}<sup>{fmtq(rr)}</sup>)<sup>{_lin(pm, pn, v)}</sup> = {us}<sup>{_lin(rr * pm, rr * pn, v)}</sup>")
            if len(prs) > 1:
                rows.append(f"Powers of the same base multiply by <b>adding</b> the indices: " + " &times; ".join(f"{us}<sup>{_lin(rmap[pb] * pm, rmap[pb] * pn, v)}</sup>" for pb, pm, pn in prs) + f" = {us}<sup>{_lin(Mj, Nj, v)}</sup>")
    if rows:
        steps.append(f"<b>Write every power with the same base ({us}):</b><br>" + "<br>".join(rows))
    # generator
    g = Fraction(0)
    for Mj in M:
        g = _fgcd(g, abs(Mj))
    exps = [int(Mj / g) for Mj in M]
    ymin = min(exps + [0])
    ymax = max(exps + [0])
    if ymax - ymin > 4:
        return _fail("The powers are too far apart for me to solve this by hand. Please check the equation.")
    ytxt = f"{us}<sup>{(fmtq(g) if g != 1 else '')}{v}</sup>"
    if len(var_terms) == 1 and len(set(exps)) == 1 and exps[0] == 1 or (len(var_terms) >= 1 and g != 1 or True):
        steps.append(f"<b>Let y = {ytxt}</b>" + (" (every power of x in the equation can be written using y)." if len(var_terms) > 1 or abs(exps[0]) != 1 else "."))
    coeffs = {}
    for e, kq in zip(exps, kap):
        coeffs[e - ymin] = coeffs.get(e - ymin, Fraction(0)) + kq
    coeffs[0 - ymin] = coeffs.get(0 - ymin, Fraction(0)) + const0
    deg = ymax - ymin
    E = P1([coeffs.get(i, Fraction(0)) for i in range(deg + 1)])
    # show substituted equation before shifting
    def y_term(e):
        return "y" if e == 1 else (f"y<sup>{e}</sup>" if e > 1 else f"y<sup>{MINUS}{-e}</sup>")
    shown = []
    for e in sorted({*exps, 0} if const0 else set(exps), reverse=True):
        c = sum((kq for ee, kq in zip(exps, kap) if ee == e), Fraction(0)) + (const0 if e == 0 else 0)
        if c == 0:
            continue
        mag = abs(c)
        body = (fmtq(mag) if (mag != 1 or e == 0) else "") + ("" if e == 0 else y_term(e))
        shown.append((c, body))
    eq_txt = ""
    for i, (c, body) in enumerate(shown):
        eq_txt += (MINUS if c < 0 else "") + body if i == 0 else f" {MINUS if c < 0 else '+'} {body}"
    steps.append(f"<b>Substitute:</b> {HL(eq_txt + ' = 0')}")
    if ymin < 0:
        steps.append(f"<b>Multiply through by y{'<sup>' + str(-ymin) + '</sup>' if -ymin > 1 else ''}</b> to remove the negative powers.")
    if deg == 0:
        return _fail("The equation reduces to a plain number statement, so it has no unknown left.")
    if E.is_zero():
        return _ok(steps + ["Both sides are always equal, so the equation is true for <b>every</b> value of " + v + "."], "True for every value of " + v + " (an identity)")
    yroots = solve_poly_steps(E, "y", steps, "the equation in y", show_std=(deg > 1 or ymin < 0))
    if not yroots:
        return _ok(steps + ["There is no real value of y, so <b>no solution</b>."], "No solution")
    answers, accepted = [], 0
    for r in yroots:
        ex, fl, txt = r
        if fl <= 1e-12:
            steps.append(f"y = {txt} is <b>rejected</b>: y = {ytxt} is a power of a positive number, which can never be zero or negative.")
            continue
        accepted += 1
        ux = float(u) if u != "e" else math.e
        if ex is not None and u != "e":
            rr = exact_log(ex, u)
        else:
            rr = None
        if rr is None and u != "e" and fl > 0:
            lx0 = math.log(fl) / (math.log(float(u)) * float(g))
            fr0 = Fraction(lx0).limit_denominator(12)
            if abs(float(fr0) - lx0) < 1e-9 * max(1, abs(lx0)):
                rr = fr0 * g
        if rr is not None:
            xq = rr / g
            steps.append(f"y = {txt}: {ytxt} = {txt} = {us}<sup>{fmtq(rr)}</sup>. The bases match, so the powers match: {(fmtq(g) if g != 1 else '')}{v} = {fmtq(rr)}"
                         + (f", so {v} = {fmtq(rr)} &divide; {fmtq(g)} = {HL(fmtq(xq))}" if g != 1 else f", so {HL(v + ' = ' + fmtq(xq))}"))
            xval = float(xq)
            answers.append(f"{v} = {fmtq(xq)}" + (f" (= {sig(xval, 4)})" if "/" in fmtq(xq) else ""))
        else:
            if u == "e":
                lx = math.log(fl) / float(g)
                steps.append(f"y = {txt}: e<sup>{(fmtq(g) if g != 1 else '')}{v}</sup> = {sig(fl, 5)}. Take natural logs (ln) of both sides: {(fmtq(g) if g != 1 else '')}{v} = ln({sig(fl, 5)}), so {v} = {HL(sig(lx, 4))}")
            else:
                lg_y, lg_u = round(math.log10(fl), 4), round(math.log10(ux), 4)
                lx = lg_y / lg_u / float(g)
                steps.append(f"y = {txt}: {ytxt} = {sig(fl, 5)}. <b>Take logs of both sides</b> (log brings the power down): {(fmtq(g) + ' &times; ' if g != 1 else '')}{v} &times; lg({us}) = lg({sig(fl, 5)}). "
                             f"With lg({us}) = {dp_(lg_u, 4)} and lg({sig(fl, 5)}) = {dp_(lg_y, 4)}: {v} = {dp_(lg_y, 4)} &divide; ({(fmtq(g) + ' &times; ' if g != 1 else '')}{dp_(lg_u, 4)}) = {HL(sig(lx, 4))}")
            answers.append(f"{v} &asymp; {sig(lx, 4)}")
    if not accepted:
        return _ok(steps, "No solution")
    return _ok(steps, ", &nbsp; ".join(answers))


def _fgcd(a, b):
    a, b = Fraction(a), Fraction(b)
    if a == 0:
        return b
    if b == 0:
        return a
    n = math.gcd(a.numerator * b.denominator, b.numerator * a.denominator)
    return Fraction(n, a.denominator * b.denominator)


def _lin(m, n, v):
    m, n = Fraction(m), Fraction(n)
    s = ""
    if m != 0:
        s = ("" if m == 1 else (MINUS if m == -1 else fmtq(m))) + v
    if n != 0:
        s += (f" {'+' if n > 0 else MINUS} {fmtq(abs(n))}" if s else fmtq(n))
    return s or "0"


def _fallback_two_bases(var_terms, const0, v, steps):
    if const0 != 0 or len(var_terms) != 2:
        return _fail("This equation mixes powers with different bases in a way that is too hard for this solver. Try to rearrange it so that each side is a single power.")
    t1, t2 = var_terms
    if "e" in (t1.B, t2.B):
        return _fail("Please use powers of e only, or only whole-number bases.")
    # coef1*B1^(m1 x+n1) + coef2*B2^(m2 x+n2) = 0  ->  A B1^.. = C B2^..
    if t1.coef * t2.coef >= 0:
        return _ok(steps + ["Both powers are positive numbers, so they cannot add up to zero."], "No solution")
    A, C = t1.coef, -t2.coef
    if A < 0:
        A, C = -A, -C
        A, C = -t1.coef, t2.coef  # fallback consistent
        A, C = abs(t1.coef), abs(t2.coef)
    steps.append(f"<b>The bases ({fmtq(t1.B)} and {fmtq(t2.B)}) cannot be written as powers of one number, so take logs of both sides.</b> "
                 f"{(fmtq(A) + ' &times; ') if A != 1 else ''}{fmtq(t1.B)}<sup>{_lin(t1.m, t1.n, v)}</sup> = {(fmtq(C) + ' &times; ') if C != 1 else ''}{fmtq(t2.B)}<sup>{_lin(t2.m, t2.n, v)}</sup>")
    l1, l2, la, lc = _lg4(t1.B), _lg4(t2.B), _lg4(A), _lg4(C)
    steps.append(f"<b>Log of both sides</b> (log of a product is a sum; log of a power brings the power down): " +
                 (f"lg({fmtq(A)}) + " if A != 1 else "") + f"({_lin(t1.m, t1.n, v)}) lg({fmtq(t1.B)}) = " + (f"lg({fmtq(C)}) + " if C != 1 else "") + f"({_lin(t2.m, t2.n, v)}) lg({fmtq(t2.B)})")
    steps.append(f"Values: lg({fmtq(t1.B)}) = {dp_(l1)}, lg({fmtq(t2.B)}) = {dp_(l2)}" + (f", lg({fmtq(A)}) = {dp_(la)}" if A != 1 else "") + (f", lg({fmtq(C)}) = {dp_(lc)}" if C != 1 else ""))
    coef_x = float(t1.m) * l1 - float(t2.m) * l2
    rest = lc - la + float(t2.n) * l2 - float(t1.n) * l1
    steps.append(f"<b>Collect the {v} terms:</b> {v}({fmtq(t1.m)} &times; {dp_(l1)} {MINUS} {fmtq(t2.m)} &times; {dp_(l2)}) = {dp_(rest)} &nbsp;&rarr;&nbsp; {dp_(coef_x)}{v} = {dp_(rest)}")
    if abs(coef_x) < 1e-12:
        return _ok(steps, "No solution" if abs(rest) > 1e-9 else "True for all x")
    x = rest / coef_x
    steps.append(f"{v} = {dp_(rest)} &divide; {dp_(coef_x)} = {HL(sig(x, 4))}")
    return _ok(steps, f"{v} &asymp; {sig(x, 4)}")
