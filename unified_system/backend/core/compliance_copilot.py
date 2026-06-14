"""
Compliance Copilot - Natural Language Interface for Compliance Queries
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta


@dataclass
class CopilotResponse:
    query: str
    query_type: str
    answer: str
    answer_summary: str
    results: List[Dict] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    confidence: float = 0.8
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ComplianceCopilot:
    FRAMEWORK_MAP = {
        'gdpr': 'GDPR', 'nist': 'NIST', 'sox': 'SOX',
        'pci': 'PCI-DSS', 'pci-dss': 'PCI-DSS', 'iso': 'ISO27001', 
        'iso27001': 'ISO27001', 'iso 27001': 'ISO27001',
        'hipaa': 'HIPAA', 'cis': 'CIS',
    }

    def __init__(self, knowledge_graph, semantic_mapper, confidence_engine, database=None):
        self.kg = knowledge_graph
        self.mapper = semantic_mapper
        self.engine = confidence_engine
        self.db = database

    def query(self, user_query: str) -> CopilotResponse:
        q = user_query.lower()

        # Gap analysis queries
        if any(p in q for p in ['gap', 'gaps', 'missing', 'no evidence', 'not covered', 'incomplete']):
            return self._gaps_query(user_query)

        # Evidence queries  
        if any(p in q for p in ['show evidence', 'evidence for', 'list evidence', 'what evidence', 'prove']):
            return self._evidence_query(user_query)

        # Stale evidence queries
        if any(p in q for p in ['stale', 'old', 'outdated', 'expired']):
            return self._stale_evidence_query(user_query)

        # Framework-specific queries
        if any(fw in q for fw in self.FRAMEWORK_MAP.keys()):
            return self._framework_query(user_query)

        # Requirement queries
        if any(p in q for p in ['requirement', 'requirements', 'controls']):
            return self._requirements_query(user_query)

        # Status/summary queries
        if any(p in q for p in ['status', 'how are', 'what is', 'summary', 'overview']):
            return self._status_query(user_query)

        # Anomaly queries
        if any(p in q for p in ['anomal', 'issue', 'problem', 'risk']):
            return self._anomaly_query(user_query)

        return self._help_response(user_query)

    def _framework_query(self, query: str) -> CopilotResponse:
        fw = self._extract_framework(query)
        if not fw:
            return self._help_response(query)

        # Get data from database if available
        if self.db:
            all_reqs = self.db.get_all_requirements()
            all_evidence = self.db.get_all_evidence()
            
            # Filter by framework
            fw_reqs = [r for r in all_reqs if r.get('framework') == fw]
            fw_evidence = [e for e in all_evidence if e.get('framework') == fw]
            
            # Calculate statistics
            total_reqs = len(fw_reqs)
            reqs_with_evidence = len(set([e.get('requirement_id') for e in fw_evidence if e.get('requirement_id')]))
            
            # Check for gaps
            req_ids = set([r.get('requirement_id') for r in fw_reqs])
            evidence_req_ids = set([e.get('requirement_id') for e in fw_evidence if e.get('requirement_id')])
            gaps = req_ids - evidence_req_ids
            
            # Count stale evidence (>90 days)
            stale_count = 0
            low_confidence = 0
            for e in fw_evidence:
                if e.get('freshness_days', 0) > 90:
                    stale_count += 1
                if e.get('confidence_score', 1.0) < 0.70:
                    low_confidence += 1
            
            coverage_pct = (reqs_with_evidence / total_reqs * 100) if total_reqs > 0 else 0
            
            if coverage_pct >= 85:
                status_icon = "✅"
                status_text = "COMPLIANT"
            elif coverage_pct >= 70:
                status_icon = "⚠️"
                status_text = "CONDITIONAL"
            elif coverage_pct >= 50:
                status_icon = "⚠️"
                status_text = "AT RISK"
            else:
                status_icon = "❌"
                status_text = "NON-COMPLIANT"

            answer = (
                f"## {fw} Compliance Status {status_icon}\n\n"
                f"**Coverage:** {reqs_with_evidence}/{total_reqs} requirements ({coverage_pct:.1f}%)\n\n"
                f"**Requirements Missing Evidence:** {len(gaps)}\n\n"
                f"**Stale Evidence (>90 days):** {stale_count} item(s)\n\n"
                f"**Low Confidence Evidence (<0.70):** {low_confidence} item(s)\n\n"
                f"**Overall Status:** {status_text}\n\n"
            )
            
            if len(gaps) > 0:
                answer += f"\n**Top Gaps:**\n"
                gap_list = list(gaps)[:5]
                for g in gap_list:
                    req = next((r for r in fw_reqs if r.get('requirement_id') == g), None)
                    if req:
                        desc = req.get('description', 'N/A')[:80]
                        answer += f"- `{g}`: {desc}\n"
                if len(gaps) > 5:
                    answer += f"\n... and {len(gaps) - 5} more gaps\n"

            return CopilotResponse(
                query=query,
                query_type="framework_status",
                answer=answer,
                answer_summary=f"{fw}: {coverage_pct:.0f}% coverage ({status_text})",
                frameworks=[fw],
                results=fw_reqs[:10],
                confidence=0.90,
            )
        
        # Fallback to knowledge graph
        fw_key = f"FW-{fw}"
        coverage = self.kg.get_framework_coverage(fw_key)
        reqs = self.kg.get_requirements_by_framework(fw_key)
        pct = coverage.get('coverage_percent', 0)

        if pct >= 80:
            status_icon = "✅"
            status_text = "GOOD"
        elif pct >= 50:
            status_icon = "⚠️"
            status_text = "PARTIAL"
        else:
            status_icon = "❌"
            status_text = "AT RISK"

        answer = (
            f"**{fw} Compliance Status** {status_icon}\n\n"
            f"Coverage: {coverage.get('requirements_with_evidence', 0)}/{coverage.get('total_requirements', 0)} requirements ({pct:.0f}%)\n"
            f"Stale Evidence: {coverage.get('stale_evidence_count', 0)} item(s)\n"
            f"Low Confidence Items: {coverage.get('low_confidence_count', 0)}\n"
            f"Status: {status_text}"
        )

        return CopilotResponse(
            query=query,
            query_type="framework_status",
            answer=answer,
            answer_summary=f"{fw}: {pct:.0f}% coverage ({status_text})",
            frameworks=[fw],
            confidence=0.90,
        )

    def _gaps_query(self, query: str) -> CopilotResponse:
        fw = self._extract_framework(query)
        
        if self.db:
            all_reqs = self.db.get_all_requirements()
            all_evidence = self.db.get_all_evidence()
            
            # Filter by framework if specified
            if fw:
                all_reqs = [r for r in all_reqs if r.get('framework') == fw]
                all_evidence = [e for e in all_evidence if e.get('framework') == fw]
            
            # Find requirements with no evidence
            req_ids_with_evidence = set([e.get('requirement_id') for e in all_evidence if e.get('requirement_id')])
            gaps = [r for r in all_reqs if r.get('requirement_id') not in req_ids_with_evidence]
            
            if not gaps:
                answer = f"✅ Great news! All {fw if fw else ''} requirements have supporting evidence."
            else:
                fw_text = f"{fw} " if fw else ""
                answer = f"## Found **{len(gaps)}** {fw_text}requirement(s) without evidence:\n\n"
                for i, req in enumerate(gaps[:10], 1):
                    req_id = req.get('requirement_id', 'N/A')
                    desc = req.get('description', 'Unknown')[:100]
                    framework = req.get('framework', 'N/A')
                    answer += f"{i}. **`{req_id}`** ({framework})\n   {desc}...\n\n"
                if len(gaps) > 10:
                    answer += f"... and {len(gaps) - 10} more\n\n"
                
                answer += "\n**Recommendation:** Upload evidence for these requirements or collect automatically via integrations."

            return CopilotResponse(
                query=query,
                query_type="gaps",
                answer=answer,
                answer_summary=f"{len(gaps)} requirement(s) need evidence",
                results=gaps[:20],
                frameworks=[fw] if fw else [],
                confidence=0.95,
            )
        
        # Fallback
        lacking = self.kg.get_requirements_needing_evidence()
        if not lacking:
            answer = "✅ Great news! All requirements have at least some supporting evidence."
        else:
            answer = f"Found **{len(lacking)} requirement(s)** without evidence:\n\n"
            for i, req in enumerate(lacking[:8], 1):
                answer += f"{i}. `{req.get('requirement_id', 'N/A')}` — {req.get('requirement_name', 'Unknown')[:80]}\n"
            if len(lacking) > 8:
                answer += f"\n... and {len(lacking) - 8} more"

        return CopilotResponse(
            query=query,
            query_type="gaps",
            answer=answer,
            answer_summary=f"{len(lacking)} requirement(s) need evidence",
            results=lacking[:10],
            confidence=0.95,
        )

    def _evidence_query(self, query: str) -> CopilotResponse:
        fw = self._extract_framework(query)
        
        if self.db:
            all_evidence = self.db.get_all_evidence()
            
            # Filter by framework if specified
            if fw:
                all_evidence = [e for e in all_evidence if e.get('framework') == fw]
            
            total_evidence = len(all_evidence)
            
            # Categorize evidence
            fresh = [e for e in all_evidence if e.get('freshness_days', 0) <= 30]
            moderate = [e for e in all_evidence if 30 < e.get('freshness_days', 0) <= 90]
            stale = [e for e in all_evidence if e.get('freshness_days', 0) > 90]
            
            fw_text = f"{fw} " if fw else ""
            answer = f"## {fw_text}Evidence Status\n\n"
            answer += f"**Total Evidence:** {total_evidence} item(s)\n\n"
            answer += f"**Fresh (<30 days):** {len(fresh)} ✅\n\n"
            answer += f"**Moderate (30-90 days):** {len(moderate)} ⚠️\n\n"
            answer += f"**Stale (>90 days):** {len(stale)} ❌\n\n"
            
            if stale:
                answer += "\n**Stale Evidence Items:**\n"
                for i, e in enumerate(stale[:5], 1):
                    ev_id = e.get('evidence_id', 'N/A')
                    days = e.get('freshness_days', 0)
                    summary = e.get('evidence_summary', 'No description')[:80]
                    answer += f"{i}. `{ev_id}` ({days} days old): {summary}...\n"
                if len(stale) > 5:
                    answer += f"\n... and {len(stale) - 5} more stale items\n"
            
            return CopilotResponse(
                query=query,
                query_type="evidence",
                answer=answer,
                answer_summary=f"{total_evidence} evidence items ({len(stale)} stale)",
                results=all_evidence[:20],
                frameworks=[fw] if fw else [],
                confidence=0.90,
            )
        
        # Fallback
        stale = self.kg.get_stale_evidence(threshold_days=30)
        answer = "**Evidence Status**\n\n"
        if stale:
            answer += f"⚠️ {len(stale)} evidence item(s) are older than 30 days and may need refresh.\n\n"
        else:
            answer += "✅ All evidence appears fresh (< 30 days).\n\n"
        answer += "Use the Evidence page to view, filter, and upload evidence artifacts."

        return CopilotResponse(
            query=query,
            query_type="evidence",
            answer=answer,
            answer_summary=f"{len(stale)} stale evidence item(s) found",
            confidence=0.85,
        )
    
    def _stale_evidence_query(self, query: str) -> CopilotResponse:
        """Query specifically for stale/old evidence"""
        fw = self._extract_framework(query)
        
        if self.db:
            all_evidence = self.db.get_all_evidence()
            
            if fw:
                all_evidence = [e for e in all_evidence if e.get('framework') == fw]
            
            stale = [e for e in all_evidence if e.get('freshness_days', 0) > 90]
            
            fw_text = f"{fw} " if fw else ""
            if not stale:
                answer = f"✅ No stale {fw_text}evidence found! All evidence is less than 90 days old."
            else:
                answer = f"## Found **{len(stale)}** stale {fw_text}evidence item(s) (>90 days old):\n\n"
                for i, e in enumerate(stale[:10], 1):
                    ev_id = e.get('evidence_id', 'N/A')
                    days = e.get('freshness_days', 0)
                    summary = e.get('evidence_summary', 'No description')[:80]
                    req_id = e.get('requirement_id', 'N/A')
                    answer += f"{i}. **`{ev_id}`** ({days} days old)\n"
                    answer += f"   Requirement: `{req_id}`\n"
                    answer += f"   {summary}...\n\n"
                if len(stale) > 10:
                    answer += f"... and {len(stale) - 10} more\n\n"
                answer += "\n**Recommendation:** Refresh or recollect these evidence items."
            
            return CopilotResponse(
                query=query,
                query_type="stale_evidence",
                answer=answer,
                answer_summary=f"{len(stale)} stale evidence items",
                results=stale[:20],
                frameworks=[fw] if fw else [],
                confidence=0.90,
            )
        
        return self._evidence_query(query)
    
    def _requirements_query(self, query: str) -> CopilotResponse:
        """Query about requirements"""
        fw = self._extract_framework(query)
        
        if self.db:
            all_reqs = self.db.get_all_requirements()
            
            if fw:
                all_reqs = [r for r in all_reqs if r.get('framework') == fw]
            
            fw_text = f"{fw} " if fw else ""
            answer = f"## {fw_text}Requirements\n\n"
            answer += f"**Total Requirements:** {len(all_reqs)}\n\n"
            
            if len(all_reqs) > 0:
                answer += "**Sample Requirements:**\n\n"
                for i, req in enumerate(all_reqs[:10], 1):
                    req_id = req.get('requirement_id', 'N/A')
                    desc = req.get('description', 'No description')[:100]
                    framework = req.get('framework', 'N/A')
                    answer += f"{i}. **`{req_id}`** ({framework})\n   {desc}...\n\n"
                if len(all_reqs) > 10:
                    answer += f"... and {len(all_reqs) - 10} more\n"
            
            return CopilotResponse(
                query=query,
                query_type="requirements",
                answer=answer,
                answer_summary=f"{len(all_reqs)} requirements found",
                results=all_reqs[:20],
                frameworks=[fw] if fw else [],
                confidence=0.90,
            )
        
        return self._help_response(query)
    
    def _anomaly_query(self, query: str) -> CopilotResponse:
        """Query about anomalies and issues"""
        fw = self._extract_framework(query)
        
        if self.db:
            all_evidence = self.db.get_all_evidence()
            
            if fw:
                all_evidence = [e for e in all_evidence if e.get('framework') == fw]
            
            # Identify potential anomalies
            anomalies = []
            for e in all_evidence:
                issues = []
                if e.get('freshness_days', 0) > 90:
                    issues.append(f"Stale ({e.get('freshness_days')} days)")
                if e.get('confidence_score', 1.0) < 0.70:
                    issues.append(f"Low confidence ({e.get('confidence_score', 0):.2f})")
                if e.get('status') == 'REJECTED':
                    issues.append("Rejected")
                if e.get('anomaly_marker'):
                    issues.append(e.get('anomaly_marker'))
                
                if issues:
                    anomalies.append({
                        'evidence': e,
                        'issues': issues
                    })
            
            fw_text = f"{fw} " if fw else ""
            if not anomalies:
                answer = f"✅ No anomalies detected in {fw_text}evidence!"
            else:
                answer = f"## Found **{len(anomalies)}** potential {fw_text}anomalies:\n\n"
                for i, a in enumerate(anomalies[:10], 1):
                    e = a['evidence']
                    ev_id = e.get('evidence_id', 'N/A')
                    issues_text = ', '.join(a['issues'])
                    answer += f"{i}. **`{ev_id}`**: {issues_text}\n"
                    answer += f"   {e.get('evidence_summary', 'No description')[:80]}...\n\n"
                if len(anomalies) > 10:
                    answer += f"... and {len(anomalies) - 10} more\n\n"
                answer += "\n**Recommendation:** Review and remediate these issues in the Anomaly Detection page."
            
            return CopilotResponse(
                query=query,
                query_type="anomalies",
                answer=answer,
                answer_summary=f"{len(anomalies)} anomalies detected",
                results=[a['evidence'] for a in anomalies[:20]],
                frameworks=[fw] if fw else [],
                confidence=0.85,
            )
        
        return self._help_response(query)

    def _status_query(self, query: str) -> CopilotResponse:
        if self.db:
            all_reqs = self.db.get_all_requirements()
            all_evidence = self.db.get_all_evidence()
            
            # Group by framework
            frameworks = {}
            for req in all_reqs:
                fw = req.get('framework', 'Unknown')
                if fw not in frameworks:
                    frameworks[fw] = {'reqs': 0, 'evidence': 0}
                frameworks[fw]['reqs'] += 1
            
            for ev in all_evidence:
                fw = ev.get('framework', 'Unknown')
                if fw in frameworks:
                    frameworks[fw]['evidence'] += 1
            
            # Calculate overall statistics
            req_ids_with_evidence = set([e.get('requirement_id') for e in all_evidence if e.get('requirement_id')])
            reqs_with_evidence = len([r for r in all_reqs if r.get('requirement_id') in req_ids_with_evidence])
            
            stale_count = len([e for e in all_evidence if e.get('freshness_days', 0) > 90])
            low_confidence = len([e for e in all_evidence if e.get('confidence_score', 1.0) < 0.70])
            
            overall_coverage = (reqs_with_evidence / len(all_reqs) * 100) if all_reqs else 0
            
            answer = "## System Status Overview\n\n"
            answer += f"**Overall Compliance Coverage:** {overall_coverage:.1f}%\n\n"
            answer += f"**Total Requirements:** {len(all_reqs)}\n\n"
            answer += f"**Requirements with Evidence:** {reqs_with_evidence}\n\n"
            answer += f"**Total Evidence Items:** {len(all_evidence)}\n\n"
            answer += f"**Stale Evidence (>90 days):** {stale_count}\n\n"
            answer += f"**Low Confidence Evidence:** {low_confidence}\n\n"
            
            answer += "\n**Framework Breakdown:**\n\n"
            for fw, stats in sorted(frameworks.items()):
                coverage = (stats['evidence'] / stats['reqs'] * 100) if stats['reqs'] > 0 else 0
                status = "✅" if coverage >= 85 else "⚠️" if coverage >= 70 else "❌"
                answer += f"- **{fw}** {status}: {stats['reqs']} requirements, {coverage:.0f}% coverage\n"
            
            return CopilotResponse(
                query=query,
                query_type="status",
                answer=answer,
                answer_summary=f"Overall coverage: {overall_coverage:.0f}%",
                confidence=0.95,
            )
        
        # Fallback
        summary = self.kg.get_summary()
        answer = (
            f"**System Status**\n\n"
            f"Knowledge Graph: {summary.get('total_nodes', 0)} nodes, {summary.get('total_edges', 0)} edges\n"
            f"Requirements tracked: {summary.get('node_types', {}).get('REQUIREMENT', 0)}\n"
            f"Evidence artifacts: {summary.get('node_types', {}).get('EVIDENCE', 0)}\n"
            f"Frameworks: {summary.get('node_types', {}).get('FRAMEWORK', 0)}\n\n"
            f"Missing evidence: {len(self.kg.get_requirements_needing_evidence())} requirement(s)"
        )
        return CopilotResponse(
            query=query,
            query_type="status",
            answer=answer,
            answer_summary="System status retrieved",
            confidence=0.95,
        )

    def _help_response(self, query: str) -> CopilotResponse:
        answer = (
            "## Compliance Copilot - How Can I Help?\n\n"
            "I can answer questions about your compliance status. Try asking:\n\n"
            "**Framework Queries:**\n"
            "- 'Show GDPR compliance status'\n"
            "- 'What is the SOX coverage?'\n"
            "- 'HIPAA gaps'\n\n"
            "**Gap Analysis:**\n"
            "- 'Which requirements are missing evidence?'\n"
            "- 'Show GDPR gaps'\n"
            "- 'What requirements need evidence?'\n\n"
            "**Evidence Queries:**\n"
            "- 'Show all evidence'\n"
            "- 'What evidence is stale?'\n"
            "- 'List NIST evidence'\n\n"
            "**Status & Overview:**\n"
            "- 'System status'\n"
            "- 'Overall compliance summary'\n"
            "- 'What is the current coverage?'\n\n"
            "**Issues & Risks:**\n"
            "- 'Show anomalies'\n"
            "- 'What are the risks?'\n"
            "- 'List compliance issues'\n"
        )
        return CopilotResponse(
            query=query,
            query_type="help",
            answer=answer,
            answer_summary="How can I help?",
            confidence=0.5,
        )

    def _extract_framework(self, query: str) -> Optional[str]:
        q = query.lower()
        for key, value in self.FRAMEWORK_MAP.items():
            if key in q:
                return value
        return None
