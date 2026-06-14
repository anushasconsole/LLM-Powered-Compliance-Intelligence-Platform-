"""
Evidence Collection Integrations
Mock implementations for CloudTrail, AWS Config, Splunk, and other sources
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


class CloudTrailIntegration:
    """
    Mock AWS CloudTrail integration for collecting audit logs.
    In production, would use boto3 to query CloudTrail API.
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.event_types = [
            'PutObject', 'GetObject', 'DeleteObject',
            'CreateKey', 'RotateKey', 'DisableKey',
            'StartInstances', 'StopInstances', 'TerminateInstances',
            'CreateUser', 'DeleteUser', 'AttachUserPolicy',
            'PutBucketEncryption', 'PutBucketLogging'
        ]
    
    def collect_evidence(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Collect CloudTrail events for the last N days.
        Returns mock evidence artifacts.
        """
        evidence_list = []
        
        for i in range(random.randint(10, 30)):
            event_time = datetime.now() - timedelta(days=random.randint(0, days))
            event_name = random.choice(self.event_types)
            
            # Determine framework based on event type
            if 'Key' in event_name or 'Encryption' in event_name:
                framework = random.choice(['GDPR', 'NIST', 'PCI-DSS'])
                req_id = 'REQ-ENC-001'
            elif 'User' in event_name or 'Policy' in event_name:
                framework = random.choice(['SOX', 'ISO27001'])
                req_id = 'REQ-AC-001'
            else:
                framework = random.choice(['NIST', 'HIPAA'])
                req_id = 'REQ-AUD-001'
            
            evidence = {
                'evidence_id': f'EVD-CT-{i:04d}',
                'requirement_id': req_id,
                'requirement_description': f'CloudTrail event: {event_name}',
                'framework': framework,
                'evidence_type': 'CloudTrail',
                'confidence_score': random.uniform(0.75, 0.95),
                'freshness_days': (datetime.now() - event_time).days,
                'status': 'Verified',
                'collected_by': 'CloudTrail Collector',
                'collection_date': event_time.strftime('%Y-%m-%d %H:%M:%S'),
                'evidence_summary': f'CloudTrail event: {event_name} in {self.region}',
                'source_system': f'AWS CloudTrail ({self.region})',
                'anomaly_marker': ''
            }
            
            evidence_list.append(evidence)
        
        return evidence_list


class AWSConfigIntegration:
    """
    Mock AWS Config integration for collecting configuration snapshots.
    In production, would use boto3 to query AWS Config API.
    """
    
    def __init__(self):
        self.config_rules = [
            'encrypted-volumes',
            's3-bucket-public-read-prohibited',
            'rds-encryption-enabled',
            'iam-password-policy',
            'cloudtrail-enabled',
            'mfa-enabled-for-iam-console-access'
        ]
    
    def collect_evidence(self) -> List[Dict[str, Any]]:
        """
        Collect AWS Config rule compliance status.
        Returns mock evidence artifacts.
        """
        evidence_list = []
        
        for i, rule in enumerate(self.config_rules):
            compliant = random.choice([True, True, True, False])  # 75% compliant
            
            # Map rule to framework
            if 'encrypt' in rule:
                framework = random.choice(['GDPR', 'HIPAA', 'PCI-DSS'])
                req_id = 'REQ-ENC-001'
            elif 'iam' in rule or 'mfa' in rule:
                framework = random.choice(['SOX', 'NIST'])
                req_id = 'REQ-AC-001'
            else:
                framework = random.choice(['ISO27001', 'NIST'])
                req_id = 'REQ-AUD-001'
            
            evidence = {
                'evidence_id': f'EVD-CFG-{i:04d}',
                'requirement_id': req_id,
                'requirement_description': f'AWS Config rule: {rule}',
                'framework': framework,
                'evidence_type': 'Config',
                'confidence_score': 0.90 if compliant else 0.40,
                'freshness_days': random.randint(1, 7),
                'status': 'Verified' if compliant else 'Rejected',
                'collected_by': 'AWS Config Collector',
                'collection_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'evidence_summary': f'Config rule "{rule}" status: {"COMPLIANT" if compliant else "NON_COMPLIANT"}',
                'source_system': 'AWS Config',
                'anomaly_marker': '' if compliant else 'non_compliant'
            }
            
            evidence_list.append(evidence)
        
        return evidence_list


class SplunkIntegration:
    """
    Mock Splunk integration for collecting security logs.
    In production, would use Splunk SDK to query Splunk API.
    """
    
    def __init__(self, splunk_host: str = 'splunk.company.com'):
        self.splunk_host = splunk_host
        self.log_sources = [
            'firewall_logs',
            'authentication_logs',
            'database_audit_logs',
            'application_logs',
            'network_traffic_logs'
        ]
    
    def collect_evidence(self, query: str = '*', days: int = 7) -> List[Dict[str, Any]]:
        """
        Collect evidence from Splunk logs.
        Returns mock evidence artifacts.
        """
        evidence_list = []
        
        for i in range(random.randint(15, 25)):
            source = random.choice(self.log_sources)
            log_time = datetime.now() - timedelta(days=random.randint(0, days))
            
            # Determine framework based on log source
            if 'auth' in source or 'database' in source:
                framework = random.choice(['SOX', 'HIPAA', 'GDPR'])
                req_id = 'REQ-AC-001'
            elif 'firewall' in source or 'network' in source:
                framework = random.choice(['NIST', 'PCI-DSS'])
                req_id = 'REQ-AUD-001'
            else:
                framework = random.choice(['ISO27001', 'NIST'])
                req_id = 'REQ-AUD-001'
            
            evidence = {
                'evidence_id': f'EVD-SPL-{i:04d}',
                'requirement_id': req_id,
                'requirement_description': f'Splunk log from {source}',
                'framework': framework,
                'evidence_type': 'Log',
                'confidence_score': random.uniform(0.70, 0.92),
                'freshness_days': (datetime.now() - log_time).days,
                'status': random.choice(['Verified', 'Verified', 'Pending']),
                'collected_by': 'Splunk Collector',
                'collection_date': log_time.strftime('%Y-%m-%d %H:%M:%S'),
                'evidence_summary': f'Log events from {source}: {random.randint(100, 5000)} events',
                'source_system': f'Splunk ({self.splunk_host})',
                'anomaly_marker': ''
            }
            
            evidence_list.append(evidence)
        
        return evidence_list


class VendorCertificationIntegration:
    """
    Mock integration for collecting third-party vendor certifications.
    In production, would fetch from vendor APIs or certification databases.
    """
    
    def __init__(self):
        self.vendors = [
            ('AWS', 'SOC 2 Type II'),
            ('Azure', 'ISO 27001'),
            ('Okta', 'SOC 2 Type II'),
            ('Salesforce', 'HIPAA BAA'),
            ('Snowflake', 'HIPAA Compliant'),
            ('Datadog', 'SOC 2 Type II')
        ]
    
    def collect_evidence(self) -> List[Dict[str, Any]]:
        """
        Collect vendor certification evidence.
        Returns mock evidence artifacts.
        """
        evidence_list = []
        
        for i, (vendor, cert) in enumerate(self.vendors):
            # Determine framework
            if 'HIPAA' in cert:
                framework = 'HIPAA'
                req_id = 'REQ-HIPAA-001'
            elif 'ISO' in cert:
                framework = 'ISO27001'
                req_id = 'REQ-ISO-001'
            elif 'SOC' in cert:
                framework = random.choice(['SOX', 'NIST'])
                req_id = 'REQ-SOX-001'
            else:
                framework = 'NIST'
                req_id = 'REQ-NIST-001'
            
            # Certificates are typically valid for 1-2 years
            issue_days_ago = random.randint(30, 365)
            expiry_days = random.randint(365 - issue_days_ago, 730 - issue_days_ago)
            
            evidence = {
                'evidence_id': f'EVD-CERT-{i:04d}',
                'requirement_id': req_id,
                'requirement_description': f'Vendor certification: {vendor} - {cert}',
                'framework': framework,
                'evidence_type': 'Cert',
                'confidence_score': 0.95,  # Certifications are high confidence
                'freshness_days': issue_days_ago,
                'status': 'Verified' if expiry_days > 30 else 'Pending',
                'collected_by': 'Certification Collector',
                'collection_date': (datetime.now() - timedelta(days=issue_days_ago)).strftime('%Y-%m-%d %H:%M:%S'),
                'evidence_summary': f'{vendor} holds {cert} certification (expires in {expiry_days} days)',
                'source_system': f'{vendor} Certification Portal',
                'anomaly_marker': '' if expiry_days > 30 else 'expiring_soon'
            }
            
            evidence_list.append(evidence)
        
        return evidence_list


class EvidenceCollectorOrchestrator:
    """
    Orchestrates evidence collection from multiple sources.
    """
    
    def __init__(self):
        self.cloudtrail = CloudTrailIntegration()
        self.aws_config = AWSConfigIntegration()
        self.splunk = SplunkIntegration()
        self.vendor_certs = VendorCertificationIntegration()
    
    def collect_all_evidence(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect evidence from all integrated sources.
        Returns dictionary with evidence by source.
        """
        print("🔄 Collecting evidence from all sources...")
        
        evidence_by_source = {}
        
        print("   📊 Collecting from CloudTrail...")
        evidence_by_source['cloudtrail'] = self.cloudtrail.collect_evidence(days=7)
        
        print("   📊 Collecting from AWS Config...")
        evidence_by_source['aws_config'] = self.aws_config.collect_evidence()
        
        print("   📊 Collecting from Splunk...")
        evidence_by_source['splunk'] = self.splunk.collect_evidence(days=7)
        
        print("   📊 Collecting from Vendor Certifications...")
        evidence_by_source['vendor_certs'] = self.vendor_certs.collect_evidence()
        
        total = sum(len(evs) for evs in evidence_by_source.values())
        print(f"✅ Collected {total} evidence artifacts from {len(evidence_by_source)} sources")
        
        return evidence_by_source
    
    def get_all_evidence_flat(self) -> List[Dict[str, Any]]:
        """
        Get all evidence as a flat list.
        """
        evidence_by_source = self.collect_all_evidence()
        
        all_evidence = []
        for source, evidence_list in evidence_by_source.items():
            all_evidence.extend(evidence_list)
        
        return all_evidence


def demo_integrations():
    """Demo the evidence collection integrations"""
    
    print("\n" + "="*70)
    print(" EVIDENCE COLLECTION INTEGRATIONS DEMO")
    print("="*70 + "\n")
    
    orchestrator = EvidenceCollectorOrchestrator()
    evidence_by_source = orchestrator.collect_all_evidence()
    
    print("\n📊 Evidence Summary by Source:")
    print("-" * 70)
    
    for source, evidence_list in evidence_by_source.items():
        print(f"\n{source.upper()}:")
        print(f"  • Count: {len(evidence_list)}")
        
        if evidence_list:
            frameworks = set(e['framework'] for e in evidence_list)
            print(f"  • Frameworks: {', '.join(frameworks)}")
            
            verified = sum(1 for e in evidence_list if e['status'] == 'Verified')
            print(f"  • Verified: {verified}/{len(evidence_list)} ({verified/len(evidence_list):.1%})")
            
            avg_confidence = sum(e['confidence_score'] for e in evidence_list) / len(evidence_list)
            print(f"  • Avg Confidence: {avg_confidence:.1%}")
            
            print(f"  • Sample: {evidence_list[0]['evidence_summary'][:60]}...")
    
    print("\n" + "="*70)
    print(f"✅ Total Evidence Collected: {sum(len(e) for e in evidence_by_source.values())}")
    print("="*70 + "\n")


if __name__ == '__main__':
    demo_integrations()
