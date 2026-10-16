"""Matrices: operations, determinant & inverse, simultaneous equations, transformations."""
import base64
import io
import math
import re
from fractions import Fraction
import topics
import poly as P
from tcommon import *
from frac_numeric import _ok, _fail

MAXN = 5


def mx(M):
    rows = "".join("<tr>" + "".join(f"<td>{v if isinstance(v, str) else fr(v)}</td>" for v in r) + "</tr>" for r in M)
    return f'<table class="mx">{rows}</table>'


def mxs(M, scalar=None):
    return (f"{fr(scalar)}" if scalar is not None else "") + mx(M)


def parse_matrix(text, label="matrix"):
    s = (text or "").strip()
    if not s or len(s) > 400:
        raise UErr(f"Please type {label}, for example: 1 2; 3 4")
    s = re.sub(r"\]\s*,?\s*\[", ";", s).replace("[", "").replace("]", "").replace("(", "").replace(")", "")
    rows = [r for r in re.split(r"[;\n|]+", s) if r.strip()]
    if len(rows) > MAXN:
        raise UErr(f"{label}: please use at most {MAXN} rows.")
    M = []
    for r in rows:
        items = [t for t in re.split(r"[,\s]+", r.strip()) if t]
        if len(items) > MAXN:
            raise UErr(f"{label}: please use at most {MAXN} columns.")
        M.append([num(t, f"an entry of {label}") for t in items])
    if len({len(r) for r in M}) != 1:
        raise UErr(f"{label}: every row must have the same number of entries. Separate rows with a semicolon (;).")
    return M


def dims(M):
    return f"{len(M)}&times;{len(M[0])}"


def transpose(M):
    return [list(r) for r in zip(*M)]


def mmul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]


def det2(a, b, c, d):
    return a * d - b * c


def det(M):
    n = len(M)
    if n == 1:
        return M[0][0]
    if n == 2:
        return det2(M[0][0], M[0][1], M[1][0], M[1][1])
    return sum((-1) ** j * M[0][j] * det([r[:j] + r[j + 1:] for r in M[1:]]) for j in range(n))


def minor(M, i, j):
    return [r[:j] + r[j + 1:] for k, r in enumerate(M) if k != i]


def sg(v):
    return fm(v, 4) if v >= 0 else f"({fm(v, 4)})"


# ---------------------------------------------------------------- operations --

