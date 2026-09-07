"""
Step-by-step maths solvers for WAEC/NECO topics, ported from the
Tkinter desktop app (MathsAssistTk). Each function returns a dict:
    {"steps": [str, ...], "result": str, "ok": bool, "error": str or None}
"""
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
    convert_xor,
)

x, y = sp.symbols("x y")
TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)


def _parse(expr_str, local_syms=None):
    syms = local_syms or {"x": x, "y": y}
    return parse_expr(expr_str, local_dict=syms, transformations=TRANSFORMS)


def _fail(msg):
    return {"steps": [], "result": None, "ok": False, "error": msg}


def _ok(steps, result):
    return {"steps": steps, "result": result, "ok": True, "error": None}


# ---------------------------------------------------------------- ALGEBRA --

def solve_quadratic(expr_str):
    try:
        expr = _parse(expr_str)
        eq = sp.Eq(expr, 0)
        poly = sp.Poly(expr, x)
        if poly.degree() != 2:
            return _fail("That isn't a quadratic (degree must be 2).")
        a, b, c = poly.all_coeffs()
        steps = [f"Standard form: {a}x² + ({b})x + ({c}) = 0"]
        disc = sp.simplify(b**2 - 4*a*c)
        steps.append(f"Discriminant, Δ = b² − 4ac = ({b})² − 4({a})({c}) = {disc}")
        if disc > 0:
            steps.append("Δ > 0 → two distinct real roots")
        elif disc == 0:
            steps.append("Δ = 0 → one repeated real root")
        else:
            steps.append("Δ < 0 → two complex roots")
        steps.append("x = [−b ± √Δ] / 2a")
        roots = sp.solve(eq, x)
        roots_s = [sp.nsimplify(r) for r in roots]
        for r in roots_s:
            steps.append(f"x = {r}  (≈ {sp.N(r, 4)})" if not r.is_real is False else f"x = {r}")
        result = ", ".join(f"x = {r}" for r in roots_s)
        return _ok(steps, result)
    except Exception as e:
        return _fail(f"Could not parse/solve: {e}")


def solve_linear(expr_str):
    try:
        if "=" in expr_str:
            lhs, rhs = expr_str.split("=", 1)
            eq = sp.Eq(_parse(lhs), _parse(rhs))
        else:
            eq = sp.Eq(_parse(expr_str), 0)
        steps = [f"Equation: {sp.sstr(eq.lhs)} = {sp.sstr(eq.rhs)}"]
        moved = sp.simplify(eq.lhs - eq.rhs)
        steps.append(f"Move everything to one side: {moved} = 0")
        sol = sp.solve(sp.Eq(moved, 0), x)
        if not sol:
            return _fail("No solution found — check the equation is linear in x.")
        steps.append(f"Isolate x: x = {sol[0]}")
        return _ok(steps, f"x = {sol[0]}")
    except Exception as e:
        return _fail(f"Could not parse/solve: {e}")


def solve_simultaneous_linear(eq1_str, eq2_str):
    try:
        def to_eq(s):
            if "=" in s:
                l, r = s.split("=", 1)
                return sp.Eq(_parse(l), _parse(r))
            return sp.Eq(_parse(s), 0)

        eq1, eq2 = to_eq(eq1_str), to_eq(eq2_str)
        steps = [
            "Equations:",
            f"  (1) {sp.sstr(eq1.lhs)} = {sp.sstr(eq1.rhs)}",
            f"  (2) {sp.sstr(eq2.lhs)} = {sp.sstr(eq2.rhs)}",
            "Using elimination/substitution (sympy linsolve):",
        ]
        sol = sp.linsolve([eq1, eq2], x, y)
        if not sol:
            return _fail("No unique solution — lines may be parallel or identical.")
        xv, yv = list(sol)[0]
        steps.append(f"x = {xv}, y = {yv}")
        return _ok(steps, f"x = {xv}, y = {yv}")
    except Exception as e:
        return _fail(f"Could not parse/solve: {e}")


