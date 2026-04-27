import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from app import get_step_by_step, x, y, transformations
import traceback

ineq_str = "-3x + 5 <= 2"
try:
    parsed_ineq = parse_expr(ineq_str, transformations=transformations, evaluate=False)
    free_syms = parsed_ineq.free_symbols
    has_y = y in free_syms
    has_x = x in free_syms

    var_to_solve = y if has_y else x
    
    step_res = get_step_by_step(parsed_ineq, var_to_solve)
    if step_res[0]:
        steps, solved = step_res
    else:
        print("step_res is False")

    solved_op = solved.rel_op
    
    # Ensure var is on LHS
    if solved.lhs != var_to_solve:
         pass
         
    bound_expr = solved.rhs if solved.lhs == var_to_solve else solved.lhs
    is_x_solved = (var_to_solve == x)

    # Build Plotly Data
    x_vals = [-15, 15]
    y_vals = []
    fill_poly_x = []
    fill_poly_y = []
    
    if not is_x_solved: # solved for Y
        try:
            y_func = sp.lambdify(x, bound_expr, "math")
            y_vals = [float(y_func(v)) for v in x_vals]
        except Exception:
            val = float(bound_expr.evalf())
            y_vals = [val, val]
            
        if solved_op in ['<', '<=']:
            fill_poly_x = [x_vals[0], x_vals[1], x_vals[1], x_vals[0]]
            fill_poly_y = [-30, -30, y_vals[1], y_vals[0]]
        else:
            fill_poly_x = [x_vals[0], x_vals[1], x_vals[1], x_vals[0]]
            fill_poly_y = [30, 30, y_vals[1], y_vals[0]]
            
    else: # solved for X
        val = float(bound_expr.evalf())
        c = val
        x_vals = [c, c]
        y_vals = [-30, 30]
        
        if solved_op in ['<', '<=']:
            fill_poly_x = [-30, -30, c, c]
            fill_poly_y = [30, -30, -30, 30]
        else:
            fill_poly_x = [30, 30, c, c]
            fill_poly_y = [30, -30, -30, 30]
            
    print("Success")
except Exception as e:
    traceback.print_exc()
