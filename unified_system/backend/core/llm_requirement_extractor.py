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
        """
        Generate requirements from policy content.

        Primary strategy: parse structured REQUIREMENT N: lines directly from the text.
        Fallback: keyword-template approach when no structured lines are found.
        """
        text = policy_doc.extracted_text
        text_lower = text.lower()

        # ── Strategy 1: parse structured "REQUIREMENT N: ..." lines ──────────
        structured = self._parse_structured_requirements(text, policy_doc)
        if len(structured) >= 2:
            return structured

        # ── Strategy 2: keyword-template fallback ─────────────────────────────
        return self._keyword_templates(text, text_lower, policy_doc)

    def _parse_structured_requirements(
        self, text: str, policy_doc: PolicyDocument
    ) -> List[ExtractedRequirement]:
        """
        Parse blocks like:
            REQUIREMENT 1: <text>
            - Responsible: ...
            - Compliance Mapping: GDPR Article 32, NIST SC-7
        """
        import re

        # Split policy text into per-policy blocks
        policy_blocks = re.split(r'\n---\n', text.strip())

        requirements = []
        req_counter = 0

        for block in policy_blocks:
            # Extract policy metadata
            pid_match  = re.search(r'POLICY_ID\s*:\s*(\S+)', block, re.IGNORECASE)
            name_match = re.search(r'^POLICY\s*:\s*(.+)', block, re.IGNORECASE | re.MULTILINE)
            policy_id  = pid_match.group(1).strip()  if pid_match  else policy_doc.policy_id
            policy_nm  = name_match.group(1).strip() if name_match else policy_doc.policy_name

            # Find all REQUIREMENT lines
            req_matches = re.finditer(
                r'REQUIREMENT\s+\d+\s*:\s*(.+?)(?=\nREQUIREMENT\s+\d|\Z)',
                block, re.DOTALL | re.IGNORECASE
            )

            for rm in req_matches:
                req_counter += 1
                req_block = rm.group(0)
                req_text  = rm.group(1).split('\n')[0].strip()

                # Extract compliance mapping
                cm_match = re.search(
                    r'Compliance Mapping\s*:\s*(.+)', req_block, re.IGNORECASE
                )
                frameworks: List[str] = []
                if cm_match:
                    cm_raw = cm_match.group(1)
                    fw_map = {
                        'gdpr': 'GDPR', 'nist': 'NIST', 'sox': 'SOX',
                        'pci': 'PCI-DSS', 'hipaa': 'HIPAA',
                        'iso 27001': 'ISO27001', 'iso27001': 'ISO27001',
                        'cis': 'CIS',
                    }
                    for key, value in fw_map.items():
                        if key in cm_raw.lower() and value not in frameworks:
                            frameworks.append(value)
                if not frameworks:
                    frameworks = ['General']

                # Extract responsible team
                resp_match = re.search(
                    r'Responsible\s*:\s*(.+)', req_block, re.IGNORECASE
                )
                team = resp_match.group(1).strip() if resp_match else 'Security Team'

                # Extract frequency
                freq_match = re.search(
                    r'Audit Frequency\s*:\s*(.+)', req_block, re.IGNORECASE
                )
                freq = freq_match.group(1).strip().lower() if freq_match else 'monthly'

                # Derive control area and severity from content
                tl = req_text.lower()
                if any(w in tl for w in ['encrypt', 'aes', 'tls', 'kms', 'crypto']):
                    area, severity = 'Encryption', 'CRITICAL'
                elif any(w in tl for w in ['access', 'auth', 'mfa', 'privilege', 'iam']):
                    area, severity = 'Access Control', 'CRITICAL'
                elif any(w in tl for w in ['log', 'audit', 'monitor', 'retain']):
                    area, severity = 'Audit Logging', 'HIGH'
                elif any(w in tl for w in ['incident', 'breach', 'notification', 'response']):
                    area, severity = 'Incident Response', 'HIGH'
                elif any(w in tl for w in ['change', 'segregat', 'financial', 'sox']):
                    area, severity = 'Financial Controls', 'HIGH'
                elif any(w in tl for w in ['backup', 'recovery', 'continuity']):
                    area, severity = 'Business Continuity', 'MEDIUM'
                elif any(w in tl for w in ['asset', 'classif', 'inventory']):
                    area, severity = 'Asset Management', 'MEDIUM'
                else:
                    area, severity = 'General', 'MEDIUM'

                requirements.append(ExtractedRequirement(
                    req_id=f"{policy_id}-REQ{req_counter:03d}",
                    policy_id=policy_id,
                    policy_name=policy_nm,
                    requirement_text=req_text,
                    structured_requirement=req_text,
                    frameworks=frameworks,
                    control_area=area,
                    burden_of_proof=[],
                    evidence_types_expected=['Report', 'Configuration Snapshot'],
                    freshness_requirement=freq,
                    responsible_team=team,
                    severity=severity,
                    confidence_score=0.85,
                    extraction_rationale='Parsed from structured REQUIREMENT block',
                ))

        return requirements

    def _keyword_templates(
        self, text: str, text_lower: str, policy_doc: PolicyDocument
    ) -> List[ExtractedRequirement]:
        """Keyword-template fallback for unstructured policy text."""
        templates = []

        if "encrypt" in text_lower or "aes" in text_lower or "kms" in text_lower:
            templates += [
                ("All data at rest must be encrypted using AES-256 or stronger",
                 "Encryption at rest: AES-256 minimum", ["GDPR", "NIST", "PCI-DSS"],
                 "Encryption", ["Encryption Certificate", "Configuration Snapshot"],
                 "quarterly", "CRITICAL", "Security Team"),
                ("Encryption keys must be rotated at least annually",
                 "Key rotation: all keys rotated ≤ 365 days", ["NIST", "PCI-DSS", "ISO27001"],
                 "Key Management", ["Key Rotation Log", "Audit Log"],
                 "monthly", "HIGH", "Security Team"),
                ("Data in transit must use TLS 1.2 or higher",
                 "Transit encryption: TLS 1.2+", ["GDPR", "NIST", "PCI-DSS"],
                 "Encryption", ["SSL Certificate", "Network Configuration"],
                 "quarterly", "CRITICAL", "Network Security"),
            ]

        if "access" in text_lower or "authentication" in text_lower or "mfa" in text_lower:
            templates += [
                ("Administrative access requires multi-factor authentication",
                 "MFA required for all admin accounts", ["NIST", "CIS", "GDPR"],
                 "Multi-Factor Auth", ["Configuration Snapshot", "Policy Document"],
                 "quarterly", "CRITICAL", "IT Operations"),
                ("Access must follow principle of least privilege",
                 "Least privilege: users have minimum required access",
                 ["NIST", "SOX", "ISO27001"], "Access Control",
                 ["Access Report", "IAM Configuration"],
                 "quarterly", "HIGH", "Access Control Board"),
            ]

        if "log" in text_lower or "audit" in text_lower or "monitor" in text_lower:
            templates += [
                ("All access to sensitive data must be logged",
                 "Audit logging: all access events captured",
                 ["GDPR", "NIST", "SOX"], "Audit Logging",
                 ["Audit Log", "Configuration Snapshot"],
                 "continuous", "CRITICAL", "Security Operations"),
                ("Logs must be retained for minimum 90 days",
                 "Log retention: minimum 90 days", ["NIST", "PCI-DSS", "SOX"],
                 "Audit Logging", ["Log Storage Configuration"],
                 "monthly", "HIGH", "Log Management"),
            ]

        if "incident" in text_lower or "breach" in text_lower or "hipaa" in text_lower:
            templates += [
                ("Security incidents must be reported and investigated",
                 "Incident response: all incidents reported within 72 hours",
                 ["GDPR", "NIST", "HIPAA"], "Incident Response",
                 ["Policy Document", "Test Report"],
                 "annually", "HIGH", "Security Team"),
            ]

        if "financial" in text_lower or "sox" in text_lower or "segregat" in text_lower:
            templates += [
                ("Financial system access must be controlled and audited",
                 "SOX 404: financial system access documented",
                 ["SOX"], "Financial Controls",
                 ["Access Control Report", "SOX 404 Documentation"],
                 "quarterly", "HIGH", "Financial Controls Team"),
            ]

        if not templates:
            templates = [
                ("Implement and maintain information security controls",
                 "Information security: documented controls implemented",
                 ["ISO27001", "NIST"], "General",
                 ["Policy Document", "Test Report"],
                 "annually", "MEDIUM", "Security Team"),
                ("Security incidents must be reported and investigated",
                 "Incident response: all incidents reported within 72 hours",
                 ["GDPR", "NIST", "HIPAA"], "Incident Response",
                 ["Policy Document", "Test Report"],
                 "annually", "HIGH", "Security Team"),
            ]

        requirements = []
        for idx, (req_text, structured, frameworks, area, evidence_types,
                   freshness, severity, team) in enumerate(templates, 1):
            requirements.append(ExtractedRequirement(
                req_id=f"{policy_doc.policy_id}-REQ{idx:03d}",
                policy_id=policy_doc.policy_id,
                policy_name=policy_doc.policy_name,
                requirement_text=req_text,
                structured_requirement=structured,
                frameworks=frameworks,
                control_area=area,
                burden_of_proof=[],
                evidence_types_expected=evidence_types,
                freshness_requirement=freshness,
                responsible_team=team,
                severity=severity,
                confidence_score=0.85,
                extraction_rationale='Extracted from policy document (keyword match)',
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
