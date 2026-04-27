import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

transformations = (standard_transformations + (implicit_multiplication_application,))
x = sp.symbols('x')

def solve_step_by_step_1d(rel, var):
    steps = []
    steps.append({"step": "Original Inequality", "math": str(rel)})
    
    diff = rel.lhs - rel.rhs
    expanded = sp.expand(diff)
    
    try:
        poly = sp.Poly(expanded, var)
        if poly.degree() != 1:
            return None
    except sp.PolynomialError:
        return None
        
    coeffs = poly.all_coeffs() # returns [a, b] for ax+b, even if b is 0
    if len(coeffs) == 2:
        a, b = coeffs
    else:
        # constant? 
        return None
        
    op = rel.rel_op
    
    class RelBuilder:
        @staticmethod
        def make(lhs, op, rhs):
            if op == '>': return sp.StrictGreaterThan(lhs, rhs, evaluate=False)
            elif op == '>=': return sp.GreaterThan(lhs, rhs, evaluate=False)
            elif op == '<': return sp.StrictLessThan(lhs, rhs, evaluate=False)
            elif op == '<=': return sp.LessThan(lhs, rhs, evaluate=False)

    new_rel = RelBuilder.make(a*var, op, -b)
    
    # Don't add structural match if it's the same
    if sp.simplify(rel.lhs - a*var) != 0 or sp.simplify(rel.rhs - (-b)) != 0:
        steps.append({
            "step": "Group terms (variables on the left, constants on the right)",
            "math": str(new_rel)
        })
        
    if a != 1 and a != 0:
        flip_dict = {'>': '<', '>=': '<=', '<': '>', '<=': '>='}
        if a < 0:
            step_desc = f"Divide both sides by {a}, and flip the inequality sign"
            final_op = flip_dict[op]
        else:
            step_desc = f"Divide both sides by {a}"
            final_op = op
            
        final_rhs = sp.simplify(-b / a)
        final_rel = RelBuilder.make(var, final_op, final_rhs)
        
        steps.append({
            "step": step_desc,
            "math": str(final_rel)
        })
        
    return steps

exprs = ["2x + 3 > 7", "-3x + 5 <= 2", "-x < -4", "x / 2 >= 3"]
for e in exprs:
    parsed = parse_expr(e, transformations=transformations, evaluate=False)
    print(f"\n--- {e} ---")
    for s in solve_step_by_step_1d(parsed, x):
        print(f"Step: {s['step']}  =>  {s['math']}")
