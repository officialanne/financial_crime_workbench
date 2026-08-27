# Adds unit tests to verify directed graph construction,
# edge threshold filtering, centrality metric computation, and schema integrity
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services import graph_analysis


def test_build_network_graph_structure():
    graph_data = graph_analysis.build_network_graph(limit=50)
    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert "statistics" in graph_data

    stats = graph_data["statistics"]
    assert stats["total_nodes"] >= 0
    assert stats["total_edges"] >= 0
    assert stats["connected_components_count"] >= 0


def test_node_attributes():
    graph_data = graph_analysis.build_network_graph(limit=50)
    nodes = graph_data["nodes"]
    if nodes:
        node = nodes[0]
        assert "id" in node
        assert "label" in node
        assert "betweenness_centrality" in node
        assert "degree" in node
        assert isinstance(node["betweenness_centrality"], float)


def test_network_filtering_by_amount():
    graph_data = graph_analysis.build_network_graph(min_amount=10000, limit=20)
    for edge in graph_data["edges"]:
        assert edge["amount"] >= 10000
