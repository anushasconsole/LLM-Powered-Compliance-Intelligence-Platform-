"""
Compliance Narrative Engine - Main Runner
=========================================
Run: python solution.py
Outputs: reports/audit_report.txt, reports/audit_report.json
"""
import os
import sys
import time
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, classification_report

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from policy_parser import load_policies
from evidence_analyzer import (
    load_evidence, classify_anomalies, build_evidence_nodes,
    build_proof_graph, get_framework_summary, get_anomaly_summary
)
from report_generator import generate_text_report, generate_json_report, generate_narrative


def print_separator(title=""):
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print('='*60)
    else:
        print('='*60)


def main():
    start = time.time()
    base = os.path.dirname(__file__)
    data_dir = os.path.join(base, 'data')
    reports_dir = os.path.join(base, 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    print_separator("COMPLIANCE NARRATIVE ENGINE")
    print("  Automated Compliance Evidence Collection & Audit")
    print("  Problem Statement 03 Solution")
    print_separator()

    # ─── STEP 1: Parse Policies ───────────────────────────────────────
    print("\n[1/5] Parsing policy documents...")
    policies = load_policies(os.path.join(data_dir, 'policy_documents.txt'))
    all_requirements = [req for policy in policies for req in policy.requirements]

    print(f"  ✅ Loaded {len(policies)} policies")
    print(f"  ✅ Extracted {len(all_requirements)} requirements")
    for policy in policies:
        print(f"     • {policy.policy_id}: {policy.name} ({len(policy.requirements)} requirements)")
        for req in policy.requirements:
            print(f"       - {req.req_id}: {req.text[:60]}...")
            print(f"         Frameworks: {', '.join(req.frameworks)} | "
                  f"Evidence types: {', '.join(req.acceptable_evidence_types[:3])}")
            print(f"         Burden of proof ({len(req.burden_of_proof)} items):")
            for burden in req.burden_of_proof[:2]:
                print(f"           → {burden}")

    # ─── STEP 2: Load & Classify Evidence ────────────────────────────
    print("\n[2/5] Loading and classifying evidence artifacts...")
    df = load_evidence(os.path.join(data_dir, 'evidence_artifacts.csv'))
    df = classify_anomalies(df, staleness_threshold=90)

    total = len(df)
    anomalies = df['is_anomaly'].sum()
    print(f"  ✅ Loaded {total} evidence records")
    print(f"  🚨 Anomalies detected: {anomalies} ({anomalies/total*100:.1f}%)")
    print(f"  📊 Status breakdown: {df['status'].value_counts().to_dict()}")
    print(f"  📊 Anomaly types: {df['anomaly_type'].value_counts().to_dict()}")

    # ─── STEP 3: Evaluate Against Ground Truth ────────────────────────
    print("\n[3/5] Evaluating detection accuracy...")
    # Ground truth comes from the anomaly_marker column (non-empty = anomaly)
    y_true = (df['anomaly_marker'] != '').astype(int)
    y_pred = df['is_anomaly'].astype(int)

    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    print(f"  📈 Precision: {precision:.2%}")
    print(f"  📈 Recall:    {recall:.2%}")
    print(f"  📈 F1 Score:  {f1:.2f}")
    print()
    print(classification_report(
        y_true, y_pred,
        target_names=['Clean Evidence', 'Anomalous Evidence'],
        zero_division=0
    ))

    # ─── STEP 4: Build Proof Graph ────────────────────────────────────
    print("\n[4/5] Building compliance proof graph...")
    evidence_nodes = build_evidence_nodes(df)
    chains = build_proof_graph(all_requirements, evidence_nodes)

    compliant = sum(1 for c in chains if c.compliance_status == "COMPLIANT")
    conditional = sum(1 for c in chains if c.compliance_status == "CONDITIONAL")
    at_risk = sum(1 for c in chains if c.compliance_status == "AT_RISK")
    non_compliant = sum(1 for c in chains if c.compliance_status == "NON_COMPLIANT")

    print(f"  ✅ Proof chains built: {len(chains)}")
    print(f"     • COMPLIANT:      {compliant}")
    print(f"     • CONDITIONAL:    {conditional}")
    print(f"     • AT RISK:        {at_risk}")
    print(f"     • NON-COMPLIANT:  {non_compliant}")

    # Show example proof chain
    print("\n  📋 EXAMPLE PROOF CHAIN (first requirement):")
    if chains:
        ex = chains[0]
        print(f"     Requirement: {ex.requirement_text[:65]}...")
        print(f"     Status: {ex.compliance_status} | Confidence: {ex.overall_confidence:.0%}")
        print(f"     Supporting evidence: {len(ex.supporting_evidence)} items")
        print(f"     Devil's advocate objections: {len(ex.devils_advocate_objections)}")
        if ex.devils_advocate_objections:
            print(f"     → {ex.devils_advocate_objections[0]}")

    # ─── STEP 5: Generate Reports ─────────────────────────────────────
    print("\n[5/5] Generating audit reports...")
    anomaly_summary = get_anomaly_summary(df)
    framework_summary = get_framework_summary(chains)

    text_path = os.path.join(reports_dir, 'audit_report.txt')
    json_path = os.path.join(reports_dir, 'audit_report.json')

    generate_text_report(chains, anomaly_summary, framework_summary, text_path)
    generate_json_report(chains, anomaly_summary, framework_summary, json_path)

    elapsed = time.time() - start
    print(f"  ✅ Text report:  {text_path}")
    print(f"  ✅ JSON report:  {json_path}")
    print(f"\n⏱  Total analysis time: {elapsed:.2f} seconds")
    print_separator()
    print("  ANALYSIS COMPLETE")
    print_separator()


if __name__ == "__main__":
    main()
