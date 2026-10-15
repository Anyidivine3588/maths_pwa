"""Commercial arithmetic: VAT, income tax, rates, wages, commission, hire purchase, currency, bills, shares."""
import re
from fractions import Fraction

import topics
from tcommon import UErr, fm, num, pos, dec, field, select, guard, _ok, _fail
from frac_numeric import table

MINUS = "&minus;"
NAIRA = "&#8358;"


def HL(s):
    return f"<span class='hl'>{s}</span>"


def N(x, p=2):
    s = format(dec(x, p), ",f") if False else f"{dec(x, p):,.{p}f}"
    return f"{NAIRA}{s}"


def pc(x):
    return fm(x, 4) + "%"


def money_in(d, key, label, allow0=False):
    v = Fraction(num(d.get(key), label))
    if v < 0 or (v == 0 and not allow0):
        raise UErr(f"{label} must be {'0 or more' if allow0 else 'bigger than 0'}.")
    if v > 10 ** 13:
        raise UErr("That number is too big.")
    return v


def pct_in(d, key, label, hi=1000):
    v = Fraction(num(d.get(key), label))
    if v < 0 or v > hi:
        raise UErr(f"{label} must be between 0 and {hi}.")
    return v


# ------------------------------------------------------------------- tax ----
@guard
def vat(d):
    mode = d.get("mode", "add")
    r = pct_in(d, "r", "The VAT rate", 100) if mode != "rate" else Fraction(0)
    steps = ["<b>VAT (Value Added Tax)</b> is a percentage added to the price of goods and services. The shop collects it for the government."]
    if mode == "add":
        p = money_in(d, "p", "The price before VAT")
        vt = p * r / 100
        steps.append(f"<b>VAT amount</b> = {fm(r, 4)}% of {N(p)} = {fm(r, 4)} &divide; 100 &times; {fm(p, 2)} = {HL(N(vt))}")
        steps.append(f"<b>Price including VAT</b> = price + VAT = {N(p)} + {N(vt)} = {HL(N(p + vt))}")
        steps.append(f"<b>Shortcut:</b> multiply the price by {fm(1 + r / 100, 4)} (that is 100% + {fm(r, 4)}% = {fm(100 + r, 4)}%, as a decimal) to get the answer in one step.")
        return _ok(steps, f"<b>VAT = {N(vt)}; price with VAT = {N(p + vt)}</b>")
    if mode == "remove":
        t = money_in(d, "p", "The price including VAT")
        steps.append(f"<b>The price {N(t)} already includes VAT.</b> It is <b>100% + {fm(r, 4)}% = {fm(100 + r, 4)}%</b> of the original price (the price before VAT is the 100%).")
        steps.append(f"<b>Find 1% first:</b> {fm(t, 2)} &divide; {fm(100 + r, 4)} = {fm(t / (100 + r), 6)}")
        orig = t * 100 / (100 + r)
        steps.append(f"<b>Price before VAT</b> = 100 &times; 1% = {HL(N(orig))}")
        steps.append(f"<b>VAT paid</b> = {N(t)} &minus; {N(orig)} = {HL(N(t - orig))}")
        steps.append("<b>Common mistake:</b> do NOT take the VAT percentage off the total. The VAT was worked out on the smaller, original price.")
        return _ok(steps, f"<b>Original price = {N(orig)}; VAT = {N(t - orig)}</b>")
    # find rate
    p = money_in(d, "p", "The price before VAT")
    t = money_in(d, "t", "The price including VAT")
    if t < p:
        raise UErr("The price including VAT must be bigger than the price before VAT.")
    steps = [steps[0], f"<b>VAT paid</b> = {N(t)} &minus; {N(p)} = {N(t - p)}",
             f"<b>VAT rate</b> = VAT &divide; original price &times; 100% = {fm(t - p, 2)} &divide; {fm(p, 2)} &times; 100 = {HL(pc((t - p) / p * 100))}"]
    return _ok(steps, f"<b>VAT rate = {pc((t - p) / p * 100)}</b>")


