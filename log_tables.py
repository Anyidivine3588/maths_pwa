"""Log-table method (WAEC/NECO): characteristic, mantissa, bar notation, antilog,
and calculating with logs. Pure Python."""
import math
import re
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from log_core import LogErr, parse, fmtq
from log_solvers import _ok, _fail, guard, HL

BAR = "&#772;"
MINUS = "&minus;"


def _lt(x, d=4):
    return Fraction(round(x * 10 ** d), 10 ** d)


def barfmt(L):
    """L is a Fraction with at most 4 dp, e.g. -2.4559 -> 3-bar.4559"""
    c = math.floor(L)
    m = L - c
    digits = f"{int(m * 10000):04d}"
    if c < 0:
        return f"{abs(c)}{BAR}.{digits}"
    return f"{c}.{digits}"


def plain(L):
    s = f"{abs(float(L)):.4f}"
    return (MINUS if L < 0 else "") + s


def sci(dec):
    """Decimal > 0 -> (A, c) with 1 <= A < 10"""
    t = dec.as_tuple()
    digits = "".join(map(str, t.digits)).lstrip("0")
    if not digits:
        raise LogErr("Logarithms are only defined for positive numbers.")
    # position of the first non-zero digit
    full = "".join(map(str, t.digits))
    lead = len(full) - len(full.lstrip("0"))
    c = len(full) + t.exponent - 1 - lead
    A = Decimal(digits[0] + "." + (digits[1:] or "0"))
    return A, c


def _dec(text, what="the number"):
    text = (text or "").strip().replace(",", "").replace(" ", "")
    if not text:
        raise LogErr(f"Please type {what}.")
    try:
        d = Decimal(text)
    except InvalidOperation:
        raise LogErr(f"I could not read '{text}' as a number. Type something like <b>587</b> or <b>0.00342</b>.")
    if d <= 0:
        raise LogErr("Logarithms are only defined for <b>positive</b> numbers (you cannot take the log of zero or a negative number).")
    return d


def _count_word(c):
    if c >= 0:
        return f"{c + 1} digit{'s' if c + 1 != 1 else ''} before the decimal point"
    return f"{abs(c) - 1} zero{'s' if abs(c) - 1 != 1 else ''} right after the decimal point"


def _char_steps(num_txt, A, c, steps):
    Atxt = f"{A.normalize():f}" if A != A.to_integral() else str(int(A))
    steps.append(f"<b>Step 1 &ndash; standard form:</b> move the decimal point until there is exactly one non-zero digit in front of it. "
                 f"{num_txt} = {HL(Atxt + ' &times; 10<sup>' + (str(c) if c >= 0 else MINUS + str(abs(c))) + '</sup>')}")
    if c >= 0:
        steps.append(f"<b>Step 2 &ndash; characteristic</b> = the power of 10 = <b>{c}</b>. "
                     f"(Quick check: the number has {_count_word(c)}, and the characteristic is one less than that count of digits.)")
    else:
        steps.append(f"<b>Step 2 &ndash; characteristic</b> = the power of 10 = <b>{MINUS}{abs(c)}</b>. "
                     f"The number is less than 1 (it has {_count_word(c)}), so the characteristic is negative. "
                     f"We write it as <b>{abs(c)}{BAR}</b> (say &ldquo;bar {abs(c)}&rdquo;): the minus sign sits over the {abs(c)} "
                     f"because <i>only the characteristic is negative &ndash; the mantissa stays positive</i>.")


def _mantissa_steps(A, steps):
    a4 = A.quantize(Decimal("0.001")) if len(str(A).replace(".", "")) > 4 else A
    sf = f"{float(A):.3f}".rstrip("0").rstrip(".") if A != A.to_integral() else str(int(A))
    # round to 4 s.f. as the table does
    A4 = float(f"{float(A):.3f}")
    m = _lt(math.log10(A4))
    base3 = float(f"{A4:.2f}")
    m3 = _lt(math.log10(base3))
    row = int(round(base3 * 10))
    col_digit = int(round(A4 * 100)) % 10
    diff_digit = int(round(A4 * 1000)) % 10
    first2 = int(A4 * 10)
    third = int(round(A4 * 100)) % 10
    desc = (f"<b>Step 3 &ndash; mantissa</b> from the 4-figure log table (round the number to 4 significant figures first: {A4:g}). "
            f"Look down the left-hand column to <b>{first2}</b>, then across to column <b>{third}</b>: that gives {float(m3):.4f}"
            )
    if diff_digit:
        dd = int(round((m - m3) * 10000))
        desc += f". Now move along to the <i>mean-difference</i> column <b>{diff_digit}</b>, which adds <b>{dd}</b> (in the last place): "
        desc += f"{float(m3):.4f} + 0.{dd:04d} = {float(m):.4f}"
    desc += f".<br>So the mantissa = <b>{float(m):.4f}</b> (it is always between 0 and 1)."
    steps.append(desc)
    return m


