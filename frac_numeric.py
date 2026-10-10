"""
Fractions topic - numbers (pure Python, no sympy).
Every solver returns {"ok", "steps", "result", "error"}.  Steps / results
are small HTML snippets (stacked fractions use the .frac CSS class).
"""
import re
from fractions import Fraction
from math import gcd, lcm, isqrt
from functools import reduce

MUL = "&times;"
DIV = "&divide;"
MINUS = "&minus;"


# ------------------------------------------------------------ plumbing -----

def _ok(steps, result):
    return {"ok": True, "steps": steps, "result": result, "error": None}


def _fail(msg):
    return {"ok": False, "steps": [], "result": None, "error": msg}


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def FR(n, d):
    return (f'<span class="frac"><span class="fn">{n}</span>'
            f'<span class="fd">{d}</span></span>')


def fr(x):
    """Fraction -> HTML (integers stay plain)."""
    x = Fraction(x)
    sign = MINUS if x < 0 else ""
    x = abs(x)
    if x.denominator == 1:
        return f"{sign}{x.numerator}"
    return f"{sign}{FR(x.numerator, x.denominator)}"


def mixed_html(x):
    x = Fraction(x)
    sign = MINUS if x < 0 else ""
    a = abs(x)
    w, r = divmod(a.numerator, a.denominator)
    if r == 0:
        return f"{sign}{w}"
    if w == 0:
        return f"{sign}{FR(r, a.denominator)}"
    return f'{sign}{w}{FR(r, a.denominator)}'


def dec_str(x, places=4):
    x = Fraction(x)
    s = f"{float(x):.{places}f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-") else "0"


def table(rows, header=None):
    h = ""
    if header:
        h = "<tr>" + "".join(f"<th>{c}</th>" for c in header) + "</tr>"
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="stat-table">{h}{body}</table>'


# ------------------------------------------------------------- parsing -----

_MIXED = re.compile(r"(-?\d+)\s+(\d+)\s*/\s*(\d+)")


def norm_text(s):
    s = str(s)
    for ch in ("‒", "–", "—", "―", "−", "‐"):
        s = s.replace(ch, "-")
    s = s.replace("×", "*").replace("÷", "/").replace("⁄", "/")
    s = re.sub(r"\bof\b", "*", s, flags=re.I)
    s = re.sub(r"(?<=[\d)])\s*[xX]\s*(?=[\d(])", "*", s)
    return s.strip()


def parse_one(tok):
    """'3/4', '2 1/3', '-5', '0.75' -> Fraction (raises ValueError)."""
    t = norm_text(tok)
    m = _MIXED.fullmatch(t)
    if m:
        w, n, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if d == 0:
            raise ValueError("A denominator cannot be zero.")
        val = Fraction(abs(w) * d + n, d)
        return -val if (w < 0 or t.startswith("-")) else val
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*/\s*(-?\d+(?:\.\d+)?)", t)
    if m:
        d = Fraction(m.group(2))
        if d == 0:
            raise ValueError("A denominator cannot be zero.")
        return Fraction(m.group(1)) / d
    m = re.fullmatch(r"-?\d+(?:\.\d+)?", t)
    if m:
        return Fraction(t)
    raise ValueError(f"I could not read &lsquo;{esc(tok)}&rsquo; as a number or fraction.")


_NUM_RE = re.compile(r"^[+-]?\d{1,15}(?:\.\d{1,10})?$")


def sfrac(v):
    """Safe number parser: plain digits / decimals only (no 1e999 style exponents,
    which could freeze the server) and a sensible size limit."""
    t = str(v).strip().replace("\u2212", "-")
    if not _NUM_RE.match(t):
        raise ValueError(f"&lsquo;{esc(t[:30])}&rsquo; is not a valid number (use plain digits, e.g. 25 or 2.5).")
    return Fraction(t)


def split_list(text):
    parts = [p.strip() for p in re.split(r"[,;\n]+", str(text)) if p.strip()]
    return parts


def has_letters(s):
    return bool(re.search(r"[A-Za-z]", re.sub(r"\bof\b", "", str(s), flags=re.I)))


# ------------------------------------------------------------- primes ------

def prime_factors(n):
    n = abs(int(n))
    out = []
    p = 2
    while p * p <= n:
        while n % p == 0:
            out.append(p)
            n //= p
        p += 1
    if n > 1:
        out.append(n)
    return out


def pf_power_str(fs):
    if not fs:
        return "1"
    cnt = {}
    for p in fs:
        cnt[p] = cnt.get(p, 0) + 1
    return f" {MUL} ".join(f"{p}<sup>{e}</sup>" if e > 1 else str(p) for p, e in sorted(cnt.items()))


