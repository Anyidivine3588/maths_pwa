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


def solve_quadratic_completing_square(expr_str):
    """Solve ax^2+bx+c=0 by completing the square -- works for any quadratic."""
    try:
        expr_str = _require(expr_str, "the equation")
        expr = _parse(expr_str)
        poly = sp.Poly(expr, x)
        if poly.degree() != 2:
            return _fail("That isn't a quadratic (degree must be 2).")
        a, b, c = poly.all_coeffs()

        def signed(val, suffix=""):
            """'+ 5x' or '- 5x' -- for chaining onto an existing term."""
            v = _mathstr(val if val >= 0 else -val)
            if suffix and getattr(val, "q", 1) != 1 and val != 0:
                v = f"({v})"
            if val < 0:
                return f"- {v}{suffix}"
            return f"+ {v}{suffix}"

        def paren_sq(val):
            """'(val)^2' with parens only when actually needed for clarity."""
            v = _mathstr(val)
            if val < 0 or getattr(val, "q", 1) != 1:
                return f"({v})^2"
            return f"{v}^2"

        steps = [f"Standard form: {a}x^2 + ({b})x + ({c}) = 0  (a = {a}, b = {b}, c = {c})"]

        if a != 1:
            steps.append(f"Divide every term by a = {a} so the x^2 coefficient is 1:")
            b_over_a = sp.nsimplify(sp.Rational(b, a)) if b != 0 else sp.Integer(0)
            c_over_a = sp.nsimplify(sp.Rational(c, a))
            steps.append(f"x^2 {signed(b_over_a, 'x')} {signed(c_over_a)} = 0")
        else:
            b_over_a = b
            c_over_a = c

        steps.append("Move the constant to the right-hand side:")
        steps.append(f"x^2 {signed(b_over_a, 'x')} = {_mathstr(-c_over_a)}")

        half = sp.nsimplify(sp.Rational(1, 2) * b_over_a)
        half_sq = sp.nsimplify(half ** 2)
        steps.append(f"Take half of the x-coefficient ({_mathstr(b_over_a)}/2 = {_mathstr(half)}), "
                      f"square it ({paren_sq(half)} = {_mathstr(half_sq)}), and add it to both sides:")
        rhs = sp.nsimplify(sp.simplify(-c_over_a + half_sq))
        steps.append(f"x^2 {signed(b_over_a, 'x')} + {_mathstr(half_sq)} = {_mathstr(-c_over_a)} + {_mathstr(half_sq)}")
        steps.append(f"(x {signed(half)})^2 = {_mathstr(rhs)}")

        if rhs < 0:
            steps.append(f"Since the right-hand side ({_mathstr(rhs)}) is negative, there is no real "
                         "square root -- this equation has no real solutions.")
            return _fail(f"No real solutions -- completing the square gives (x {signed(half)})^2 "
                         f"= {_mathstr(rhs)}, and a square can't be negative.")

        steps.append("Take the square root of both sides:")
        sqrt_rhs = sp.nsimplify(sp.sqrt(rhs))
        steps.append(f"x {signed(half)} = \u00b1\u221a({_mathstr(rhs)}) = \u00b1{_mathstr(sqrt_rhs)}")

        r_plus = sp.nsimplify(sp.simplify(-half + sqrt_rhs))
        r_minus = sp.nsimplify(sp.simplify(-half - sqrt_rhs))
        neg_half = _mathstr(-half)

        def fmt_root(r):
            return _mathstr(r) + ("" if r.is_real is False or r.is_integer else f"  (~= {sp.N(r, 4)})")

        if rhs == 0:
            steps.append(f"x = {neg_half} = {fmt_root(r_plus)}")
            result = f"x = {_mathstr(r_plus)}"
        else:
            steps.append(f"x = {neg_half} {signed(sqrt_rhs)} = {fmt_root(r_plus)}")
            steps.append(f"x = {neg_half} {signed(-sqrt_rhs)} = {fmt_root(r_minus)}")
            result = f"x = {_mathstr(r_plus)}, x = {_mathstr(r_minus)}"

        return _ok(steps, result)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not parse/solve: {e}")


def solve_quadratic_factorisation(expr_str):
    """Solve ax^2+bx+c=0 by factorisation (splitting the middle term),
    for quadratics that factorise nicely over rational numbers."""
    try:
        expr_str = _require(expr_str, "the equation")
        expr = _parse(expr_str)
        poly = sp.Poly(expr, x)
        if poly.degree() != 2:
            return _fail("That isn't a quadratic (degree must be 2).")
        a, b, c = poly.all_coeffs()
        if not (a.is_Integer and b.is_Integer and c.is_Integer):
            return _fail("Factorisation here needs whole-number coefficients -- please try the "
                         "Completing the Square or Formula method instead.")

        steps = [f"Standard form: {a}x^2 + ({b})x + ({c}) = 0  (a = {a}, b = {b}, c = {c})"]

        factored = sp.factor(expr)
        is_factored = isinstance(factored, sp.Mul) or (
            isinstance(factored, sp.Pow) and factored.exp == 2)
        if not is_factored:
            return _fail("This quadratic doesn't factorise nicely over whole numbers -- please "
                         "try the Completing the Square or Formula method instead.")

        ac = a * c
        found = None
        limit = int(abs(ac)) + 1
        for m in range(-limit, limit + 1):
            if m == 0 or ac % m != 0:
                continue
            n = ac // m
            if m + n == b:
                found = (m, n)
                break

        if found:
            m, n = found
            steps.append(f"Find two numbers that multiply to give a x c = ({a})({c}) = {ac} "
                          f"and add to give b = {b}: {m} and {n}")
            m_term = f"+ {m}x" if m >= 0 else f"- {abs(m)}x"
            n_term = f"+ {n}x" if n >= 0 else f"- {abs(n)}x"
            steps.append(f"Split the middle term: {a}x^2 {m_term} {n_term} + ({c}) = 0")
            steps.append("Group in pairs and factorise each group, then factor out the common bracket:")

        def clean(s):
            return str(s).replace("**", "^").replace("*", "")

        steps.append(f"Factorised form: {clean(sp.factor(expr, x))} = 0")

        # Extract the linear factors (handling a repeated/squared factor too)
        if isinstance(factored, sp.Pow):
            factors = [factored.base] * 2
        else:
            factors = []
            for f in factored.args:
                if f.is_number:
                    continue
                if isinstance(f, sp.Pow):
                    factors.extend([f.base] * int(f.exp))
                else:
                    factors.append(f)

        steps.append("Using the zero product rule: if two things multiply to give 0, at least "
                      "one of them must be 0.")

        roots = []
        for f in factors:
            fpoly = sp.Poly(f, x)
            fa, fb = fpoly.all_coeffs() if fpoly.degree() == 1 else (sp.Integer(0), f)
            eq_line = f"{clean(f)} = 0"
            steps.append(eq_line)
            root = sp.nsimplify(sp.simplify(-fb / fa))
            root_line = f"x = {_mathstr(root)}"
            if root_line != eq_line:
                steps.append(root_line)
            roots.append(root)

        if len(roots) == 2 and roots[0] == roots[1]:
            result = f"x = {_mathstr(roots[0])} (repeated root)"
        else:
            result = ", ".join(f"x = {_mathstr(r)}" for r in roots)
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

