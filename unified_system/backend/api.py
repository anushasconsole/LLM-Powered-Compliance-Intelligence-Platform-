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
from core.anomaly_classifier import AnomalyClassifier
from core.evidence_integrations import EvidenceCollectorOrchestrator

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
anomaly_classifier = AnomalyClassifier()
evidence_orchestrator = EvidenceCollectorOrchestrator()


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

        # Evidence type distribution for pie chart
        all_evidence = db.get_all_evidence()
        type_map = {}
        type_colors = {
            'Configuration_Snapshot': '#8b5cf6',
            'Audit_Log':              '#ec4899',
            'Encryption_Cert':        '#10b981',
            'Test_Result':            '#f59e0b',
            'Report':                 '#3b82f6',
            'Access_Report':          '#06b6d4',
            'Training_Record':        '#84cc16',
            'Screenshot':             '#f43f5e',
            'Procedure_Evidence':     '#a78bfa',
        }
        for ev in all_evidence:
            t = ev.get('evidence_type') or 'Other'
            type_map[t] = type_map.get(t, 0) + 1
        stats['evidenceByType'] = [
            {'name': t, 'value': c, 'color': type_colors.get(t, '#64748b')}
            for t, c in sorted(type_map.items(), key=lambda x: -x[1])
        ]

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
#  ANOMALY DETECTION
# ===================================================================== #

@app.route('/api/anomaly/detect', methods=['POST'])
def detect_anomalies():
    """
    Run anomaly detection on all evidence or a posted subset.
    POST body (optional): { "threshold": 0.45, "framework": "GDPR" }
    Returns per-record predictions and aggregate metrics.
    """
    try:
        data = request.json or {}
        threshold = float(data.get('threshold', 0.20))
        fw_filter = data.get('framework')

        evidence = db.get_all_evidence()
        if fw_filter and fw_filter != 'ALL':
            evidence = [e for e in evidence if e.get('framework') == fw_filter]

        if not evidence:
            return ok({"anomalies": [], "total": 0, "anomaly_count": 0, "anomaly_rate": 0})

        predictions = anomaly_classifier.predict_batch(evidence, threshold=threshold)

        # predictions may be a DataFrame or a list of dicts
        try:
            records = predictions.to_dict('records')
        except AttributeError:
            records = predictions  # already a list of dicts

        anomalies = [r for r in records if r.get('predicted_anomaly')]
        anomaly_rate = len(anomalies) / len(records) if records else 0

        # Aggregate by type
        type_counts: dict = {}
        for r in anomalies:
            t = r.get('anomaly_type', 'unknown')
            type_counts[t] = type_counts.get(t, 0) + 1

        return ok({
            "total": len(records),
            "anomaly_count": len(anomalies),
            "normal_count": len(records) - len(anomalies),
            "anomaly_rate": round(anomaly_rate * 100, 1),
            "threshold_used": threshold,
            "framework_filter": fw_filter or "ALL",
            "anomaly_type_breakdown": type_counts,
            "anomalies": anomalies,
            "all_predictions": records,
            "detected_at": datetime.now().isoformat(),
        })
    except Exception as e:
        return err(e)


@app.route('/api/anomaly/evaluate', methods=['POST'])
def evaluate_anomaly_classifier():
    """
    Evaluate the classifier against a ground-truth labels CSV.
    POST body: { "labels_csv": "<csv content string>" }
    Returns precision, recall, F1, accuracy.
    """
    try:
        import csv
        import io
        data = request.json or {}
        labels_csv = data.get('labels_csv', '')
        if not labels_csv:
            # Try to load the bundled labels file if it exists
            base = Path(__file__).parent
            labels_path = base / 'data' / 'evidence_labels.csv'
            if labels_path.exists():
                labels_csv = labels_path.read_text(encoding='utf-8')
            else:
                return err("labels_csv required (or place evidence_labels.csv in data/)")

        reader = csv.DictReader(io.StringIO(labels_csv))
        ground_truth = [dict(row) for row in reader]

        # Run predictions on all evidence
        evidence = db.get_all_evidence()
        if not evidence:
            return err("No evidence loaded. Initialize the system first.")

        predictions = anomaly_classifier.predict_batch(evidence)
        try:
            pred_records = predictions.to_dict('records')
        except AttributeError:
            pred_records = predictions

        metrics = anomaly_classifier.evaluate(pred_records, ground_truth)

        if 'error' in metrics:
            return err(metrics['error'])

        return ok({
            **metrics,
            "rubric_targets": {
                "precision_target": "70%",
                "recall_target": "60%",
                "precision_met": metrics.get('precision', 0) >= 0.70,
                "recall_met": metrics.get('recall', 0) >= 0.60,
            },
            "evaluated_at": datetime.now().isoformat(),
        })
    except Exception as e:
        return err(e)


