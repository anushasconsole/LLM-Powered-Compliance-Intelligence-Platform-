"""
Enhanced Narrative Generator
Generates auditor-quality compliance narratives.
Uses LLM when available, falls back to template-based generation.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


@dataclass
class ComplianceNarrative:
    requirement_id: str
    requirement_text: str
    executive_summary: str
    detailed_narrative: str
    supporting_points: List[str] = field(default_factory=list)
    risk_assessment: str = ""
    recommendation: str = ""
    frameworks_addressed: List[str] = field(default_factory=list)
    confidence_level: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class EnhancedNarrativeGenerator:
    def __init__(self, api_key: Optional[str] = None, use_mock: bool = True):
        self.use_mock = use_mock
        self.client = None

        if not use_mock and OpenAI is not None:
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
                self.use_mock = False

    def generate_narrative(
        self,
        requirement_id: str,
        requirement_text: str,
        supporting_evidence: List[Dict],
        confidence_score: float = 0.8,
        frameworks: List[str] = None,
        responsible_team: str = "Unknown",
        contradicting_evidence: List[Dict] = None,
    ) -> ComplianceNarrative:
        frameworks = frameworks or []
        contradicting_evidence = contradicting_evidence or []

        if self.use_mock or self.client is None:
            return self._template_narrative(
                requirement_id, requirement_text, supporting_evidence,
                confidence_score, frameworks, responsible_team, contradicting_evidence
            )

        try:
            return self._llm_narrative(
                requirement_id, requirement_text, supporting_evidence,
                confidence_score, frameworks, responsible_team, contradicting_evidence
            )
        except Exception as e:
            print(f"LLM narrative error: {e}, using template")
            return self._template_narrative(
                requirement_id, requirement_text, supporting_evidence,
                confidence_score, frameworks, responsible_team, contradicting_evidence
            )

    def _llm_narrative(self, req_id, req_text, evidence, confidence, frameworks, team, contradicting):
        ev_count = len(evidence)
        con_count = len(contradicting)
        fw_str = ", ".join(frameworks) if frameworks else "General"

        prompt = f"""You are a senior compliance auditor writing an audit narrative.

Requirement: {req_text}
Frameworks: {fw_str}
Responsible Team: {team}
Evidence Count: {ev_count} supporting, {con_count} contradicting
Confidence Score: {confidence:.0%}

Write a professional compliance narrative with:
1. Executive Summary (1-2 sentences, start with PASS/FAIL/CONDITIONAL)
2. Detailed Assessment (2-3 paragraphs)
3. Risk Assessment (one paragraph)
4. Recommendation (one sentence)

Format as JSON:
{{"executive_summary": "...", "detailed_narrative": "...", "risk_assessment": "...", "recommendation": "..."}}"""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=600,
        )
        import json, re
        text = response.choices[0].message.content.strip()
        text = re.sub(r"```json?\n?", "", text).rstrip("`")
        data = json.loads(text)

        return ComplianceNarrative(
            requirement_id=req_id,
            requirement_text=req_text,
            executive_summary=data.get("executive_summary", ""),
            detailed_narrative=data.get("detailed_narrative", ""),
            supporting_points=[e.get('evidence_summary', '') for e in evidence[:3]],
            risk_assessment=data.get("risk_assessment", ""),
            recommendation=data.get("recommendation", ""),
            frameworks_addressed=frameworks,
            confidence_level=self._conf_level(confidence),
        )

    def _template_narrative(self, req_id, req_text, evidence, confidence, frameworks, team, contradicting):
        ev_count = len(evidence)
        con_count = len(contradicting)
        fw_str = ", ".join(frameworks) if frameworks else "General"

        if confidence >= 0.85 and con_count == 0:
            summary = f"PASS: Organization demonstrates compliance with '{req_text}'. {ev_count} artifact(s) support this assessment with {confidence:.0%} confidence."
            narrative = (
                f"The organization is required to: {req_text}. "
                f"This requirement maps to {fw_str} compliance frameworks and is owned by the {team}. "
                f"Evidence collection identified {ev_count} supporting artifact(s) demonstrating effective control implementation. "
                f"Based on evidence quality, recency, and source reliability, confidence in compliance is {confidence:.0%}. "
                f"The evidence chain is strong and well-corroborated from multiple sources."
            )
            risk = "LOW RISK: Strong evidence with high confidence. Control is effectively maintained."
            rec = "PASS FOR AUDIT: Evidence is sufficient. No remediation required."
        elif confidence >= 0.60:
            summary = f"CONDITIONAL: Partial compliance shown for '{req_text}'. {ev_count} artifact(s), confidence {confidence:.0%}."
            narrative = (
                f"The organization must satisfy: {req_text}. "
                f"This maps to {fw_str} frameworks, owned by {team}. "
                f"While {ev_count} supporting artifact(s) exist, the evidence could be strengthened. "
                + (f"Additionally, {con_count} contradicting item(s) were identified. " if con_count else "") +
                f"Confidence is {confidence:.0%}, indicating partial compliance with some gaps."
            )
            risk = "MEDIUM RISK: Some evidence present but gaps remain. Control may not be fully effective."
            rec = "CONDITIONAL PASS: Collect additional evidence and resolve identified gaps before audit."
        else:
            summary = f"AT RISK/FAIL: Insufficient compliance evidence for '{req_text}'. Confidence: {confidence:.0%}."
            narrative = (
                f"The organization must satisfy: {req_text}. "
                f"Only {ev_count} evidence artifact(s) were found, which is insufficient for audit. "
                + (f"{con_count} contradicting evidence item(s) further undermine compliance. " if con_count else "") +
                f"Confidence in compliance is only {confidence:.0%}, indicating significant risk. "
                f"Immediate remediation is required before this requirement can pass an audit."
            )
            risk = "HIGH RISK: Insufficient evidence. Control likely not implemented or documented."
            rec = "FAIL: Immediate remediation required. Implement control and collect strong evidence."

        return ComplianceNarrative(
            requirement_id=req_id,
            requirement_text=req_text,
            executive_summary=summary,
            detailed_narrative=narrative,
            supporting_points=[e.get('evidence_summary', e.get('description', '')) for e in evidence[:3]],
            risk_assessment=risk,
            recommendation=rec,
            frameworks_addressed=frameworks,
            confidence_level=self._conf_level(confidence),
        )

    def _conf_level(self, score: float) -> str:
        if score >= 0.90:
            return "VERY HIGH"
        elif score >= 0.75:
            return "HIGH"
        elif score >= 0.60:
            return "MEDIUM"
        elif score >= 0.40:
            return "LOW"
        return "VERY LOW"
