"""
Unified Compliance Intelligence Platform - Flask REST API
Full pipeline backend serving the React frontend.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, jsonify, request
from flask_cors import CORS

from core.system_orchestrator import UnifiedCompliancePlatform
from core.database import ComplianceDatabase

# ---- App setup ----
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

DB_PATH = os.getenv("DB_PATH", "data/compliance.db")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
USE_MOCK = OPENAI_KEY is None

platform = UnifiedCompliancePlatform(
    db_path=DB_PATH,
    use_mock=USE_MOCK,
    openai_api_key=OPENAI_KEY
)
db = ComplianceDatabase(db_path=DB_PATH)


def ok(data, status=200):
    return jsonify({"status": "success", "data": data}), status


def err(msg, status=400):
    return jsonify({"status": "error", "message": str(msg)}), status


# ===================================================================== #
#  HEALTH & STATUS
# ===================================================================== #

@app.route('/api/health', methods=['GET'])
def health():
    return ok({"healthy": True, "timestamp": datetime.now().isoformat(), "version": "2.0.0"})


@app.route('/api/status', methods=['GET'])
def system_status():
    try:
        return ok(platform.get_system_status())
    except Exception as e:
        return err(e)


# ===================================================================== #
#  INITIALIZATION
# ===================================================================== #

@app.route('/api/initialize', methods=['POST'])
def initialize():
    try:
        data = request.json or {}
        policy_file = data.get('policy_file')
        evidence_file = data.get('evidence_file')

        # Default to bundled data files
        if not policy_file:
            base = Path(__file__).parent
            policy_file = str(base / 'data' / 'policy_documents.txt')
        if not evidence_file:
            base = Path(__file__).parent
            evidence_file = str(base / 'data' / 'evidence_artifacts.csv')

        result = platform.initialize_from_files(
            policy_file_path=policy_file if Path(policy_file).exists() else None,
            evidence_csv_path=evidence_file if Path(evidence_file).exists() else None,
        )
        platform.reload_caches()
        return ok(result)
    except Exception as e:
        return err(e)


@app.route('/api/initialize/text', methods=['POST'])
def initialize_from_text():
    """Initialize system from directly posted policy text and evidence CSV."""
    try:
        data = request.json or {}
        policy_text = data.get('policy_text')
        evidence_csv = data.get('evidence_csv')

        result = platform.initialize_from_files(
            policy_text=policy_text,
            evidence_csv_content=evidence_csv,
        )
        platform.reload_caches()
        return ok(result)
    except Exception as e:
        return err(e)


# ===================================================================== #
#  DASHBOARD
# ===================================================================== #

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    try:
        stats = db.get_dashboard_stats()
        # Framework scores
        frameworks_data = []
        for fw in stats.get('frameworks', []):
            cov = platform.knowledge_graph.get_framework_coverage(f"FW-{fw}")
            frameworks_data.append({
                "name": fw,
                "score": round(cov.get('coverage_percent', 0), 1),
                "total_requirements": cov.get('total_requirements', 0),
                "covered_requirements": cov.get('requirements_with_evidence', 0),
            })
        stats['framework_scores'] = frameworks_data
        return ok(stats)
    except Exception as e:
        return err(e)


# ===================================================================== #
#  FRAMEWORKS
# ===================================================================== #

@app.route('/api/frameworks', methods=['GET'])
def frameworks():
    try:
        all_reqs = db.get_all_requirements()
        fw_map = {}
        for req in all_reqs:
            fw = req.get('framework', 'UNKNOWN')
            if fw == 'META':
                continue
            if fw not in fw_map:
                fw_map[fw] = {'name': fw, 'total': 0, 'covered': 0}
            fw_map[fw]['total'] += 1

        mappings = db.get_all_mappings()
        mapped_ids = set(m['requirement_id'] for m in mappings)
        for req in all_reqs:
            fw = req.get('framework', 'UNKNOWN')
            if fw == 'META':
                continue
            if req['requirement_id'] in mapped_ids and fw in fw_map:
                fw_map[fw]['covered'] += 1

        result = []
        for fw_name, d in fw_map.items():
            total = d['total']
            covered = d['covered']
            score = round(covered / total * 100, 1) if total > 0 else 0
            result.append({
                "name": fw_name,
                "score": score,
                "total_requirements": total,
                "covered_requirements": covered,
                "status": "excellent" if score >= 85 else "good" if score >= 70 else "acceptable",
            })
        return ok(result)
    except Exception as e:
        return err(e)


# ===================================================================== #
#  COMPLIANCE ANALYSIS
# ===================================================================== #

@app.route('/api/analysis/<framework>', methods=['GET'])
def run_analysis(framework):
    try:
        result = platform.run_compliance_analysis(framework=framework)
        return ok(result)
    except Exception as e:
        return err(e)


# ===================================================================== #
#  CHALLENGE AUDIT
# ===================================================================== #

@app.route('/api/challenge-audit/<framework>', methods=['POST'])
def run_challenge_audit(framework):
    try:
        result = platform.run_challenge_audit(framework=framework)
        return ok(result)
    except Exception as e:
        return err(e)


@app.route('/api/challenge-findings', methods=['GET'])
def challenge_findings():
    try:
        fw = request.args.get('framework')
        findings = db.get_all_challenge_findings(framework=fw if fw and fw != 'ALL' else None)
        return ok(findings)
    except Exception as e:
        return err(e)


# ===================================================================== #
#  CONFIDENCE + NARRATIVES
# ===================================================================== #

@app.route('/api/confidence/<framework>', methods=['GET'])
def get_confidence(framework):
    try:
        result = platform.run_confidence_and_narratives(framework=framework)
        return ok(result)
    except Exception as e:
        return err(e)


@app.route('/api/narrative/<requirement_id>', methods=['GET'])
def get_narrative(requirement_id):
    try:
        narratives = db.get_narratives_for_requirement(requirement_id)
        return ok(narratives[0] if narratives else {})
    except Exception as e:
        return err(e)


# ===================================================================== #
#  EVIDENCE
# ===================================================================== #

@app.route('/api/evidence', methods=['GET'])
def get_evidence():
    try:
        evidence = db.get_all_evidence()
        fw = request.args.get('framework')
        search = request.args.get('search', '').lower()
        status_filter = request.args.get('status')

        if fw and fw != 'ALL':
            evidence = [e for e in evidence if e.get('framework') == fw]
        if search:
            evidence = [e for e in evidence
                        if search in e.get('evidence_id', '').lower()
                        or search in e.get('evidence_summary', '').lower()
                        or search in e.get('evidence_type', '').lower()]
        if status_filter and status_filter != 'ALL':
            evidence = [e for e in evidence if e.get('status') == status_filter]

        return ok({"items": evidence, "total": len(evidence)})
    except Exception as e:
        return err(e)


@app.route('/api/evidence/<evidence_id>', methods=['GET'])
def get_evidence_by_id(evidence_id):
    try:
        ev = db.get_evidence_by_id(evidence_id)
        if not ev:
            return err("Evidence not found", 404)
        mappings = [m for m in db.get_all_mappings() if m.get('evidence_id') == evidence_id]
        return ok({"evidence": ev, "mappings": mappings})
    except Exception as e:
        return err(e)


@app.route('/api/evidence', methods=['POST'])
def upload_evidence():
    try:
        data = request.json
        if not data:
            return err("No data provided")
        if not data.get('evidence_id'):
            data['evidence_id'] = f"EVD-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        db.insert_evidence(data)
        platform.reload_caches()
        return ok({"message": "Evidence uploaded", "evidence_id": data['evidence_id']}, 201)
    except Exception as e:
        return err(e)


# ===================================================================== #
#  REQUIREMENTS
# ===================================================================== #

@app.route('/api/requirements', methods=['GET'])
def get_requirements():
    try:
        reqs = db.get_all_requirements()
        fw = request.args.get('framework')
        if fw and fw != 'ALL':
            reqs = [r for r in reqs if r.get('framework') == fw]
        reqs = [r for r in reqs if r.get('framework') != 'META']
        return ok({"items": reqs, "total": len(reqs)})
    except Exception as e:
        return err(e)


@app.route('/api/requirements/<req_id>', methods=['GET'])
def get_requirement(req_id):
    try:
        req = db.get_requirement_by_id(req_id)
        if not req:
            return err("Requirement not found", 404)
        mappings = [m for m in db.get_all_mappings() if m.get('requirement_id') == req_id]
        evidence_ids = [m['evidence_id'] for m in mappings]
        evidence = [db.get_evidence_by_id(eid) for eid in evidence_ids]
        evidence = [e for e in evidence if e]
        return ok({"requirement": req, "mappings": mappings, "evidence": evidence})
    except Exception as e:
        return err(e)


# ===================================================================== #
#  REPORTS
# ===================================================================== #

@app.route('/api/reports', methods=['GET'])
def get_reports():
    try:
        reports = db.get_all_reports()
        return ok({"items": reports, "total": len(reports)})
    except Exception as e:
        return err(e)


@app.route('/api/reports/generate', methods=['POST'])
def generate_report():
    try:
        data = request.json or {}
        framework = data.get('framework', 'ALL')
        result = platform.generate_report(framework=framework)
        return ok(result, 201)
    except Exception as e:
        return err(e)


@app.route('/api/reports/<report_id>', methods=['GET'])
def get_report(report_id):
    try:
        report = db.get_report_by_id(report_id)
        if not report:
            return err("Report not found", 404)
        return ok(report)
    except Exception as e:
        return err(e)


# ===================================================================== #
#  KNOWLEDGE GRAPH
# ===================================================================== #

@app.route('/api/knowledge-graph', methods=['GET'])
def knowledge_graph():
    try:
        graph_data = platform.knowledge_graph.export_for_visualization()
        return ok(graph_data)
    except Exception as e:
        return err(e)


# ===================================================================== #
#  COMPLIANCE COPILOT
# ===================================================================== #

@app.route('/api/copilot', methods=['POST'])
def copilot_query():
    try:
        data = request.json or {}
        question = data.get('query', '').strip()
        if not question:
            return err("Query is required")
        result = platform.query_copilot(question)
        return ok(result)
    except Exception as e:
        return err(e)


@app.route('/api/copilot/history', methods=['GET'])
def copilot_history():
    try:
        history = db.get_copilot_history(limit=20)
        return ok(history)
    except Exception as e:
        return err(e)


# ===================================================================== #
#  MAPPINGS
# ===================================================================== #

@app.route('/api/mappings', methods=['GET'])
def get_mappings():
    try:
        mappings = db.get_all_mappings()
        return ok({"items": mappings, "total": len(mappings)})
    except Exception as e:
        return err(e)


@app.route('/api/mappings/rebuild', methods=['POST'])
def rebuild_mappings():
    try:
        platform.reload_caches()
        return ok({"message": "Mappings rebuilt successfully"})
    except Exception as e:
        return err(e)


# ===================================================================== #
#  ERROR HANDLERS
# ===================================================================== #

@app.errorhandler(404)
def not_found(e):
    return err("Endpoint not found", 404)

@app.errorhandler(500)
def server_error(e):
    return err("Internal server error", 500)


# ===================================================================== #
#  MAIN
# ===================================================================== #

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 UNIFIED COMPLIANCE INTELLIGENCE PLATFORM - REST API v2.0")
    print("=" * 70)
    print(f"  Mode: {'MOCK (no API key)' if USE_MOCK else 'LIVE (OpenAI)'}")
    print(f"  DB:   {DB_PATH}")
    print(f"  URL:  http://localhost:5000")
    print("=" * 70)
    print("\nAuto-initializing with default data...")
    base = Path(__file__).parent
    policy_path = base / 'data' / 'policy_documents.txt'
    evidence_path = base / 'data' / 'evidence_artifacts.csv'
    if policy_path.exists() and evidence_path.exists():
        result = platform.initialize_from_files(
            policy_file_path=str(policy_path),
            evidence_csv_path=str(evidence_path),
        )
        platform.reload_caches()
        print(f"  ✓ {result.get('requirements_extracted', 0)} requirements extracted")
        print(f"  ✓ {result.get('evidence_loaded', 0)} evidence records loaded")
        print(f"  ✓ {result.get('mappings_created', 0)} mappings created")
    print("=" * 70)
    app.run(debug=True, host='0.0.0.0', port=5000)
