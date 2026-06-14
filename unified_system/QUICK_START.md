# Quick Start Guide

## Run the System (2 steps)

### Step 1 — Backend
```cmd
cd unified_system\backend
pip install flask flask-cors networkx python-dotenv pandas numpy scikit-learn
python api.py
```
Expected: `Running on http://0.0.0.0:5000`

### Step 2 — Frontend
```cmd
cd unified_system\frontend
.\node_modules\.bin\vite.cmd
```
Open **http://localhost:3000**

---

## Optional: Live LLM mode (OpenAI)
```cmd
set OPENAI_API_KEY=sk-...
python api.py
```

## Optional: PDF report export
```cmd
pip install weasyprint
# OR
pip install reportlab
```

## Optional: Better semantic matching
```cmd
pip install sentence-transformers
```

---

## Jupyter Notebook
```cmd
pip install jupyter matplotlib seaborn plotly
jupyter notebook Compliance_Analysis.ipynb
```

---

## What the system covers

| Requirement | Status |
|---|---|
| Policy parser — 6 frameworks, 21 requirements | ✅ |
| Evidence mapping — semantic + synonym matching | ✅ |
| Anomaly classifier — Precision 84.8%, Recall 100% | ✅ |
| Confidence engine — multi-factor scoring | ✅ |
| Challenge auditor — adversarial gap detection | ✅ |
| Narrative generator — AI audit narratives | ✅ |
| PDF / HTML report download | ✅ |
| 4 evidence integrations (CloudTrail, Config, Splunk, Certs) | ✅ |
| Knowledge graph visualisation | ✅ |
| Compliance Copilot (NL queries) | ✅ |
| Dashboard + 10 UI pages | ✅ |
| Jupyter notebook | ✅ |
| 500 evidence records + ground-truth labels | ✅ |
