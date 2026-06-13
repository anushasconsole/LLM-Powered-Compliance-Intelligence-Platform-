"""
Report Generator - Produces audit-ready narratives and compliance reports.
Generates both machine-readable JSON and human-readable text reports.
"""
import json
import os
from datetime import datetime
from typing import List, Dict
from evidence_analyzer import ProofChain, EvidenceNode, get_framework_summary, get_anomaly_summary
import pandas as pd


STATUS_ICONS = {
    "COMPLIANT": "✅",
    "CONDITIONAL": "⚠️",
    "AT_RISK": "🔶",
    "NON_COMPLIANT": "❌",
    "UNKNOWN": "❓",
}

SEVERITY_ICONS = {
    "HIGH": "🔴",
    "MEDIUM": "🟡",
    "LOW": "🟢",
    "": "⚪",
}


def generate_narrative(chain: ProofChain) -> str:
    """Generate an auditor-quality narrative for a compliance requirement."""
    icon = STATUS_ICONS.get(chain.compliance_status, "❓")
    fw_str = ", ".join(chain.frameworks[:3])
    support_count = len(chain.supporting_evidence)
    undermine_count = len(chain.undermining_evidence)

    if chain.compliance_status == "COMPLIANT":
        narrative = (
            f"The organization demonstrates compliance with '{chain.requirement_text}' "
            f"({fw_str}). "
        )
        if chain.supporting_evidence:
            types = list(set(e.evidence_type.replace('_', ' ') for e in chain.supporting_evidence))
            narrative += (
                f"Supporting evidence includes {support_count} artifact(s) of types: "
                f"{', '.join(types[:3])}. "
            )
        if chain.addressed_burdens:
            narrative += (
                f"The following proof obligations are satisfied: "
                f"{'; '.join(chain.addressed_burdens[:2])}. "
            )
        narrative += f"Overall confidence: {chain.overall_confidence:.0%}. Status: COMPLIANT."

    elif chain.compliance_status == "CONDITIONAL":
        narrative = (
            f"Partial compliance is demonstrated for '{chain.requirement_text}' ({fw_str}). "
            f"{support_count} supporting artifact(s) were found, but {len(chain.unaddressed_burdens)} "
            f"proof obligation(s) remain unaddressed. "
        )
        if chain.unaddressed_burdens:
            narrative += (
                f"Outstanding gaps: {'; '.join(chain.unaddressed_burdens[:2])}. "
            )
        if undermine_count > 0:
            narrative += f"{undermine_count} undermining evidence item(s) reduce confidence. "
        narrative += (
            f"Overall confidence: {chain.overall_confidence:.0%}. "
            f"Status: CONDITIONAL PASS — remediation required before audit."
        )

    elif chain.compliance_status == "AT_RISK":
        narrative = (
            f"Compliance with '{chain.requirement_text}' ({fw_str}) is AT RISK. "
        )
        if support_count == 0:
            narrative += "No valid supporting evidence was found. "
        else:
            narrative += f"Only {support_count} weak evidence artifact(s) exist. "
        if undermine_count:
            narrative += f"{undermine_count} item(s) actively undermine the compliance argument. "
        narrative += (
            f"Overall confidence: {chain.overall_confidence:.0%}. "
            f"Immediate evidence collection and remediation required."
        )

    else:
        narrative = (
            f"NON-COMPLIANT: No evidence found for '{chain.requirement_text}' ({fw_str}). "
            f"This requirement has no supporting documentation and will result in an audit finding. "
            f"Escalate to {chain.frameworks[0] if chain.frameworks else 'compliance'} team immediately."
        )

    return narrative


def format_proof_chain_text(chain: ProofChain, idx: int) -> str:
    """Format a proof chain as human-readable text."""
    icon = STATUS_ICONS.get(chain.compliance_status, "❓")
    lines = []
    lines.append(f"\n{'='*70}")
    lines.append(f"REQUIREMENT {idx}: {chain.requirement_id}")
    lines.append(f"Policy: {chain.policy_name}")
    lines.append(f"Requirement: {chain.requirement_text}")
    lines.append(f"Frameworks: {', '.join(chain.frameworks)}")
    lines.append(f"Status: {icon} {chain.compliance_status} | Confidence: {chain.overall_confidence:.0%}")
    lines.append(f"{'='*70}")

    lines.append("\n📋 BURDEN OF PROOF:")
    for burden in chain.burden_of_proof:
        addressed = burden in chain.addressed_burdens
        marker = "✅" if addressed else "❌"
        lines.append(f"  {marker} {burden}")

    if chain.supporting_evidence:
        lines.append(f"\n✅ SUPPORTING EVIDENCE ({len(chain.supporting_evidence)} items):")
        for e in chain.supporting_evidence[:4]:
            lines.append(
                f"  • [{e.evidence_id}] {e.evidence_type.replace('_',' ')} | "
                f"Confidence: {e.confidence_score:.0%} | "
                f"Age: {e.freshness_days}d | Status: {e.status}"
            )

    if chain.undermining_evidence:
        lines.append(f"\n⚠️  UNDERMINING EVIDENCE ({len(chain.undermining_evidence)} items):")
        for e in chain.undermining_evidence[:3]:
            lines.append(
                f"  • [{e.evidence_id}] {e.evidence_type.replace('_',' ')} | "
                f"Anomaly: {e.anomaly_type} | Status: {e.status}"
            )

    if chain.devils_advocate_objections:
        lines.append(f"\n😈 DEVIL'S ADVOCATE (Pre-Audit Stress Test):")
        for i, obj in enumerate(chain.devils_advocate_objections, 1):
            lines.append(f"  [{i}] {obj}")

    lines.append(f"\n📝 AUDIT NARRATIVE:")
    lines.append(f"  {generate_narrative(chain)}")

    return "\n".join(lines)


