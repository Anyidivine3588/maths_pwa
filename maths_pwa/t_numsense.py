"""Number sense: standard form, rounding (d.p. / s.f.), estimation, errors and limits of accuracy."""
import ast
import math
import re
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, getcontext
from fractions import Fraction

import topics
from tcommon import UErr, field, select, guard, _ok, _fail
from frac_numeric import table

getcontext().prec = 80
MINUS = "&minus;"


def HL(s):
    return f"<span class='hl'>{s}</span>"


def D(s, label="the number"):
    t = (s or "").strip().replace("−", "-").replace(",", "").replace(" ", "")
    if t == "":
        raise UErr(f"Please fill in {label}.")
    if not re.fullmatch(r"[+-]?(\d{1,30}(\.\d{0,30})?|\.\d{1,30})", t):
        raise UErr(f"{label}: '{re.sub('[<>&]', '', t[:20])}' is not a number. Use things like 45000 or 0.0037.")
    return Decimal(t)


def plain(x):
    if x.as_tuple().exponent < -10:
        x = x.quantize(Decimal("1e-10"))
    s = format(x, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return (s or "0").replace("-", MINUS)


def sci(a, n):
    a = Decimal(a)
    return f"{plain(a)} &times; 10<sup>{str(n).replace('-', MINUS)}</sup>"


def to_sf(x):
    """normalise Decimal -> (mantissa, exponent) with 1 <= |m| < 10"""
    if x == 0:
        return Decimal(0), 0
    e = x.adjusted()
    m = x.scaleb(-e)
    return m.normalize(), e


def count_sf(text):
    t = text.strip().lstrip("+-−").replace(",", "")
    if "." in t:
        digits = t.replace(".", "").lstrip("0")
        return len(digits)
    return len(t.lstrip("0").rstrip("0")) or 1


# ----------------------------------------------------------- standard form ----
@guard
def standard(d):
    mode = d.get("mode", "to")
    steps = []
    if mode == "to":
        txt = d.get("x", "")
        x = D(txt, "The number")
        if x == 0:
            raise UErr("Zero cannot be written in standard form.")
        m, e = to_sf(x)
        steps.append("<b>Standard form</b> (also called scientific notation) writes a number as <b>a &times; 10<sup>n</sup></b>, where <b>a is between 1 and 10</b> (at least 1, less than 10) and n is a whole number (it can be negative). It is used for very big and very small numbers.")
        digits = format(abs(x), "f")
        steps.append(f"<b>Step 1: find where the decimal point must go.</b> Put it just after the first non-zero digit, so a is between 1 and 10. Your number {HL(plain(x))} becomes a = {HL(plain(m))}.")
        if e > 0:
            steps.append(f"<b>Step 2: count how many places the point moved.</b> It moved {e} place{'s' if e != 1 else ''} to the <b>left</b>, and the number was big, so the power is <b>positive</b>: n = {e}.")
        elif e < 0:
            steps.append(f"<b>Step 2: count how many places the point moved.</b> It moved {-e} place{'s' if e != -1 else ''} to the <b>right</b>, and the number was small (less than 1), so the power is <b>negative</b>: n = {MINUS}{-e}.")
        else:
            steps.append("The point did not need to move, so n = 0 (10<sup>0</sup> = 1).")
        steps.append("<b>Rule to remember:</b> big number &rarr; positive power; small number (between 0 and 1) &rarr; negative power.")
        ans = sci(m, e)
        steps.append(f"<b>Answer:</b> {HL(ans)}")
        return _ok(steps, f"<b>{plain(x)} = {ans}</b>")
    if mode == "from":
        a = D(d.get("a"), "a")
        n = int(D(d.get("n"), "The power n"))
        if abs(n) > 40:
            raise UErr("Please use a power between &minus;40 and 40.")
        val = a.scaleb(n)
        steps.append(f"<b>Standard form to ordinary number.</b> {sci(a, n)}. The power {HL(str(n).replace('-', MINUS))} tells us how many places to move the decimal point: "
                     f"{'<b>right</b> (positive power makes the number bigger)' if n > 0 else ('<b>left</b> (negative power makes the number smaller)' if n < 0 else 'none')}.")
        steps.append(f"Move the point in {plain(a)} by {abs(n)} place{'s' if abs(n) != 1 else ''} {'to the right' if n > 0 else 'to the left'}, filling empty places with zeros.")
        steps.append(f"<b>Answer:</b> {HL(plain(val) if abs(n) < 40 else format(val, 'f'))}")
        return _ok(steps, f"<b>{sci(a, n)} = {plain(val)}</b>")
    # calculate
    a1, n1 = D(d.get("a1"), "First a"), int(D(d.get("n1"), "First power"))
    a2, n2 = D(d.get("a2"), "Second a"), int(D(d.get("n2"), "Second power"))
    op = d.get("op", "mul")
    for a in (a1, a2):
        if a == 0:
            raise UErr("Use non-zero numbers.")
    if max(abs(n1), abs(n2)) > 40:
        raise UErr("Please use powers between &minus;40 and 40.")
    steps = [f"<b>Calculate:</b> ({sci(a1, n1)}) {'&times;' if op == 'mul' else ('&divide;' if op == 'div' else ('+' if op == 'add' else MINUS))} ({sci(a2, n2)})"]
    if op == "mul":
        steps.append(f"<b>Multiply the a-parts</b> and <b>add the powers</b> of 10 (10<sup>{n1}</sup> &times; 10<sup>{n2}</sup> = 10<sup>{n1} + {n2}</sup>): ({plain(a1)} &times; {plain(a2)}) &times; 10<sup>{n1 + n2}</sup> = {plain(a1 * a2)} &times; 10<sup>{n1 + n2}</sup>".replace("+ -", "+ (&minus;"))
        val = a1 * a2
        e = n1 + n2
    elif op == "div":
        steps.append(f"<b>Divide the a-parts</b> and <b>subtract the powers</b> (10<sup>{n1}</sup> &divide; 10<sup>{n2}</sup> = 10<sup>{n1} &minus; ({n2})</sup>): ({plain(a1)} &divide; {plain(a2)}) &times; 10<sup>{n1 - n2}</sup> = {plain(a1 / a2)} &times; 10<sup>{n1 - n2}</sup>")
        val = a1 / a2
        e = n1 - n2
    else:
        e = max(n1, n2)
        b1, b2 = a1.scaleb(n1 - e), a2.scaleb(n2 - e)
        steps.append(f"<b>To add or subtract, the powers of 10 must be the same.</b> Change both to 10<sup>{e}</sup>: {plain(a1)} &times; 10<sup>{n1}</sup> = {plain(b1)} &times; 10<sup>{e}</sup>, and {plain(a2)} &times; 10<sup>{n2}</sup> = {plain(b2)} &times; 10<sup>{e}</sup>.")
        val = b1 + b2 if op == "add" else b1 - b2
        steps.append(f"Now {'add' if op == 'add' else 'subtract'} the a-parts: {plain(b1)} {'+' if op == 'add' else MINUS} {plain(b2)} = {plain(val)}, giving {plain(val)} &times; 10<sup>{e}</sup>.")
    if val == 0:
        steps.append("The result is 0.")
        return _ok(steps, "<b>0</b>")
    m, k = to_sf(val)
    if k != 0:
        steps.append(f"<b>Is the a-part between 1 and 10?</b> No ({plain(val)}), so adjust: {plain(val)} = {plain(m)} &times; 10<sup>{k}</sup>, so the total power becomes {e} + {k} = {e + k}.".replace("+ -", "+ (&minus;"))
    ans = sci(m, e + k)
    steps.append(f"<b>Answer in standard form:</b> {HL(ans)}")
    return _ok(steps, f"<b>{ans}</b> &nbsp; (= {plain(val.scaleb(e))})")


# ---------------------------------------------------------------- rounding ----
@guard
def rounding(d):
    txt = d.get("x", "")
    x = D(txt, "The number")
    mode = d.get("mode", "sf")
    steps = [f"<b>Your number:</b> {HL(plain(x))}"]
    ax = abs(x)
    if mode == "sf":
        n = int(D(d.get("n"), "How many significant figures"))
        if not 1 <= n <= 20:
            raise UErr("Use between 1 and 20 significant figures.")
        if x == 0:
            raise UErr("Zero has no significant figures to round.")
        steps.append("<b>Significant figures (s.f.)</b> count digits starting from the <b>first non-zero digit</b>. Zeros at the front never count. Zeros between or after other digits (after the decimal point) do count.")
        steps.append(f"Your number has {HL(str(count_sf(txt)))} significant figure{'s' if count_sf(txt) != 1 else ''}" + (" (taking trailing zeros of a whole number as place holders)." if "." not in txt else "."))
        e = ax.adjusted()
        q = Decimal(1).scaleb(e - n + 1)
        res = x.quantize(q, rounding=ROUND_HALF_UP) if (e - n + 1) <= 0 or True else x
        if res.adjusted() > e:
            res = x.quantize(Decimal(1).scaleb(e - n + 2), rounding=ROUND_HALF_UP)
        # deciding digit = digit just after the last kept digit
        shifted = ax.scaleb(-(e - n))   # nth+1 digit is units place
        deciding = int(shifted) % 10
        kept = int(ax.scaleb(-(e - n + 1)))
        steps.append(f"<b>Step 1:</b> the first non-zero digit is the 1st s.f. Count {n} digit{'s' if n != 1 else ''} from it: the last digit we keep is the {n}{'st' if n == 1 else 'nd' if n == 2 else 'rd' if n == 3 else 'th'} s.f.")
        steps.append(f"<b>Step 2: look at the very next digit</b> (the <b>deciding digit</b>): it is {HL(str(deciding))}.")
        steps.append(f"<b>Step 3:</b> deciding digit {deciding} is {'<b>5 or more</b>, so ROUND UP (add 1 to the last kept digit)' if deciding >= 5 else '<b>less than 5</b>, so ROUND DOWN (leave the last kept digit as it is)'}.")
        s = format(res, "f")
        if e - n + 1 > 0 and "." in s:
            s = s.split(".")[0]
        steps.append("<b>Step 4:</b> drop the digits after it, and replace any dropped digits <b>before</b> the decimal point with zeros (so the size stays right).")
        ans = s.replace("-", MINUS)
        steps.append(f"<b>Answer:</b> {HL(ans)} &nbsp; ({n} s.f.)")
        return _ok(steps, f"<b>{plain(x)} = {ans} to {n} significant figure{'s' if n != 1 else ''}</b>")
    if mode == "dp":
        n = int(D(d.get("n"), "How many decimal places"))
        if not 0 <= n <= 20:
            raise UErr("Use between 0 and 20 decimal places.")
        steps.append("<b>Decimal places (d.p.)</b> are the digits <b>after the decimal point</b>. The 1st d.p. is the tenths, 2nd d.p. the hundredths, and so on.")
        shifted = ax.scaleb(n)
        deciding = int(shifted.scaleb(1)) % 10
        steps.append(f"<b>Step 1:</b> count {n} digit{'s' if n != 1 else ''} after the decimal point: that is where we stop.")
        steps.append(f"<b>Step 2: the deciding digit</b> is the next one: {HL(str(deciding))}.")
        steps.append(f"<b>Step 3:</b> {deciding} is {'<b>5 or more</b>: ROUND UP (add 1 to the last kept digit)' if deciding >= 5 else '<b>less than 5</b>: ROUND DOWN (keep the last digit the same)'}.")
        res = x.quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP)
        ans = format(res, "f").replace("-", MINUS)
        steps.append(f"<b>Answer:</b> {HL(ans)} &nbsp; ({n} d.p.)")
        return _ok(steps, f"<b>{plain(x)} = {ans} to {n} decimal place{'s' if n != 1 else ''}</b>")
    # nearest
    p = int(d.get("place", "10"))
    steps.append(f"<b>Rounding to the nearest {p:,}</b>: find the multiples of {p:,} on either side of your number, and pick the closer one. If it is exactly half way, round up.")
    lo = (ax // p) * p
    hi = lo + p
    steps.append(f"Your number lies between {HL(f'{lo:,}')} and {HL(f'{hi:,}')}. The half-way point is {plain(lo + Decimal(p) / 2)}.")
    res = hi if ax - lo >= Decimal(p) / 2 else lo
    steps.append(f"{plain(ax)} is {'at or above' if ax - lo >= Decimal(p) / 2 else 'below'} the half-way point, so it is nearer to {HL(f'{res:,}')}.")
    ans = (MINUS if x < 0 else "") + f"{res:,}"
    return _ok(steps, f"<b>{plain(x)} &asymp; {ans} (nearest {p:,})</b>")


# -------------------------------------------------------------- estimation ----
def _ev(node):
    if isinstance(node, ast.Expression):
        return _ev(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Fraction(str(node.value))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        v = _ev(node.operand)
        return -v if isinstance(node.op, ast.USub) else v
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        a, b = _ev(node.left), _ev(node.right)
        if isinstance(node.op, ast.Add):
            return a + b
        if isinstance(node.op, ast.Sub):
            return a - b
        if isinstance(node.op, ast.Mult):
            return a * b
        if b == 0:
            raise UErr("That divides by 0 after rounding. Use another number.")
        return a / b
    raise UErr("Use only numbers, + - x / and brackets.")


def round1(x):
    """round Decimal to 1 s.f."""
    if x == 0:
        return x
    e = x.adjusted()
    return x.quantize(Decimal(1).scaleb(e), rounding=ROUND_HALF_UP)


@guard
def estimate(d):
    expr = (d.get("e") or "").strip().replace("×", "*").replace("x", "*").replace("X", "*").replace("÷", "/").replace("−", "-").replace(",", "")
    if not expr or len(expr) > 80 or not re.fullmatch(r"[0-9.+\-*/() ]+", expr):
        raise UErr("Type a calculation using numbers, + - x / and brackets, like 4.87 x 31.2 / 0.52.")
    nums = re.findall(r"\d+(?:\.\d+)?|\.\d+", expr)
    if len(nums) > 8:
        raise UErr("Use at most 8 numbers.")
    try:
        exact = _ev(ast.parse(expr, mode="eval"))
    except (SyntaxError, RecursionError):
        raise UErr("I could not read that calculation. Check the brackets and signs.")
    rounded = expr
    reps = []
    def rep(m):
        v = Decimal(m.group())
        r = round1(v)
        reps.append((m.group(), r))
        return format(r, "f")
    rounded = re.sub(r"\d+(?:\.\d+)?|\.\d+", rep, expr)
    est = _ev(ast.parse(rounded, mode="eval"))
    steps = ["<b>Estimating</b> means finding an answer that is close, quickly, without a calculator. The usual method: <b>round every number to 1 significant figure</b>, then do the easy sum.",
             "<b>Step 1: round each number to 1 s.f.</b> (keep the first non-zero digit; look at the next digit to round up or down):",
             table([(a, plain(r)) for a, r in reps], ["Number", "To 1 s.f."]),
             f"<b>Step 2: do the easy calculation:</b> {rounded.replace('*', ' &times; ').replace('/', ' &divide; ')}",
             f"The estimate is {HL(plain(Decimal(est.numerator) / Decimal(est.denominator)))}"]
    ex_d = Decimal(exact.numerator) / Decimal(exact.denominator)
    es_d = Decimal(est.numerator) / Decimal(est.denominator)
    steps.append(f"<b>Check with the exact value:</b> the calculator gives {plain(ex_d.quantize(Decimal('0.0001')))}. The estimate {plain(es_d.quantize(Decimal('0.0001')))} is close, so the working is sensible.")
    if exact != 0:
        pe = abs(float(est - exact) / float(exact)) * 100
        steps.append(f"The estimate is {pe:.1f}% away from the exact answer.")
    return _ok(steps, f"<b>Estimate &asymp; {plain(es_d.quantize(Decimal('0.0001')))}</b>")


# ------------------------------------------------------------------ errors ----
@guard
def errors(d):
    mode = d.get("mode", "err")
    if mode == "err":
        ex = D(d.get("ex"), "The exact (true) value")
        ap = D(d.get("ap"), "The approximate value")
        if ex == 0:
            raise UErr("The exact value cannot be 0 for a percentage error.")
        err = ap - ex
        steps = ["<b>Error</b> tells us how far an approximation is from the true value.",
                 f"<b>Absolute error</b> = |approximate &minus; exact| = |{plain(ap)} &minus; {plain(ex)}| = {HL(plain(abs(err)))}",
                 f"<b>Relative error</b> = absolute error &divide; exact value = {plain(abs(err))} &divide; {plain(abs(ex))} = {HL(plain((abs(err) / abs(ex)).quantize(Decimal('0.000001'))))}",
                 f"<b>Percentage error</b> = relative error &times; 100% = {HL(plain((abs(err) / abs(ex) * 100).quantize(Decimal('0.0001'))) + '%')}"]
        return _ok(steps, f"<b>Absolute error = {plain(abs(err))}; percentage error = {plain((abs(err) / abs(ex) * 100).quantize(Decimal('0.0001')))}%</b>")
    # limits
    u1 = Decimal(d.get("u1", "1"))
    x = D(d.get("x"), "The measured value")
    steps = ["<b>Limits of accuracy.</b> When a number is rounded, the true value could be a little bigger or smaller. If a value is correct to the nearest unit u, the true value is within <b>half of u</b> either side.",
             f"x = {plain(x)} to the nearest {plain(u1)}: half of {plain(u1)} = {plain(u1 / 2)}"]
    lo, hi = x - u1 / 2, x + u1 / 2
    steps.append(f"<b>Lower limit</b> = {plain(x)} &minus; {plain(u1 / 2)} = {HL(plain(lo))} &nbsp;&nbsp; <b>Upper limit</b> = {plain(x)} + {plain(u1 / 2)} = {HL(plain(hi))}")
    steps.append(f"<b>Error interval:</b> {plain(lo)} &le; x &lt; {plain(hi)} (the upper limit itself would round up, so it is not included).")
    y_txt = (d.get("y") or "").strip()
    if y_txt:
        y = D(y_txt, "The second value")
        u2 = Decimal(d.get("u2", "1"))
        lo2, hi2 = y - u2 / 2, y + u2 / 2
        steps.append(f"<b>Second value</b> y = {plain(y)} to the nearest {plain(u2)}: {plain(lo2)} &le; y &lt; {plain(hi2)}")
        op = d.get("op", "add")
        steps.append("<b>Combining:</b> to get the <b>smallest</b> result use the lowest and highest values in the way that makes it smallest; for the <b>largest</b> do the opposite. "
                     "(For subtraction and division the lower limit of the answer uses the UPPER limit of the second number.)")
        if op == "add":
            L, U, sym = lo + lo2, hi + hi2, "+"
        elif op == "sub":
            L, U, sym = lo - hi2, hi - lo2, MINUS
        elif op == "mul":
            L, U, sym = lo * lo2, hi * hi2, "&times;"
        else:
            if lo2 <= 0:
                raise UErr("The second value's lower limit is not above 0, so division is not possible.")
            L, U, sym = lo / hi2, hi / lo2, "&divide;"
        steps.append(f"Smallest x {sym} y = {plain(lo)} {sym} {plain(hi2 if op in ('sub', 'div') else lo2)} = {HL(plain(L.quantize(Decimal('0.000001'))))}")
        steps.append(f"Largest x {sym} y = {plain(hi)} {sym} {plain(lo2 if op in ('sub', 'div') else hi2)} = {HL(plain(U.quantize(Decimal('0.000001'))))}")
        return _ok(steps, f"<b>{plain(L.quantize(Decimal('0.000001')))} &le; x {sym} y &lt; {plain(U.quantize(Decimal('0.000001')))}</b>")
    return _ok(steps, f"<b>{plain(lo)} &le; x &lt; {plain(hi)}</b>")


ACC = [("1000", "nearest 1000"), ("100", "nearest 100"), ("10", "nearest 10"), ("1", "nearest whole number"), ("0.1", "nearest 0.1 (1 d.p.)"), ("0.01", "nearest 0.01 (2 d.p.)"), ("0.001", "nearest 0.001 (3 d.p.)")]

SPEC = {
    "title": "Standard Form & Approximation",
    "intro": "<b>Standard form, rounding (decimal places and significant figures), estimation, errors and limits of accuracy</b>, every step explained.",
    "tabs": [
        {"id": "ns", "label": "Standard form", "title": "Standard form (scientific notation)", "endpoint": "standard",
         "fields": [select("mode", "What do you want to do?", [("to", "write a number in standard form"), ("from", "turn standard form into a normal number"), ("calc", "calculate with standard form")], wide=True),
                    field("x", "The number", "45000", show_if={"mode": "to"}, wide=True),
                    field("a", "a (between 1 and 10)", "3.2", show_if={"mode": "from"}), field("n", "power n", "-4", show_if={"mode": "from"}),
                    field("a1", "First number: a", "3.2", show_if={"mode": "calc"}), field("n1", "First number: power", "5", show_if={"mode": "calc"}),
                    select("op", "Operation", [("mul", "multiply"), ("div", "divide"), ("add", "add"), ("sub", "subtract")], show_if={"mode": "calc"}),
                    field("a2", "Second number: a", "4.5", show_if={"mode": "calc"}), field("n2", "Second number: power", "3", show_if={"mode": "calc"})], "button": "Work it out"},
        {"id": "nr", "label": "Rounding", "title": "Round to decimal places, significant figures or the nearest 10, 100...", "endpoint": "rounding",
         "fields": [field("x", "The number", "0.004567", wide=True),
                    select("mode", "Round to", [("sf", "significant figures"), ("dp", "decimal places"), ("near", "the nearest 10, 100, 1000...")], wide=True),
                    field("n", "How many?", "2", show_if={"mode": ["sf", "dp"]}),
                    select("place", "Nearest", [("10", "10"), ("100", "100"), ("1000", "1000"), ("10000", "10 000"), ("1000000", "1 000 000")], show_if={"mode": "near"})], "button": "Round it"},
        {"id": "ne", "label": "Estimation", "title": "Estimate a calculation", "endpoint": "estimate",
         "hint": "Type the calculation with + &minus; x / and brackets. Example: 4.87 x 31.2 / 0.52",
         "fields": [field("e", "Calculation", "4.87 x 31.2 / 0.52", wide=True)], "button": "Estimate"},
        {"id": "nl", "label": "Errors and limits", "title": "Errors and limits of accuracy", "endpoint": "errors",
         "fields": [select("mode", "Find", [("err", "absolute and percentage error"), ("lim", "limits of accuracy (upper and lower bounds)")], wide=True),
                    field("ex", "Exact (true) value", "12.5", show_if={"mode": "err"}), field("ap", "Approximate value", "12", show_if={"mode": "err"}),
                    field("x", "Measured value x", "6.5", show_if={"mode": "lim"}), select("u1", "x is correct to", ACC, show_if={"mode": "lim"}),
                    field("y", "Second value y (optional, empty = skip)", "", show_if={"mode": "lim"}),
                    select("u2", "y is correct to", ACC, show_if={"mode": "lim"}),
                    select("op", "Calculate x ... y", [("add", "x + y"), ("sub", "x &minus; y"), ("mul", "x &times; y"), ("div", "x &divide; y")], show_if={"mode": "lim"})], "button": "Work it out"},
    ],
}
topics.register("numsense", SPEC, {"standard": standard, "rounding": rounding, "estimate": estimate, "errors": errors})