@guard
def operations(d):
    op = d.get("op", "add")
    A = parse_matrix(d.get("A"), "matrix A")
    steps = [f"<b>Matrix A</b> (size {dims(A)}):  {mx(A)}"]
    B = None
    if op in ("add", "sub", "mul", "mulBA"):
        B = parse_matrix(d.get("B"), "matrix B")
        steps.append(f"<b>Matrix B</b> (size {dims(B)}):  {mx(B)}")
    if op in ("add", "sub"):
        if (len(A), len(A[0])) != (len(B), len(B[0])):
            raise UErr(f"You can only {'add' if op == 'add' else 'subtract'} matrices of the SAME size. A is {dims(A)} but B is {dims(B)}.")
        sym = "+" if op == "add" else MINUS
        steps.append(f"<b>Rule:</b> {'add' if op == 'add' else 'subtract'} the entries in the same positions.")
        lines = []
        R = []
        for i in range(len(A)):
            R.append([])
            for j in range(len(A[0])):
                v = A[i][j] + B[i][j] if op == "add" else A[i][j] - B[i][j]
                R[-1].append(v)
                lines.append(f"Row {i + 1}, column {j + 1}: {sg(A[i][j])} {sym} {sg(B[i][j])} = {fm(v, 4)}")
        steps.append("<br>".join(lines))
        return _ok(steps, f"<b>A {sym} B =</b> {mx(R)}")
    if op in ("mul", "mulBA"):
        if op == "mulBA":
            A, B = B, A
            steps.append("<b>We work out B &times; A</b> (the order matters in matrix multiplication!). So the left matrix is B and the right matrix is A.")
        if len(A[0]) != len(B):
            raise UErr(f"These cannot be multiplied: the left matrix has {len(A[0])} column(s) but the right matrix has {len(B)} row(s). "
                       f"The number of columns of the first must equal the number of rows of the second.")
        steps.append(f"<b>Check the sizes:</b> {dims(A)} &times; {dims(B)} &rarr; the inner numbers ({len(A[0])} and {len(B)}) match, "
                     f"so we can multiply, and the answer has size {len(A)}&times;{len(B[0])} (the outer numbers).")
        steps.append("<b>Rule:</b> to get the entry in row i, column j, multiply row i of the left matrix by column j of the right matrix, "
                     "pair by pair, then add.")
        lines = []
        R = [[Fraction(0)] * len(B[0]) for _ in A]
        for i in range(len(A)):
            for j in range(len(B[0])):
                prods = [A[i][k] * B[k][j] for k in range(len(B))]
                v = sum(prods)
                R[i][j] = v
                expr = " + ".join(f"{sg(A[i][k])}&times;{sg(B[k][j])}" for k in range(len(B)))
                lines.append(f"Row {i + 1} &times; column {j + 1}: {expr} = {' + '.join(sg(p) for p in prods)} = <b>{fm(v, 4)}</b>")
        steps.append("<br>".join(lines))
        return _ok(steps, f"<b>{'BA' if op == 'mulBA' else 'AB'} =</b> {mx(R)}")
    if op == "scalar":
        k = num(d.get("k"), "the number k")
        steps.append(f"<b>Rule:</b> to multiply a matrix by a number, multiply EVERY entry by that number.")
        R = [[k * v for v in r] for r in A]
        steps.append("<br>".join(f"Row {i + 1}: " + ", ".join(f"{sg(k)}&times;{sg(v)} = {fm(k * v, 4)}" for v in r) for i, r in enumerate(A)))
        return _ok(steps, f"<b>{fm(k, 4)}A =</b> {mx(R)}")
    if op == "transpose":
        steps.append("<b>Rule:</b> the transpose swaps rows and columns: row 1 becomes column 1, row 2 becomes column 2, and so on.")
        return _ok(steps, f"<b>A<sup>T</sup> =</b> {mx(transpose(A))}")
    if op == "square":
        if len(A) != len(A[0]):
            raise UErr("Only a square matrix can be squared.")
        steps.append("<b>A<sup>2</sup> means A &times; A.</b>")
        lines = []
        R = mmul(A, A)
        n = len(A)
        for i in range(n):
            for j in range(n):
                expr = " + ".join(f"{sg(A[i][k])}&times;{sg(A[k][j])}" for k in range(n))
                lines.append(f"Row {i + 1} &times; column {j + 1}: {expr} = <b>{fm(R[i][j], 4)}</b>")
        steps.append("<br>".join(lines))
        return _ok(steps, f"<b>A<sup>2</sup> =</b> {mx(R)}")
    raise UErr("Choose an operation.")


# ------------------------------------------------------------ determinant etc --

def _det_steps(M, steps):
    n = len(M)
    if n == 2:
        a, b, c, d = M[0][0], M[0][1], M[1][0], M[1][1]
        v = det2(a, b, c, d)
        steps.append(f"<b>Determinant of a 2&times;2 matrix</b> {mx([['a', 'b'], ['c', 'd']]).replace('<td>', '<td>')} is ad &minus; bc "
                     f"(multiply the main diagonal, subtract the product of the other diagonal).")
        steps.append(f"det = ({sg(a)})({sg(d)}) &minus; ({sg(b)})({sg(c)}) = {fm(a * d, 4)} &minus; ({fm(b * c, 4)}) = <span class='hl'>{fm(v, 4)}</span>")
        return v
    if n == 3:
        steps.append("<b>Determinant of a 3&times;3 matrix</b> (expand along the first row): "
                     "a(ei &minus; fh) &minus; b(di &minus; fg) + c(dh &minus; eg), where the letters are the entries in order.")
        parts = []
        lines = []
        total = Fraction(0)
        for j in range(3):
            m = minor(M, 0, j)
            mv = det2(m[0][0], m[0][1], m[1][0], m[1][1])
            sign = 1 if j % 2 == 0 else -1
            term = sign * M[0][j] * mv
            total += term
            lines.append(f"{'+' if sign > 0 else MINUS} {sg(M[0][j])} &times; (minor {mx(m)}= {fm(mv, 4)})  = {fm(term, 4)}")
        steps.append("<br>".join(lines))
        steps.append(f"Add: det = {' + '.join(sg(Fraction(0)) for _ in [])}"
                     f"{fm(total, 4)}".replace(" + ", "") if False else f"Add the three results: det = <span class='hl'>{fm(total, 4)}</span>")
        return total
    raise UErr("Only 2&times;2 and 3&times;3 determinants are shown here.")


