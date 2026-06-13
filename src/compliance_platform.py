"""
Compliance Intelligence Platform - Integration Layer

Orchestrates all Option A components:
- LLM Policy Extraction
- Knowledge Graph
- Semantic Evidence Mapping
- Auditor Confidence Engine
- Compliance Copilot
- Enhanced Narrative Generation

This is the main entry point for the LLM-powered compliance platform.

Example:
    platform = ComplianceIntelligencePlatform()
    
    # Load policies
    policies = platform.load_policies('policies/')
    
    # Extract requirements using LLM
    requirements = platform.extract_requirements(policies)
    
    # Build knowledge graph
    kg = platform.build_knowledge_graph(requirements, evidence)
    
    # Generate narratives and reports
    report = platform.generate_audit_report()
"""

from typing import List, Dict, Optional
from datetime import datetime
import json
import os

from llm_requirement_extractor import LLMRequirementExtractor, PolicyDocument, ExtractedRequirement
from knowledge_graph import KnowledgeGraph
from semantic_mapper import SemanticEvidenceMapper
from confidence_engine import AuditorConfidenceEngine, ComplianceConfidence
from compliance_copilot import ComplianceCopilot
from enhanced_narrative_generator import EnhancedNarrativeGenerator, ComplianceNarrative


class ComplianceIntelligencePlatform:
    """
    Enterprise-grade LLM-powered compliance intelligence platform.
    
    Capabilities:
    1. Extract requirements from unstructured policies using LLM
    2. Build knowledge graph of policy → control → evidence → framework
    3. Semantically match evidence to requirements
    4. Calculate auditor confidence scores
    5. Generate audit narratives
    6. Enable auditor queries via compliance copilot
    7. Track compliance metrics and trends
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        use_mock: bool = False,
        config: Optional[Dict] = None
    ):
        """
        Initialize compliance platform.
        
        Args:
            openai_api_key: OpenAI API key
            use_mock: Use mock models (no API calls)
            config: Configuration dict
        """
        self.config = config or {}
        self.use_mock = use_mock
        
        # Initialize components
        self.extractor = LLMRequirementExtractor(
            api_key=openai_api_key,
            use_mock=use_mock
        )
        
        self.knowledge_graph = KnowledgeGraph()
        
        self.semantic_mapper = SemanticEvidenceMapper(use_mock=use_mock)
        
        self.confidence_engine = AuditorConfidenceEngine()
        
        self.narrative_generator = EnhancedNarrativeGenerator(
            api_key=openai_api_key,
            use_mock=use_mock
        )
        
        self.copilot = ComplianceCopilot(
            self.knowledge_graph,
            self.semantic_mapper,
            self.confidence_engine
        )
        
        # Storage
        self.policies: Dict[str, PolicyDocument] = {}
        self.extracted_requirements: List[ExtractedRequirement] = []
        self.evidence_artifacts: List[Dict] = []
        self.compliance_assessments: Dict[str, ComplianceConfidence] = {}
        self.narratives: Dict[str, ComplianceNarrative] = {}
    
    def load_policies_from_files(self, directory: str) -> List[PolicyDocument]:
        """Load policy documents from directory"""
        
        policies = []
        
        if not os.path.exists(directory):
            print(f"Warning: Directory {directory} not found")
            return policies
        
        for filename in os.listdir(directory):
            if filename.endswith(('.txt', '.pdf', '.md')):
                filepath = os.path.join(directory, filename)
                
                try:
                    policy_doc = self.extractor.extract_from_file(filepath)
                    policies.append(policy_doc)
                    self.policies[policy_doc.policy_id] = policy_doc
                    print(f"Loaded policy: {policy_doc.policy_name}")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        return policies
    
    def extract_requirements_from_policies(
        self,
        policies: List[PolicyDocument]
    ) -> List[ExtractedRequirement]:
        """Extract requirements from policies using LLM"""
        
        all_requirements = []
        
        for policy in policies:
            print(f"Extracting requirements from {policy.policy_name}...")
            
            requirements = self.extractor.extract_requirements(policy)
            all_requirements.extend(requirements)
            
            # Update policy document
            policy.extracted_requirements = requirements
            policy.extraction_quality_score = self.extractor._calculate_quality_score(policy)
        
        self.extracted_requirements = all_requirements
        print(f"Extracted {len(all_requirements)} total requirements")
        
        return all_requirements
    
    def load_evidence(self, evidence_list: List[Dict]):
        """Load evidence artifacts"""
        
        self.evidence_artifacts = evidence_list
        print(f"Loaded {len(evidence_list)} evidence artifacts")
    
    def build_knowledge_graph(self):
        """Build knowledge graph from requirements and evidence"""
        
        print("Building knowledge graph...")
        
        # Add framework nodes
        frameworks = {
            'FW-GDPR': 'GDPR',
            'FW-NIST': 'NIST',
            'FW-SOX': 'SOX',
            'FW-ISO27001': 'ISO 27001',
            'FW-PCIDD': 'PCI-DSS',
            'FW-HIPAA': 'HIPAA'
        }
        
        for fw_id, fw_name in frameworks.items():
            self.knowledge_graph.add_framework(fw_id, fw_name)
        
        # Add team nodes
        teams = {
            'TEAM-SEC': 'Security Team',
            'TEAM-AUDIT': 'Audit Team',
            'TEAM-DB': 'Database Team',
            'TEAM-NET': 'Network Team'
        }
        
        for team_id, team_name in teams.items():
            self.knowledge_graph.add_team(team_id, team_name)
        
        # Add control area nodes
        control_areas = {
            'CTRL-ENC': 'Encryption',
            'CTRL-AC': 'Access Control',
            'CTRL-AUDIT': 'Audit Logging',
            'CTRL-IR': 'Incident Response',
            'CTRL-KM': 'Key Management',
            'CTRL-MFA': 'Multi-Factor Auth'
        }
        
        for area_id, area_name in control_areas.items():
            self.knowledge_graph.add_control_area(area_id, area_name)
        
        # Add policy and requirement nodes
        for req in self.extracted_requirements:
            # Add policy node if not exists
            if not self.knowledge_graph.graph.has_node(req.policy_id):
                self.knowledge_graph.add_policy(
                    req.policy_id,
                    req.policy_name
                )
            
            # Add requirement node
            self.knowledge_graph.add_requirement(
                req.req_id,
                req.requirement_text,
                req.policy_id,
                severity=req.severity,
                freshness=req.freshness_requirement,
                burden_of_proof=req.burden_of_proof
            )
            
            # Link to frameworks
            for fw in req.frameworks:
                fw_id = f"FW-{fw.upper().replace(' ', '')}"
                self.knowledge_graph.link_requirement_to_framework(req.req_id, fw_id)
            
            # Link to team (simple mapping)
            team_id = 'TEAM-SEC'  # Default to security team
            if 'audit' in req.control_area.lower():
                team_id = 'TEAM-AUDIT'
            self.knowledge_graph.link_requirement_to_team(req.req_id, team_id)
            
            # Link to control area
            ctrl_key = self._map_control_area(req.control_area)
            if ctrl_key:
                self.knowledge_graph.link_requirement_to_control_area(req.req_id, ctrl_key)
        
        # Add evidence nodes and link to requirements
        print(f"Linking {len(self.evidence_artifacts)} evidence artifacts...")
        
        for evidence in self.evidence_artifacts:
            evidence_id = evidence.get('evidence_id', '')
            
            if not evidence_id:
                continue
            
            self.knowledge_graph.add_evidence(
                evidence_id,
                evidence.get('evidence_type', 'Report'),
                evidence.get('description', ''),
                evidence.get('collection_date', ''),
                evidence.get('freshness_days', 30),
                confidence=evidence.get('confidence_score', 0.5)
            )
        
        # Semantically link evidence to requirements
        print("Performing semantic matching...")
        for req in self.extracted_requirements:
            matches = self.semantic_mapper.search_evidence_for_requirement(
                req.req_id,
                req.requirement_text,
                self.evidence_artifacts,
                threshold=0.35,
                top_k=5
            )
            
            for match in matches:
                evidence_id = match.evidence_id
                strength = match.similarity_score
                self.knowledge_graph.link_evidence_supports(evidence_id, req.req_id, strength=strength)
        
        print("Knowledge graph built successfully")
        self.knowledge_graph.print_summary()
        
        return self.knowledge_graph
    
    def assess_compliance(self):
        """Calculate compliance confidence for all requirements"""
        
        print("Assessing compliance...")
        
        for req in self.extracted_requirements:
            # Get evidence for this requirement
            evidence_data = self.knowledge_graph.get_evidence_for_requirement(req.req_id)
            
            supporting = [
                e for e in evidence_data if e.get('relation') == 'SUPPORTS'
            ]
            
            contradicting = [
                e for e in evidence_data if e.get('relation') == 'CONTRADICTS'
            ]
            
            # Convert to format expected by confidence engine
            supporting_for_engine = [
                {
                    'evidence_id': e['evidence_id'],
                    'evidence_type': e['attributes'].get('attributes', {}).get('evidence_type', ''),
                    'freshness_days': e['attributes'].get('attributes', {}).get('freshness_days', 30),
                    'confidence_score': e.get('strength', 0.5),
                    'review_status': 'Approved'
                }
                for e in supporting
            ]
            
            # Calculate confidence
            confidence = self.confidence_engine.calculate_confidence(
                req.req_id,
                req.requirement_text,
                supporting_for_engine,
                [],  # contradicting
                requirement_severity=req.severity
            )
            
            self.compliance_assessments[req.req_id] = confidence
        
        print(f"Assessed {len(self.compliance_assessments)} requirements")
        
        return self.compliance_assessments
    
    def generate_narratives(self):
        """Generate audit narratives for all requirements"""
        
        print("Generating narratives...")
        
        for req in self.extracted_requirements:
            if req.req_id not in self.compliance_assessments:
                continue
            
            assessment = self.compliance_assessments[req.req_id]
            
            # Get evidence
            evidence_data = self.knowledge_graph.get_evidence_for_requirement(req.req_id)
            supporting = [
                {
                    'evidence_id': e['evidence_id'],
                    'description': e['attributes'].get('name', ''),
                    'evidence_type': e['attributes'].get('attributes', {}).get('evidence_type', ''),
                    'freshness_days': e['attributes'].get('attributes', {}).get('freshness_days', 30)
                }
                for e in evidence_data if e.get('relation') == 'SUPPORTS'
            ]
            
            narrative = self.narrative_generator.generate_narrative(
                req.req_id,
                req.requirement_text,
                supporting,
                confidence_score=assessment.confidence_score,
                frameworks=req.frameworks,
                responsible_team=req.responsible_team
            )
            
            self.narratives[req.req_id] = narrative
        
        print(f"Generated {len(self.narratives)} narratives")
        
        return self.narratives
    
    def query_compliance(self, query: str) -> Dict:
        """Query compliance status using copilot"""
        
        response = self.copilot.query(query)
        
        return {
            'query': query,
            'answer': response.answer,
            'summary': response.answer_summary,
            'confidence': response.confidence,
            'type': str(response.query_type)
        }
    
    def generate_audit_report(self) -> Dict:
        """Generate comprehensive audit report"""
        
        total_requirements = len(self.extracted_requirements)
        compliant = sum(
            1 for assessment in self.compliance_assessments.values()
            if assessment.compliance_status.value == 'COMPLIANT'
        )
        conditional = sum(
            1 for assessment in self.compliance_assessments.values()
            if assessment.compliance_status.value == 'CONDITIONAL'
        )
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'executive_summary': {
                'total_requirements': total_requirements,
                'compliant': compliant,
                'conditional': conditional,
                'non_compliant': total_requirements - compliant - conditional,
                'compliance_percentage': (compliant / total_requirements * 100) if total_requirements > 0 else 0,
                'audit_ready': compliant >= total_requirements * 0.8
            },
            'frameworks': self._get_framework_summary(),
            'requirements': [],
            'recommendations': self._generate_recommendations()
        }
        
        # Add detailed requirement assessments
        for req in self.extracted_requirements:
            if req.req_id in self.narratives:
                narrative = self.narratives[req.req_id]
                assessment = self.compliance_assessments.get(req.req_id)
                
                report['requirements'].append({
                    'requirement_id': req.req_id,
                    'requirement_text': req.requirement_text,
                    'status': assessment.compliance_status.value if assessment else 'UNKNOWN',
                    'confidence': assessment.confidence_score if assessment else 0.0,
                    'summary': narrative.executive_summary,
                    'narrative': narrative.detailed_narrative,
                    'risk': narrative.risk_assessment,
                    'recommendation': narrative.recommendation,
                    'frameworks': req.frameworks
                })
        
        return report
    
    def _map_control_area(self, control_area: str) -> Optional[str]:
        """Map control area name to knowledge graph key"""
        
        mapping = {
            'Encryption': 'CTRL-ENC',
            'Access Control': 'CTRL-AC',
            'Audit Logging': 'CTRL-AUDIT',
            'Incident Response': 'CTRL-IR',
            'Key Management': 'CTRL-KM',
            'Multi-Factor Auth': 'CTRL-MFA'
        }
        
        for key, value in mapping.items():
            if key.lower() in control_area.lower() or control_area.lower() in key.lower():
                return value
        
        return None
    
    def _get_framework_summary(self) -> Dict[str, Dict]:
        """Get compliance summary by framework"""
        
        summary = {}
        
        frameworks = ['GDPR', 'NIST', 'SOX', 'ISO 27001', 'PCI-DSS', 'HIPAA']
        
        for fw in frameworks:
            coverage = self.knowledge_graph.get_framework_coverage(f'FW-{fw.upper().replace(" ", "")}')
            summary[fw] = {
                'total_requirements': coverage.get('total_requirements', 0),
                'with_evidence': coverage.get('requirements_with_evidence', 0),
                'coverage_percent': coverage.get('coverage_percent', 0)
            }
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate high-level recommendations"""
        
        recommendations = []
        
        # Check for missing evidence
        lacking = self.knowledge_graph.get_requirements_needing_evidence()
        if lacking:
            recommendations.append(f"Collect evidence for {len(lacking)} requirements without documentation")
        
        # Check for stale evidence
        stale = self.knowledge_graph.get_stale_evidence(threshold_days=30)
        if stale:
            recommendations.append(f"Refresh {len(stale)} evidence artifacts older than 30 days")
        
        # Check for low confidence
        low_confidence = [
            a for a in self.compliance_assessments.values()
            if a.confidence_score < 0.6
        ]
        if low_confidence:
            recommendations.append(f"Strengthen evidence for {len(low_confidence)} requirements with low confidence")
        
        return recommendations
    
    def export_report_json(self, report: Dict, filepath: str):
        """Export report to JSON"""
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Report exported to {filepath}")
    
    def print_report_summary(self, report: Dict):
        """Print report summary to console"""
        
        print("\n" + "="*70)
        print("COMPLIANCE AUDIT REPORT")
        print("="*70)
        
        summary = report['executive_summary']
        print(f"\nExecutive Summary:")
        print(f"  Total Requirements: {summary['total_requirements']}")
        print(f"  Compliant: {summary['compliant']} ({summary['compliance_percentage']:.0f}%)")
        print(f"  Conditional: {summary['conditional']}")
        print(f"  Non-Compliant: {summary['non_compliant']}")
        print(f"  Audit Ready: {'✅ YES' if summary['audit_ready'] else '❌ NO'}")
        
        print(f"\nFramework Coverage:")
        for fw, stats in report['frameworks'].items():
            pct = stats['coverage_percent']
            print(f"  {fw}: {stats['with_evidence']}/{stats['total_requirements']} ({pct:.0f}%)")
        
        print(f"\nTop Recommendations:")
        for i, rec in enumerate(report['recommendations'][:3], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "="*70)


# Example usage
if __name__ == "__main__":
    print("Initializing Compliance Intelligence Platform...")
    
    platform = ComplianceIntelligencePlatform(use_mock=True)
    
    # Create mock policy and evidence
    mock_policy = PolicyDocument(
        policy_id="POL-GDPR-001",
        policy_name="GDPR Data Protection",
        version="1.0",
        extracted_text="""
        Requirement 1: All personal data must be encrypted at rest
        Requirement 2: Keys must be rotated quarterly
        """
    )
    
    mock_evidence = [
        {
            'evidence_id': 'EV-001',
            'evidence_type': 'Encryption_Cert',
            'description': 'AWS KMS encryption enabled',
            'collection_date': '2026-04-15',
            'freshness_days': 5,
            'confidence_score': 0.95
        }
    ]
    
    # Process
    platform.policies['POL-GDPR-001'] = mock_policy
    platform.extracted_requirements = platform.extractor.extract_requirements(mock_policy)
    platform.evidence_artifacts = mock_evidence
    
    kg = platform.build_knowledge_graph()
    assessments = platform.assess_compliance()
    narratives = platform.generate_narratives()
    
    report = platform.generate_audit_report()
    platform.print_report_summary(report)
