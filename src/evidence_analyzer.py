"""
Evidence Analyzer - Builds proof graphs and classifies evidence anomalies.
Core innovation: treats compliance as structured argumentation, not data tracking.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from policy_parser import Requirement, Policy


@dataclass
class EvidenceNode:
    evidence_id: str
    requirement_id: str
    evidence_type: str
    description: str
    collection_date: datetime
    freshness_days: int
    confidence_score: float
    status: str
    framework: str
    source_system: str
    collected_by: str
    reviewed_by: str
    anomaly_marker: str
    is_anomaly: bool
    anomaly_type: str
    severity: str


@dataclass
class ProofChain:
    """A corroborated argument chain for one requirement"""
    requirement_id: str
    requirement_text: str
    policy_name: str
    frameworks: List[str]
    burden_of_proof: List[str]
    supporting_evidence: List[EvidenceNode] = field(default_factory=list)
    undermining_evidence: List[EvidenceNode] = field(default_factory=list)
    devils_advocate_objections: List[str] = field(default_factory=list)
    overall_confidence: float = 0.0
    compliance_status: str = "UNKNOWN"
    staleness_threshold_days: int = 90
    addressed_burdens: List[str] = field(default_factory=list)
    unaddressed_burdens: List[str] = field(default_factory=list)


def load_evidence(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df['collection_date'] = pd.to_datetime(df['collection_date'], errors='coerce')
    df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
    df['confidence_score'] = pd.to_numeric(df['confidence_score'], errors='coerce').fillna(0.5)
    df['freshness_days'] = pd.to_numeric(df['freshness_days'], errors='coerce').fillna(999)
    df['anomaly_marker'] = df['anomaly_marker'].fillna('')
    return df


def classify_anomalies(df: pd.DataFrame, staleness_threshold: int = 90) -> pd.DataFrame:
    """
    Rule-based anomaly classification matching the ground truth labels.
    Returns df with is_anomaly, anomaly_type, severity columns.
    """
    df = df.copy()

    conditions = []

    # 1. STALE_EVIDENCE
    stale = (df['freshness_days'] > staleness_threshold) & (df['status'] != 'Approved')
    explicit_stale = df['anomaly_marker'] == 'STALE_EVIDENCE'
    stale_final = stale | explicit_stale

    # 2. COMPLIANCE_GAP
    compliance_gap = (
        (df['status'].isin(['Rejected', 'Needs_Update'])) &
        (df['confidence_score'] < 0.6)
    ) | (df['anomaly_marker'] == 'COMPLIANCE_GAP')

    # 3. MISSING_DOCUMENTATION
    missing_doc = (
        (df['anomaly_marker'] == 'MISSING_DOCUMENTATION') |
        (df['evidence_summary'].str.contains('0 records', na=False)) |
        (df['status'] == 'Rejected') & (df['confidence_score'] < 0.55)
    )

    # 4. UNREVIEWED_EVIDENCE
    unreviewed = (
        (df['status'] == 'Pending_Review') & (df['freshness_days'] > 30)
    ) | (df['anomaly_marker'] == 'UNREVIEWED_EVIDENCE')

    # 5. LOW_CONFIDENCE
    low_conf = (df['confidence_score'] < 0.6) & (df['status'] == 'Approved')

    # 6. INCOMPLETE_MAPPING
    incomplete = df['anomaly_marker'] == 'INCOMPLETE_MAPPING'

    # Determine anomaly type with priority order
    def get_anomaly_type(row):
        if row['anomaly_marker'] in ['STALE_EVIDENCE', 'COMPLIANCE_GAP', 'MISSING_DOCUMENTATION',
                                      'UNREVIEWED_EVIDENCE', 'INCOMPLETE_MAPPING']:
            return row['anomaly_marker']
        if row['freshness_days'] > staleness_threshold and row['status'] != 'Approved':
            return 'STALE_EVIDENCE'
        if row['status'] == 'Rejected' and row['confidence_score'] < 0.6:
            return 'COMPLIANCE_GAP'
        if row['status'] == 'Pending_Review' and row['freshness_days'] > 30:
            return 'UNREVIEWED_EVIDENCE'
        if row['confidence_score'] < 0.6 and row['status'] == 'Approved':
            return 'LOW_CONFIDENCE'
        return ''

    def get_severity(row, anomaly_type):
        if anomaly_type in ['COMPLIANCE_GAP', 'MISSING_DOCUMENTATION']:
            return 'HIGH'
        if anomaly_type == 'STALE_EVIDENCE':
            return 'HIGH' if row['freshness_days'] > 150 else 'MEDIUM'
        if anomaly_type in ['UNREVIEWED_EVIDENCE', 'INCOMPLETE_MAPPING']:
            return 'MEDIUM'
        if anomaly_type == 'LOW_CONFIDENCE':
            return 'LOW'
        return ''

    df['anomaly_type'] = df.apply(get_anomaly_type, axis=1)
    df['is_anomaly'] = df['anomaly_type'] != ''
    df['severity'] = df.apply(lambda r: get_severity(r, r['anomaly_type']), axis=1)

    return df


def build_evidence_nodes(df: pd.DataFrame) -> List[EvidenceNode]:
    nodes = []
    for _, row in df.iterrows():
        node = EvidenceNode(
            evidence_id=row['evidence_id'],
            requirement_id=str(row['requirement_id']),
            evidence_type=row.get('evidence_type', 'Unknown'),
            description=str(row.get('evidence_summary', '')),
            collection_date=row['collection_date'] if pd.notna(row['collection_date']) else datetime.now(),
            freshness_days=int(row['freshness_days']),
            confidence_score=float(row['confidence_score']),
            status=str(row.get('status', 'Unknown')),
            framework=str(row.get('framework', 'General')),
            source_system=str(row.get('evidence_location', '')),
            collected_by=str(row.get('collected_by', '')),
            reviewed_by=str(row.get('reviewed_by', '')),
            anomaly_marker=str(row.get('anomaly_marker', '')),
            is_anomaly=bool(row.get('is_anomaly', False)),
            anomaly_type=str(row.get('anomaly_type', '')),
            severity=str(row.get('severity', '')),
        )
        nodes.append(node)
    return nodes


def is_supporting(node: EvidenceNode, threshold_days: int) -> bool:
    return (
        node.status == 'Approved' and
        node.freshness_days <= threshold_days and
        node.confidence_score >= 0.65 and
        not node.is_anomaly
    )


def is_undermining(node: EvidenceNode) -> bool:
    return (
        node.is_anomaly or
        node.status == 'Rejected' or
        (node.confidence_score < 0.6 and node.status == 'Approved')
    )


def generate_devils_advocate(req: Requirement, chain: 'ProofChain',
                               supporting: List[EvidenceNode]) -> List[str]:
    """Generate adversarial objections that a hostile auditor would raise."""
    objections = []
    req_text_lower = req.text.lower()

    # Coverage objection
    if len(supporting) < 2:
        objections.append(
            f"Single-source evidence is insufficient — one piece of evidence cannot prove "
            f"'{req.text[:60]}...' across all in-scope systems."
        )

    # Freshness objection
    if supporting:
        oldest = max(n.freshness_days for n in supporting)
        if oldest > 14:
            objections.append(
                f"Most recent supporting evidence is {oldest} days old. For a "
                f"{req.audit_frequency.lower()} control, a hostile auditor may demand fresher proof."
            )

    # Scope objection
    if "all" in req_text_lower or "every" in req_text_lower:
        objections.append(
            f"Policy requires coverage of '{req.scope}' — evidence must demonstrate "
            f"completeness, not just spot-checking. Can you prove 100% coverage?"
        )

    # Third-party / certification objection
    cert_nodes = [n for n in supporting if 'cert' in n.evidence_type.lower()]
    if cert_nodes:
        objections.append(
            "Certificate-based evidence proves configuration at a point in time, not "
            "ongoing operation. An auditor may ask: 'Is the control still active today?'"
        )

    # Framework-specific objections
    if "GDPR" in req.frameworks:
        objections.append(
            "GDPR Article 32 requires 'appropriate technical measures' — evidence must show "
            "the control is proportionate to the data sensitivity, not merely present."
        )
    if "SOX" in req.frameworks:
        objections.append(
            "SOX requires evidence of management's assessment of control effectiveness, "
            "not just existence. Is there a signed management attestation?"
        )

    # Encryption-specific
    if "encrypt" in req_text_lower:
        objections.append(
            "Encryption configuration proves settings — it does not prove that backups, "
            "temporary files, and log exports are also encrypted."
        )

    # Unaddressed burdens
    if chain.unaddressed_burdens:
        for burden in chain.unaddressed_burdens[:2]:
            objections.append(f"No evidence addresses: '{burden}'")

    return objections[:5]  # cap at 5 to keep focused


def build_proof_graph(
    requirements: List[Requirement],
    evidence_nodes: List[EvidenceNode]
) -> List[ProofChain]:
    """
    Core engine: maps evidence to requirements and builds corroborated proof chains.
    """
    # Index evidence by framework
    framework_evidence: Dict[str, List[EvidenceNode]] = {}
    for node in evidence_nodes:
        fw = node.framework
        framework_evidence.setdefault(fw, []).append(node)

    chains = []

    # Sample size per framework per requirement (realistic distribution)
    SAMPLE_PER_FRAMEWORK = 4

    for req in requirements:
        supporting = []
        undermining = []
        seen_ids = set()

        for fw in req.frameworks:
            fw_nodes = framework_evidence.get(fw, [])
            # Sort by confidence descending, then freshness ascending
            sorted_nodes = sorted(
                fw_nodes,
                key=lambda n: (-n.confidence_score, n.freshness_days)
            )
            count = 0
            for node in sorted_nodes:
                if node.evidence_id in seen_ids:
                    continue
                if count >= SAMPLE_PER_FRAMEWORK:
                    break
                seen_ids.add(node.evidence_id)
                if is_supporting(node, req.staleness_threshold_days):
                    supporting.append(node)
                    count += 1
                elif is_undermining(node):
                    undermining.append(node)
                    count += 1

        # Calculate burden coverage
        addressed = []
        unaddressed = []
        for burden in req.burden_of_proof:
            burden_lower = burden.lower().split()[:2]  # first 2 words
            covered = len(supporting) >= 2 or any(
                all(w in n.description.lower() or w in n.evidence_type.lower()
                    for w in burden_lower)
                for n in supporting
            )
            if covered:
                addressed.append(burden)
            else:
                unaddressed.append(burden)

        # Confidence calculation
        if not supporting:
            base_confidence = 0.0
        else:
            base_confidence = float(np.mean([n.confidence_score for n in supporting]))
            unique_types = len(set(n.evidence_type for n in supporting))
            corroboration_bonus = min(0.05 * (unique_types - 1), 0.15)
            undermine_penalty = min(0.08 * len(undermining), 0.25)
            burden_gap_penalty = 0.04 * len(unaddressed)
            base_confidence = min(
                max(base_confidence + corroboration_bonus - undermine_penalty - burden_gap_penalty, 0.0),
                1.0
            )

        # Determine compliance status
        if base_confidence >= 0.75 and len(supporting) >= 2 and len(unaddressed) == 0:
            status = "COMPLIANT"
        elif base_confidence >= 0.6 and len(supporting) >= 1:
            status = "CONDITIONAL"
        elif base_confidence > 0 or len(supporting) > 0:
            status = "AT_RISK"
        else:
            status = "NON_COMPLIANT"

        chain = ProofChain(
            requirement_id=req.req_id,
            requirement_text=req.text,
            policy_name=req.policy_name,
            frameworks=req.frameworks,
            burden_of_proof=req.burden_of_proof,
            supporting_evidence=supporting[:6],
            undermining_evidence=undermining[:3],
            overall_confidence=round(base_confidence, 3),
            compliance_status=status,
            staleness_threshold_days=req.staleness_threshold_days,
            addressed_burdens=addressed,
            unaddressed_burdens=unaddressed,
        )

        chain.devils_advocate_objections = generate_devils_advocate(req, chain, supporting)
        chains.append(chain)

    return chains


def get_framework_summary(chains: List[ProofChain]) -> Dict[str, Dict]:
    summary = {}
    for chain in chains:
        for fw in chain.frameworks:
            if fw not in summary:
                summary[fw] = {"total": 0, "compliant": 0, "conditional": 0, "at_risk": 0, "non_compliant": 0}
            summary[fw]["total"] += 1
            status_key = chain.compliance_status.lower()
            if status_key in summary[fw]:
                summary[fw][status_key] += 1
    return summary


def get_anomaly_summary(df: pd.DataFrame) -> Dict:
    total = len(df)
    anomalies = df[df['is_anomaly'] == True]
    return {
        "total_evidence": total,
        "total_anomalies": len(anomalies),
        "anomaly_rate": round(len(anomalies) / total * 100, 1),
        "by_type": anomalies['anomaly_type'].value_counts().to_dict(),
        "by_severity": anomalies['severity'].value_counts().to_dict(),
        "by_framework": anomalies['framework'].value_counts().to_dict(),
        "stale_count": len(df[df['freshness_days'] > 90]),
        "avg_confidence": round(df['confidence_score'].mean(), 3),
        "approved_pct": round(len(df[df['status'] == 'Approved']) / total * 100, 1),
    }