@guard
def detinv(d):
    M = parse_matrix(d.get("A"), "the matrix")
    n = len(M)
    if n != len(M[0]) or n not in (2, 3):
        raise UErr("Please enter a square matrix, 2&times;2 or 3&times;3.")
    what = d.get("what", "det")
    steps = [f"<b>The matrix:</b> {mx(M)}"]
    dv = _det_steps(M, steps)
    if what == "det":
        return _ok(steps, f"<b>|A| = {fm(dv, 4)}</b>" + ("  &nbsp;(singular: the matrix has no inverse)" if dv == 0 else ""))
    if dv == 0:
        steps.append("<b>The determinant is 0</b>, so the matrix is <b>singular</b> and has <b>no inverse</b>.")
        return _ok(steps, "<b>No inverse exists (determinant = 0)</b>")
    steps.append(f"<b>The determinant is not 0</b>, so an inverse exists. A<sup>&minus;1</sup> = {FR('1', 'det')} &times; (adjoint of A) = {FR('1', fm(dv, 4))} &times; adjoint.")
    if n == 2:
        a, b, c, dd = M[0][0], M[0][1], M[1][0], M[1][1]
        adj = [[dd, -b], [-c, a]]
        steps.append(f"<b>Adjoint of a 2&times;2:</b> swap the two numbers on the main diagonal ({sg(a)} and {sg(dd)}) and change the signs of the other two ({sg(b)} and {sg(c)}): {mx(adj)}")
    else:
        cof = [[(-1) ** (i + j) * det(minor(M, i, j)) for j in range(3)] for i in range(3)]
        lines = []
        for i in range(3):
            for j in range(3):
                m = minor(M, i, j)
                mv = det2(m[0][0], m[0][1], m[1][0], m[1][1])
                lines.append(f"Position ({i + 1},{j + 1}): cover row {i + 1} and column {j + 1} &rarr; minor = {fm(mv, 4)}; sign {'+' if (i + j) % 2 == 0 else MINUS} &rarr; cofactor <b>{fm(cof[i][j], 4)}</b>")
        steps.append("<b>Step A - Find the cofactor of every entry:</b> cover its row and column, take the determinant of what is left (the minor), "
                     "then apply the sign pattern + &minus; + / &minus; + &minus; / + &minus; +.<br>" + "<br>".join(lines))
        steps.append(f"<b>Matrix of cofactors:</b> {mx(cof)}")
        adj = transpose(cof)
        steps.append(f"<b>Step B - Transpose it</b> (swap rows and columns) to get the adjoint: {mx(adj)}")
    inv = [[v / dv for v in r] for r in adj]
    steps.append(f"<b>Step C - Divide every entry by the determinant ({fm(dv, 4)}):</b> {mx(inv)}")
    chk = mmul(M, inv)
    ident = all(chk[i][j] == (1 if i == j else 0) for i in range(n) for j in range(n))
    steps.append(f"<b>Check:</b> A &times; A<sup>&minus;1</sup> = {mx(chk)} " + ("= the identity matrix &#10003;" if ident else ""))
    return _ok(steps, f"<b>A<sup>&minus;1</sup> =</b> {mx(inv)}")


# --------------------------------------------------- simultaneous equations ---

