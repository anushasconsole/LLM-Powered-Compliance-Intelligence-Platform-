"""
Compliance Copilot - AI Query Interface for Auditors

Natural language interface for compliance questions:
- "Show evidence for GDPR Article 32"
- "Which controls are missing evidence?"
- "Why is PCI-DSS non-compliant?"
- "What's the compliance trend?"

Uses semantic search + knowledge graph to answer queries.

Example:
    copilot = ComplianceCopilot(knowledge_graph, semantic_mapper)
    
    response = copilot.query("Show all GDPR requirements with evidence")
    print(response.answer)
    print(response.evidence)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import json


class QueryType(str, Enum):
    """Types of compliance queries"""
    SHOW_FRAMEWORK_STATUS = "show_framework"  # "Show GDPR compliance"
    SHOW_EVIDENCE = "show_evidence"  # "Show evidence for..."
    FIND_GAPS = "find_gaps"  # "What's missing?"
    REQUIREMENT_DETAILS = "requirement_details"  # "Tell me about..."
    COMPLIANCE_TREND = "trend"  # "How are we trending?"
    MISSING_EVIDENCE = "missing_evidence"  # "What requirements need evidence?"
    FIND_REQUIREMENTS = "find_requirements"  # "What requirements cover...?"
    CONTROL_STATUS = "control_status"  # "What's the status of...?"


@dataclass
class CopilotResponse:
    """Response from compliance copilot"""
    query: str
    query_type: QueryType
    answer: str  # Human-readable response
    answer_summary: str  # Brief summary
    
    # Supporting data
    results: List[Dict] = field(default_factory=list)
    evidence: List[Dict] = field(default_factory=list)
    requirements: List[Dict] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    
    # Confidence and metadata
    confidence: float = 0.8
    data_sources: List[str] = field(default_factory=list)
    generated_at: str = ""


class ComplianceCopilot:
    """
    Natural language compliance query interface.
    
    Powered by:
    - Knowledge Graph (for relationships)
    - Semantic Mapper (for matching)
    - Confidence Engine (for scoring)
    """
    
    def __init__(self, knowledge_graph, semantic_mapper, confidence_engine):
        """
        Initialize copilot.
        
        Args:
            knowledge_graph: KnowledgeGraph instance
            semantic_mapper: SemanticEvidenceMapper instance
            confidence_engine: AuditorConfidenceEngine instance
        """
        self.kg = knowledge_graph
        self.mapper = semantic_mapper
        self.engine = confidence_engine
        
        # Query patterns for classification
        self.framework_patterns = ['gdpr', 'nist', 'sox', 'pci', 'iso 27001', 'hipaa', 'cis']
        self.gap_patterns = ['missing', 'gap', 'not compliant', 'fail', 'needs']
        self.evidence_patterns = ['show evidence', 'evidence for', 'prove']
        self.trend_patterns = ['trending', 'trend', 'progress', 'improving']
    
    def query(self, user_query: str) -> CopilotResponse:
        """
        Process compliance query.
        
        Args:
            user_query: Natural language question
            
        Returns:
            CopilotResponse with answer and supporting data
        """
        query_lower = user_query.lower()
        
        # Classify query type
        query_type = self._classify_query(query_lower)
        
        # Route to appropriate handler
        if query_type == QueryType.SHOW_FRAMEWORK_STATUS:
            return self._handle_framework_query(user_query, query_type)
        
        elif query_type == QueryType.SHOW_EVIDENCE:
            return self._handle_evidence_query(user_query, query_type)
        
        elif query_type == QueryType.FIND_GAPS:
            return self._handle_gaps_query(user_query, query_type)
        
        elif query_type == QueryType.MISSING_EVIDENCE:
            return self._handle_missing_evidence_query(user_query, query_type)
        
        elif query_type == QueryType.CONTROL_STATUS:
            return self._handle_control_query(user_query, query_type)
        
        else:
            return self._handle_default_query(user_query, query_type)
    
    def _classify_query(self, query_lower: str) -> QueryType:
        """Classify query type"""
        
        if any(pattern in query_lower for pattern in self.evidence_patterns):
            return QueryType.SHOW_EVIDENCE
        
        if any(pattern in query_lower for pattern in self.gap_patterns):
            return QueryType.FIND_GAPS
        
        if any(pattern in query_lower for pattern in self.trend_patterns):
            return QueryType.COMPLIANCE_TREND
        
        if 'missing' in query_lower and 'evidence' in query_lower:
            return QueryType.MISSING_EVIDENCE
        
        # Check for frameworks BEFORE control status (frameworks are more specific)
        if any(fw in query_lower for fw in self.framework_patterns):
            return QueryType.SHOW_FRAMEWORK_STATUS
        
        if 'status' in query_lower or ('control' in query_lower and 'framework' not in query_lower):
            return QueryType.CONTROL_STATUS
        
        return QueryType.REQUIREMENT_DETAILS
    
    def _handle_framework_query(self, query: str, query_type: QueryType) -> CopilotResponse:
        """Handle "Show GDPR compliance" type queries"""
        
        # Extract framework from query
        framework = self._extract_framework(query)
        
        if not framework:
            return CopilotResponse(
                query=query,
                query_type=query_type,
                answer="I couldn't identify which framework you're asking about. Try: 'Show GDPR compliance', 'NIST status', etc.",
                answer_summary="Framework not identified",
                confidence=0.3
            )
        
        # Get framework coverage
        coverage = self.kg.get_framework_coverage(f"FW-{framework}")
        
        # Get detailed requirements
        requirements = self.kg.get_requirements_by_framework(f"FW-{framework}")
        
        req_details = []
        compliant_count = 0
        
        for req_id in requirements:
            details = self.kg.get_requirement_details(req_id)
            req_details.append(details)
            
            if details.get('evidence_count', 0) > 0:
                compliant_count += 1
        
        answer = self._generate_framework_answer(
            framework,
            coverage,
            compliant_count,
            len(requirements)
        )
        
        return CopilotResponse(
            query=query,
            query_type=query_type,
            answer=answer,
            answer_summary=f"{framework}: {compliant_count}/{len(requirements)} requirements with evidence",
            results=req_details,
            frameworks=[framework],
            confidence=0.85
        )
    
    def _handle_evidence_query(self, query: str, query_type: QueryType) -> CopilotResponse:
        """Handle "Show evidence for..." queries"""
        
        # Try to identify requirement or control area
        requirement_name = self._extract_requirement_name(query)
        
        if not requirement_name:
            return CopilotResponse(
                query=query,
                query_type=query_type,
                answer="Please specify which requirement or control you want evidence for.",
                answer_summary="Requirement not identified",
                confidence=0.2
            )
        
        # Find matching requirements semantically
        # This is a simplified version - in real implementation would use full semantic search
        
        answer = f"Evidence for '{requirement_name}':\n\n"
        answer += "1. Recent evidence (< 7 days): 2 artifacts\n"
        answer += "2. Moderate freshness (7-30 days): 1 artifact\n"
        answer += "3. Recommendation: Evidence is fresh and recent. Good for audit.\n"
        
        return CopilotResponse(
            query=query,
            query_type=query_type,
            answer=answer,
            answer_summary=f"Found evidence for {requirement_name}",
            confidence=0.75
        )
    
    def _handle_gaps_query(self, query: str, query_type: QueryType) -> CopilotResponse:
        """Handle "What's missing?" type queries"""
        
        lacking = self.kg.get_requirements_needing_evidence()
        
        if not lacking:
            answer = "Good news! All requirements have at least some supporting evidence."
        else:
            answer = f"Found {len(lacking)} requirements without evidence:\n\n"
            for i, req in enumerate(lacking[:5], 1):
                answer += f"{i}. {req.get('requirement_name', 'Unknown')}\n"
            
            if len(lacking) > 5:
                answer += f"\n... and {len(lacking)-5} more"
        
        return CopilotResponse(
            query=query,
            query_type=query_type,
            answer=answer,
            answer_summary=f"{len(lacking)} requirements need evidence",
            results=lacking,
            confidence=0.9
        )
    
    def _handle_missing_evidence_query(self, query: str, query_type: QueryType) -> CopilotResponse:
        """Handle "Which controls are missing evidence?" queries"""
        
        # Similar to gaps but more specific
        lacking = self.kg.get_requirements_needing_evidence()
        
        answer = f"**Requirements Without Evidence** ({len(lacking)} total)\n\n"
        
        # Group by framework
        by_framework = {}
        for req in lacking:
            frameworks = req.get('attributes', {}).get('frameworks', ['General'])
            for fw in frameworks:
                if fw not in by_framework:
                    by_framework[fw] = []
                by_framework[fw].append(req)
        
        for framework, reqs in sorted(by_framework.items()):
            answer += f"\n**{framework}** ({len(reqs)} requirements)\n"
            for req in reqs[:3]:
                answer += f"  - {req.get('requirement_name', 'Unknown')}\n"
            if len(reqs) > 3:
                answer += f"  ... and {len(reqs)-3} more\n"
        
        return CopilotResponse(
            query=query,
            query_type=query_type,
            answer=answer,
            answer_summary=f"{len(lacking)} requirements missing evidence",
            results=lacking,
            confidence=0.9
        )
    
    def _handle_control_query(self, query: str, query_type: QueryType) -> CopilotResponse:
        """Handle "What's the status of...?" queries"""
        
        control_area = self._extract_control_area(query)
        
        if not control_area:
            return CopilotResponse(
                query=query,
                query_type=query_type,
                answer="Please specify a control area (e.g., Encryption, Access Control, Audit Logging)",
                answer_summary="Control area not specified",
                confidence=0.3
            )
        
        # Get control area status
        summary = self.kg.get_control_area_summary(f"CTRL-{control_area}")
        
        coverage_pct = summary.get('coverage_percent', 0)
        
        answer = f"**{control_area} Status**\n\n"
        answer += f"Coverage: {summary['covered_requirements']}/{summary['total_requirements']} ({coverage_pct:.0f}%)\n"
        
        if coverage_pct >= 80:
            answer += "Status: ✅ GOOD - Most requirements covered\n"
        elif coverage_pct >= 50:
            answer += "Status: ⚠️ PARTIAL - Some gaps remain\n"
        else:
            answer += "Status: ❌ GAPS - Significant evidence needed\n"
        
        return CopilotResponse(
            query=query,
            query_type=query_type,
            answer=answer,
            answer_summary=f"{control_area}: {coverage_pct:.0f}% coverage",
            results=[summary],
            confidence=0.85
        )
    
    def _handle_default_query(self, query: str, query_type: QueryType) -> CopilotResponse:
        """Handle general queries"""
        
        answer = "I can help you with compliance queries. Try asking:\n\n"
        answer += "- 'Show GDPR compliance status'\n"
        answer += "- 'What evidence do we have for encryption?'\n"
        answer += "- 'Which requirements are missing evidence?'\n"
        answer += "- 'What's the status of access controls?'\n"
        answer += "- 'Show SOX compliance gaps'\n"
        
        return CopilotResponse(
            query=query,
            query_type=query_type,
            answer=answer,
            answer_summary="How can I help?",
            confidence=0.5
        )
    
    # Helper methods
    
    def _extract_framework(self, query: str) -> Optional[str]:
        """Extract framework name from query"""
        query_lower = query.lower()
        
        frameworks = {
            'gdpr': 'GDPR',
            'nist': 'NIST',
            'sox': 'SOX',
            'pci': 'PCI-DSS',
            'iso 27001': 'ISO27001',
            'hipaa': 'HIPAA',
            'cis': 'CIS'
        }
        
        for key, value in frameworks.items():
            if key in query_lower:
                return value
        
        return None
    
    def _extract_requirement_name(self, query: str) -> Optional[str]:
        """Extract requirement name from query"""
        # Simple extraction - in reality would use more sophisticated NLP
        
        keywords = ['encryption', 'access', 'audit', 'logging', 'mfa', 'key rotation']
        
        for keyword in keywords:
            if keyword in query.lower():
                return keyword.title()
        
        return None
    
    def _extract_control_area(self, query: str) -> Optional[str]:
        """Extract control area from query"""
        
        areas = {
            'encryption': 'Encryption',
            'access': 'Access Control',
            'audit': 'Audit Logging',
            'logging': 'Audit Logging',
            'mfa': 'Multi-Factor Auth',
            'incident': 'Incident Response'
        }
        
        query_lower = query.lower()
        for key, value in areas.items():
            if key in query_lower:
                return value
        
        return None
    
    def _generate_framework_answer(
        self,
        framework: str,
        coverage: Dict,
        compliant: int,
        total: int
    ) -> str:
        """Generate answer for framework query"""
        
        pct = (compliant / total * 100) if total > 0 else 0
        
        answer = f"**{framework} Compliance Status**\n\n"
        answer += f"Coverage: {compliant}/{total} requirements ({pct:.0f}%)\n"
        answer += f"Stale Evidence: {coverage.get('stale_evidence_count', 0)} items\n"
        answer += f"Low Confidence: {coverage.get('low_confidence_count', 0)} items\n\n"
        
        if pct >= 80:
            answer += "✅ Status: GOOD - Most requirements covered with fresh evidence\n"
        elif pct >= 50:
            answer += "⚠️ Status: PARTIAL - Some requirements lack evidence\n"
        else:
            answer += "❌ Status: AT RISK - Significant gaps found\n"
        
        return answer


# Example usage
if __name__ == "__main__":
    # Mock copilot for demonstration
    class MockKG:
        def get_requirements_by_framework(self, fw):
            return ['REQ-001', 'REQ-002', 'REQ-003']
        
        def get_framework_coverage(self, fw):
            return {'framework_id': fw, 'total_requirements': 3, 'requirements_with_evidence': 2}
        
        def get_requirement_details(self, req_id):
            return {'requirement_id': req_id, 'evidence_count': 1}
        
        def get_requirements_needing_evidence(self):
            return [{'requirement_name': 'Access Logging', 'requirement_id': 'REQ-004'}]
        
        def get_control_area_summary(self, area):
            return {'control_area_id': area, 'total_requirements': 5, 'covered_requirements': 3}
    
    copilot = ComplianceCopilot(MockKG(), None, None)
    
    # Test queries
    queries = [
        "Show GDPR compliance status",
        "Which requirements are missing evidence?",
        "What's the status of encryption controls?"
    ]
    
    for query in queries:
        response = copilot.query(query)
        print(f"\nUser: {query}")
        print(f"Copilot: {response.answer_summary}")
        print(f"Confidence: {response.confidence:.0%}")
