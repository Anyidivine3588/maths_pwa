"""Percentages, ratio & proportion, profit/loss, interest, rounding & standard form."""
import math
import re
from fractions import Fraction
import topics
from tcommon import *
from frac_numeric import _ok, _fail

K = lambda kind: {"kind": kind}


def P(x):
    return fm(x, 4) + "%"


# ============================================================ percentages ===

@guard
def percentages(d):
    kind = d.get("kind", "of")
    steps = []
    if kind == "of":
        p, n = num(d.get("p"), "the percentage"), num(d.get("n"), "the amount")
        steps.append(f"<b>Step 1.</b> 'Percent' means 'out of 100'. So {fm(p)}% = {FR(fm(p), 100)}.")
        steps.append(f"<b>Step 2.</b> 'Of' means multiply: {FR(fm(p), 100)} {TIMES} {fm(n)}")
        r = p / 100 * n
        steps.append(f"<b>Step 3.</b> Work it out: ({fm(p)} {TIMES} {fm(n)}) {DIVIDE} 100 = {fm(p * n)} {DIVIDE} 100 = <span class='hl'>{fm(r, 4)}</span>")
        return _ok(steps, f"<b>{fm(p)}% of {fm(n)} = {fm(r, 4)}</b>")
    if kind == "whatpct":
        a, b = num(d.get("a"), "the part"), pos(d.get("b"), "the whole")
        steps.append(f"<b>Step 1.</b> To write A as a percentage of B, make a fraction {FR('A', 'B')} and multiply by 100.")
        steps.append(f"<b>Step 2.</b> {FR(fm(a), fm(b))} {TIMES} 100")
        r = a / b * 100
        steps.append(f"<b>Step 3.</b> = {fm(a * 100)} {DIVIDE} {fm(b)} = <span class='hl'>{fm(r, 4)}%</span>")
        return _ok(steps, f"<b>{fm(a)} is {fm(r, 4)}% of {fm(b)}</b>")
    if kind == "incdec":
        n, p = num(d.get("n"), "the amount"), num(d.get("p"), "the percentage")
        up = d.get("dir", "inc") == "inc"
        mult = 1 + p / 100 if up else 1 - p / 100
        if mult < 0:
            raise UErr("A decrease of more than 100% would give a negative amount.")
        steps.append(f"<b>Step 1 - Multiplier method.</b> {'Increasing' if up else 'Decreasing'} by {fm(p)}% means you "
                     f"{'have' if up else 'keep'} {FR(fm(100 + p) if up else fm(100 - p), 100)} of the original. "
                     f"Multiplier = {fm(mult, 6)}.")
        r = n * mult
        steps.append(f"<b>Step 2.</b> New amount = {fm(n)} {TIMES} {fm(mult, 6)} = <span class='hl'>{fm(r, 4)}</span>")
        chg = n * p / 100
        steps.append(f"<b>Check (other way).</b> {fm(p)}% of {fm(n)} = {fm(chg, 4)}; {fm(n)} {'+' if up else MINUS} {fm(chg, 4)} = {fm(r, 4)}.")
        return _ok(steps, f"<b>New amount = {fm(r, 4)}</b>")
    if kind == "change":
        old, new = pos(d.get("old"), "the old value"), num(d.get("new"), "the new value")
        diff = new - old
        word = "increase" if diff >= 0 else "decrease"
        steps.append(f"<b>Step 1.</b> Find the change: new &minus; old = {fm(new)} &minus; {fm(old)} = {fm(diff, 4)}")
        steps.append(f"<b>Step 2.</b> Percentage change = {FR('change', 'ORIGINAL')} {TIMES} 100 (always divide by the <b>original</b>, the old value).")
        r = diff / old * 100
        steps.append(f"<b>Step 3.</b> = {FR(fm(abs(diff), 4), fm(old))} {TIMES} 100 = <span class='hl'>{fm(abs(r), 4)}%</span> {word}")
        return _ok(steps, f"<b>{fm(abs(r), 4)}% {word}</b>")
    if kind == "original":
        v, p = num(d.get("v"), "the new value"), num(d.get("p"), "the percentage")
        up = d.get("dir", "inc") == "inc"
        pct = 100 + p if up else 100 - p
        if pct <= 0:
            raise UErr("That percentage change is not possible.")
        steps.append(f"<b>Step 1.</b> Call the original amount 100%. After {'an increase' if up else 'a decrease'} of {fm(p)}% the new value is {fm(pct)}% of the original.")
        steps.append(f"<b>Step 2.</b> So {fm(pct)}% of the original = {fm(v)}.")
        one = v / pct
        steps.append(f"<b>Step 3.</b> Divide to find 1%: {fm(v)} {DIVIDE} {fm(pct)} = {fm(one, 6)}")
        r = one * 100
        steps.append(f"<b>Step 4.</b> Multiply by 100 to find 100%: {fm(one, 6)} {TIMES} 100 = <span class='hl'>{fm(r, 4)}</span>")
        steps.append("<i>Common mistake:</i> do NOT take the percentage off the new value. The percentage was taken from the original.")
        return _ok(steps, f"<b>Original = {fm(r, 4)}</b>")
    if kind == "successive":
        n = num(d.get("n"), "the starting amount")
        parts = [t for t in re.split(r"[,;\s]+", (d.get("list") or "").strip()) if t]
        if not parts or len(parts) > 12:
            raise UErr("Type the changes separated by commas, like +10, -20, +5 (1 to 12 changes).")
        cur = n
        mult = Fraction(1)
        steps.append(f"<b>Start:</b> {fm(n)}. An increase of p% = multiply by (1 + p/100); a decrease = multiply by (1 &minus; p/100).")
        for i, t in enumerate(parts, 1):
            p = num(t, f"change {i}")
            m = 1 + p / 100
            if m < 0:
                raise UErr("A decrease of more than 100% is not possible.")
            new = cur * m
            steps.append(f"Change {i}: {fm(p)}% &rarr; {fm(cur, 4)} {TIMES} {fm(m, 6)} = {fm(new, 4)}")
            cur = new
            mult *= m
        total = (mult - 1) * 100
        steps.append(f"<b>Overall:</b> multiplier = {fm(mult, 6)}, so the overall change = ({fm(mult, 6)} &minus; 1) {TIMES} 100 = {fm(total, 4)}%")
        steps.append("<i>Note:</i> successive percentages are not simply added, because each one is taken from a different amount.")
        return _ok(steps, f"<b>Final amount {fm(cur, 4)}, overall {fm(abs(total), 4)}% {'increase' if total >= 0 else 'decrease'}</b>")
    raise UErr("Choose a type of question.")