def generate_text_report(
    chains: List[ProofChain],
    anomaly_summary: Dict,
    framework_summary: Dict,
    output_path: str
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    lines = []

    lines.append("=" * 70)
    lines.append("  COMPLIANCE EVIDENCE AUDIT REPORT")
    lines.append(f"  Generated: {now}")
    lines.append("  System: Compliance Narrative Engine v1.0")
    lines.append("=" * 70)

    # Executive Summary
    total = len(chains)
    compliant = sum(1 for c in chains if c.compliance_status == "COMPLIANT")
    conditional = sum(1 for c in chains if c.compliance_status == "CONDITIONAL")
    at_risk = sum(1 for c in chains if c.compliance_status == "AT_RISK")
    non_compliant = sum(1 for c in chains if c.compliance_status == "NON_COMPLIANT")
    overall_pct = round(compliant / total * 100) if total > 0 else 0

    lines.append("\n\n🔍 EXECUTIVE SUMMARY")
    lines.append("-" * 40)
    lines.append(f"  Requirements Assessed:  {total}")
    lines.append(f"  ✅ Compliant:            {compliant} ({overall_pct}%)")
    lines.append(f"  ⚠️  Conditional Pass:     {conditional}")
    lines.append(f"  🔶 At Risk:              {at_risk}")
    lines.append(f"  ❌ Non-Compliant:        {non_compliant}")
    lines.append(f"\n  Total Evidence Items:   {anomaly_summary['total_evidence']}")
    lines.append(f"  Anomalous Evidence:     {anomaly_summary['total_anomalies']} ({anomaly_summary['anomaly_rate']}%)")
    lines.append(f"  Avg Confidence Score:   {anomaly_summary['avg_confidence']:.0%}")
    lines.append(f"  Approved Evidence:      {anomaly_summary['approved_pct']}%")

    # Framework Summary
    lines.append("\n\n📊 FRAMEWORK COMPLIANCE OVERVIEW")
    lines.append("-" * 40)
    for fw, stats in framework_summary.items():
        total_fw = stats['total']
        compliant_fw = stats['compliant']
        pct = round(compliant_fw / total_fw * 100) if total_fw > 0 else 0
        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
        lines.append(f"  {fw:<12} [{bar}] {pct:3d}% ({compliant_fw}/{total_fw} compliant)")

    # Anomaly Breakdown
    lines.append("\n\n🚨 EVIDENCE ANOMALY BREAKDOWN")
    lines.append("-" * 40)
    for atype, count in anomaly_summary['by_type'].items():
        lines.append(f"  {atype:<30} {count:4d} items")

    # Individual Requirements
    lines.append("\n\n📋 REQUIREMENT DETAILS")
    for i, chain in enumerate(chains, 1):
        lines.append(format_proof_chain_text(chain, i))

    # Action Items
    lines.append("\n\n🎯 PRIORITY ACTION ITEMS")
    lines.append("-" * 40)
    action_num = 1
    for chain in chains:
        if chain.compliance_status in ["NON_COMPLIANT", "AT_RISK"]:
            lines.append(
                f"  {action_num}. [URGENT] {chain.requirement_id}: "
                f"Collect evidence immediately — {chain.requirement_text[:60]}..."
            )
            action_num += 1
    for chain in chains:
        if chain.compliance_status == "CONDITIONAL":
            lines.append(
                f"  {action_num}. [REVIEW] {chain.requirement_id}: "
                f"Address {len(chain.unaddressed_burdens)} gap(s) — {chain.unaddressed_burdens[0] if chain.unaddressed_burdens else 'review objections'}"
            )
            action_num += 1

    if action_num == 1:
        lines.append("  ✅ No urgent actions required.")

    lines.append("\n" + "=" * 70)
    lines.append("  END OF REPORT")
    lines.append("=" * 70)

    report_text = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    return report_text


def generate_json_report(
    chains: List[ProofChain],
    anomaly_summary: Dict,
    framework_summary: Dict,
    output_path: str
) -> Dict:
    now = datetime.now().isoformat()

    findings = []
    for chain in chains:
        findings.append({
            "requirement_id": chain.requirement_id,
            "requirement_text": chain.requirement_text,
            "policy_name": chain.policy_name,
            "frameworks": chain.frameworks,
            "compliance_status": chain.compliance_status,
            "confidence": chain.overall_confidence,
            "supporting_evidence_count": len(chain.supporting_evidence),
            "undermining_evidence_count": len(chain.undermining_evidence),
            "addressed_burdens": chain.addressed_burdens,
            "unaddressed_burdens": chain.unaddressed_burdens,
            "devils_advocate_objections": chain.devils_advocate_objections,
            "audit_narrative": generate_narrative(chain),
            "evidence_ids": [e.evidence_id for e in chain.supporting_evidence[:4]],
        })

    report = {
        "generated_at": now,
        "metadata": {
            "total_requirements": len(chains),
            "total_evidence": anomaly_summary["total_evidence"],
            "anomaly_rate_pct": anomaly_summary["anomaly_rate"],
            "avg_confidence": anomaly_summary["avg_confidence"],
        },
        "summary": {
            "compliant": sum(1 for c in chains if c.compliance_status == "COMPLIANT"),
            "conditional": sum(1 for c in chains if c.compliance_status == "CONDITIONAL"),
            "at_risk": sum(1 for c in chains if c.compliance_status == "AT_RISK"),
            "non_compliant": sum(1 for c in chains if c.compliance_status == "NON_COMPLIANT"),
        },
        "framework_summary": framework_summary,
        "anomaly_summary": anomaly_summary,
        "findings": findings,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    return report