def parse_bands(text):
    out = []
    for part in re.split(r"[;,\n]+", (text or "").strip()):
        part = part.strip()
        if not part:
            continue
        m = re.fullmatch(r"(rest|\d+(?:\.\d+)?)\s*[:@]\s*(\d+(?:\.\d+)?)\s*%?", part, re.I)
        if not m:
            raise UErr(f"I could not read '{re.sub('[<>&]', '', part[:25])}'. Write each band as amount:rate, like 300000:7, and the last as rest:24.")
        out.append((None if m.group(1).lower() == "rest" else Fraction(m.group(1)), Fraction(m.group(2))))
    if not out or len(out) > 10:
        raise UErr("Give between 1 and 10 tax bands.")
    return out


@guard
def income_tax(d):
    gross = money_in(d, "g", "The gross income")
    relief = money_in(d, "rl", "The relief", allow0=True) if (d.get("rl") or "").strip() else Fraction(0)
    bands = parse_bands(d.get("bands"))
    taxable = gross - relief
    steps = ["<b>Income tax</b> is charged in <b>bands</b> (a graduated or progressive system): the first part of your taxable income is taxed at a low rate, the next part at a higher rate, and so on. You only pay the higher rate on the part of your income that falls in that band.",
             "<i>The bands used here are the ones you typed (the default is a textbook example). Tax laws change, so always use the bands given in your question.</i>",
             f"<b>Taxable income</b> = gross income &minus; reliefs/allowances = {N(gross)} &minus; {N(relief)} = {HL(N(taxable))}"]
    if taxable <= 0:
        steps.append("The taxable income is 0 or less, so no tax is paid.")
        return _ok(steps, f"<b>Tax = {N(0)}</b>")
    rows, remaining, total = [], taxable, Fraction(0)
    for i, (amt, rate) in enumerate(bands):
        if remaining <= 0:
            break
        part = remaining if amt is None else min(amt, remaining)
        tx = part * rate / 100
        rows.append((f"Band {i + 1}: {'the rest' if amt is None else 'first' if i == 0 else 'next'} {N(part, 0) if True else ''}", f"{fm(rate, 4)}%", f"{fm(rate, 4)}% of {fm(part, 2)}", N(tx)))
        total += tx
        remaining -= part
    if remaining > 0:
        steps.append(f"<b>Note:</b> your bands did not cover all the income. {N(remaining)} was left untaxed. Add a last band like rest:24.")
    steps.append(table(rows, ["Part of income", "Rate", "Working", "Tax"]))
    steps.append(f"<b>Total tax</b> = add the tax from every band = {HL(N(total))}")
    steps.append(f"<b>Net (take-home) income</b> = gross &minus; tax = {N(gross)} &minus; {N(total)} = {HL(N(gross - total))}. "
                 f"<b>Average tax rate</b> = {fm(total, 2)} &divide; {fm(gross, 2)} &times; 100 = {pc(total / gross * 100)}")
    return _ok(steps, f"<b>Tax = {N(total)}; take-home = {N(gross - total)}</b>")


