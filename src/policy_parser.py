"""
Policy Parser - Extracts structured requirements from policy documents
Uses rule-based NLP to decompose policies into machine-readable claim trees.
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional

FRAMEWORK_KEYWORDS = {
    "GDPR": ["gdpr", "article 32", "article 33", "article 25", "personal data", "data protection"],
    "NIST": ["nist", "sc-7", "ac-2", "ac-3", "au-2", "au-4", "au-5", "ia-2", "cp-2", "nist sp"],
    "ISO27001": ["iso 27001", "iso27001", "a.10.1", "a.12", "a.13", "a.6", "iso 27001"],
    "PCI-DSS": ["pci-dss", "pci dss", "pci", "3.4"],
    "SOX": ["sox", "sox 302", "sox 404", "financial controls", "internal controls"],
    "HIPAA": ["hipaa", "phi", "protected health"],
    "CIS": ["cis", "cis 4.1", "cis 5.3"],
}

# Override frameworks per requirement ID (based on compliance_mapping in policy text)
REQUIREMENT_FRAMEWORK_OVERRIDE = {
    "POL-ENC-001-REQ01": ["GDPR", "NIST", "PCI-DSS"],
    "POL-ENC-001-REQ02": ["NIST", "ISO27001"],
    "POL-ENC-001-REQ03": ["GDPR", "NIST"],
    "POL-AC-001-REQ01":  ["NIST", "ISO27001"],
    "POL-AC-001-REQ02":  ["NIST", "SOX"],
    "POL-AC-001-REQ03":  ["NIST", "ISO27001"],
    "POL-AUD-001-REQ01": ["GDPR", "NIST", "SOX"],
    "POL-AUD-001-REQ02": ["NIST", "PCI-DSS"],
    "POL-AUD-001-REQ03": ["NIST", "ISO27001"],
}

EVIDENCE_TYPE_MAP = {
    "encryption": ["Encryption_Cert", "Configuration_Snapshot", "Audit_Log"],
    "access": ["Access_Report", "Audit_Log", "Configuration_Snapshot"],
    "logging": ["Audit_Log", "Configuration_Snapshot", "Report"],
    "mfa": ["Access_Report", "Configuration_Snapshot", "Screenshot"],
    "key rotation": ["Encryption_Cert", "Audit_Log"],
    "tls": ["Configuration_Snapshot", "Encryption_Cert"],
    "retention": ["Configuration_Snapshot", "Policy_Document", "Audit_Log"],
    "privilege": ["Access_Report", "Audit_Log", "Configuration_Snapshot"],
    "monitor": ["Audit_Log", "Report", "Access_Report"],
}

STALENESS_BY_FREQUENCY = {
    "daily": 7,
    "weekly": 14,
    "monthly": 30,
    "quarterly": 90,
    "continuous": 3,
    "annually": 365,
}

@dataclass
class Requirement:
    req_id: str
    policy_id: str
    policy_name: str
    text: str
    responsible_team: str
    scope: str
    evidence_sources: List[str]
    audit_frequency: str
    frameworks: List[str]
    acceptable_evidence_types: List[str]
    staleness_threshold_days: int
    burden_of_proof: List[str]  # what must be proven

@dataclass
class Policy:
    policy_id: str
    name: str
    version: str
    status: str
    last_updated: str
    requirements: List[Requirement] = field(default_factory=list)


def detect_frameworks(text: str) -> List[str]:
    text_lower = text.lower()
    found = []
    for fw, keywords in FRAMEWORK_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(fw)
    return found or ["General"]


def detect_evidence_types(text: str) -> List[str]:
    text_lower = text.lower()
    types = set()
    for keyword, ev_types in EVIDENCE_TYPE_MAP.items():
        if keyword in text_lower:
            types.update(ev_types)
    return list(types) if types else ["Report", "Audit_Log"]


def extract_burden_of_proof(text: str) -> List[str]:
    """Decompose requirement into what must be proven - the unique part."""
    burdens = []
    text_lower = text.lower()

    if "encrypt" in text_lower:
        burdens.append("Encryption standard (AES-256 or stronger) is in use")
        burdens.append("Coverage is complete across all in-scope systems")
    if "key" in text_lower and "rotat" in text_lower:
        burdens.append("Key rotation occurred within the required timeframe")
        burdens.append("Rotation audit logs are maintained and accessible")
    if "tls" in text_lower or "transit" in text_lower:
        burdens.append("TLS 1.2+ is enforced on all in-scope communications")
        burdens.append("No legacy protocols (TLS 1.0/1.1) are permitted")
    if "mfa" in text_lower or "multi-factor" in text_lower:
        burdens.append("MFA is enforced for all administrative accounts")
        burdens.append("No admin access bypass exists without MFA")
    if "least privilege" in text_lower or "access" in text_lower:
        burdens.append("Access rights do not exceed role requirements")
        burdens.append("Periodic access reviews are conducted")
    if "log" in text_lower:
        burdens.append("All in-scope events are captured in audit logs")
        burdens.append("Logs are tamper-evident and attributable")
    if "retain" in text_lower or "retention" in text_lower:
        burdens.append("Retention period meets minimum policy requirement")
        burdens.append("Logs are accessible and retrievable during retention period")
    if "restrict" in text_lower and "log" in text_lower:
        burdens.append("Log access is limited to authorized personnel only")
        burdens.append("Log access itself is logged and monitored")

    if not burdens:
        burdens.append("Control is implemented as described in policy")
        burdens.append("Evidence is current and from an authoritative source")

    return burdens


def get_staleness_threshold(frequency: str) -> int:
    freq_lower = frequency.lower()
    for key, days in STALENESS_BY_FREQUENCY.items():
        if key in freq_lower:
            return days
    return 90  # default


def parse_requirement_block(block: str, policy_id: str, policy_name: str, req_index: int) -> Optional[Requirement]:
    """Parse a single REQUIREMENT block into a structured object."""
    lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
    if not lines:
        return None

    text = lines[0].lstrip("0123456789: ").strip()

    def extract_field(field_name: str) -> str:
        for line in lines:
            if line.lower().startswith(field_name.lower()):
                parts = line.split(":", 1)
                return parts[1].strip() if len(parts) > 1 else ""
        return ""

    responsible = extract_field("Responsible") or extract_field("responsible")
    scope = extract_field("Scope") or extract_field("scope") or "All systems"
    evidence_src = extract_field("Evidence Source") or extract_field("evidence source") or ""
    frequency = extract_field("Audit Frequency") or extract_field("audit frequency") or "Monthly"
    compliance_mapping = extract_field("Compliance Mapping") or extract_field("compliance mapping") or ""

    # Merge frameworks from text + compliance mapping
    all_text = text + " " + compliance_mapping
    frameworks = detect_frameworks(all_text)
    req_id = f"{policy_id}-REQ{req_index:02d}"

    # Apply override if available
    if req_id in REQUIREMENT_FRAMEWORK_OVERRIDE:
        frameworks = REQUIREMENT_FRAMEWORK_OVERRIDE[req_id]

    evidence_sources = [e.strip() for e in evidence_src.split(",") if e.strip()]
    acceptable_types = detect_evidence_types(text)
    staleness = get_staleness_threshold(frequency)
    burdens = extract_burden_of_proof(text)

    req_id = f"{policy_id}-REQ{req_index:02d}"

    return Requirement(
        req_id=req_id,
        policy_id=policy_id,
        policy_name=policy_name,
        text=text,
        responsible_team=responsible or "Security Operations",
        scope=scope,
        evidence_sources=evidence_sources,
        audit_frequency=frequency,
        frameworks=frameworks,
        acceptable_evidence_types=acceptable_types,
        staleness_threshold_days=staleness,
        burden_of_proof=burdens,
    )


def parse_policy_document(text: str) -> List[Policy]:
    """Parse a full policy document text into Policy objects."""
    policies = []

    # Split on policy boundaries
    policy_blocks = re.split(r'\n---+\n', text)

    for block in policy_blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.splitlines()

        # Extract policy header fields
        policy_name = ""
        policy_id = ""
        version = "1.0"
        status = "Active"
        last_updated = "Unknown"

        for line in lines[:10]:
            line = line.strip()
            if line.startswith("POLICY:"):
                policy_name = line.replace("POLICY:", "").strip()
            elif line.startswith("POLICY_ID:"):
                policy_id = line.replace("POLICY_ID:", "").strip()
            elif line.startswith("VERSION:"):
                version = line.replace("VERSION:", "").strip()
            elif line.startswith("STATUS:"):
                status = line.replace("STATUS:", "").strip()
            elif line.startswith("LAST_UPDATED:"):
                last_updated = line.replace("LAST_UPDATED:", "").strip()

        if not policy_id:
            policy_id = f"POL-{len(policies)+1:03d}"
        if not policy_name:
            policy_name = f"Policy {len(policies)+1}"

        # Find requirement blocks
        req_pattern = re.compile(r'REQUIREMENT\s+(\d+):(.*?)(?=REQUIREMENT\s+\d+:|$)', re.DOTALL)
        req_matches = req_pattern.findall(block)

        requirements = []
        for idx, (num, req_content) in enumerate(req_matches, start=1):
            req = parse_requirement_block(req_content.strip(), policy_id, policy_name, int(num))
            if req:
                requirements.append(req)

        if requirements:
            policies.append(Policy(
                policy_id=policy_id,
                name=policy_name,
                version=version,
                status=status,
                last_updated=last_updated,
                requirements=requirements,
            ))

    return policies


def load_policies(filepath: str) -> List[Policy]:
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    return parse_policy_document(text)