@app.route('/api/anomaly/summary', methods=['GET'])
def anomaly_summary():
    """
    Quick anomaly summary for dashboard — no ground truth needed.
    Returns counts by type and a risk signal.
    """
    try:
        threshold = float(request.args.get('threshold', 0.20))
        evidence = db.get_all_evidence()
        if not evidence:
            return ok({"anomaly_count": 0, "total": 0, "anomaly_rate": 0, "risk": "UNKNOWN"})

        predictions = anomaly_classifier.predict_batch(evidence, threshold=threshold)
        try:
            records = predictions.to_dict('records')
        except AttributeError:
            records = predictions

        anomalies = [r for r in records if r.get('predicted_anomaly')]
        rate = len(anomalies) / len(records) if records else 0

        type_counts: dict = {}
        for r in anomalies:
            t = r.get('anomaly_type', 'unknown')
            type_counts[t] = type_counts.get(t, 0) + 1

        risk = "HIGH" if rate > 0.40 else "MEDIUM" if rate > 0.20 else "LOW"

        return ok({
            "total": len(records),
            "anomaly_count": len(anomalies),
            "anomaly_rate": round(rate * 100, 1),
            "risk_signal": risk,
            "anomaly_type_breakdown": type_counts,
            "sampled_anomalies": anomalies[:10],
        })
    except Exception as e:
        return err(e)


# ===================================================================== #
#  PDF REPORT DOWNLOAD
# ===================================================================== #

@app.route('/api/reports/<report_id>/pdf', methods=['GET'])
def download_report_pdf(report_id):
    """Generate and stream an HTML/PDF compliance report for the given report_id."""
    try:
        from flask import Response
        from core.pdf_report_generator import PDFReportGenerator

        report = db.get_report_by_id(report_id)
        if not report:
            return err("Report not found", 404)

        data_inner = report.get('data', {})
        analysis = data_inner.get('compliance_analysis', {})
        challenge = data_inner.get('challenge_audit', {})

        # Build payload for the PDF generator
        fw_scores = []
        for fw_entry in analysis.get('gaps', []):
            pass  # gaps not framework scores; use platform cache
        for fw_entry in (data_inner.get('compliance_analysis', {}).get('framework_scores') or []):
            fw_scores.append(fw_entry)

        findings = [
            {
                'finding_type': f.get('type', ''),
                'severity': f.get('severity', 'MEDIUM'),
                'requirement_id': r.get('requirement_id', ''),
                'description': f.get('description', ''),
                'remediation': f.get('remediation', ''),
            }
            for r in challenge.get('detailed_results', [])
            for f in r.get('findings', [])
        ]

        pdf_data = {
            'generated_at': report.get('generated_at', datetime.now().isoformat()),
            'overall_compliance': analysis.get('compliance_score', 0) / 100,
            'total_evidence': db.get_dashboard_stats().get('totalEvidence', 0),
            'frameworks_covered': len(set(
                r.get('framework', '') for r in (db.get_all_requirements() or [])
                if r.get('framework') not in ('META', '', None)
            )),
            'critical_findings': challenge.get('critical_findings', 0),
            'status': report.get('status', 'UNKNOWN'),
            'framework_scores': fw_scores,
            'findings': findings[:20],
        }

        generator = PDFReportGenerator()
        html_content = generator.generate_html_report(pdf_data)
        return Response(html_content, mimetype='text/html',
                        headers={'Content-Disposition': f'inline; filename="report-{report_id}.html"'})
    except Exception as e:
        return err(e)


# ===================================================================== #
#  EVIDENCE INTEGRATIONS
# ===================================================================== #

