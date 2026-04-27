# Linear Inequality Explainer & Grapher

A web application that allows students to input linear inequalities, visualizes the solution regions on an interactive Cartesian plane, and provides step-by-step, AI-generated explanations on how to solve them.

## Features

- **Solve Linear Inequalities**: Capable of solving multiple complex linear inequalities (e.g., `-3x + 5 <= 2`, `y > 2x - 1`).
- **Interactive Graphing**: Visualizes the boundaries, shaded regions, and intersection of the inequalities using Plotly.
- **AI Tutor Explanations**: Generates supportive, step-by-step teacher-like explanations formatted in LaTeX using the Gemini API.
- **Modern User Interface**: A clean frontend for data entry, beautifully formatted step display, and responsive graphing.

## Tech Stack

- **Backend**: Python, Flask
- **Math Engine**: SymPy (for symbolic evaluation and expression manipulation)
- **Graphing**: Plotly (Python generation, Plotly.js for rendering)
- **AI Integration**: Google GenAI SDK (Gemini 2.5 Flash)
- **Frontend**: HTML, CSS, Vanilla JavaScript, MathJax (for LaTeX rendering)

## Overview 

When an inequality is submitted, the Flask backend uses SymPy to parse the expression safely and isolate the relevant variable (`x` or `y`). It then determines the boundary conditions and shading domains to construct a Plotly JSON schema. Concurrently, a structured prompt is sent to the Gemini API, asking it to act as an encouraging math teacher and provide step-by-step instructions. Both the steps and the graph JSON are returned to the frontend, where Plotly.js renders the graph and MathJax processes the LaTeX text.

## Setup Instructions

### Prerequisites
Make sure you have Python 3.8+ installed.

### 1. Clone or Download the repository
Navigate into your project directory.

### 2. Create a Virtual Environment
```bash
python -m venv venv
```

### 3. Activate the Environment
- On Windows:
  ```bash
  venv\Scripts\activate
  ```
- On macOS/Linux:
  ```bash
  source venv/bin/activate
  ```

### 4. Install Dependencies
Ensure you have the required packages. You might normally install via a `requirements.txt`. Key packages include:
```bash
pip install flask sympy plotly python-dotenv google-genai
```

### 5. Setup Environment Variables
Create a `.env` file in the root of the project to store your API credentials securely:
```env
# .env file content
GEMINI_API_KEY=your_gemini_api_key_here
```
> **Note**: You must replace `your_gemini_api_key_here` with a real Google Gemini API key to activate the AI tutor feature. Without it, the graph will still generate but the text steps will show a fallback warning.

### 6. Run the Application
Start the Flask development server:
```bash
python app.py
```
Open up your browser and go to `http://localhost:5000` to start exploring linear inequalities!

## Running Tests

This project includes regression and unit tests for the core logic:
- `test_solve.py`: Validates the SymPy mathematical solving mechanics.
- `test_steps.py`: Validates steps formatting.
- `test_sympy.py`: Tests underlying sympy parsing edge cases.
- `test_genai.py`: Validates Gemini prompt payloads.

You can run these via `pytest` or Python's built-in `unittest` if configured:
```bash
python -m unittest discover .
```
