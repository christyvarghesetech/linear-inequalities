document.getElementById('ineq-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const inputField = document.getElementById('ineq-input');
    const ineqStr = inputField.value;
    const errDiv = document.getElementById('error-message');
    const resultsDiv = document.getElementById('results');
    const btn = document.getElementById('solve-btn');
    
    if(!ineqStr.trim()){
        return;
    }

    errDiv.classList.add('hidden');
    resultsDiv.classList.add('hidden');
    
    btn.disabled = true;
    btn.textContent = 'Solving...';
    
    try {
        const response = await fetch('/api/solve', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ inequality: ineqStr })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Server error occurred');
        }
        
        renderResults(data);
    } catch(err) {
        errDiv.textContent = err.message;
        errDiv.classList.remove('hidden');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Solve & Plot';
    }
});

let globalSteps = [];
let globalGraph = null;
let globalIntervals = null;
let currentStepIndex = 0;

function renderResults(data) {
    globalSteps = data.steps;
    globalGraph = data.graph;
    globalIntervals = data.intervals;
    currentStepIndex = 0;

    const resultsDiv = document.getElementById('results');
    resultsDiv.classList.remove('hidden');
    
    // Clear Steps
    const stepsListContainer = document.getElementById('steps-list');
    stepsListContainer.innerHTML = '';
    
    const ul = document.createElement('ul');
    ul.id = 'steps-ul';
    stepsListContainer.appendChild(ul);
    
    // Hide graph initially
    const graphContainer = document.querySelector('.graph-container');
    if (graphContainer) graphContainer.classList.add('hidden');
    
    // Reset next button
    const nextBtn = document.getElementById('next-step-btn');
    if (nextBtn) nextBtn.classList.remove('hidden');
    
    // If no steps are present or empty, fallback
    if (!globalSteps || globalSteps.length === 0) {
        if (nextBtn) nextBtn.classList.add('hidden');
        showGraph();
        return;
    }
    
    // Show first step automatically
    renderNextStep();
}

function renderNextStep() {
    if (currentStepIndex < globalSteps.length) {
        const step = globalSteps[currentStepIndex];
        const ul = document.getElementById('steps-ul');
        
        const li = document.createElement('li');
        
        const desc = document.createElement('div');
        desc.className = 'step-desc';
        desc.textContent = step.step;
        
        const math = document.createElement('div');
        math.className = 'step-math';
        math.innerHTML = `\\[${step.math}\\]`;
        
        li.appendChild(desc);
        li.appendChild(math);
        ul.appendChild(li);
        
        if(window.MathJax) {
            MathJax.typesetPromise([li]).then(() => {});
        }
        
        currentStepIndex++;
        
        const nextBtn = document.getElementById('next-step-btn');
        if (currentStepIndex < globalSteps.length) {
            if (nextBtn) nextBtn.classList.remove('hidden');
        } else {
            if (nextBtn) nextBtn.classList.add('hidden');
            showGraph();
        }
    }
}

function showGraph() {
    const graphContainer = document.querySelector('.graph-container');
    if (graphContainer) graphContainer.classList.remove('hidden');
    
    const plotDiv = document.getElementById('plot-div');
    if (globalGraph && plotDiv) {
        Plotly.newPlot(plotDiv, globalGraph.data, globalGraph.layout, {responsive: true});
    }
    
    const intervalsDiv = document.getElementById('intervals-div');
    if (intervalsDiv) {
        if (globalIntervals && Object.keys(globalIntervals).length > 0) {
            intervalsDiv.classList.remove('hidden');
            document.querySelector('.intervals-content').innerHTML = '';
            for (const [key, value] of Object.entries(globalIntervals)) {
                const span = document.createElement('span');
                span.innerHTML = `\\( ${key} \\in ${value} \\)`;
                document.querySelector('.intervals-content').appendChild(span);
            }
            if(window.MathJax) {
                MathJax.typesetPromise([intervalsDiv]).then(() => {});
            }
        } else {
            intervalsDiv.classList.add('hidden');
        }
    }
}

// Attach listener to next button if it exists
document.addEventListener('DOMContentLoaded', () => {
    const nextBtn = document.getElementById('next-step-btn');
    if (nextBtn) {
        nextBtn.addEventListener('click', renderNextStep);
    }

    const modal = document.getElementById('graph-modal');
    const expandBtn = document.getElementById('expand-graph-btn');
    const closeBtn = document.querySelector('.close-btn');

    if (expandBtn) {
        expandBtn.addEventListener('click', () => {
            if (globalGraph) {
                modal.classList.remove('hidden');
                Plotly.newPlot('modal-plot-div', globalGraph.data, globalGraph.layout, {responsive: true});
            }
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
        });
    }

    // Close when clicking outside of modal content
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add('hidden');
        }
    });
});
