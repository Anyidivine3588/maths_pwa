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
