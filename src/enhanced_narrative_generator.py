"""
Enhanced Narrative Generator - LLM-Powered Audit Narratives

Generates auditor-quality compliance narratives that explain:
- What the requirement is
- What evidence exists
- What gaps remain
- Risk assessment
- Recommendations

Powered by LLM for intelligent analysis and executive summaries.

Example:
    generator = EnhancedNarrativeGenerator(use_mock=False)
    
    narrative = generator.generate_narrative(
        requirement_id='REQ-001',
        requirement_text='Encryption keys must be rotated quarterly',
        supporting_evidence=[...],
        confidence_score=0.87,
        frameworks=['GDPR', 'NIST']
    )
    
    print(narrative.executive_summary)
    print(narrative.detailed_narrative)
    print(narrative.recommendation)
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


@dataclass
class ComplianceNarrative:
    """Generated compliance narrative"""
    requirement_id: str
    requirement_text: str
    
    executive_summary: str  # 1-2 sentences
    detailed_narrative: str  # Paragraph-length explanation
    
    supporting_points: List[str] = field(default_factory=list)
    risk_assessment: str = ""
    recommendation: str = ""
    
    frameworks_addressed: List[str] = field(default_factory=list)
    confidence_level: str = ""
    
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class EnhancedNarrativeGenerator:
    """
    LLM-powered narrative generation for compliance reports.
    
    Generates:
    - Executive summaries (for audit leadership)
    - Detailed narratives (for auditors)
    - Risk assessments
    - Recommendations
    
    Focuses on clear communication of compliance posture.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4", use_mock: bool = False):
        """
        Initialize narrative generator.
        
        Args:
            api_key: OpenAI API key
            model: Model to use
            use_mock: Use mock responses (for testing)
        """
        self.use_mock = use_mock
        self.model = model
        
        if not use_mock:
            if OpenAI is None:
                raise ImportError("openai package required")
            
            import os
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required")
            
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
    
    def generate_narrative(
        self,
        requirement_id: str,
        requirement_text: str,
        supporting_evidence: List[Dict],
        contradicting_evidence: List[Dict] = None,
        confidence_score: float = 0.8,
        frameworks: List[str] = None,
        responsible_team: str = "Unknown",
        evidence_quality_scores: Dict[str, float] = None
    ) -> ComplianceNarrative:
        """
        Generate compliance narrative for a requirement.
        
        Args:
            requirement_id: Requirement identifier
            requirement_text: Full requirement text
            supporting_evidence: List of evidence dicts
            contradicting_evidence: List of contradicting evidence
            confidence_score: Auditor confidence (0-1)
            frameworks: List of frameworks (GDPR, NIST, etc.)
            responsible_team: Team responsible for control
            evidence_quality_scores: Quality scores for evidence
            
        Returns:
            ComplianceNarrative object
        """
        contradicting_evidence = contradicting_evidence or []
        frameworks = frameworks or []
        evidence_quality_scores = evidence_quality_scores or {}
        
        # Generate using LLM
        if self.use_mock:
            return self._generate_mock_narrative(
                requirement_id, requirement_text, supporting_evidence,
                confidence_score, frameworks
            )
        
        try:
            executive_summary = self._generate_executive_summary(
                requirement_text, supporting_evidence, confidence_score
            )
            
            detailed_narrative = self._generate_detailed_narrative(
                requirement_text, supporting_evidence, contradicting_evidence,
                confidence_score, responsible_team
            )
            
            risk_assessment = self._generate_risk_assessment(
                requirement_text, confidence_score, contradicting_evidence
            )
            
            recommendation = self._generate_recommendation(
                confidence_score, supporting_evidence, contradicting_evidence
            )
            
            supporting_points = self._extract_supporting_points(supporting_evidence)
            
        except Exception as e:
            print(f"Narrative generation error: {e}")
            return self._generate_mock_narrative(
                requirement_id, requirement_text, supporting_evidence,
                confidence_score, frameworks
            )
        
        return ComplianceNarrative(
            requirement_id=requirement_id,
            requirement_text=requirement_text,
            executive_summary=executive_summary,
            detailed_narrative=detailed_narrative,
            supporting_points=supporting_points,
            risk_assessment=risk_assessment,
            recommendation=recommendation,
            frameworks_addressed=frameworks,
            confidence_level=self._confidence_to_level(confidence_score)
        )
    
    def _generate_executive_summary(
        self,
        requirement: str,
        evidence: List[Dict],
        confidence: float
    ) -> str:
        """Generate 1-2 sentence executive summary"""
        
        prompt = f"""
Generate a brief, 1-2 sentence executive summary for this requirement:

Requirement: {requirement}
Evidence Found: {len(evidence)} artifacts
Confidence: {confidence:.0%}

Summary should be suitable for C-suite/audit leadership. Be concise and clear.
Start with PASS/FAIL assessment.

Respond with ONLY the summary text, no preamble.
"""
        
        if self.use_mock:
            if confidence >= 0.8:
                return f"PASS: Organization demonstrates compliance with '{requirement}' through {len(evidence)} artifacts. Confidence: {confidence:.0%}"
            else:
                return f"CONDITIONAL: Partial compliance shown but gaps remain. Evidence: {len(evidence)} artifacts, Confidence: {confidence:.0%}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except:
            return self._generate_executive_summary(requirement, evidence, confidence) if not self.use_mock else ""
    
    def _generate_detailed_narrative(
        self,
        requirement: str,
        supporting: List[Dict],
        contradicting: List[Dict],
        confidence: float,
        team: str
    ) -> str:
        """Generate detailed paragraph-length narrative"""
        
        evidence_summary = self._summarize_evidence(supporting)
        
        prompt = f"""
Generate a detailed compliance narrative (2-3 paragraphs) for this requirement:

Requirement: {requirement}
Responsible Team: {team}
Supporting Evidence: {evidence_summary}
Contradicting Evidence: {len(contradicting)} items
Confidence: {confidence:.0%}

The narrative should:
1. Explain what the requirement means
2. Describe what evidence was found
3. Assess whether requirement is met
4. Note any concerns or gaps
5. Be suitable for audit documentation

Use clear, professional language suitable for auditors.
Respond with ONLY the narrative text.
"""
        
        if self.use_mock:
            narrative = f"The organization must satisfy '{requirement}'. "
            narrative += f"The {team} is responsible for implementing and maintaining this control. "
            
            if supporting:
                narrative += f"{len(supporting)} evidence artifact(s) were collected demonstrating compliance: {evidence_summary}. "
            
            if contradicting:
                narrative += f"However, {len(contradicting)} potential issues were identified that may undermine compliance. "
            
            narrative += f"Based on evidence quality and recency, confidence in compliance is {confidence:.0%}. "
            
            if confidence >= 0.8:
                narrative += "Overall assessment: COMPLIANT."
            elif confidence >= 0.6:
                narrative += "Overall assessment: CONDITIONAL."
            else:
                narrative += "Overall assessment: AT RISK or NON-COMPLIANT."
            
            return narrative
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=400
            )
            return response.choices[0].message.content.strip()
        except:
            return ""
    
    def _generate_risk_assessment(
        self,
        requirement: str,
        confidence: float,
        contradicting: List[Dict]
    ) -> str:
        """Generate risk assessment"""
        
        if confidence >= 0.8 and not contradicting:
            return "LOW RISK: Strong evidence of compliance. Control is effective and well-maintained."
        
        elif confidence >= 0.6:
            risk_factors = []
            if confidence < 0.75:
                risk_factors.append("Evidence is moderately fresh")
            if contradicting:
                risk_factors.append(f"{len(contradicting)} contradicting evidence items")
            
            factors_str = "; ".join(risk_factors)
            return f"MEDIUM RISK: Partial compliance demonstrated. Risk factors: {factors_str}"
        
        else:
            return f"HIGH RISK: Weak evidence of compliance. Control may not be effectively implemented. Confidence: {confidence:.0%}"
    
    def _generate_recommendation(
        self,
        confidence: float,
        supporting: List[Dict],
        contradicting: List[Dict]
    ) -> str:
        """Generate auditor recommendation"""
        
        if confidence >= 0.8 and not contradicting:
            return "PASS FOR AUDIT: Evidence is sufficient for audit purposes. No remediation required."
        
        elif confidence >= 0.6:
            recommendations = ["Collect additional evidence", "Address noted gaps", "Schedule follow-up review"]
            
            if len(supporting) < 2:
                recommendations.insert(0, "Increase evidence sources")
            
            if contradicting:
                recommendations.insert(0, "Resolve contradicting evidence items")
            
            return "CONDITIONAL PASS: " + "; ".join(recommendations)
        
        else:
            return "REMEDIATION REQUIRED: Insufficient evidence. Implement control and re-collect evidence before audit."
    
    def _summarize_evidence(self, evidence: List[Dict]) -> str:
        """Create brief evidence summary"""
        
        if not evidence:
            return "No evidence found"
        
        types = {}
        for ev in evidence:
            ev_type = ev.get('evidence_type', 'Unknown')
            types[ev_type] = types.get(ev_type, 0) + 1
        
        summary = ", ".join(f"{count} {ev_type}(s)" for ev_type, count in types.items())
        return f"{len(evidence)} artifact(s): {summary}"
    
    def _extract_supporting_points(self, evidence: List[Dict]) -> List[str]:
        """Extract key supporting points from evidence"""
        
        points = []
        
        # Get evidence descriptions
        for ev in evidence[:3]:  # Top 3
            description = ev.get('description', '')
            if description:
                points.append(description)
        
        return points
    
    def _confidence_to_level(self, confidence: float) -> str:
        """Convert confidence score to level"""
        
        if confidence >= 0.9:
            return "VERY HIGH"
        elif confidence >= 0.75:
            return "HIGH"
        elif confidence >= 0.6:
            return "MEDIUM"
        elif confidence >= 0.4:
            return "LOW"
        else:
            return "VERY LOW"
    
    def _generate_mock_narrative(
        self,
        req_id: str,
        req_text: str,
        evidence: List[Dict],
        confidence: float,
        frameworks: List[str]
    ) -> ComplianceNarrative:
        """Generate mock narrative for testing"""
        
        if confidence >= 0.8:
            summary = f"PASS: Organization demonstrates compliance with '{req_text}'. {len(evidence)} artifacts support this assessment."
            
            narrative = (
                f"The organization is required to: {req_text}. "
                f"This requirement maps to {', '.join(frameworks)} compliance frameworks. "
                f"Evidence collection identified {len(evidence)} supporting artifacts demonstrating "
                f"effective control implementation. "
                f"Based on evidence quality, recency, and source reliability, "
                f"confidence in compliance is {confidence:.0%}. "
                f"Overall assessment: COMPLIANT with strong supporting evidence."
            )
            
            risk = "LOW RISK: Strong evidence of compliance."
            rec = "PASS FOR AUDIT: Evidence is sufficient for audit purposes."
        
        else:
            summary = f"AT RISK: Partial compliance shown. {len(evidence)} artifacts found, confidence {confidence:.0%}."
            
            narrative = (
                f"The organization must satisfy: {req_text}. "
                f"Only {len(evidence)} evidence artifact(s) were found. "
                f"While some evidence of compliance exists, additional documentation would strengthen "
                f"the compliance argument. "
                f"Confidence in compliance is {confidence:.0%}, which indicates gaps that should be addressed. "
                f"Overall assessment: CONDITIONAL PASS with recommendations for improvement."
            )
            
            risk = f"MEDIUM RISK: {len(evidence)} evidence items found. Recommend additional corroboration."
            rec = f"CONDITIONAL: Collect additional evidence and schedule follow-up review."
        
        points = [
            ev.get('description', '') for ev in evidence[:3]
        ]
        
        return ComplianceNarrative(
            requirement_id=req_id,
            requirement_text=req_text,
            executive_summary=summary,
            detailed_narrative=narrative,
            supporting_points=[p for p in points if p],
            risk_assessment=risk,
            recommendation=rec,
            frameworks_addressed=frameworks,
            confidence_level=self._confidence_to_level(confidence)
        )
    
    def generate_executive_report(
        self,
        all_narratives: List[ComplianceNarrative],
        report_title: str = "Compliance Executive Summary"
    ) -> str:
        """Generate executive summary of all compliance narratives"""
        
        total = len(all_narratives)
        compliant = sum(1 for n in all_narratives if "PASS" in n.executive_summary.upper())
        at_risk = sum(1 for n in all_narratives if "AT RISK" in n.executive_summary.upper() or "CONDITIONAL" in n.executive_summary.upper())
        non_compliant = total - compliant - at_risk
        
        avg_confidence = sum(
            float(''.join(filter(str.isdigit, n.confidence_level)))
            for n in all_narratives
        ) / total if total > 0 else 0
        
        report = f"""
{report_title}
{'='*60}

COMPLIANCE SUMMARY
==================
Total Requirements Assessed: {total}
Compliant: {compliant} ({compliant/total*100:.0f}%)
Conditional/At Risk: {at_risk} ({at_risk/total*100:.0f}%)
Non-Compliant: {non_compliant} ({non_compliant/total*100:.0f}%)

FRAMEWORKS COVERED
==================
"""
        
        frameworks = set()
        for narrative in all_narratives:
            frameworks.update(narrative.frameworks_addressed)
        
        for framework in sorted(frameworks):
            report += f"- {framework}\n"
        
        report += f"\nOVERALL CONFIDENCE: {avg_confidence:.0f}%\n"
        
        if compliant >= total * 0.8:
            report += "STATUS: ✅ READY FOR AUDIT\n"
        elif compliant >= total * 0.6:
            report += "STATUS: ⚠️ CONDITIONAL - Address gaps before audit\n"
        else:
            report += "STATUS: ❌ NOT READY - Significant remediation required\n"
        
        return report


# Example usage
if __name__ == "__main__":
    generator = EnhancedNarrativeGenerator(use_mock=True)
    
    narrative = generator.generate_narrative(
        requirement_id='REQ-001',
        requirement_text='Encryption keys must be rotated quarterly',
        supporting_evidence=[
            {
                'evidence_id': 'EV-001',
                'evidence_type': 'Encryption_Cert',
                'description': 'AWS KMS rotation policy configured'
            },
            {
                'evidence_id': 'EV-002',
                'evidence_type': 'Audit_Log',
                'description': 'Key rotation events logged'
            }
        ],
        confidence_score=0.87,
        frameworks=['GDPR', 'NIST'],
        responsible_team='Security Team'
    )
    
    print("EXECUTIVE SUMMARY")
    print(narrative.executive_summary)
    print("\nDETAILED NARRATIVE")
    print(narrative.detailed_narrative)
    print(f"\nConfidence Level: {narrative.confidence_level}")
    print(f"\nRisk Assessment: {narrative.risk_assessment}")
    print(f"\nRecommendation: {narrative.recommendation}")
