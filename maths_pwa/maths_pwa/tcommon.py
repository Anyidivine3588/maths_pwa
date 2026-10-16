"""Shared helpers for the generic-topic modules (pure Python)."""
import re
from decimal import Decimal, ROUND_HALF_UP, getcontext
from fractions import Fraction
from frac_numeric import sfrac, fr, FR, esc, dec_str, table, _ok, _fail  # noqa: F401

getcontext().prec = 80
MINUS = "&minus;"
TIMES = "&times;"
DIVIDE = "&divide;"


class UErr(Exception):
    """User-input error: message is shown to the student."""


def num(s, label="the number", blank=False):
    s = (s or "").strip().replace("−", "-").replace(",", "").replace("%", "").replace("₦", "")
    if s == "":
        if blank:
            return None
        raise UErr(f"Please fill in {label}.")
    m = re.fullmatch(r"([+-]?\d{1,15}(?:\.\d{1,10})?)\s*/\s*(\d{1,15}(?:\.\d{1,10})?)", s)
    try:
        if m:
            d = sfrac(m.group(2))
            if d == 0:
                raise UErr(f"{label}: the bottom of a fraction cannot be 0.")
            return sfrac(m.group(1)) / d
        return sfrac(s)
    except UErr:
        raise
    except Exception:
        raise UErr(f"{label}: '{esc(s)}' is not a number. Use things like 12, 2.5 or 3/4.")


def pos(s, label, blank=False):
    v = num(s, label, blank)
    if v is not None and v <= 0:
        raise UErr(f"{label} must be bigger than 0.")
    return v


def dec(x, p=2):
    x = Fraction(x)
    q = (Decimal(x.numerator) / Decimal(x.denominator)).quantize(Decimal(1).scaleb(-p), rounding=ROUND_HALF_UP)
    return q


def fm(x, p=2):
    """number -> text with at most p decimals, trailing zeros removed, no sci notation"""
    x = Fraction(x)
    if x.denominator == 1:
        return f"{x.numerator:,}".replace(",", "") if abs(x) < 10 ** 15 else str(x.numerator)
    s = format(dec(x, p), "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def money(x, p=2):
    return format(dec(x, p), "f")


def exact_or_dec(x, p=2):
    """fraction shown stacked if neat, plus decimal"""
    x = Fraction(x)
    if x.denominator == 1:
        return fm(x)
    return f"{fr(x)} = {fm(x, p)}"


def field(name, label, ph="", **kw):
    d = dict(name=name, label=label, placeholder=ph, type="text", half=True)
    d.update(kw)
    return d


def select(name, label, options, **kw):
    d = dict(name=name, label=label, type="select", options=options, half=True)
    d.update(kw)
    return d


def guard(fn):
    def wrapped(d):
        try:
            return fn(d)
        except UErr as e:
            return _fail(str(e))
    wrapped.__name__ = fn.__name__
    return wrapped