@guard
def tables(number_str):
    d = _dec(number_str)
    A, c = sci(d)
    steps = []
    num_txt = number_str.strip().replace(",", "")
    _char_steps(num_txt, A, c, steps)
    m = _mantissa_steps(A, steps)
    L = c + m
    steps.append(f"<b>Step 4 &ndash; join them:</b> log {num_txt} = characteristic + mantissa = {c if c >= 0 else MINUS + str(abs(c))} + {float(m):.4f}")
    if c < 0:
        steps.append(f"In bar form this is {HL(barfmt(L))}. As an ordinary decimal it is {MINUS}{abs(c)} + {float(m):.4f} = {plain(L)}.")
        return _ok(steps, f"log {num_txt} = {barfmt(L)} &nbsp;(= {plain(L)})")
    return _ok(steps, f"log {num_txt} = {barfmt(L)}")


_BAR_PATTERNS = [
    re.compile(r"^bar\s*\(?(\d+)\)?\s*\.\s*(\d+)$"),
    re.compile(r"^(\d+)\s*(?:-?bar|̄|̅|~|_)\s*\.\s*(\d+)$"),
    re.compile(r"^(\d+)\s*\.\s*(\d+)\s*bar$"),
]


def _read_log_value(text):
    t = (text or "").strip().lower().replace("−", "-").replace("&#772;", "̄").replace("-bar", "bar")
    if not t:
        raise LogErr("Please type the logarithm value, like <b>2.7686</b> or <b>3&#772;.5441</b> (you can type <b>bar3.5441</b>).")
    t = t.replace("̄", "bar").replace("bar", "bar ") if "̄" in t else t
    t = re.sub(r"\s+", " ", t)
    m = re.match(r"^bar ?\(?(\d+)\)?\s*\.\s*(\d+)$", t) or re.match(r"^(\d+)\s*bar\s*\.\s*(\d+)$", t)
    if m:
        c = -int(m.group(1))
        mant = Fraction("0." + m.group(2))
        return c, mant, True
    m = re.match(r"^(-?)\s*(\d+)\s*\+\s*(0?\.\d+)$", t)
    try:
        v = Fraction(Decimal(t.replace(" ", "")))
    except InvalidOperation:
        raise LogErr(f"I could not read '{text}'. Type a decimal like <b>2.7686</b> or <b>&minus;2.4559</b>, or bar form like <b>bar3.5441</b>.")
    c = math.floor(v)
    return c, v - c, False


def _place(A, c):
    """A (Decimal, 4 s.f.) x 10^c as plain text"""
    d = A.scaleb(c)
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


@guard
def antilog(value_str):
    c, mant, was_bar = _read_log_value(value_str)
    steps = []
    if was_bar:
        steps.append(f"You gave bar form: characteristic = {MINUS}{abs(c)}, mantissa = {float(mant):.4f}.")
    else:
        v = c + mant
        steps.append(f"Split the log into a whole part and a decimal part: {fmtq(v) if False else str(float(v))}")
        if c < 0:
            steps[-1] = (f"The log is negative ({str(float(v))}), but the <b>mantissa must be positive</b>. "
                         f"Add enough to reach the next whole number below: {str(float(v))} = {MINUS}{abs(c)} + {float(mant):.4f}, which is {abs(c)}{BAR}.{int(mant * 10000):04d} in bar form.")
        else:
            steps[-1] = f"Split the log into characteristic (whole part) and mantissa (decimal part): {float(v)} = <b>{c}</b> + <b>{float(mant):.4f}</b>."
    m4 = float(mant)
    A = round(10 ** m4, 3)
    Ad = Decimal(f"{A:.3f}")
    steps.append(f"<b>Antilog of the mantissa</b> (use the antilog table: row = first two decimals, column = third decimal, then add the mean difference for the fourth): "
                 f"antilog {m4:.4f} = <b>{A:.3f}</b>")
    steps.append(f"<b>Place the decimal point using the characteristic ({c if c >= 0 else MINUS + str(abs(c))}):</b> "
                 f"{A:.3f} &times; 10<sup>{c if c >= 0 else MINUS + str(abs(c))}</sup>" + (f" &nbsp; (move the point {c} place{'s' if abs(c) != 1 else ''} to the right)" if c > 0 else
                  f" &nbsp; (move the point {abs(c)} place{'s' if abs(c) != 1 else ''} to the left)" if c < 0 else " &nbsp; (no movement)"))
    ans = _place(Ad, c)
    steps.append(f"Answer: {HL(ans)}  (to 4 significant figures)")
    return _ok(steps, ans)


