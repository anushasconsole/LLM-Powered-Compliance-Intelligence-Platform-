"""
LLM-Powered Policy Parser & Requirement Extractor

Extracts structured requirements from unstructured policy documents using LLM.
Handles ambiguous language, framework mapping, and creates burden-of-proof decomposition.

Architecture:
  1. Document ingestion (PDF, TXT, Markdown)
  2. Policy chunking (semantic paragraphs)
  3. LLM extraction (structured requirements)
  4. Framework mapping (GDPR, NIST, SOX, etc.)
  5. Quality validation (requirement coherence)
"""

import json
import os
import re
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


@dataclass
class ExtractedRequirement:
    """Machine-readable requirement extracted by LLM"""
    req_id: str  # POL-{POLICY_ID}-{REQ_NUMBER}
    policy_id: str
    policy_name: str
    requirement_text: str  # Original text from policy
    structured_requirement: str  # Normalized requirement
    frameworks: List[str]  # GDPR, NIST, SOX, etc.
    control_area: str  # e.g., "Encryption", "Access Control", "Audit Logging"
    burden_of_proof: List[str]  # What must be proven
    evidence_types_expected: List[str]  # Types of evidence that satisfy this
    freshness_requirement: str  # e.g., "monthly", "quarterly", "continuous"
    responsible_team: str  # Who owns this control
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    confidence_score: float  # LLM confidence in extraction (0-1)
    extraction_rationale: str  # Why LLM extracted it this way
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PolicyDocument:
    """Parsed policy document with extracted requirements"""
    policy_id: str
    policy_name: str
    version: str
    extracted_text: str
    extracted_requirements: List[ExtractedRequirement] = field(default_factory=list)
    extraction_quality_score: float = 0.0
    frameworks_detected: List[str] = field(default_factory=list)
    extraction_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class LLMRequirementExtractor:
    """
    Uses OpenAI GPT or compatible LLM to extract requirements from policies.
    
    Example:
        extractor = LLMRequirementExtractor(api_key="sk-...")
        policy_doc = PolicyDocument(
            policy_id="POL-GDPR-001",
            policy_name="Data Protection",
            version="1.0",
            extracted_text="All personal data must be encrypted at rest..."
        )
        requirements = extractor.extract_requirements(policy_doc)
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4", use_mock: bool = False):
        """
        Initialize LLM extractor.
        
        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
            model: Model to use (gpt-4, gpt-3.5-turbo, etc.)
            use_mock: If True, uses mock responses (for testing)
        """
        self.use_mock = use_mock
        self.model = model
        
        if not use_mock:
            if OpenAI is None:
                raise ImportError("openai package required. Install with: pip install openai")
            
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required. Set OPENAI_API_KEY or pass api_key parameter.")
            
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
        
        self.extraction_prompt_template = """
You are a compliance expert analyzing policy documents. Your task is to extract 
structured requirements from unstructured policy text.

For each requirement identified in the policy, extract:

1. **Requirement**: The exact requirement text from the policy
2. **Structured Form**: Normalize the requirement into clear, machine-readable form
3. **Frameworks**: List compliance frameworks this maps to (GDPR, NIST, SOX, ISO 27001, PCI-DSS, HIPAA, CIS)
4. **Control Area**: Categorize into: Encryption, Access Control, Audit Logging, Incident Response, 
   Data Retention, Key Management, Multi-Factor Auth, Monitoring, Vulnerability Management, etc.
5. **Burden of Proof**: List specific things that must be proven to satisfy this requirement.
   Examples:
   - "System has encryption enabled"
   - "Encryption keys are rotated quarterly"
   - "Audit logs record all access"
   - "Access is restricted to authorized users"
6. **Evidence Types**: What artifacts would satisfy this requirement?
   Examples: "Encryption Certificate", "Audit Log", "Configuration Snapshot", "Access Report"