@guard
def rates(d):
    mode = d.get("mode", "kobo")
    if mode == "kobo":
        v = money_in(d, "v", "The assessed value of the property")
        k = pct_in(d, "k", "The rate (kobo in the naira)", 100)
        steps = [f"<b>Rates</b> are local taxes on property. A rate of <b>{fm(k, 4)}k in the &#8358;</b> means you pay {fm(k, 4)} kobo for every &#8358;1 of the assessed value.",
                 f"<b>Change kobo to naira:</b> 100 kobo = &#8358;1, so {fm(k, 4)}k = &#8358;{fm(k / 100, 6)}",
                 f"<b>Rates payable</b> = assessed value &times; rate per naira = {fm(v, 2)} &times; {fm(k / 100, 6)} = {HL(N(v * k / 100))}"]
        return _ok(steps, f"<b>Rates = {N(v * k / 100)}</b>")
    if mode == "find":
        v = money_in(d, "v", "The assessed value")
        a = money_in(d, "a", "The rates paid")
        steps = [f"<b>Rate in the naira</b> = rates paid &divide; assessed value = {fm(a, 2)} &divide; {fm(v, 2)} = &#8358;{fm(a / v, 6)} per &#8358;1",
                 f"Change to kobo (&times; 100): {HL(fm(a / v * 100, 4) + 'k in the &#8358;')}"]
        return _ok(steps, f"<b>Rate = {fm(a / v * 100, 4)}k in the &#8358;</b>")
    p = money_in(d, "v", "The value of the goods")
    r = pct_in(d, "k", "The duty rate (%)", 1000)
    steps = [f"<b>Import duty</b> is a tax on goods brought into the country. It is a percentage of the value of the goods.",
             f"Duty = {fm(r, 4)}% of {N(p)} = {fm(r, 4)} &divide; 100 &times; {fm(p, 2)} = {HL(N(p * r / 100))}",
             f"<b>Total cost</b> = value + duty = {N(p)} + {N(p * r / 100)} = {HL(N(p + p * r / 100))}"]
    return _ok(steps, f"<b>Duty = {N(p * r / 100)}; total = {N(p + p * r / 100)}</b>")


# ----------------------------------------------------------------- wages ----
@guard
def wages(d):
    mode = d.get("mode", "hourly")
    if mode == "hourly":
        rate = money_in(d, "rate", "The pay per hour")
        h = money_in(d, "h", "The normal hours worked")
        oh = money_in(d, "oh", "The overtime hours", allow0=True) if (d.get("oh") or "").strip() else Fraction(0)
        mult = Fraction(num(d.get("mult"), "The overtime multiplier"))
        steps = [f"<b>Basic pay</b> = normal hours &times; rate per hour = {fm(h, 2)} &times; {fm(rate, 2)} = {HL(N(h * rate))}"]
        ot_rate = rate * mult
        ot = oh * ot_rate
        if oh > 0:
            steps.append(f"<b>Overtime rate</b> = normal rate &times; {fm(mult, 2)} ({'time and a half' if mult == Fraction(3, 2) else 'double time' if mult == 2 else 'overtime multiplier'}) = {fm(rate, 2)} &times; {fm(mult, 2)} = {N(ot_rate)} per hour")
            steps.append(f"<b>Overtime pay</b> = {fm(oh, 2)} &times; {N(ot_rate)} = {HL(N(ot))}")
        tot = h * rate + ot
        steps.append(f"<b>Total pay</b> = basic + overtime = {N(h * rate)} + {N(ot)} = {HL(N(tot))}")
        return _ok(steps, f"<b>Total pay = {N(tot)}</b>")
    if mode == "comm":
        s = money_in(d, "s", "The total sales")
        c = pct_in(d, "c", "The commission rate", 100)
        sal = Fraction(num(d.get("sal"), "The basic salary", True) or 0)
        steps = [f"<b>Commission</b> is extra pay for selling things: a percentage of the sales. Commission = {fm(c, 4)}% of {N(s)} = {fm(c, 4)} &divide; 100 &times; {fm(s, 2)} = {HL(N(s * c / 100))}"]
        if sal:
            steps.append(f"<b>Total earnings</b> = basic salary + commission = {N(sal)} + {N(s * c / 100)} = {HL(N(sal + s * c / 100))}")
        return _ok(steps, f"<b>Commission = {N(s * c / 100)}" + (f"; total = {N(sal + s * c / 100)}" if sal else "") + "</b>")
    g = money_in(d, "g", "The gross salary")
    ded = [(Fraction(num(d.get(k), lab, True) or 0)) for k, lab in (("d1", "Tax"), ("d2", "Pension"), ("d3", "Other deduction"))]
    names = ["Tax", "Pension", "Other"]
    steps = [f"<b>Gross salary</b> is what you earn before anything is taken off: {N(g)}. <b>Net salary</b> (take-home pay) is what is left after deductions.",
             "<b>Deductions</b> (each as a percentage of the gross salary):"]
    rows, tot = [], Fraction(0)
    for nm, r in zip(names, ded):
        if r:
            rows.append((nm, f"{fm(r, 4)}%", f"{fm(r, 4)}% of {fm(g, 2)}", N(g * r / 100)))
            tot += g * r / 100
    if rows:
        steps.append(table(rows, ["Deduction", "Rate", "Working", "Amount"]))
    steps.append(f"<b>Total deductions</b> = {N(tot)}")
    steps.append(f"<b>Net salary</b> = gross &minus; deductions = {N(g)} &minus; {N(tot)} = {HL(N(g - tot))}")
    return _ok(steps, f"<b>Net salary = {N(g - tot)}</b>")