def _clean_equation_for_function(s):
    """Tolerate a student writing the full equation (y = 2x+3, f(x)=2x+3,
    or even 2x+3=0) instead of just the bare expression in x."""
    s = s.strip()
    if "=" in s:
        lhs, rhs = s.split("=", 1)
        lhs_clean = lhs.strip().lower().replace(" ", "")
        if lhs_clean in ("y", "f(x)", "g(x)", "f", "g", "fx", "gx"):
            return rhs.strip()
        return f"({lhs.strip()}) - ({rhs.strip()})"
    return s


def table_of_values(expr_str, x_min, x_max, step=1):
    try:
        expr_str = _require(expr_str, "f(x)")
        x_min = _require(x_min, "x min")
        x_max = _require(x_max, "x max")
        expr_str = _clean_equation_for_function(expr_str)
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

    expr_str = _clean_equation_for_function(expr_str)
    if expr2_str:
        expr2_str = _clean_equation_for_function(expr2_str)

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

def ap_solve(a=None, d=None, n=None, Tn=None, Sn=None):
    """General Arithmetic Progression solver. Provide whichever of
    a, d, n, Tn (nth term), Sn (sum of n terms) you know, and leave the
    rest blank -- this solves for whatever is missing using:
        Tn = a + (n-1)d
        Sn = (n/2)[2a + (n-1)d]
    """
    try:
        vals = {"a": a, "d": d, "n": n, "Tn": Tn, "Sn": Sn}
        known = {k: sp.nsimplify(v) for k, v in vals.items() if v not in (None, "")}
        missing = [k for k in vals if k not in known]
        if not missing:
            return _fail("Please leave at least one value blank -- that's the one to find.")

        A, D, N, TNs, SNs = sp.symbols("a d n Tn Sn", real=True)
        symmap = {"a": A, "d": D, "n": N, "Tn": TNs, "Sn": SNs}
        eq_tn = sp.Eq(TNs, A + (N - 1) * D)
        eq_sn = sp.Eq(SNs, (N / 2) * (2 * A + (N - 1) * D))

        steps = [
            "Formulas: Tn = a + (n - 1)d   and   Sn = (n/2)[2a + (n - 1)d]",
            "Known: " + ", ".join(f"{k} = {v}" for k, v in known.items()),
        ]
        subs = {symmap[k]: v for k, v in known.items()}
        eq_tn_sub = eq_tn.subs(subs)
        eq_sn_sub = eq_sn.subs(subs)

        target_syms = [symmap[k] for k in missing]
        sol = sp.solve([eq_tn_sub, eq_sn_sub], target_syms, dict=True)
        if not sol:
            # Fall back to whichever single equation is enough (e.g. Sn not
            # involved at all in what's known/missing)
            sol = sp.solve([eq_tn_sub], target_syms, dict=True) or \
                  sp.solve([eq_sn_sub], target_syms, dict=True)
        if not sol:
            return _fail("Could not solve for the missing value(s) with the numbers given -- "
                         "please check there's enough information (and that it's consistent).")

        chosen = None
        for cand in sol:
            if "n" in missing and N in cand:
                nv = sp.simplify(cand[N])
                if nv.is_real and nv > 0 and float(nv) == int(round(float(nv))):
                    chosen = cand
                    break
            else:
                chosen = cand
                break
        if chosen is None:
            chosen = sol[0]

        for k in missing:
            val = sp.nsimplify(sp.simplify(chosen[symmap[k]]))
            steps.append(f"{k} = {_mathstr(val)}")
            known[k] = val

        result = ", ".join(f"{k} = {_mathstr(known[k])}" for k in ("a", "d", "n", "Tn", "Sn"))
        return _ok(steps, result)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def ap_list_terms(a=None, d=None, start=None, end=None):
    """List AP terms from term number `start` to term number `end` (inclusive)."""
    try:
        a = sp.nsimplify(_require(a, "first term (a)"))
        d = sp.nsimplify(_require(d, "common difference (d)"))
        start = int(sp.nsimplify(_require(start, "start term number")))
        end = int(sp.nsimplify(_require(end, "end term number")))
        if start < 1 or end < start:
            return _fail("Start must be at least 1, and end must not be before start.")
        if end - start > 200:
            return _fail("That's a lot of terms -- please ask for 200 or fewer at a time.")
        steps = ["Tn = a + (n - 1)d", f"a = {a}, d = {d}"]
        terms = []
        for k in range(start, end + 1):
            tk = sp.simplify(a + (k - 1) * d)
            terms.append(_mathstr(tk))
        steps.append(f"Terms {start} to {end}: " + ", ".join(terms))
        return _ok(steps, ", ".join(terms))
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def gp_solve(a=None, r=None, n=None, Tn=None, Sn=None):
    """General Geometric Progression solver. Provide whichever of
    a, r, n, Tn (nth term), Sn (sum of n terms) you know, and leave the
    rest blank. Uses Tn = a.r^(n-1) and Sn = a(r^n - 1)/(r - 1)."""
    try:
        vals = {"a": a, "r": r, "n": n, "Tn": Tn, "Sn": Sn}
        known = {k: sp.nsimplify(v) for k, v in vals.items() if v not in (None, "")}
        missing = [k for k in vals if k not in known]
        if not missing:
            return _fail("Please leave at least one value blank -- that's the one to find.")

        steps = [
            "Formulas: Tn = a x r^(n-1)   and   Sn = a(r^n - 1)/(r - 1)  [r != 1]",
            "Known: " + ", ".join(f"{k} = {v}" for k, v in known.items()),
        ]

        # Step 1: if exactly one of a/r/n is missing (and Tn is known),
        # solve for it using the inverse of the Tn formula.
        core_missing = [k for k in ("a", "r", "n") if k in missing]
        if len(core_missing) == 1 and "Tn" in known:
            only = core_missing[0]
            if only == "a":
                r_, n_, tn_ = known["r"], known["n"], known["Tn"]
                a_ = sp.nsimplify(sp.simplify(tn_ / r_ ** (n_ - 1)))
                steps.append(f"a = Tn / r^(n-1) = {tn_} / ({r_})^({n_}-1) = {_mathstr(a_)}")
                known["a"] = a_
            elif only == "r":
                a_, n_, tn_ = known["a"], known["n"], known["Tn"]
                if n_ == 1:
                    return _fail("With n = 1, Tn = a always -- r cannot be determined from this.")
                r_ = sp.nsimplify(sp.real_root(sp.simplify(tn_ / a_), int(n_ - 1)))
                steps.append(f"r^({n_}-1) = Tn/a = {tn_}/{a_}")
                steps.append(f"r = ({tn_}/{a_})^(1/{n_-1}) = {_mathstr(r_)}")
                known["r"] = r_
            elif only == "n":
                a_, r_, tn_ = known["a"], known["r"], known["Tn"]
                if r_ in (1, -1) or a_ == 0:
                    return _fail("Can't uniquely determine n from these values (r = 1, r = -1, or "
                                 "a = 0 makes this ambiguous).")
                n_ = sp.simplify(1 + sp.log(tn_ / a_) / sp.log(r_))
                n_num = sp.N(n_, 10)
                steps.append(f"r^(n-1) = Tn/a = {tn_}/{a_}")
                steps.append("n - 1 = log(Tn/a) / log(r)")
                if abs(n_num - round(float(n_num))) < 1e-6:
                    n_ = int(round(float(n_num)))
                steps.append(f"n = {n_}")
                known["n"] = n_
        elif len(core_missing) > 1:
            return _fail("Please provide at least two of a, r, n (plus Tn if needed) -- there "
                         "isn't enough information to solve for more than one of a, r, n at once.")

        # Step 2: once a, r, n are all known, fill in any of Tn/Sn still missing.
        if not ({"a", "r", "n"} <= set(known.keys())):
            return _fail("Not enough information -- please provide at least three of a, r, n, Tn "
                         "(with at most one of a, r, n left blank), so the rest can be worked out.")

        a_, r_, n_ = known["a"], known["r"], known["n"]
        if "Tn" not in known:
            tn_ = sp.nsimplify(sp.simplify(a_ * r_ ** (n_ - 1)))
            steps.append(f"Tn = a x r^(n-1) = {a_} x ({r_})^({n_}-1) = {_mathstr(tn_)}")
            known["Tn"] = tn_
        if "Sn" not in known:
            if r_ == 1:
                sn_ = sp.simplify(a_ * n_)
            else:
                sn_ = sp.nsimplify(sp.simplify(a_ * (r_ ** n_ - 1) / (r_ - 1)))
            steps.append(f"Sn = a(r^n - 1)/(r - 1) = {_mathstr(sn_)}")
            known["Sn"] = sn_

        result = ", ".join(f"{k} = {_mathstr(known[k])}" for k in ("a", "r", "n", "Tn", "Sn") if k in known)
        return _ok(steps, result)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def gp_list_terms(a=None, r=None, start=None, end=None):
    """List GP terms from term number `start` to term number `end` (inclusive)."""
    try:
        a = sp.nsimplify(_require(a, "first term (a)"))
        r = sp.nsimplify(_require(r, "common ratio (r)"))
        start = int(sp.nsimplify(_require(start, "start term number")))
        end = int(sp.nsimplify(_require(end, "end term number")))
        if start < 1 or end < start:
            return _fail("Start must be at least 1, and end must not be before start.")
        if end - start > 200:
            return _fail("That's a lot of terms -- please ask for 200 or fewer at a time.")
        steps = ["Tn = a x r^(n-1)", f"a = {a}, r = {r}"]
        terms = []
        for k in range(start, end + 1):
            tk = sp.nsimplify(sp.simplify(a * r ** (k - 1)))
            terms.append(_mathstr(tk))
        steps.append(f"Terms {start} to {end}: " + ", ".join(terms))
        return _ok(steps, ", ".join(terms))
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


