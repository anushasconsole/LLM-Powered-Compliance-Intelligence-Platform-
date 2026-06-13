# Option A: Quick Start Guide

## What Is Option A?

**LLM-Powered Compliance Intelligence Platform** — An enterprise-grade system that:
1. **Understands** policies using LLM (not rules)
2. **Maps** evidence semantically (not keywords)
3. **Scores** confidence intelligently (not binary)
4. **Generates** audit narratives (not checklists)
5. **Answers** compliance questions (copilot interface)

---

## Installation (5 minutes)

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key (optional - uses mock mode by default)
export OPENAI_API_KEY="sk-your-api-key"

# Run demo
python solution_option_a.py
```

---

## Core Features At a Glance

### 1. LLM Policy Extraction
```python
from src.llm_requirement_extractor import LLMRequirementExtractor

extractor = LLMRequirementExtractor(use_mock=True)

# Parse policy
policy_text = "All data must be encrypted at rest..."
requirements = extractor.extract_requirements(policy)

# Output: Structured requirements with frameworks, controls, burden of proof
```

### 2. Knowledge Graph
```python
from src.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()

# Build relationships
kg.add_policy("POL-001", "Data Protection")
kg.add_requirement("REQ-001", "Encryption at Rest", "POL-001")
kg.add_evidence("EV-001", "AWS KMS Config", ...)
kg.link_evidence_supports("EV-001", "REQ-001", strength=0.95)

# Query
requirements = kg.get_requirements_by_framework("FW-GDPR")
evidence = kg.get_evidence_for_requirement("REQ-001")
coverage = kg.get_framework_coverage("FW-GDPR")
```

### 3. Semantic Evidence Mapping
```python
from src.semantic_mapper import SemanticEvidenceMapper

mapper = SemanticEvidenceMapper(use_mock=True)

requirement = "Encryption keys rotated quarterly"
evidence_list = [
    {"description": "KMS keys rotated every 90 days"},  # ✅ MATCH
    {"description": "Backup completed"},                 # ❌ NO MATCH
]

matches = mapper.search_evidence_for_requirement(
    "REQ-001", requirement, evidence_list
)
# Returns: [{similarity: 0.87, confidence: "HIGH", ...}]
```

### 4. Auditor Confidence Scoring
```python
from src.confidence_engine import AuditorConfidenceEngine

engine = AuditorConfidenceEngine()

confidence = engine.calculate_confidence(
    "REQ-001",
    "Encryption at Rest",
    supporting_evidence=[...],  # 3 recent, high-quality artifacts
    requirement_severity="CRITICAL"
)

print(confidence.compliance_status)      # COMPLIANT
print(confidence.confidence_percentage)  # 87%
print(confidence.recommendation)         # "PASS FOR AUDIT"
```

### 5. LLM Narrative Generation
```python
from src.enhanced_narrative_generator import EnhancedNarrativeGenerator

generator = EnhancedNarrativeGenerator(use_mock=True)

narrative = generator.generate_narrative(
    requirement_id="REQ-001",
    requirement_text="Encryption at Rest",
    supporting_evidence=[...],
    confidence_score=0.87,
    frameworks=["GDPR", "NIST"]
)

print(narrative.executive_summary)  # "PASS: Organization demonstrates..."
print(narrative.detailed_narrative) # Full audit-ready narrative
print(narrative.recommendation)     # "PASS FOR AUDIT"
```

### 6. Compliance Copilot
```python
from src.compliance_copilot import ComplianceCopilot

copilot = ComplianceCopilot(kg, mapper, engine)

# Ask questions
response = copilot.query("Show GDPR compliance status")
print(response.answer)  # "GDPR: 47/50 requirements with evidence (94%)"

response = copilot.query("Which requirements are missing evidence?")
print(response.answer)  # Lists 3 requirements needing documentation
```

### 7. Complete Platform Integration
```python
from src.compliance_platform import ComplianceIntelligencePlatform

# Initialize
platform = ComplianceIntelligencePlatform(use_mock=True)

# Load and process
policies = platform.load_policies_from_files('policies/')
requirements = platform.extract_requirements_from_policies(policies)
platform.load_evidence(evidence_list)
kg = platform.build_knowledge_graph()
assessments = platform.assess_compliance()
narratives = platform.generate_narratives()

# Query
response = platform.query_compliance("Show GDPR status")

# Report
report = platform.generate_audit_report()
platform.export_report_json(report, "audit_report.json")
platform.print_report_summary(report)
```

---

## Example: End-to-End Workflow

### Step 1: Define Policies
```python
from src.llm_requirement_extractor import PolicyDocument

policies = [
    PolicyDocument(
        policy_id="POL-SEC-001",
        policy_name="Encryption Policy",
        version="1.0",
        extracted_text="All data must be encrypted at rest using AES-256..."
    )
]
```

### Step 2: Load Evidence
```python
evidence = [
    {
        'evidence_id': 'EV-001',
        'evidence_type': 'Configuration_Snapshot',
        'description': 'AWS KMS configured with AES-256',
        'collection_date': '2026-04-13',
        'freshness_days': 2,
        'confidence_score': 0.95
    }
]
```

### Step 3: Process with Platform
```python
from src.compliance_platform import ComplianceIntelligencePlatform

platform = ComplianceIntelligencePlatform(use_mock=True)

# Extract requirements
for policy in policies:
    platform.policies[policy.policy_id] = policy
extracted_reqs = platform.extract_requirements_from_policies(policies)

# Link evidence
platform.load_evidence(evidence)
kg = platform.build_knowledge_graph()

# Assess
assessments = platform.assess_compliance()
narratives = platform.generate_narratives()

# Report
report = platform.generate_audit_report()
```

### Step 4: Query & Report
```python
# Query
response = platform.query_compliance("Show evidence for encryption")
print(response['summary'])  # "Found evidence for Encryption"

