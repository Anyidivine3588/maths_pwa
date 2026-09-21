"""
Step-by-step maths solvers for WAEC/NECO topics, ported from the
Tkinter desktop app (MathsAssistTk). Each function returns a dict:
    {"steps": [str, ...], "result": str, "ok": bool, "error": str or None}
"""
import re
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
    convert_xor,
)

x, y = sp.symbols("x y")
TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)


def _normalize_expr(s):
    """Make common mobile/typing variations parse correctly instead of failing:
    curly/unicode minus signs, multiplication/division symbols, superscript
    powers, and a stray capital X (only lowercase x is a defined symbol).
    Uses \\uXXXX escape codes throughout (instead of literal special
    characters) so this file stays plain ASCII and can't be corrupted by
    a text editor saving in a non-UTF-8 encoding."""
    if s is None:
        return s
    s = str(s)
    # Unicode dash/minus variants -> plain hyphen-minus
    for ch in ("\u2012", "\u2013", "\u2014", "\u2015", "\u2212", "\u2010"):
        s = s.replace(ch, "-")
    # Multiplication / division symbols
    s = s.replace("\u00d7", "*").replace("\u00f7", "/")
    # Superscript digits -> ^digit  (e.g. x\u00b2 -> x^2)
    superscripts = {
        "\u2070": "0", "\u00b9": "1", "\u00b2": "2", "\u00b3": "3", "\u2074": "4",
        "\u2075": "5", "\u2076": "6", "\u2077": "7", "\u2078": "8", "\u2079": "9",
    }
    for sup, digit in superscripts.items():
        s = s.replace(sup, f"^{digit}")
    # A lone capital X is almost always meant to be the variable x
    s = re.sub(r"(?<![A-Za-z])X(?![A-Za-z])", "x", s)
    return s.strip()


def _mathstr(obj):
    """String-format a sympy value using the radical symbol instead of the word 'sqrt'."""
    return str(obj).replace("sqrt(", "\u221a(")


def _parse(expr_str, local_syms=None):
    syms = local_syms or {"x": x, "y": y}
    return parse_expr(_normalize_expr(expr_str), local_dict=syms, transformations=TRANSFORMS)


def _fail(msg):
    return {"steps": [], "result": None, "ok": False, "error": msg}


def _ok(steps, result):
    return {"steps": steps, "result": result, "ok": True, "error": None}


def _require(value, label):
    """Raise a clear, friendly error if a required field was left blank."""
    if value is None or str(value).strip() == "":
        raise _MissingInput(f"Please enter a value for {label} before solving.")
    return str(value).strip()


class _MissingInput(Exception):
    pass


# ---------------------------------------------------------------- ALGEBRA --

def solve_quadratic(expr_str):
    try:
        expr_str = _require(expr_str, "the equation")
        expr = _parse(expr_str)
        eq = sp.Eq(expr, 0)
        poly = sp.Poly(expr, x)
        if poly.degree() != 2:
            return _fail("That isn't a quadratic (degree must be 2).")
        a, b, c = poly.all_coeffs()

        def fmt_sub(m, n):
            """Format 'm - n' without an ugly double negative like '9 - -40'."""
            return f"{m} + {-n}" if n < 0 else f"{m} - {n}"

        steps = [f"Standard form: {a}x^2 + ({b})x + ({c}) = 0  (a = {a}, b = {b}, c = {c})"]
        steps.append("Using the quadratic formula (the \"almighty formula\"):")
        steps.append("x = [ -b +/- \u221a(b^2 - 4ac) ] / 2a")

        disc = sp.simplify(b**2 - 4*a*c)
        steps.append(f"Substitute a = {a}, b = {b}, c = {c}:")
        steps.append(f"x = [ -({b}) +/- \u221a( ({b})^2 - 4({a})({c}) ) ] / 2({a})")
        steps.append(f"x = [ {-b} +/- \u221a( {fmt_sub(b**2, 4*a*c)} ) ] / {2*a}")
        steps.append(f"b^2 - 4ac = {disc}   (this part under the root is called the discriminant)")

        if disc > 0:
            steps.append("Since the discriminant is positive, there are two distinct real roots.")
        elif disc == 0:
            steps.append("Since the discriminant is zero, there is one repeated real root.")
        else:
            steps.append("Since the discriminant is negative, the roots are complex (not real numbers).")

        sqrt_disc = sp.sqrt(disc)
        steps.append(f"x = [ {-b} +/- \u221a({disc}) ] / {2*a}")
        simplified_sqrt = sp.nsimplify(sqrt_disc)
        if simplified_sqrt != sqrt_disc or disc >= 0:
            steps.append(f"\u221a({disc}) = {_mathstr(simplified_sqrt)}")

        # Compute the "+" and "-" roots directly (rather than trusting the
        # order sympy's solve() happens to return them in) so the working
        # shown always matches the +/- sign actually used.
        r_plus = sp.nsimplify(sp.simplify((-b + sqrt_disc) / (2 * a)))
        r_minus = sp.nsimplify(sp.simplify((-b - sqrt_disc) / (2 * a)))

        def fmt_root(r):
            return _mathstr(r) + ("" if r.is_real is False or r.is_integer else f"  (~= {sp.N(r, 4)})")

        if disc == 0:
            steps.append(f"x = [ {-b} + \u221a({disc}) ] / {2*a}  =  {fmt_root(r_plus)}")
            result = f"x = {_mathstr(r_plus)}"
        else:
            steps.append(f"x = [ {-b} + \u221a({disc}) ] / {2*a}  =  {fmt_root(r_plus)}")
            steps.append(f"x = [ {-b} - \u221a({disc}) ] / {2*a}  =  {fmt_root(r_minus)}")
            result = f"x = {_mathstr(r_plus)}, x = {_mathstr(r_minus)}"

        return _ok(steps, result)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not parse/solve: {e}")