@guard
def simult(d):
    text = (d.get("eqs") or "").strip()
    if not text or len(text) > 300:
        raise UErr("Type the equations separated by commas, for example: 2x + 3y = 8, x - y = 1")
    items = [t.strip() for t in re.split(r"[;,\n]+", P.normalise(text)) if t.strip()]
    if not 2 <= len(items) <= 3:
        raise UErr("Please give 2 or 3 equations.")
    polys = []
    for it in items:
        if it.count("=") != 1:
            raise UErr(f"'{esc(it)}' needs exactly one = sign.")
        L, R = it.split("=")
        try:
            p = P.parse_poly(L) - P.parse_poly(R)
        except P.ParseError as e:
            raise UErr(str(e))
        polys.append(p)
    vs = sorted(set(v for p in polys for v in p.vars()))
    n = len(items)
    if len(vs) != n:
        raise UErr(f"You gave {n} equations but {len(vs)} different letters ({', '.join(vs) or 'none'}). They must match.")
    if any(p.total_degree() > 1 for p in polys):
        raise UErr("Matrices solve equations with only first powers (no x&sup2; or xy).")
    A = []
    Bv = []
    for p in polys:
        row = []
        for v in vs:
            row.append(sum((c for k, c in p.t.items() if k == ((v, 1),)), Fraction(0)))
        A.append(row)
        Bv.append([-p.const_value()])
    steps = ["<b>Step 1 - Write the equations in matrix form AX = B</b> (coefficients, unknowns, answers):<br>" + mx(A) + mx([[v] for v in vs]) + " = " + mx(Bv)]
    dv = det(A)
    steps.append(f"<b>Step 2 - Find the determinant of A</b> (the coefficient matrix).")
    _det_steps(A, steps)
    if dv == 0:
        steps.append("The determinant is 0, so there is <b>no single solution</b> (the equations either contradict each other or are repeats of one another).")
        return _ok(steps, "<b>No unique solution (determinant = 0)</b>")
    steps.append("<b>Step 3 - Find the inverse of A.</b>")
    if n == 2:
        a, b, c, dd = A[0][0], A[0][1], A[1][0], A[1][1]
        adj = [[dd, -b], [-c, a]]
        steps.append(f"Swap the diagonal numbers, change the signs of the other two: {mx(adj)}; divide by the determinant {fm(dv, 4)}.")
    else:
        cof = [[(-1) ** (i + j) * det(minor(A, i, j)) for j in range(3)] for i in range(3)]
        adj = transpose(cof)
        steps.append(f"Cofactors: {mx(cof)}; transpose to get the adjoint: {mx(adj)}; divide by the determinant {fm(dv, 4)}.")
    inv = [[v / dv for v in r] for r in adj]
    steps.append(f"A<sup>&minus;1</sup> = {mx(inv)}")
    X = mmul(inv, Bv)
    steps.append("<b>Step 4 - Multiply:</b> since AX = B, we get X = A<sup>&minus;1</sup>B.<br>" + mx(inv) + mx(Bv) + " = " + mx(X))
    sol = {v: X[i][0] for i, v in enumerate(vs)}
    chk = []
    for it, p in zip(items, polys):
        lhs = Fraction(0)
        for k, c in p.t.items():
            if k == ():
                lhs += c
            else:
                (vv, e), = k
                lhs += c * sol[vv]
        chk.append(lhs == 0)
    steps.append("<b>Step 5 - Check</b> by putting the answers back into the original equations: " + ("all are true &#10003;" if all(chk) else "something is wrong"))
    return _ok(steps, "<b>" + ", &nbsp; ".join(f"{v} = {fr(sol[v])}" for v in vs) + "</b>")


# ------------------------------------------------------------ transformations --

_PTS = re.compile(r"([A-Za-z]?)\s*\(\s*([^,()]+?)\s*,\s*([^,()]+?)\s*\)")


def parse_points(text, maxn=8):
    found = _PTS.findall(text or "")
    if not found:
        raise UErr("Type the points like A(1,1), B(3,1), C(3,2).")
    if len(found) > maxn:
        raise UErr(f"Please use at most {maxn} points.")
    out = []
    for i, (nm, x, y) in enumerate(found):
        out.append((nm.upper() or "ABCDEFGH"[i], num(x, "an x-coordinate"), num(y, "a y-coordinate")))
    return out