# Export
platform.export_report_json(report, "reports/audit_report.json")
platform.print_report_summary(report)
```

---

## Understanding the Output

### Confidence Score Example
```
Requirement: "Encryption keys must be rotated quarterly"
Status: COMPLIANT
Confidence: 87%

Breakdown:
  - Evidence Freshness: 90% (2 days old)
  - Evidence Count: 100% (3 sources)
  - Source Reliability: 95% (Encryption certs + logs)
  - Review Status: 100% (all approved)
  - Semantic Quality: 92% (strong matches)

Recommendation: PASS FOR AUDIT
```

### Knowledge Graph Query Example
```python
kg.get_framework_coverage("FW-GDPR")
# Returns:
# {
#   'framework_id': 'FW-GDPR',
#   'total_requirements': 50,
#   'requirements_with_evidence': 45,
#   'coverage_percent': 90%
# }
```

### Copilot Query Example
```
User: "Which requirements are missing evidence?"
Copilot: "Found 5 requirements without documentation:
  1. Access logging for payment systems
  2. Incident response testing
  3. Third-party vendor assessments
  4. Data retention policy review
  5. Exception handling procedures"
```

---

## Key Concepts

### Burden of Proof
Each requirement is decomposed into specific proof obligations:
```
Requirement: "Encryption keys rotated quarterly"

Burden of Proof:
  ✓ Encryption algorithm specified
  ✓ Key rotation frequency defined (quarterly)
  ✓ Rotation logs maintained
  ✓ Audit trail non-repudiable
```

### Semantic Matching
Matches evidence even when wording differs:
```
Requirement: "Keys must be rotated quarterly"
Evidence 1: "KMS keys rotated every 90 days"        ✅ 92% match
Evidence 2: "Annual key rotation policy"             ❌ 15% match
Evidence 3: "90-day rotation cycle configured"       ✅ 95% match
```

### Multi-Framework Correlation
One control supports multiple frameworks:
```
Control: "AES-256 Encryption"
  ├─ GDPR Article 32 (Security of processing)
  ├─ NIST SC-7 (Boundary Protection)
  ├─ PCI-DSS Requirement 3.6
  └─ ISO 27001 A.10.2.1
```

---

## Configuration

### Environment Variables
```bash
export OPENAI_API_KEY="sk-..."        # For LLM features
export USE_MOCK_MODE="true"           # Test without API
export LOG_LEVEL="DEBUG"              # Verbose logging
```

### Platform Configuration
```python
config = {
    'semantic_model': 'all-MiniLM-L6-v2',  # Embeddings model
    'freshness_threshold_days': 30,         # Evidence staleness
    'confidence_min': 0.6,                  # Minimum audit confidence
    'batch_size': 100                       # Processing batch size
}

platform = ComplianceIntelligencePlatform(config=config)
```

---

## Troubleshooting

### "OpenAI API Error"
→ Use `use_mock=True` for testing without API key

### "ImportError: sentence_transformers"
→ Run `pip install sentence-transformers`

### "Knowledge graph has 0 nodes"
→ Ensure policies and evidence are loaded before building graph

### "Semantic mapper returns low scores"
→ Check evidence descriptions are descriptive (min 10 words)

---

## Performance Tips

1. **Batch Processing**: Process multiple policies together
```python
policies = platform.load_policies_from_files('policies/')
requirements = platform.extract_requirements_from_policies(policies)
```

2. **Cache Embeddings**: Reuse semantic embeddings
```python
mapper = SemanticEvidenceMapper()
# mapper caches embeddings automatically
```

3. **Limit Evidence**: Focus on recent evidence
```python
fresh_evidence = [e for e in evidence if e['freshness_days'] < 30]
```

4. **Parallel Queries**: Process requirements in parallel
```python
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=4)
```

---

## Real-World Integration

### Connect to CloudTrail
```python
import boto3

cloudtrail = boto3.client('cloudtrail')
events = cloudtrail.lookup_events(MaxResults=100)

evidence = []
for event in events['Events']:
    evidence.append({
        'evidence_id': event['EventID'],
        'evidence_type': 'Audit_Log',
        'description': event['CloudTrailEvent'],
        'collection_date': event['EventTime'].isoformat(),
        'freshness_days': (datetime.now() - event['EventTime']).days
    })

platform.load_evidence(evidence)
```

### Export to PDF
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def export_pdf(report, filepath):
    c = canvas.Canvas(filepath, pagesize=letter)
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Compliance Audit Report")
    
    # Summary
    c.setFont("Helvetica", 10)
    summary = report['executive_summary']
    c.drawString(50, 700, f"Compliance: {summary['compliance_percentage']:.0f}%")
    
    c.save()

export_pdf(report, "audit_report.pdf")
```

---

## Next Steps

1. **Run the demo**: `python solution_option_a.py`
2. **Explore modules**: Check `src/` directory
3. **Read architecture**: See `OPTION_A_ARCHITECTURE.md`
4. **Build custom queries**: Extend `compliance_copilot.py`
5. **Connect real data**: Integrate with CloudTrail, Splunk, etc.

---

## Questions?

- **Architecture**: See `OPTION_A_ARCHITECTURE.md`
- **API Docs**: Check docstrings in each module
- **Examples**: Run `solution_option_a.py` for full demo
- **Testing**: Use `use_mock=True` to test without API keys

---

## Success Metrics

After implementing Option A, you should achieve:
- ✅ 90%+ requirements with evidence
- ✅ <15 min report generation
- ✅ <7 days average evidence freshness
- ✅ 4.5+/5 auditor confidence rating
- ✅ 70%+ automation rate

---

**Ready to build enterprise compliance intelligence? Let's go! 🚀**
