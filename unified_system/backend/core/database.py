"""
Database Layer - SQLite with full schema for evidence, requirements, mappings, reports.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class ComplianceDatabase:
    def __init__(self, db_path: str = "data/compliance.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._conn()
        c = conn.cursor()

        c.execute("""CREATE TABLE IF NOT EXISTS evidence (
            evidence_id TEXT PRIMARY KEY,
            requirement_id TEXT,
            requirement_description TEXT,
            framework TEXT,
            evidence_type TEXT,
            collected_by TEXT,
            collector_email TEXT,
            collection_date TEXT,
            freshness_days INTEGER,
            evidence_summary TEXT,
            reviewed_by TEXT,
            reviewer_email TEXT,
            review_date TEXT,
            evidence_location TEXT,
            confidence_score REAL,
            status TEXT,
            anomaly_marker TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS requirements (
            requirement_id TEXT PRIMARY KEY,
            description TEXT,
            framework TEXT,
            policy_id TEXT,
            audit_frequency TEXT,
            responsible_team TEXT,
            scope TEXT,
            severity TEXT DEFAULT 'MEDIUM',
            control_area TEXT,
            burden_of_proof TEXT,
            evidence_types TEXT,
            freshness_requirement TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS policies (
            policy_id TEXT PRIMARY KEY,
            policy_name TEXT,
            version TEXT,
            status TEXT,
            last_updated TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS compliance_mappings (
            mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT,
            requirement_id TEXT,
            confidence REAL,
            mapped_by TEXT,
            mapped_date TEXT,
            similarity_score REAL
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS challenge_findings (
            finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
            requirement_id TEXT,
            finding_type TEXT,
            description TEXT,
            severity TEXT,
            remediation_suggestion TEXT,
            status TEXT DEFAULT 'OPEN',
            impact_on_confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS confidence_scores (
            score_id INTEGER PRIMARY KEY AUTOINCREMENT,
            requirement_id TEXT,
            compliance_status TEXT,
            confidence_score REAL,
            confidence_percentage TEXT,
            audit_ready INTEGER,
            recommendation TEXT,
            next_review_date TEXT,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS narratives (
            narrative_id INTEGER PRIMARY KEY AUTOINCREMENT,
            requirement_id TEXT,
            executive_summary TEXT,
            detailed_narrative TEXT,
            risk_assessment TEXT,
            recommendation TEXT,
            confidence_level TEXT,
            frameworks TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS reports (
            report_id TEXT PRIMARY KEY,
            report_type TEXT,
            framework TEXT,
            generated_at TEXT,
            generated_by TEXT,
            status TEXT,
            summary TEXT,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        c.execute("""CREATE TABLE IF NOT EXISTS copilot_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            query_type TEXT,
            answer TEXT,
            confidence REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        conn.commit()
        conn.close()

    # ---- Evidence ----
    def insert_evidence(self, d: Dict) -> bool:
        conn = self._conn()
        try:
            conn.execute("""INSERT OR REPLACE INTO evidence
                (evidence_id,requirement_id,requirement_description,framework,evidence_type,
                 collected_by,collector_email,collection_date,freshness_days,evidence_summary,
                 reviewed_by,reviewer_email,review_date,evidence_location,confidence_score,status,anomaly_marker)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (d.get('evidence_id'), d.get('requirement_id'), d.get('requirement_description'),
                 d.get('framework'), d.get('evidence_type'), d.get('collected_by'),
                 d.get('collector_email'), d.get('collection_date'), d.get('freshness_days'),
                 d.get('evidence_summary'), d.get('reviewed_by'), d.get('reviewer_email'),
                 d.get('review_date'), d.get('evidence_location'), d.get('confidence_score'),
                 d.get('status'), d.get('anomaly_marker')))
            conn.commit()
            return True
        except Exception as e:
            print(f"Evidence insert error: {e}")
            return False
        finally:
            conn.close()

    def get_all_evidence(self) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute("SELECT * FROM evidence").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_evidence_by_id(self, evidence_id: str) -> Optional[Dict]:
        conn = self._conn()
        row = conn.execute("SELECT * FROM evidence WHERE evidence_id=?", (evidence_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_evidence_by_framework(self, framework: str) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute("SELECT * FROM evidence WHERE framework=?", (framework,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ---- Requirements ----
    def insert_requirement(self, d: Dict) -> bool:
        conn = self._conn()
        try:
            conn.execute("""INSERT OR REPLACE INTO requirements
                (requirement_id,description,framework,policy_id,audit_frequency,responsible_team,
                 scope,severity,control_area,burden_of_proof,evidence_types,freshness_requirement)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (d.get('requirement_id'), d.get('description'), d.get('framework'),
                 d.get('policy_id'), d.get('audit_frequency'), d.get('responsible_team'),
                 d.get('scope'), d.get('severity', 'MEDIUM'), d.get('control_area', ''),
                 json.dumps(d.get('burden_of_proof', [])),
                 json.dumps(d.get('evidence_types_expected', [])),
                 d.get('freshness_requirement', 'monthly')))
            conn.commit()
            return True
        except Exception as e:
            print(f"Requirement insert error: {e}")
            return False
        finally:
            conn.close()

    def get_all_requirements(self) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute("SELECT * FROM requirements").fetchall()
        conn.close()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d['burden_of_proof'] = json.loads(d.get('burden_of_proof', '[]'))
            except Exception:
                d['burden_of_proof'] = []
            try:
                d['evidence_types'] = json.loads(d.get('evidence_types', '[]'))
            except Exception:
                d['evidence_types'] = []
            result.append(d)
        return result

    def get_requirement_by_id(self, req_id: str) -> Optional[Dict]:
        conn = self._conn()
        row = conn.execute("SELECT * FROM requirements WHERE requirement_id=?", (req_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    # ---- Mappings ----
    def insert_mapping(self, d: Dict) -> bool:
        conn = self._conn()
        try:
            conn.execute("""INSERT INTO compliance_mappings
                (evidence_id,requirement_id,confidence,mapped_by,mapped_date,similarity_score)
                VALUES (?,?,?,?,?,?)""",
                (d.get('evidence_id'), d.get('requirement_id'), d.get('confidence'),
                 d.get('mapped_by', 'SEMANTIC_MAPPER'), d.get('mapped_date', datetime.now().isoformat()),
                 d.get('similarity_score', 0.0)))
            conn.commit()
            return True
        except Exception as e:
            print(f"Mapping insert error: {e}")
            return False
        finally:
            conn.close()

    def get_all_mappings(self) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute("SELECT * FROM compliance_mappings").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ---- Challenge Findings ----
    def insert_challenge_finding(self, d: Dict) -> bool:
        conn = self._conn()
        try:
            conn.execute("""INSERT INTO challenge_findings
                (requirement_id,finding_type,description,severity,remediation_suggestion,status,impact_on_confidence)
                VALUES (?,?,?,?,?,?,?)""",
                (d.get('requirement_id'), d.get('finding_type'), d.get('description'),
                 d.get('severity'), d.get('remediation_suggestion'), d.get('status', 'OPEN'),
                 d.get('impact_on_confidence', 0.0)))
            conn.commit()
            return True
        except Exception as e:
            return False
        finally:
            conn.close()

    def get_all_challenge_findings(self, framework: str = None) -> List[Dict]:
        conn = self._conn()
        if framework:
            req_ids = [r['requirement_id'] for r in self.get_all_requirements()
                       if r.get('framework') == framework]
            placeholders = ','.join('?' for _ in req_ids)
            if req_ids:
                rows = conn.execute(
                    f"SELECT * FROM challenge_findings WHERE requirement_id IN ({placeholders}) ORDER BY severity",
                    req_ids
                ).fetchall()
            else:
                rows = []
        else:
            rows = conn.execute("SELECT * FROM challenge_findings ORDER BY severity").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ---- Confidence Scores ----
    def insert_confidence_score(self, d: Dict) -> bool:
        conn = self._conn()
        try:
            conn.execute("""INSERT INTO confidence_scores
                (requirement_id,compliance_status,confidence_score,confidence_percentage,
                 audit_ready,recommendation,next_review_date)
                VALUES (?,?,?,?,?,?,?)""",
                (d.get('requirement_id'), d.get('compliance_status'), d.get('confidence_score'),
                 d.get('confidence_percentage'), 1 if d.get('audit_ready') else 0,
                 d.get('recommendation'), d.get('next_review_date')))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    # ---- Narratives ----
    def insert_narrative(self, d: Dict) -> bool:
        conn = self._conn()
        try:
            conn.execute("""INSERT INTO narratives
                (requirement_id,executive_summary,detailed_narrative,risk_assessment,
                 recommendation,confidence_level,frameworks)
                VALUES (?,?,?,?,?,?,?)""",
                (d.get('requirement_id'), d.get('executive_summary'), d.get('detailed_narrative'),
                 d.get('risk_assessment'), d.get('recommendation'), d.get('confidence_level'),
                 json.dumps(d.get('frameworks_addressed', []))))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def get_narratives_for_requirement(self, req_id: str) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM narratives WHERE requirement_id=? ORDER BY generated_at DESC LIMIT 1",
            (req_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ---- Reports ----
    def insert_report(self, d: Dict) -> bool:
        conn = self._conn()
        try:
            conn.execute("""INSERT OR REPLACE INTO reports
                (report_id,report_type,framework,generated_at,generated_by,status,summary,data)
                VALUES (?,?,?,?,?,?,?,?)""",
                (d.get('report_id'), d.get('report_type'), d.get('framework'),
                 d.get('generated_at'), d.get('generated_by'), d.get('status'),
                 d.get('summary'), json.dumps(d.get('data', {}))))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def get_all_reports(self) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute("SELECT * FROM reports ORDER BY created_at DESC").fetchall()
        conn.close()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d['data'] = json.loads(d.get('data', '{}'))
            except Exception:
                d['data'] = {}
            result.append(d)
        return result

    def get_report_by_id(self, report_id: str) -> Optional[Dict]:
        conn = self._conn()
        row = conn.execute("SELECT * FROM reports WHERE report_id=?", (report_id,)).fetchone()
        conn.close()
        if row:
            d = dict(row)
            try:
                d['data'] = json.loads(d.get('data', '{}'))
            except Exception:
                d['data'] = {}
            return d
        return None

    # ---- Copilot History ----
    def insert_copilot_query(self, query: str, query_type: str, answer: str, confidence: float) -> bool:
        conn = self._conn()
        try:
            conn.execute("INSERT INTO copilot_history (query,query_type,answer,confidence) VALUES (?,?,?,?)",
                         (query, query_type, answer, confidence))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def get_copilot_history(self, limit: int = 20) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM copilot_history ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ---- Stats ----
    def get_dashboard_stats(self) -> Dict:
        conn = self._conn()
        total_evidence = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
        total_requirements = conn.execute("SELECT COUNT(*) FROM requirements").fetchone()[0]
        total_mappings = conn.execute("SELECT COUNT(*) FROM compliance_mappings").fetchone()[0]
        critical_findings = conn.execute(
            "SELECT COUNT(*) FROM challenge_findings WHERE severity='CRITICAL' AND status='OPEN'"
        ).fetchone()[0]
        frameworks = [r[0] for r in conn.execute(
            "SELECT DISTINCT framework FROM requirements WHERE framework IS NOT NULL"
        ).fetchall()]
        conn.close()

        coverage = (total_mappings / total_requirements * 100) if total_requirements > 0 else 0

        return {
            'totalEvidence': total_evidence,
            'totalRequirements': total_requirements,
            'totalMappings': total_mappings,
            'criticalFindings': critical_findings,
            'complianceScore': round(min(coverage, 100), 1),
            'frameworks': frameworks,
            'lastUpdated': datetime.now().isoformat(),
        }
