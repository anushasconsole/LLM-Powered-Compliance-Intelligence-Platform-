"""
Compliance Copilot - Natural Language Interface for Compliance Queries
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


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
        'pci': 'PCI-DSS', 'iso': 'ISO27001', 'hipaa': 'HIPAA', 'cis': 'CIS',
    }

    def __init__(self, knowledge_graph, semantic_mapper, confidence_engine):
        self.kg = knowledge_graph
        self.mapper = semantic_mapper
        self.engine = confidence_engine

    def query(self, user_query: str) -> CopilotResponse:
        q = user_query.lower()

        if any(p in q for p in ['show evidence', 'evidence for', 'prove']):
            return self._evidence_query(user_query)

        if any(p in q for p in ['missing', 'gap', 'not covered', 'no evidence']):
            return self._gaps_query(user_query)

        if any(fw in q for fw in self.FRAMEWORK_MAP.keys()):
            return self._framework_query(user_query)

        if any(p in q for p in ['status', 'how are', 'what is the']):
            return self._status_query(user_query)

        return self._help_response(user_query)

    def _framework_query(self, query: str) -> CopilotResponse:
        fw = self._extract_framework(query)
        if not fw:
            return self._help_response(query)

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

    def _status_query(self, query: str) -> CopilotResponse:
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
            "I can help you with compliance queries. Try asking:\n\n"
            "- **'Show GDPR compliance status'**\n"
            "- **'Which requirements are missing evidence?'**\n"
            "- **'Show NIST gaps'**\n"
            "- **'What is the current system status?'**\n"
            "- **'Show SOX compliance'**\n"
            "- **'What evidence is stale?'**"
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