def solve_linear(expr_str):
    try:
        expr_str = _require(expr_str, "the equation")
        if "=" in expr_str:
            lhs_s, rhs_s = expr_str.split("=", 1)
            lhs_expr = _parse(lhs_s)
            rhs_expr = _parse(rhs_s)
        else:
            lhs_expr = _parse(expr_str)
            rhs_expr = sp.Integer(0)

        combined = sp.expand(lhs_expr - rhs_expr)
        poly = sp.Poly(combined, x)
        if poly.degree() > 1:
            return _fail("That isn't linear in x (highest power of x must be 1).")
        if poly.degree() < 1:
            return _fail("There's no x term to solve for -- check the equation.")

        lhs_terms = sp.expand(lhs_expr).as_coefficients_dict()
        rhs_terms = sp.expand(rhs_expr).as_coefficients_dict()
        a_l = lhs_terms.get(x, sp.Integer(0))
        b_l = lhs_terms.get(sp.Integer(1), sp.Integer(0))
        a_r = rhs_terms.get(x, sp.Integer(0))
        b_r = rhs_terms.get(sp.Integer(1), sp.Integer(0))

        def fmt_x_term(coef):
            if coef == 1:
                return "x"
            if coef == -1:
                return "-x"
            if getattr(coef, "q", 1) != 1:
                return f"({coef})x"
            return f"{coef}x"

        def join_terms(parts):
            """parts: list of display strings for terms already carrying their
            own sign (e.g. '6x', '-2x'). Joins with proper +/- spacing."""
            if not parts:
                return "0"
            out = parts[0]
            for p in parts[1:]:
                if p.startswith("-"):
                    out += f" - {p[1:]}"
                else:
                    out += f" + {p}"
            return out

        def fmt_eq_side(expr):
            return sp.sstr(expr).replace("*x", "x").replace("* x", "x")

        steps = [f"Equation: {fmt_eq_side(lhs_expr)} = {fmt_eq_side(rhs_expr)}"]

        # Collect like terms: x-terms to the left, numbers to the right.
        # Moving a term to the other side of "=" flips its sign.
        left_parts = [fmt_x_term(a_l)]
        if a_r != 0:
            left_parts.append(fmt_x_term(-a_r))
        right_parts = [str(b_r)] if b_r != 0 or b_l == 0 else []
        if b_l != 0:
            right_parts.append(str(-b_l))
        if not right_parts:
            right_parts = ["0"]

        if a_r != 0 or b_l != 0:
            steps.append("Collect like terms (x-terms on the left, numbers on the right; "
                          "a term's sign flips when it crosses the '='):")
            new_b_preview = sp.simplify(b_r - b_l)
            steps.append(f"{join_terms(left_parts)} = {join_terms(right_parts)} = {new_b_preview}")
        else:
            steps.append(f"Collect like terms: {fmt_x_term(a_l)} = {b_r}")

        new_a = sp.simplify(a_l - a_r)
        new_b = sp.simplify(b_r - b_l)

        if new_a == 0:
            return _fail("No solution -- the x terms cancel out completely.")

        sol = sp.nsimplify(sp.simplify(new_b / new_a))
        if new_a != 1:
            if new_a == -1:
                steps.append(f"Multiply both sides by -1 (to make the x-term positive): x = -({new_b}) = {sol}")
            elif getattr(new_a, "q", 1) != 1:
                recip = 1 / new_a
                steps.append(f"Make x the subject (divide both sides by ({new_a}), same as "
                              f"multiplying by {recip}): x = {new_b} \u00d7 {recip}")
            else:
                divisor_str = f"({new_a})" if new_a < 0 else str(new_a)
                steps.append(f"Make x the subject: {fmt_x_term(new_a)}/{divisor_str} = {new_b}/{divisor_str}")
        if not sol.is_integer:
            steps.append(f"x = {_mathstr(sol)}  (~= {sp.N(sol, 4)})")
        else:
            steps.append(f"x = {sol}")
        return _ok(steps, f"x = {_mathstr(sol)}")
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not parse/solve: {e}")


def solve_simultaneous_linear(eq1_str, eq2_str):
    try:
        eq1_str = _require(eq1_str, "Equation 1")
        eq2_str = _require(eq2_str, "Equation 2")

        def to_eq(s):
            if "=" in s:
                l, r = s.split("=", 1)
                return sp.Eq(_parse(l), _parse(r))
            return sp.Eq(_parse(s), 0)

        eq1, eq2 = to_eq(eq1_str), to_eq(eq2_str)

        def coeffs(eq):
            d = sp.expand(eq.lhs - eq.rhs).as_coefficients_dict()
            a = d.get(x, sp.Integer(0))
            b = d.get(y, sp.Integer(0))
            c = sp.expand(eq.rhs - (eq.lhs - a * x - b * y)).as_coefficients_dict().get(sp.Integer(1), sp.Integer(0))
            # c = the constant that ends up on the right when written as a*x + b*y = c
            c = sp.simplify(-(d.get(sp.Integer(1), sp.Integer(0))))
            return a, b, c

        a1, b1, c1 = coeffs(eq1)
        a2, b2, c2 = coeffs(eq2)

        steps = [
            "Equations:",
            f"  (1) {a1}x + {b1}y = {c1}",
            f"  (2) {a2}x + {b2}y = {c2}",
        ]

        # Eliminate x by default; if x is missing from one equation, eliminate
        # y instead (swap the roles of the two variables in the logic below).
        eliminate_y_instead = (a1 == 0 or a2 == 0)
        if eliminate_y_instead:
            p1, q1, p2, q2 = b1, a1, b2, a2  # p = coeff of variable we DO eliminate, q = the other
            elim_name, keep_name = "y", "x"
        else:
            p1, q1, p2, q2 = a1, b1, a2, b2
            elim_name, keep_name = "x", "y"

        if p1 == 0 or p2 == 0:
            return _fail(f"Can't eliminate {elim_name} -- it's missing from one of the equations "
                         "in a way this solver doesn't handle. Please check the equations.")

        g = sp.gcd(p1, p2)
        k1 = sp.simplify(p2 / g)
        k2 = sp.simplify(p1 / g)

        steps.append(f"To eliminate {elim_name}, multiply equation (1) by {k1} and "
                      f"equation (2) by {k2}, so the {elim_name}-coefficients match:")

        na1, nb1, nc1 = sp.simplify(a1 * k1), sp.simplify(b1 * k1), sp.simplify(c1 * k1)
        na2, nb2, nc2 = sp.simplify(a2 * k2), sp.simplify(b2 * k2), sp.simplify(c2 * k2)
        steps.append(f"  (1) x {k1}: {na1}x + {nb1}y = {nc1}")
        steps.append(f"  (2) x {k2}: {na2}x + {nb2}y = {nc2}")

        steps.append(f"Since the {elim_name}-coefficients now match, subtract equation (1) "
                      f"from equation (2) to eliminate {elim_name}:")

        if eliminate_y_instead:
            other_new1, other_new2, const_new1, const_new2 = na1, na2, nc1, nc2
        else:
            other_new1, other_new2, const_new1, const_new2 = nb1, nb2, nc1, nc2

        diff_other = sp.simplify(other_new2 - other_new1)
        diff_const = sp.simplify(const_new2 - const_new1)
        other_label = "x" if eliminate_y_instead else "y"
        steps.append(f"({other_new2} - {other_new1}){other_label} = {const_new2} - {const_new1}")
        steps.append(f"{diff_other}{other_label} = {diff_const}")

        if diff_other == 0:
            if diff_const == 0:
                return _fail("Infinitely many solutions -- the two equations represent the same line.")
            return _fail("No solution -- the two lines are parallel (never meet).")

        keep_val = sp.nsimplify(sp.simplify(diff_const / diff_other))
        raw_frac = f"{diff_const}/{diff_other}"
        if _mathstr(keep_val) == raw_frac:
            steps.append(f"{keep_name} = {raw_frac}")
        else:
            steps.append(f"{keep_name} = {raw_frac} = {_mathstr(keep_val)}")

        steps.append(f"Substitute {keep_name} = {_mathstr(keep_val)} back into equation (1) to find {elim_name}:")
        if eliminate_y_instead:
            # keep_name is x; substitute into a1*x + b1*y = c1 to find y
            steps.append(f"{a1}({_mathstr(keep_val)}) + {b1}y = {c1}")
            rhs_after = sp.simplify(c1 - a1 * keep_val)
            steps.append(f"{b1}y = {rhs_after}")
            elim_val = sp.nsimplify(sp.simplify(rhs_after / b1))
            xv, yv = keep_val, elim_val
        else:
            # keep_name is y; substitute into a1*x + b1*y = c1 to find x
            steps.append(f"{a1}x + {b1}({_mathstr(keep_val)}) = {c1}")
            rhs_after = sp.simplify(c1 - b1 * keep_val)
            steps.append(f"{a1}x = {rhs_after}")
            elim_val = sp.nsimplify(sp.simplify(rhs_after / a1))
            xv, yv = elim_val, keep_val

        steps.append(f"{elim_name} = {_mathstr(elim_val)}")
        steps.append(f"x = {_mathstr(xv)}, y = {_mathstr(yv)}")
        return _ok(steps, f"x = {_mathstr(xv)}, y = {_mathstr(yv)}")
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not parse/solve: {e}")