# --------------------------------------------------------- hire purchase ----
@guard
def hire(d):
    mode = d.get("mode", "total")
    cash = money_in(d, "cash", "The cash price")
    dep = money_in(d, "dep", "The deposit", allow0=True) if (d.get("dep") or "").strip() else Fraction(0)
    steps = ["<b>Hire purchase (HP)</b> lets you take the goods now, pay a <b>deposit</b>, and pay the rest in <b>instalments</b>. It usually costs more than the cash price, because of interest."]
    if mode == "total":
        n = int(Fraction(num(d.get("n"), "The number of instalments")))
        inst = money_in(d, "inst", "The amount of each instalment")
        if not 1 <= n <= 600:
            raise UErr("Use between 1 and 600 instalments.")
        paid = inst * n
        total = dep + paid
        steps.append(f"<b>Total of the instalments</b> = {n} &times; {N(inst)} = {HL(N(paid))}")
        steps.append(f"<b>Hire purchase price</b> = deposit + instalments = {N(dep)} + {N(paid)} = {HL(N(total))}")
        extra = total - cash
        steps.append(f"<b>Extra cost</b> compared with cash = {N(total)} &minus; {N(cash)} = {HL(N(extra))}")
        steps.append(f"<b>Extra cost as a percentage of the cash price</b> = {fm(extra, 2)} &divide; {fm(cash, 2)} &times; 100 = {HL(pc(extra / cash * 100))}")
        return _ok(steps, f"<b>HP price = {N(total)}; extra = {N(extra)} ({pc(extra / cash * 100)})</b>")
    # monthly instalment with flat interest
    n = int(Fraction(num(d.get("n"), "The number of instalments")))
    r = pct_in(d, "r", "The interest rate per year", 200)
    yrs = Fraction(num(d.get("yrs"), "The number of years"))
    if yrs <= 0 or yrs > 50 or not 1 <= n <= 600:
        raise UErr("Use a sensible number of years and instalments.")
    bal = cash - dep
    steps.append(f"<b>Balance to be paid by instalments</b> = cash price &minus; deposit = {N(cash)} &minus; {N(dep)} = {HL(N(bal))}")
    interest = bal * r * yrs / 100
    steps.append(f"<b>Simple interest</b> on the balance = P &times; R &times; T &divide; 100 = {fm(bal, 2)} &times; {fm(r, 4)} &times; {fm(yrs, 4)} &divide; 100 = {HL(N(interest))}")
    tot = bal + interest
    steps.append(f"<b>Total to repay</b> = balance + interest = {N(bal)} + {N(interest)} = {HL(N(tot))}")
    steps.append(f"<b>Each instalment</b> = total &divide; {n} = {fm(tot, 2)} &divide; {n} = {HL(N(tot / n))}")
    steps.append(f"<b>Hire purchase price</b> = deposit + total repaid = {N(dep)} + {N(tot)} = {N(dep + tot)}")
    return _ok(steps, f"<b>Instalment = {N(tot / n)}; HP price = {N(dep + tot)}</b>")