# ================================================================== ratio ===

def _ratio_list(text, maxn=6):
    parts = [p for p in re.split(r"\s*[:;,]\s*", (text or "").strip().replace("∶", ":")) if p]
    if len(parts) < 2 or len(parts) > maxn:
        raise UErr("Write the ratio with a colon, like 2:3 or 1:2:5.")
    out = [num(p, "a ratio term") for p in parts]
    if any(v <= 0 for v in out):
        raise UErr("Ratio terms must be bigger than 0.")
    return out


def _clear(vals):
    """scale a list of Fractions to smallest whole numbers"""
    den = 1
    for v in vals:
        den = den * v.denominator // math.gcd(den, v.denominator)
    ints = [int(v * den) for v in vals]
    g = 0
    for i in ints:
        g = math.gcd(g, i)
    return [i // g for i in ints], den, g


def _rt(vals):
    return ":".join(fm(v, 4) for v in vals)


@guard
def ratio(d):
    kind = d.get("kind", "share")
    steps = []
    if kind == "simplify":
        vals = _ratio_list(d.get("r"))
        steps.append(f"<b>Ratio:</b> {_rt(vals)}")
        ints, den, g = _clear(vals)
        if den != 1:
            steps.append(f"<b>Step 1.</b> Remove decimals/fractions by multiplying every term by {den}: " + ":".join(str(int(v * den)) for v in vals))
        base = [int(v * den) for v in vals]
        gg = 0
        for b in base:
            gg = math.gcd(gg, b)
        steps.append(f"<b>Step {2 if den != 1 else 1}.</b> Find the HCF of the terms ({', '.join(str(b) for b in base)}): {gg}")
        steps.append(f"<b>Step {3 if den != 1 else 2}.</b> Divide every term by {gg}: <span class='hl'>{':'.join(str(i) for i in ints)}</span>")
        return _ok(steps, f"<b>{_rt(vals)} = {':'.join(str(i) for i in ints)}</b>")
    if kind == "share":
        amt = pos(d.get("amt"), "the amount")
        vals = _ratio_list(d.get("r"))
        ints, den, g = _clear(vals)
        total = sum(ints)
        steps.append(f"<b>Step 1 - Add the ratio parts</b> to find the number of equal parts: {' + '.join(str(i) for i in ints)} = {total} parts.")
        one = amt / total
        steps.append(f"<b>Step 2 - Find one part:</b> {fm(amt, 4)} {DIVIDE} {total} = {fm(one, 4)}")
        lines = []
        shares = []
        for i, r in enumerate(ints):
            s = one * r
            shares.append(s)
            lines.append(f"Share {i + 1}: {r} {TIMES} {fm(one, 4)} = <b>{fm(s, 4)}</b>")
        steps.append("<b>Step 3 - Multiply each ratio number by one part:</b><br>" + "<br>".join(lines))
        steps.append(f"<b>Check:</b> {' + '.join(fm(s, 4) for s in shares)} = {fm(sum(shares), 4)} &#10003;")
        return _ok(steps, "<b>" + " : ".join(fm(s, 4) for s in shares) + "</b>")
    if kind == "known":
        vals = _ratio_list(d.get("r"))
        ints, den, g = _clear(vals)
        idx = int(num(d.get("which"), "which term (1, 2, 3...)")) - 1
        if not 0 <= idx < len(ints):
            raise UErr(f"The ratio has only {len(ints)} terms, so choose 1 to {len(ints)}.")
        known = pos(d.get("val"), "the known amount")
        one = known / ints[idx]
        steps.append(f"<b>Step 1.</b> In the ratio {':'.join(map(str, ints))}, term {idx + 1} is {ints[idx]} parts and it equals {fm(known, 4)}.")
        steps.append(f"<b>Step 2 - One part:</b> {fm(known, 4)} {DIVIDE} {ints[idx]} = {fm(one, 4)}")
        shares = [one * r for r in ints]
        steps.append("<b>Step 3 - Every share</b> = ratio number {0} one part: ".format(TIMES) + ", ".join(f"{r}{TIMES}{fm(one, 4)} = {fm(s, 4)}" for r, s in zip(ints, shares)))
        steps.append(f"<b>Total</b> = {total_s(shares)}")
        return _ok(steps, f"<b>Shares: {' : '.join(fm(s, 4) for s in shares)} &nbsp; Total: {total_s(shares)}</b>")
    if kind == "missing":
        a, b, c, e = (num(d.get(k), "", True) for k in ("a", "b", "c", "e"))
        vals = [a, b, c, e]
        if sum(v is None for v in vals) != 1:
            raise UErr("Leave exactly one of the four boxes empty: that is the one to find.")
        steps.append("<b>Step 1.</b> Write the proportion as two equal fractions: " + FR("a", "b") + " = " + FR("c", "e") + ", then cross-multiply: a &times; e = b &times; c.")
        sh = ["?" if v is None else fm(v, 4) for v in vals]
        steps.append(f"<b>Step 2.</b> Put the numbers in: {FR(sh[0], sh[1])} = {FR(sh[2], sh[3])}")
        if a is None:
            if e == 0 or b == 0:
                raise UErr("A zero cannot be used here.")
            r = b * c / e
            steps.append(f"<b>Step 3.</b> a = {FR('b &times; c', 'e')} = {FR(fm(b) + ' &times; ' + fm(c), fm(e))} = <span class='hl'>{fm(r, 4)}</span>")
        elif b is None:
            if c == 0:
                raise UErr("A zero cannot be used here.")
            r = a * e / c
            steps.append(f"<b>Step 3.</b> b = {FR('a &times; e', 'c')} = {FR(fm(a) + ' &times; ' + fm(e), fm(c))} = <span class='hl'>{fm(r, 4)}</span>")
        elif c is None:
            if b == 0:
                raise UErr("A zero cannot be used here.")
            r = a * e / b
            steps.append(f"<b>Step 3.</b> c = {FR('a &times; e', 'b')} = {FR(fm(a) + ' &times; ' + fm(e), fm(b))} = <span class='hl'>{fm(r, 4)}</span>")
        else:
            if a == 0:
                raise UErr("A zero cannot be used here.")
            r = b * c / a
            steps.append(f"<b>Step 3.</b> e = {FR('b &times; c', 'a')} = {FR(fm(b) + ' &times; ' + fm(c), fm(a))} = <span class='hl'>{fm(r, 4)}</span>")
        return _ok(steps, f"<b>The missing number = {fm(r, 4)}</b>")
    if kind == "combine":
        r1, r2 = _ratio_list(d.get("r1"), 2), _ratio_list(d.get("r2"), 2)
        a, b = r1
        c, e = r2
        steps.append(f"<b>Given:</b> A:B = {fm(a)}:{fm(b)} and B:C = {fm(c)}:{fm(e)}. B appears in both, so make B the same number in each ratio.")
        L = b * c // 1 if False else None
        lcm_num = Fraction(1)
        # scale to whole numbers first
        (ia, ib), _, _ = _clear([a, b])
        (ic, ie), _, _ = _clear([c, e])
        l = ib * ic // math.gcd(ib, ic)
        m1, m2 = l // ib, l // ic
        steps.append(f"<b>Step 1.</b> Make both ratios whole: {ia}:{ib} and {ic}:{ie}. The B numbers are {ib} and {ic}; their LCM is {l}.")
        steps.append(f"<b>Step 2.</b> Multiply the first ratio by {m1}: {ia * m1}:{l}. Multiply the second ratio by {m2}: {l}:{ie * m2}.")
        fin = [ia * m1, l, ie * m2]
        g = math.gcd(math.gcd(fin[0], fin[1]), fin[2])
        fin = [x // g for x in fin]
        steps.append(f"<b>Step 3.</b> Now B is {l} in both, so A:B:C = {ia * m1}:{l}:{ie * m2}" + (f" = {':'.join(map(str, fin))} (divided by {g})" if g > 1 else ""))
        return _ok(steps, f"<b>A : B : C = {':'.join(map(str, fin))}</b>")
    if kind == "increase":
        q = pos(d.get("q"), "the quantity")
        r = _ratio_list(d.get("r"), 2)
        steps.append(f"<b>Step 1.</b> Increasing (or decreasing) {fm(q, 4)} in the ratio {fm(r[0])}:{fm(r[1])} means: new : old = {fm(r[0])} : {fm(r[1])}.")
        steps.append(f"<b>Step 2.</b> New = {FR(fm(r[0]), fm(r[1]))} {TIMES} {fm(q, 4)}")
        res = q * r[0] / r[1]
        steps.append(f"<b>Step 3.</b> = <span class='hl'>{fm(res, 4)}</span>")
        return _ok(steps, f"<b>New quantity = {fm(res, 4)}</b>")
    if kind in ("direct", "inverse"):
        a1, b1, a2 = pos(d.get("a1"), "the first number"), pos(d.get("b1"), "the first answer"), pos(d.get("a2"), "the second number")
        if kind == "direct":
            steps.append("<b>Step 1.</b> This is <b>direct proportion</b>: when one quantity goes up, the other goes up in the same way (more items &rarr; more cost).")
            steps.append(f"<b>Step 2 - Unitary method.</b> For 1 unit: {fm(b1, 4)} {DIVIDE} {fm(a1, 4)} = {fm(b1 / a1, 6)}")
            r = b1 / a1 * a2
            steps.append(f"<b>Step 3.</b> For {fm(a2, 4)} units: {fm(b1 / a1, 6)} {TIMES} {fm(a2, 4)} = <span class='hl'>{fm(r, 4)}</span>")
        else:
            steps.append("<b>Step 1.</b> This is <b>inverse proportion</b>: when one quantity goes up, the other goes DOWN (more workers &rarr; fewer days).")
            steps.append(f"<b>Step 2 - Find the total 'work'.</b> {fm(a1, 4)} {TIMES} {fm(b1, 4)} = {fm(a1 * b1, 4)} (this stays the same).")
            r = a1 * b1 / a2
            steps.append(f"<b>Step 3.</b> Divide by the new number: {fm(a1 * b1, 4)} {DIVIDE} {fm(a2, 4)} = <span class='hl'>{fm(r, 4)}</span>")
        return _ok(steps, f"<b>Answer = {fm(r, 4)}</b>")
    raise UErr("Choose a type of question.")


def total_s(shares):
    return fm(sum(shares), 4)


# ========================================================== profit & loss ===

@guard
def profit(d):
    kind = d.get("kind", "pl")
    steps = []
    if kind == "pl":
        cp, sp = pos(d.get("cp"), "the cost price"), pos(d.get("sp"), "the selling price")
        steps.append(f"<b>Step 1.</b> Compare cost price (CP = {fm(cp)}) and selling price (SP = {fm(sp)}). If SP is bigger there is a <b>profit</b>; if SP is smaller there is a <b>loss</b>.")
        diff = sp - cp
        if diff == 0:
            return _ok(steps + ["SP = CP, so there is neither profit nor loss."], "<b>No profit, no loss</b>")
        word = "Profit" if diff > 0 else "Loss"
        steps.append(f"<b>Step 2.</b> {word} = {'SP &minus; CP' if diff > 0 else 'CP &minus; SP'} = {fm(max(sp, cp))} &minus; {fm(min(sp, cp))} = {fm(abs(diff), 4)}")
        pct = abs(diff) / cp * 100
        steps.append(f"<b>Step 3.</b> {word} % = {FR(word.lower(), 'cost price')} {TIMES} 100 = {FR(fm(abs(diff), 4), fm(cp))} {TIMES} 100 = <span class='hl'>{fm(pct, 4)}%</span>")
        steps.append("<i>Remember:</i> percentage profit or loss is always based on the <b>cost price</b>.")
        return _ok(steps, f"<b>{word} = {fm(abs(diff), 4)}, {word.lower()} percent = {fm(pct, 4)}%</b>")
    if kind == "sp":
        cp, p = pos(d.get("cp"), "the cost price"), num(d.get("p"), "the percentage")
        gain = d.get("dir", "profit") == "profit"
        pct = 100 + p if gain else 100 - p
        steps.append(f"<b>Step 1.</b> CP = 100%. With a {fm(p)}% {'profit' if gain else 'loss'}, SP = {fm(pct)}% of CP.")
        r = cp * pct / 100
        steps.append(f"<b>Step 2.</b> SP = {FR(fm(pct), 100)} {TIMES} {fm(cp)} = <span class='hl'>{fm(r, 4)}</span>")
        return _ok(steps, f"<b>Selling price = {fm(r, 4)}</b>")
    if kind == "cp":
        sp, p = pos(d.get("sp"), "the selling price"), num(d.get("p"), "the percentage")
        gain = d.get("dir", "profit") == "profit"
        pct = 100 + p if gain else 100 - p
        if pct <= 0:
            raise UErr("That loss percentage is not possible.")
        steps.append(f"<b>Step 1.</b> CP = 100%. With a {fm(p)}% {'profit' if gain else 'loss'}, SP = {fm(pct)}% of CP, and SP = {fm(sp)}.")
        one = sp / pct
        steps.append(f"<b>Step 2.</b> 1% = {fm(sp)} {DIVIDE} {fm(pct)} = {fm(one, 6)}")
        r = one * 100
        steps.append(f"<b>Step 3.</b> CP (100%) = {fm(one, 6)} {TIMES} 100 = <span class='hl'>{fm(r, 4)}</span>")
        return _ok(steps, f"<b>Cost price = {fm(r, 4)}</b>")
    if kind == "discount":
        mp = pos(d.get("mp"), "the marked price")
        dp = num(d.get("dp"), "", True)
        sp = num(d.get("sp"), "", True)
        if (dp is None) == (sp is None):
            raise UErr("Fill in either the discount % (to find the selling price) or the selling price (to find the discount %).")
        if dp is not None:
            disc = mp * dp / 100
            steps.append(f"<b>Step 1.</b> Discount = {fm(dp)}% of {fm(mp)} = {FR(fm(dp), 100)} {TIMES} {fm(mp)} = {fm(disc, 4)}")
            steps.append(f"<b>Step 2.</b> Price paid = marked price &minus; discount = {fm(mp)} &minus; {fm(disc, 4)} = <span class='hl'>{fm(mp - disc, 4)}</span>")
            return _ok(steps, f"<b>Selling price = {fm(mp - disc, 4)}</b>")
        disc = mp - sp
        steps.append(f"<b>Step 1.</b> Discount = marked price &minus; selling price = {fm(mp)} &minus; {fm(sp)} = {fm(disc, 4)}")
        r = disc / mp * 100
        steps.append(f"<b>Step 2.</b> Discount % = {FR('discount', 'marked price')} {TIMES} 100 = {FR(fm(disc, 4), fm(mp))} {TIMES} 100 = <span class='hl'>{fm(r, 4)}%</span>")
        return _ok(steps, f"<b>Discount = {fm(r, 4)}%</b>")
    if kind == "commission":
        sales, rate = pos(d.get("sales"), "the total sales"), num(d.get("rate"), "the commission rate")
        base = num(d.get("base"), "", True) or Fraction(0)
        com = sales * rate / 100
        steps.append(f"<b>Step 1.</b> Commission = {fm(rate)}% of sales = {FR(fm(rate), 100)} {TIMES} {fm(sales)} = <span class='hl'>{fm(com, 4)}</span>")
        if base:
            steps.append(f"<b>Step 2.</b> Total earnings = basic salary + commission = {fm(base)} + {fm(com, 4)} = <span class='hl'>{fm(base + com, 4)}</span>")
        return _ok(steps, f"<b>Commission = {fm(com, 4)}" + (f", total earnings = {fm(base + com, 4)}" if base else "") + "</b>")
    if kind == "vat":
        price, rate = pos(d.get("price"), "the price"), num(d.get("rate"), "the VAT / tax rate")
        rev = d.get("dir", "add") == "remove"
        if not rev:
            tax = price * rate / 100
            steps.append(f"<b>Step 1.</b> VAT = {fm(rate)}% of {fm(price)} = {fm(tax, 4)}")
            steps.append(f"<b>Step 2.</b> Price with VAT = {fm(price)} + {fm(tax, 4)} = <span class='hl'>{fm(price + tax, 4)}</span>")
            return _ok(steps, f"<b>Total = {fm(price + tax, 4)}</b>")
        steps.append(f"<b>Step 1.</b> The price {fm(price)} already includes VAT, so it is {fm(100 + rate)}% of the price before VAT.")
        one = price / (100 + rate)
        steps.append(f"<b>Step 2.</b> 1% = {fm(price)} {DIVIDE} {fm(100 + rate)} = {fm(one, 6)}")
        r = one * 100
        steps.append(f"<b>Step 3.</b> Price before VAT = {fm(one, 6)} {TIMES} 100 = <span class='hl'>{fm(r, 4)}</span>; the VAT is {fm(price - r, 4)}")
        return _ok(steps, f"<b>Price without VAT = {fm(r, 4)}</b>")
    raise UErr("Choose a type of question.")


# =============================================================== interest ===

@guard
def interest(d):
    kind = d.get("kind", "simple")
    steps = []
    if kind == "simple":
        I, Pp, R, T = (num(d.get(k), "", True) for k in ("I", "P", "R", "T"))
        vals = {"I": I, "P": Pp, "R": R, "T": T}
        blanks = [k for k, v in vals.items() if v is None]
        if len(blanks) != 1:
            raise UErr("Fill in three of the four boxes (I, P, R, T) and leave the one you want to find EMPTY.")
        for k, v in vals.items():
            if v is not None and v <= 0:
                raise UErr("All the values must be bigger than 0.")
        steps.append(f"<b>Step 1 - The formula.</b> Simple interest: <span class='hl'>I = {FR('P &times; R &times; T', 100)}</span> where I = interest, P = principal (money at the start), R = rate % per year, T = time in years.")
        t = blanks[0]
        sh = {k: ("?" if v is None else fm(v, 4)) for k, v in vals.items()}
        steps.append(f"<b>Step 2 - Put in the numbers.</b> I = {sh['I']}, P = {sh['P']}, R = {sh['R']}, T = {sh['T']}")
        if t == "I":
            r = Pp * R * T / 100
            steps.append(f"<b>Step 3.</b> I = {FR(fm(Pp) + ' &times; ' + fm(R) + ' &times; ' + fm(T), 100)} = {FR(fm(Pp * R * T, 4), 100)} = <span class='hl'>{fm(r, 4)}</span>")
            steps.append(f"<b>Amount</b> (principal + interest) = {fm(Pp)} + {fm(r, 4)} = {fm(Pp + r, 4)}")
        elif t == "P":
            r = I * 100 / (R * T)
            steps.append(f"<b>Step 3 - Make P the subject:</b> P = {FR('I &times; 100', 'R &times; T')} = {FR(fm(I) + ' &times; 100', fm(R) + ' &times; ' + fm(T))} = <span class='hl'>{fm(r, 4)}</span>")
        elif t == "R":
            r = I * 100 / (Pp * T)
            steps.append(f"<b>Step 3 - Make R the subject:</b> R = {FR('I &times; 100', 'P &times; T')} = {FR(fm(I) + ' &times; 100', fm(Pp) + ' &times; ' + fm(T))} = <span class='hl'>{fm(r, 4)}%</span>")
        else:
            r = I * 100 / (Pp * R)
            steps.append(f"<b>Step 3 - Make T the subject:</b> T = {FR('I &times; 100', 'P &times; R')} = {FR(fm(I) + ' &times; 100', fm(Pp) + ' &times; ' + fm(R))} = <span class='hl'>{fm(r, 4)} years</span>")
        return _ok(steps, f"<b>{t} = {fm(r, 4)}</b>")
    if kind in ("compound", "cfindP"):
        n = num(d.get("n"), "the number of years")
        R = num(d.get("R"), "the rate")
        k = int(num(d.get("freq") or "1", "the compounding frequency"))
        if not (0 < n <= 60) or n * k > 600:
            raise UErr("Use a time between 0 and 60 years.")
        if k not in (1, 2, 4, 12):
            raise UErr("Compounding must be yearly (1), half-yearly (2), quarterly (4) or monthly (12).")
        if R <= -100:
            raise UErr("The rate is not possible.")
        rate_per = R / k
        periods = n * k
        if periods.denominator != 1:
            raise UErr("Time &times; compounding must be a whole number of periods (for example 2.5 years half-yearly = 5 periods).")
        periods = int(periods)
        m = 1 + rate_per / 100
        steps.append(f"<b>Step 1 - The formula.</b> <span class='hl'>A = P(1 + {FR('R', 100)})<sup>n</sup></span> where A = amount at the end, P = principal, "
                     f"R = rate per period, n = number of periods." + (f" Here the rate per period is {fm(R)} {DIVIDE} {k} = {fm(rate_per, 6)}% and there are {periods} periods." if k != 1 else ""))
        steps.append(f"<b>Step 2 - The multiplier.</b> 1 + {FR(fm(rate_per, 6), 100)} = {fm(m, 8)}")
        if kind == "compound":
            Pp = pos(d.get("P"), "the principal")
            rows = []
            cur = Pp
            for i in range(1, min(periods, 12) + 1):
                new = cur * m
                rows.append([str(i), fm(cur, 2), fm(new - cur, 2), fm(new, 2)])
                cur = new
            full = Pp * m ** periods
            if periods <= 12:
                steps.append("<b>Step 3 - Year by year</b> (to see what is happening):")
                steps.append(table(rows, ["Period", "Start", "Interest", "End"]))
            steps.append(f"<b>Step {3 if periods > 12 else 4} - Use the formula.</b> A = {fm(Pp)} {TIMES} ({fm(m, 8)})<sup>{periods}</sup> = <span class='hl'>{fm(full, 2)}</span>")
            steps.append(f"<b>Compound interest</b> = A &minus; P = {fm(full, 2)} &minus; {fm(Pp)} = <span class='hl'>{fm(full - Pp, 2)}</span>")
            return _ok(steps, f"<b>Amount = {fm(full, 2)}, compound interest = {fm(full - Pp, 2)}</b>")
        A = pos(d.get("A"), "the final amount")
        r = A / m ** periods
        steps.append(f"<b>Step 3.</b> A = P &times; ({fm(m, 8)})<sup>{periods}</sup>, so P = {FR(fm(A), '(' + fm(m, 8) + ')<sup>' + str(periods) + '</sup>')} = <span class='hl'>{fm(r, 2)}</span>")
        return _ok(steps, f"<b>Principal = {fm(r, 2)}</b>")
    if kind == "crate":
        Pp, A, n = pos(d.get("P"), "the principal"), pos(d.get("A"), "the final amount"), pos(d.get("n"), "the years")
        if A <= Pp:
            raise UErr("The final amount must be bigger than the principal.")
        steps.append("<b>Step 1.</b> A = P(1 + R/100)<sup>n</sup>. Divide both sides by P: " + FR("A", "P") + " = (1 + R/100)<sup>n</sup>")
        ratio_ = float(A / Pp)
        root = ratio_ ** (1 / float(n))
        steps.append(f"<b>Step 2.</b> {FR(fm(A), fm(Pp))} = {fm(A / Pp, 6)} = (1 + R/100)<sup>{fm(n)}</sup>")
        steps.append(f"<b>Step 3.</b> Take the {fm(n)}th root of both sides: 1 + R/100 = {root:.6f}")
        R = (root - 1) * 100
        steps.append(f"<b>Step 4.</b> R/100 = {root - 1:.6f}, so <span class='hl'>R = {R:.4f}%</span>")
        return _ok(steps, f"<b>Rate = {R:.2f}% per year</b>")
    if kind == "ctime":
        Pp, A, R = pos(d.get("P"), "the principal"), pos(d.get("A"), "the final amount"), pos(d.get("R"), "the rate")
        if A <= Pp:
            raise UErr("The final amount must be bigger than the principal.")
        m = 1 + R / 100
        steps.append(f"<b>Step 1.</b> A = P(1 + R/100)<sup>n</sup> &rarr; {fm(A)} = {fm(Pp)} {TIMES} ({fm(m, 6)})<sup>n</sup> &rarr; ({fm(m, 6)})<sup>n</sup> = {fm(A / Pp, 6)}")
        n = math.log(float(A / Pp)) / math.log(float(m))
        steps.append(f"<b>Step 2 - Use logarithms:</b> n log({fm(m, 6)}) = log({fm(A / Pp, 6)}), so n = {FR('log ' + fm(A / Pp, 6), 'log ' + fm(m, 6))} = <span class='hl'>{n:.4f}</span>")
        steps.append(f"So it takes about {n:.2f} years (the first whole year in which the money reaches {fm(A)} is year {math.ceil(n - 1e-9)}).")
        return _ok(steps, f"<b>n &asymp; {n:.2f} years</b>")
    if kind == "depr":
        Pp, R, n = pos(d.get("P"), "the original value"), num(d.get("R"), "the rate"), num(d.get("n"), "the years")
        if not 0 < n <= 60 or n.denominator != 1:
            raise UErr("Use a whole number of years (1 to 60).")
        n = int(n)
        m = 1 - R / 100
        if m <= 0:
            raise UErr("The rate must be less than 100%.")
        steps.append(f"<b>Step 1.</b> Depreciation means value goes DOWN by R% each year. Value after n years = P(1 &minus; {FR('R', 100)})<sup>n</sup>.")
        steps.append(f"<b>Step 2.</b> Multiplier = 1 &minus; {FR(fm(R), 100)} = {fm(m, 6)}")
        rows = []
        cur = Pp
        for i in range(1, min(n, 10) + 1):
            new = cur * m
            rows.append([str(i), fm(cur, 2), fm(cur - new, 2), fm(new, 2)])
            cur = new
        steps.append(table(rows, ["Year", "Start value", "Loss", "End value"]))
        v = Pp * m ** n
        steps.append(f"<b>Step 3.</b> Value = {fm(Pp)} {TIMES} ({fm(m, 6)})<sup>{n}</sup> = <span class='hl'>{fm(v, 2)}</span>")
        return _ok(steps, f"<b>Value after {n} years = {fm(v, 2)}</b> (lost {fm(Pp - v, 2)})")
    raise UErr("Choose a type of question.")


# ====================================================== rounding / std form ==

def _sf_round(x, sf):
    x = Fraction(x)
    if x == 0:
        return Fraction(0), 0
    e = 0
    a = abs(x)
    while a >= 10:
        a /= 10
        e += 1
    while a < 1:
        a *= 10
        e -= 1
    # a in [1,10); round at sf digits
    scaled = a * 10 ** (sf - 1)
    r = Fraction(int(scaled + Fraction(1, 2)))
    if r >= 10 ** sf:
        r /= 10
        e += 1
    val = (r / 10 ** (sf - 1)) * Fraction(10) ** e
    return val if x > 0 else -val, e


@guard
def rounding(d):
    kind = d.get("kind", "dp")
    steps = []
    if kind == "dp":
        x, n = num(d.get("x"), "the number"), int(num(d.get("n"), "the decimal places"))
        if not 0 <= n <= 10:
            raise UErr("Use 0 to 10 decimal places.")
        r = dec(x, n)
        steps.append(f"<b>Step 1.</b> Count {n} decimal place{'s' if n != 1 else ''} after the point, and look at the NEXT digit.")
        s = format(dec(abs(x), 12), "f")
        ip, _, fp = s.partition(".")
        nxt = fp[n] if n < len(fp) else "0"
        steps.append(f"<b>Step 2.</b> The next digit is {nxt}. If it is 5 or more, round UP; if it is 4 or less, leave it.")
        steps.append(f"<b>Step 3.</b> {fm(x, 12)} &rarr; <span class='hl'>{r}</span> (to {n} d.p.)")
        return _ok(steps, f"<b>{r}</b> to {n} decimal place{'s' if n != 1 else ''}")
    if kind == "sf":
        x, n = num(d.get("x"), "the number"), int(num(d.get("n"), "the significant figures"))
        if x == 0 or not 1 <= n <= 12:
            raise UErr("Use a non-zero number and 1 to 12 significant figures.")
        v, e = _sf_round(x, n)
        steps.append("<b>Step 1.</b> Significant figures start counting from the first digit that is NOT zero (zeros at the front do not count).")
        steps.append(f"<b>Step 2.</b> Keep {n} significant figure{'s' if n != 1 else ''}, look at the next digit, round up if it is 5 or more, and fill the rest with zeros if needed.")
        out = fm(v, max(0, n - 1 - e)) if v.denominator == 1 or e < n - 1 else fm(v, max(0, n - 1 - e))
        if e >= n - 1:
            out = str(int(v))
        else:
            out = format(dec(v, n - 1 - e), "f")
        steps.append(f"<b>Step 3.</b> {fm(x, 12)} &rarr; <span class='hl'>{out}</span> ({n} s.f.)")
        return _ok(steps, f"<b>{out}</b> to {n} significant figure{'s' if n != 1 else ''}")
    if kind == "std":
        x = num(d.get("x"), "the number")
        if x == 0:
            raise UErr("Zero cannot be written in standard form.")
        a = abs(x)
        e = 0
        while a >= 10:
            a /= 10
            e += 1
        while a < 1:
            a *= 10
            e -= 1
        steps.append("<b>Step 1.</b> Standard form is A &times; 10<sup>n</sup>, where A is between 1 and 10 (1 &le; A &lt; 10) and n is a whole number.")
        move = "left" if e > 0 else "right"
        steps.append(f"<b>Step 2.</b> Move the decimal point {abs(e)} place{'s' if abs(e) != 1 else ''} to the {move} so that it sits after the first non-zero digit: A = {fm(a, 12)}.")
        steps.append(f"<b>Step 3.</b> {'Moving left makes the power positive' if e > 0 else 'Moving right makes the power negative' if e < 0 else 'No move was needed, so the power is 0'}: n = {e}.")
        out = f"{'&minus;' if x < 0 else ''}{fm(a, 12)} &times; 10<sup>{str(e).replace('-', '&minus;')}</sup>"
        return _ok(steps, f"<b>{fm(x, 12)} = {out}</b>")
    if kind == "unstd":
        a, e = num(d.get("a"), "A"), num(d.get("e"), "the power")
        if e.denominator != 1 or abs(e) > 30:
            raise UErr("The power must be a whole number between -30 and 30.")
        e = int(e)
        v = a * Fraction(10) ** e
        steps.append(f"<b>Step 1.</b> The power is {e}: " + (f"move the decimal point {e} place{'s' if e != 1 else ''} to the RIGHT (make the number bigger)." if e > 0 else f"move the decimal point {-e} place{'s' if e != -1 else ''} to the LEFT (make the number smaller)." if e < 0 else "the power is 0, so multiply by 1."))
        steps.append(f"<b>Step 2.</b> {fm(a, 12)} &times; 10<sup>{str(e).replace('-', '&minus;')}</sup> = <span class='hl'>{fm(v, 30)}</span>")
        return _ok(steps, f"<b>{fm(v, 30)}</b>")
    if kind == "error":
        act, meas = pos(d.get("act"), "the actual value"), num(d.get("meas"), "the measured value")
        err = abs(meas - act)
        steps.append(f"<b>Step 1 - Error</b> = |measured &minus; actual| = |{fm(meas, 6)} &minus; {fm(act, 6)}| = {fm(err, 6)}")
        r = err / act * 100
        steps.append(f"<b>Step 2 - Percentage error</b> = {FR('error', 'actual value')} {TIMES} 100 = {FR(fm(err, 6), fm(act, 6))} {TIMES} 100 = <span class='hl'>{fm(r, 4)}%</span>")
        return _ok(steps, f"<b>Error = {fm(err, 6)}; percentage error = {fm(r, 4)}%</b>")
    if kind == "limits":
        x, n = num(d.get("x"), "the number"), pos(d.get("unit"), "the accuracy (10, 1, 0.1, 0.01 ...)")
        half = n / 2
        steps.append(f"<b>Step 1.</b> {fm(x, 8)} has been given to the nearest {fm(n, 8)}. Half of {fm(n, 8)} is {fm(half, 8)}.")
        steps.append(f"<b>Step 2.</b> Lower limit = {fm(x, 8)} &minus; {fm(half, 8)} = <span class='hl'>{fm(x - half, 8)}</span>; upper limit = {fm(x, 8)} + {fm(half, 8)} = <span class='hl'>{fm(x + half, 8)}</span>")
        steps.append(f"So the true value x satisfies {fm(x - half, 8)} &le; x &lt; {fm(x + half, 8)}.")
        return _ok(steps, f"<b>{fm(x - half, 8)} &le; x &lt; {fm(x + half, 8)}</b>")
    raise UErr("Choose a type of question.")


# ================================================================== spec ====

def _kind(options):
    return select("kind", "What do you want to do?", options, wide=True)


_DIR_IU = [("inc", "increase"), ("dec", "decrease")]

SPEC = {
    "title": "Percentages, Ratio, Profit & Interest",
    "intro": "Everyday and exam arithmetic with every step explained.",
    "tabs": [
        {"id": "pp", "label": "Percentages", "title": "Percentage problems", "endpoint": "percentages",
         "fields": [
             _kind([("of", "Find x% of an amount"), ("whatpct", "Write one amount as a % of another"),
                    ("incdec", "Increase or decrease an amount by x%"), ("change", "Find the % change (old &rarr; new)"),
                    ("original", "Find the ORIGINAL amount after a % change"), ("successive", "Successive % changes")]),
             field("p", "Percentage (%)", "15", show_if={"kind": ["of", "incdec", "original"]}),
             field("n", "Amount", "2400", show_if={"kind": ["of", "incdec", "successive"]}),
             field("a", "The part (the smaller amount)", "30", show_if={"kind": "whatpct"}),
             field("b", "The whole (the other amount)", "120", show_if={"kind": "whatpct"}),
             select("dir", "Increase or decrease?", _DIR_IU, show_if={"kind": ["incdec", "original"]}),
             field("old", "Old (original) value", "80", show_if={"kind": "change"}),
             field("new", "New value", "100", show_if={"kind": "change"}),
             field("v", "Value AFTER the change", "460", show_if={"kind": "original"}),
             field("list", "The changes, e.g. +10, -20, +5", "+10, -20, +5", wide=True, show_if={"kind": "successive"}),
         ]},
        {"id": "pr", "label": "Ratio & proportion", "title": "Ratio and proportion", "endpoint": "ratio",
         "fields": [
             _kind([("share", "Share an amount in a ratio"), ("simplify", "Simplify a ratio"),
                    ("known", "One share is known - find the others"), ("missing", "Find the missing number in a proportion"),
                    ("combine", "Combine two ratios (A:B and B:C)"), ("increase", "Increase / decrease in a ratio"),
                    ("direct", "Direct proportion (more &rarr; more)"), ("inverse", "Inverse proportion (more &rarr; less)")]),
             field("r", "Ratio (e.g. 2:3:5)", "2:3:5", show_if={"kind": ["share", "simplify", "known"]}),
             field("amt", "Amount to share", "1000", show_if={"kind": "share"}),
             field("which", "Which term is known? (1, 2, 3...)", "2", show_if={"kind": "known"}),
             field("val", "Value of that term", "60", show_if={"kind": "known"}),
             field("a", "a", "3", show_if={"kind": "missing"}), field("b", "b", "5", show_if={"kind": "missing"}),
             field("c", "c", "9", show_if={"kind": "missing"}), field("e", "e (leave one box empty)", "", show_if={"kind": "missing"}),
             field("r1", "First ratio A:B", "2:3", show_if={"kind": "combine"}),
             field("r2", "Second ratio B:C", "4:5", show_if={"kind": "combine"}),
             field("q", "Quantity", "120", show_if={"kind": "increase"}),
             field("r", "Ratio new:old (e.g. 5:4)", "5:4", show_if={"kind": "increase"}),
             field("a1", "First number (e.g. 5 men)", "5", show_if={"kind": ["direct", "inverse"]}),
             field("b1", "Its answer (e.g. 12 days)", "12", show_if={"kind": ["direct", "inverse"]}),
             field("a2", "New number (e.g. 3 men)", "3", show_if={"kind": ["direct", "inverse"]}),
         ]},
        {"id": "pf", "label": "Profit, loss & discount", "title": "Profit, loss, discount, commission and VAT", "endpoint": "profit",
         "fields": [
             _kind([("pl", "Find profit or loss and the percentage"), ("sp", "Find the selling price from CP and %"),
                    ("cp", "Find the cost price from SP and %"), ("discount", "Discount"),
                    ("commission", "Commission"), ("vat", "VAT / tax")]),
             field("cp", "Cost price", "800", show_if={"kind": ["pl", "sp"]}),
             field("sp", "Selling price", "920", show_if={"kind": ["pl", "cp"]}),
             field("p", "Percentage (%)", "15", show_if={"kind": ["sp", "cp"]}),
             select("dir", "Profit or loss?", [("profit", "profit"), ("loss", "loss")], show_if={"kind": ["sp", "cp"]}),
             field("mp", "Marked price", "5000", show_if={"kind": "discount"}),
             field("dp", "Discount % (to find the price)", "10", show_if={"kind": "discount"}),
             field("sp", "OR selling price (to find the discount %)", "", show_if={"kind": "discount"}),
             field("sales", "Total sales", "250000", show_if={"kind": "commission"}),
             field("rate", "Commission rate (%)", "4", show_if={"kind": "commission"}),
             field("base", "Basic salary (optional)", "", show_if={"kind": "commission"}),
             field("price", "Price", "20000", show_if={"kind": "vat"}),
             field("rate", "VAT rate (%)", "7.5", show_if={"kind": "vat"}),
             select("dir", "Add VAT or remove it?", [("add", "add VAT to the price"), ("remove", "price already includes VAT")], show_if={"kind": "vat"}),
         ]},
        {"id": "pi", "label": "Simple & compound interest", "title": "Interest and depreciation", "endpoint": "interest",
         "fields": [
             _kind([("simple", "Simple interest (find I, P, R or T)"), ("compound", "Compound interest - find amount"),
                    ("cfindP", "Compound interest - find the principal"), ("crate", "Compound interest - find the rate"),
                    ("ctime", "Compound interest - find the time"), ("depr", "Depreciation")]),
             field("I", "Interest (I)", "", show_if={"kind": "simple"}), field("P", "Principal (P)", "50000", show_if={"kind": ["simple", "compound", "crate", "ctime", "depr"]}),
             field("R", "Rate % per year (R)", "5", show_if={"kind": ["simple", "compound", "cfindP", "ctime", "depr"]}),
             field("T", "Time in years (T)", "3", show_if={"kind": "simple"}),
             field("n", "Time in years", "3", show_if={"kind": ["compound", "cfindP", "crate", "depr"]}),
             select("freq", "Compounded", [("1", "yearly"), ("2", "half-yearly"), ("4", "quarterly"), ("12", "monthly")], show_if={"kind": ["compound", "cfindP"]}),
             field("A", "Final amount (A)", "60000", show_if={"kind": ["cfindP", "crate", "ctime"]}),
         ]},
        {"id": "pa", "label": "Rounding & standard form", "title": "Approximation, standard form and errors", "endpoint": "rounding",
         "fields": [
             _kind([("dp", "Round to decimal places"), ("sf", "Round to significant figures"),
                    ("std", "Write in standard form"), ("unstd", "Standard form &rarr; ordinary number"),
                    ("error", "Percentage error"), ("limits", "Limits of accuracy")]),
             field("x", "Number", "0.004567", show_if={"kind": ["dp", "sf", "std", "limits"]}),
             field("n", "How many?", "2", show_if={"kind": ["dp", "sf"]}),
             field("a", "A (between 1 and 10)", "3.5", show_if={"kind": "unstd"}), field("e", "Power of 10 (n)", "-4", show_if={"kind": "unstd"}),
             field("act", "Actual value", "50", show_if={"kind": "error"}), field("meas", "Measured value", "48.5", show_if={"kind": "error"}),
             field("unit", "Given to the nearest ... (10, 1, 0.1 ...)", "10", show_if={"kind": "limits"}),
         ]},
    ],
}

# fields reused under the same name need unique visibility; the page sends only visible controls.
topics.register("percent", SPEC, {"percentages": percentages, "ratio": ratio, "profit": profit,
                                   "interest": interest, "rounding": rounding})
