"""
Challenge Auditor - Adversarial compliance testing.
Stress-tests evidence quality before real auditors do.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta


@dataclass
class AuditChallenge:
    challenge_id: str
    requirement_id: str
    challenge_type: str
    severity: str   # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    evidence_ids: List[str]
    remediation_suggestion: str
    impact_on_confidence: float


@dataclass
class AuditChallengeReport:
    total_challenges: int
    critical_challenges: int
    high_challenges: int
    medium_challenges: int
    low_challenges: int
    challenges: List[AuditChallenge]
    overall_audit_recommendation: str
    status: str   # PASS, PASS_WITH_CONCERNS, CONDITIONAL_PASS, FAIL


class ChallengeAuditor:
    def audit_requirement(
        self,
        requirement_id: str,
        requirement_text: str,
        confidence_score: float,
        evidence_list: List[Dict],
    ) -> AuditChallengeReport:
        challenges: List[AuditChallenge] = []

        # 1. Missing evidence
        ch = self._check_missing(requirement_id, evidence_list)
        if ch:
            challenges.append(ch)

        # 2. Stale evidence
        ch = self._check_freshness(requirement_id, evidence_list)
        if ch:
            challenges.append(ch)

        # 3. Scope / single-source
        ch = self._check_scope(requirement_id, evidence_list)
        if ch:
            challenges.append(ch)

        # 4. Conflicting evidence
        ch = self._check_conflicts(requirement_id, evidence_list)
        if ch:
            challenges.append(ch)

        # 5. Weak confidence
        ch = self._check_confidence(requirement_id, confidence_score)
        if ch:
            challenges.append(ch)

        # 6. Documentation completeness
        ch = self._check_docs(requirement_id, evidence_list)
        if ch:
            challenges.append(ch)

        # 7. Rejected evidence
        ch = self._check_rejected(requirement_id, evidence_list)
        if ch:
            challenges.append(ch)

        critical = sum(1 for c in challenges if c.severity == "CRITICAL")
        high = sum(1 for c in challenges if c.severity == "HIGH")
        medium = sum(1 for c in challenges if c.severity == "MEDIUM")
        low = sum(1 for c in challenges if c.severity == "LOW")

        if critical > 0:
            status = "FAIL"
            rec = "❌ FAIL - Critical issues must be resolved before audit"
        elif high >= 2:
            status = "CONDITIONAL_PASS"
            rec = "⚠️ CONDITIONAL PASS - High priority issues should be addressed"
        elif high == 1 or medium > 0:
            status = "PASS_WITH_CONCERNS"
            rec = "⚡ PASS WITH CONCERNS - Minor issues identified"
        else:
            status = "PASS"
            rec = "✅ PASS - Evidence chain is solid"

        return AuditChallengeReport(
            total_challenges=len(challenges),
            critical_challenges=critical,
            high_challenges=high,
            medium_challenges=medium,
            low_challenges=low,
            challenges=challenges,
            overall_audit_recommendation=rec,
            status=status,
        )

    def _check_missing(self, req_id: str, evs: List[Dict]) -> Optional[AuditChallenge]:
        if not evs:
            return AuditChallenge(
                challenge_id=f"CH-MISS-{req_id}",
                requirement_id=req_id,
                challenge_type="MISSING_EVIDENCE",
                severity="CRITICAL",
                description="No evidence found. Auditor will reject this claim immediately.",
                evidence_ids=[],
                remediation_suggestion="Collect and upload compliance evidence for this requirement.",
                impact_on_confidence=-1.0,
            )
        return None

    def _check_freshness(self, req_id: str, evs: List[Dict]) -> Optional[AuditChallenge]:
        if not evs:
            return None
        def _days(e):
            raw = e.get('freshness_days', 0)
            try:
                return int(float(raw)) if raw not in (None, '', 'None') else 0
            except (ValueError, TypeError):
                return 0
        stale_critical = [e for e in evs if _days(e) > 180]
        stale_high     = [e for e in evs if 90 < _days(e) <= 180]
        if stale_critical:
            return AuditChallenge(
                challenge_id=f"CH-STALE-{req_id}",
                requirement_id=req_id,
                challenge_type="STALE_EVIDENCE",
                severity="CRITICAL",
                description=f"{len(stale_critical)} evidence item(s) are over 180 days old.",
                evidence_ids=[e.get('evidence_id', '') for e in stale_critical[:3]],
                remediation_suggestion="Refresh evidence through re-testing or re-certification.",
                impact_on_confidence=-0.5,
            )
        elif len(stale_high) > len(evs) / 2:
            return AuditChallenge(
                challenge_id=f"CH-STALE-{req_id}",
                requirement_id=req_id,
                challenge_type="STALE_EVIDENCE",
                severity="HIGH",
                description=f"Majority ({len(stale_high)}/{len(evs)}) of evidence is 90–180 days old.",
                evidence_ids=[e.get('evidence_id', '') for e in stale_high[:3]],
                remediation_suggestion="Update evidence with recent snapshots or test results.",
                impact_on_confidence=-0.3,
            )
        return None

    def _check_scope(self, req_id: str, evs: List[Dict]) -> Optional[AuditChallenge]:
        if not evs:
            return None
        if len(evs) == 1:
            return AuditChallenge(
                challenge_id=f"CH-SCOPE-{req_id}",
                requirement_id=req_id,
                challenge_type="SINGLE_SOURCE",
                severity="MEDIUM",
                description="Only one evidence artifact. Auditor prefers independent corroboration.",
                evidence_ids=[evs[0].get('evidence_id', '')],
                remediation_suggestion="Add evidence from at least one additional independent source.",
                impact_on_confidence=-0.2,
            )
        collectors = set(e.get('collected_by', '') for e in evs if e.get('collected_by'))
        if len(collectors) == 1 and len(evs) > 1:
            return AuditChallenge(
                challenge_id=f"CH-SRC-{req_id}",
                requirement_id=req_id,
                challenge_type="SINGLE_COLLECTOR",
                severity="MEDIUM",
                description=f"All evidence collected by one source: {list(collectors)[0]}",
                evidence_ids=[e.get('evidence_id', '') for e in evs],
                remediation_suggestion="Obtain verification from an independent team or third-party.",
                impact_on_confidence=-0.15,
            )
        return None

    def _check_conflicts(self, req_id: str, evs: List[Dict]) -> Optional[AuditChallenge]:
        if len(evs) < 2:
            return None
        conflict_keywords = ['not enabled', 'disabled', 'failed', 'non-compliant', 'unencrypted']
        for ev in evs:
            desc = ev.get('evidence_summary', ev.get('description', '')).lower()
            if any(kw in desc for kw in conflict_keywords):
                return AuditChallenge(
                    challenge_id=f"CH-CONF-{req_id}",
                    requirement_id=req_id,
                    challenge_type="CONFLICTING_EVIDENCE",
                    severity="CRITICAL",
                    description="Evidence contains contradictory statements about compliance status.",
                    evidence_ids=[ev.get('evidence_id', '')],
                    remediation_suggestion="Investigate and resolve conflicting evidence before audit.",
                    impact_on_confidence=-0.8,
                )
        return None

    def _check_confidence(self, req_id: str, score: float) -> Optional[AuditChallenge]:
        if score <= 0.0:
            return None  # No evidence case handled elsewhere
        if score < 0.50:
            return AuditChallenge(
                challenge_id=f"CH-LOWCONF-{req_id}",
                requirement_id=req_id,
                challenge_type="WEAK_CONFIDENCE",
                severity="CRITICAL",
                description=f"Confidence score {score:.0%} is critically low.",
                evidence_ids=[],
                remediation_suggestion="Collect stronger, more specific evidence.",
                impact_on_confidence=-0.5,
            )
        elif score < 0.70:
            return AuditChallenge(
                challenge_id=f"CH-LOWCONF-{req_id}",
                requirement_id=req_id,
                challenge_type="WEAK_CONFIDENCE",
                severity="HIGH",
                description=f"Confidence score {score:.0%} is below audit threshold (70%).",
                evidence_ids=[],
                remediation_suggestion="Strengthen evidence with additional corroborating sources.",
                impact_on_confidence=-0.2,
            )
        return None

    def _check_docs(self, req_id: str, evs: List[Dict]) -> Optional[AuditChallenge]:
        if not evs:
            return None
        incomplete = []
        for ev in evs:
            missing = [f for f in ['evidence_id', 'collection_date', 'evidence_summary']
                       if not ev.get(f)]
            if missing:
                incomplete.append(ev.get('evidence_id', 'unknown'))
        if incomplete:
            return AuditChallenge(
                challenge_id=f"CH-DOC-{req_id}",
                requirement_id=req_id,
                challenge_type="MISSING_DOCUMENTATION",
                severity="HIGH",
                description=f"Incomplete evidence records: {incomplete[:3]}",
                evidence_ids=incomplete[:3],
                remediation_suggestion="Ensure all evidence has ID, date, and description.",
                impact_on_confidence=-0.3,
            )
        return None

    def _check_rejected(self, req_id: str, evs: List[Dict]) -> Optional[AuditChallenge]:
        rejected = [e for e in evs if e.get('status') == 'Rejected']
        if rejected:
            return AuditChallenge(
                challenge_id=f"CH-REJ-{req_id}",
                requirement_id=req_id,
                challenge_type="REJECTED_EVIDENCE",
                severity="HIGH",
                description=f"{len(rejected)} evidence item(s) previously rejected.",
                evidence_ids=[e.get('evidence_id', '') for e in rejected[:3]],
                remediation_suggestion="Replace rejected evidence with approved alternatives.",
                impact_on_confidence=-0.35,
            )
        return None
