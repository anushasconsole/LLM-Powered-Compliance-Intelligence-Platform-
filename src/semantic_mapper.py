"""
Semantic Evidence Mapper

Uses embeddings (Sentence Transformers) to semantically link evidence to requirements.
Solves the problem: "Policy says X, but evidence describes Y using different words."

Example:
    mapper = SemanticEvidence Mapper()
    
    requirement = "Encryption keys must be rotated quarterly"
    evidence = "KMS master keys rotated every 365 days"
    
    similarity = mapper.similarity(requirement, evidence)  # 0.87
    
    # Batch semantic search
    top_matches = mapper.search_evidence_for_requirement(
        requirement_id="REQ-001",
        requirement_text="Encryption keys rotated annually",
        all_evidence=[...]
    )
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer = None


@dataclass
class SemanticMatch:
    """Result of semantic matching"""
    evidence_id: str
    evidence_text: str
    requirement_id: str
    requirement_text: str
    similarity_score: float  # 0-1, higher is more similar
    match_confidence: str  # HIGH, MEDIUM, LOW, NONE
    reasoning: str  # Explanation of the match


class SemanticEvidenceMapper:
    """
    Semantic evidence retrieval using embeddings.
    
    Handles the nuance of compliance language:
    - "Encryption keys rotated" vs "KMS annual key rotation"
    - "Access logs captured" vs "IAM audit trail enabled"
    - "Financial controls" vs "SOX 404 compliance"
    
    Uses Sentence Transformers for efficient semantic matching.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", use_mock: bool = False):
        """
        Initialize semantic mapper.
        
        Args:
            model_name: Sentence Transformers model (all-MiniLM-L6-v2 is lightweight)
            use_mock: If True, uses mock embeddings (for testing without GPU)
        """
        self.use_mock = use_mock
        self.model_name = model_name
        
        if not use_mock:
            if SentenceTransformer is None:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Install with: pip install sentence-transformers"
                )
            self.model = SentenceTransformer(model_name)
        else:
            self.model = None
        
        # Cache for embeddings
        self.embedding_cache = {}
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts (0-1).
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0 = dissimilar, 1 = identical)
        """
        if self.use_mock:
            return self._mock_similarity(text1, text2)
        
        try:
            embedding1 = self.encode(text1)
            embedding2 = self.encode(text2)
            
            # Cosine similarity
            similarity = util.pytorch_cos_sim(embedding1, embedding2)[0][0].item()
            return float(similarity)
        except Exception as e:
            print(f"Similarity calculation error: {e}")
            return 0.5  # Default to medium confidence
    
    def encode(self, text: str) -> np.ndarray:
        """Encode text to embedding"""
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        if self.use_mock:
            embedding = self._mock_encode(text)
        else:
            embedding = self.model.encode(text, convert_to_tensor=True)
        
        self.embedding_cache[text] = embedding
        return embedding
    
    def search_evidence_for_requirement(
        self,
        requirement_id: str,
        requirement_text: str,
        all_evidence: List[Dict],
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[SemanticMatch]:
        """
        Find evidence most relevant to a requirement.
        
        Args:
            requirement_id: Requirement ID
            requirement_text: Full requirement text
            all_evidence: List of evidence dicts with 'evidence_id' and 'description'
            top_k: Return top K matches
            threshold: Only include matches above threshold
            
        Returns:
            Sorted list of SemanticMatch objects
        """
        matches = []
        
        for evidence in all_evidence:
            evidence_id = evidence.get('evidence_id', '')
            evidence_text = evidence.get('description', '')
            
            similarity = self.similarity(requirement_text, evidence_text)
            
            if similarity >= threshold:
                confidence = self._calculate_confidence(similarity)
                reasoning = self._generate_reasoning(
                    requirement_text, evidence_text, similarity
                )
                
                match = SemanticMatch(
                    evidence_id=evidence_id,
                    evidence_text=evidence_text,
                    requirement_id=requirement_id,
                    requirement_text=requirement_text,
                    similarity_score=similarity,
                    match_confidence=confidence,
                    reasoning=reasoning
                )
                matches.append(match)
        
        # Sort by similarity (descending)
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return matches[:top_k]
    
    def batch_search(
        self,
        requirements: List[Dict],
        all_evidence: List[Dict],
        threshold: float = 0.5
    ) -> Dict[str, List[SemanticMatch]]:
        """
        Search evidence for multiple requirements efficiently.
        
        Args:
            requirements: List of {requirement_id, requirement_text}
            all_evidence: List of {evidence_id, description}
            threshold: Minimum similarity threshold
            
        Returns:
            Dict mapping requirement_id to list of SemanticMatch
        """
        results = {}
        
        for req in requirements:
            req_id = req.get('requirement_id')
            req_text = req.get('requirement_text')
            
            matches = self.search_evidence_for_requirement(
                req_id, req_text, all_evidence, threshold=threshold
            )
            results[req_id] = matches
        
        return results
    
    def find_contradictions(
        self,
        requirement_text: str,
        all_evidence: List[Dict]
    ) -> List[SemanticMatch]:
        """
        Find evidence that contradicts a requirement.
        
        Example:
            requirement: "All systems have MFA enabled"
            evidence: "System X does not have MFA"
            
            This would be found as contradiction.
        """
        contradiction_keywords = [
            "not enabled",
            "not implemented",
            "disabled",
            "failed",
            "no longer",
            "does not",
            "exception",
            "exemption",
            "bypass"
        ]
        
        contradictions = []
        
        for evidence in all_evidence:
            evidence_text = evidence.get('description', '').lower()
            
            # Check for contradiction keywords
            has_contradiction = any(
                keyword in evidence_text for keyword in contradiction_keywords
            )
            
            if has_contradiction:
                similarity = self.similarity(requirement_text, evidence.get('description', ''))
                
                # Contradictions have inverted meaning but similar topics
                if similarity > 0.6:
                    reasoning = f"Evidence describes exception/failure related to requirement"
                    match = SemanticMatch(
                        evidence_id=evidence.get('evidence_id', ''),
                        evidence_text=evidence.get('description', ''),
                        requirement_id='N/A',
                        requirement_text=requirement_text,
                        similarity_score=similarity,
                        match_confidence="HIGH",
                        reasoning=reasoning
                    )
                    contradictions.append(match)
        
        return contradictions
    
    def calculate_evidence_quality(
        self,
        evidence_dict: Dict,
        requirement_text: str
    ) -> float:
        """
        Calculate quality score for evidence w.r.t. requirement.
        
        Factors:
        - Semantic relevance (similarity score)
        - Evidence freshness (days old)
        - Evidence type appropriateness
        - Reviewer confidence
        
        Returns:
            Quality score 0-1
        """
        similarity = self.similarity(
            requirement_text,
            evidence_dict.get('description', '')
        )
        
        # Freshness factor
        freshness_days = evidence_dict.get('freshness_days', 30)
        if freshness_days <= 7:
            freshness_factor = 1.0
        elif freshness_days <= 30:
            freshness_factor = 0.9
        elif freshness_days <= 90:
            freshness_factor = 0.7
        else:
            freshness_factor = 0.4
        
        # Reviewer confidence
        confidence_score = evidence_dict.get('confidence_score', 0.5)
        
        # Combined quality
        quality = (similarity * 0.5 + freshness_factor * 0.3 + confidence_score * 0.2)
        return min(1.0, quality)
    
    def rank_evidence_by_quality(
        self,
        requirement_text: str,
        all_evidence: List[Dict]
    ) -> List[Dict]:
        """Rank evidence by quality for a requirement"""
        ranked = []
        
        for evidence in all_evidence:
            quality = self.calculate_evidence_quality(evidence, requirement_text)
            ranked.append({
                **evidence,
                'quality_score': quality
            })
        
        ranked.sort(key=lambda x: x['quality_score'], reverse=True)
        return ranked
    
    def _calculate_confidence(self, similarity: float) -> str:
        """Convert similarity to confidence level"""
        if similarity >= 0.8:
            return "HIGH"
        elif similarity >= 0.6:
            return "MEDIUM"
        elif similarity >= 0.4:
            return "LOW"
        else:
            return "NONE"
    
    def _generate_reasoning(self, requirement: str, evidence: str, similarity: float) -> str:
        """Generate human-readable explanation of match"""
        if similarity >= 0.8:
            return "Strong semantic match: requirement and evidence use similar language"
        elif similarity >= 0.6:
            return "Moderate match: evidence addresses similar concepts"
        elif similarity >= 0.4:
            return "Weak match: possible relevance but significant language differences"
        else:
            return "Insufficient match: evidence unlikely related to requirement"
    
    def _mock_similarity(self, text1: str, text2: str) -> float:
        """Mock similarity calculation for testing"""
        # Simple but effective word overlap for compliance terms
        
        # Normalize text
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # Create word sets (skip very short words)
        words1 = set(w for w in text1_lower.split() if len(w) > 2)
        words2 = set(w for w in text2_lower.split() if len(w) > 2)
        
        if not words1 or not words2:
            return 0.5
        
        # Calculate basic Jaccard similarity
        overlap = len(words1 & words2)
        union = len(words1 | words2)
        jaccard = overlap / union if union > 0 else 0
        
        # Compliance synonym matching - improve Jaccard with semantic understanding
        synonyms = {
            'encrypt': ['encryption', 'encrypted', 'aes-256', 'aes', 'kms'],
            'audit': ['logging', 'log', 'logs', 'monitor', 'monitoring', 'trail'],
            'rotate': ['rotation', 'rotated', 'quarterly', '90-day', '90', 'cycling'],
            'access': ['auth', 'authentication', 'authorized', 'control'],
            'key': ['keys', 'kms', 'hsm', 'encryption'],
            'mfa': ['multi-factor', 'factor', '2fa'],
            'fresh': ['recent', 'current', 'latest', 'up-to-date'],
            'configure': ['configuration', 'configured', 'config'],
        }
        
        # Count matching synonym groups
        semantic_score = 0
        for base, variants in synonyms.items():
            all_forms = [base] + variants
            if any(form in text1_lower for form in all_forms) and \
               any(form in text2_lower for form in all_forms):
                semantic_score += 0.05
        
        # Combine: word overlap (60%) + semantic synonyms (40%)
        combined = (jaccard * 0.6) + min(0.4, semantic_score)
        
        # Ensure minimum relevance for any text with some overlap
        if overlap > 0:
            combined = max(combined, 0.45)
        
        return min(1.0, combined)
    
    def _mock_encode(self, text: str) -> np.ndarray:
        """Mock encoding for testing"""
        # Create deterministic embedding based on text
        np.random.seed(hash(text) % 2**31)
        return np.random.randn(384)  # Standard embedding size


def create_semantic_evidence_report(
    requirements: List[Dict],
    all_evidence: List[Dict],
    mapper: SemanticEvidenceMapper
) -> Dict:
    """
    Create comprehensive semantic matching report.
    
    Returns:
        Dict with matching statistics and details
    """
    results = mapper.batch_search(requirements, all_evidence)
    
    report = {
        'total_requirements': len(requirements),
        'total_evidence': len(all_evidence),
        'matched_requirements': 0,
        'unmatched_requirements': 0,
        'total_matches': 0,
        'average_match_quality': 0.0,
        'matches_by_confidence': {
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'NONE': 0
        },
        'detailed_results': []
    }
    
    total_quality = 0
    all_matches_count = 0
    
    for req_id, matches in results.items():
        if matches:
            report['matched_requirements'] += 1
            report['total_matches'] += len(matches)
            
            for match in matches:
                report['matches_by_confidence'][match.match_confidence] += 1
                total_quality += match.similarity_score
                all_matches_count += 1
            
            report['detailed_results'].append({
                'requirement_id': req_id,
                'match_count': len(matches),
                'top_match': {
                    'evidence_id': matches[0].evidence_id,
                    'similarity': matches[0].similarity_score,
                    'confidence': matches[0].match_confidence
                } if matches else None
            })
        else:
            report['unmatched_requirements'] += 1
    
    if all_matches_count > 0:
        report['average_match_quality'] = total_quality / all_matches_count
    
    return report


# Example usage
if __name__ == "__main__":
    mapper = SemanticEvidenceMapper(use_mock=True)
    
    requirement = "Encryption keys must be rotated quarterly"
    evidence_samples = [
        {
            'evidence_id': 'EV-001',
            'description': 'AWS KMS keys rotated every quarter'
        },
        {
            'evidence_id': 'EV-002',
            'description': 'Database backup completed successfully'
        },
        {
            'evidence_id': 'EV-003',
            'description': 'Key rotation logs show 90-day rotation cycle'
        },
    ]
    
    print("Semantic Evidence Matching")
    print("=" * 60)
    print(f"Requirement: {requirement}\n")
    
    matches = mapper.search_evidence_for_requirement(
        'REQ-001',
        requirement,
        evidence_samples,
        threshold=0.0
    )
    
    for match in matches:
        print(f"Evidence: {match.evidence_id}")
        print(f"  Text: {match.evidence_text}")
        print(f"  Similarity: {match.similarity_score:.2f}")
        print(f"  Confidence: {match.match_confidence}")
        print(f"  Reasoning: {match.reasoning}")
        print()