def general_sequence(terms_str, find_upto=None):
    """A 'series' that is neither AP nor GP -- deduce the pattern from a few
    given consecutive terms using the method of differences (handles linear
    i.e. AP, quadratic, and constant-ratio i.e. GP patterns), find the
    formula for Tn, and optionally list terms up to a given term number."""
    try:
        terms_str = _require(terms_str, "the known terms")
        raw = [p.strip() for p in re.split(r"[,\s]+", terms_str.strip()) if p.strip() != ""]
        if len(raw) < 3:
            return _fail("Please give at least 3 consecutive terms so a pattern can be found.")
        terms = [sp.nsimplify(t) for t in raw]
        steps = [f"Given terms: {', '.join(str(t) for t in terms)}"]

        d1 = [sp.simplify(terms[i + 1] - terms[i]) for i in range(len(terms) - 1)]
        steps.append(f"1st differences: {', '.join(str(x) for x in d1)}")

        n = sp.Symbol("n")
        if len(set(d1)) == 1:
            d = d1[0]
            a = terms[0]
            steps.append(f"The 1st differences are constant (d = {d}) -- this is an Arithmetic sequence.")
            Tn_formula = sp.expand(a + (n - 1) * d)
            steps.append(f"Tn = a + (n-1)d = {a} + (n-1)({d}) = {Tn_formula}")
        elif len(terms) >= 2 and all(t != 0 for t in terms[:-1]) and \
                len({sp.simplify(terms[i + 1] / terms[i]) for i in range(len(terms) - 1)}) == 1:
            r = sp.simplify(terms[1] / terms[0])
            a = terms[0]
            steps.append(f"The ratio between consecutive terms is constant (r = {r}) -- this is a Geometric sequence.")
            Tn_formula = a * r ** (n - 1)
            steps.append(f"Tn = a x r^(n-1) = {a} x ({r})^(n-1)")
        elif len(d1) >= 2 and len(set(sp.simplify(d1[i + 1] - d1[i]) for i in range(len(d1) - 1))) == 1:
            d2 = sp.simplify(d1[1] - d1[0])
            steps.append(f"2nd differences: {', '.join(str(sp.simplify(d1[i+1]-d1[i])) for i in range(len(d1)-1))}")
            steps.append(f"The 2nd differences are constant ({d2}) -- this is a Quadratic sequence: Tn = An^2 + Bn + C.")
            A_, B_, C_ = sp.symbols("A B C")
            eqs = [sp.Eq(A_ * (i + 1) ** 2 + B_ * (i + 1) + C_, terms[i]) for i in range(3)]
            sol = sp.solve(eqs, [A_, B_, C_])
            Av, Bv, Cv = sp.nsimplify(sol[A_]), sp.nsimplify(sol[B_]), sp.nsimplify(sol[C_])
            steps.append(f"Solving using the first three terms: A = {Av}, B = {Bv}, C = {Cv}")
            Tn_formula = sp.expand(Av * n ** 2 + Bv * n + Cv)
            steps.append(f"Tn = {Tn_formula}")
        else:
            return _fail("Could not identify a simple AP, GP, or quadratic pattern from these terms. "
                         "Please check the terms are correct and in order.")

        Tn_str = str(Tn_formula).replace("**", "^").replace("*", "")
        steps[-1] = steps[-1].replace(str(Tn_formula), Tn_str) if str(Tn_formula) in steps[-1] else steps[-1]
        result = f"Tn = {Tn_str}"
        if find_upto not in (None, ""):
            find_upto = int(sp.nsimplify(find_upto))
            more = [str(sp.simplify(Tn_formula.subs(n, k))) for k in range(1, find_upto + 1)]
            steps.append(f"Terms 1 to {find_upto} using this formula: {', '.join(more)}")
            result += f"; terms 1-{find_upto}: " + ", ".join(more)
        return _ok(steps, result)
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


