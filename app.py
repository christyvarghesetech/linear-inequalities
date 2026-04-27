from flask import Flask, request, jsonify, render_template
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import plotly.graph_objs as go
import json
import plotly
import os
import math
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(override=True)

app = Flask(__name__)
transformations = (standard_transformations + (implicit_multiplication_application,))
x, y = sp.symbols('x y')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/solve', methods=['POST'])
def solve_ineq():
    data = request.json
    ineq_str = data.get('inequality', '').strip()
    
    if not ineq_str:
        return jsonify({"error": "No inequality provided"}), 400
        
    # Allow comma or newline separation
    ineq_texts = [s.strip() for s in ineq_str.replace(';', '\n').replace(',', '\n').split('\n') if s.strip()]
    if not ineq_texts:
        return jsonify({"error": "No inequality provided"}), 400

    fig = go.Figure()

    colors = [
        ('rgba(99, 102, 241, 1)', 'rgba(99, 102, 241, 0.2)'), # Indigo
        ('rgba(239, 68, 68, 1)', 'rgba(239, 68, 68, 0.2)'), # Red
        ('rgba(16, 185, 129, 1)', 'rgba(16, 185, 129, 0.2)'), # Emerald
        ('rgba(245, 158, 11, 1)', 'rgba(245, 158, 11, 0.2)'), # Amber
        ('rgba(139, 92, 246, 1)', 'rgba(139, 92, 246, 0.2)'), # Violet
    ]

    try:
        parsed_inequalities = []
        all_free_syms = set()

        for idx, text in enumerate(ineq_texts):
            parsed_ineq = parse_expr(text, transformations=transformations, evaluate=False)
            if not hasattr(parsed_ineq, 'rel_op'):
                return jsonify({"error": f"No inequality operator found in '{text}'."}), 400
            
            free_vars = {s for s in parsed_ineq.free_symbols if not s.is_number}
            all_free_syms.update(free_vars)
            parsed_inequalities.append((idx, text, parsed_ineq))
            
        if not all_free_syms:
            return jsonify({"error": "Inequalities must contain variables"}), 400
            
        is_1d_mode = len(all_free_syms) == 1
        intervals = None
        
        if is_1d_mode:
            var_1d = list(all_free_syms)[0]
            final_set = sp.S.Reals
            
            for idx, text, parsed_ineq in parsed_inequalities:
                try:
                    sol = sp.solveset(parsed_ineq, var_1d, domain=sp.Reals)
                    final_set = sp.Intersection(final_set, sol)
                except Exception as e:
                    return jsonify({"error": f"Could not solve 1D inequality '{text}'. {str(e)}"}), 400
            
            def extract_intervals(sol_set):
                if sol_set.is_empty: return []
                if isinstance(sol_set, (sp.Interval, sp.FiniteSet)): return [sol_set]
                if isinstance(sol_set, sp.Union): return list(sol_set.args)
                if sol_set == sp.S.Reals: return [sp.Interval(sp.S.NegativeInfinity, sp.S.Infinity)]
                return [sol_set]
                
            def format_set(sol_set):
                parts = []
                for part in extract_intervals(sol_set):
                    if isinstance(part, sp.FiniteSet):
                        parts.append(f"{{{', '.join(str(float(a.evalf())) for a in part.args)}}}")
                        continue
                    if not isinstance(part, sp.Interval): continue
                    st = part.start
                    en = part.end
                    ss = "-\\infty" if st == sp.S.NegativeInfinity else f"{float(st.evalf()):g}"
                    es = "\\infty" if en == sp.S.Infinity else f"{float(en.evalf()):g}"
                    lb = "(" if part.left_open or st == sp.S.NegativeInfinity else "["
                    rb = ")" if part.right_open or en == sp.S.Infinity else "]"
                    parts.append(f"{lb}{ss}, {es}{rb}")
                return " \\cup ".join(parts) if parts else "\\emptyset"
            
            var_str = str(var_1d)
            intervals = {var_str: format_set(final_set)}
            
            # 1D Plotly Mapping
            fig.add_trace(go.Scatter(x=[-20, 20], y=[0, 0], mode='lines', line=dict(color='black', width=2), hoverinfo='skip', showlegend=False))
            axis_bounds = [-10, 10]
            
            for idx, part in enumerate(extract_intervals(final_set)):
                if isinstance(part, sp.FiniteSet):
                    for pt in part.args:
                        val = float(pt.evalf())
                        fig.add_trace(go.Scatter(x=[val], y=[0], mode='markers', marker=dict(color='rgba(16, 185, 129, 1)', size=12, symbol='circle'), name=f'{var_str}={val:.2f}'))
                        axis_bounds = [min(axis_bounds[0], val-5), max(axis_bounds[1], val+5)]
                    continue
                if not isinstance(part, sp.Interval): continue
                st = float(part.start.evalf()) if part.start != sp.S.NegativeInfinity else -25.0
                en = float(part.end.evalf()) if part.end != sp.S.Infinity else 25.0
                
                axis_bounds = [min(axis_bounds[0], st-5 if st > -24 else -10), max(axis_bounds[1], en+5 if en < 24 else 10)]
                
                fig.add_trace(go.Scatter(x=[st, en], y=[0, 0], mode='lines', line=dict(color='rgba(16, 185, 129, 0.6)', width=8), name=format_set(part)))
                
                if part.start != sp.S.NegativeInfinity:
                    sym = 'circle-open' if part.left_open else 'circle'
                    fig.add_trace(go.Scatter(x=[st], y=[0], mode='markers', marker=dict(color='rgba(16, 185, 129, 1)', size=12, symbol=sym, line=dict(color='rgba(16, 185, 129, 1)', width=2)), showlegend=False))
                
                if part.end != sp.S.Infinity:
                    sym = 'circle-open' if part.right_open else 'circle'
                    fig.add_trace(go.Scatter(x=[en], y=[0], mode='markers', marker=dict(color='rgba(16, 185, 129, 1)', size=12, symbol=sym, line=dict(color='rgba(16, 185, 129, 1)', width=2)), showlegend=False))
            
            fig.update_layout(
                xaxis=dict(range=[axis_bounds[0], axis_bounds[1]], zeroline=True, zerolinewidth=2, zerolinecolor='rgba(0,0,0,0.5)', gridcolor='rgba(0,0,0,0.1)', title=var_str.upper()),
                yaxis=dict(range=[-2, 2], showgrid=False, zeroline=False, showticklabels=False, title=''),
                plot_bgcolor='white', paper_bgcolor='rgba(255,255,255,1)', margin=dict(l=20, r=20, t=20, b=20),
                showlegend=True, legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01), hovermode='closest'
            )
        else:
            # 2D Linear Solver (Existing Logic)
            half_spaces = [
                (1.0, 0.0, 15.0, '>='),
                (-1.0, 0.0, 15.0, '>='),
                (0.0, 1.0, 15.0, '>='),
                (0.0, -1.0, 15.0, '>=')
            ]
            
            parsed_2d = []
            for idx, text, parsed_ineq in parsed_inequalities:
                free_syms = parsed_ineq.free_symbols
                has_y = y in free_syms
                has_x = x in free_syms
                if not has_x and not has_y:
                    return jsonify({"error": f"Inequality '{text}' must contain 'x' or 'y'"}), 400
                
                try:
                    expr = parsed_ineq.lhs - parsed_ineq.rhs
                    A = float(expr.diff(x))
                    B = float(expr.diff(y))
                    C = float(expr.subs({x:0, y:0}))
                except Exception:
                    return jsonify({"error": f"Cannot solve multiple variables unless strictly linear: '{text}'"}), 400
                    
                op = parsed_ineq.rel_op
                half_spaces.append((A, B, C, op))
                parsed_2d.append((idx, text, A, B, C, op))
                
            for (idx, text, A, B, C, op) in parsed_2d:
                line_c, _ = colors[idx % len(colors)]
                line_dict = dict(color=line_c, width=3)
                if op in ['<', '>']: line_dict['dash'] = 'dash'
                
                y_vals = []
                x_vals = []
                if abs(B) > 1e-9:
                    x_vals = [-15, 15]
                    y_vals = [(-C - A*xv)/B for xv in x_vals]
                else:
                    c_val = -C / A
                    x_vals = [c_val, c_val]
                    y_vals = [-15, 15]

                fig.add_trace(go.Scatter(
                    x=x_vals, y=y_vals, mode='lines', line=line_dict, name=text
                ))

            lines = [(A, B, C) for (A, B, C, op) in half_spaces]
            intersection_points = []
            for i in range(len(lines)):
                for j in range(i+1, len(lines)):
                    A1, B1, C1 = lines[i]
                    A2, B2, C2 = lines[j]
                    det = A1*B2 - A2*B1
                    if abs(det) > 1e-9:
                        px = (B1*C2 - B2*C1) / det
                        py = (A2*C1 - A1*C2) / det
                        if -16 <= px <= 16 and -16 <= py <= 16:
                            intersection_points.append((px, py))
                        
            valid_vertices = []
            for px, py in intersection_points:
                valid = True
                for (A, B, C, op) in half_spaces:
                    val = A*px + B*py + C
                    tol = 1e-5
                    if op == '<' and val > tol: valid = False; break
                    if op == '<=' and val > tol: valid = False; break
                    if op == '>' and val < -tol: valid = False; break
                    if op == '>=' and val < -tol: valid = False; break
                if valid:
                    valid_vertices.append((px, py))
                    
            unique_vertices = []
            for vp in valid_vertices:
                if not any(math.isclose(vp[0], uv[0], abs_tol=1e-4) and math.isclose(vp[1], uv[1], abs_tol=1e-4) for uv in unique_vertices):
                    unique_vertices.append(vp)
                    
            if unique_vertices and len(unique_vertices) > 1:
                try:
                    min_x = min(p[0] for p in unique_vertices)
                    max_x = max(p[0] for p in unique_vertices)
                    min_y = min(p[1] for p in unique_vertices)
                    max_y = max(p[1] for p in unique_vertices)
                    
                    def format_interval(min_v, max_v):
                        min_is_inf = min_v <= -14.99
                        max_is_inf = max_v >= 14.99
                        if min_is_inf and max_is_inf: return "(-\\infty, \\infty)"
                        min_s = "-\\infty" if min_is_inf else f"{min_v:g}"
                        max_s = "\\infty" if max_is_inf else f"{max_v:g}"
                        left_bracket = "(" if min_is_inf else "["
                        right_bracket = ")" if max_is_inf else "]"
                        return f"{left_bracket}{min_s}, {max_s}{right_bracket}"
                        
                    intervals = {
                        "x": format_interval(min_x, max_x),
                        "y": format_interval(min_y, max_y)
                    }
                except Exception:
                    pass

            if len(unique_vertices) > 2:
                cx = sum(p[0] for p in unique_vertices) / len(unique_vertices)
                cy = sum(p[1] for p in unique_vertices) / len(unique_vertices)
                
                unique_vertices.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
                
                fill_poly_x = [p[0] for p in unique_vertices] + [unique_vertices[0][0]]
                fill_poly_y = [p[1] for p in unique_vertices] + [unique_vertices[0][1]]
                
                fig.add_trace(go.Scatter(
                    x=fill_poly_x, y=fill_poly_y, fill='toself',
                    fillcolor='rgba(16, 185, 129, 0.4)', mode='none',
                    name='Feasible Region', hoverinfo='skip'
                ))

            fig.update_layout(
                xaxis=dict(range=[-10, 10], zeroline=True, zerolinewidth=2, zerolinecolor='rgba(0,0,0,0.5)', gridcolor='rgba(0,0,0,0.1)', title='X'),
                yaxis=dict(range=[-10, 10], zeroline=True, zerolinewidth=2, zerolinecolor='rgba(0,0,0,0.5)', gridcolor='rgba(0,0,0,0.1)', title='Y'),
                plot_bgcolor='white', paper_bgcolor='rgba(255,255,255,1)', margin=dict(l=20, r=20, t=20, b=20),
                showlegend=True, legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01), hovermode='closest'
            )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # Generate teacher-like explanations via OpenAI API
        try:
            combined_ineqs = "\n".join(ineq_texts)
            prompt = f"""You are a helpful and experienced math teacher.
A student is trying to solve the following linear inequalities:
{combined_ineqs}

Provide a simple, clear, step-by-step explanation for how to solve each inequality. Keep your explanations short and encouraging. If applicable, explicitly mention the rule for flipping the inequality sign when dividing or multiplying by a negative number.

You MUST output your response as a JSON object containing a single key "steps". "steps" should be an array of objects. 
Each object MUST have two string keys: 
1. "step": A simple, clear text explanation.
2. "math": The mathematical equation for that step in valid LaTeX. (do NOT wrap the LaTeX in $$ or \\( \\)).

Example Output:
{{
  "steps": [
    {{"step": "Let's isolate x in the first inequality.", "math": "-3x + 5 \\leq 2"}},
    {{"step": "Subtract 5 from both sides.", "math": "-3x \\leq -3"}},
    {{"step": "Divide both sides by -3. Remember to flip the inequality sign!", "math": "x \\geq 1"}}
  ]
}}
"""
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key or api_key == 'your_gemini_api_key_here':
                raise ValueError("Valid Gemini API key not found in .env file.")

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            steps_json = json.loads(response.text)
            final_steps = steps_json.get("steps", [])
        except ValueError as e:
            final_steps = [
                {"step": "API Configuration Required", "math": "Error"},
                {"step": "Please insert a valid Gemini API key in your .env file.", "math": "\\text{Setup needed}"}
            ]
        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "UNAVAILABLE" in error_msg or "high demand" in error_msg.lower():
                final_steps = [
                    {"step": "API Temporarily Unavailable", "math": "Error 503"},
                    {"step": "The AI tutor model is currently experiencing high demand. Please try clicking Solve again in a moment.", "math": "\\text{Please retry}"}
                ]
            elif "429" in error_msg or "exhausted" in error_msg.lower() or "quota" in error_msg.lower():
                final_steps = [
                    {"step": "API Quota Exceeded", "math": "Error 429"},
                    {"step": "The AI tutor model rate limit or quota has been reached.", "math": "\\text{Rate limit}"}
                ]
            else:
                final_steps = [
                    {"step": "Error generating AI steps", "math": "Error"},
                    {"step": f"An unexpected error occurred: {error_msg[:60]}...", "math": "\\text{Failed}"}
                ]

        return jsonify({
            "steps": final_steps,
            "graph": json.loads(graphJSON),
            "intervals": intervals
        })

    except Exception as e:
        return jsonify({"error": f"Failed to parse or solve. Did you enter valid linear inequalities? Error: str({e})"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
