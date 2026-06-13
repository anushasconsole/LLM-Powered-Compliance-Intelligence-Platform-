# Unified Compliance Intelligence Platform

Automated compliance evidence collection, audit, and reporting system.
Covers GDPR · SOX · NIST · PCI-DSS · ISO 27001 · HIPAA across a full AI pipeline.

---

## Architecture

```
Frontend (React 18 + Vite)
        ↓  HTTP /api/*
Flask REST API  (api.py)
        ↓
System Orchestrator  ←── coordinates all modules
        │
        ├── LLM Requirement Extractor   policy text → structured requirements
        ├── Semantic Mapper             evidence ↔ requirement matching
        ├── Knowledge Graph             NetworkX — policy/req/evidence relationships
        ├── Challenge Auditor           adversarial stress-test of evidence quality
        ├── Confidence Engine           multi-factor scoring (freshness · diversity · reliability)
        ├── Narrative Generator         AI audit narratives per requirement
        ├── Compliance Copilot          natural language query interface
        └── SQLite Database             all state persisted in data/compliance.db
```

---

## Folder Structure

```
unified_system/
├── backend/
│   ├── core/
│   │   ├── api.py                      Flask REST API (entry point)
│   │   ├── system_orchestrator.py      Full pipeline coordinator
│   │   ├── llm_requirement_extractor.py  Policy parser (mock + OpenAI)
│   │   ├── semantic_mapper.py          Synonym + Jaccard evidence matching
│   │   ├── knowledge_graph.py          NetworkX graph of all entities
│   │   ├── challenge_auditor.py        Adversarial audit checks
│   │   ├── confidence_engine.py        Multi-factor confidence scoring
│   │   ├── narrative_generator.py      Audit narrative writer
│   │   ├── compliance_copilot.py       NL query router
│   │   └── database.py                 SQLite ORM layer
│   ├── data/
│   │   ├── policy_documents.txt        Sample policies (GDPR/NIST/SOX etc.)
│   │   ├── evidence_artifacts.csv      500 sample evidence records
│   │   └── compliance.db               SQLite database (auto-created)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/                      9 UI pages
│   │   ├── components/                 Navbar, ParticlesBackground
│   │   ├── api/client.jsx              Axios API client
│   │   ├── App.jsx                     Router + loading screen
│   │   └── index.jsx                   React entry point
│   ├── vite.config.js                  Vite + proxy config
│   ├── tailwind.config.cjs
│   ├── postcss.config.cjs
│   └── package.json
├── start_backend.bat                   One-click backend start (Windows)
├── start_frontend.bat                  One-click frontend start (Windows)
└── README.md
```

---

## How to Run

### Prerequisites

- Python 3.9+ installed  →  `python --version`
- Node.js 18+ installed  →  `node --version`

### Step 1 — Start the Backend

Open a terminal and run:

```cmd
cd unified_system\backend
python api.py
```

Or double-click `start_backend.bat`.

You should see:

```
🚀 UNIFIED COMPLIANCE INTELLIGENCE PLATFORM - REST API v2.0
  Mode: MOCK (no API key)
  URL:  http://localhost:5000
Auto-initializing with default data...
  ✓ 13 requirements extracted
  ✓ 500 evidence records loaded
  ✓ 104 mappings created
 * Running on http://0.0.0.0:5000
```

### Step 2 — Start the Frontend

Open a **second** terminal:

```cmd
cd unified_system\frontend
.\node_modules\.bin\vite.cmd
```

Or double-click `start_frontend.bat`.

You should see:

```
VITE v5.4.21  ready in ~600ms
➜  Local:   http://localhost:3000/
```

### Step 3 — Open the App

Go to **http://localhost:3000** in your browser.

> If port 3000 is taken, Vite will use 3001 — check your terminal output for the exact URL.

---

## First-Time Setup

The backend auto-initializes on startup using the bundled data files.
If the dashboard shows zeros, go to **Settings → Initialize with Default Data**.

---

## Pages

| Page | Route | What it does |
|------|-------|-------------|
| Dashboard | `/` | Live stats, framework scores, charts |
| Compliance Copilot | `/copilot` | Ask natural language compliance questions |
| Evidence | `/evidence` | Browse and filter all 500 evidence artifacts |
| Analysis | `/analysis` | Run per-framework compliance scoring |
| Challenge Audit | `/challenge-audit` | Adversarial audit — finds weak evidence |
| Confidence Engine | `/confidence` | Multi-factor scores + AI narratives per requirement |
| Knowledge Graph | `/knowledge-graph` | Visual graph of policy → requirement → evidence |
| Reports | `/reports` | Generate and download full audit reports |
| Settings | `/settings` | System health, initialize, rebuild mappings |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/dashboard` | Summary stats |
| GET | `/api/frameworks` | Per-framework scores |
| POST | `/api/initialize` | Load policies + evidence |
| GET | `/api/analysis/{fw}` | Run compliance analysis |
| POST | `/api/challenge-audit/{fw}` | Run adversarial audit |
| GET | `/api/confidence/{fw}` | Confidence scores + narratives |
| POST | `/api/copilot` | Natural language query |
| GET | `/api/evidence` | All evidence (supports ?framework= ?search= ?status=) |
| GET | `/api/requirements` | All extracted requirements |
| POST | `/api/reports/generate` | Generate full audit report |
| GET | `/api/reports` | List all generated reports |
| GET | `/api/knowledge-graph` | Graph nodes + edges for visualization |

---

## Configuration

### Mock mode (default — no API key needed)

Works out of the box. Uses template-based requirement extraction and synonym matching.

### Live mode (OpenAI)

Set the `OPENAI_API_KEY` environment variable before starting the backend:

```cmd
set OPENAI_API_KEY=sk-...
python api.py
```

This enables GPT-4 powered requirement extraction and narrative generation.

### Install dependencies (first time only)

**Backend:**
```cmd
cd unified_system\backend
pip install flask flask-cors networkx python-dotenv
```

**Frontend** (already installed via node_modules):
```cmd
cd unified_system\frontend
npm install --legacy-peer-deps
```

---

## Pipeline Flow

1. **Policy Upload** — raw text in `data/policy_documents.txt`
2. **LLM Extractor** — parses policies into structured requirements (framework, severity, burden of proof, evidence types)
3. **Semantic Mapper** — matches each evidence artifact to requirements using synonym groups + Jaccard similarity, boosted by framework match
4. **Knowledge Graph** — builds a directed graph: `Policy → Requirement → Evidence → Framework`
5. **Challenge Auditor** — adversarial checks per requirement: missing evidence, stale (>90 days), single-source, rejected, low confidence, conflicting
6. **Confidence Engine** — calculates weighted score: 40% freshness · 25% count/diversity · 15% source reliability · 10% review status · 10% semantic quality
7. **Narrative Generator** — writes executive summary, detailed narrative, risk assessment, and recommendation per requirement
8. **Report** — comprehensive JSON audit report stored in SQLite and downloadable

---

## Compliance Frameworks Supported

GDPR · SOX · NIST SP 800-53 · PCI-DSS · ISO 27001 · HIPAA · CIS

---

## Tech Stack

**Backend:** Python 3.9+ · Flask · SQLite · NetworkX · no ML dependencies required

**Frontend:** React 18 · Vite 5 · Tailwind CSS · Framer Motion · Recharts · Axios