def describe(M):
    a, b, c, dd = M[0][0], M[0][1], M[1][0], M[1][1]
    dv = det2(a, b, c, dd)
    lines = []
    ortho = (a * a + c * c == 1 and b * b + dd * dd == 1 and a * b + c * dd == 0)
    kind = None
    if M == [[1, 0], [0, 1]]:
        kind = "the <b>identity</b>: nothing moves."
    elif b == 0 and c == 0 and a == dd:
        kind = f"an <b>enlargement</b>, centre (0, 0), scale factor <b>{fm(a, 4)}</b>" + (" (negative: the image is on the opposite side of the centre)" if a < 0 else "") + "."
    elif ortho and dv == 1:
        ang = math.degrees(math.atan2(float(c), float(a)))
        kind = f"a <b>rotation</b> about (0, 0) through <b>{ang:.4g}&deg; anticlockwise</b>" + (f" (the same as {360 - ang:.4g}&deg; clockwise)" if 0 < ang < 360 else "") + "."
    elif ortho and dv == -1:
        th = math.atan2(float(c), float(a)) / 2
        t = math.tan(th)
        if abs(math.cos(th)) < 1e-9:
            line = "x = 0 (the y-axis)"
        elif abs(t) < 1e-9:
            line = "y = 0 (the x-axis)"
        else:
            line = f"y = {fm(Fraction(t).limit_denominator(1000), 4)}x"
            if abs(t - 1) < 1e-9:
                line = "y = x"
            elif abs(t + 1) < 1e-9:
                line = "y = &minus;x"
        kind = f"a <b>reflection</b> in the line <b>{line}</b>."
    elif b == 0 and c == 0:
        parts = []
        if a != 1:
            parts.append(f"a stretch of scale factor {fm(a, 4)} parallel to the x-axis (the y-axis is invariant)")
        if dd != 1:
            parts.append(f"a stretch of scale factor {fm(dd, 4)} parallel to the y-axis (the x-axis is invariant)")
        kind = "a <b>stretch</b>: " + " and ".join(parts) + "."
    elif a == 1 and dd == 1 and c == 0 and b != 0:
        kind = f"a <b>shear</b> with the x-axis invariant, shear factor <b>{fm(b, 4)}</b>."
    elif a == 1 and dd == 1 and b == 0 and c != 0:
        kind = f"a <b>shear</b> with the y-axis invariant, shear factor <b>{fm(c, 4)}</b>."
    else:
        kind = "a general linear transformation (not one of the single standard ones; it may be a combination)."
    lines.append(f"This matrix represents {kind}")
    lines.append(f"Determinant = {fm(dv, 4)}, so <b>areas are multiplied by {fm(abs(dv), 4)}</b>" + (" and the shape is flipped over (orientation reversed)." if dv < 0 else ".") if dv != 0
                 else "Determinant = 0: everything collapses onto a line (no inverse).")
    return " ".join(lines[:1]) + "<br>" + lines[1]


def plot_transform(pts, M):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    img = [(nm, M[0][0] * x + M[0][1] * y, M[1][0] * x + M[1][1] * y) for nm, x, y in pts]
    allx = [float(p[1]) for p in pts] + [float(p[1]) for p in img] + [0]
    ally = [float(p[2]) for p in pts] + [float(p[2]) for p in img] + [0]
    pad = max(max(allx) - min(allx), max(ally) - min(ally), 4) * 0.15 + 0.5
    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    ax.axhline(0, color="#111827", lw=1.2)
    ax.axvline(0, color="#111827", lw=1.2)
    ox = [float(p[1]) for p in pts]
    oy = [float(p[2]) for p in pts]
    ix = [float(p[1]) for p in img]
    iy = [float(p[2]) for p in img]
    if len(pts) >= 3:
        ax.fill(ox, oy, color="#93c5fd", alpha=0.5, label="object")
        ax.fill(ix, iy, color="#fca5a5", alpha=0.5, label="image")
    ax.plot(ox + [ox[0]], oy + [oy[0]], "o-", color="#2563eb", lw=2)
    ax.plot(ix + [ix[0]], iy + [iy[0]], "o-", color="#dc2626", lw=2)
    for (nm, x, y), (_, X, Y) in zip(pts, img):
        ax.annotate(nm, (float(x), float(y)), textcoords="offset points", xytext=(7, 6), color="#1d4ed8", fontsize=11, fontweight="bold")
        ax.annotate(nm + "'", (float(X), float(Y)), textcoords="offset points", xytext=(7, 6), color="#b91c1c", fontsize=11, fontweight="bold")
    ax.set_xlim(min(allx) - pad, max(allx) + pad)
    ax.set_ylim(min(ally) - pad, max(ally) + pad)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend(loc="best") if len(pts) >= 3 else None
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii"), img


_STD = {
    "refx": ("reflection in the x-axis (y = 0)", lambda k: [[1, 0], [0, -1]]),
    "refy": ("reflection in the y-axis (x = 0)", lambda k: [[-1, 0], [0, 1]]),
    "refd": ("reflection in the line y = x", lambda k: [[0, 1], [1, 0]]),
    "refnd": ("reflection in the line y = &minus;x", lambda k: [[0, -1], [-1, 0]]),
    "rot90": ("rotation of 90&deg; anticlockwise about the origin", lambda k: [[0, -1], [1, 0]]),
    "rot180": ("rotation of 180&deg; about the origin", lambda k: [[-1, 0], [0, -1]]),
    "rot270": ("rotation of 270&deg; anticlockwise (90&deg; clockwise) about the origin", lambda k: [[0, 1], [-1, 0]]),
    "enl": ("enlargement, centre the origin, scale factor k", lambda k: [[k, 0], [0, k]]),
    "strx": ("stretch parallel to the x-axis with scale factor k", lambda k: [[k, 0], [0, 1]]),
    "stry": ("stretch parallel to the y-axis with scale factor k", lambda k: [[1, 0], [0, k]]),
    "shx": ("shear, x-axis invariant, shear factor k", lambda k: [[1, k], [0, 1]]),
    "shy": ("shear, y-axis invariant, shear factor k", lambda k: [[1, 0], [k, 1]]),
}


