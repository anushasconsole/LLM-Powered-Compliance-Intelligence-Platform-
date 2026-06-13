"""
Dashboard Generator - Creates a standalone interactive HTML compliance dashboard.
"""
import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from policy_parser import load_policies
from evidence_analyzer import (
    load_evidence, classify_anomalies, build_evidence_nodes,
    build_proof_graph, get_framework_summary, get_anomaly_summary
)
from report_generator import generate_narrative


def build_dashboard_data(chains, df, anomaly_summary, framework_summary):
    """Build JSON payload for the dashboard."""
    findings = []
    for chain in chains:
        supporting = [
            {
                "id": e.evidence_id,
                "type": e.evidence_type.replace("_", " "),
                "confidence": round(e.confidence_score * 100),
                "age_days": e.freshness_days,
                "status": e.status,
                "collected_by": e.collected_by,
                "description": e.description[:80] + "..." if len(e.description) > 80 else e.description,
            }
            for e in chain.supporting_evidence[:4]
        ]
        undermining = [
            {
                "id": e.evidence_id,
                "type": e.evidence_type.replace("_", " "),
                "anomaly": e.anomaly_type,
                "status": e.status,
            }
            for e in chain.undermining_evidence[:3]
        ]
        findings.append({
            "req_id": chain.requirement_id,
            "req_text": chain.requirement_text,
            "policy": chain.policy_name,
            "frameworks": chain.frameworks,
            "status": chain.compliance_status,
            "confidence": round(chain.overall_confidence * 100),
            "supporting": supporting,
            "undermining": undermining,
            "burdens_ok": chain.addressed_burdens,
            "burdens_gap": chain.unaddressed_burdens,
            "objections": chain.devils_advocate_objections,
            "narrative": generate_narrative(chain),
        })

    # Evidence anomaly data for chart
    anomaly_by_type = []
    for k, v in anomaly_summary["by_type"].items():
        anomaly_by_type.append({"label": k.replace("_", " "), "count": v})

    # Framework compliance data
    fw_data = []
    for fw, stats in framework_summary.items():
        total = stats["total"]
        pct = round(stats["compliant"] / total * 100) if total > 0 else 0
        fw_data.append({
            "name": fw,
            "compliant": stats["compliant"],
            "conditional": stats["conditional"],
            "at_risk": stats["at_risk"],
            "non_compliant": stats["non_compliant"],
            "total": total,
            "pct": pct,
        })

    # Evidence freshness histogram buckets
    freshness_buckets = {"0-30d": 0, "31-60d": 0, "61-90d": 0, "91-120d": 0, "120d+": 0}
    for v in df["freshness_days"]:
        if v <= 30: freshness_buckets["0-30d"] += 1
        elif v <= 60: freshness_buckets["31-60d"] += 1
        elif v <= 90: freshness_buckets["61-90d"] += 1
        elif v <= 120: freshness_buckets["91-120d"] += 1
        else: freshness_buckets["120d+"] += 1

    return {
        "findings": findings,
        "anomaly_by_type": anomaly_by_type,
        "framework_data": fw_data,
        "freshness_buckets": [{"label": k, "count": v} for k, v in freshness_buckets.items()],
        "summary": {
            "total_requirements": len(chains),
            "compliant": sum(1 for c in chains if c.status == "COMPLIANT"),
            "conditional": sum(1 for c in chains if c.status == "CONDITIONAL"),
            "at_risk": sum(1 for c in chains if c.status == "AT_RISK"),
            "non_compliant": sum(1 for c in chains if c.status == "NON_COMPLIANT"),
            "total_evidence": anomaly_summary["total_evidence"],
            "total_anomalies": anomaly_summary["total_anomalies"],
            "anomaly_rate": anomaly_summary["anomaly_rate"],
            "avg_confidence": round(anomaly_summary["avg_confidence"] * 100),
            "approved_pct": anomaly_summary["approved_pct"],
        }
    }