# -------------------------------------------------------------- currency ----
@guard
def currency(d):
    mode = d.get("mode", "to")
    amt = money_in(d, "amt", "The amount")
    rate = money_in(d, "rate", "The exchange rate")
    cur = re.sub(r"[^A-Za-z]", "", d.get("cur") or "")[:6].upper() or "USD"
    steps = [f"<b>Exchange rate:</b> 1 {cur} = {NAIRA}{fm(rate, 4)}. To change money, <b>multiply or divide</b> by the rate."]
    if mode == "to":
        steps.append(f"<b>Foreign money &rarr; naira:</b> multiply by the rate (1 {cur} is worth many naira, so you get more naira). {fm(amt, 2)} &times; {fm(rate, 4)} = {HL(N(amt * rate))}")
        steps.append(f"<b>Check:</b> the answer should be <b>bigger</b> than {fm(amt, 2)}, because naira is worth less than 1 {cur}. &check;")
        return _ok(steps, f"<b>{fm(amt, 2)} {cur} = {N(amt * rate)}</b>")
    steps.append(f"<b>Naira &rarr; foreign money:</b> divide by the rate. {N(amt)} &divide; {fm(rate, 4)} = {HL(fm(amt / rate, 2) + ' ' + cur)}")
    steps.append(f"<b>Check:</b> the answer should be <b>smaller</b> than {fm(amt, 2)}. &check;")
    return _ok(steps, f"<b>{N(amt)} = {fm(amt / rate, 2)} {cur}</b>")


@guard
def cross_rate(d):
    amt = money_in(d, "amt", "The amount")
    r1 = money_in(d, "r1", "The first rate")
    r2 = money_in(d, "r2", "The second rate")
    c1 = re.sub(r"[^A-Za-z]", "", d.get("c1") or "")[:6].upper() or "USD"
    c2 = re.sub(r"[^A-Za-z]", "", d.get("c2") or "")[:6].upper() or "GBP"
    steps = [f"<b>Changing one foreign currency into another</b> (say {c1} into {c2}) goes <b>through naira</b>. Rates: 1 {c1} = {NAIRA}{fm(r1, 4)} and 1 {c2} = {NAIRA}{fm(r2, 4)}.",
             f"<b>Step 1: {c1} &rarr; naira</b> (multiply): {fm(amt, 2)} &times; {fm(r1, 4)} = {N(amt * r1)}",
             f"<b>Step 2: naira &rarr; {c2}</b> (divide): {fm(amt * r1, 2)} &divide; {fm(r2, 4)} = {HL(fm(amt * r1 / r2, 2) + ' ' + c2)}"]
    return _ok(steps, f"<b>{fm(amt, 2)} {c1} = {fm(amt * r1 / r2, 2)} {c2}</b>")


# ----------------------------------------------------------------- bills ----
@guard
def bill(d):
    units = money_in(d, "u", "The units used")
    rate = money_in(d, "rate", "The cost per unit")
    fix = money_in(d, "fix", "The fixed charge", allow0=True) if (d.get("fix") or "").strip() else Fraction(0)
    v = pct_in(d, "vat", "The VAT rate", 100) if (d.get("vat") or "").strip() else Fraction(0)
    steps = ["<b>A bill</b> (electricity, water, phone...) usually has a <b>fixed charge</b> plus a charge for the <b>units used</b>, and sometimes VAT.",
             f"<b>Cost of units</b> = units &times; cost per unit = {fm(units, 2)} &times; {N(rate)} = {HL(N(units * rate))}",
             f"<b>Subtotal</b> = fixed charge + units = {N(fix)} + {N(units * rate)} = {HL(N(fix + units * rate))}"]
    sub = fix + units * rate
    if v:
        steps.append(f"<b>VAT</b> = {fm(v, 4)}% of {N(sub)} = {HL(N(sub * v / 100))}")
        steps.append(f"<b>Total bill</b> = {N(sub)} + {N(sub * v / 100)} = {HL(N(sub + sub * v / 100))}")
    return _ok(steps, f"<b>Total bill = {N(sub + sub * v / 100)}</b>")