def _fmt_set(s):
    ordered = sorted(s, key=lambda v: (len(v), v))
    return "{" + ", ".join(ordered) + "}" if ordered else "{ } (empty set)"


def _venn_png(circles, texts, xlim=(-3.4, 3.4), ylim=(-2.6, 2.6), figsize=(6.5, 5.2)):
    """circles: list of (cx, cy, radius, facecolor). texts: list of (x, y, string, fontsize)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import io, base64

    fig, ax = plt.subplots(figsize=figsize)
    # bounding rectangle represents the universal set U
    rect_x0, rect_y0 = xlim[0] + 0.15, ylim[0] + 0.15
    rect_w, rect_h = (xlim[1] - xlim[0]) - 0.3, (ylim[1] - ylim[0]) - 0.3
    ax.add_patch(plt.Rectangle((rect_x0, rect_y0), rect_w, rect_h,
                                fill=False, edgecolor="#334155", linewidth=1.6))
    ax.text(rect_x0 + 0.12, rect_y0 + rect_h - 0.12, "U", fontsize=15, fontweight="bold",
            ha="left", va="top", color="#334155")

    for (cx, cy, r, color) in circles:
        ax.add_patch(plt.Circle((cx, cy), r, facecolor=color, edgecolor="#1e293b",
                                 linewidth=1.6, alpha=0.45))

    for (x, y, s, fs) in texts:
        ax.text(x, y, s, fontsize=fs, ha="center", va="center", color="#0f172a", wrap=True)

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def _venn2_diagram(label_a, label_b, only_a_text, only_b_text, both_text, neither_text):
    circles = [(-0.85, 0, 1.7, "#60a5fa"), (0.85, 0, 1.7, "#f472b6")]
    texts = [
        (-1.9, 1.9, label_a, 14),
        (1.9, 1.9, label_b, 14),
        (-1.55, 0, only_a_text, 10),
        (1.55, 0, only_b_text, 10),
        (0, 0, both_text, 10),
        (-2.7, -2.1, "neither:\n" + neither_text, 9.5),
    ]
    return _venn_png(circles, texts)


def _venn3_diagram(only_a, only_b, only_c, ab, ac, bc, abc, neither_text):
    circles = [
        (-0.85, 0.6, 1.6, "#60a5fa"),
        (0.85, 0.6, 1.6, "#f472b6"),
        (0, -0.85, 1.6, "#4ade80"),
    ]
    texts = [
        (-1.9, 2.1, "A", 14),
        (1.9, 2.1, "B", 14),
        (0, -2.3, "C", 14),
        (-1.55, 1.15, only_a, 9),
        (1.55, 1.15, only_b, 9),
        (0, -1.75, only_c, 9),
        (0, 1.2, ab, 9),
        (-1.05, -0.65, ac, 9),
        (1.05, -0.65, bc, 9),
        (0, 0.05, abc, 9),
        (-2.9, -2.2, "neither:\n" + neither_text, 9),
    ]
    return _venn_png(circles, texts)


def set_operations(set_a_str, set_b_str, universal_str=None):
    """Union, intersection, differences, and (if a universal set is given) complements.
    Also draws the corresponding 2-set Venn diagram with elements shown."""
    try:
        A, a_order = _parse_set(set_a_str, "Set A")
        B, b_order = _parse_set(set_b_str, "Set B")
        steps = [f"A = {{{', '.join(a_order)}}}", f"B = {{{', '.join(b_order)}}}"]

        union = A | B
        inter = A & B
        a_only = A - B
        b_only = B - A

        steps.append("Union (elements in A or B or both):")
        steps.append(f"A \u222a B = {_fmt_set(union)}")
        steps.append("Intersection (elements in both A and B):")
        steps.append(f"A \u2229 B = {_fmt_set(inter)}")
        steps.append("A only (in A but not B):")
        steps.append(f"A - B = {_fmt_set(a_only)}")
        steps.append("B only (in B but not A):")
        steps.append(f"B - A = {_fmt_set(b_only)}")

        result_lines = [f"A \u222a B = {_fmt_set(union)}", f"A \u2229 B = {_fmt_set(inter)}"]
        neither_text = ""
        U = None
        if universal_str not in (None, ""):
            U, u_order = _parse_set(universal_str, "the universal set")
            steps.append(f"U = {{{', '.join(u_order)}}}")
            a_comp = U - A
            b_comp = U - B
            neither = U - union
            steps.append("Complement of A (in U but not in A):")
            steps.append(f"A' = {_fmt_set(a_comp)}")
            steps.append("Complement of B (in U but not in B):")
            steps.append(f"B' = {_fmt_set(b_comp)}")
            result_lines.append(f"A' = {_fmt_set(a_comp)}")
            result_lines.append(f"B' = {_fmt_set(b_comp)}")
            neither_text = ", ".join(sorted(neither, key=lambda v: (len(v), v))) or "none"

        def short(s, limit=8):
            ordered = sorted(s, key=lambda v: (len(v), v))
            txt = ", ".join(ordered) if ordered else "-"
            if len(ordered) > limit:
                txt = ", ".join(ordered[:limit]) + ", ..."
            return txt

        img = _venn2_diagram("A", "B", short(a_only), short(b_only), short(inter), neither_text or "-")
        return _ok(steps, {"image": img, "text": "; ".join(result_lines)})
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def venn_two_set(n_u=None, n_a=None, n_b=None, n_both=None, n_neither=None):
    """2-set Venn diagram word problem. Exactly one of the five quantities
    should be left blank; the others are used to solve for it via
    inclusion-exclusion, then the full breakdown is shown, along with a
    drawn Venn diagram."""
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
        img = _venn2_diagram("A", "B", str(a_only), str(b_only), str(n_both_v), str(n_neither_v))
        return _ok(steps, {"image": img, "text": result})
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def venn_two_set_elements(set_a_str, set_b_str, universal_str):
    """2-set Venn diagram built directly from actual set elements, showing
    exactly which elements fall in each region, and drawing the diagram."""
    try:
        A, a_order = _parse_set(set_a_str, "Set A")
        B, b_order = _parse_set(set_b_str, "Set B")
        U, u_order = _parse_set(universal_str, "the universal set")
        if not (A <= U and B <= U):
            return _fail("Every element of A and B should also be in the universal set U -- "
                         "please check for typos.")

        steps = [f"U = {{{', '.join(u_order)}}}", f"A = {{{', '.join(a_order)}}}", f"B = {{{', '.join(b_order)}}}"]

        a_only = A - B
        b_only = B - A
        both = A & B
        neither = U - (A | B)

        steps.append(f"Only A: {_fmt_set(a_only)}")
        steps.append(f"Only B: {_fmt_set(b_only)}")
        steps.append(f"Both (A and B): {_fmt_set(both)}")
        steps.append(f"Neither: {_fmt_set(neither)}")
        steps.append(f"n(A)={len(A)}, n(B)={len(B)}, n(A and B)={len(both)}, "
                      f"n(A or B)={len(A|B)}, n(neither)={len(neither)}, n(U)={len(U)}")

        def joined(s, per_line=5):
            ordered = sorted(s, key=lambda v: (len(v), v))
            if not ordered:
                return "-"
            lines = [", ".join(ordered[i:i+per_line]) for i in range(0, len(ordered), per_line)]
            return "\n".join(lines)

        img = _venn2_diagram("A", "B", joined(a_only), joined(b_only), joined(both), joined(neither))
        result = (f"only A={_fmt_set(a_only)}; only B={_fmt_set(b_only)}; "
                  f"both={_fmt_set(both)}; neither={_fmt_set(neither)}")
        return _ok(steps, {"image": img, "text": result})
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

        ab_only = sp.simplify(known["n_ab"] - known["n_abc"])
        ac_only = sp.simplify(known["n_ac"] - known["n_abc"])
        bc_only = sp.simplify(known["n_bc"] - known["n_abc"])
        neither = sp.simplify(known["n_u"] - (only_a + only_b + only_c + ab_only + ac_only + bc_only + known["n_abc"]))

        result = (f"n(U)={known['n_u']}, only A={only_a}, only B={only_b}, only C={only_c}, "
                  f"n(A and B and C)={known['n_abc']}, neither={neither}")
        img = _venn3_diagram(str(only_a), str(only_b), str(only_c), str(ab_only),
                              str(ac_only), str(bc_only), str(known["n_abc"]), str(neither))
        return _ok(steps, {"image": img, "text": result})
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def venn_three_set_elements(set_a_str, set_b_str, set_c_str, universal_str):
    """3-set Venn diagram built directly from actual set elements."""
    try:
        A, a_order = _parse_set(set_a_str, "Set A")
        B, b_order = _parse_set(set_b_str, "Set B")
        C, c_order = _parse_set(set_c_str, "Set C")
        U, u_order = _parse_set(universal_str, "the universal set")
        if not (A <= U and B <= U and C <= U):
            return _fail("Every element of A, B and C should also be in the universal set U -- "
                         "please check for typos.")

        steps = [f"U = {{{', '.join(u_order)}}}", f"A = {{{', '.join(a_order)}}}",
                 f"B = {{{', '.join(b_order)}}}", f"C = {{{', '.join(c_order)}}}"]

        only_a = A - B - C
        only_b = B - A - C
        only_c = C - A - B
        ab_only = (A & B) - C
        ac_only = (A & C) - B
        bc_only = (B & C) - A
        abc = A & B & C
        neither = U - (A | B | C)

        steps.append(f"Only A: {_fmt_set(only_a)}")
        steps.append(f"Only B: {_fmt_set(only_b)}")
        steps.append(f"Only C: {_fmt_set(only_c)}")
        steps.append(f"A and B only: {_fmt_set(ab_only)}")
        steps.append(f"A and C only: {_fmt_set(ac_only)}")
        steps.append(f"B and C only: {_fmt_set(bc_only)}")
        steps.append(f"A and B and C: {_fmt_set(abc)}")
        steps.append(f"Neither: {_fmt_set(neither)}")

        def joined(s, per_line=5):
            ordered = sorted(s, key=lambda v: (len(v), v))
            if not ordered:
                return "-"
            lines = [", ".join(ordered[i:i+per_line]) for i in range(0, len(ordered), per_line)]
            return "\n".join(lines)

        img = _venn3_diagram(joined(only_a), joined(only_b), joined(only_c), joined(ab_only),
                              joined(ac_only), joined(bc_only), joined(abc), joined(neither))
        result = f"only A={_fmt_set(only_a)}; only B={_fmt_set(only_b)}; only C={_fmt_set(only_c)}; all three={_fmt_set(abc)}; neither={_fmt_set(neither)}"
        return _ok(steps, {"image": img, "text": result})
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


# ---------------------------------------------------------------- INDICES --

def _clean_pow(s):
    return str(s).replace("**", "^").replace("*", "")


def indices_law_multiply(base, m, n):
    """a^m x a^n = a^(m+n)"""
    try:
        base = _require(base, "the base (a)")
        m = sp.nsimplify(_require(m, "first index (m)"))
        n = sp.nsimplify(_require(n, "second index (n)"))
        base_e = _parse(base)
        steps = ["Law: a^m x a^n = a^(m + n) (same base -- add the indices)",
                 f"a = {base}, m = {m}, n = {n}"]
        total = sp.simplify(m + n)
        steps.append(f"{base}^{m} x {base}^{n} = {base}^({m} + {n}) = {base}^{total}")
        val = sp.nsimplify(sp.simplify(base_e ** total))
        if val.is_number:
            steps.append(f"= {_mathstr(val)}")
            result = f"{base}^{total} = {_mathstr(val)}"
        else:
            result = f"{_clean_pow(base_e**total)}"
        return _ok(steps, result)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def indices_law_divide(base, m, n):
    """a^m / a^n = a^(m-n)"""
    try:
        base = _require(base, "the base (a)")
        m = sp.nsimplify(_require(m, "first index (m)"))
        n = sp.nsimplify(_require(n, "second index (n)"))
        base_e = _parse(base)
        steps = ["Law: a^m / a^n = a^(m - n) (same base -- subtract the indices)",
                 f"a = {base}, m = {m}, n = {n}"]
        total = sp.simplify(m - n)
        steps.append(f"{base}^{m} / {base}^{n} = {base}^({m} - {n}) = {base}^{total}")
        val = sp.nsimplify(sp.simplify(base_e ** total))
        if val.is_number:
            steps.append(f"= {_mathstr(val)}")
            result = f"{base}^{total} = {_mathstr(val)}"
        else:
            result = f"{_clean_pow(base_e**total)}"
        return _ok(steps, result)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def indices_law_power(base, m, n):
    """(a^m)^n = a^(m x n)"""
    try:
        base = _require(base, "the base (a)")
        m = sp.nsimplify(_require(m, "inner index (m)"))
        n = sp.nsimplify(_require(n, "outer index (n)"))
        base_e = _parse(base)
        steps = ["Law: (a^m)^n = a^(m x n) (power of a power -- multiply the indices)",
                 f"a = {base}, m = {m}, n = {n}"]
        total = sp.simplify(m * n)
        steps.append(f"({base}^{m})^{n} = {base}^({m} x {n}) = {base}^{total}")
        val = sp.nsimplify(sp.simplify(base_e ** total))
        if val.is_number:
            steps.append(f"= {_mathstr(val)}")
            result = f"{base}^{total} = {_mathstr(val)}"
        else:
            result = f"{_clean_pow(base_e**total)}"
        return _ok(steps, result)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def indices_evaluate(expr_str):
    """Simplify/evaluate a general expression involving indices, narrating
    the relevant law where a clear same-base pattern is detected."""
    try:
        expr_str = _require(expr_str, "the expression")
        expr = _parse(expr_str)
        steps = [f"Expression: {_clean_pow(expr)}"]

        narrated = False
        if isinstance(expr, sp.Mul):
            bases = {}
            for f in expr.args:
                if isinstance(f, sp.Pow):
                    bases.setdefault(f.base, []).append(f.exp)
                elif f.is_number:
                    bases.setdefault(f, []).append(sp.Integer(1))
                else:
                    bases.setdefault(f, []).append(sp.Integer(1))
            for b, exps in bases.items():
                if len(exps) > 1:
                    steps.append(f"Same base {b}: add the indices {' + '.join(str(e) for e in exps)} "
                                  f"= {sp.simplify(sum(exps))}")
                    narrated = True
        elif isinstance(expr, sp.Pow) and isinstance(expr.base, sp.Pow):
            inner = expr.base
            steps.append(f"Power of a power: multiply the indices {inner.exp} x {expr.exp} "
                          f"= {sp.simplify(inner.exp * expr.exp)}")
            narrated = True

        simplified = sp.nsimplify(sp.powsimp(sp.simplify(expr), force=True))
        if narrated:
            steps.append(f"Result: {_clean_pow(simplified)}")
        else:
            steps.append(f"Using the laws of indices, this simplifies to: {_clean_pow(simplified)}")

        if simplified.is_number and not simplified.is_integer:
            steps.append(f"~= {sp.N(simplified, 6)}")
        return _ok(steps, _clean_pow(simplified))
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def indices_solve_equation(expr_str):
    """Solve an equation with the unknown x in an index, e.g. 2^(x+1) = 16."""
    try:
        expr_str = _require(expr_str, "the equation")
        if "=" not in expr_str:
            return _fail("Please give a full equation with an '=' sign, e.g. 2^(x+1) = 16.")
        lhs_s, rhs_s = expr_str.split("=", 1)
        lhs = _parse(lhs_s)
        rhs = _parse(rhs_s)
        steps = [f"Equation: {_clean_pow(lhs)} = {_clean_pow(rhs)}"]

        # Try to express both sides as powers of the same base.
        def base_exp(e):
            if isinstance(e, sp.Pow):
                return e.base, e.exp
            return None, None

        lb, le = base_exp(lhs)
        rb, re_ = base_exp(rhs)

        same_base = None
        if lb is not None and rb is None and rhs.is_number and rhs > 0:
            # try to rewrite rhs as lb**k
            for k in range(1, 40):
                if sp.simplify(lb ** k - rhs) == 0:
                    same_base = (lb, le, sp.Integer(k))
                    break
                if sp.simplify(lb ** sp.Rational(1, k) - rhs) == 0:
                    same_base = (lb, le, sp.Rational(1, k))
                    break

        if same_base:
            b, exp_lhs, exp_rhs = same_base
            steps.append(f"Rewrite {_mathstr(rhs)} as a power of {b}: {_mathstr(rhs)} = {b}^{exp_rhs}")
            steps.append(f"So {b}^({_clean_pow(exp_lhs)}) = {b}^{exp_rhs}")
            steps.append("Since the bases match, the indices must be equal:")
            eq = sp.Eq(exp_lhs, exp_rhs)
            steps.append(f"{_clean_pow(exp_lhs)} = {exp_rhs}")
            sol = sp.solve(eq, x)
            if not sol:
                return _fail("Could not solve for x from the matched indices.")
            for s in sol:
                steps.append(f"x = {_mathstr(sp.nsimplify(s))}")
            result = ", ".join(f"x = {_mathstr(sp.nsimplify(s))}" for s in sol)
            return _ok(steps, result)

        # Fall back to logarithms.
        steps.append("The two sides don't share an obvious common base, so take logarithms of "
                      "both sides:")
        steps.append(f"log({_clean_pow(lhs)}) = log({_clean_pow(rhs)})")

        if lb is not None and le.has(x):
            # lhs = base^(linear expr in x); solve the exponent directly
            # ourselves so the final answer matches the derivation shown,
            # rather than letting sp.solve pick a differently-formatted
            # but equivalent answer.
            steps.append(f"{_clean_pow(le)} x log({lb}) = log({_clean_pow(rhs)})")
            target = sp.log(rhs) / sp.log(lb)
            steps.append(f"{_clean_pow(le)} = log({_clean_pow(rhs)})/log({lb})")
            le_poly = sp.Poly(le, x)
            if le_poly.degree() == 1:
                p, q = le_poly.all_coeffs()
            else:
                p, q = sp.Integer(1), sp.Integer(0)
            sol_val = (target - q) / p
            if p != 1:
                steps.append(f"x = ( log({_clean_pow(rhs)})/log({lb}) - ({q}) ) / {p}")
            sol = [sol_val]
        else:
            sol = sp.solve(sp.Eq(sp.log(lhs), sp.log(rhs)), x) or sp.solve(sp.Eq(lhs, rhs), x)

        if not sol:
            return _fail("Could not solve this equation -- please check it's set up correctly.")
        for s in sol:
            sv = sp.nsimplify(s)
            steps.append(f"x = {_mathstr(sv)}  (~= {sp.N(sv, 6)})")
        result = ", ".join(f"x = {_mathstr(sp.nsimplify(s))}" for s in sol)
        return _ok(steps, result)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")



# ------------------------------------------------------------- LOGARITHMS --

def _clean_log(s):
    """Like _clean_pow, but keeps a space before log/sqrt/ln so '3log(x)'
    reads as '3 log(x)' instead of merging together."""
    s = str(s).replace("**", "^")
    s = re.sub(r"\*(log|sqrt|ln)\(", r" \1(", s)
    s = s.replace("*", "")
    return s


def _parse_log(expr_str):
    """Parse an expression that may contain log_b(x) notation (custom base)
    by converting it to sympy's log(x, b) form first."""
    s = expr_str.strip()
    # log_b(...) -> a placeholder sympy can parse: use Function-call style log(x, b)
    s = re.sub(r"log_(\w+)\(", r"log(", s)  # base handled separately per-call below
    return s


