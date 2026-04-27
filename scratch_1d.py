import sympy as sp

x = sp.Symbol('x')
e1 = (2*x - 3)/(x + 1) >= 1
# e1 = x > 0

sol = sp.solveset(e1, x, domain=sp.Reals)

def extract_intervals(sol_set):
    if sol_set.is_empty:
        return []
    if isinstance(sol_set, (sp.Interval, sp.FiniteSet)):
        return [sol_set]
    if isinstance(sol_set, sp.Union):
        return list(sol_set.args)
    if isinstance(sol_set, sp.ConditionSet):
        raise ValueError("Cannot resolve into explicit intervals.")
    if sol_set == sp.S.Reals:
        return [sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)]
    return [sol_set]

def format_set(sol_set):
    parts = []
    for part in extract_intervals(sol_set):
        if isinstance(part, sp.FiniteSet):
            parts.append(f"{{{', '.join(str(float(a.evalf())) for a in part.args)}}}")
            continue
        if not isinstance(part, sp.Interval):
            continue
            
        start = part.start
        end = part.end
        left_open = part.left_open
        right_open = part.right_open
        
        start_str = "-\\infty" if start == sp.S.NegativeInfinity else f"{float(start.evalf()):.2f}".rstrip('0').rstrip('.')
        end_str = "\\infty" if end == sp.S.Infinity else f"{float(end.evalf()):.2f}".rstrip('0').rstrip('.')
        
        lb = "(" if left_open or start == sp.S.NegativeInfinity else "["
        rb = ")" if right_open or end == sp.S.Infinity else "]"
        parts.append(f"{lb}{start_str}, {end_str}{rb}")
    
    if not parts:
        return "\\emptyset"
    return " \\cup ".join(parts)

print(format_set(sol))

intervals = extract_intervals(sol)

traces = []
bound_min = 0
bound_max = 0

for i, part in enumerate(intervals):
    if not isinstance(part, sp.Interval): continue
    s = float(part.start) if part.start != sp.S.NegativeInfinity else -20.0
    e = float(part.end) if part.end != sp.S.Infinity else 20.0
    
    bound_min = min(bound_min, s)
    bound_max = max(bound_max, e)
    
print(traces)