def solve_simultaneous_mixed(linear_str, quad_str):
    """One linear, one quadratic — per WAEC/NECO exam requirement."""
    try:
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
            steps.append(f"From the linear equation, y = {y_expr}")
            substituted = sp.Eq((eq_quad.lhs - eq_quad.rhs).subs(y, y_expr), 0)
            steps.append(f"Substitute into the quadratic: {sp.simplify(substituted.lhs)} = 0")
            xs = sp.solve(substituted, x)
            pairs = [(xv, sp.simplify(y_expr.subs(x, xv))) for xv in xs]
        else:
            sol = sp.solve([eq_lin, eq_quad], [x, y])
            pairs = sol if isinstance(sol, list) else [sol]
        for xv, yv in pairs:
            steps.append(f"x = {xv}, y = {yv}")
        result = "; ".join(f"(x={xv}, y={yv})" for xv, yv in pairs)
        return _ok(steps, result)
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
            steps = [f"Area = l × w = {l} × {w} = {area}",
                     f"Perimeter = 2(l + w) = 2({l} + {w}) = {perim}"]
            result = {"Area": area, "Perimeter": perim}

        elif shape == "square":
            s = v["side"]
            steps = [f"Area = s² = {s}² = {s**2}", f"Perimeter = 4s = 4×{s} = {4*s}"]
            result = {"Area": s**2, "Perimeter": 4 * s}

        elif shape == "triangle":
            a, b, c = v["a"], v["b"], v["c"]
            s = sp.Rational(1, 2) * (a + b + c)
            area = sp.sqrt(s * (s - a) * (s - b) * (s - c))
            steps = [
                f"Heron's formula: s = (a+b+c)/2 = ({a}+{b}+{c})/2 = {s}",
                f"Area = √[s(s−a)(s−b)(s−c)] = √[{s}({s}−{a})({s}−{b})({s}−{c})] = {sp.nsimplify(area)}",
                f"Perimeter = a+b+c = {a+b+c}",
            ]
            result = {"Area": sp.N(area, 4), "Perimeter": a + b + c}

        elif shape == "circle":
            r = v["radius"]
            area = sp.pi * r**2
            circ = 2 * sp.pi * r
            steps = [f"Area = πr² = π×{r}² = {area} ≈ {sp.N(area,4)}",
                     f"Circumference = 2πr = 2π×{r} = {circ} ≈ {sp.N(circ,4)}"]
            result = {"Area": sp.N(area, 4), "Circumference": sp.N(circ, 4)}

        elif shape == "parallelogram":
            b, h = v["base"], v["height"]
            steps = [f"Area = base × height = {b} × {h} = {b*h}"]
            result = {"Area": b * h}

        elif shape == "trapezium":
            a, b, h = v["a"], v["b"], v["height"]
            area = sp.Rational(1, 2) * (a + b) * h
            steps = [f"Area = ½(a+b)h = ½({a}+{b})×{h} = {area}"]
            result = {"Area": area}

        elif shape == "rhombus":
            d1, d2 = v["d1"], v["d2"]
            area = sp.Rational(1, 2) * d1 * d2
            steps = [f"Area = ½ d₁d₂ = ½×{d1}×{d2} = {area}"]
            result = {"Area": area}

        elif shape == "cone":
            r, h = v["radius"], v["height"]
            l = sp.sqrt(r**2 + h**2)
            vol = sp.Rational(1, 3) * sp.pi * r**2 * h
            csa = sp.pi * r * l
            tsa = csa + sp.pi * r**2
            steps = [
                f"Slant height, l = √(r²+h²) = √({r}²+{h}²) = {sp.N(l,4)}",
                f"Volume = ⅓πr²h = ⅓π×{r}²×{h} ≈ {sp.N(vol,4)}",
                f"Curved surface area = πrl = π×{r}×{sp.N(l,4)} ≈ {sp.N(csa,4)}",
                f"Total surface area = πrl + πr² ≈ {sp.N(tsa,4)}",
            ]
            result = {"Volume": sp.N(vol, 4), "Curved SA": sp.N(csa, 4), "Total SA": sp.N(tsa, 4)}

        elif shape == "cylinder":
            r, h = v["radius"], v["height"]
            vol = sp.pi * r**2 * h
            csa = 2 * sp.pi * r * h
            tsa = csa + 2 * sp.pi * r**2
            steps = [
                f"Volume = πr²h = π×{r}²×{h} ≈ {sp.N(vol,4)}",
                f"Curved surface area = 2πrh = 2π×{r}×{h} ≈ {sp.N(csa,4)}",
                f"Total surface area = 2πrh + 2πr² ≈ {sp.N(tsa,4)}",
            ]
            result = {"Volume": sp.N(vol, 4), "Curved SA": sp.N(csa, 4), "Total SA": sp.N(tsa, 4)}
        else:
            return _fail("Unknown shape.")

        result_str = ", ".join(f"{k} = {val}" for k, val in result.items())
        return _ok(steps, result_str)
    except KeyError as e:
        return _fail(f"Missing value: {e}")
    except Exception as e:
        return _fail(f"Could not compute: {e}")