def log_evaluate(expr_str, base=None):
    """Evaluate a logarithm, e.g. log_2(8), log(100) [base 10], ln(x) [base e]."""
    try:
        expr_str = _require(expr_str, "the expression")
        m = re.match(r"^\s*log_(\w+)\((.+)\)\s*$", expr_str.strip())
        if m:
            base_val = sp.nsimplify(m.group(1))
            arg_str = m.group(2)
        elif base not in (None, ""):
            base_val = sp.nsimplify(base)
            inner = re.match(r"^\s*(?:log|ln)\((.+)\)\s*$", expr_str.strip())
            arg_str = inner.group(1) if inner else expr_str
        elif expr_str.strip().lower().startswith("ln("):
            base_val = sp.E
            arg_str = expr_str.strip()[3:-1]
        else:
            base_val = sp.Integer(10)
            inner = re.match(r"^\s*log\((.+)\)\s*$", expr_str.strip())
            arg_str = inner.group(1) if inner else expr_str

        arg = _parse(arg_str, {"x": x, "y": y, "e": sp.E, "pi": sp.pi})
        base_disp = "e" if base_val == sp.E else _mathstr(base_val)
        arg_disp = "e" if arg == sp.E else _clean_log(arg)
        steps = [f"log base {base_disp} of {arg_disp}"]

        numeric = sp.N(sp.log(arg) / sp.log(base_val), 15)
        rounded_int = round(float(numeric))
        if arg.is_number and abs(float(numeric) - rounded_int) < 1e-9 and \
                sp.simplify(base_val ** rounded_int - arg) == 0:
            steps.append(f"= {rounded_int}  (since {base_disp}^{rounded_int} = {arg_disp})")
            return _ok(steps, str(rounded_int))

        if arg.is_number:
            rat = sp.nsimplify(float(numeric), rational=True, tolerance=1e-9)
            if getattr(rat, "q", 1) <= 12 and abs(float(rat) - float(numeric)) < 1e-9 and \
                    sp.simplify(base_val ** rat - arg) == 0:
                steps.append(f"= {_mathstr(rat)}  (since {base_disp}^({_mathstr(rat)}) = {arg_disp})")
                return _ok(steps, _mathstr(rat))
            steps.append(f"~= {sp.N(numeric, 6)}  (not a whole/simple number -- this is the "
                          "decimal approximation)")
            return _ok(steps, f"~= {sp.N(numeric, 6)}")

        val = sp.logcombine(sp.log(arg, base_val), force=True)
        steps.append(f"= {_clean_log(val)}")
        return _ok(steps, _clean_log(val))
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def log_change_of_base(value, from_base, to_base=10):
    """log_b(a) = log_c(a) / log_c(b) -- change of base formula."""
    try:
        value = sp.nsimplify(_require(value, "the number (a)"))
        from_base = sp.nsimplify(_require(from_base, "the original base (b)"))
        to_base = sp.nsimplify(to_base) if to_base not in (None, "") else sp.Integer(10)
        steps = [
            "Change of base formula: log_b(a) = log_c(a) / log_c(b)",
            f"a = {value}, b = {from_base}, new base c = {to_base}",
            f"log_{from_base}({value}) = log_{to_base}({value}) / log_{to_base}({from_base})",
        ]
        result_val = sp.log(value, to_base) / sp.log(from_base, to_base)
        result_val = sp.simplify(result_val)
        steps.append(f"= {_mathstr(sp.N(result_val, 6))}")
        exact = sp.nsimplify(sp.log(value) / sp.log(from_base))
        if exact.is_rational:
            steps.append(f"(exactly {_mathstr(exact)})")
            return _ok(steps, _mathstr(exact))
        return _ok(steps, f"~= {sp.N(result_val, 6)}")
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def log_laws_simplify(expr_str):
    """Simplify/expand a log expression using the laws of logarithms."""
    try:
        expr_str = _require(expr_str, "the expression")
        expr = _parse(expr_str, {"x": x, "log": sp.log, "ln": sp.log})
        steps = [f"Expression: {_clean_log(expr)}"]

        expanded = sp.expand_log(expr, force=True)
        combined = sp.logcombine(expr, force=True)

        if expanded != expr:
            steps.append("Expanding using the laws log(ab) = log(a) + log(b), "
                          "log(a/b) = log(a) - log(b), log(a^n) = n.log(a):")
            steps.append(f"= {_clean_log(expanded)}")
            return _ok(steps, _clean_log(expanded))
        elif combined != expr:
            steps.append("Combining using the laws of logarithms:")
            steps.append(f"= {_clean_log(combined)}")
            return _ok(steps, _clean_log(combined))
        else:
            simplified = sp.simplify(expr)
            steps.append(f"Simplified: {_clean_log(simplified)}")
            return _ok(steps, _clean_log(simplified))
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def log_solve_equation(expr_str):
    """Solve an equation involving logarithms, e.g. log_2(x) = 5, or
    log(x+1) + log(x-1) = log(8)."""
    try:
        expr_str = _require(expr_str, "the equation")
        if "=" not in expr_str:
            return _fail("Please give a full equation with an '=' sign, e.g. log_2(x) = 5.")
        lhs_s, rhs_s = expr_str.split("=", 1)

        def to_log_expr(s):
            s = s.strip()
            m = re.match(r"^log_(\w+)\((.+)\)$", s)
            if m:
                base_val = sp.nsimplify(m.group(1))
                arg = _parse(m.group(2))
                return sp.log(arg, base_val)
            return _parse(s, {"x": x, "log": sp.log, "ln": sp.log})

        lhs = to_log_expr(lhs_s)
        rhs = to_log_expr(rhs_s)
        steps = [f"Equation: {_clean_log(lhs)} = {_clean_log(rhs)}"]

        combined_eq = sp.Eq(sp.logcombine(lhs - rhs, force=True), 0)
        if combined_eq.lhs != lhs - rhs:
            steps.append("Combine the logarithms on one side using the laws of logarithms:")
            steps.append(f"{_clean_log(combined_eq.lhs)} = 0")

        sol = sp.solve(combined_eq, x)
        if not sol:
            sol = sp.solve(sp.Eq(lhs, rhs), x)
        if not sol:
            return _fail("Could not solve this equation -- please check it's set up correctly.")

        # Reject solutions that would take a log of a non-positive number.
        valid = []
        log_args = [a.args[0] for a in (lhs, rhs) if a.has(sp.log) for a in a.atoms(sp.log)]
        for s in sol:
            if not s.is_real:
                continue
            ok = True
            for la in log_args:
                v = la.subs(x, s)
                if v.is_number and v <= 0:
                    ok = False
                    break
            if ok:
                valid.append(s)

        if not valid:
            return _fail("No valid solution -- every candidate value makes one of the logarithms "
                         "undefined (log of a non-positive number).")

        steps.append("Solve for x (rejecting any solution that makes a log argument <= 0):")
        for s in valid:
            sv = sp.nsimplify(s)
            steps.append(f"x = {_mathstr(sv)}")
        result = ", ".join(f"x = {_mathstr(sp.nsimplify(s))}" for s in valid)
        return _ok(steps, result)
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")