@guard
def transform(d):
    kind = d.get("kind", "apply")
    steps = []
    if kind == "std":
        key = d.get("std", "refx")
        nm, fn = _STD[key]
        k = num(d.get("k"), "k", blank=True) if key in ("enl", "strx", "stry", "shx", "shy") else Fraction(1)
        if k is None:
            raise UErr("Please fill in k for this transformation.")
        M = [[Fraction(v) for v in r] for r in fn(k)]
        steps.append(f"<b>Idea:</b> the columns of the matrix are where the points (1, 0) and (0, 1) go.")
        steps.append(f"Under the {nm}: (1, 0) goes to ({fm(M[0][0], 4)}, {fm(M[1][0], 4)}) and (0, 1) goes to ({fm(M[0][1], 4)}, {fm(M[1][1], 4)}).")
        steps.append("Put these in as the first and second columns of the matrix.")
        steps.append(describe(M))
        return _ok(steps, f"<b>Matrix =</b> {mx(M)}")
    if kind == "cols":
        pi = parse_points(d.get("i"))
        pj = parse_points(d.get("j"))
        if len(pi) != 1 or len(pj) != 1:
            raise UErr("Give ONE point in each box, like (0, 1).")
        M = [[pi[0][1], pj[0][1]], [pi[0][2], pj[0][2]]]
        steps.append("<b>Idea:</b> the first column of the matrix is the image of (1, 0), and the second column is the image of (0, 1).")
        steps.append(f"Image of (1, 0) is ({fm(pi[0][1], 4)}, {fm(pi[0][2], 4)}), image of (0, 1) is ({fm(pj[0][1], 4)}, {fm(pj[0][2], 4)}).")
        steps.append(f"So the matrix is {mx(M)}")
        steps.append(describe(M))
        return _ok(steps, f"<b>Matrix =</b> {mx(M)}")
    if kind == "from2":
        obj = parse_points(d.get("pts"))
        img = parse_points(d.get("imgs"))
        if len(obj) != 2 or len(img) != 2:
            raise UErr("Give exactly TWO object points and their TWO images.")
        P0 = [[obj[0][1], obj[1][1]], [obj[0][2], obj[1][2]]]
        Q = [[img[0][1], img[1][1]], [img[0][2], img[1][2]]]
        dv = det(P0)
        if dv == 0:
            raise UErr("The two object points lie on a line through the origin, so they cannot fix the matrix. Choose different points.")
        steps.append(f"<b>Idea:</b> let the matrix be M. Then M &times; (object points as columns) = (image points as columns), so M = (images) &times; (objects)<sup>&minus;1</sup>.")
        steps.append(f"Objects as columns: {mx(P0)} &nbsp; Images as columns: {mx(Q)}")
        steps.append(f"<b>Inverse of the object matrix:</b> determinant = {fm(dv, 4)}; swap the diagonal, change the other signs, divide by {fm(dv, 4)}.")
        inv = [[P0[1][1] / dv, -P0[0][1] / dv], [-P0[1][0] / dv, P0[0][0] / dv]]
        steps.append(mx(inv))
        M = mmul(Q, inv)
        steps.append(f"<b>Multiply:</b> M = {mx(Q)}{mx(inv)} = {mx(M)}")
        steps.append(describe(M))
        return _ok(steps, f"<b>M =</b> {mx(M)}")
    # apply
    M = parse_matrix(d.get("M"), "the matrix")
    if len(M) != 2 or len(M[0]) != 2:
        raise UErr("Use a 2&times;2 matrix like 0 -1; 1 0.")
    pts = parse_points(d.get("pts"))
    steps.append(f"<b>Matrix:</b> {mx(M)}")
    steps.append("<b>Rule:</b> to transform a point (x, y), write it as a column and multiply: "
                 f"{mx([['a', 'b'], ['c', 'd']])}{mx([['x'], ['y']])} = {mx([['ax + by'], ['cx + dy']])}")
    lines = []
    for nm, x, y in pts:
        X = M[0][0] * x + M[0][1] * y
        Y = M[1][0] * x + M[1][1] * y
        lines.append(f"{nm}({fm(x, 4)}, {fm(y, 4)}): x' = {sg(M[0][0])}({sg(x)}) + {sg(M[0][1])}({sg(y)}) = <b>{fm(X, 4)}</b>, "
                     f"y' = {sg(M[1][0])}({sg(x)}) + {sg(M[1][1])}({sg(y)}) = <b>{fm(Y, 4)}</b> &rarr; {nm}'({fm(X, 4)}, {fm(Y, 4)})")
    steps.append("<br>".join(lines))
    steps.append(describe(M))
    b64, img = plot_transform(pts, M)
    txt = "<b>Images:</b> " + ", ".join(f"{nm}'({fm(x, 4)}, {fm(y, 4)})" for nm, x, y in img) + "<br>" + describe(M)
    return _ok(steps, {"image": b64, "text": txt})