def solve_simultaneous_mixed(linear_str, quad_str):
    """One linear, one quadratic -- per WAEC/NECO exam requirement."""
    try:
        linear_str = _require(linear_str, "the linear equation")
        quad_str = _require(quad_str, "the quadratic equation")

        def to_eq(s):
            if "=" in s:
                l, r = s.split("=", 1)
                return sp.Eq(_parse(l), _parse(r))
            return sp.Eq(_parse(s), 0)

        eq_lin, eq_quad = to_eq(linear_str), to_eq(quad_str)
        steps = [
            "Equations:",
            f"  Linear:    {sp.sstr(eq_lin.lhs)} = {sp.sstr(eq_lin.rhs)}",
            f"  Quadratic: {sp.sstr(eq_quad.lhs)} = {sp.sstr(eq_quad.rhs)}",
        ]
        y_expr = sp.solve(eq_lin, y)
        if y_expr:
            y_expr = y_expr[0]
            steps.append(f"Make y the subject of the linear equation: y = {_mathstr(y_expr)}")
            substituted = sp.Eq((eq_quad.lhs - eq_quad.rhs).subs(y, y_expr), 0)
            steps.append(f"Substitute this into the quadratic equation: {_mathstr(sp.simplify(substituted.lhs))} = 0")
            xs = sp.solve(substituted, x)
            steps.append("Solve this quadratic for x, then substitute each x-value back "
                          "into y = " + _mathstr(y_expr) + " to find the matching y-value:")
            pairs = [(xv, sp.simplify(y_expr.subs(x, xv))) for xv in xs]
        else:
            sol = sp.solve([eq_lin, eq_quad], [x, y])
            pairs = sol if isinstance(sol, list) else [sol]
        for xv, yv in pairs:
            steps.append(f"x = {_mathstr(xv)}, y = {_mathstr(yv)}")
        result = "; ".join(f"(x={_mathstr(xv)}, y={_mathstr(yv)})" for xv, yv in pairs)
        return _ok(steps, result)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not parse/solve: {e}")


# ---------------------------------------------------------------- GEOMETRY --

def area_perimeter(shape, **vals):
    try:
        v = {k: sp.nsimplify(val) for k, val in vals.items() if val not in (None, "")}
        steps, result = [], {}

        if shape == "rectangle":
            l, w = v["length"], v["width"]
            area = l * w
            perim = 2 * (l + w)
            steps = [f"Area = l * w = {l} * {w} = {area}",
                     f"Perimeter = 2(l + w) = 2({l} + {w}) = {perim}"]
            result = {"Area": area, "Perimeter": perim}

        elif shape == "square":
            s = v["side"]
            steps = [f"Area = s^2 = {s}^2 = {s**2}", f"Perimeter = 4s = 4*{s} = {4*s}"]
            result = {"Area": s**2, "Perimeter": 4 * s}

        elif shape == "triangle":
            a, b, c = v["a"], v["b"], v["c"]
            s = sp.Rational(1, 2) * (a + b + c)
            area = sp.sqrt(s * (s - a) * (s - b) * (s - c))
            steps = [
                f"Heron's formula: s = (a+b+c)/2 = ({a}+{b}+{c})/2 = {s}",
                f"Area = \u221a[s(s-a)(s-b)(s-c)] = \u221a[{s}({s}-{a})({s}-{b})({s}-{c})] = {_mathstr(sp.nsimplify(area))}",
                f"Perimeter = a+b+c = {a+b+c}",
            ]
            result = {"Area": sp.N(area, 4), "Perimeter": a + b + c}

        elif shape == "circle":
            r = v["radius"]
            area = sp.pi * r**2
            circ = 2 * sp.pi * r
            steps = [f"Area = pir^2 = pi*{r}^2 = {area} ~= {sp.N(area,4)}",
                     f"Circumference = 2pir = 2pi*{r} = {circ} ~= {sp.N(circ,4)}"]
            result = {"Area": sp.N(area, 4), "Circumference": sp.N(circ, 4)}

        elif shape == "parallelogram":
            b, h = v["base"], v["height"]
            steps = [f"Area = base * height = {b} * {h} = {b*h}"]
            result = {"Area": b * h}

        elif shape == "trapezium":
            a, b, h = v["a"], v["b"], v["height"]
            area = sp.Rational(1, 2) * (a + b) * h
            steps = [f"Area = 1/2(a+b)h = 1/2({a}+{b})*{h} = {area}"]
            result = {"Area": area}

        elif shape == "rhombus":
            d1, d2 = v["d1"], v["d2"]
            area = sp.Rational(1, 2) * d1 * d2
            steps = [f"Area = 1/2 d1d2 = 1/2*{d1}*{d2} = {area}"]
            result = {"Area": area}

        elif shape == "cone":
            r, h = v["radius"], v["height"]
            l = sp.sqrt(r**2 + h**2)
            vol = sp.Rational(1, 3) * sp.pi * r**2 * h
            csa = sp.pi * r * l
            tsa = csa + sp.pi * r**2
            steps = [
                f"Slant height, l = \u221a(r^2+h^2) = \u221a({r}^2+{h}^2) = {sp.N(l,4)}",
                f"Volume = 1/3pir^2h = 1/3pi*{r}^2*{h} ~= {sp.N(vol,4)}",
                f"Curved surface area = pirl = pi*{r}*{sp.N(l,4)} ~= {sp.N(csa,4)}",
                f"Total surface area = pirl + pir^2 ~= {sp.N(tsa,4)}",
            ]
            result = {"Volume": sp.N(vol, 4), "Curved SA": sp.N(csa, 4), "Total SA": sp.N(tsa, 4)}

        elif shape == "cylinder":
            r, h = v["radius"], v["height"]
            vol = sp.pi * r**2 * h
            csa = 2 * sp.pi * r * h
            tsa = csa + 2 * sp.pi * r**2
            steps = [
                f"Volume = pir^2h = pi*{r}^2*{h} ~= {sp.N(vol,4)}",
                f"Curved surface area = 2pirh = 2pi*{r}*{h} ~= {sp.N(csa,4)}",
                f"Total surface area = 2pirh + 2pir^2 ~= {sp.N(tsa,4)}",
            ]
            result = {"Volume": sp.N(vol, 4), "Curved SA": sp.N(csa, 4), "Total SA": sp.N(tsa, 4)}
        else:
            return _fail("Unknown shape.")

        result_str = ", ".join(f"{k} = {val}" for k, val in result.items())
        return _ok(steps, result_str)
    except KeyError as e:
        return _fail(f"Missing value: {e}")
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not compute: {e}")


