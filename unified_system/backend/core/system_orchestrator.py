"""
Unified Compliance Intelligence Platform - System Orchestrator
Full pipeline: Policy Upload → LLM Extractor → Semantic Mapper → Knowledge Graph
              → Challenge Auditor → Confidence Engine → Narrative Generator → Report
"""

import csv
import io
import json
from datetime import datetime
from typing import List, Dict, Optional

from .llm_requirement_extractor import LLMRequirementExtractor, PolicyDocument
from .semantic_mapper import SemanticEvidenceMapper
from .knowledge_graph import KnowledgeGraph
from .challenge_auditor import ChallengeAuditor
from .confidence_engine import AuditorConfidenceEngine
from .narrative_generator import EnhancedNarrativeGenerator
from .compliance_copilot import ComplianceCopilot
from .database import ComplianceDatabase


FRAMEWORKS = ["GDPR", "NIST", "SOX", "PCI-DSS", "ISO27001", "HIPAA", "CIS"]


class UnifiedCompliancePlatform:
    def __init__(self, db_path: str = "data/compliance.db", use_mock: bool = True,
                 openai_api_key: Optional[str] = None):
        self.db = ComplianceDatabase(db_path)
        self.use_mock = use_mock

        self.llm_extractor = LLMRequirementExtractor(
            api_key=openai_api_key, use_mock=use_mock
        )
        self.semantic_mapper = SemanticEvidenceMapper(use_mock=use_mock)
        self.knowledge_graph = KnowledgeGraph()
        self.challenge_auditor = ChallengeAuditor()
        self.confidence_engine = AuditorConfidenceEngine()
        self.narrative_generator = EnhancedNarrativeGenerator(
            api_key=openai_api_key, use_mock=use_mock
        )
        self.compliance_copilot = ComplianceCopilot(
            self.knowledge_graph, self.semantic_mapper, self.confidence_engine, database=self.db
        )

        self._requirements_cache: List[Dict] = []
        self._evidence_cache: List[Dict] = []

    # ------------------------------------------------------------------ #
    #  INITIALIZATION                                                       #
    # ------------------------------------------------------------------ #

    def initialize_from_files(
        self,
        policy_text: Optional[str] = None,
        policy_file_path: Optional[str] = None,
        evidence_csv_path: Optional[str] = None,
        evidence_csv_content: Optional[str] = None,
    ) -> Dict:
        summary = {
            "policies_loaded": 0,
            "requirements_extracted": 0,
            "evidence_loaded": 0,
            "mappings_created": 0,
            "status": "SUCCESS"
        }

        try:
            # 1. Load policy text
            if policy_file_path:
                with open(policy_file_path, 'r', encoding='utf-8') as f:
                    policy_text = f.read()

            if policy_text:
                reqs = self._process_policy_text(policy_text)
                summary["requirements_extracted"] = len(reqs)
                summary["policies_loaded"] = 1

            # 2. Load evidence
            if evidence_csv_path:
                with open(evidence_csv_path, 'r', encoding='utf-8') as f:
                    evidence_csv_content = f.read()

            if evidence_csv_content:
                evidence = self._parse_evidence_csv(evidence_csv_content)
                for ev in evidence:
                    self.db.insert_evidence(ev)
                self._evidence_cache = evidence
                summary["evidence_loaded"] = len(evidence)

            # 3. Build knowledge graph and map
            self._rebuild_knowledge_graph()
            mappings = self._run_semantic_mapping()
            summary["mappings_created"] = len(mappings)

        except Exception as e:
            summary["status"] = "PARTIAL_FAILURE"
            summary["error"] = str(e)
            print(f"Initialization error: {e}")

        return summary

    def _process_policy_text(self, text: str) -> List[Dict]:
        """Extract requirements from policy text using LLM extractor."""
        # Split into blocks by POLICY: header
        blocks = [b.strip() for b in text.split('---') if b.strip()]
        if len(blocks) <= 1:
            blocks = [text]

        all_reqs = []
        for i, block in enumerate(blocks):
            # Derive a policy id from the block
            import re
            pid_match = re.search(r'POLICY_ID\s*:\s*(\S+)', block, re.IGNORECASE)
            pname_match = re.search(r'POLICY\s*:\s*(.+?)(?=\n|POLICY_ID)', block, re.IGNORECASE)
            policy_id = pid_match.group(1).strip() if pid_match else f"POL-{i+1:03d}"
            policy_name = pname_match.group(1).strip() if pname_match else f"Policy {i+1}"

            doc = self.llm_extractor.extract_from_text(block, policy_id, policy_name)
            self.db.insert_requirement({
                'requirement_id': f"_POLICY_{policy_id}",
                'description': policy_name,
                'framework': 'META',
                'policy_id': policy_id,
            })

            for req in doc.extracted_requirements:
                req_dict = {
                    'requirement_id': req.req_id,
                    'description': req.requirement_text,
                    'framework': req.frameworks[0] if req.frameworks else 'General',
                    'policy_id': req.policy_id,
                    'audit_frequency': req.freshness_requirement,
                    'responsible_team': req.responsible_team,
                    'scope': req.structured_requirement,
                    'severity': req.severity,
                    'control_area': req.control_area,
                    'burden_of_proof': req.burden_of_proof,
                    'evidence_types_expected': req.evidence_types_expected,
                    'freshness_requirement': req.freshness_requirement,
                }
                self.db.insert_requirement(req_dict)
                all_reqs.append(req_dict)

        self._requirements_cache = self.db.get_all_requirements()
        return all_reqs

    def _parse_evidence_csv(self, csv_content: str) -> List[Dict]:
        """Parse evidence CSV into list of dicts."""
        reader = csv.DictReader(io.StringIO(csv_content))
        evidence = []
        for row in reader:
            evidence.append(dict(row))
        return evidence

    def _rebuild_knowledge_graph(self):
        """Rebuild knowledge graph from database."""
        kg = self.knowledge_graph
        requirements = self.db.get_all_requirements()
        evidence_list = self.db.get_all_evidence()

        # Add frameworks
        for fw in FRAMEWORKS:
            kg.add_framework(f"FW-{fw}", fw)

        # Add requirements
        for req in requirements:
            if req.get('framework') == 'META':
                continue
            kg.add_requirement(
                req['requirement_id'],
                req.get('description', ''),
                req.get('policy_id', 'UNKNOWN'),
                control_area=req.get('control_area', ''),
                responsible_team=req.get('responsible_team', ''),
                severity=req.get('severity', 'MEDIUM'),
                freshness=req.get('freshness_requirement', 'monthly'),
                burden_of_proof=req.get('burden_of_proof', []),
            )
            fw = req.get('framework', 'General')
            fw_id = f"FW-{fw}"
            if fw_id not in kg._nodes:
                kg.add_framework(fw_id, fw)
            kg.link_requirement_to_framework(req['requirement_id'], fw_id)

        # Add evidence
        for ev in evidence_list:
            raw_fresh = ev.get('freshness_days', 30)
            raw_conf  = ev.get('confidence_score', 0.5)
            try:
                freshness = int(float(raw_fresh)) if raw_fresh not in (None, '', 'None') else 30
            except (ValueError, TypeError):
                freshness = 30
            try:
                confidence = float(raw_conf) if raw_conf not in (None, '', 'None') else 0.5
            except (ValueError, TypeError):
                confidence = 0.5
            kg.add_evidence(
                ev['evidence_id'],
                ev.get('evidence_summary', ''),
                ev.get('collected_by', 'Unknown'),
                ev.get('collection_date', ''),
                freshness_days=freshness,
                confidence=confidence,
                evidence_type=ev.get('evidence_type', 'Unknown'),
                status=ev.get('status', 'Unknown'),
            )

        self._requirements_cache = requirements
        self._evidence_cache = evidence_list

    def _run_semantic_mapping(self) -> List[Dict]:
        """Run semantic mapping between evidence and requirements."""
        requirements = [r for r in self._requirements_cache if r.get('framework') != 'META']
        evidence = self._evidence_cache
        if not requirements or not evidence:
            return []

        mappings = []
        req_list = [
            {
                'requirement_id': r['requirement_id'],
                'requirement_text': r.get('description', ''),
                'framework': r.get('framework', ''),
            }
            for r in requirements
        ]
        result = self.semantic_mapper.batch_search(req_list, evidence, threshold=0.20)

        for req_id, matches in result.items():
            for match in matches[:8]:  # top 8 per requirement
                mapping = {
                    'evidence_id': match.evidence_id,
                    'requirement_id': req_id,
                    'confidence': match.similarity_score,
                    'similarity_score': match.similarity_score,
                    'mapped_by': 'SEMANTIC_MAPPER',
                    'mapped_date': datetime.now().isoformat(),
                }
                self.db.insert_mapping(mapping)
                self.knowledge_graph.link_evidence_supports(
                    match.evidence_id, req_id, strength=match.similarity_score
                )
                mappings.append(mapping)

        return mappings

    # ------------------------------------------------------------------ #
    #  ANALYSIS                                                            #
    # ------------------------------------------------------------------ #

    def run_compliance_analysis(self, framework: str = "ALL") -> Dict:
        requirements = self._get_requirements_for_framework(framework)
        if not requirements:
            return {"error": f"No requirements for framework: {framework}", "compliance_score": 0}

        mappings = self.db.get_all_mappings()
        mapped_req_ids = set(m['requirement_id'] for m in mappings)
        covered = [r for r in requirements if r['requirement_id'] in mapped_req_ids]
        coverage_pct = len(covered) / len(requirements) * 100 if requirements else 0

        # Average confidence of mappings for this framework
        fw_mapping_confs = [
            m['confidence'] for m in mappings
            if m['requirement_id'] in {r['requirement_id'] for r in requirements}
        ]
        avg_conf = sum(fw_mapping_confs) / len(fw_mapping_confs) if fw_mapping_confs else 0

        score = (coverage_pct * 0.6 + avg_conf * 100 * 0.4)

        gaps = [r for r in requirements if r['requirement_id'] not in mapped_req_ids]

        return {
            "framework": framework,
            "analysis_date": datetime.now().isoformat(),
            "compliance_score": round(score, 1),
            "coverage_percentage": f"{coverage_pct:.1f}%",
            "requirements_analyzed": len(requirements),
            "requirements_covered": len(covered),
            "requirements_with_gaps": len(gaps),
            "average_confidence": round(avg_conf, 3),
            "gaps": [{"requirement_id": r["requirement_id"],
                       "description": r.get("description", ""),
                       "priority": "HIGH"} for r in gaps[:20]],
            "status": "COMPLIANT" if score >= 75 else "NON_COMPLIANT",
        }

    # ------------------------------------------------------------------ #
    #  CHALLENGE AUDIT                                                     #
    # ------------------------------------------------------------------ #

    def run_challenge_audit(self, framework: str = "ALL") -> Dict:
        requirements = self._get_requirements_for_framework(framework)
        if not requirements:
            return {"error": f"No requirements for framework: {framework}"}

        evidence = self._evidence_cache or self.db.get_all_evidence()
        mappings = self.db.get_all_mappings()
        evidence_by_id = {e['evidence_id']: e for e in evidence}

        results = []
        for req in requirements:
            req_id = req['requirement_id']
            req_mappings = [m for m in mappings if m['requirement_id'] == req_id]
            req_evidence = [evidence_by_id[m['evidence_id']] for m in req_mappings
                            if m['evidence_id'] in evidence_by_id]
            avg_conf = (sum(m['confidence'] for m in req_mappings) / len(req_mappings)
                        if req_mappings else 0.0)

            report = self.challenge_auditor.audit_requirement(
                req_id, req.get('description', ''), avg_conf, req_evidence
            )

            for ch in report.challenges:
                self.db.insert_challenge_finding({
                    'requirement_id': req_id,
                    'finding_type': ch.challenge_type,
                    'description': ch.description,
                    'severity': ch.severity,
                    'remediation_suggestion': ch.remediation_suggestion,
                    'impact_on_confidence': ch.impact_on_confidence,
                    'status': 'OPEN',
                })

            results.append({
                "requirement_id": req_id,
                "requirement_description": req.get('description', ''),
                "status": report.status,
                "findings_count": report.total_challenges,
                "recommendation": report.overall_audit_recommendation,
                "findings": [
                    {"type": c.challenge_type, "severity": c.severity,
                     "description": c.description, "remediation": c.remediation_suggestion}
                    for c in report.challenges
                ],
            })

        fail_count = sum(1 for r in results if r['status'] == 'FAIL')
        conditional = sum(1 for r in results if r['status'] == 'CONDITIONAL_PASS')
        concerns = sum(1 for r in results if r['status'] == 'PASS_WITH_CONCERNS')
        passes = sum(1 for r in results if r['status'] == 'PASS')
        all_findings = [f for r in results for f in r['findings']]
        criticals = sum(1 for f in all_findings if f['severity'] == 'CRITICAL')
        highs = sum(1 for f in all_findings if f['severity'] == 'HIGH')

        if fail_count > 0:
            exec_summary = f"🚨 AUDIT RISK HIGH: {fail_count} requirement(s) have insufficient evidence. {criticals} critical issues found."
        elif conditional > len(results) * 0.3:
            exec_summary = f"⚠️ AUDIT RISK MODERATE: {conditional} requirement(s) need strengthening."
        else:
            exec_summary = "✅ AUDIT READY: Strong evidence across most requirements."

        return {
            "framework": framework,
            "total_challenged": len(results),
            "pass_count": passes,
            "conditional_count": conditional,
            "concerns_count": concerns,
            "fail_count": fail_count,
            "critical_findings": criticals,
            "high_findings": highs,
            "total_findings": len(all_findings),
            "executive_summary": exec_summary,
            "detailed_results": results,
            "challenged_at": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------ #
    #  CONFIDENCE + NARRATIVES                                             #
    # ------------------------------------------------------------------ #

    def run_confidence_and_narratives(self, framework: str = "ALL") -> Dict:
        requirements = self._get_requirements_for_framework(framework)
        evidence = self._evidence_cache or self.db.get_all_evidence()
        mappings = self.db.get_all_mappings()
        evidence_by_id = {e['evidence_id']: e for e in evidence}

        results = []
        for req in requirements:
            req_id = req['requirement_id']
            req_mappings = [m for m in mappings if m['requirement_id'] == req_id]
            req_evidence = [evidence_by_id[m['evidence_id']] for m in req_mappings
                            if m['evidence_id'] in evidence_by_id]

            confidence = self.confidence_engine.calculate_confidence(
                requirement_id=req_id,
                requirement_text=req.get('description', ''),
                supporting_evidence=req_evidence,
                requirement_severity=req.get('severity', 'MEDIUM'),
            )

            narrative = self.narrative_generator.generate_narrative(
                requirement_id=req_id,
                requirement_text=req.get('description', ''),
                supporting_evidence=req_evidence,
                confidence_score=confidence.confidence_score,
                frameworks=[req.get('framework', 'General')],
                responsible_team=req.get('responsible_team', 'Unknown'),
            )

            self.db.insert_confidence_score({
                'requirement_id': req_id,
                'compliance_status': confidence.compliance_status,
                'confidence_score': confidence.confidence_score,
                'confidence_percentage': confidence.confidence_percentage,
                'audit_ready': confidence.audit_ready,
                'recommendation': confidence.recommendation,
                'next_review_date': confidence.next_review_date,
            })
            self.db.insert_narrative({
                'requirement_id': req_id,
                'executive_summary': narrative.executive_summary,
                'detailed_narrative': narrative.detailed_narrative,
                'risk_assessment': narrative.risk_assessment,
                'recommendation': narrative.recommendation,
                'confidence_level': narrative.confidence_level,
                'frameworks_addressed': narrative.frameworks_addressed,
            })

            results.append({
                "requirement_id": req_id,
                "description": req.get('description', ''),
                "framework": req.get('framework', 'General'),
                "compliance_status": confidence.compliance_status,
                "confidence_score": confidence.confidence_score,
                "confidence_percentage": confidence.confidence_percentage,
                "audit_ready": confidence.audit_ready,
                "red_flags": confidence.red_flags,
                "strengths": confidence.strengths,
                "recommendation": confidence.recommendation,
                "next_review_date": confidence.next_review_date,
                "factors": [
                    {"name": f.name, "score": f.score, "weight": f.weight,
                     "reasoning": f.reasoning}
                    for f in confidence.factors
                ],
                "narrative": {
                    "executive_summary": narrative.executive_summary,
                    "detailed_narrative": narrative.detailed_narrative,
                    "risk_assessment": narrative.risk_assessment,
                    "recommendation": narrative.recommendation,
                    "confidence_level": narrative.confidence_level,
                    "supporting_points": narrative.supporting_points,
                },
            })

        return {
            "framework": framework,
            "total_requirements": len(results),
            "compliant": sum(1 for r in results if r['compliance_status'] == 'COMPLIANT'),
            "conditional": sum(1 for r in results if r['compliance_status'] == 'CONDITIONAL'),
            "at_risk": sum(1 for r in results if r['compliance_status'] == 'AT_RISK'),
            "non_compliant": sum(1 for r in results if r['compliance_status'] == 'NON_COMPLIANT'),
            "audit_ready_count": sum(1 for r in results if r['audit_ready']),
            "requirements": results,
            "generated_at": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------ #
    #  REPORT GENERATION                                                   #
    # ------------------------------------------------------------------ #

    def generate_report(self, framework: str = "ALL") -> Dict:
        analysis = self.run_compliance_analysis(framework)
        challenge = self.run_challenge_audit(framework)
        confidence_data = self.run_confidence_and_narratives(framework)

        report_id = f"RPT-{framework}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "report_id": report_id,
            "framework": framework,
            "generated_at": datetime.now().isoformat(),
            "generated_by": "Unified Compliance Intelligence Platform",
            "compliance_analysis": analysis,
            "challenge_audit": challenge,
            "confidence_assessment": confidence_data,
            "executive_summary": self._exec_summary(analysis, challenge, confidence_data),
            "recommendations": self._recommendations(analysis, challenge, confidence_data),
        }

        self.db.insert_report({
            "report_id": report_id,
            "report_type": "COMPREHENSIVE_AUDIT",
            "framework": framework,
            "generated_at": report["generated_at"],
            "generated_by": "System",
            "status": analysis.get("status", "UNKNOWN"),
            "summary": report["executive_summary"],
            "data": report,
        })

        return report

    def _exec_summary(self, analysis, challenge, confidence_data) -> str:
        score = analysis.get('compliance_score', 0)
        fail = challenge.get('fail_count', 0)
        crit = challenge.get('critical_findings', 0)
        total = confidence_data.get('total_requirements', 0)
        compliant = confidence_data.get('compliant', 0)

        parts = []
        if score >= 85:
            parts.append(f"✅ STRONG COMPLIANCE ({score:.1f}%): Organization demonstrates robust compliance.")
        elif score >= 70:
            parts.append(f"⚡ ACCEPTABLE COMPLIANCE ({score:.1f}%): Generally compliant with minor gaps.")
        else:
            parts.append(f"⚠️ COMPLIANCE GAPS ({score:.1f}%): Significant improvements needed.")

        if fail > 0:
            parts.append(f"{fail} requirement(s) have insufficient evidence and require immediate attention.")
        if crit > 0:
            parts.append(f"{crit} critical issue(s) must be resolved before external audit.")
        parts.append(f"Confidence assessment: {compliant}/{total} requirements fully compliant.")

        return " ".join(parts)

    def _recommendations(self, analysis, challenge, confidence_data) -> List[str]:
        recs = []
        if analysis.get('requirements_with_gaps', 0) > 0:
            recs.append(f"Collect evidence for {analysis['requirements_with_gaps']} requirement(s) with no evidence.")
        if challenge.get('fail_count', 0) > 0:
            recs.append(f"Address {challenge['fail_count']} failing requirement(s) before audit.")
        if challenge.get('critical_findings', 0) > 0:
            recs.append(f"Resolve {challenge['critical_findings']} critical finding(s) immediately.")
        if not recs:
            recs.append("Maintain current compliance practices. Schedule next review on time.")
        return recs

    # ------------------------------------------------------------------ #
    #  COPILOT                                                             #
    # ------------------------------------------------------------------ #

    def query_copilot(self, question: str) -> Dict:
        response = self.compliance_copilot.query(question)
        self.db.insert_copilot_query(
            question, response.query_type, response.answer, response.confidence
        )
        return {
            "query": response.query,
            "query_type": response.query_type,
            "answer": response.answer,
            "answer_summary": response.answer_summary,
            "confidence": response.confidence,
            "frameworks": response.frameworks,
            "results": response.results,
            "generated_at": response.generated_at,
        }

    # ------------------------------------------------------------------ #
    #  HELPERS                                                             #
    # ------------------------------------------------------------------ #

    def _get_requirements_for_framework(self, framework: str) -> List[Dict]:
        all_reqs = self._requirements_cache or self.db.get_all_requirements()
        if framework == "ALL":
            return [r for r in all_reqs if r.get('framework') != 'META']
        return [r for r in all_reqs if r.get('framework') == framework and r.get('framework') != 'META']

    def get_system_status(self) -> Dict:
        stats = self.db.get_dashboard_stats()
        kg_summary = self.knowledge_graph.get_summary()
        return {
            **stats,
            "knowledge_graph": kg_summary,
            "components": {
                "llm_extractor": "mock" if self.use_mock else "live",
                "semantic_mapper": "mock" if self.semantic_mapper.use_mock else "sentence-transformers",
                "knowledge_graph": "active",
                "challenge_auditor": "active",
                "confidence_engine": "active",
                "narrative_generator": "mock" if self.use_mock else "llm",
                "compliance_copilot": "active",
            }
        }

    def reload_caches(self):
        self._requirements_cache = self.db.get_all_requirements()
        self._evidence_cache = self.db.get_all_evidence()
        self._rebuild_knowledge_graph()