# ------------------------------------------------------------------- spec -----

SPEC = {
    "title": "Matrices",
    "intro": "Matrix arithmetic, determinants, inverses, simultaneous equations and transformations. Type a matrix with spaces between entries and a semicolon between rows, e.g. <b>1 2; 3 4</b>.",
    "tabs": [
        {"id": "mo", "label": "Operations", "title": "Add, subtract, multiply, transpose", "endpoint": "ops",
         "fields": [select("op", "Operation", [("add", "A + B"), ("sub", "A &minus; B"), ("mul", "A &times; B"), ("mulBA", "B &times; A"),
                                               ("scalar", "k &times; A"), ("transpose", "Transpose of A"), ("square", "A squared")], wide=True),
                    field("A", "Matrix A", "1 2; 3 4"),
                    field("B", "Matrix B", "0 1; -1 5", show_if={"op": ["add", "sub", "mul", "mulBA"]}),
                    field("k", "Number k", "3", show_if={"op": "scalar"})]},
        {"id": "mi", "label": "Determinant & inverse", "title": "Determinant and inverse", "endpoint": "detinv",
         "fields": [field("A", "Square matrix (2&times;2 or 3&times;3)", "3 1; 5 2"),
                    select("what", "Find", [("det", "the determinant only"), ("inv", "the inverse (and determinant)")])]},
        {"id": "ms", "label": "Simultaneous equations", "title": "Solve equations with matrices", "endpoint": "simult",
         "hint": "Example: <i>2x + 3y = 8, x - y = 1</i> or three equations in x, y, z.",
         "fields": [field("eqs", "Equations (separate with commas)", "2x + 3y = 8, x - y = 1", wide=True, half=False)]},
        {"id": "mt", "label": "Transformations", "title": "Matrix transformations", "endpoint": "transform",
         "hint": "The columns of a transformation matrix are the images of (1, 0) and (0, 1).",
         "fields": [select("kind", "What do you want to do?", [("apply", "Apply a matrix to points (and draw it)"),
                                                                 ("std", "Matrix for a standard transformation"),
                                                                 ("cols", "Matrix from the images of (1,0) and (0,1)"),
                                                                 ("from2", "Matrix from two points and their images")], wide=True),
                    field("M", "Matrix (2&times;2)", "0 -1; 1 0", show_if={"kind": "apply"}),
                    field("pts", "Points", "A(1,1), B(3,1), C(3,2)", wide=True, half=False, show_if={"kind": ["apply"]}),
                    select("std", "Transformation", [(k, v[0]) for k, v in _STD.items()], wide=True, show_if={"kind": "std"}),
                    field("k", "k (scale / shear factor)", "2", show_if={"kind": "std"}),
                    field("i", "Image of (1, 0)", "(0, 1)", show_if={"kind": "cols"}),
                    field("j", "Image of (0, 1)", "(-1, 0)", show_if={"kind": "cols"}),
                    field("pts", "Two object points", "(1,0), (1,1)", wide=True, half=False, show_if={"kind": "from2"}),
                    field("imgs", "Their two images (same order)", "(0,1), (-1,1)", wide=True, half=False, show_if={"kind": "from2"})]},
    ],
}

topics.register("matrices", SPEC, {"ops": operations, "detinv": detinv, "simult": simult, "transform": transform})
