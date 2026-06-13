"""
Semantic Evidence Mapper
Maps evidence to requirements using keyword + synonym matching.
Includes framework-based boosting so same-framework evidence always maps.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class SemanticMatch:
    evidence_id: str
    evidence_text: str
    requirement_id: str
    requirement_text: str
    similarity_score: float
    match_confidence: str   # HIGH, MEDIUM, LOW
    reasoning: str


# Synonym groups — any word in a group matches any other word in the same group
SYNONYM_GROUPS = [
    # Encryption
    ['encrypt', 'encryption', 'encrypted', 'encrypting', 'aes', 'aes-256',
     'kms', 'cipher', 'tls', 'ssl', 'cryptograph', 'cryptographic', 'crypt'],
    # Logging / auditing
    ['audit', 'log', 'logged', 'logging', 'logs', 'trail', 'monitor',
     'monitoring', 'monitored', 'record', 'records', 'recorded', 'track', 'tracked'],
    # Access control
    ['access', 'authentication', 'authenticate', 'auth', 'iam', 'permission',
     'authorized', 'authorised', 'authorization', 'authorisation', 'control', 'identity'],
    # Key management
    ['key', 'keys', 'kms', 'hsm', 'certificate', 'cert', 'certs', 'certificates',
     'rotation', 'rotate', 'rotated', 'rotating', 'renewal', 'renew'],
    # MFA
    ['mfa', 'multi-factor', 'two-factor', '2fa', 'authenticator', 'otp',
     'multifactor', 'second-factor'],
    # Backup / recovery
    ['backup', 'backups', 'snapshot', 'snapshots', 'restore', 'restoration',
     'recovery', 'disaster', 'redundan', 'replicate', 'replication'],
    # Incident response
    ['incident', 'incidents', 'response', 'breach', 'breaches', 'alert', 'alerts',
     'notification', 'notifications', 'event', 'events'],
    # Data / PII
    ['data', 'personal', 'pii', 'sensitive', 'information', 'storage',
     'store', 'stored', 'database', 'confidential', 'private'],
    # Testing / scanning
    ['test', 'tests', 'tested', 'testing', 'scan', 'scans', 'scanning',
     'vulnerability', 'vulnerabilities', 'penetration', 'pentest', 'assessment'],
    # Policy / documentation
    ['policy', 'policies', 'procedure', 'procedures', 'document', 'documentation',
     'documented', 'standard', 'standards', 'guideline', 'guidelines', 'compliance'],
    # User / account management
    ['user', 'users', 'account', 'accounts', 'privilege', 'privileged',
     'least', 'principle', 'role', 'roles', 'rbac', 'separation', 'segregation'],
    # Network
    ['network', 'firewall', 'segmentation', 'dmz', 'perimeter', 'transit', 'transmission'],
    # Patching
    ['patch', 'patches', 'patching', 'update', 'updates', 'remediation',
     'remediate', 'fix', 'cve'],
    # Training
    ['training', 'trained', 'awareness', 'education', 'onboarding', 'educated'],
    # Reports / config
    ['report', 'reports', 'reporting', 'review', 'reviews', 'configuration',
     'config', 'configs', 'configured', 'snapshot', 'evidence', 'artifact'],
    # Retention
    ['retain', 'retention', 'retaining', 'kept', 'stored', 'preserve', 'preservation'],
    # Transit
    ['transit', 'transmission', 'transmit', 'transfer', 'sending', 'communication'],
]

# Pre-build a lookup: word → group_index
_WORD_TO_GROUP: Dict[str, int] = {}
for _gi, _grp in enumerate(SYNONYM_GROUPS):
    for _w in _grp:
        _WORD_TO_GROUP[_w] = _gi


def _tokenize(text: str) -> List[str]:
    """Lower-case, split on spaces/punctuation, filter short tokens."""
    import re
    tokens = re.split(r'[\s\-_/\\.,;:()\[\]]+', text.lower())
    return [t for t in tokens if len(t) >= 3]


def _synonym_score(tokens1: List[str], tokens2: List[str]) -> float:
    """Count how many synonym-group overlaps exist between two token lists."""
    groups1 = set(_WORD_TO_GROUP[t] for t in tokens1 if t in _WORD_TO_GROUP)
    groups2 = set(_WORD_TO_GROUP[t] for t in tokens2 if t in _WORD_TO_GROUP)
    shared = groups1 & groups2
    if not groups1 and not groups2:
        return 0.0
    union = groups1 | groups2
    return len(shared) / len(union) if union else 0.0


def _jaccard(tokens1: List[str], tokens2: List[str]) -> float:
    s1, s2 = set(tokens1), set(tokens2)
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)


def text_similarity(text1: str, text2: str) -> float:
    """
    Combined similarity: 50% Jaccard on tokens + 50% synonym-group overlap.
    Returns 0..1.
    """
    t1 = _tokenize(text1)
    t2 = _tokenize(text2)
    jac = _jaccard(t1, t2)
    syn = _synonym_score(t1, t2)
    score = jac * 0.5 + syn * 0.5
    # Boost if there is ANY synonym overlap
    if syn > 0:
        score = max(score, 0.42)
    return min(1.0, score)


class SemanticEvidenceMapper:
    """
    Evidence-to-requirement mapper.
    Primary: text similarity (synonym + jaccard).
    Fallback boost: same framework automatically gets a base score.
    """

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.model = None
        if not use_mock:
            self._try_load_transformers()

    def _try_load_transformers(self):
        try:
            from sentence_transformers import SentenceTransformer, util
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self._util = util
        except Exception:
            self.model = None

    def similarity(self, text1: str, text2: str) -> float:
        if self.model:
            try:
                e1 = self.model.encode(text1, convert_to_tensor=True)
                e2 = self.model.encode(text2, convert_to_tensor=True)
                return float(self._util.pytorch_cos_sim(e1, e2)[0][0])
            except Exception:
                pass
        return text_similarity(text1, text2)

    def search_evidence_for_requirement(
        self,
        requirement_id: str,
        requirement_text: str,
        all_evidence: List[Dict],
        top_k: int = 10,
        threshold: float = 0.20,
        requirement_framework: str = None,
    ) -> List['SemanticMatch']:
        matches = []
        for ev in all_evidence:
            ev_id = ev.get('evidence_id', '')
            ev_text = ev.get('evidence_summary', ev.get('description', ''))
            ev_framework = ev.get('framework', '')

            score = self.similarity(requirement_text, ev_text)

            # Framework match gives a guaranteed base score
            if requirement_framework and ev_framework == requirement_framework:
                score = max(score, 0.45)

            if score >= threshold:
                conf = "HIGH" if score >= 0.70 else "MEDIUM" if score >= 0.45 else "LOW"
                reasoning = (
                    "Strong semantic match"
                    if score >= 0.70
                    else "Framework match + moderate semantic overlap"
                    if score >= 0.45
                    else "Weak match: possible relevance"
                )
                matches.append(SemanticMatch(
                    evidence_id=ev_id,
                    evidence_text=ev_text,
                    requirement_id=requirement_id,
                    requirement_text=requirement_text,
                    similarity_score=round(score, 3),
                    match_confidence=conf,
                    reasoning=reasoning,
                ))

        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return matches[:top_k]

    def batch_search(
        self,
        requirements: List[Dict],
        all_evidence: List[Dict],
        threshold: float = 0.20,
    ) -> Dict[str, List['SemanticMatch']]:
        results = {}
        for req in requirements:
            req_id = req.get('requirement_id', '')
            req_text = req.get('requirement_text', req.get('description', ''))
            req_fw = req.get('framework', '')
            results[req_id] = self.search_evidence_for_requirement(
                req_id, req_text, all_evidence,
                threshold=threshold,
                requirement_framework=req_fw,
            )
        return results