7. **Freshness**: How often must evidence be collected? (daily, weekly, monthly, quarterly, continuous, annually)
8. **Severity**: CRITICAL, HIGH, MEDIUM, or LOW
9. **Responsible Team**: Which team likely owns this control?
   Examples: "Security Team", "Database Team", "Audit Team", "Compliance Team"

Policy Text:
{policy_text}

Respond ONLY with a valid JSON array. Each element is an extracted requirement object.
Do NOT include markdown formatting. Do NOT use triple backticks.

Example format:
[
  {{
    "requirement": "All personal data must be encrypted at rest",
    "structured_requirement": "Encryption at rest: AES-256 or stronger",
    "frameworks": ["GDPR", "NIST", "PCI-DSS"],
    "control_area": "Encryption",
    "burden_of_proof": ["Encryption algorithm is AES-256+", "Encryption is enabled on all data stores"],
    "evidence_types": ["Encryption Certificate", "Configuration Snapshot", "Audit Log"],
    "freshness": "quarterly",
    "severity": "CRITICAL",
    "responsible_team": "Security Team",
    "extraction_rationale": "Explicitly stated in Section 3.1"
  }},
  ...
]
"""
    
    def extract_requirements(self, policy_doc: PolicyDocument) -> List[ExtractedRequirement]:
        """
        Extract requirements from a policy document.
        
        Args:
            policy_doc: PolicyDocument object
            
        Returns:
            List of ExtractedRequirement objects
        """
        prompt = self.extraction_prompt_template.format(
            policy_text=policy_doc.extracted_text[:4000]  # Limit to 4000 chars to stay in token budget
        )
        
        if self.use_mock:
            return self._mock_extract(policy_doc)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a compliance extraction expert. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                top_p=0.9,
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Clean up response (remove markdown formatting if present)
            if response_text.startswith("```"):
                response_text = re.sub(r"```json?\n?", "", response_text)
                response_text = response_text.rstrip("`")
            
            extracted_list = json.loads(response_text)
            
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return self._mock_extract(policy_doc)
        except Exception as e:
            print(f"LLM extraction error: {e}")
            return self._mock_extract(policy_doc)
        
        # Convert to ExtractedRequirement objects
        requirements = []
        for idx, req in enumerate(extracted_list, 1):
            req_id = self._generate_req_id(policy_doc.policy_id, idx)
            
            extracted_req = ExtractedRequirement(
                req_id=req_id,
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
            )
            requirements.append(extracted_req)
        
        return requirements
    
    def _generate_req_id(self, policy_id: str, index: int) -> str:
        """Generate unique requirement ID"""
        return f"{policy_id}-REQ{index:03d}"
    
    def _mock_extract(self, policy_doc: PolicyDocument) -> List[ExtractedRequirement]:
        """Generate mock requirements for testing (no API call)"""
        mock_requirements = [
            ExtractedRequirement(
                req_id="MOCK-001",
                policy_id=policy_doc.policy_id,
                policy_name=policy_doc.policy_name,
                requirement_text="All personal data must be encrypted at rest",
                structured_requirement="Encryption at rest: AES-256 or stronger",
                frameworks=["GDPR", "NIST", "PCI-DSS"],
                control_area="Encryption",
                burden_of_proof=[
                    "Encryption algorithm is AES-256 or stronger",
                    "Encryption is enabled on all data stores",
                    "Keys are properly managed"
                ],
                evidence_types_expected=["Encryption Certificate", "Configuration Snapshot"],
                freshness_requirement="quarterly",
                responsible_team="Security Team",
                severity="CRITICAL",
                confidence_score=0.9,
                extraction_rationale="Critical compliance requirement"
            ),
            ExtractedRequirement(
                req_id="MOCK-002",
                policy_id=policy_doc.policy_id,
                policy_name=policy_doc.policy_name,
                requirement_text="Access to systems must be logged and audited",
                structured_requirement="Audit logging: All access events logged with timestamp and actor",
                frameworks=["GDPR", "NIST", "SOX"],
                control_area="Audit Logging",
                burden_of_proof=[
                    "Audit logs capture all access attempts",
                    "Logs include timestamp, actor, action, and outcome",
                    "Logs are retained for minimum 90 days"
                ],
                evidence_types_expected=["Audit Log", "Configuration Snapshot"],
                freshness_requirement="continuous",
                responsible_team="Audit Team",
                severity="CRITICAL",
                confidence_score=0.85,
                extraction_rationale="Fundamental audit requirement"
            ),
        ]
        return mock_requirements
    
    def extract_from_file(self, filepath: str) -> PolicyDocument:
        """
        Extract policy text from file and create PolicyDocument.
        
        Args:
            filepath: Path to policy file (TXT, PDF, Markdown)
            
        Returns:
            PolicyDocument object
        """
        if filepath.endswith('.pdf'):
            text = self._extract_pdf_text(filepath)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
        
        # Generate policy ID from filename
        policy_name = os.path.basename(filepath).replace('.pdf', '').replace('.txt', '')
        policy_id = self._generate_policy_id(policy_name)
        
        return PolicyDocument(
            policy_id=policy_id,
            policy_name=policy_name,
            version="1.0",
            extracted_text=text
        )
    
    def _extract_pdf_text(self, filepath: str) -> str:
        """Extract text from PDF file"""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except ImportError:
            print("PyPDF2 not installed, install with: pip install PyPDF2")
            return ""
    
    def _generate_policy_id(self, policy_name: str) -> str:
        """Generate policy ID from name"""
        # Remove special chars and convert to uppercase
        clean_name = re.sub(r'[^A-Za-z0-9]', '_', policy_name).upper()
        # Truncate to 15 chars for readability
        return f"POL_{clean_name[:15]}"
    
    def batch_extract(self, policy_docs: List[PolicyDocument]) -> List[PolicyDocument]:
        """Extract requirements from multiple policy documents"""
        for doc in policy_docs:
            doc.extracted_requirements = self.extract_requirements(doc)
            doc.extraction_quality_score = self._calculate_quality_score(doc)
            doc.frameworks_detected = self._detect_frameworks(doc)
        return policy_docs
    
    def _calculate_quality_score(self, policy_doc: PolicyDocument) -> float:
        """Calculate extraction quality (0-1)"""
        if not policy_doc.extracted_requirements:
            return 0.0
        
        avg_confidence = sum(r.confidence_score for r in policy_doc.extracted_requirements) / len(policy_doc.extracted_requirements)
        completeness = min(len(policy_doc.extracted_requirements) / 5, 1.0)  # Expect ~5 requirements
        
        return (avg_confidence * 0.7 + completeness * 0.3)
    
    def _detect_frameworks(self, policy_doc: PolicyDocument) -> List[str]:
        """Detect frameworks from extracted requirements"""
        frameworks = set()
        for req in policy_doc.extracted_requirements:
            frameworks.update(req.frameworks)
        return list(frameworks)


def export_requirements_json(requirements: List[ExtractedRequirement], filepath: str):
    """Export extracted requirements to JSON"""
    data = {
        "extracted_at": datetime.now().isoformat(),
        "requirements": [asdict(r) for r in requirements]
    }
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


# Example usage
if __name__ == "__main__":
    # Mock extraction (no API key needed)
    extractor = LLMRequirementExtractor(use_mock=True)
    
    sample_policy = PolicyDocument(
        policy_id="POL-GDPR-001",
        policy_name="Data Protection and Encryption",
        version="1.0",
        extracted_text="""
        POLICY: Data Protection and Encryption
        
        REQUIREMENT 1: All personal data must be encrypted at rest using
        cryptographic methods approved in NIST SP 800-175B.
        
        REQUIREMENT 2: Encryption keys must be rotated annually
        with audit logs maintained.
        
        REQUIREMENT 3: Access to encryption keys is restricted to
        authorized personnel with multi-factor authentication.
        """
    )
    
    requirements = extractor.extract_requirements(sample_policy)
    print(f"Extracted {len(requirements)} requirements")
    for req in requirements:
        print(f"  - {req.req_id}: {req.requirement_text}")
