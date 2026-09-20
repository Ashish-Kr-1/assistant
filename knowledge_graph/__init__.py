"""
knowledge_graph — Relational Knowledge Graph package for Charaka IP.
Enables multi-hop statutory and regulatory reasoning across Indian IP law,
AYUSH guidelines, Biological Diversity Act, TKDL, and international treaties.
"""

from knowledge_graph.schema import NodeType, EdgeType, KGNode, KGEdge
from knowledge_graph.builder import build_charak_knowledge_graph, get_knowledge_graph
from knowledge_graph.query import query_knowledge_graph

__all__ = [
    "NodeType",
    "EdgeType",
    "KGNode",
    "KGEdge",
    "build_charak_knowledge_graph",
    "get_knowledge_graph",
    "query_knowledge_graph",
]