def pf_counts(n):
    cnt = {}
    for p in prime_factors(n):
        cnt[p] = cnt.get(p, 0) + 1
    return cnt


def ladder_division(n):
    """repeated division text for a single number"""
    rows = []
    cur = n
    for p in prime_factors(n):
        rows.append((p, cur))
        cur //= p
    rows.append((1, cur))
    return rows


def ladder_table(n):
    rows = ladder_division(n)
    return table([[f"{p}" if p != 1 else "", c] for p, c in rows])


def _factors(n):
    out = []
    for i in range(1, isqrt(n) + 1):
        if n % i == 0:
            out.append(i)
            if i != n // i:
                out.append(n // i)
    return sorted(out)


# ---------------------------------------------------------- LCM / HCF ------

def _prime_method(nums, want):
    steps = []
    steps.append("<b>Step 1.</b> Break every number into its prime factors "
                 "(keep dividing by 2, 3, 5, 7 ... until you reach 1).")
    pcs = []
    for n in nums:
        pcs.append(pf_counts(n))
        steps.append(f"{n} = {pf_power_str(prime_factors(n))}")
    primes = sorted({p for pc in pcs for p in pc})
    res = {}
    if want in ("lcm", "both"):
        steps.append("<b>LCM:</b> pick <b>every</b> prime that appears, each with its <b>highest</b> power.")
        parts, val = [], 1
        for p in primes:
            e = max(pc.get(p, 0) for pc in pcs)
            parts.append(f"{p}<sup>{e}</sup>" if e > 1 else str(p))
            val *= p ** e
        steps.append(f"LCM = {f' {MUL} '.join(parts)} = {val}")
        res["lcm"] = val
    if want in ("hcf", "both"):
        steps.append("<b>HCF:</b> pick only the primes that appear in <b>all</b> the numbers, each with its <b>lowest</b> power.")
        common = [p for p in primes if all(pc.get(p, 0) > 0 for pc in pcs)]
        if not common:
            steps.append("There is no prime common to all of them, so HCF = 1.")
            res["hcf"] = 1
        else:
            parts, val = [], 1
            for p in common:
                e = min(pc[p] for pc in pcs)
                parts.append(f"{p}<sup>{e}</sup>" if e > 1 else str(p))
                val *= p ** e
            steps.append(f"HCF = {f' {MUL} '.join(parts)} = {val}")
            res["hcf"] = val
    return steps, res


def _division_method(nums, want):
    """ladder (short division) table"""
    steps = []
    cur = list(nums)
    rows = []
    divisors = []
    steps.append("<b>Division method (ladder):</b> write the numbers in a row. "
                 "Divide by a prime that divides <b>at least one</b> of them (write the others down unchanged). "
                 "Keep going until every number is 1.")
    while any(c != 1 for c in cur):
        p = next(q for q in range(2, max(cur) + 1)
                 if any(c % q == 0 for c in cur) and all(prime_factors(q) == [q] for _ in [0]))
        rows.append([str(p)] + [str(c) for c in cur])
        divisors.append(p)
        cur = [c // p if c % p == 0 else c for c in cur]
    rows.append([""] + [str(c) for c in cur])
    steps.append(table(rows))
    val = 1
    for p in divisors:
        val *= p
    res = {}
    if want in ("lcm", "both"):
        steps.append(f"LCM = product of the divisors on the left = {f' {MUL} '.join(map(str, divisors))} = {val}")
        res["lcm"] = val
    return steps, res


def _listing_method(nums, want):
    steps = []
    res = {}
    if want in ("lcm", "both"):
        steps.append("<b>Listing multiples:</b> write the multiples of each number until one number appears in every list.")
        big = reduce(lcm, nums)
        if big <= 2000 and len(nums) <= 4:
            lists = []
            for n in nums:
                ms = [n * k for k in range(1, big // n + 1)]
                lists.append(ms)
                shown = ", ".join(map(str, ms[:12])) + (" ..." if len(ms) > 12 else "")
                steps.append(f"Multiples of {n}: {shown}")
            steps.append(f"The first number in all the lists is <b>{big}</b>, so LCM = {big}.")
        else:
            steps.append("These numbers are too large for a neat list, so use the prime factor method above.")
        res["lcm"] = big
    if want in ("hcf", "both"):
        g = reduce(gcd, nums)
        steps.append("<b>Listing factors:</b> write all the factors of each number, then find the biggest one they share.")
        lists = [_factors(n) for n in nums]
        if max(nums) <= 5000:
            for n, fl in zip(nums, lists):
                steps.append(f"Factors of {n}: {', '.join(map(str, fl))}")
            common = sorted(set(lists[0]).intersection(*map(set, lists[1:])))
            steps.append(f"Common factors: {', '.join(map(str, common))}")
            steps.append(f"The highest common factor is <b>{g}</b>.")
        res["hcf"] = g
    return steps, res


def lcm_hcf_numbers(text, want="both", method="prime", unit=""):
    try:
        parts = split_list(text)
        if len(parts) < 2:
            return _fail("Please give at least two numbers, separated by commas (e.g. 12, 18, 30).")
        if len(parts) > 6:
            return _fail("Please use six numbers or fewer.")
        nums = []
        for p in parts:
            if not re.fullmatch(r"\d+", p.strip()):
                return _fail(f"&lsquo;{esc(p)}&rsquo; is not a positive whole number.")
            v = int(p)
            if v == 0:
                return _fail("Zero cannot be used for LCM or HCF.")
            if v > 10 ** 9:
                return _fail("Please use numbers below 1,000,000,000.")
            nums.append(v)
        steps = []
        if method == "division":
            s, res = _division_method(nums, want)
            steps += s
            if want in ("hcf", "both"):
                s2, r2 = _prime_method(nums, "hcf")
                steps.append("For the HCF, use prime factors:")
                steps += s2
                res.update(r2)
        elif method == "listing":
            s, res = _listing_method(nums, want)
            steps += s
        else:
            s, res = _prime_method(nums, want)
            steps += s
        if len(nums) == 2 and want == "both" and "lcm" in res and "hcf" in res:
            a, b = nums
            steps.append(f"<b>Check:</b> HCF {MUL} LCM = {res['hcf']} {MUL} {res['lcm']} = {res['hcf'] * res['lcm']} "
                         f"and {a} {MUL} {b} = {a * b}. They are equal, so the answers are right.")
        u = f" {esc(unit)}" if unit else ""
        out = []
        if "lcm" in res:
            out.append(f"LCM = {res['lcm']}{u}")
        if "hcf" in res:
            out.append(f"HCF = {res['hcf']}{u}")
        return _ok(steps, "<br>".join(out))
    except Exception as e:  # pragma: no cover
        return _fail(f"Something went wrong: {esc(e)}")


def lcm_hcf_fractions(text, want="both"):
    try:
        parts = split_list(text)
        if len(parts) < 2:
            return _fail("Please give at least two fractions, separated by commas (e.g. 2/3, 4/9, 5/6).")
        fs = []
        for p in parts:
            f = parse_one(p)
            if f <= 0:
                return _fail("Use positive fractions only.")
            fs.append(f)
        steps = ["First write each as a fraction in its simplest form (lowest terms):",
                 ", ".join(fr(f) for f in fs)]
        nums = [f.numerator for f in fs]
        dens = [f.denominator for f in fs]
        res = []
        if want in ("hcf", "both"):
            hn = reduce(gcd, nums)
            ld = reduce(lcm, dens)
            steps.append(f"<b>HCF of fractions</b> = {FR('HCF of the numerators', 'LCM of the denominators')}")
            steps.append(f"HCF of {', '.join(map(str, nums))} = {hn}")
            steps.append(f"LCM of {', '.join(map(str, dens))} = {ld}")
            ans = Fraction(hn, ld)
            steps.append(f"HCF = {FR(hn, ld)} = {fr(ans)}")
            res.append(f"HCF = {fr(ans)}")
        if want in ("lcm", "both"):
            ln = reduce(lcm, nums)
            hd = reduce(gcd, dens)
            steps.append(f"<b>LCM of fractions</b> = {FR('LCM of the numerators', 'HCF of the denominators')}")
            steps.append(f"LCM of {', '.join(map(str, nums))} = {ln}")
            steps.append(f"HCF of {', '.join(map(str, dens))} = {hd}")
            ans = Fraction(ln, hd)
            steps.append(f"LCM = {FR(ln, hd)} = {fr(ans)}")
            res.append(f"LCM = {fr(ans)}")
        return _ok(steps, "<br>".join(res))
    except ValueError as e:
        return _fail(str(e))


# ---------------------------------------------------------- types ----------

def fraction_types(text):
    try:
        parts = split_list(text)
        if not parts:
            return _fail("Please type a fraction, e.g. 7/3 or 2 1/3.")
        steps, out = [], []
        for p in parts[:8]:
            raw = norm_text(p)
            is_mixed = bool(_MIXED.fullmatch(raw))
            f = parse_one(p)
            a = abs(f)
            n, d = a.numerator, a.denominator
            sign = MINUS if f < 0 else ""
            steps.append(f"<b>{esc(p)}</b>")
            if f.denominator == 1 and not re.search(r"/", raw):
                steps.append(f"{esc(p)} is a whole number. As a fraction: {fr(f)}/1 (denominator 1).")
                out.append(f"{esc(p)}: whole number")
                continue
            if is_mixed:
                w, r = divmod(n, d)
                steps.append(f"It is a <b>mixed number</b> (a whole number {w} plus the proper fraction {FR(r, d)}).")
                steps.append(f"To make it an improper fraction: (whole {MUL} denominator + numerator) over the denominator")
                steps.append(f"= {FR(f'({w} {MUL} {d}) + {r}', d)} = {FR(f'{w*d} + {r}', d)} = {sign}{FR(n, d)}")
                out.append(f"{mixed_html(f)} = {sign}{FR(n, d)} (improper fraction)")
            else:
                # numerator/denominator as typed
                m = re.fullmatch(r"(-?\d+)\s*/\s*(\d+)", raw)
                tn, td = (abs(int(m.group(1))), int(m.group(2))) if m else (n, d)
                if tn < td:
                    steps.append(f"The numerator {tn} is <b>smaller</b> than the denominator {td}, so it is a <b>proper fraction</b> (less than 1).")
                    out.append(f"{FR(tn, td)}: proper fraction")
                elif tn == td:
                    steps.append(f"The numerator and denominator are equal, so it equals 1 (an improper fraction).")
                    out.append(f"{FR(tn, td)} = 1")
                else:
                    w, r = divmod(tn, td)
                    steps.append(f"The numerator {tn} is <b>bigger</b> than the denominator {td}, so it is an <b>improper fraction</b> (more than 1).")
                    if r == 0:
                        steps.append(f"Divide {tn} by {td}: {tn} &divide; {td} = {w} exactly, so it is the whole number {w}.")
                        out.append(f"{FR(tn, td)} = {sign}{w}")
                    else:
                        steps.append(f"To change to a mixed number divide {tn} by {td}: {td} goes into {tn}, {w} times, remainder {r}.")
                        steps.append(f"Whole number = {w}, new numerator = remainder {r}, denominator stays {td}.")
                        steps.append(f"{sign}{FR(tn, td)} = {sign}{w}{FR(r, td)}")
                        out.append(f"{FR(tn, td)} = {sign}{w}{FR(r, td)} (mixed number)")
                if m and Fraction(tn, td).denominator != td:
                    s = Fraction(tn, td)
                    steps.append(f"It also simplifies: {FR(tn, td)} = {fr(s)}")
            steps.append(f"As a decimal: {dec_str(f, 5)}")
        return _ok(steps, "<br>".join(out))
    except ValueError as e:
        return _fail(str(e))


# --------------------------------------------------------- simplify --------

def simplify_fraction(text):
    try:
        raw = norm_text(text)
        m = re.fullmatch(r"(-?\d+)\s*/\s*(-?\d+)", raw)
        if not m:
            return _fail("Type a fraction like 18/24.")
        n, d = int(m.group(1)), int(m.group(2))
        if d == 0:
            return _fail("A denominator cannot be zero.")
        g = gcd(abs(n), abs(d))
        sign = -1 if (n < 0) != (d < 0) else 1
        steps = [f"To simplify {FR(n, d)} we divide the top and bottom by their <b>HCF</b>."]
        if n == 0:
            return _ok(steps + ["The numerator is 0."], "0")
        if max(abs(n), abs(d)) <= 10 ** 7:
            steps.append(f"Factors of {abs(n)}: " + ", ".join(map(str, _factors(abs(n)))))
            steps.append(f"Factors of {abs(d)}: " + ", ".join(map(str, _factors(abs(d)))))
        else:
            steps.append("(The numbers are large, so the HCF is found with the Euclidean method instead of listing factors.)")
        steps.append(f"The highest common factor is <b>{g}</b>.")
        if g == 1:
            steps.append("The HCF is 1, so the fraction is already in its simplest form.")
        else:
            steps.append(f"Divide top and bottom by {g}: {FR(f'{abs(n)} {DIV} {g}', f'{abs(d)} {DIV} {g}')} = {FR(abs(n)//g, abs(d)//g)}")
        res = Fraction(sign * abs(n), abs(d))
        return _ok(steps, fr(res))
    except ValueError as e:
        return _fail(str(e))


# --------------------------------------------------- numeric expression ----

class _NumErr(Exception):
    pass


def _tokens(s):
    s = norm_text(s)
    s = _MIXED.sub(lambda m: f"MIX{m.group(1)}_{m.group(2)}_{m.group(3)}", s)
    toks = []
    pos = 0
    pat = re.compile(r"\s*(MIX-?\d+_\d+_\d+|\d+\s*/\s*\d+|\d+\.\d+|\d+|[-+*/()])")
    while pos < len(s):
        m = pat.match(s, pos)
        if not m:
            if s[pos:].strip() == "":
                break
            raise _NumErr(f"I could not understand &lsquo;{esc(s[pos:].strip()[0])}&rsquo;.")
        toks.append(m.group(1))
        pos = m.end()
    return toks


def _narrate_add(a, b, sub, steps):
    sym = MINUS if sub else "+"
    bb = -b if sub else b
    da, db = a.denominator, b.denominator
    if da == db:
        if da == 1:
            steps.append(f"{fr(a)} {sym} {fr(b)} = {fr(a + bb)}")
            return a + bb
        steps.append(f"The denominators are the same ({da}), so just {'subtract' if sub else 'add'} the numerators: "
                     f"{FR(a.numerator, da)} {sym} {FR(b.numerator, db)} = {FR(f'{a.numerator} {sym} {b.numerator}', da)} = {fr(a + bb)}")
        return a + bb
    L = lcm(da, db)
    ma, mb = L // da, L // db
    steps.append(f"The denominators are different ({da} and {db}). The LCM of {da} and {db} is <b>{L}</b>, so use {L} as the common denominator.")
    steps.append(f"{fr(a)} = {FR(f'{a.numerator} {MUL} {ma}', f'{da} {MUL} {ma}')} = {FR(a.numerator * ma, L)}"
                 f" &nbsp;and&nbsp; {fr(b)} = {FR(f'{b.numerator} {MUL} {mb}', f'{db} {MUL} {mb}')} = {FR(b.numerator * mb, L)}")
    tot = a.numerator * ma + (-b.numerator * mb if sub else b.numerator * mb)
    steps.append(f"{FR(a.numerator * ma, L)} {sym} {FR(b.numerator * mb, L)} = {FR(f'{a.numerator * ma} {sym} {b.numerator * mb}', L)} = {FR(tot, L)}")
    res = a + bb
    if res.denominator != L and tot != 0:
        g = gcd(abs(tot), L)
        steps.append(f"Simplify: divide top and bottom by {g}: {FR(tot, L)} = {fr(res)}")
    return res


def _narrate_mul(a, b, steps):
    an, ad, bn, bd = abs(a.numerator), a.denominator, abs(b.numerator), b.denominator
    sign = -1 if (a < 0) != (b < 0) else 1
    if a == 0 or b == 0:
        steps.append(f"{fr(a)} {MUL} {fr(b)} = 0")
        return Fraction(0)
    g1, g2 = gcd(an, bd), gcd(bn, ad)
    steps.append(f"Multiply: {fr(a)} {MUL} {fr(b)} = {FR(f'{an} {MUL} {bn}', f'{ad} {MUL} {bd}')}")
    if g1 > 1 or g2 > 1:
        cn1, cd2, cn2, cd1 = an // g1, bd // g1, bn // g2, ad // g2
        steps.append(f"Cancel common factors before multiplying (divide a top and a bottom by the same number): "
                     f"{FR(f'{cn1} {MUL} {cn2}', f'{cd1} {MUL} {cd2}')}")
    res = Fraction(sign * an * bn, ad * bd)
    steps.append(f"= {fr(res)}")
    return res


def _narrate_div(a, b, steps):
    if b == 0:
        raise _NumErr("You cannot divide by zero.")
    inv = Fraction(b.denominator, b.numerator)
    steps.append(f"To divide by a fraction, change {DIV} to {MUL} and turn the second fraction upside down: "
                 f"{fr(a)} {DIV} {fr(b)} = {fr(a)} {MUL} {fr(inv)}")
    return _narrate_mul(a, inv, steps)


def numeric_expression(text):
    try:
        toks = _tokens(text)
        if not toks:
            return _fail("Please type a fraction sum, e.g. 2 1/3 + 3/4.")
        pos = [0]
        steps = []

        def peek():
            return toks[pos[0]] if pos[0] < len(toks) else None

        def eat():
            t = toks[pos[0]]
            pos[0] += 1
            return t

        def expr():
            v = term()
            while peek() in ("+", "-"):
                op = eat()
                w = term()
                steps.append(f"<b>{fr(v)} {'+' if op == '+' else MINUS} {fr(w)}</b>")
                v = _narrate_add(v, w, op == "-", steps)
            return v

        def term():
            v = unary()
            while peek() in ("*", "/"):
                op = eat()
                w = unary()
                steps.append(f"<b>{fr(v)} {MUL if op == '*' else DIV} {fr(w)}</b>")
                v = _narrate_mul(v, w, steps) if op == "*" else _narrate_div(v, w, steps)
            return v

        def unary():
            if peek() == "-":
                eat()
                return -unary()
            return atom()

        def atom():
            t = peek()
            if t is None:
                raise _NumErr("The sum ends too early.")
            if t == "(":
                eat()
                steps.append("<i>Brackets first:</i>")
                v = expr()
                if peek() != ")":
                    raise _NumErr("A bracket is not closed.")
                eat()
                steps.append(f"<i>The bracket equals {fr(v)}</i>")
                return v
            eat()
            if re.fullmatch(r"\d+\s*/\s*\d+", t):
                a_, b_ = [int(z) for z in t.split("/")]
                if b_ == 0:
                    raise _NumErr("A denominator cannot be zero.")
                return Fraction(a_, b_)
            if t.startswith("MIX"):
                w, n, d = t[3:].split("_")
                val = parse_one(f"{w} {n}/{d}")
                steps.append(f"Change the mixed number {mixed_html(val)} to an improper fraction: "
                             f"{FR(f'({abs(int(w))} {MUL} {d}) + {n}', d)} = {fr(val)}")
                return val
            if re.fullmatch(r"\d+\.\d+", t):
                val = Fraction(t)
                steps.append(f"Change the decimal {t} to a fraction: {fr(val)}")
                return val
            return Fraction(int(t))

        # show the numbers as typed first
        v = expr()
        if pos[0] != len(toks):
            raise _NumErr("I could not understand that sum - check the signs and brackets.")
        steps.append("<b>Final answer:</b> " + (fr(v) if v.denominator == 1 else
                     f"{fr(v)}" + (f" = {mixed_html(v)}" if abs(v) > 1 else "")))
        res = fr(v)
        if v.denominator != 1 and abs(v) > 1:
            res += f" = {mixed_html(v)}"
        res += f" (decimal: {dec_str(v)})" if v.denominator != 1 else ""
        return _ok(steps, res)
    except (_NumErr, ValueError) as e:
        return _fail(str(e))


# ----------------------------------------------------------- compare -------

def compare_fractions(text, order="ascending"):
    try:
        parts = split_list(text)
        if len(parts) < 2:
            return _fail("Please give at least two fractions, separated by commas (e.g. 3/4, 2/3, 5/6).")
        fs = [(p, parse_one(p)) for p in parts[:8]]
        dens = [f.denominator for _, f in fs]
        L = reduce(lcm, dens)
        steps = [f"To compare fractions, give them the same denominator. The LCM of the denominators "
                 f"({', '.join(map(str, dens))}) is <b>{L}</b>."]
        conv = []
        for p, f in fs:
            k = L // f.denominator
            steps.append(f"{fr(f)} = {FR(f'{f.numerator} {MUL} {k}', f'{f.denominator} {MUL} {k}')} = {FR(f.numerator * k, L)}")
            conv.append((f.numerator * k, f, p))
        steps.append(f"Now compare the numerators: {', '.join(str(c[0]) for c in conv)}")
        rev = order == "descending"
        srt = sorted(conv, key=lambda c: c[0], reverse=rev)
        steps.append(f"Arranged in {'descending (biggest first)' if rev else 'ascending (smallest first)'} order of the numerators.")
        sep = " &gt; " if rev else " &lt; "
        res = sep.join(fr(c[1]) for c in srt)
        steps.append("Decimals as a check: " + ", ".join(f"{fr(c[1])} = {dec_str(c[1], 4)}" for c in srt))
        return _ok(steps, res)
    except ValueError as e:
        return _fail(str(e))


# ----------------------------------------------------------- convert -------

def _long_division(n, d, max_digits=40):
    """digits after decimal point, with detection of recurring part"""
    whole, r = divmod(n, d)
    seen = {}
    digits = []
    while r != 0 and r not in seen and len(digits) < max_digits:
        seen[r] = len(digits)
        r *= 10
        digits.append(r // d)
        r %= d
    if r == 0:
        return whole, digits, None
    start = seen[r]
    return whole, digits[:start], digits[start:]


def _dec_text(whole, nonrep, rep):
    s = str(whole)
    if nonrep or rep:
        s += "."
        s += "".join(map(str, nonrep))
        if rep:
            s += "(" + "".join(map(str, rep)) + ")"
    return s


def fraction_to_decimal(text):
    try:
        f = parse_one(text)
        a = abs(f)
        sign = "-" if f < 0 else ""
        whole, nonrep, rep = _long_division(a.numerator, a.denominator)
        steps = [f"A fraction means 'top &divide; bottom': {FR(a.numerator, a.denominator)} = {a.numerator} &divide; {a.denominator}"]
        steps.append(f"Divide {a.numerator} by {a.denominator} using long division (add zeros after the decimal point).")
        if rep is None:
            steps.append("The division ends (remainder 0), so this is a terminating decimal.")
            txt = sign + _dec_text(whole, nonrep, None)
        else:
            steps.append("The remainders repeat, so the digits repeat forever: a <b>recurring decimal</b>. "
                         "A dot (or bar) is written over the repeating digits - here shown in brackets.")
            txt = sign + _dec_text(whole, nonrep, rep)
        steps.append(f"{fr(f)} = {txt}")
        steps.append(f"As a percentage: {fr(f)} {MUL} 100% = {dec_str(f * 100, 4)}%")
        return _ok(steps, f"{fr(f)} = {txt}")
    except ValueError as e:
        return _fail(str(e))


def decimal_to_fraction(text):
    try:
        t = norm_text(text).replace(" ", "")
        m = re.fullmatch(r"(-?)(\d*)\.?(\d*)(?:\((\d+)\))?", t)
        if not m or not (m.group(2) or m.group(3) or m.group(4)):
            return _fail("Type a decimal like 0.375 or a recurring one like 0.(3) or 0.1(6) "
                         "(put the repeating digits in brackets).")
        sign = -1 if m.group(1) else 1
        ip, nr, rp = m.group(2) or "0", m.group(3) or "", m.group(4) or ""
        steps = []
        if not rp:
            k = len(nr)
            num = int(ip + nr)
            den = 10 ** k
            steps.append(f"{t} has {k} digit{'s' if k != 1 else ''} after the decimal point, so write it over 1 followed by {k} zero{'s' if k != 1 else ''}:")
            steps.append(f"{t} = {FR(num, den)}")
            res = Fraction(sign * num, den)
            g = gcd(num, den)
            if g > 1:
                steps.append(f"Simplify by dividing top and bottom by their HCF, {g}: {fr(res)}")
        else:
            m_, r_ = len(nr), len(rp)
            steps.append(f"This is a recurring decimal. Let <b>x</b> = {t.lstrip('-')} (the repeating digits are {rp}).")
            A = int(ip + nr + rp)
            B = int(ip + nr) if (ip + nr) else 0
            steps.append(f"Multiply by 10<sup>{m_ + r_}</sup> so one full set of repeating digits moves in front of the point: {10 ** (m_ + r_)}x = {A}.({rp}...)")
            if m_:
                steps.append(f"Multiply by 10<sup>{m_}</sup> to line the repeats up: {10 ** m_}x = {B}.({rp}...)")
            else:
                steps.append(f"Also x = {B}.({rp}...)")
            steps.append(f"Subtract the two lines (the repeating parts cancel): {10 ** (m_ + r_) - 10 ** m_}x = {A - B}")
            num, den = A - B, 10 ** (m_ + r_) - 10 ** m_
            res = Fraction(sign * num, den)
            steps.append(f"x = {FR(num, den)} = {fr(res)}")
        steps.append(f"Check as mixed number: {mixed_html(res)}" if abs(res) > 1 else "")
        steps = [s for s in steps if s]
        return _ok(steps, fr(res))
    except ValueError as e:
        return _fail(str(e))


def fraction_to_percent(text):
    try:
        f = parse_one(text)
        steps = [f"To change a fraction to a percentage, multiply by 100%.",
                 f"{fr(f)} {MUL} 100% = {FR(f'{f.numerator} {MUL} 100', f.denominator)}% = {dec_str(f * 100, 4)}%"]
        return _ok(steps, f"{dec_str(f * 100, 4)}%")
    except ValueError as e:
        return _fail(str(e))


def percent_to_fraction(text):
    try:
        t = norm_text(text).replace("%", "").strip()
        v = sfrac(t)
        steps = [f"'Per cent' means 'out of 100'. So {t}% = {FR(t, 100)}"]
        res = v / 100
        steps.append(f"Simplify: {fr(res)}")
        return _ok(steps, fr(res))
    except (ValueError, ZeroDivisionError):
        return _fail("Type a percentage like 35 or 12.5.")


# -------------------------------------------------------------- word -------

def _frac_arg(s, label):
    try:
        v = parse_one(s)
    except ValueError:
        raise ValueError(f"Please type {label} as a fraction like 3/5.")
    return v


def fraction_word(kind, **kw):
    try:
        if kind == "of":
            f = _frac_arg(kw.get("fraction", ""), "the fraction")
            q = sfrac(str(kw.get("quantity", "")).replace(",", ""))
            res = f * q
            steps = [f"'of' means multiply: {fr(f)} of {dec_str(q)} = {fr(f)} {MUL} {dec_str(q)}",
                     f"= {FR(f'{f.numerator} {MUL} {dec_str(q)}', f.denominator)} = {dec_str(res)}",
                     "(Tip: divide the quantity by the denominator first, then multiply by the numerator.)",
                     f"{dec_str(q)} {DIV} {f.denominator} = {dec_str(q / f.denominator)}, then {MUL} {f.numerator} = {dec_str(res)}"]
            return _ok(steps, dec_str(res))
        if kind == "express":
            a = sfrac(str(kw.get("a", "")).replace(",", ""))
            b = sfrac(str(kw.get("b", "")).replace(",", ""))
            if b == 0:
                return _fail("The total cannot be zero.")
            res = a / b
            steps = [f"'Express {dec_str(a)} as a fraction of {dec_str(b)}' means {dec_str(a)} out of {dec_str(b)}: {FR(dec_str(a), dec_str(b))}",
                     f"Simplify: {fr(res)}",
                     f"As a percentage: {fr(res)} {MUL} 100% = {dec_str(res * 100, 4)}%"]
            return _ok(steps, f"{fr(res)} ({dec_str(res * 100, 4)}%)")
        if kind == "whole":
            f = _frac_arg(kw.get("fraction", ""), "the fraction")
            part = sfrac(str(kw.get("part", "")).replace(",", ""))
            if f == 0:
                return _fail("The fraction cannot be zero.")
            whole = part / f
            steps = [f"Let the whole number be <b>N</b>. Then {fr(f)} {MUL} N = {dec_str(part)}.",
                     f"To find N, divide {dec_str(part)} by {fr(f)}: N = {dec_str(part)} {DIV} {fr(f)}",
                     f"= {dec_str(part)} {MUL} {fr(1 / f)} = {dec_str(whole)}",
                     f"<b>Check:</b> {fr(f)} of {dec_str(whole)} = {dec_str(f * whole)} &#10003;"]
            return _ok(steps, dec_str(whole))
        if kind == "remainder":
            total = sfrac(str(kw.get("total", "")).replace(",", ""))
            fl = [_frac_arg(x, "each fraction") for x in split_list(kw.get("fractions", ""))]
            if not fl:
                return _fail("Please give at least one fraction (e.g. 1/4, 1/3).")
            of_rem = str(kw.get("basis", "remainder")) != "original"
            steps = [f"Start with {dec_str(total)}."]
            left = total
            for i, f in enumerate(fl, 1):
                base = left if of_rem else total
                spent = f * base
                steps.append(f"Part {i}: {fr(f)} of {dec_str(base)} = {dec_str(spent)}")
                left -= spent
                steps.append(f"Remaining = {dec_str(left + spent)} {MINUS} {dec_str(spent)} = {dec_str(left)}")
            if left < 0:
                return _fail("The fractions add up to more than the whole - please check them.")
            return _ok(steps, f"Left over: {dec_str(left)} ({fr(left / total)} of the original)" if total else dec_str(left))
        if kind == "change":
            f = _frac_arg(kw.get("fraction", ""), "the fraction")
            q = sfrac(str(kw.get("quantity", "")).replace(",", ""))
            inc = str(kw.get("direction", "increase")) != "decrease"
            mult = 1 + f if inc else 1 - f
            steps = [f"{'Increasing' if inc else 'Decreasing'} by {fr(f)} means the new value is {fr(mult)} of the old one "
                     f"(1 {'+' if inc else MINUS} {fr(f)} = {fr(mult)}).",
                     f"New value = {fr(mult)} {MUL} {dec_str(q)} = {dec_str(mult * q)}"]
            return _ok(steps, dec_str(mult * q))
        return _fail("Unknown fraction word-problem type.")
    except (ValueError, ZeroDivisionError) as e:
        return _fail(str(e) or "Please check the numbers you typed.")