@app.route('/api/integrations', methods=['GET'])
def list_integrations():
    """List all available evidence integrations and their status."""
    return ok({
        "integrations": [
            {
                "id": "cloudtrail",
                "name": "AWS CloudTrail",
                "description": "Collects AWS API audit events (CreateKey, RotateKey, PutBucketEncryption...)",
                "type": "automated",
                "frameworks": ["GDPR", "NIST", "PCI-DSS", "SOX"],
                "status": "available",
                "real_tool": "boto3 → cloudtrail.lookup_events()"
            },
            {
                "id": "aws_config",
                "name": "AWS Config",
                "description": "Checks AWS Config rule compliance (encrypted-volumes, rds-encryption, mfa-enabled...)",
                "type": "automated",
                "frameworks": ["NIST", "SOX", "ISO27001", "HIPAA"],
                "status": "available",
                "real_tool": "boto3 → config.get_compliance_details_by_config_rule()"
            },
            {
                "id": "splunk",
                "name": "Splunk SIEM",
                "description": "Pulls security log events from Splunk (firewall, auth, database audit, network)",
                "type": "automated",
                "frameworks": ["SOX", "HIPAA", "GDPR", "PCI-DSS"],
                "status": "available",
                "real_tool": "Splunk SDK → client.jobs.create(search_query)"
            },
            {
                "id": "vendor_certs",
                "name": "Vendor Certifications",
                "description": "Collects 3rd-party vendor certs (AWS SOC2, Azure ISO27001, Okta SOC2, Snowflake HIPAA...)",
                "type": "automated",
                "frameworks": ["SOX", "ISO27001", "HIPAA"],
                "status": "available",
                "real_tool": "Vendor certification portal API"
            },
        ]
    })


@app.route('/api/integrations/collect', methods=['POST'])
def collect_from_integrations():
    """
    Trigger evidence collection from all (or selected) integrations.
    POST body (optional): { "sources": ["cloudtrail", "aws_config", "splunk", "vendor_certs"] }
    Collected evidence is stored in the DB and available immediately.
    """
    try:
        data = request.json or {}
        requested = set(data.get('sources', ['cloudtrail', 'aws_config', 'splunk', 'vendor_certs']))

        from core.evidence_integrations import (
            CloudTrailIntegration, AWSConfigIntegration,
            SplunkIntegration, VendorCertificationIntegration,
        )

        collected_by_source = {}
        total_collected = 0

        if 'cloudtrail' in requested:
            records = CloudTrailIntegration().collect_evidence(days=7)
            for r in records:
                db.insert_evidence(r)
            collected_by_source['cloudtrail'] = len(records)
            total_collected += len(records)

        if 'aws_config' in requested:
            records = AWSConfigIntegration().collect_evidence()
            for r in records:
                db.insert_evidence(r)
            collected_by_source['aws_config'] = len(records)
            total_collected += len(records)

        if 'splunk' in requested:
            records = SplunkIntegration().collect_evidence(days=7)
            for r in records:
                db.insert_evidence(r)
            collected_by_source['splunk'] = len(records)
            total_collected += len(records)

        if 'vendor_certs' in requested:
            records = VendorCertificationIntegration().collect_evidence()
            for r in records:
                db.insert_evidence(r)
            collected_by_source['vendor_certs'] = len(records)
            total_collected += len(records)

        # Rebuild semantic mappings so new evidence is linked to requirements
        platform.reload_caches()

        return ok({
            "message": f"Collected {total_collected} evidence records from {len(collected_by_source)} sources",
            "total_collected": total_collected,
            "by_source": collected_by_source,
            "sources_triggered": list(requested),
            "collected_at": datetime.now().isoformat(),
        })
    except Exception as e:
        return err(e)


@app.route('/api/integrations/collect/<source_id>', methods=['POST'])
def collect_from_single_integration(source_id):
    """Trigger collection from a single integration source."""
    try:
        from core.evidence_integrations import (
            CloudTrailIntegration, AWSConfigIntegration,
            SplunkIntegration, VendorCertificationIntegration,
        )
        source_map = {
            'cloudtrail':   lambda: CloudTrailIntegration().collect_evidence(days=7),
            'aws_config':   lambda: AWSConfigIntegration().collect_evidence(),
            'splunk':       lambda: SplunkIntegration().collect_evidence(days=7),
            'vendor_certs': lambda: VendorCertificationIntegration().collect_evidence(),
        }
        if source_id not in source_map:
            return err(f"Unknown source '{source_id}'. Valid: {list(source_map.keys())}", 404)

        records = source_map[source_id]()
        for r in records:
            db.insert_evidence(r)
        platform.reload_caches()

        return ok({
            "source": source_id,
            "collected": len(records),
            "sample": records[:3],
            "collected_at": datetime.now().isoformat(),
        })
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