# ----------------------------------------------------------------- SURDS --

def _clean_surd(s):
    """Like _mathstr, but also strips the '*' between a coefficient and a
    surd/bracket so '5*sqrt(2)' reads as '5sqrt(2)' -> '5' + radical + '(2)'."""
    return _mathstr(s).replace("*", "")


def surd_simplify(expr_str):
    """Simplify a surd, e.g. sqrt(50) -> 5*sqrt(2)."""
    try:
        expr_str = _require(expr_str, "the surd expression")
        expr = _parse(expr_str)
        steps = [f"Expression: {_clean_surd(expr)}"]

        simplified = sp.sqrtdenest(sp.radsimp(sp.simplify(expr)))
        simplified = sp.nsimplify(simplified)

        # Try to narrate factoring out the largest perfect square, for a
        # single sqrt(N) case specifically.
        if isinstance(expr, sp.Pow) and expr.exp == sp.Rational(1, 2) and expr.base.is_Integer and expr.base > 0:
            n = int(expr.base)
            biggest_sq = 1
            biggest_rest = n
            for k in range(2, int(n ** 0.5) + 1):
                if n % (k * k) == 0:
                    if k * k > biggest_sq:
                        biggest_sq = k * k
                        biggest_rest = n // (k * k)
            if biggest_sq > 1:
                root = int(biggest_sq ** 0.5)
                steps.append(f"Find the largest perfect square factor of {n}: {biggest_sq} x {biggest_rest} = {n}")
                steps.append(f"\u221a{n} = \u221a({biggest_sq} x {biggest_rest}) = \u221a{biggest_sq} x \u221a{biggest_rest} "
                              f"= {root}\u221a{biggest_rest}" if biggest_rest > 1 else f"\u221a{n} = {root}")

        steps.append(f"Simplified: {_clean_surd(simplified)}")
        return _ok(steps, _clean_surd(simplified))
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def surd_arithmetic(expr_str):
    """Add, subtract, multiply, or divide surd expressions, e.g.
    2*sqrt(3) + 5*sqrt(3), or sqrt(2)*sqrt(8), or sqrt(12)+sqrt(27)."""
    try:
        expr_str = _require(expr_str, "the expression")
        expr = _parse(expr_str)
        steps = [f"Expression: {_clean_surd(expr)}"]

        if isinstance(expr, sp.Add):
            steps.append("Simplify each surd term first:")
            parts = []
            for term in expr.args:
                simp = sp.nsimplify(sp.sqrtdenest(sp.radsimp(sp.simplify(term))))
                steps.append(f"  {_clean_surd(term)} = {_clean_surd(simp)}")
                parts.append(simp)
            combined = sp.nsimplify(sp.radsimp(sum(parts)))
            steps.append("Now combine like surds (same number under the root):")
            steps.append(f"= {_clean_surd(combined)}")
            return _ok(steps, _clean_surd(combined))
        else:
            simplified = sp.nsimplify(sp.sqrtdenest(sp.radsimp(sp.simplify(expr))))
            steps.append(f"Multiply/divide and simplify: {_clean_surd(simplified)}")
            return _ok(steps, _clean_surd(simplified))
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")


