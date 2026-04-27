import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

transformations = (standard_transformations + (implicit_multiplication_application,))
exprs = ["2x - 3y > 6", "y < 2x", "x >= 4", "5 >= 2y + x"]
x, y = sp.symbols('x y')

for e in exprs:
    parsed = parse_expr(e, transformations=transformations, evaluate=False)
    print(f"Original: {parsed}")
    has_y = y in parsed.free_symbols
    var_to_solve = y if has_y else x
    try:
        solved = sp.solve(parsed, var_to_solve)
        print(f"Solved for {var_to_solve}: {solved} (Type: {type(solved)})")
        if isinstance(solved, sp.Relational):
            print(f"  LHS: {solved.lhs}, RHS: {solved.rhs}, RelOp: {solved.rel_op}")
    except NotImplementedError:
        print(f"Failed to solve for {var_to_solve}.")
