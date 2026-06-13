"""
Knowledge Graph Builder & Query Engine

Models relationships between:
  - Policies
  - Requirements (controls)
  - Evidence artifacts
  - Compliance frameworks
  - Responsible teams

Enables enterprise-grade compliance architecture visualization and querying.

Example:
    kg = KnowledgeGraph()
    kg.add_requirement(req)
    kg.add_evidence(evidence)
    kg.link_evidence_to_requirement(evidence_id, req_id)
    
    # Query: Show all evidence supporting GDPR
    results = kg.query_by_framework("GDPR")
"""

import networkx as nx
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class GraphNode:
    """Base node in knowledge graph"""
    node_id: str
    node_type: str  # "POLICY", "REQUIREMENT", "EVIDENCE", "FRAMEWORK", "TEAM", "CONTROL_AREA"
    name: str
    attributes: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class KnowledgeGraph:
    """
    Compliance Knowledge Graph - models enterprise compliance architecture.
    
    Node Types:
    - POLICY: Policy documents
    - REQUIREMENT: Extracted compliance requirements
    - EVIDENCE: Evidence artifacts
    - FRAMEWORK: GDPR, NIST, SOX, ISO 27001, PCI-DSS, HIPAA
    - TEAM: Responsible teams (Security, Audit, Database, etc.)
    - CONTROL_AREA: Functional areas (Encryption, Access Control, etc.)
    
    Edge Types:
    - CONTAINS: Policy contains requirements
    - REQUIRES: Requirement requires evidence
    - SUPPORTS: Evidence supports requirement
    - CONTRADICTS: Evidence contradicts requirement
    - MAPS_TO: Requirement maps to framework
    - OWNED_BY: Requirement owned by team
    - CATEGORIZED_AS: Requirement categorized as control area
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.node_lookup = {}  # Quick lookup: (type, id) -> node
        self.evidence_requirement_map = defaultdict(list)  # evidence_id -> [req_ids]
        self.framework_requirement_map = defaultdict(list)  # framework -> [req_ids]
        self.requirement_freshness_map = {}  # req_id -> freshness requirement
    
    def add_policy(self, policy_id: str, policy_name: str, version: str = "1.0") -> GraphNode:
        """Add policy node to graph"""
        node = GraphNode(
            node_id=policy_id,
            node_type="POLICY",
            name=policy_name,
            attributes={"version": version}
        )
        self.graph.add_node(policy_id, **node.__dict__)
        self.node_lookup[(policy_id, "POLICY")] = node
        return node
    
    def add_requirement(self, req_id: str, req_name: str, policy_id: str, 
                       severity: str = "MEDIUM", freshness: str = "monthly",
                       burden_of_proof: List[str] = None, **attributes) -> GraphNode:
        """Add requirement node and link to policy"""
        node = GraphNode(
            node_id=req_id,
            node_type="REQUIREMENT",
            name=req_name,
            attributes={
                "severity": severity,
                "freshness": freshness,
                "burden_of_proof": burden_of_proof or [],
                **attributes
            }
        )
        self.graph.add_node(req_id, **node.__dict__)
        self.node_lookup[(req_id, "REQUIREMENT")] = node
        
        # Link to policy
        if self.graph.has_node(policy_id):
            self.graph.add_edge(policy_id, req_id, relation="CONTAINS")
        
        # Store freshness
        self.requirement_freshness_map[req_id] = freshness
        
        return node
    
    def add_evidence(self, evidence_id: str, evidence_type: str, description: str,
                     collection_date: str, freshness_days: int, confidence: float = 0.5,
                     **attributes) -> GraphNode:
        """Add evidence node"""
        node = GraphNode(
            node_id=evidence_id,
            node_type="EVIDENCE",
            name=description,
            attributes={
                "evidence_type": evidence_type,
                "collection_date": collection_date,
                "freshness_days": freshness_days,
                "confidence": confidence,
                **attributes
            }
        )
        self.graph.add_node(evidence_id, **node.__dict__)
        self.node_lookup[(evidence_id, "EVIDENCE")] = node
        return node
    
    def add_framework(self, framework_id: str, framework_name: str) -> GraphNode:
        """Add framework node (GDPR, NIST, SOX, etc.)"""
        node = GraphNode(
            node_id=framework_id,
            node_type="FRAMEWORK",
            name=framework_name
        )
        self.graph.add_node(framework_id, **node.__dict__)
        self.node_lookup[(framework_id, "FRAMEWORK")] = node
        return node
    
    def add_team(self, team_id: str, team_name: str) -> GraphNode:
        """Add responsible team node"""
        node = GraphNode(
            node_id=team_id,
            node_type="TEAM",
            name=team_name
        )
        self.graph.add_node(team_id, **node.__dict__)
        self.node_lookup[(team_id, "TEAM")] = node
        return node
    
    def add_control_area(self, area_id: str, area_name: str) -> GraphNode:
        """Add control area node (Encryption, Access Control, Audit Logging, etc.)"""
        node = GraphNode(
            node_id=area_id,
            node_type="CONTROL_AREA",
            name=area_name
        )
        self.graph.add_node(area_id, **node.__dict__)
        self.node_lookup[(area_id, "CONTROL_AREA")] = node
        return node
    
    def link_evidence_supports(self, evidence_id: str, requirement_id: str, 
                              strength: float = 0.8) -> Tuple[str, str]:
        """Evidence supports a requirement"""
        if self.graph.has_node(evidence_id) and self.graph.has_node(requirement_id):
            self.graph.add_edge(evidence_id, requirement_id, 
                              relation="SUPPORTS", strength=strength)
            self.evidence_requirement_map[evidence_id].append(requirement_id)
        return (evidence_id, requirement_id)
    
    def link_evidence_contradicts(self, evidence_id: str, requirement_id: str,
                                 strength: float = 0.8) -> Tuple[str, str]:
        """Evidence contradicts a requirement"""
        if self.graph.has_node(evidence_id) and self.graph.has_node(requirement_id):
            self.graph.add_edge(evidence_id, requirement_id, 
                              relation="CONTRADICTS", strength=strength)
        return (evidence_id, requirement_id)
    
    def link_requirement_to_framework(self, requirement_id: str, framework_id: str):
        """Requirement maps to framework"""
        if self.graph.has_node(requirement_id) and self.graph.has_node(framework_id):
            self.graph.add_edge(requirement_id, framework_id, relation="MAPS_TO")
            self.framework_requirement_map[framework_id].append(requirement_id)
    
    def link_requirement_to_team(self, requirement_id: str, team_id: str):
        """Requirement owned by team"""
        if self.graph.has_node(requirement_id) and self.graph.has_node(team_id):
            self.graph.add_edge(requirement_id, team_id, relation="OWNED_BY")
    
    def link_requirement_to_control_area(self, requirement_id: str, area_id: str):
        """Requirement categorized as control area"""
        if self.graph.has_node(requirement_id) and self.graph.has_node(area_id):
            self.graph.add_edge(requirement_id, area_id, relation="CATEGORIZED_AS")
    
    # Query Methods
    
    def get_requirements_by_framework(self, framework_id: str) -> List[str]:
        """Get all requirements mapped to a framework"""
        return self.framework_requirement_map.get(framework_id, [])
    
    def get_evidence_for_requirement(self, requirement_id: str) -> List[Dict]:
        """Get all evidence supporting/contradicting a requirement"""
        evidence_list = []
        
        # Find all edges TO this requirement
        for source, target, data in self.graph.edges(data=True):
            if target == requirement_id and self.graph.nodes[source].get('node_type') == 'EVIDENCE':
                evidence_list.append({
                    'evidence_id': source,
                    'relation': data.get('relation', 'UNKNOWN'),
                    'strength': data.get('strength', 0.5),
                    'attributes': dict(self.graph.nodes[source])
                })
        
        return evidence_list
    
    def get_requirement_details(self, requirement_id: str) -> Dict:
        """Get comprehensive requirement details"""
        if not self.graph.has_node(requirement_id):
            return {}
        
        req_data = dict(self.graph.nodes[requirement_id])
        
        # Get supporting evidence
        supporting_evidence = [
            e for e in self.get_evidence_for_requirement(requirement_id)
            if e['relation'] == 'SUPPORTS'
        ]
        
        # Get contradicting evidence
        contradicting_evidence = [
            e for e in self.get_evidence_for_requirement(requirement_id)
            if e['relation'] == 'CONTRADICTS'
        ]
        
        # Get frameworks
        frameworks = []
        for source, target, data in self.graph.edges(data=True):
            if source == requirement_id and data.get('relation') == 'MAPS_TO':
                frameworks.append(target)
        
        # Get owning team
        team = None
        for source, target, data in self.graph.edges(data=True):
            if source == requirement_id and data.get('relation') == 'OWNED_BY':
                team = target
                break
        
        # Get control area
        control_area = None
        for source, target, data in self.graph.edges(data=True):
            if source == requirement_id and data.get('relation') == 'CATEGORIZED_AS':
                control_area = target
                break
        
        return {
            **req_data,
            'supporting_evidence': supporting_evidence,
            'contradicting_evidence': contradicting_evidence,
            'frameworks': frameworks,
            'owned_by_team': team,
            'control_area': control_area,
            'evidence_count': len(supporting_evidence),
            'contradiction_count': len(contradicting_evidence)
        }
    
    def get_stale_evidence(self, threshold_days: int = 30) -> List[Dict]:
        """Get evidence older than threshold"""
        stale = []
        for node_id, attrs in self.graph.nodes(data=True):
            if attrs.get('node_type') == 'EVIDENCE':
                freshness_days = attrs.get('attributes', {}).get('freshness_days', 0)
                if freshness_days > threshold_days:
                    stale.append({
                        'evidence_id': node_id,
                        'freshness_days': freshness_days,
                        'attributes': attrs
                    })
        return stale
    
    def get_requirements_needing_evidence(self) -> List[Dict]:
        """Get requirements with no supporting evidence"""
        lacking = []
        for node_id, attrs in self.graph.nodes(data=True):
            if attrs.get('node_type') == 'REQUIREMENT':
                evidence = self.get_evidence_for_requirement(node_id)
                supporting = [e for e in evidence if e['relation'] == 'SUPPORTS']
                if not supporting:
                    lacking.append({
                        'requirement_id': node_id,
                        'requirement_name': attrs.get('name'),
                        'attributes': attrs.get('attributes', {})
                    })
        return lacking
    
    def get_framework_coverage(self, framework_id: str) -> Dict:
        """Get compliance coverage for framework"""
        requirements = self.get_requirements_by_framework(framework_id)
        
        with_evidence = 0
        stale_evidence = 0
        low_confidence = 0
        
        for req_id in requirements:
            evidence = self.get_evidence_for_requirement(req_id)
            supporting = [e for e in evidence if e['relation'] == 'SUPPORTS']
            
            if supporting:
                with_evidence += 1
                
                # Check freshness
                for ev in supporting:
                    if ev['attributes'].get('attributes', {}).get('freshness_days', 0) > 30:
                        stale_evidence += 1
                    if ev.get('strength', 0.5) < 0.6:
                        low_confidence += 1
        
        return {
            'framework_id': framework_id,
            'total_requirements': len(requirements),
            'requirements_with_evidence': with_evidence,
            'coverage_percent': (with_evidence / len(requirements) * 100) if requirements else 0,
            'stale_evidence_count': stale_evidence,
            'low_confidence_count': low_confidence
        }
    
    def get_control_area_summary(self, area_id: str) -> Dict:
        """Get summary of control area"""
        # Find all requirements in this control area
        requirements = []
        for source, target, data in self.graph.edges(data=True):
            if target == area_id and data.get('relation') == 'CATEGORIZED_AS':
                requirements.append(source)
        
        coverage = []
        for req_id in requirements:
            evidence = self.get_evidence_for_requirement(req_id)
            supporting = [e for e in evidence if e['relation'] == 'SUPPORTS']
            coverage.append(len(supporting) > 0)
        
        return {
            'control_area_id': area_id,
            'total_requirements': len(requirements),
            'covered_requirements': sum(coverage),
            'coverage_percent': (sum(coverage) / len(requirements) * 100) if requirements else 0
        }
    
    def get_team_responsibilities(self, team_id: str) -> List[Dict]:
        """Get all requirements owned by team"""
        requirements = []
        for source, target, data in self.graph.edges(data=True):
            if target == team_id and data.get('relation') == 'OWNED_BY':
                req_details = self.get_requirement_details(source)
                requirements.append(req_details)
        return requirements
    
    def export_to_dict(self) -> Dict:
        """Export graph as dictionary for serialization"""
        nodes = {}
        edges = []
        
        for node_id, attrs in self.graph.nodes(data=True):
            nodes[node_id] = dict(attrs)
        
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                'source': source,
                'target': target,
                'relation': data.get('relation', 'UNKNOWN'),
                'attributes': dict(data)
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'node_count': len(nodes),
            'edge_count': len(edges),
            'exported_at': datetime.now().isoformat()
        }
    
    def print_summary(self):
        """Print graph summary"""
        print("=" * 60)
        print("KNOWLEDGE GRAPH SUMMARY")
        print("=" * 60)
        print(f"Total nodes: {self.graph.number_of_nodes()}")
        print(f"Total edges: {self.graph.number_of_edges()}")
        
        node_types = defaultdict(int)
        for node_id, attrs in self.graph.nodes(data=True):
            node_types[attrs.get('node_type', 'UNKNOWN')] += 1
        
        print("\nNode types:")
        for ntype, count in sorted(node_types.items()):
            print(f"  {ntype}: {count}")
        
        edge_types = defaultdict(int)
        for source, target, data in self.graph.edges(data=True):
            edge_types[data.get('relation', 'UNKNOWN')] += 1
        
        print("\nEdge types:")
        for etype, count in sorted(edge_types.items()):
            print(f"  {etype}: {count}")


# Example usage
if __name__ == "__main__":
    kg = KnowledgeGraph()
    
    # Add policy
    kg.add_policy("POL-GDPR-001", "GDPR Data Protection", "1.0")
    
    # Add frameworks
    kg.add_framework("FW-GDPR", "GDPR")
    kg.add_framework("FW-NIST", "NIST")
    
    # Add teams
    kg.add_team("TEAM-SEC", "Security Team")
    kg.add_team("TEAM-AUDIT", "Audit Team")
    
    # Add control areas
    kg.add_control_area("CTRL-ENC", "Encryption")
    kg.add_control_area("CTRL-AUDIT", "Audit Logging")
    
    # Add requirements
    kg.add_requirement(
        "REQ-001",
        "Encryption at Rest",
        "POL-GDPR-001",
        severity="CRITICAL",
        freshness="quarterly",
        burden_of_proof=["AES-256 encryption enabled", "Keys rotated quarterly"]
    )
    
    kg.add_requirement(
        "REQ-002",
        "Access Logging",
        "POL-GDPR-001",
        severity="CRITICAL",
        freshness="continuous"
    )
    
    # Add evidence
    kg.add_evidence(
        "EV-001",
        "Encryption Certificate",
        "AWS KMS Configuration",
        "2026-04-15",
        freshness_days=5,
        confidence=0.95
    )
    
    # Link them
    kg.link_requirement_to_framework("REQ-001", "FW-GDPR")
    kg.link_requirement_to_team("REQ-001", "TEAM-SEC")
    kg.link_requirement_to_control_area("REQ-001", "CTRL-ENC")
    kg.link_evidence_supports("EV-001", "REQ-001", strength=0.95)
    
    kg.print_summary()
    
    # Query examples
    print("\n" + "=" * 60)
    print("SAMPLE QUERIES")
    print("=" * 60)
    
    req_details = kg.get_requirement_details("REQ-001")
    print(f"\nRequirement REQ-001 has {req_details['evidence_count']} supporting evidence items")
    print(f"Coverage: {req_details}")
