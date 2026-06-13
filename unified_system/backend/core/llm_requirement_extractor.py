"""
LLM-Powered Policy Parser & Requirement Extractor
Extracts structured requirements from unstructured policy documents.
Falls back to mock extraction when no API key is configured.
"""

import json
import os
import re
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


@dataclass
class ExtractedRequirement:
    req_id: str
    policy_id: str
    policy_name: str
    requirement_text: str
    structured_requirement: str
    frameworks: List[str]
    control_area: str
    burden_of_proof: List[str]
    evidence_types_expected: List[str]
    freshness_requirement: str
    responsible_team: str
    severity: str
    confidence_score: float
    extraction_rationale: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PolicyDocument:
    policy_id: str
    policy_name: str
    version: str
    extracted_text: str
    extracted_requirements: List[ExtractedRequirement] = field(default_factory=list)
    extraction_quality_score: float = 0.0
    frameworks_detected: List[str] = field(default_factory=list)
    extraction_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class LLMRequirementExtractor:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4", use_mock: bool = True):
        self.use_mock = use_mock
        self.model = model

        if not use_mock and OpenAI is not None:
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
                self.use_mock = False
            else:
                self.client = None
                self.use_mock = True
        else:
            self.client = None
            self.use_mock = True

    def extract_requirements(self, policy_doc: PolicyDocument) -> List[ExtractedRequirement]:
        if self.use_mock:
            return self._mock_extract(policy_doc)

        prompt = f"""You are a compliance expert. Extract structured requirements from this policy text.
For each requirement, return a JSON array with objects containing:
- requirement, structured_requirement, frameworks (list), control_area,
  burden_of_proof (list), evidence_types (list), freshness, severity, responsible_team, extraction_rationale

Policy Text:
{policy_doc.extracted_text[:4000]}

Respond ONLY with valid JSON array. No markdown."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a compliance extraction expert. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            text = response.choices[0].message.content.strip()
            text = re.sub(r"```json?\n?", "", text).rstrip("`")
            extracted_list = json.loads(text)
        except Exception as e:
            print(f"LLM extraction error: {e}, using mock")
            return self._mock_extract(policy_doc)

        requirements = []
        for idx, req in enumerate(extracted_list, 1):
            requirements.append(ExtractedRequirement(
                req_id=f"{policy_doc.policy_id}-REQ{idx:03d}",
                policy_id=policy_doc.policy_id,
                policy_name=policy_doc.policy_name,
                requirement_text=req.get("requirement", ""),
                structured_requirement=req.get("structured_requirement", ""),
                frameworks=req.get("frameworks", ["General"]),
                control_area=req.get("control_area", "General"),
                burden_of_proof=req.get("burden_of_proof", []),
                evidence_types_expected=req.get("evidence_types", ["Report"]),
                freshness_requirement=req.get("freshness", "monthly"),
                responsible_team=req.get("responsible_team", "Unknown"),
                severity=req.get("severity", "MEDIUM"),
                confidence_score=req.get("confidence", 0.8),
                extraction_rationale=req.get("extraction_rationale", "")
            ))
        return requirements

    def _mock_extract(self, policy_doc: PolicyDocument) -> List[ExtractedRequirement]:
        """Generate realistic mock requirements based on policy content."""
        text = policy_doc.policy_text if hasattr(policy_doc, 'policy_text') else policy_doc.extracted_text
        text_lower = text.lower()

        templates = []

        if "encrypt" in text_lower or "aes" in text_lower or "kms" in text_lower:
            templates += [
                ("All data at rest must be encrypted using AES-256 or stronger",
                 "Encryption at rest: AES-256 minimum", ["GDPR", "NIST", "PCI-DSS"], "Encryption",
                 ["AES-256 algorithm confirmed", "All data stores encrypted", "Key management documented"],
                 ["Encryption Certificate", "Configuration Snapshot"], "quarterly", "CRITICAL", "Security Team"),
                ("Encryption keys must be rotated at least annually",
                 "Key rotation: all keys rotated ≤ 365 days", ["NIST", "PCI-DSS", "ISO 27001"], "Key Management",
                 ["Rotation schedule documented", "Last rotation within threshold", "Rotation logs available"],
                 ["Key Rotation Log", "Audit Log"], "monthly", "HIGH", "Security Team"),
                ("Data in transit must use TLS 1.2 or higher",
                 "Transit encryption: TLS 1.2+", ["GDPR", "NIST", "PCI-DSS"], "Encryption",
                 ["TLS version verified", "Certificates valid", "No plaintext transmission"],
                 ["SSL Certificate", "Network Configuration", "Test Report"], "quarterly", "CRITICAL", "Network Security"),
            ]

        if "access" in text_lower or "authentication" in text_lower or "mfa" in text_lower:
            templates += [
                ("Administrative access requires multi-factor authentication",
                 "MFA required for all admin accounts", ["NIST", "CIS", "GDPR"], "Multi-Factor Auth",
                 ["MFA enabled on all admin accounts", "Users required to use MFA", "Backup auth documented"],
                 ["Configuration Snapshot", "Policy Document", "Test Report"], "quarterly", "CRITICAL", "IT Operations"),
                ("Access must follow principle of least privilege",
                 "Least privilege: users have minimum required access", ["NIST", "SOX", "ISO 27001"], "Access Control",
                 ["Access reviews completed quarterly", "No excess permissions found", "Role definitions documented"],
                 ["Access Report", "IAM Configuration", "Review Log"], "quarterly", "HIGH", "Access Control Board"),
            ]

        if "log" in text_lower or "audit" in text_lower or "monitor" in text_lower:
            templates += [
                ("All access to sensitive data must be logged",
                 "Audit logging: all access events captured with timestamp", ["GDPR", "NIST", "SOX"], "Audit Logging",
                 ["Logs capture all access attempts", "Logs include timestamp actor action", "Logs retained 90+ days"],
                 ["Audit Log", "Configuration Snapshot"], "continuous", "CRITICAL", "Security Operations"),
                ("Logs must be retained for minimum 90 days",
                 "Log retention: minimum 90 days", ["NIST", "PCI-DSS", "SOX"], "Audit Logging",
                 ["Retention policy set to 90+ days", "Storage capacity verified", "Archived logs accessible"],
                 ["Log Storage Configuration", "Retention Policy"], "monthly", "HIGH", "Log Management"),
            ]

        if not templates:
            templates = [
                ("Implement and maintain information security controls",
                 "Information security: documented controls implemented", ["ISO 27001", "NIST"], "General",
                 ["Controls documented", "Controls tested annually"], ["Policy Document", "Test Report"],
                 "annually", "MEDIUM", "Security Team"),
                ("Security incidents must be reported and investigated",
                 "Incident response: all incidents reported within 72 hours", ["GDPR", "NIST", "HIPAA"], "Incident Response",
                 ["IR plan documented", "Plan tested within 12 months", "Roles defined"],
                 ["Policy Document", "Test Report", "Training Record"], "annually", "HIGH", "Security Team"),
            ]

        requirements = []
        for idx, (req_text, structured, frameworks, area, burden, evidence_types, freshness, severity, team) in enumerate(templates, 1):
            requirements.append(ExtractedRequirement(
                req_id=f"{policy_doc.policy_id}-REQ{idx:03d}",
                policy_id=policy_doc.policy_id,
                policy_name=policy_doc.policy_name,
                requirement_text=req_text,
                structured_requirement=structured,
                frameworks=frameworks,
                control_area=area,
                burden_of_proof=burden,
                evidence_types_expected=evidence_types,
                freshness_requirement=freshness,
                responsible_team=team,
                severity=severity,
                confidence_score=0.85,
                extraction_rationale="Extracted from policy document"
            ))
        return requirements

    def extract_from_text(self, text: str, policy_id: str, policy_name: str) -> PolicyDocument:
        doc = PolicyDocument(
            policy_id=policy_id,
            policy_name=policy_name,
            version="1.0",
            extracted_text=text
        )
        doc.extracted_requirements = self.extract_requirements(doc)
        doc.extraction_quality_score = self._quality_score(doc)
        doc.frameworks_detected = list(set(fw for r in doc.extracted_requirements for fw in r.frameworks))
        return doc

    def _quality_score(self, doc: PolicyDocument) -> float:
        if not doc.extracted_requirements:
            return 0.0
        avg_conf = sum(r.confidence_score for r in doc.extracted_requirements) / len(doc.extracted_requirements)
        completeness = min(len(doc.extracted_requirements) / 5, 1.0)
        return round(avg_conf * 0.7 + completeness * 0.3, 3)