# ---------------------------------------------------------------- shares ----
@guard
def shares(d):
    n = money_in(d, "n", "The number of shares")
    nominal = money_in(d, "nom", "The nominal (face) value of one share")
    mkt = money_in(d, "mkt", "The market price of one share")
    div = pct_in(d, "div", "The dividend rate", 1000)
    br = pct_in(d, "br", "The brokerage rate", 100) if (d.get("br") or "").strip() else Fraction(0)
    steps = ["<b>Shares:</b> buying a share makes you a part-owner of a company. Two prices matter: the <b>nominal (face) value</b> on the certificate, and the <b>market price</b> you actually pay. "
             "The <b>dividend</b> (your share of the profit) is a percentage of the <b>nominal</b> value, not of the market price.",
             f"<b>Cost of the shares</b> = number &times; market price = {fm(n, 2)} &times; {N(mkt)} = {HL(N(n * mkt))}"]
    cost = n * mkt
    if br:
        steps.append(f"<b>Brokerage</b> (the stockbroker's fee) = {fm(br, 4)}% of {N(cost)} = {N(cost * br / 100)}, so the total paid = {HL(N(cost + cost * br / 100))}")
        cost += cost * br / 100
    dv = n * nominal * div / 100
    steps.append(f"<b>Dividend received</b> = {fm(div, 4)}% of the nominal value = {fm(div, 4)} &divide; 100 &times; ({fm(n, 2)} &times; {fm(nominal, 2)}) = {HL(N(dv))}")
    steps.append(f"<b>Dividend yield</b> (how much you earn compared with what you paid) = dividend &divide; cost &times; 100 = {fm(dv, 2)} &divide; {fm(cost, 2)} &times; 100 = {HL(pc(dv / cost * 100))}")
    return _ok(steps, f"<b>Cost = {N(cost)}; dividend = {N(dv)}; yield = {pc(dv / cost * 100)}</b>")