def pythagoras(mode, a=None, b=None, c=None):
    try:
        a = sp.nsimplify(a) if a not in (None, "") else None
        b = sp.nsimplify(b) if b not in (None, "") else None
        c = sp.nsimplify(c) if c not in (None, "") else None
        if mode == "hypotenuse":
            h = sp.sqrt(a**2 + b**2)
            steps = [f"c² = a² + b² = {a}² + {b}² = {a**2 + b**2}",
                     f"c = √{a**2+b**2} ≈ {sp.N(h,4)}"]
            return _ok(steps, f"c ≈ {sp.N(h, 4)}")
        else:  # find a leg
            known, hyp = (a, c) if a is not None else (b, c)
            leg = sp.sqrt(hyp**2 - known**2)
            label = "a" if a is not None else "b"
            steps = [f"{label}² = c² − known² = {hyp}² − {known}² = {hyp**2 - known**2}",
                     f"{label} = √{hyp**2-known**2} ≈ {sp.N(leg,4)}"]
            return _ok(steps, f"{label} ≈ {sp.N(leg, 4)}")
    except Exception as e:
        return _fail(f"Could not compute: {e}")


def coordinate_geometry(x1, y1, x2, y2):
    try:
        x1, y1, x2, y2 = [sp.nsimplify(v) for v in (x1, y1, x2, y2)]
        dist = sp.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        mid = (sp.Rational(x1 + x2, 1) / 2, sp.Rational(y1 + y2, 1) / 2)
        steps = [
            f"Distance = √[(x₂−x₁)² + (y₂−y₁)²] = √[({x2}−{x1})² + ({y2}−{y1})²] ≈ {sp.N(dist,4)}",
            f"Midpoint = ((x₁+x₂)/2, (y₁+y₂)/2) = (({x1}+{x2})/2, ({y1}+{y2})/2) = ({mid[0]}, {mid[1]})",
        ]
        if x2 != x1:
            grad = sp.Rational(y2 - y1, x2 - x1) if (y2 - y1) == int(y2 - y1) and (x2 - x1) == int(x2 - x1) else (y2 - y1) / (x2 - x1)
            steps.append(f"Gradient, m = (y₂−y₁)/(x₂−x₁) = ({y2}−{y1})/({x2}−{x1}) = {grad}")
            c_val = sp.simplify(y1 - grad * x1)
            steps.append(f"Line equation: y − {y1} = {grad}(x − {x1})  →  y = {grad}x + {c_val}")
            result = f"Distance ≈ {sp.N(dist,4)}, Midpoint = ({mid[0]}, {mid[1]}), Gradient = {grad}, y = {grad}x + {c_val}"
        else:
            steps.append("Gradient is undefined (vertical line); equation: x = " + str(x1))
            result = f"Distance ≈ {sp.N(dist,4)}, Midpoint = ({mid[0]}, {mid[1]}), vertical line x = {x1}"
        return _ok(steps, result)
    except Exception as e:
        return _fail(f"Could not compute: {e}")


# ------------------------------------------------------------------ GRAPHS --

def table_of_values(expr_str, x_min, x_max, step=1):
    try:
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
    except Exception as e:
        return _fail(f"Could not evaluate: {e}")


def plot_functions_png(expr_str, expr2_str=None, x_min=-10, x_max=10):
    """Returns a base64-encoded PNG of the plotted function(s)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import io, base64

    x_min = float(x_min)
    x_max = float(x_max)
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