def pythagoras(mode, a=None, b=None, c=None):
    try:
        if mode == "hypotenuse":
            a = _require(a, "leg a")
            b = _require(b, "leg b")
        else:
            a = _require(a, "the known leg")
            c = _require(c, "the hypotenuse")
        a = sp.nsimplify(a) if a not in (None, "") else None
        b = sp.nsimplify(b) if b not in (None, "") else None
        c = sp.nsimplify(c) if c not in (None, "") else None
        if mode == "hypotenuse":
            h = sp.sqrt(a**2 + b**2)
            steps = [f"c^2 = a^2 + b^2 = {a}^2 + {b}^2 = {a**2 + b**2}",
                     f"c = \u221a{a**2+b**2} ~= {sp.N(h,4)}"]
            return _ok(steps, f"c ~= {sp.N(h, 4)}")
        else:  # find a leg
            known, hyp = (a, c) if a is not None else (b, c)
            leg = sp.sqrt(hyp**2 - known**2)
            label = "a" if a is not None else "b"
            steps = [f"{label}^2 = c^2 - known^2 = {hyp}^2 - {known}^2 = {hyp**2 - known**2}",
                     f"{label} = \u221a{hyp**2-known**2} ~= {sp.N(leg,4)}"]
            return _ok(steps, f"{label} ~= {sp.N(leg, 4)}")
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not compute: {e}")


def coordinate_geometry(x1, y1, x2, y2):
    try:
        x1 = _require(x1, "x1")
        y1 = _require(y1, "y1")
        x2 = _require(x2, "x2")
        y2 = _require(y2, "y2")
        x1, y1, x2, y2 = [sp.nsimplify(v) for v in (x1, y1, x2, y2)]
        dist = sp.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        mid = (sp.Rational(x1 + x2, 1) / 2, sp.Rational(y1 + y2, 1) / 2)
        steps = [
            f"Distance = \u221a[(x2-x1)^2 + (y2-y1)^2] = \u221a[({x2}-{x1})^2 + ({y2}-{y1})^2] ~= {sp.N(dist,4)}",
            f"Midpoint = ((x1+x2)/2, (y1+y2)/2) = (({x1}+{x2})/2, ({y1}+{y2})/2) = ({mid[0]}, {mid[1]})",
        ]
        if x2 != x1:
            grad = sp.Rational(y2 - y1, x2 - x1) if (y2 - y1) == int(y2 - y1) and (x2 - x1) == int(x2 - x1) else (y2 - y1) / (x2 - x1)
            steps.append(f"Gradient, m = (y2-y1)/(x2-x1) = ({y2}-{y1})/({x2}-{x1}) = {grad}")
            c_val = sp.simplify(y1 - grad * x1)
            steps.append(f"Line equation: y - {y1} = {grad}(x - {x1})  ->  y = {grad}x + {c_val}")
            result = f"Distance ~= {sp.N(dist,4)}, Midpoint = ({mid[0]}, {mid[1]}), Gradient = {grad}, y = {grad}x + {c_val}"
        else:
            steps.append("Gradient is undefined (vertical line); equation: x = " + str(x1))
            result = f"Distance ~= {sp.N(dist,4)}, Midpoint = ({mid[0]}, {mid[1]}), vertical line x = {x1}"
        return _ok(steps, result)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not compute: {e}")


# ------------------------------------------------------------------ GRAPHS --

def table_of_values(expr_str, x_min, x_max, step=1):
    try:
        expr_str = _require(expr_str, "f(x)")
        x_min = _require(x_min, "x min")
        x_max = _require(x_max, "x max")
        expr = _parse(expr_str, {"x": x})
        xs = []
        val = sp.nsimplify(x_min)
        xmax = sp.nsimplify(x_max)
        st = sp.nsimplify(step)
        while val <= xmax:
            xs.append(val)
            val += st
        rows = []
        for xv in xs:
            yv = expr.subs(x, xv)
            try:
                yv = sp.N(yv, 4)
            except Exception:
                pass
            rows.append({"x": str(xv), "y": str(yv)})
        return _ok([f"Substituting x = {r['x']} into y = {expr}: y = {r['y']}" for r in rows],
                    rows)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not evaluate: {e}")


