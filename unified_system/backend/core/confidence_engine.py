"""
Auditor Confidence Engine
Multi-factor confidence scoring for compliance claims.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta


@dataclass
class ConfidenceFactor:
    name: str
    weight: float
    score: float
    reasoning: str
    recommendation: Optional[str] = None


@dataclass
class ComplianceConfidence:
    requirement_id: str
    requirement_text: str
    compliance_status: str   # COMPLIANT, CONDITIONAL, AT_RISK, NON_COMPLIANT
    confidence_score: float
    confidence_percentage: str
    factors: List[ConfidenceFactor] = field(default_factory=list)
    supporting_evidence_count: int = 0
    contradicting_evidence_count: int = 0
    red_flags: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    recommendation: str = ""
    next_review_date: str = ""
    audit_ready: bool = False


class AuditorConfidenceEngine:
    WEIGHTS = {
        'freshness': 0.40,
        'count_and_diversity': 0.25,
        'source_reliability': 0.15,
        'review_status': 0.10,
        'semantic_quality': 0.10,
    }

    SOURCE_RELIABILITY = {
        'System_Log': 0.95, 'Audit_Log': 0.95, 'Encryption_Cert': 0.90,
        'Configuration_Snapshot': 0.85, 'Access_Report': 0.85,
        'Report': 0.75, 'Policy_Document': 0.70, 'Test_Result': 0.75,
        'Training_Record': 0.65, 'Manual_Submission': 0.60,
        'Screenshot': 0.50, 'Email': 0.40, 'Procedure_Evidence': 0.72,
    }

    def calculate_confidence(
        self,
        requirement_id: str,
        requirement_text: str,
        supporting_evidence: List[Dict],
        contradicting_evidence: List[Dict] = None,
        evidence_quality_scores: Dict[str, float] = None,
        requirement_severity: str = "MEDIUM",
    ) -> ComplianceConfidence:
        contradicting_evidence = contradicting_evidence or []
        evidence_quality_scores = evidence_quality_scores or {}

        freshness = self._freshness(supporting_evidence)
        count_div = self._count_diversity(supporting_evidence)
        reliability = self._reliability(supporting_evidence)
        review = self._review_status(supporting_evidence)
        quality = self._semantic_quality(supporting_evidence, evidence_quality_scores)
        contradiction_penalty = min(0.5, len(contradicting_evidence) * 0.15)

        base = (freshness * self.WEIGHTS['freshness'] +
                count_div * self.WEIGHTS['count_and_diversity'] +
                reliability * self.WEIGHTS['source_reliability'] +
                review * self.WEIGHTS['review_status'] +
                quality * self.WEIGHTS['semantic_quality'])

        final = max(0.0, min(1.0, base - contradiction_penalty))
        status = self._status(final, len(supporting_evidence), len(contradicting_evidence), requirement_severity)

        factors = [
            ConfidenceFactor("Evidence Freshness", self.WEIGHTS['freshness'], freshness,
                             self._freshness_reason(supporting_evidence),
                             "Collect evidence more frequently" if freshness < 0.6 else None),
            ConfidenceFactor("Evidence Count & Diversity", self.WEIGHTS['count_and_diversity'], count_div,
                             f"{len(supporting_evidence)} evidence source(s) from {self._type_count(supporting_evidence)} type(s)",
                             "Gather evidence from more sources" if count_div < 0.6 else None),
            ConfidenceFactor("Source Reliability", self.WEIGHTS['source_reliability'], reliability,
                             self._reliability_reason(supporting_evidence)),
            ConfidenceFactor("Review Status", self.WEIGHTS['review_status'], review,
                             self._review_reason(supporting_evidence)),
            ConfidenceFactor("Semantic Match Quality", self.WEIGHTS['semantic_quality'], quality,
                             f"Average evidence match quality: {quality:.0%}"),
        ]

        red_flags = self._red_flags(final, supporting_evidence, contradicting_evidence, freshness, review)
        strengths = self._strengths(final, count_div, reliability, contradiction_penalty)
        recommendation = self._recommendation(status, final, red_flags)
        next_review = self._next_review(supporting_evidence, requirement_severity)
        audit_ready = final >= 0.72 and len(red_flags) < 2

        return ComplianceConfidence(
            requirement_id=requirement_id,
            requirement_text=requirement_text,
            compliance_status=status,
            confidence_score=round(final, 3),
            confidence_percentage=f"{final*100:.0f}%",
            factors=factors,
            supporting_evidence_count=len(supporting_evidence),
            contradicting_evidence_count=len(contradicting_evidence),
            red_flags=red_flags,
            strengths=strengths,
            recommendation=recommendation,
            next_review_date=next_review,
            audit_ready=audit_ready,
        )

    def _freshness(self, evs: List[Dict]) -> float:
        if not evs:
            return 0.0
        scores = []
        for e in evs:
            raw = e.get('freshness_days', 999)
            try:
                d = int(float(raw)) if raw not in (None, '', 'None') else 999
            except (ValueError, TypeError):
                d = 999
            if d <= 7:
                scores.append(1.0)
            elif d <= 30:
                scores.append(0.9)
            elif d <= 90:
                scores.append(0.7)
            elif d <= 180:
                scores.append(0.4)
            else:
                scores.append(0.1)
        return sum(scores) / len(scores)

    def _count_diversity(self, evs: List[Dict]) -> float:
        if not evs:
            return 0.0
        types = set(e.get('evidence_type', e.get('type', 'Unknown')) for e in evs)
        if len(evs) >= 3 and len(types) >= 2:
            return 1.0
        elif len(evs) >= 2:
            return 0.8
        elif len(evs) == 1:
            return 0.5
        return 0.0

    def _reliability(self, evs: List[Dict]) -> float:
        if not evs:
            return 0.0
        scores = [self.SOURCE_RELIABILITY.get(
            e.get('evidence_type', e.get('type', 'Report')), 0.65) for e in evs]
        return sum(scores) / len(scores)

    def _review_status(self, evs: List[Dict]) -> float:
        if not evs:
            return 0.0
        reviewed = sum(1 for e in evs if e.get('status') in ['Approved', 'Approved_With_Notes'])
        ratio = reviewed / len(evs)
        return 1.0 if ratio == 1.0 else 0.7 if ratio >= 0.5 else 0.4 if ratio > 0 else 0.1

    def _semantic_quality(self, evs: List[Dict], quality_scores: Dict) -> float:
        if not evs:
            return 0.0
        scores = []
        for e in evs:
            raw = quality_scores.get(e.get('evidence_id', ''),
                                     e.get('confidence_score', 0.5))
            try:
                scores.append(float(raw) if raw not in (None, '', 'None') else 0.5)
            except (ValueError, TypeError):
                scores.append(0.5)
        return sum(scores) / len(scores)

    def _type_count(self, evs: List[Dict]) -> int:
        return len(set(e.get('evidence_type', e.get('type', 'Unknown')) for e in evs))

    def _status(self, conf: float, sup: int, con: int, severity: str) -> str:
        # No supporting evidence at all → immediately non-compliant
        if sup == 0:
            return "NON_COMPLIANT"
        ct = 0.85 if severity == "CRITICAL" else 0.75
        at = 0.65 if severity == "CRITICAL" else 0.50
        # Contradicting evidence lowers the confidence score via the contradiction_penalty
        # already applied above; don't hard-fail here so partial compliance can surface
        if conf >= ct:
            return "COMPLIANT"
        elif conf >= at:
            return "CONDITIONAL"
        elif conf >= 0.30:
            return "AT_RISK"
        return "NON_COMPLIANT"

    def _red_flags(self, conf, supporting, contradicting, freshness, review) -> List[str]:
        flags = []
        if not supporting:
            flags.append("No supporting evidence found")
        if contradicting:
            flags.append(f"{len(contradicting)} contradicting evidence item(s) found")
        if freshness < 0.5:
            flags.append("Evidence is stale (older than 90 days)")
        if review < 0.4:
            flags.append("Most evidence has not been reviewed/approved")
        if len(supporting) == 1:
            flags.append("Only single evidence source — recommend corroboration")
        if conf < 0.5:
            flags.append("Overall confidence score below 50%")
        return flags

    def _strengths(self, conf, count_div, reliability, contradiction_penalty) -> List[str]:
        s = []
        if conf >= 0.8:
            s.append("Strong overall confidence in compliance claim")
        if count_div >= 0.9:
            s.append("Multiple evidence sources with good diversity")
        if reliability >= 0.9:
            s.append("Evidence from reliable, auditable sources")
        if contradiction_penalty == 0:
            s.append("No contradicting evidence found")
        return s

    def _recommendation(self, status: str, conf: float, red_flags: List[str]) -> str:
        if status == "COMPLIANT":
            return "PASS: Evidence supports compliance. Ready for audit."
        elif status == "CONDITIONAL":
            issues = "; ".join(red_flags[:2]) if red_flags else "See details"
            return f"CONDITIONAL PASS: Address issues before audit. Issues: {issues}"
        elif status == "AT_RISK":
            return "AT RISK: Collect additional evidence and remediate gaps."
        return "FAIL: No evidence of compliance. Immediate remediation required."

    def _freshness_reason(self, evs: List[Dict]) -> str:
        if not evs:
            return "No evidence to assess"
        def _safe_days(e):
            raw = e.get('freshness_days', 999)
            try:
                return int(float(raw)) if raw not in (None, '', 'None') else 999
            except (ValueError, TypeError):
                return 999
        avg = sum(_safe_days(e) for e in evs) / len(evs)
        if avg <= 7:
            return "Evidence is very recent (< 1 week)"
        elif avg <= 30:
            return "Evidence is recent (< 1 month)"
        elif avg <= 90:
            return "Evidence is moderately recent (< 3 months)"
        return f"Evidence is stale (avg {avg:.0f} days old)"

    def _reliability_reason(self, evs: List[Dict]) -> str:
        types = set(e.get('evidence_type', e.get('type', 'Unknown')) for e in evs)
        return f"Evidence from {len(types)} source type(s): {', '.join(list(types)[:3])}"

    def _review_reason(self, evs: List[Dict]) -> str:
        reviewed = sum(1 for e in evs if e.get('status') == 'Approved')
        return f"{reviewed}/{len(evs)} evidence item(s) approved"

    def _next_review(self, evs: List[Dict], severity: str) -> str:
        days = 30 if severity == "CRITICAL" else 60 if severity == "HIGH" else 90
        return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