DEFB = "300000:7, 300000:11, 500000:15, 500000:19, 1600000:21, rest:24"
SPEC = {
    "title": "Commercial Arithmetic",
    "intro": "Money maths for real life and for the exam: <b>VAT, income tax, rates, wages, commission, hire purchase, currency exchange, bills and shares</b>. All amounts are in naira (&#8358;).",
    "tabs": [
        {"id": "cv", "label": "VAT", "title": "Value Added Tax", "endpoint": "vat",
         "fields": [select("mode", "I want to", [("add", "add VAT to a price"), ("remove", "find the price before VAT"), ("rate", "find the VAT rate")], wide=True),
                    field("p", "Price", "20000", show_if={"mode": ["add", "remove", "rate"]}), field("r", "VAT rate (%)", "7.5", show_if={"mode": ["add", "remove"]}),
                    field("t", "Price including VAT", "21500", show_if={"mode": "rate"})], "button": "Work it out"},
        {"id": "ci", "label": "Income tax", "title": "Income tax in bands", "endpoint": "income_tax",
         "hint": "Write each band as <b>amount:rate</b>, separated by commas. The last band can be <b>rest:rate</b> (everything above). The default is a textbook example; use the bands in your question.",
         "fields": [field("g", "Gross income per year", "2400000"), field("rl", "Reliefs / allowances (empty = 0)", "400000"), field("bands", "Tax bands", DEFB, wide=True, half=False)], "button": "Work out tax"},
        {"id": "cr", "label": "Rates and duty", "title": "Rates, import duty", "endpoint": "rates",
         "fields": [select("mode", "I want", [("kobo", "rates from kobo in the naira"), ("find", "the kobo-in-the-naira rate"), ("duty", "import duty")], wide=True),
                    field("v", "Value (assessed value / goods)", "800000"), field("k", "Rate (kobo in &#8358; or duty %)", "12", show_if={"mode": ["kobo", "duty"]}),
                    field("a", "Rates paid", "96000", show_if={"mode": "find"})], "button": "Work it out"},
        {"id": "cw", "label": "Wages and salary", "title": "Wages, overtime, commission and net salary", "endpoint": "wages",
         "fields": [select("mode", "Type", [("hourly", "hourly pay with overtime"), ("comm", "commission on sales"), ("net", "gross to net salary")], wide=True),
                    field("rate", "Pay per hour", "1500", show_if={"mode": "hourly"}), field("h", "Normal hours", "40", show_if={"mode": "hourly"}),
                    field("oh", "Overtime hours", "6", show_if={"mode": "hourly"}),
                    select("mult", "Overtime paid at", [("3/2", "time and a half (&times;1.5)"), ("2", "double time (&times;2)"), ("5/4", "&times;1.25")], show_if={"mode": "hourly"}),
                    field("s", "Total sales", "850000", show_if={"mode": "comm"}), field("c", "Commission (%)", "4", show_if={"mode": "comm"}), field("sal", "Basic salary (empty = none)", "50000", show_if={"mode": "comm"}),
                    field("g", "Gross salary", "180000", show_if={"mode": "net"}), field("d1", "Tax (%)", "10", show_if={"mode": "net"}),
                    field("d2", "Pension (%)", "8", show_if={"mode": "net"}), field("d3", "Other (%)", "", show_if={"mode": "net"})], "button": "Work it out"},
        {"id": "ch", "label": "Hire purchase", "title": "Hire purchase", "endpoint": "hire",
         "fields": [select("mode", "I know", [("total", "the instalments (find the HP price)"), ("flat", "the interest rate (find the instalment)")], wide=True),
                    field("cash", "Cash price", "240000"), field("dep", "Deposit (empty = 0)", "60000"), field("n", "Number of instalments", "12"),
                    field("inst", "Each instalment", "17500", show_if={"mode": "total"}),
                    field("r", "Interest rate per year (%)", "15", show_if={"mode": "flat"}), field("yrs", "Time (years)", "1", show_if={"mode": "flat"})], "button": "Work it out"},
        {"id": "cc", "label": "Currency exchange", "title": "Currency exchange", "endpoint": "currency",
         "fields": [select("mode", "Change", [("to", "foreign money into naira"), ("from", "naira into foreign money")], wide=True),
                    field("amt", "Amount", "250"), field("cur", "Currency code", "USD"), field("rate", "1 unit = how many naira?", "1500")], "button": "Convert"},
        {"id": "cx", "label": "Between currencies", "title": "Change one foreign currency into another (through naira)", "endpoint": "cross_rate",
         "fields": [field("amt", "Amount", "200"), field("c1", "From currency", "USD"), field("r1", "1 unit = &#8358;", "1500"), field("c2", "To currency", "GBP"), field("r2", "1 unit = &#8358;", "1950")], "button": "Convert"},
        {"id": "cb", "label": "Bills", "title": "Utility bills", "endpoint": "bill",
         "fields": [field("u", "Units used", "320"), field("rate", "Cost per unit (&#8358;)", "68"), field("fix", "Fixed charge (empty = 0)", "1500"), field("vat", "VAT % (empty = none)", "7.5")], "button": "Work out bill"},
        {"id": "cs", "label": "Shares", "title": "Shares, dividends and yield", "endpoint": "shares",
         "fields": [field("n", "Number of shares", "2000"), field("nom", "Nominal value per share", "1"), field("mkt", "Market price per share", "2.50"),
                    field("div", "Dividend rate (%)", "12"), field("br", "Brokerage % (empty = none)", "1.5")], "button": "Work it out"},
    ],
}
topics.register("commerce", SPEC, {"vat": vat, "income_tax": income_tax, "rates": rates, "wages": wages, "hire": hire, "currency": currency, "cross_rate": cross_rate, "bill": bill, "shares": shares})
