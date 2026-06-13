"""
Auditor Confidence Engine

Calculates confidence scores for compliance claims based on:
- Evidence freshness
- Evidence count and type diversity
- Source reliability
- Review status
- Semantic matching quality
- Framework-specific factors

Output is auditor-focused: instead of just "PASS", shows "PASS (89% confidence)".

Example:
    engine = AuditorConfidenceEngine()
    
    confidence = engine.calculate_confidence(
        requirement_id='REQ-001',
        supporting_evidence=[...],
        contradicting_evidence=[...],
        evidence_quality_scores={...}
    )
    
    print(f"Compliance Status: {confidence.status}")
    print(f"Confidence: {confidence.score:.1%}")
    print(f"Factors: {confidence.breakdown}")
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum


class ComplianceStatus(str, Enum):
    """Compliance status levels"""
    COMPLIANT = "COMPLIANT"
    CONDITIONAL = "CONDITIONAL"  # Has evidence but with issues
    AT_RISK = "AT_RISK"  # Weak or stale evidence
    NON_COMPLIANT = "NON_COMPLIANT"  # No evidence


@dataclass
class ConfidenceFactor:
    """Individual confidence factor"""
    name: str  # e.g., "Evidence Freshness", "Source Reliability"
    weight: float  # 0-1, contribution to overall score
    score: float  # 0-1, this factor's score
    reasoning: str  # Why this score
    recommendation: Optional[str] = None  # Improvement suggestion


@dataclass
class ComplianceConfidence:
    """Auditor confidence in compliance claim"""
    requirement_id: str
    requirement_text: str
    compliance_status: ComplianceStatus
    confidence_score: float  # 0-1
    confidence_percentage: str  # "89%"
    
    factors: List[ConfidenceFactor] = field(default_factory=list)
    
    supporting_evidence_count: int = 0
    contradicting_evidence_count: int = 0
    
    red_flags: List[str] = field(default_factory=list)  # Issues found
    strengths: List[str] = field(default_factory=list)  # What's good
    
    recommendation: str = "N/A"
    next_review_date: str = "N/A"
    audit_ready: bool = False
    auditor_notes: str = ""


class AuditorConfidenceEngine:
    """
    Multi-factor confidence scoring for compliance claims.
    
    Factors considered:
    1. Evidence Freshness (40%): How recent is the evidence?
    2. Evidence Count & Type Diversity (25%): Multiple sources?
    3. Source Reliability (15%): Is the source trustworthy?
    4. Review Status (10%): Has it been reviewed by auditors?
    5. Semantic Match Quality (10%): Does evidence really prove requirement?
    """
    
    def __init__(self):
        self.weights = {
            'freshness': 0.40,
            'count_and_diversity': 0.25,
            'source_reliability': 0.15,
            'review_status': 0.10,
            'semantic_quality': 0.10
        }
    
    def calculate_confidence(
        self,
        requirement_id: str,
        requirement_text: str,
        supporting_evidence: List[Dict],
        contradicting_evidence: List[Dict] = None,
        evidence_quality_scores: Dict[str, float] = None,
        requirement_severity: str = "MEDIUM",
        framework_criticality: str = "MEDIUM"
    ) -> ComplianceConfidence:
        """
        Calculate auditor confidence in compliance claim.
        
        Args:
            requirement_id: Requirement identifier
            requirement_text: Full requirement text
            supporting_evidence: List of supporting evidence dicts
            contradicting_evidence: List of contradicting evidence (if any)
            evidence_quality_scores: Dict mapping evidence_id to quality (0-1)
            requirement_severity: CRITICAL, HIGH, MEDIUM, LOW
            framework_criticality: Framework importance
            
        Returns:
            ComplianceConfidence object
        """
        contradicting_evidence = contradicting_evidence or []
        evidence_quality_scores = evidence_quality_scores or {}
        
        # Calculate individual factors
        freshness_score = self._calculate_freshness(supporting_evidence)
        count_score = self._calculate_count_and_diversity(supporting_evidence)
        reliability_score = self._calculate_source_reliability(supporting_evidence)
        review_score = self._calculate_review_status(supporting_evidence)
        quality_score = self._calculate_semantic_quality(
            supporting_evidence,
            evidence_quality_scores
        )
        
        # Adjust for contradictions
        contradiction_penalty = self._calculate_contradiction_penalty(
            contradicting_evidence
        )
        
        # Calculate overall confidence
        base_confidence = (
            freshness_score * self.weights['freshness'] +
            count_score * self.weights['count_and_diversity'] +
            reliability_score * self.weights['source_reliability'] +
            review_score * self.weights['review_status'] +
            quality_score * self.weights['semantic_quality']
        )
        
        final_confidence = max(0, base_confidence - contradiction_penalty)
        
        # Determine status
        status = self._determine_status(
            final_confidence,
            len(supporting_evidence),
            len(contradicting_evidence),
            requirement_severity
        )
        
        # Build factors breakdown
        factors = [
            ConfidenceFactor(
                name="Evidence Freshness",
                weight=self.weights['freshness'],
                score=freshness_score,
                reasoning=self._freshness_reasoning(supporting_evidence),
                recommendation="Collect evidence more frequently" if freshness_score < 0.6 else None
            ),
            ConfidenceFactor(
                name="Evidence Count & Diversity",
                weight=self.weights['count_and_diversity'],
                score=count_score,
                reasoning=f"{len(supporting_evidence)} evidence sources found",
                recommendation="Gather evidence from more sources" if count_score < 0.6 else None
            ),
            ConfidenceFactor(
                name="Source Reliability",
                weight=self.weights['source_reliability'],
                score=reliability_score,
                reasoning=self._reliability_reasoning(supporting_evidence)
            ),
            ConfidenceFactor(
                name="Review Status",
                weight=self.weights['review_status'],
                score=review_score,
                reasoning=self._review_reasoning(supporting_evidence)
            ),
            ConfidenceFactor(
                name="Semantic Match Quality",
                weight=self.weights['semantic_quality'],
                score=quality_score,
                reasoning=f"Average semantic match: {quality_score:.1%}"
            ),
        ]
        
        # Identify red flags and strengths
        red_flags = self._identify_red_flags(
            final_confidence,
            supporting_evidence,
            contradicting_evidence,
            freshness_score,
            review_score
        )
        
        strengths = self._identify_strengths(
            final_confidence,
            count_score,
            reliability_score,
            contradiction_penalty
        )
        
        # Generate recommendation and next review date
        recommendation = self._generate_recommendation(status, final_confidence, red_flags)
        next_review = self._calculate_next_review_date(
            supporting_evidence,
            requirement_severity
        )
        
        audit_ready = final_confidence >= 0.75 and len(red_flags) < 2
        
        return ComplianceConfidence(
            requirement_id=requirement_id,
            requirement_text=requirement_text,
            compliance_status=status,
            confidence_score=final_confidence,
            confidence_percentage=f"{final_confidence*100:.0f}%",
            factors=factors,
            supporting_evidence_count=len(supporting_evidence),
            contradicting_evidence_count=len(contradicting_evidence),
            red_flags=red_flags,
            strengths=strengths,
            recommendation=recommendation,
            next_review_date=next_review,
            audit_ready=audit_ready,
            auditor_notes=""
        )
    
    def _calculate_freshness(self, evidence_list: List[Dict]) -> float:
        """Score based on evidence age (0-1)"""
        if not evidence_list:
            return 0.0
        
        freshness_scores = []
        for evidence in evidence_list:
            days_old = evidence.get('freshness_days', 999)
            
            if days_old <= 7:
                score = 1.0
            elif days_old <= 30:
                score = 0.9
            elif days_old <= 90:
                score = 0.7
            elif days_old <= 180:
                score = 0.4
            else:
                score = 0.1
            
            freshness_scores.append(score)
        
        # Average freshness
        return sum(freshness_scores) / len(freshness_scores)
    
    def _calculate_count_and_diversity(self, evidence_list: List[Dict]) -> float:
        """Score based on number and diversity of evidence"""
        if not evidence_list:
            return 0.0
        
        count = len(evidence_list)
        
        # Count evidence types
        types = set()
        for evidence in evidence_list:
            types.add(evidence.get('evidence_type', 'Unknown'))
        
        type_diversity = len(types)
        
        # Scoring
        if count >= 3 and type_diversity >= 2:
            return 1.0
        elif count >= 2 and type_diversity >= 1:
            return 0.8
        elif count >= 1:
            return 0.5
        else:
            return 0.0
    
    def _calculate_source_reliability(self, evidence_list: List[Dict]) -> float:
        """Score based on reliability of evidence sources"""
        if not evidence_list:
            return 0.0
        
        reliable_sources = {
            'System_Log': 0.95,  # Very reliable
            'Audit_Log': 0.95,
            'Encryption_Cert': 0.90,
            'Configuration_Snapshot': 0.85,
            'Access_Report': 0.85,
            'Report': 0.75,
            'Manual_Submission': 0.60,  # Less reliable
            'Screenshot': 0.50,
            'Email': 0.40
        }
        
        scores = []
        for evidence in evidence_list:
            evidence_type = evidence.get('evidence_type', 'Report')
            score = reliable_sources.get(evidence_type, 0.65)
            scores.append(score)
        
        return sum(scores) / len(scores)
    
    def _calculate_review_status(self, evidence_list: List[Dict]) -> float:
        """Score based on whether evidence has been reviewed"""
        if not evidence_list:
            return 0.0
        
        reviewed_count = sum(
            1 for e in evidence_list 
            if e.get('review_status') in ['Approved', 'Approved_With_Notes']
        )
        
        if reviewed_count == len(evidence_list):
            return 1.0
        elif reviewed_count >= len(evidence_list) * 0.5:
            return 0.7
        elif reviewed_count > 0:
            return 0.4
        else:
            return 0.1
    
    def _calculate_semantic_quality(
        self,
        evidence_list: List[Dict],
        quality_scores: Dict[str, float]
    ) -> float:
        """Score based on semantic match quality"""
        if not evidence_list:
            return 0.0
        
        scores = []
        for evidence in evidence_list:
            evidence_id = evidence.get('evidence_id', '')
            # Use provided quality score, or estimate from confidence
            if evidence_id in quality_scores:
                score = quality_scores[evidence_id]
            else:
                score = evidence.get('confidence_score', 0.5)
            scores.append(score)
        
        return sum(scores) / len(scores)
    
    def _calculate_contradiction_penalty(self, contradicting_evidence: List[Dict]) -> float:
        """Calculate penalty for contradicting evidence"""
        if not contradicting_evidence:
            return 0.0
        
        # Each contradiction reduces confidence
        penalty_per_contradiction = 0.15
        penalty = len(contradicting_evidence) * penalty_per_contradiction
        
        return min(0.5, penalty)  # Cap at 50% penalty
    
    def _determine_status(
        self,
        confidence: float,
        supporting_count: int,
        contradicting_count: int,
        severity: str
    ) -> ComplianceStatus:
        """Determine compliance status"""
        
        # Contradicting evidence
        if contradicting_count > 0:
            return ComplianceStatus.NON_COMPLIANT
        
        # No evidence
        if supporting_count == 0:
            return ComplianceStatus.NON_COMPLIANT
        
        # Severity-adjusted thresholds
        if severity == "CRITICAL":
            compliant_threshold = 0.85
            at_risk_threshold = 0.65
        else:
            compliant_threshold = 0.75
            at_risk_threshold = 0.50
        
        if confidence >= compliant_threshold:
            return ComplianceStatus.COMPLIANT
        elif confidence >= at_risk_threshold:
            return ComplianceStatus.CONDITIONAL
        else:
            return ComplianceStatus.AT_RISK
    
    def _identify_red_flags(
        self,
        confidence: float,
        supporting_evidence: List[Dict],
        contradicting_evidence: List[Dict],
        freshness_score: float,
        review_score: float
    ) -> List[str]:
        """Identify issues that reduce confidence"""
        flags = []
        
        if confidence < 0.5:
            flags.append("Low overall confidence score")
        
        if not supporting_evidence:
            flags.append("No supporting evidence found")
        
        if contradicting_evidence:
            flags.append(f"{len(contradicting_evidence)} contradicting evidence items found")
        
        if freshness_score < 0.5:
            flags.append("Evidence is stale (older than 90 days)")
        
        if review_score < 0.4:
            flags.append("Most evidence has not been reviewed by auditor")
        
        if len(supporting_evidence) == 1:
            flags.append("Only single evidence source - recommend additional corroboration")
        
        return flags
    
    def _identify_strengths(
        self,
        confidence: float,
        count_score: float,
        reliability_score: float,
        contradiction_penalty: float
    ) -> List[str]:
        """Identify strengths of compliance claim"""
        strengths = []
        
        if confidence >= 0.8:
            strengths.append("Strong overall confidence in compliance claim")
        
        if count_score >= 0.9:
            strengths.append("Multiple evidence sources with good diversity")
        
        if reliability_score >= 0.9:
            strengths.append("Evidence from reliable, auditable sources")
        
        if contradiction_penalty == 0:
            strengths.append("No contradicting evidence found")
        
        return strengths
    
    def _generate_recommendation(
        self,
        status: ComplianceStatus,
        confidence: float,
        red_flags: List[str]
    ) -> str:
        """Generate auditor recommendation"""
        
        if status == ComplianceStatus.COMPLIANT:
            return "PASS: Evidence supports compliance. Ready for audit."
        
        elif status == ComplianceStatus.CONDITIONAL:
            issues = "; ".join(red_flags[:2]) if red_flags else "See details"
            return f"CONDITIONAL PASS: Address issues before audit. Issues: {issues}"
        
        elif status == ComplianceStatus.AT_RISK:
            return "AT RISK: Collect additional evidence and remediate gaps."
        
        else:  # NON_COMPLIANT
            return "FAIL: No evidence of compliance. Immediate remediation required."
    
    def _freshness_reasoning(self, evidence_list: List[Dict]) -> str:
        """Generate freshness reasoning"""
        if not evidence_list:
            return "No evidence to assess"
        
        days = [e.get('freshness_days', 999) for e in evidence_list]
        avg_days = sum(days) / len(days)
        
        if avg_days <= 7:
            return "Evidence is very recent (< 1 week)"
        elif avg_days <= 30:
            return "Evidence is recent (< 1 month)"
        elif avg_days <= 90:
            return "Evidence is moderately recent (< 3 months)"
        else:
            return f"Evidence is stale (average {avg_days:.0f} days old)"
    
    def _reliability_reasoning(self, evidence_list: List[Dict]) -> str:
        """Generate reliability reasoning"""
        types = [e.get('evidence_type', '') for e in evidence_list]
        unique_types = set(types)
        return f"Evidence from {len(unique_types)} different source types"
    
    def _review_reasoning(self, evidence_list: List[Dict]) -> str:
        """Generate review reasoning"""
        reviewed = sum(1 for e in evidence_list if e.get('review_status') == 'Approved')
        return f"{reviewed}/{len(evidence_list)} evidence items reviewed and approved"
    
    def _calculate_next_review_date(
        self,
        evidence_list: List[Dict],
        severity: str
    ) -> str:
        """Calculate when requirement should next be reviewed"""
        
        # Review frequency based on severity
        if severity == "CRITICAL":
            review_interval_days = 30  # Monthly for critical
        elif severity == "HIGH":
            review_interval_days = 60  # Quarterly
        else:
            review_interval_days = 90  # Annual for others
        
        # Consider freshness
        if evidence_list:
            most_recent_days = min(e.get('freshness_days', 999) for e in evidence_list)
            if most_recent_days < 7:
                review_interval_days = review_interval_days  # Use standard interval
            else:
                review_interval_days = max(7, review_interval_days - most_recent_days)
        
        next_review = datetime.now() + timedelta(days=review_interval_days)
        return next_review.strftime("%Y-%m-%d")


# Example usage
if __name__ == "__main__":
    engine = AuditorConfidenceEngine()
    
    evidence = [
        {
            'evidence_id': 'EV-001',
            'evidence_type': 'Encryption_Cert',
            'freshness_days': 5,
            'confidence_score': 0.95,
            'review_status': 'Approved'
        },
        {
            'evidence_id': 'EV-002',
            'evidence_type': 'Audit_Log',
            'freshness_days': 3,
            'confidence_score': 0.90,
            'review_status': 'Approved'
        }
    ]
    
    confidence = engine.calculate_confidence(
        'REQ-001',
        'Encryption keys must be rotated quarterly',
        supporting_evidence=evidence,
        requirement_severity='CRITICAL'
    )
    
    print(f"Status: {confidence.compliance_status}")
    print(f"Confidence: {confidence.confidence_percentage}")
    print(f"Audit Ready: {confidence.audit_ready}")
    print(f"Recommendation: {confidence.recommendation}")
    print(f"\nFactors:")
    for factor in confidence.factors:
        print(f"  {factor.name}: {factor.score:.0%} (weight: {factor.weight*100:.0f}%)")