def generate_html_dashboard(data: dict, output_path: str):
    data_json = json.dumps(data, indent=2)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Compliance Narrative Engine — Audit Dashboard</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

  :root {{
    --bg: #0a0d14;
    --surface: #111520;
    --surface2: #171d2e;
    --border: #1f2940;
    --accent: #3d9bff;
    --accent2: #7c5cfc;
    --green: #22d3a0;
    --yellow: #f5c842;
    --orange: #ff8c42;
    --red: #ff4d6d;
    --text: #c8d6f0;
    --text-muted: #5a6a8a;
    --text-dim: #8898bb;
    --mono: 'IBM Plex Mono', monospace;
    --sans: 'IBM Plex Sans', sans-serif;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: var(--sans); min-height: 100vh; }}

  /* Header */
  .header {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 20px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
  }}
  .header-left {{ display: flex; align-items: center; gap: 16px; }}
  .logo-icon {{
    width: 36px; height: 36px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
  }}
  .header h1 {{ font-size: 15px; font-weight: 600; letter-spacing: 0.02em; color: #e8f0ff; }}
  .header-sub {{ font-size: 11px; color: var(--text-muted); font-family: var(--mono); margin-top: 2px; }}
  .badge {{
    font-family: var(--mono);
    font-size: 10px;
    padding: 3px 8px;
    border-radius: 4px;
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text-muted);
  }}

  /* Layout */
  .main {{ padding: 28px 32px; max-width: 1400px; margin: 0 auto; }}

  /* KPI Row */
  .kpi-row {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 28px; }}
  .kpi {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
  }}
  .kpi::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent-color, var(--accent));
  }}
  .kpi.green {{ --accent-color: var(--green); }}
  .kpi.yellow {{ --accent-color: var(--yellow); }}
  .kpi.orange {{ --accent-color: var(--orange); }}
  .kpi.red {{ --accent-color: var(--red); }}
  .kpi-value {{ font-family: var(--mono); font-size: 32px; font-weight: 500; color: #e8f0ff; line-height: 1; }}
  .kpi-label {{ font-size: 11px; color: var(--text-muted); margin-top: 6px; text-transform: uppercase; letter-spacing: 0.08em; }}
  .kpi-sub {{ font-size: 10px; color: var(--text-muted); margin-top: 4px; font-family: var(--mono); }}

  /* Grid */
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
  .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 20px; }}

  /* Cards */
  .card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
  }}
  .card-title {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    margin-bottom: 16px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .card-title-dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
  }}

  /* Status badges */
  .status {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--mono);
    font-size: 10px;
    font-weight: 500;
    padding: 3px 8px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .status.COMPLIANT {{ background: rgba(34,211,160,0.12); color: var(--green); border: 1px solid rgba(34,211,160,0.25); }}
  .status.CONDITIONAL {{ background: rgba(245,200,66,0.12); color: var(--yellow); border: 1px solid rgba(245,200,66,0.25); }}
  .status.AT_RISK {{ background: rgba(255,140,66,0.12); color: var(--orange); border: 1px solid rgba(255,140,66,0.25); }}
  .status.NON_COMPLIANT {{ background: rgba(255,77,109,0.12); color: var(--red); border: 1px solid rgba(255,77,109,0.25); }}

  /* Framework bars */
  .fw-row {{ margin-bottom: 12px; }}
  .fw-name {{ font-family: var(--mono); font-size: 11px; color: var(--text-dim); margin-bottom: 5px; display: flex; justify-content: space-between; }}
  .fw-bar-bg {{ background: var(--surface2); border-radius: 3px; height: 6px; overflow: hidden; }}
  .fw-bar-fill {{ height: 100%; border-radius: 3px; transition: width 0.8s ease; }}

  /* Bar chart */
  .bar-chart {{ display: flex; align-items: flex-end; gap: 10px; height: 100px; }}
  .bar-col {{ flex: 1; display: flex; flex-direction: column; align-items: center; gap: 5px; }}
  .bar-fill {{ width: 100%; border-radius: 4px 4px 0 0; min-height: 4px; transition: height 0.5s ease; }}
  .bar-label {{ font-size: 9px; color: var(--text-muted); font-family: var(--mono); text-align: center; }}
  .bar-val {{ font-size: 10px; color: var(--text-dim); font-family: var(--mono); }}

  /* Requirements table */
  .req-table {{ width: 100%; margin-bottom: 24px; }}
  .req-row {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 8px;
    overflow: hidden;
    transition: border-color 0.2s;
  }}
  .req-row:hover {{ border-color: var(--accent); cursor: pointer; }}
  .req-header {{
    display: grid;
    grid-template-columns: 1fr auto auto;
    gap: 16px;
    align-items: center;
    padding: 14px 18px;
  }}
  .req-id {{ font-family: var(--mono); font-size: 10px; color: var(--text-muted); }}
  .req-text {{ font-size: 13px; color: #d0dff5; margin-top: 2px; }}
  .req-confidence {{
    font-family: var(--mono);
    font-size: 13px;
    font-weight: 500;
  }}

  /* Expanded detail */
  .req-detail {{
    display: none;
    border-top: 1px solid var(--border);
    padding: 18px;
    background: var(--surface2);
  }}
  .req-detail.open {{ display: block; }}
  .detail-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 16px; }}
  .detail-section-title {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    margin-bottom: 8px;
    font-weight: 500;
  }}
  .burden-item {{
    display: flex;
    align-items: flex-start;
    gap: 6px;
    font-size: 11px;
    color: var(--text-dim);
    margin-bottom: 5px;
    line-height: 1.4;
  }}
  .burden-icon {{ flex-shrink: 0; margin-top: 1px; }}

  .evidence-chip {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 6px;
    font-size: 11px;
  }}
  .evidence-chip-id {{ font-family: var(--mono); color: var(--accent); font-size: 10px; }}
  .evidence-chip-type {{ color: var(--text-dim); margin-top: 2px; }}
  .evidence-chip-meta {{ display: flex; gap: 12px; margin-top: 4px; }}
  .evidence-chip-badge {{
    font-family: var(--mono);
    font-size: 9px;
    padding: 1px 5px;
    border-radius: 3px;
    background: var(--surface2);
    color: var(--text-muted);
  }}

  .objection {{
    background: rgba(255,140,66,0.06);
    border: 1px solid rgba(255,140,66,0.15);
    border-left: 3px solid var(--orange);
    border-radius: 0 6px 6px 0;
    padding: 8px 12px;
    margin-bottom: 6px;
    font-size: 11px;
    color: var(--text-dim);
    line-height: 1.5;
  }}

  .narrative-box {{
    background: rgba(61,155,255,0.06);
    border: 1px solid rgba(61,155,255,0.15);
    border-radius: 8px;
    padding: 14px 16px;
    margin-top: 14px;
    font-size: 12px;
    color: var(--text-dim);
    line-height: 1.7;
    font-style: italic;
  }}
  .narrative-label {{
    font-style: normal;
    font-family: var(--mono);
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--accent);
    margin-bottom: 6px;
  }}

  /* Anomaly list */
  .anomaly-item {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
    font-size: 12px;
  }}
  .anomaly-item:last-child {{ border-bottom: none; }}
  .anomaly-count {{
    font-family: var(--mono);
    font-size: 14px;
    font-weight: 500;
    color: var(--orange);
  }}

  /* Confidence donut */
  .donut-wrap {{ display: flex; align-items: center; justify-content: center; gap: 24px; }}
  .donut-svg {{ flex-shrink: 0; }}
  .donut-legend {{ display: flex; flex-direction: column; gap: 8px; }}
  .legend-item {{ display: flex; align-items: center; gap: 8px; font-size: 12px; }}
  .legend-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}

  /* Filter tabs */
  .tabs {{ display: flex; gap: 6px; margin-bottom: 16px; }}
  .tab {{
    font-family: var(--mono);
    font-size: 10px;
    padding: 5px 12px;
    border-radius: 5px;
    border: 1px solid var(--border);
    background: var(--surface2);
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.15s;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .tab:hover, .tab.active {{
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
  }}

  /* Scrollbar */
  ::-webkit-scrollbar {{ width: 6px; }}
  ::-webkit-scrollbar-track {{ background: var(--surface); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}

  .section-title {{
    font-size: 12px;
    font-weight: 600;
    color: #e8f0ff;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .section-title::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }}

  .fw-tag {{
    display: inline-block;
    font-family: var(--mono);
    font-size: 9px;
    padding: 1px 5px;
    border-radius: 3px;
    background: rgba(124,92,252,0.15);
    color: var(--accent2);
    border: 1px solid rgba(124,92,252,0.25);
    margin-right: 3px;
  }}

  .undermining-chip {{
    background: rgba(255,77,109,0.06);
    border: 1px solid rgba(255,77,109,0.15);
    border-radius: 6px;
    padding: 7px 10px;
    margin-bottom: 5px;
    font-size: 11px;
    color: var(--text-dim);
  }}
  .undermining-chip .id {{ font-family: var(--mono); color: var(--red); font-size: 10px; }}

  .progress-ring {{ transform: rotate(-90deg); }}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <div class="logo-icon">🛡️</div>
    <div>
      <div class="header h1" style="font-size:15px;font-weight:600;color:#e8f0ff;">Compliance Narrative Engine</div>
      <div class="header-sub">Automated Evidence Collection & Audit — Problem 03</div>
    </div>
  </div>
  <div style="display:flex;gap:8px;align-items:center;">
    <span class="badge">v1.0</span>
    <span class="badge" id="genTime"></span>
  </div>
</div>

<div class="main">

  <!-- KPI Row -->
  <div class="kpi-row" id="kpiRow"></div>

  <!-- Charts Row -->
  <div class="grid-3" style="margin-bottom:20px;">
    <!-- Framework compliance -->
    <div class="card" style="grid-column: span 1;">
      <div class="card-title"><span class="card-title-dot"></span>Framework Compliance</div>
      <div id="fwChart"></div>
    </div>

    <!-- Anomaly breakdown -->
    <div class="card">
      <div class="card-title"><span class="card-title-dot" style="background:var(--orange)"></span>Evidence Anomaly Types</div>
      <div id="anomalyChart"></div>
    </div>

    <!-- Evidence freshness -->
    <div class="card">
      <div class="card-title"><span class="card-title-dot" style="background:var(--accent2)"></span>Evidence Age Distribution</div>
      <div id="freshnessChart"></div>
    </div>
  </div>

  <!-- Requirements Section -->
  <div class="section-title">Requirement Proof Chains</div>
  <div class="tabs" id="filterTabs">
    <div class="tab active" data-filter="ALL">All</div>
    <div class="tab" data-filter="COMPLIANT">✅ Compliant</div>
    <div class="tab" data-filter="CONDITIONAL">⚠️ Conditional</div>
    <div class="tab" data-filter="AT_RISK">🔶 At Risk</div>
    <div class="tab" data-filter="NON_COMPLIANT">❌ Non-Compliant</div>
  </div>
  <div id="reqTable"></div>

</div>

<script>
const DATA = {data_json};

// Helpers
function confidenceColor(pct) {{
  if (pct >= 75) return 'var(--green)';
  if (pct >= 55) return 'var(--yellow)';
  if (pct >= 35) return 'var(--orange)';
  return 'var(--red)';
}}

function statusDot(status) {{
  const map = {{
    'COMPLIANT': '✅', 'CONDITIONAL': '⚠️', 'AT_RISK': '🔶', 'NON_COMPLIANT': '❌'
  }};
  return map[status] || '❓';
}}

// Set generation time
document.getElementById('genTime').textContent = new Date().toLocaleString('en-US', {{hour12: false}});

// KPI Row
function renderKPIs() {{
  const s = DATA.summary;
  const cards = [
    {{ val: s.compliant, label: 'Compliant', sub: 'Requirements', cls: 'green' }},
    {{ val: s.conditional, label: 'Conditional Pass', sub: 'Need attention', cls: 'yellow' }},
    {{ val: s.at_risk, label: 'At Risk', sub: 'Urgent review', cls: 'orange' }},
    {{ val: s.total_anomalies, label: 'Evidence Anomalies', sub: s.anomaly_rate + '% of total', cls: 'red' }},
    {{ val: s.avg_confidence + '%', label: 'Avg Confidence', sub: s.approved_pct + '% approved', cls: '' }},
  ];
  document.getElementById('kpiRow').innerHTML = cards.map(c => `
    <div class="kpi ${{c.cls}}">
      <div class="kpi-value">${{c.val}}</div>
      <div class="kpi-label">${{c.label}}</div>
      <div class="kpi-sub">${{c.sub}}</div>
    </div>
  `).join('');
}}

// Framework bars
function renderFWChart() {{
  const html = DATA.framework_data.map(fw => {{
    const pct = fw.pct;
    const color = pct >= 70 ? 'var(--green)' : pct >= 40 ? 'var(--yellow)' : 'var(--red)';
    return `
      <div class="fw-row">
        <div class="fw-name">
          <span>${{fw.name}}</span>
          <span style="color:${{color}};font-weight:500;">${{pct}}% compliant</span>
        </div>
        <div class="fw-bar-bg">
          <div class="fw-bar-fill" style="width:${{pct}}%;background:${{color}};"></div>
        </div>
        <div style="display:flex;gap:8px;margin-top:4px;font-size:9px;color:var(--text-muted);font-family:var(--mono);">
          <span>✅ ${{fw.compliant}}</span>
          <span>⚠️ ${{fw.conditional}}</span>
          <span>🔶 ${{fw.at_risk}}</span>
          <span>❌ ${{fw.non_compliant}}</span>
        </div>
      </div>
    `;
  }}).join('');
  document.getElementById('fwChart').innerHTML = html;
}}

// Anomaly bar chart
function renderAnomalyChart() {{
  const items = DATA.anomaly_by_type;
  const max = Math.max(...items.map(i => i.count));
  const colors = ['var(--red)','var(--orange)','var(--yellow)','var(--accent)','var(--accent2)'];
  const bars = items.map((item, i) => {{
    const h = Math.round((item.count / max) * 90);
    return `
      <div class="bar-col">
        <div class="bar-val">${{item.count}}</div>
        <div class="bar-fill" style="height:${{h}}px;background:${{colors[i % colors.length]}};opacity:0.85;"></div>
        <div class="bar-label">${{item.label.replace('_',' ')}}</div>
      </div>
    `;
  }}).join('');
  document.getElementById('anomalyChart').innerHTML = `<div class="bar-chart" style="height:130px;align-items:flex-end;">${{bars}}</div>`;
}}

// Freshness histogram
function renderFreshnessChart() {{
  const items = DATA.freshness_buckets;
  const max = Math.max(...items.map(i => i.count));
  const getColor = (label) => {{
    if (label === '0-30d') return 'var(--green)';
    if (label === '31-60d') return 'var(--accent)';
    if (label === '61-90d') return 'var(--yellow)';
    if (label === '91-120d') return 'var(--orange)';
    return 'var(--red)';
  }};
  const bars = items.map(item => {{
    const h = Math.round((item.count / max) * 90);
    return `
      <div class="bar-col">
        <div class="bar-val">${{item.count}}</div>
        <div class="bar-fill" style="height:${{h}}px;background:${{getColor(item.label)}};opacity:0.85;"></div>
        <div class="bar-label">${{item.label}}</div>
      </div>
    `;
  }}).join('');
  document.getElementById('freshnessChart').innerHTML = `<div class="bar-chart" style="height:130px;align-items:flex-end;">${{bars}}</div>`;
}}

// Requirements table
let currentFilter = 'ALL';

function renderReqs() {{
  const findings = DATA.findings.filter(f =>
    currentFilter === 'ALL' || f.status === currentFilter
  );

  if (findings.length === 0) {{
    document.getElementById('reqTable').innerHTML = `
      <div style="text-align:center;padding:40px;color:var(--text-muted);font-family:var(--mono);font-size:12px;">
        No requirements match this filter.
      </div>`;
    return;
  }}

  const html = findings.map((f, idx) => {{
    const confColor = confidenceColor(f.confidence);

    const burdens = [
      ...f.burdens_ok.map(b => `<div class="burden-item"><span class="burden-icon">✅</span><span>${{b}}</span></div>`),
      ...f.burdens_gap.map(b => `<div class="burden-item"><span class="burden-icon">❌</span><span style="color:var(--red);">${{b}}</span></div>`),
    ].join('');

    const supportEv = f.supporting.map(e => `
      <div class="evidence-chip">
        <div class="evidence-chip-id">${{e.id}}</div>
        <div class="evidence-chip-type">${{e.type}}</div>
        <div class="evidence-chip-meta">
          <span class="evidence-chip-badge">${{e.confidence}}% conf</span>
          <span class="evidence-chip-badge">${{e.age_days}}d old</span>
          <span class="evidence-chip-badge" style="color:${{e.status === 'Approved' ? 'var(--green)' : 'var(--yellow)'}}">${{e.status}}</span>
        </div>
      </div>
    `).join('') || '<div style="color:var(--text-muted);font-size:11px;">No valid evidence found</div>';

    const undEv = f.undermining.map(e => `
      <div class="undermining-chip">
        <span class="id">${{e.id}}</span>
        <span style="margin-left:8px;font-size:10px;">${{e.anomaly.replace('_',' ')}}</span>
        <span style="margin-left:8px;color:var(--text-muted);font-size:10px;">${{e.status}}</span>
      </div>
    `).join('') || '<div style="color:var(--green);font-size:11px;">No undermining evidence ✓</div>';

    const objections = f.objections.map(o => `<div class="objection">😈 ${{o}}</div>`).join('') ||
      '<div style="color:var(--green);font-size:11px;">No objections raised ✓</div>';

    const fwTags = f.frameworks.map(fw => `<span class="fw-tag">${{fw}}</span>`).join('');

    return `
      <div class="req-row" onclick="toggleDetail('req-${{idx}}')">
        <div class="req-header">
          <div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
              <span class="req-id">${{f.req_id}}</span>
              ${{fwTags}}
            </div>
            <div class="req-text">${{f.req_text}}</div>
            <div style="font-size:10px;color:var(--text-muted);margin-top:3px;">${{f.policy}}</div>
          </div>
          <div class="status ${{f.status}}">${{statusDot(f.status)}} ${{f.status.replace('_',' ')}}</div>
          <div class="req-confidence" style="color:${{confColor}};min-width:40px;text-align:right;">${{f.confidence}}%</div>
        </div>
        <div class="req-detail" id="req-${{idx}}">
          <div class="detail-grid">
            <div>
              <div class="detail-section-title">📋 Burden of Proof</div>
              ${{burdens}}
            </div>
            <div>
              <div class="detail-section-title">✅ Supporting Evidence (${{f.supporting.length}})</div>
              ${{supportEv}}
              ${{f.undermining.length > 0 ? `<div class="detail-section-title" style="margin-top:10px;">⚠️ Undermining (${{f.undermining.length}})</div>${{undEv}}` : ''}}
            </div>
            <div>
              <div class="detail-section-title">😈 Devil's Advocate Objections</div>
              ${{objections}}
            </div>
          </div>
          <div class="narrative-box">
            <div class="narrative-label">📝 Audit Narrative</div>
            ${{f.narrative}}
          </div>
        </div>
      </div>
    `;
  }}).join('');

  document.getElementById('reqTable').innerHTML = html;
}}

function toggleDetail(id) {{
  const el = document.getElementById(id);
  if (el) el.classList.toggle('open');
}}

// Filter tabs
document.getElementById('filterTabs').addEventListener('click', (e) => {{
  const tab = e.target.closest('.tab');
  if (!tab) return;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  tab.classList.add('active');
  currentFilter = tab.dataset.filter;
  renderReqs();
}});

// Init
renderKPIs();
renderFWChart();
renderAnomalyChart();
renderFreshnessChart();
renderReqs();
</script>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  ✅ Dashboard: {output_path}")


if __name__ == "__main__":
    base = os.path.dirname(__file__)
    data_dir = os.path.join(base, 'data')
    reports_dir = os.path.join(base, 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    print("Building dashboard data...")
    policies = load_policies(os.path.join(data_dir, 'policy_documents.txt'))
    all_requirements = [req for policy in policies for req in policy.requirements]

    df = load_evidence(os.path.join(data_dir, 'evidence_artifacts.csv'))
    df = classify_anomalies(df, staleness_threshold=90)

    evidence_nodes = build_evidence_nodes(df)
    chains = build_proof_graph(all_requirements, evidence_nodes)
    anomaly_summary = get_anomaly_summary(df)
    framework_summary = get_framework_summary(chains)

    # Fix: use compliance_status field
    for c in chains:
        if not hasattr(c, 'status'):
            c.status = c.compliance_status

    data = build_dashboard_data(chains, df, anomaly_summary, framework_summary)
    generate_html_dashboard(data, os.path.join(reports_dir, 'dashboard.html'))
    print("Done.")