def plot_functions_png(expr_str, expr2_str=None, x_min=-10, x_max=10,
                        y_min=None, y_max=None, x_scale=None, y_scale=None):
    """Returns a base64-encoded PNG of the plotted function(s).

    x_scale / y_scale set the spacing between gridlines on each axis, so a
    WAEC/NECO-style instruction like "scale of 2cm to 5 units on the x-axis
    and 2cm to 10 units on the y-axis" can be reproduced directly: x_scale=5
    draws a gridline every 5 units on x, y_scale=10 every 10 units on y.
    y_min / y_max let the y-axis be set explicitly instead of auto-fitting,
    matching how exam graph paper is laid out.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MultipleLocator
    import numpy as np
    import io, base64

    try:
        expr_str = _require(expr_str, "f(x)")
        x_min = _require(x_min, "x min")
        x_max = _require(x_max, "x max")
        x_min = float(x_min)
        x_max = float(x_max)
        if x_min >= x_max:
            return _fail("x min must be less than x max.")

        if y_min not in (None, ""):
            y_min = float(y_min)
        else:
            y_min = None
        if y_max not in (None, ""):
            y_max = float(y_max)
        else:
            y_max = None
        if y_min is not None and y_max is not None and y_min >= y_max:
            return _fail("y min must be less than y max.")

        if x_scale not in (None, ""):
            x_scale = float(x_scale)
            if x_scale <= 0:
                return _fail("x scale (gridline spacing) must be a positive number.")
        else:
            x_scale = None
        if y_scale not in (None, ""):
            y_scale = float(y_scale)
            if y_scale <= 0:
                return _fail("y scale (gridline spacing) must be a positive number.")
        else:
            y_scale = None
    except _MissingInput as e:
        return _fail(str(e))
    except ValueError:
        return _fail("x min, x max, y min, y max, x scale and y scale must all be numbers.")

    fig, ax = plt.subplots(figsize=(6, 5))
    xs = np.linspace(x_min, x_max, 400)

    def safe_eval(estr):
        expr = _parse(estr, {"x": x})
        f = sp.lambdify(x, expr, "numpy")
        with np.errstate(all="ignore"):
            ys = f(xs)
        return np.array(ys, dtype=float)

    intersection_note = None
    try:
        ys1 = safe_eval(expr_str)
        ax.plot(xs, ys1, label=f"y = {expr_str}", color="#4f46e5")
        if expr2_str:
            ys2 = safe_eval(expr2_str)
            ax.plot(xs, ys2, label=f"y = {expr2_str}", color="#e11d48")
            expr1 = _parse(expr_str, {"x": x})
            expr2 = _parse(expr2_str, {"x": x})
            sols = sp.solve(sp.Eq(expr1, expr2), x)
            pts = []
            for s in sols:
                if s.is_real:
                    xv = float(s)
                    if x_min <= xv <= x_max:
                        yv = float(expr1.subs(x, s))
                        pts.append((xv, yv))
            if pts:
                ax.scatter(*zip(*pts), color="black", zorder=5, label="Intersection")
                intersection_note = ", ".join(f"({px:.2f}, {py:.2f})" for px, py in pts)

        ax.set_xlim(x_min, x_max)
        if y_min is not None or y_max is not None:
            # Only one of y_min/y_max given: keep matplotlib's auto value
            # for the side that wasn't specified.
            auto_lo, auto_hi = ax.get_ylim()
            ax.set_ylim(y_min if y_min is not None else auto_lo,
                        y_max if y_max is not None else auto_hi)

        if x_scale:
            ax.xaxis.set_major_locator(MultipleLocator(x_scale))
        if y_scale:
            ax.yaxis.set_major_locator(MultipleLocator(y_scale))

        ax.axhline(0, color="gray", linewidth=0.8)
        ax.axvline(0, color="gray", linewidth=0.8)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend()
        ax.set_xlabel("x")
        ax.set_ylabel("y")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode("ascii")
        return _ok([], {"image": img_b64, "intersection": intersection_note})
    except Exception as e:
        plt.close(fig)
        return _fail(f"Could not plot: {e}")


# --------------------------------------------------------------- SEQUENCES --

def ap_nth_term(a, d, n):
    """Arithmetic Progression: nth term Tn = a + (n-1)d."""
    try:
        a = sp.nsimplify(_require(a, "first term (a)"))
        d = sp.nsimplify(_require(d, "common difference (d)"))
        n = sp.nsimplify(_require(n, "term number (n)"))
        steps = [
            "Formula for the nth term of an Arithmetic Progression (AP): Tn = a + (n - 1)d",
            f"Substitute a = {a}, d = {d}, n = {n}:",
            f"T{n} = {a} + ({n} - 1)({d})",
        ]
        tn = sp.simplify(a + (n - 1) * d)
        steps.append(f"T{n} = {a} + ({n-1})({d})")
        steps.append(f"T{n} = {_mathstr(tn)}")
        return _ok(steps, f"T{n} = {_mathstr(tn)}")
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def ap_sum(a, d, n):
    """Arithmetic Progression: sum of first n terms, Sn = n/2 * (2a + (n-1)d)."""
    try:
        a = sp.nsimplify(_require(a, "first term (a)"))
        d = sp.nsimplify(_require(d, "common difference (d)"))
        n = sp.nsimplify(_require(n, "number of terms (n)"))
        steps = [
            "Formula for the sum of the first n terms of an AP: Sn = (n/2)[2a + (n - 1)d]",
            f"Substitute a = {a}, d = {d}, n = {n}:",
            f"S{n} = ({n}/2)[2({a}) + ({n} - 1)({d})]",
        ]
        inner = sp.simplify(2 * a + (n - 1) * d)
        steps.append(f"S{n} = ({n}/2)[{2*a} + ({n-1})({d})]")
        steps.append(f"S{n} = ({n}/2)({inner})")
        sn = sp.simplify(sp.Rational(1, 2) * n * inner)
        steps.append(f"S{n} = {_mathstr(sn)}")
        return _ok(steps, f"S{n} = {_mathstr(sn)}")
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def gp_nth_term(a, r, n):
    """Geometric Progression: nth term Tn = a * r^(n-1)."""
    try:
        a = sp.nsimplify(_require(a, "first term (a)"))
        r = sp.nsimplify(_require(r, "common ratio (r)"))
        n = sp.nsimplify(_require(n, "term number (n)"))
        steps = [
            "Formula for the nth term of a Geometric Progression (GP): Tn = a x r^(n-1)",
            f"Substitute a = {a}, r = {r}, n = {n}:",
            f"T{n} = {a} x ({r})^({n} - 1)",
            f"T{n} = {a} x ({r})^{n-1}",
        ]
        tn = sp.simplify(a * r ** (n - 1))
        tn = sp.nsimplify(tn)
        steps.append(f"T{n} = {_mathstr(tn)}")
        return _ok(steps, f"T{n} = {_mathstr(tn)}")
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def gp_sum(a, r, n):
    """Geometric Progression: sum of first n terms."""
    try:
        a = sp.nsimplify(_require(a, "first term (a)"))
        r = sp.nsimplify(_require(r, "common ratio (r)"))
        n = sp.nsimplify(_require(n, "number of terms (n)"))
        if r == 1:
            sn = sp.simplify(a * n)
            steps = [
                "Since r = 1, every term equals a, so Sn = n x a",
                f"S{n} = {n} x {a} = {_mathstr(sn)}",
            ]
            return _ok(steps, f"S{n} = {_mathstr(sn)}")

        if abs(r) > 1:
            steps = [
                "Since |r| > 1, use: Sn = a(r^n - 1) / (r - 1)",
                f"Substitute a = {a}, r = {r}, n = {n}:",
                f"S{n} = {a}(({r})^{n} - 1) / ({r} - 1)",
            ]
            rn = sp.simplify(r ** n)
            steps.append(f"({r})^{n} = {rn}")
            sn = sp.simplify(a * (rn - 1) / (r - 1))
        else:
            steps = [
                "Since |r| < 1, use: Sn = a(1 - r^n) / (1 - r)",
                f"Substitute a = {a}, r = {r}, n = {n}:",
                f"S{n} = {a}(1 - ({r})^{n}) / (1 - {r})",
            ]
            rn = sp.simplify(r ** n)
            steps.append(f"({r})^{n} = {rn}")
            sn = sp.simplify(a * (1 - rn) / (1 - r))

        sn = sp.nsimplify(sn)
        steps.append(f"S{n} = {_mathstr(sn)}")
        if not sn.is_integer:
            steps.append(f"S{n} \u2248 {sp.N(sn, 6)}")
        return _ok(steps, f"S{n} = {_mathstr(sn)}")
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def gp_sum_infinity(a, r):
    """Geometric Progression: sum to infinity, S_inf = a / (1 - r), valid only for |r| < 1."""
    try:
        a = sp.nsimplify(_require(a, "first term (a)"))
        r = sp.nsimplify(_require(r, "common ratio (r)"))
        if abs(r) >= 1:
            return _fail("Sum to infinity only exists when -1 < r < 1 (the terms must keep "
                          f"shrinking). Here r = {r}, so this series does not converge.")
        steps = [
            "Since -1 < r < 1, the sum to infinity is: S_inf = a / (1 - r)",
            f"Substitute a = {a}, r = {r}:",
            f"S_inf = {a} / (1 - {r})",
        ]
        denom = sp.simplify(1 - r)
        s_inf = sp.nsimplify(sp.simplify(a / denom))
        denom_str = f"({denom})" if denom < 0 or getattr(denom, "q", 1) != 1 else str(denom)
        steps.append(f"S_inf = {a} / {denom_str}")
        steps.append(f"S_inf = {_mathstr(s_inf)}")
        return _ok(steps, f"S_inf = {_mathstr(s_inf)}")
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


# -------------------------------------------------------------------- SETS --

def _parse_set(s, label):
    """Parse a comma/space separated list like '1,2,3' or 'a,b,c' into a set of strings."""
    s = _require(s, label)
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1]
    parts = [p.strip() for p in re.split(r"[,\s]+", s) if p.strip() != ""]
    return set(parts), parts  # set (for ops) and ordered list (for readable display)


def set_operations(set_a_str, set_b_str, universal_str=None):
    """Union, intersection, differences, and (if a universal set is given) complements."""
    try:
        A, a_order = _parse_set(set_a_str, "Set A")
        B, b_order = _parse_set(set_b_str, "Set B")
        steps = [f"A = {{{', '.join(a_order)}}}", f"B = {{{', '.join(b_order)}}}"]

        def show(label_expr, s):
            ordered = sorted(s, key=lambda v: (len(v), v))
            return f"{label_expr} = {{{', '.join(ordered) if ordered else ''}}}" + (
                "  (the empty set)" if not ordered else "")

        union = A | B
        inter = A & B
        a_only = A - B
        b_only = B - A

        steps.append("Union (elements in A or B or both):")
        steps.append(show("A \u222a B", union))
        steps.append("Intersection (elements in both A and B):")
        steps.append(show("A \u2229 B", inter))
        steps.append("A only (in A but not B):")
        steps.append(show("A - B", a_only))
        steps.append("B only (in B but not A):")
        steps.append(show("B - A", b_only))

        result_lines = [
            f"A \u222a B = {{{', '.join(sorted(union, key=lambda v: (len(v), v)))}}}",
            f"A \u2229 B = {{{', '.join(sorted(inter, key=lambda v: (len(v), v)))}}}",
        ]

        if universal_str not in (None, ""):
            U, u_order = _parse_set(universal_str, "the universal set")
            steps.append(f"U = {{{', '.join(u_order)}}}")
            a_comp = U - A
            b_comp = U - B
            steps.append("Complement of A (in U but not in A):")
            steps.append(show("A'", a_comp))
            steps.append("Complement of B (in U but not in B):")
            steps.append(show("B'", b_comp))
            result_lines.append(f"A' = {{{', '.join(sorted(a_comp, key=lambda v: (len(v), v)))}}}")
            result_lines.append(f"B' = {{{', '.join(sorted(b_comp, key=lambda v: (len(v), v)))}}}")

        return _ok(steps, "; ".join(result_lines))
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def venn_two_set(n_u=None, n_a=None, n_b=None, n_both=None, n_neither=None):
    """2-set Venn diagram word problem. Exactly one of the five quantities
    should be left blank; the others are used to solve for it via
    inclusion-exclusion, then the full breakdown is shown."""
    try:
        vals = {"n_u": n_u, "n_a": n_a, "n_b": n_b, "n_both": n_both, "n_neither": n_neither}
        labels = {"n_u": "n(U) - total", "n_a": "n(A)", "n_b": "n(B)",
                  "n_both": "n(A and B) - both", "n_neither": "n(neither)"}
        known = {k: sp.nsimplify(v) for k, v in vals.items() if v not in (None, "")}
        missing = [k for k, v in vals.items() if v in (None, "")]
        if len(missing) == 0:
            missing_key = None
        elif len(missing) == 1:
            missing_key = missing[0]
        else:
            return _fail("Please leave exactly ONE of the five values blank -- that's the one "
                         "this solver will work out for you.")

        U, Av, Bv, Both, Neither = sp.symbols("U A B Both Neither")
        symmap = {"n_u": U, "n_a": Av, "n_b": Bv, "n_both": Both, "n_neither": Neither}

        steps = ["Using: n(A \u222a B) = n(A) + n(B) - n(A and B), and n(U) = n(A \u222a B) + n(neither)"]

        if missing_key:
            eq1 = sp.Eq(symmap["n_u"] - symmap["n_neither"], symmap["n_a"] + symmap["n_b"] - symmap["n_both"])
            subs = {symmap[k]: v for k, v in known.items()}
            eq1_sub = eq1.subs(subs)
            steps.append(f"We're missing {labels[missing_key]}, so solve for it from the others:")
            sol = sp.solve(eq1_sub, symmap[missing_key])
            if not sol:
                return _fail("Could not solve for the missing value with the numbers given -- "
                             "please check they're consistent.")
            missing_val = sp.simplify(sol[0])
            steps.append(f"{labels[missing_key]} = {_mathstr(missing_val)}")
            known[missing_key] = missing_val

        n_u_v, n_a_v, n_b_v, n_both_v = known["n_u"], known["n_a"], known["n_b"], known["n_both"]
        n_neither_v = known["n_neither"]
        a_only = sp.simplify(n_a_v - n_both_v)
        b_only = sp.simplify(n_b_v - n_both_v)
        union = sp.simplify(n_a_v + n_b_v - n_both_v)

        steps.append(f"Only A (A but not B): n(A) - n(A and B) = {n_a_v} - {n_both_v} = {a_only}")
        steps.append(f"Only B (B but not A): n(B) - n(A and B) = {n_b_v} - {n_both_v} = {b_only}")
        steps.append(f"n(A \u222a B) = {n_a_v} + {n_b_v} - {n_both_v} = {union}")
        steps.append(f"Check: n(U) = n(A \u222a B) + n(neither) = {union} + {n_neither_v} = {sp.simplify(union+n_neither_v)}")

        result = (f"n(U)={n_u_v}, n(A)={n_a_v}, n(B)={n_b_v}, both={n_both_v}, "
                  f"only A={a_only}, only B={b_only}, neither={n_neither_v}")
        return _ok(steps, result)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def venn_three_set(n_u=None, n_a=None, n_b=None, n_c=None,
                    n_ab=None, n_ac=None, n_bc=None, n_abc=None):
    """3-set Venn diagram word problem, using inclusion-exclusion.
    n_ab/n_ac/n_bc = number in each PAIR of sets (including the ones also in
    the third set); n_abc = number in all three. Exactly one value blank."""
    try:
        vals = {"n_u": n_u, "n_a": n_a, "n_b": n_b, "n_c": n_c,
                "n_ab": n_ab, "n_ac": n_ac, "n_bc": n_bc, "n_abc": n_abc}
        labels = {"n_u": "n(U)", "n_a": "n(A)", "n_b": "n(B)", "n_c": "n(C)",
                  "n_ab": "n(A and B)", "n_ac": "n(A and C)", "n_bc": "n(B and C)",
                  "n_abc": "n(A and B and C)"}
        known = {k: sp.nsimplify(v) for k, v in vals.items() if v not in (None, "")}
        missing = [k for k, v in vals.items() if v in (None, "")]
        if len(missing) != 1:
            return _fail("Please leave exactly ONE of the eight values blank -- that's the one "
                         "this solver will work out for you.")
        missing_key = missing[0]

        syms = {k: sp.Symbol(k) for k in vals}
        union_expr = (syms["n_a"] + syms["n_b"] + syms["n_c"]
                      - syms["n_ab"] - syms["n_ac"] - syms["n_bc"] + syms["n_abc"])
        eq = sp.Eq(syms["n_u"], union_expr)

        steps = ["Using: n(A \u222a B \u222a C) = n(A)+n(B)+n(C) - n(A and B) - n(A and C) - "
                 "n(B and C) + n(A and B and C), and this equals n(U) "
                 "(assuming everyone in U is in at least one of A, B, C):"]
        subs = {syms[k]: v for k, v in known.items()}
        eq_sub = eq.subs(subs)
        steps.append(f"We're missing {labels[missing_key]}, so solve for it from the rest:")
        sol = sp.solve(eq_sub, syms[missing_key])
        if not sol:
            return _fail("Could not solve for the missing value -- please check the numbers given.")
        missing_val = sp.simplify(sol[0])
        steps.append(f"{labels[missing_key]} = {_mathstr(missing_val)}")
        known[missing_key] = missing_val

        only_a = sp.simplify(known["n_a"] - known["n_ab"] - known["n_ac"] + known["n_abc"])
        only_b = sp.simplify(known["n_b"] - known["n_ab"] - known["n_bc"] + known["n_abc"])
        only_c = sp.simplify(known["n_c"] - known["n_ac"] - known["n_bc"] + known["n_abc"])
        steps.append(f"Only A: n(A) - n(A and B) - n(A and C) + n(A and B and C) = {only_a}")
        steps.append(f"Only B: n(B) - n(A and B) - n(B and C) + n(A and B and C) = {only_b}")
        steps.append(f"Only C: n(C) - n(A and C) - n(B and C) + n(A and B and C) = {only_c}")

        result = (f"n(U)={known['n_u']}, only A={only_a}, only B={only_b}, only C={only_c}, "
                  f"n(A and B and C)={known['n_abc']}")
        return _ok(steps, result)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


# ------------------------------------------------------------- TRIGONOMETRY --

def _deg_sin(deg):
    return sp.sin(sp.rad(deg))


def _deg_cos(deg):
    return sp.cos(sp.rad(deg))


def _deg_tan(deg):
    return sp.tan(sp.rad(deg))


def right_triangle(opposite=None, adjacent=None, hypotenuse=None, angle=None):
    """Solve a right-angled triangle given exactly two of the four values
    (opposite, adjacent, hypotenuse, angle in degrees) using SOHCAHTOA."""
    try:
        vals = {"opposite": opposite, "adjacent": adjacent, "hypotenuse": hypotenuse, "angle": angle}
        known = {k: v for k, v in vals.items() if v not in (None, "")}
        if len(known) != 2:
            return _fail("Please provide exactly TWO of: opposite, adjacent, hypotenuse, angle "
                         "-- the solver will find the rest.")
        known = {k: sp.nsimplify(v) for k, v in known.items()}

        steps = ["SOHCAHTOA: sin = opposite/hypotenuse, cos = adjacent/hypotenuse, tan = opposite/adjacent"]
        opp, adj, hyp, ang = (known.get("opposite"), known.get("adjacent"),
                               known.get("hypotenuse"), known.get("angle"))

        have = set(known.keys())
        if have == {"opposite", "adjacent"}:
            hyp = sp.sqrt(opp ** 2 + adj ** 2)
            steps.append(f"Find the hypotenuse with Pythagoras: hyp = \u221a(opp^2 + adj^2) = "
                          f"\u221a({opp}^2 + {adj}^2) = {_mathstr(sp.simplify(hyp))}")
            hyp = sp.simplify(hyp)
            ang = sp.deg(sp.atan(opp / adj))
            steps.append(f"tan(angle) = opposite/adjacent = {opp}/{adj}")
            steps.append(f"angle = tan^-1({opp}/{adj}) = {sp.N(ang, 4)} degrees")
        elif have == {"opposite", "hypotenuse"}:
            adj = sp.sqrt(hyp ** 2 - opp ** 2)
            steps.append(f"Find the adjacent side with Pythagoras: adj = \u221a(hyp^2 - opp^2) = "
                          f"\u221a({hyp}^2 - {opp}^2) = {_mathstr(sp.simplify(adj))}")
            adj = sp.simplify(adj)
            ang = sp.deg(sp.asin(opp / hyp))
            steps.append(f"sin(angle) = opposite/hypotenuse = {opp}/{hyp}")
            steps.append(f"angle = sin^-1({opp}/{hyp}) = {sp.N(ang, 4)} degrees")
        elif have == {"adjacent", "hypotenuse"}:
            opp = sp.sqrt(hyp ** 2 - adj ** 2)
            steps.append(f"Find the opposite side with Pythagoras: opp = \u221a(hyp^2 - adj^2) = "
                          f"\u221a({hyp}^2 - {adj}^2) = {_mathstr(sp.simplify(opp))}")
            opp = sp.simplify(opp)
            ang = sp.deg(sp.acos(adj / hyp))
            steps.append(f"cos(angle) = adjacent/hypotenuse = {adj}/{hyp}")
            steps.append(f"angle = cos^-1({adj}/{hyp}) = {sp.N(ang, 4)} degrees")
        elif have == {"opposite", "angle"}:
            hyp = sp.simplify(opp / _deg_sin(ang))
            steps.append(f"sin({ang}) = opposite/hypotenuse, so hypotenuse = opposite/sin({ang})")
            steps.append(f"hypotenuse = {opp}/sin({ang}) = {sp.N(hyp, 4)}")
            adj = sp.simplify(opp / _deg_tan(ang))
            steps.append(f"adjacent = opposite/tan({ang}) = {opp}/tan({ang}) = {sp.N(adj, 4)}")
        elif have == {"adjacent", "angle"}:
            hyp = sp.simplify(adj / _deg_cos(ang))
            steps.append(f"cos({ang}) = adjacent/hypotenuse, so hypotenuse = adjacent/cos({ang})")
            steps.append(f"hypotenuse = {adj}/cos({ang}) = {sp.N(hyp, 4)}")
            opp = sp.simplify(adj * _deg_tan(ang))
            steps.append(f"opposite = adjacent x tan({ang}) = {adj} x tan({ang}) = {sp.N(opp, 4)}")
        elif have == {"hypotenuse", "angle"}:
            opp = sp.simplify(hyp * _deg_sin(ang))
            steps.append(f"opposite = hypotenuse x sin({ang}) = {hyp} x sin({ang}) = {sp.N(opp, 4)}")
            adj = sp.simplify(hyp * _deg_cos(ang))
            steps.append(f"adjacent = hypotenuse x cos({ang}) = {hyp} x cos({ang}) = {sp.N(adj, 4)}")
        else:
            return _fail("That combination isn't supported -- please give exactly two of "
                         "opposite, adjacent, hypotenuse, angle.")

        def fmt_val(v):
            v = sp.N(v, 4)
            return str(v)

        result = f"opposite \u2248 {fmt_val(opp)}, adjacent \u2248 {fmt_val(adj)}, hypotenuse \u2248 {fmt_val(hyp)}, angle \u2248 {fmt_val(ang)} degrees"
        return _ok(steps, result)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def sine_rule(a=None, A=None, b=None, B=None, c=None, C=None):
    """Sine rule: a/sin(A) = b/sin(B) = c/sin(C). Provide any 3 of the 6
    values (a full side/angle pair plus one more value) to find the rest."""
    try:
        vals = {"a": a, "A": A, "b": b, "B": B, "c": c, "C": C}
        known = {k: sp.nsimplify(v) for k, v in vals.items() if v not in (None, "")}
        pairs = [("a", "A"), ("b", "B"), ("c", "C")]
        full_pairs = [p for p in pairs if p[0] in known and p[1] in known]
        if not full_pairs:
            return _fail("Please provide at least one full side/opposite-angle pair "
                         "(e.g. side a and angle A) plus one more known value.")
        side_k, angle_k = full_pairs[0]
        ratio = sp.simplify(known[side_k] / _deg_sin(known[angle_k]))
        steps = [
            "Sine rule: a/sin(A) = b/sin(B) = c/sin(C)",
            f"Using the known pair {side_k} = {known[side_k]}, {angle_k} = {known[angle_k]} degrees:",
            f"{side_k}/sin({angle_k}) = {known[side_k]}/sin({known[angle_k]}) = {sp.N(ratio, 5)}",
        ]
        for s_key, a_key in pairs:
            if s_key == side_k:
                continue
            if s_key in known and a_key not in known:
                # find the angle
                sin_val = sp.simplify(known[s_key] / ratio)
                if abs(sin_val) > 1:
                    return _fail(f"No valid triangle -- sin({a_key}) would have to be {sp.N(sin_val,4)}, "
                                 "which is impossible.")
                ang = sp.deg(sp.asin(sin_val))
                steps.append(f"sin({a_key}) = {s_key}/{ratio_str(ratio)} = {known[s_key]}/{sp.N(ratio,5)} = {sp.N(sin_val,4)}")
                steps.append(f"{a_key} = sin^-1({sp.N(sin_val,4)}) = {sp.N(ang,4)} degrees")
                known[a_key] = ang
            elif a_key in known and s_key not in known:
                # find the side
                side_val = sp.simplify(_deg_sin(known[a_key]) * ratio)
                steps.append(f"{s_key} = sin({a_key}) x {sp.N(ratio,5)} = {sp.N(side_val,4)}")
                known[s_key] = side_val
            elif s_key not in known and a_key not in known:
                # find via angle sum if the other two angles are known
                other_angles = [v for k, v in known.items() if k in ("A", "B", "C")]
                if len(other_angles) == 2:
                    third_angle = sp.simplify(180 - sum(other_angles))
                    steps.append(f"{a_key} = 180 - (sum of the other two angles) = {sp.N(third_angle,4)} degrees")
                    known[a_key] = third_angle
                    side_val = sp.simplify(_deg_sin(known[a_key]) * ratio)
                    steps.append(f"{s_key} = sin({a_key}) x {sp.N(ratio,5)} = {sp.N(side_val,4)}")
                    known[s_key] = side_val

        result_parts = []
        for k in ("a", "A", "b", "B", "c", "C"):
            if k in known:
                v = sp.N(known[k], 4)
                result_parts.append(f"{k}={v}{' deg' if k in ('A','B','C') else ''}")
        return _ok(steps, ", ".join(result_parts))
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def ratio_str(r):
    return str(sp.N(r, 5))


def cosine_rule(a=None, b=None, c=None, C=None):
    """Cosine rule. Two modes:
    - Given all three sides a, b, c (C left blank): find angle C (opposite side c).
    - Given two sides a, b and the included angle C: find the third side c."""
    try:
        vals = {"a": a, "b": b, "c": c, "C": C}
        known = {k: sp.nsimplify(v) for k, v in vals.items() if v not in (None, "")}
        steps = ["Cosine rule: c^2 = a^2 + b^2 - 2ab.cos(C)   (C is the angle between sides a and b, opposite side c)"]

        if "a" in known and "b" in known and "c" in known and "C" not in known:
            av, bv, cv = known["a"], known["b"], known["c"]
            cosC = sp.simplify((av ** 2 + bv ** 2 - cv ** 2) / (2 * av * bv))
            steps.append("Rearranged to find the angle: cos(C) = (a^2 + b^2 - c^2) / (2ab)")
            steps.append(f"cos(C) = ({av}^2 + {bv}^2 - {cv}^2) / (2 x {av} x {bv})")
            steps.append(f"cos(C) = {sp.N(cosC, 5)}")
            if abs(cosC) > 1:
                return _fail("These three side lengths can't form a real triangle "
                             "(check the values entered).")
            Cang = sp.deg(sp.acos(cosC))
            steps.append(f"C = cos^-1({sp.N(cosC,5)}) = {sp.N(Cang,4)} degrees")
            return _ok(steps, f"C \u2248 {sp.N(Cang,4)} degrees")

        if "a" in known and "b" in known and "C" in known and "c" not in known:
            av, bv, Cv = known["a"], known["b"], known["C"]
            steps.append(f"Substitute a = {av}, b = {bv}, C = {Cv} degrees:")
            steps.append(f"c^2 = {av}^2 + {bv}^2 - 2({av})({bv})cos({Cv})")
            c2 = sp.simplify(av ** 2 + bv ** 2 - 2 * av * bv * _deg_cos(Cv))
            steps.append(f"c^2 = {sp.N(c2, 5)}")
            if c2 < 0:
                return _fail("These values don't form a valid triangle (c^2 came out negative).")
            cv = sp.sqrt(c2)
            steps.append(f"c = \u221a({sp.N(c2,5)}) = {sp.N(cv, 5)}")
            return _ok(steps, f"c \u2248 {sp.N(cv,5)}")

        return _fail("Please provide either all three sides (a, b, c) to find angle C, "
                     "or two sides and the included angle C to find side c.")
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def angle_of_elevation(height=None, distance=None, angle=None):
    """Angle of elevation/depression word problems: a right triangle with
    'height' (opposite) and 'distance' (adjacent), connected by tan."""
    try:
        vals = {"height": height, "distance": distance, "angle": angle}
        known = {k: v for k, v in vals.items() if v not in (None, "")}
        if len(known) != 2:
            return _fail("Please provide exactly TWO of: height, distance, angle.")
        known = {k: sp.nsimplify(v) for k, v in known.items()}

        steps = ["This forms a right triangle where tan(angle) = height / distance"]
        if "height" in known and "distance" in known:
            h, d = known["height"], known["distance"]
            steps.append(f"tan(angle) = {h}/{d}")
            ang = sp.deg(sp.atan(h / d))
            steps.append(f"angle = tan^-1({h}/{d}) = {sp.N(ang,4)} degrees")
            return _ok(steps, f"angle \u2248 {sp.N(ang,4)} degrees")
        elif "height" in known and "angle" in known:
            h, ang = known["height"], known["angle"]
            steps.append(f"tan({ang}) = {h}/distance, so distance = {h}/tan({ang})")
            d = sp.simplify(h / _deg_tan(ang))
            steps.append(f"distance = {sp.N(d,4)}")
            return _ok(steps, f"distance \u2248 {sp.N(d,4)}")
        else:  # distance and angle
            d, ang = known["distance"], known["angle"]
            steps.append(f"tan({ang}) = height/{d}, so height = {d} x tan({ang})")
            h = sp.simplify(d * _deg_tan(ang))
            steps.append(f"height = {sp.N(h,4)}")
            return _ok(steps, f"height \u2248 {sp.N(h,4)}")
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")
