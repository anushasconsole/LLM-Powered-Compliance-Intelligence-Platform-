"""
Knowledge Graph Builder & Query Engine
Models relationships between Policies, Requirements, Evidence, Frameworks, Teams.
"""

from typing import List, Dict, Optional, Set
from datetime import datetime
from collections import defaultdict

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False


class KnowledgeGraph:
    def __init__(self):
        if HAS_NX:
            self.graph = nx.DiGraph()
        else:
            self.graph = None
        self._nodes: Dict[str, Dict] = {}
        self._edges: List[Dict] = []
        self.evidence_requirement_map: Dict[str, List[str]] = defaultdict(list)
        self.framework_requirement_map: Dict[str, List[str]] = defaultdict(list)
        self.requirement_evidence_map: Dict[str, List[Dict]] = defaultdict(list)

    def _add_node(self, node_id: str, node_type: str, name: str, **attrs):
        self._nodes[node_id] = {"node_id": node_id, "node_type": node_type, "name": name, **attrs}
        if HAS_NX:
            self.graph.add_node(node_id, node_type=node_type, name=name, **attrs)

    def _add_edge(self, src: str, dst: str, relation: str, **attrs):
        self._edges.append({"source": src, "target": dst, "relation": relation, **attrs})
        if HAS_NX:
            self.graph.add_edge(src, dst, relation=relation, **attrs)

    def add_policy(self, policy_id: str, policy_name: str, version: str = "1.0"):
        self._add_node(policy_id, "POLICY", policy_name, version=version)

    def add_requirement(self, req_id: str, req_name: str, policy_id: str,
                        control_area: str = "", responsible_team: str = "",
                        severity: str = "MEDIUM", freshness: str = "monthly",
                        burden_of_proof: List[str] = None, **attrs):
        self._add_node(req_id, "REQUIREMENT", req_name,
                       control_area=control_area, responsible_team=responsible_team,
                       severity=severity, freshness=freshness,
                       burden_of_proof=burden_of_proof or [], **attrs)
        if policy_id in self._nodes:
            self._add_edge(policy_id, req_id, "CONTAINS")

    def add_evidence(self, evidence_id: str, description: str, source: str,
                     collection_date: str, freshness_days: int = 30,
                     confidence: float = 0.5, evidence_type: str = "Unknown",
                     status: str = "Approved", **attrs):
        self._add_node(evidence_id, "EVIDENCE", description,
                       evidence_type=evidence_type, collection_date=collection_date,
                       freshness_days=freshness_days, confidence=confidence,
                       status=status, source=source, **attrs)

    def add_framework(self, framework_id: str, framework_name: str = ""):
        self._add_node(framework_id, "FRAMEWORK", framework_name or framework_id)

    def add_team(self, team_id: str, team_name: str):
        self._add_node(team_id, "TEAM", team_name)

    def add_control_area(self, area_id: str, area_name: str):
        self._add_node(area_id, "CONTROL_AREA", area_name)

    def link_evidence_supports(self, evidence_id: str, requirement_id: str, strength: float = 0.8):
        if evidence_id in self._nodes and requirement_id in self._nodes:
            self._add_edge(evidence_id, requirement_id, "SUPPORTS", strength=strength)
            self.evidence_requirement_map[evidence_id].append(requirement_id)
            self.requirement_evidence_map[requirement_id].append({
                "evidence_id": evidence_id,
                "relation": "SUPPORTS",
                "strength": strength,
                "attributes": self._nodes[evidence_id]
            })

    def link_requirement_to_framework(self, requirement_id: str, framework_id: str):
        if requirement_id in self._nodes and framework_id in self._nodes:
            self._add_edge(requirement_id, framework_id, "MAPS_TO")
            self.framework_requirement_map[framework_id].append(requirement_id)

    def link_requirement_to_team(self, requirement_id: str, team_id: str):
        if requirement_id in self._nodes and team_id in self._nodes:
            self._add_edge(requirement_id, team_id, "OWNED_BY")

    def link_requirement_to_control_area(self, requirement_id: str, area_id: str):
        if requirement_id in self._nodes and area_id in self._nodes:
            self._add_edge(requirement_id, area_id, "CATEGORIZED_AS")

    def get_requirements_by_framework(self, framework_id: str) -> List[str]:
        return list(set(self.framework_requirement_map.get(framework_id, [])))

    def get_evidence_for_requirement(self, requirement_id: str) -> List[Dict]:
        return self.requirement_evidence_map.get(requirement_id, [])

    def get_requirement_details(self, requirement_id: str) -> Dict:
        node = self._nodes.get(requirement_id, {})
        supporting = self.get_evidence_for_requirement(requirement_id)
        frameworks = [e["target"] for e in self._edges
                      if e["source"] == requirement_id and e["relation"] == "MAPS_TO"]
        team = next((e["target"] for e in self._edges
                     if e["source"] == requirement_id and e["relation"] == "OWNED_BY"), None)
        return {
            **node,
            "supporting_evidence": supporting,
            "frameworks": frameworks,
            "owned_by_team": team,
            "evidence_count": len(supporting),
        }

    def get_requirements_needing_evidence(self) -> List[Dict]:
        result = []
        for nid, attrs in self._nodes.items():
            if attrs.get("node_type") == "REQUIREMENT":
                evids = self.get_evidence_for_requirement(nid)
                supporting = [e for e in evids if e["relation"] == "SUPPORTS"]
                if not supporting:
                    result.append({"requirement_id": nid, "requirement_name": attrs.get("name"), "attributes": attrs})
        return result

    def get_stale_evidence(self, threshold_days: int = 30) -> List[Dict]:
        result = []
        for nid, attrs in self._nodes.items():
            if attrs.get("node_type") == "EVIDENCE":
                if attrs.get("freshness_days", 0) > threshold_days:
                    result.append({"evidence_id": nid, **attrs})
        return result

    def get_framework_coverage(self, framework_id: str) -> Dict:
        requirements = self.get_requirements_by_framework(framework_id)
        covered = 0
        stale = 0
        low_conf = 0
        for req_id in requirements:
            evids = self.get_evidence_for_requirement(req_id)
            supporting = [e for e in evids if e["relation"] == "SUPPORTS"]
            if supporting:
                covered += 1
                for ev in supporting:
                    if ev["attributes"].get("freshness_days", 0) > 30:
                        stale += 1
                    if ev.get("strength", 0.5) < 0.6:
                        low_conf += 1
        return {
            "framework_id": framework_id,
            "total_requirements": len(requirements),
            "requirements_with_evidence": covered,
            "coverage_percent": round(covered / len(requirements) * 100, 1) if requirements else 0,
            "stale_evidence_count": stale,
            "low_confidence_count": low_conf,
        }

    def export_for_visualization(self) -> Dict:
        nodes = []
        for nid, attrs in self._nodes.items():
            nodes.append({"id": nid, **attrs})
        edges = [{"from": e["source"], "to": e["target"], "relation": e["relation"]}
                 for e in self._edges]
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "requirements": sum(1 for n in nodes if n.get("node_type") == "REQUIREMENT"),
                "evidence": sum(1 for n in nodes if n.get("node_type") == "EVIDENCE"),
                "frameworks": sum(1 for n in nodes if n.get("node_type") == "FRAMEWORK"),
            }
        }

    def get_summary(self) -> Dict:
        type_counts = defaultdict(int)
        for attrs in self._nodes.values():
            type_counts[attrs.get("node_type", "UNKNOWN")] += 1
        edge_counts = defaultdict(int)
        for e in self._edges:
            edge_counts[e.get("relation", "UNKNOWN")] += 1
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "node_types": dict(type_counts),
            "edge_types": dict(edge_counts),
        }
