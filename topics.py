"""
Topic registry.

Every topic built on the generic page template is described here by a SPEC (tabs and
form fields) and a dict of HANDLERS (one function per tab).  A handler receives the
form values as a dict of strings and returns the usual
{"ok", "steps", "result", "error"} dictionary.
"""

# (key, label, short description, group)
TOPIC_INFO = [
    # --- Number & Algebra
    ("algebra", "Algebra", "Linear, quadratic and simultaneous equations, factorisation and completing the square.", "Number & Algebra"),
    ("fractions", "Fractions", "LCM, HCF, proper and improper fractions, algebraic fractions.", "Number & Algebra"),
    ("indices", "Indices", "Laws of indices, evaluating and solving index equations.", "Number & Algebra"),
    ("logarithms", "Logarithms", "Laws of logarithms, equations, log tables and antilog.", "Number & Algebra"),
    ("surds", "Surds", "Simplify, operate, rationalise and solve surd equations.", "Number & Algebra"),
    ("sequences", "Sequences", "Arithmetic and geometric progressions and series.", "Number & Algebra"),
    ("sets", "Sets", "Set operations and Venn diagram problems.", "Number & Algebra"),
    ("variation", "Variation", "Direct, inverse, joint and partial variation.", "Number & Algebra"),
    ("bases", "Number Bases", "Convert between bases, calculate in any base, find an unknown base.", "Number & Algebra"),
    ("percent", "Percentages & Ratio", "Percentages, ratio, proportion, profit and loss, simple and compound interest.", "Number & Algebra"),
    ("inequalities", "Inequalities", "Linear and quadratic inequalities, number lines, graphs and linear programming.", "Number & Algebra"),
    ("matrices", "Matrices", "Operations, determinants, inverses, simultaneous equations and transformations.", "Number & Algebra"),
    ("binops", "Binary Operations & Modular Arithmetic", "Closure, identity, inverse, tables, congruences and remainders.", "Number & Algebra"),
    # --- Geometry & Trigonometry
    ("angles", "Angles", "All angle rules with clear diagrams: lines, parallel lines, triangles, quadrilaterals, polygons and circles.", "Geometry & Trigonometry"),
    ("transform", "Transformations", "Reflection, rotation, translation, enlargement and combined transformations with diagrams.", "Geometry & Trigonometry"),
    ("vectors", "Vectors", "Column vectors, magnitude, direction, position vectors, ratio division and parallel vectors.", "Geometry & Trigonometry"),
    ("conics", "Ellipse, Parabola & Hyperbola", "Analyse and draw conic sections: foci, vertices, directrix, asymptotes and eccentricity.", "Graphs & Calculus"),
    ("quadgraph", "Quadratic Functions & Graphs", "Vertex, axis of symmetry, roots, intercepts, completing the square and sketching.", "Graphs & Calculus"),
    ("numsense", "Standard Form & Approximation", "Standard form, significant figures, decimal places, estimation and error.", "Number & Algebra"),
    ("commerce", "Commercial Arithmetic", "Tax, VAT, rates, commission, discount, hire purchase, wages and currency exchange.", "Number & Algebra"),
    ("geometry", "Geometry", "Area, perimeter, volume, Pythagoras and coordinate geometry.", "Geometry & Trigonometry"),
    ("circles", "Circle Theorems & Mensuration", "Circle theorems with diagrams, arcs, sectors, cones, spheres and similar figures.", "Geometry & Trigonometry"),
    ("loci", "Loci & Constructions", "Construction steps with drawings and combined loci regions.", "Geometry & Trigonometry"),
    ("trigonometry", "Trigonometry", "SOHCAHTOA, sine rule, cosine rule and elevation.", "Geometry & Trigonometry"),
    ("bearings", "Bearings", "Bearing conversion, back bearings and journeys with a sketch.", "Geometry & Trigonometry"),
    ("earthgeo", "Longitude & Latitude", "Distances on the earth, locations and speed, with globe sketches.", "Geometry & Trigonometry"),
    # --- Graphs & Calculus
    ("graphs", "Graphs", "Tables of values, plotting and intersections.", "Graphs & Calculus"),
    ("calculus", "Calculus", "Differentiation, integration, turning points, tangents and areas.", "Graphs & Calculus"),
    # --- Statistics
    ("statistics", "Statistics & Probability", "Averages, grouped data, charts, probability, permutations and combinations.", "Statistics & Probability"),
]

TOPIC_LABELS = {k: label for k, label, _d, _g in TOPIC_INFO}
TOPIC_LABELS["earthgeo"] = "Longitude & Latitude"

SPECS = {}      # topic -> spec dict (see solve_generic.html)
HANDLERS = {}   # topic -> {sub: callable(data) -> result dict}


def register(topic, spec, handlers):
    SPECS[topic] = spec
    HANDLERS[topic] = handlers


def _load():
    """Import each topic module; a module that fails to import must not take the site down."""
    import importlib
    import logging
    for mod in ("t_variation", "t_bases", "t_percent", "t_inequalities", "t_matrices",
                "t_calculus", "t_circles", "t_loci", "t_binops", "t_angles", "t_conics", "t_transform", "t_quadgraph", "t_vectors", "t_numsense", "t_commerce"):
        try:
            importlib.import_module(mod)
        except ModuleNotFoundError as e:  # module not built yet / missing
            if e.name != mod:
                logging.getLogger(__name__).exception("Topic module %s failed", mod)
        except Exception:
            logging.getLogger(__name__).exception("Topic module %s failed to load", mod)
