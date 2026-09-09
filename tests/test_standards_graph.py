import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.intelligence.standards_graph import StandardsGraphBuilder

client = TestClient(app)

SAMPLE_CORPUS = [
    {
        "id": "IS-101",
        "is_number": "IS 101 : 2012",
        "title": "Standard 101",
        "sector": "Electrotechnical",
        "product_category": "Lighting",
        "revision_year": 2012,
        "status": "Active (DEMO DATA)",
        "related_standards": ["IS 102 : 2015", "IS 101 : 2012"]  # Contains self-reference
    },
    {
        "id": "IS-102",
        "is_number": "IS 102 : 2015",
        "title": "Standard 102",
        "sector": "Electrotechnical",
        "product_category": "Lighting",
        "revision_year": 2015,
        "status": "Active (DEMO DATA)",
        "related_standards": ["IS-101", "NONEXISTENT-999"]  # Contains unknown reference
    },
    {
        "id": "IS-103",
        "is_number": "IS 103 : 2018",
        "title": "Standard 103",
        "sector": "Civil Engineering",
        "product_category": "Cement",
        "revision_year": 2018,
        "status": "Active (DEMO DATA)",
        "related_standards": []
    }
]


def test_1_graph_builds_successfully():
    builder = StandardsGraphBuilder()
    graph = builder.build_graph(SAMPLE_CORPUS)
    assert graph is not None
    assert builder.get_graph_stats()["is_built"] is True


def test_2_expected_number_of_nodes():
    builder = StandardsGraphBuilder()
    builder.build_graph(SAMPLE_CORPUS)
    stats = builder.get_graph_stats()
    assert stats["total_nodes"] == 3


def test_3_existing_related_standards_create_edges():
    builder = StandardsGraphBuilder()
    builder.build_graph(SAMPLE_CORPUS)
    # IS-101 declared relation to IS-102
    assert builder.graph.has_edge("IS-101", "IS-102")


def test_4_relationship_type_is_correct():
    builder = StandardsGraphBuilder()
    builder.build_graph(SAMPLE_CORPUS)
    edge_data = builder.graph.get_edge_data("IS-101", "IS-102")
    assert edge_data["relationship_type"] == "RELATED_STANDARD"
    assert edge_data["is_inferred"] is False


def test_5_node_metadata_exists():
    builder = StandardsGraphBuilder()
    builder.build_graph(SAMPLE_CORPUS)
    node_data = builder.graph.nodes["IS-101"]
    assert node_data["is_number"] == "IS 101 : 2012"
    assert node_data["title"] == "Standard 101"
    assert node_data["product_category"] == "Lighting"


def test_6_unknown_related_standard_references_do_not_crash():
    builder = StandardsGraphBuilder()
    builder.build_graph(SAMPLE_CORPUS)
    # NONEXISTENT-999 is recorded in unresolved_references without crashing
    assert len(builder.unresolved_references) >= 1
    unresolved_refs = [ref for src, ref in builder.unresolved_references]
    assert "NONEXISTENT-999" in unresolved_refs


def test_7_self_loop_behavior():
    builder = StandardsGraphBuilder()
    builder.build_graph(SAMPLE_CORPUS)
    # Self-loop from IS-101 to IS-101 should be skipped
    assert not builder.graph.has_edge("IS-101", "IS-101")


def test_8_duplicate_relationship_handling():
    builder = StandardsGraphBuilder()
    builder.build_graph(SAMPLE_CORPUS)
    # NetworkX DiGraph automatically handles edge key overwrites, edge count is strictly bounded
    assert builder.graph.number_of_edges() >= 1


def test_9_neighbor_lookup():
    builder = StandardsGraphBuilder()
    builder.build_graph(SAMPLE_CORPUS)
    neighbors = builder.get_standard_neighbors("IS-101")
    assert isinstance(neighbors, list)
    neighbor_ids = [n["standard_id"] for n in neighbors]
    assert "IS-102" in neighbor_ids


def test_10_depth_1_traversal():
    builder = StandardsGraphBuilder()
    builder.build_graph(SAMPLE_CORPUS)
    subgraph = builder.get_standard_subgraph("IS-101", depth=1)
    assert subgraph is not None
    assert subgraph["center_node"]["id"] == "IS-101"
    assert subgraph["depth"] == 1
    node_ids = [n["id"] for n in subgraph["nodes"]]
    assert "IS-101" in node_ids
    assert "IS-102" in node_ids


def test_11_depth_2_traversal():
    builder = StandardsGraphBuilder()
    builder.build_graph(SAMPLE_CORPUS)
    subgraph = builder.get_standard_subgraph("IS-101", depth=2)
    assert subgraph is not None
    assert subgraph["depth"] == 2
    assert len(subgraph["nodes"]) >= 2


def test_12_unknown_standard_returns_none():
    builder = StandardsGraphBuilder()
    builder.build_graph(SAMPLE_CORPUS)
    result = builder.get_standard_subgraph("NONEXISTENT-ID", depth=1)
    assert result is None


def test_13_graph_initialization_reusable():
    builder = StandardsGraphBuilder()
    builder.build_graph(SAMPLE_CORPUS)
    stats1 = builder.get_graph_stats()
    stats2 = builder.get_graph_stats()
    assert stats1["total_nodes"] == stats2["total_nodes"]
    assert stats1["is_built"] is True


def test_14_existing_apis_remain_functional():
    # 1. Health check
    h_res = client.get("/api/health")
    assert h_res.status_code == 200
    assert h_res.json()["status"] == "healthy"

    # 2. Network overview endpoint
    n_res = client.get("/api/standards/network")
    assert n_res.status_code == 200
    n_data = n_res.json()
    assert n_data["total_nodes"] >= 14
    assert len(n_data["nodes"]) >= 14
    assert len(n_data["edges"]) >= 1

    # 3. Subgraph endpoint for valid ID
    s_res = client.get("/api/standards/network/IS-1180-P1?depth=1")
    assert s_res.status_code == 200
    s_data = s_res.json()
    assert s_data["standard_id"] == "IS-1180-P1"

    # 4. 404 for unknown standard ID
    err_res = client.get("/api/standards/network/UNKNOWN-ID-999")
    assert err_res.status_code == 404


def test_15_recommendation_endpoint_remains_functional():
    res = client.post("/api/recommend", json={"query": "100 kVA transformer", "top_k": 3})
    assert res.status_code == 200
    data = res.json()
    assert len(data["recommendations"]) > 0
    first_item = data["recommendations"][0]
    assert "graph_relationships" in first_item
    assert isinstance(first_item["graph_relationships"], list)


def test_16_version_intelligence_remains_functional():
    a_res = client.get("/api/standards/amendments")
    assert a_res.status_code == 200
    a_data = a_res.json()
    assert a_data["total_standards"] >= 14
    assert len(a_data["items"]) >= 14
    assert "summary" in a_data["items"][0]