def surd_rationalize(expr_str):
    """Rationalise the denominator of a fraction involving surds, handling
    both a single-surd denominator and a binomial surd denominator."""
    try:
        expr_str = _require(expr_str, "the fraction")
        expr = _parse(expr_str)
        steps = [f"Expression: {_clean_surd(expr)}"]

        frac = sp.fraction(sp.together(expr))
        num, den = frac
        if den == 1:
            return _fail("This doesn't have a surd denominator to rationalise.")

        steps.append(f"Numerator: {_clean_surd(num)}, Denominator: {_clean_surd(den)}")

        if isinstance(den, sp.Add) and len(den.args) == 2:
            a, b = den.args
            # Pick whichever sign gives a positive rational denominator
            # after multiplying -- the conventional textbook form.
            conj_ab = a - b
            if sp.expand(den * conj_ab).is_number and sp.expand(den * conj_ab) < 0:
                conjugate = b - a
            else:
                conjugate = conj_ab
            steps.append(f"The denominator is a binomial surd, so multiply top and bottom "
                          f"by its conjugate, {_clean_surd(conjugate)}:")
            new_num = sp.expand(num * conjugate)
            new_den = sp.expand(den * conjugate)
            steps.append(f"= [{_clean_surd(num)} x ({_clean_surd(conjugate)})] / "
                          f"[({_clean_surd(den)})({_clean_surd(conjugate)})]")
            steps.append(f"= ({_clean_surd(new_num)}) / {_clean_surd(new_den)}")
            result_expr = sp.nsimplify(sp.simplify(new_num / new_den))
        else:
            steps.append("Multiply top and bottom by the surd in the denominator so it "
                          "becomes a whole number:")
            new_num = sp.expand(num * den)
            new_den = sp.expand(den * den)
            steps.append(f"= [{_clean_surd(num)} x {_clean_surd(den)}] / [{_clean_surd(den)} x {_clean_surd(den)}]")
            steps.append(f"= ({_clean_surd(new_num)}) / {_clean_surd(new_den)}")
            result_expr = sp.nsimplify(sp.simplify(new_num / new_den))

        result_expr = sp.nsimplify(sp.radsimp(result_expr))
        steps.append(f"Simplified: {_clean_surd(result_expr)}")
        return _ok(steps, _clean_surd(result_expr))
    except _MissingInput as e:
        return _fail(str(e))
    except Exception as e:
        return _fail(f"Could not solve: {e}")