def _collect(node, sign, power, out):
    """flatten product/quotient/power/root of plain numbers into (number, exponent Fraction)"""
    k = node[0]
    if k == "num":
        if node[1] <= 0:
            raise LogErr("Every number must be positive to use log tables.")
        out.append((node[1], sign * power))
    elif k == "mul":
        _collect(node[1], sign, power, out); _collect(node[2], sign, power, out)
    elif k == "div":
        _collect(node[1], sign, power, out); _collect(node[2], -sign, power, out)
    elif k == "sqrt":
        _collect(node[1], sign, power / 2, out)
    elif k == "pow":
        e = node[2]
        if e[0] == "neg" and e[1][0] == "num":
            ev = -e[1][1]
        elif e[0] == "num":
            ev = e[1]
        elif e[0] == "div" and e[1][0] == "num" and e[2][0] == "num":
            ev = e[1][1] / e[2][1]
        else:
            raise LogErr("The power must be a plain number like 3 or 1/3.")
        _collect(node[1], sign, power * ev, out)
    elif k == "neg":
        raise LogErr("Every number must be positive to use log tables.")
    else:
        raise LogErr("Log tables are used for multiplying, dividing, powers and roots of numbers, e.g. <b>587 &times; 0.0342</b> or <b>(2.35)^3</b>. Adding and subtracting are not done with logs.")


def _num_txt(q):
    return fmtq(q) if q.denominator == 1 else str(float(q))


@guard
def calculate(expr):
    if not (expr or "").strip():
        raise LogErr("Type a calculation like <b>587 * 0.0342</b>, <b>45.6 / 2.37</b>, <b>2.35^3</b> or <b>sqrt(587)</b>.")
    node = parse(expr)
    if node[0] == "num":
        raise LogErr("Type a calculation (with *, /, ^ or sqrt), not just a number.")
    items = []
    _collect(node, 1, Fraction(1), items)
    steps = ["<b>Plan:</b> multiplying adds logs, dividing subtracts logs, a power multiplies the log, a root divides the log. "
             "So we find the log of every number, do the easy arithmetic on the logs, then take the antilog."]
    rows = []
    total = Fraction(0)
    detail = []
    for q, e in items:
        d = Decimal(str(float(q))) if q.denominator != 1 else Decimal(int(q))
        A, c = sci(d)
        A4 = float(f"{float(A):.3f}")
        m = _lt(math.log10(A4))
        L = c + m
        rows.append((_num_txt(q), barfmt(L), e))
    tab = "<table class='stat-table'><tr><th>Number</th><th>Its log</th><th>Used as</th></tr>"
    for (nt, lt, e), (q, ee) in zip(rows, items):
        role = "add" if ee == 1 else "subtract" if ee == -1 else f"multiply log by {fmtq(ee)}" if ee > 0 else f"subtract (log &times; {fmtq(-ee)})"
        tab += f"<tr><td>{nt}</td><td>{lt}</td><td>{role}</td></tr>"
    tab += "</table>"
    steps.append("<b>Step 1 &ndash; find each log from the table</b> (characteristic from the standard form, mantissa from the table):")
    steps.append(tab)
    # arithmetic
    terms = []
    for (q, ee), (_, lt, _) in zip(items, rows):
        d = Decimal(str(float(q))) if q.denominator != 1 else Decimal(int(q))
        A, c = sci(d)
        L = c + _lt(math.log10(float(f"{float(A):.3f}")))
        terms.append((L, ee))
    total = sum(L * ee for L, ee in terms)
    txt = []
    for i, (L, ee) in enumerate(terms):
        t = barfmt(L)
        if ee not in (1, -1):
            t = f"{fmtq(abs(ee))} &times; {t}"
        if i == 0:
            txt.append(("" if ee > 0 else MINUS) + t)
        else:
            txt.append(("+ " if ee > 0 else MINUS + " ") + t)
    steps.append("<b>Step 2 &ndash; do the arithmetic on the logs</b> (treat each bar log as its negative characteristic plus the positive mantissa):<br>"
                 + " ".join(txt) + f" = {HL(plain(total) if total < 0 else plain(total))}")
    total = _lt(float(total))
    c = math.floor(total)
    m = total - c
    steps.append(f"Write the result with a positive mantissa: {plain(total)} = {barfmt(total)}" if total < 0 else f"The log of the answer is {barfmt(total)}.")
    # ready-made antilog
    r = antilog(str(float(total)))
    steps.append("<b>Step 3 &ndash; antilog</b> to get the answer:")
    steps.extend(r["steps"][1:] if r["ok"] else [])
    if not r["ok"]:
        raise LogErr("Could not finish the antilog.")
    exact = float(1)
    try:
        import operator
        val = 1.0
        for q, ee in items:
            val *= float(q) ** float(ee)
        steps.append(f"<b>Check with a calculator:</b> {val:.4g}. The table answer is close (tables are only accurate to about 4 figures).")
    except Exception:
        pass
    return _ok(steps, f"{r['result']}")
