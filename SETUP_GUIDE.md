# Compliance Engine - Setup Guide

## Quick Setup (5 minutes)

This project does **NOT** include `node_modules` or Python `venv` to keep the size small.
You need to install dependencies before running.

---

## Prerequisites

- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)

Check versions:
```bash
python3 --version
node --version
npm --version
```

---

## Backend Setup (2 minutes)

### Step 1: Navigate to backend directory
```bash
cd unified_system/backend
```

### Step 2: Create virtual environment
```bash
python3 -m venv venv
```

### Step 3: Activate virtual environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate
```

### Step 4: Install Python dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- flask
- flask-cors
- pandas
- numpy
- networkx
- python-dotenv
- scikit-learn

### Step 5: Start backend server
```bash
python api.py
```

You should see:
```
🚀 UNIFIED COMPLIANCE INTELLIGENCE PLATFORM - REST API v2.0
  Mode: MOCK (no API key)
  URL:  http://localhost:5000
Auto-initializing with default data...
  ✓ 21 requirements extracted
  ✓ 500 evidence records loaded
  ✓ 168 mappings created
 * Running on http://127.0.0.1:5000
```

---

## Frontend Setup (3 minutes)

Open a **NEW terminal window** (keep backend running).

### Step 1: Navigate to frontend directory
```bash
cd unified_system/frontend
```

### Step 2: Install Node.js dependencies
```bash
npm install
```

This will download ~121MB of dependencies (only needed once).

### Step 3: Start development server
```bash
npm run dev
```

You should see:
```
VITE v5.0.0  ready in 500 ms
➜  Local:   http://localhost:3000/
```

---

## Access the Application

Open your browser and go to:
```
http://localhost:3000
```

---

## Project Structure

```
Compliance_engine 2/
├── README.md                      # Main documentation
├── SETUP_GUIDE.md                 # This file
├── FUNCTIONALITY_TEST_REPORT.md   # Test results
├── .gitignore                     # Git ignore rules
│
└── unified_system/
    ├── QUICK_START.md
    ├── Compliance_Analysis.ipynb  # Jupyter notebook
    │
    ├── backend/                   # Python/Flask API
    │   ├── api.py                 # Main API server
    │   ├── requirements.txt       # Python dependencies
    │   ├── core/                  # Core modules
    │   │   ├── system_orchestrator.py
    │   │   ├── compliance_copilot.py
    │   │   ├── anomaly_classifier.py
    │   │   ├── confidence_engine.py
    │   │   ├── knowledge_graph.py
    │   │   └── ...
    │   ├── data/                  # Data files
    │   │   ├── compliance.db      # SQLite database
    │   │   ├── policy_documents.txt
    │   │   ├── evidence_artifacts.csv
    │   │   └── evidence_labels.csv
    │   └── venv/                  # (Created after setup)
    │
    └── frontend/                  # React/Vite UI
        ├── package.json           # Node dependencies
        ├── vite.config.js         # Vite config
        ├── src/
        │   ├── App.jsx            # Main component
        │   ├── pages/             # 10 UI pages
        │   │   ├── Dashboard.jsx
        │   │   ├── ComplianceCopilot.jsx
        │   │   ├── KnowledgeGraphPage.jsx
        │   │   ├── AnomalyDetection.jsx
        │   │   └── ...
        │   ├── components/        # Reusable components
        │   └── api/client.jsx     # API client
        └── node_modules/          # (Created after npm install)
```

---

## File Sizes

| Item | Size | Included? |
|------|------|-----------|
| **Source Code** | ~1.4 MB | ✅ Yes |
| **Python venv** | ~314 MB | ❌ No (install with pip) |
| **node_modules** | ~121 MB | ❌ No (install with npm) |
| **Total Compressed** | **~2 MB** | ✅ Ready to share |

---

## Troubleshooting

### Backend won't start

**Error:** `No module named 'flask'`

**Solution:**
```bash
cd unified_system/backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

### Frontend build fails

**Error:** `Cannot find module 'vite'`

**Solution:**
```bash
cd unified_system/frontend
rm -rf node_modules package-lock.json
npm install
```

---

### Port already in use

**Error:** `Port 5000 already in use`

**Solution (macOS/Linux):**
```bash
lsof -ti:5000 | xargs kill -9
```

**Solution (Windows):**
```cmd
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

---

### Database errors

**Error:** `unable to open database file`

**Solution:**
```bash
cd unified_system/backend
mkdir -p data
python api.py  # Will auto-initialize
```

---

## Optional Enhancements

### 1. Add OpenAI API Key (for GPT-powered features)

Create `.env` file in `unified_system/backend/`:
```
OPENAI_API_KEY=sk-your-key-here
```

Restart backend server.

### 2. Install PDF Generation

```bash
pip install weasyprint
# OR
pip install reportlab
```

### 3. Install Better Semantic Matching

```bash
pip install sentence-transformers
```

---

## Running Tests

### Backend API Test
```bash
curl http://localhost:5000/api/health
```

Expected:
```json
{
  "data": {
    "healthy": true,
    "version": "2.0.0"
  },
  "status": "success"
}
```

### Test Compliance Copilot
```bash
curl -X POST http://localhost:5000/api/copilot \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the GDPR status?"}'
```

---

## Deployment

### Production Backend
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api:app
```

### Production Frontend
```bash
npm run build
# Serve the dist/ folder with nginx or any static server
```

---

## Features

- ✅ 6 Compliance Frameworks (GDPR, SOX, NIST, PCI-DSS, ISO 27001, HIPAA)
- ✅ 21 Requirements extracted and structured
- ✅ 500 Evidence artifacts with automatic mapping
- ✅ AI-Powered Compliance Copilot
- ✅ Knowledge Graph (528 nodes)
- ✅ Anomaly Detection (91% precision, 94% recall)
- ✅ Challenge Audit (adversarial validation)
- ✅ Confidence Engine (5-factor scoring)
- ✅ Automated Report Generation

---

## Support

For issues or questions:
1. Check `FUNCTIONALITY_TEST_REPORT.md` for test results
2. Review `README.md` for detailed documentation
3. Check API endpoints at `http://localhost:5000/api/health`

---

## License

MIT License

---

**Enjoy your Compliance Engine!** 🚀
