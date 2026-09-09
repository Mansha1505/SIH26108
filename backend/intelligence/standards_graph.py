from typing import Dict, Any, List, Optional, Set, Tuple
import networkx as nx
from backend.utils.logger import get_logger

logger = get_logger("StandardsGraph")


class StandardsGraphBuilder:
    """
    Deterministic Knowledge Graph / Standards Network builder using NetworkX.
    Operates on structured Indian Standards metadata.
    
    IMPORTANT DATA HONESTY:
    - This is NOT a complete BIS normative reference graph.
    - Edges are clearly categorized as Declared (RELATED_STANDARD) or Inferred (SAME_PRODUCT_CATEGORY).
    - Prevents self-loops and handles unresolved references safely.
    - Reusable singleton graph built once during application lifecycle.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.standards_map: Dict[str, Dict[str, Any]] = {}
        self.id_lookup: Dict[str, str] = {}
        self._is_built = False
        self.unresolved_references: List[Tuple[str, str]] = []
        self.declared_edge_count = 0
        self.inferred_edge_count = 0

    def build_graph(self, standards: List[Dict[str, Any]]) -> nx.DiGraph:
        """
        Builds the NetworkX directional standards graph from standards metadata.
        Adds nodes and edges with rich metadata while preventing duplicate edges and self-loops.
        """
        self.graph.clear()
        self.standards_map.clear()
        self.id_lookup.clear()
        self.unresolved_references.clear()
        self.declared_edge_count = 0
        self.inferred_edge_count = 0

        if not standards:
            logger.warning("Empty standards list provided to StandardsGraphBuilder.")
            self._is_built = True
            return self.graph

        # 1. Store standards & populate lookup indices
        for std in standards:
            if not isinstance(std, dict):
                continue
            std_id = std.get("id")
            if not std_id:
                continue

            self.standards_map[std_id] = std
            
            # Primary lookup keys
            self.id_lookup[std_id.lower()] = std_id
            
            is_num = std.get("is_number", "")
            if is_num:
                self.id_lookup[is_num.lower()] = std_id
                # Also index base IS code (e.g. "IS 10322", "IS 1180", "IS 7098")
                base_code = is_num.split(":")[0].split("-")[0].strip().lower()
                if base_code and base_code not in self.id_lookup:
                    self.id_lookup[base_code] = std_id

            # Add node to NetworkX graph
            self.graph.add_node(
                std_id,
                id=std_id,
                is_number=std.get("is_number", "Unknown Designation"),
                title=std.get("title", ""),
                sector=std.get("sector", ""),
                product_category=std.get("product_category", ""),
                revision_year=std.get("revision_year"),
                status=std.get("status", "Active (DEMO / SAMPLE DATA)")
            )

        # 2. Build Declared Edges (RELATED_STANDARD)
        for std_id, std in self.standards_map.items():
            related_list = std.get("related_standards", [])
            if not isinstance(related_list, list):
                continue

            for ref in related_list:
                if not ref or not isinstance(ref, str):
                    continue

                target_id = self._resolve_standard_id(ref)
                if target_id:
                    # Prevent self-loops
                    if target_id == std_id:
                        logger.debug(f"Skipping self-loop edge for standard '{std_id}'")
                        continue

                    # Avoid duplicate edges
                    if not self.graph.has_edge(std_id, target_id):
                        self.graph.add_edge(
                            std_id,
                            target_id,
                            relationship_type="RELATED_STANDARD",
                            relationship_label="Related standard (prototype corpus)",
                            source_type="standards.json (declared)",
                            is_inferred=False
                        )
                        self.declared_edge_count += 1
                else:
                    self.unresolved_references.append((std_id, ref))
                    logger.warning(
                        f"Unresolved related standard reference: '{ref}' referenced by '{std_id}'"
                    )

        # 3. Build Inferred Category Edges (SAME_PRODUCT_CATEGORY)
        category_clusters: Dict[str, List[str]] = {}
        for std_id, std in self.standards_map.items():
            cat = std.get("product_category")
            if cat and isinstance(cat, str) and cat.strip():
                category_clusters.setdefault(cat.strip(), []).append(std_id)

        for cat, node_ids in category_clusters.items():
            if len(node_ids) < 2:
                continue
            for i in range(len(node_ids)):
                for j in range(i + 1, len(node_ids)):
                    u, v = node_ids[i], node_ids[j]
                    # Only add inferred edge if no direct declared relationship exists
                    if not self.graph.has_edge(u, v) and not self.graph.has_edge(v, u):
                        self.graph.add_edge(
                            u,
                            v,
                            relationship_type="SAME_PRODUCT_CATEGORY",
                            relationship_label="Same Product Category",
                            source_type="corpus_category_inference",
                            is_inferred=True
                        )
                        self.inferred_edge_count += 1

        self._is_built = True
        logger.info(
            f"Standards Graph initialized successfully with {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges ({self.declared_edge_count} declared, "
            f"{self.inferred_edge_count} category-inferred). Unresolved refs: {len(self.unresolved_references)}"
        )
        return self.graph

    def _resolve_standard_id(self, query_ref: str) -> Optional[str]:
        """Resolves standard ID from exact ID, is_number, or normalized designation code."""
        if not query_ref:
            return None

        q_clean = query_ref.strip().lower()
        if q_clean in self.id_lookup:
            return self.id_lookup[q_clean]

        # Try base code matching (e.g. "IS 10322" from "IS 10322 (Part 5/Sec 3)")
        base_ref = q_clean.split(":")[0].split("-")[0].strip()
        if base_ref in self.id_lookup:
            return self.id_lookup[base_ref]

        # Partial substring matching fallback
        for key, std_id in self.id_lookup.items():
            if base_ref in key or key in base_ref:
                return std_id

        return None

    def get_network_overview(self) -> Dict[str, Any]:
        """Returns JSON-serializable full network overview."""
        nodes = []
        for n, data in self.graph.nodes(data=True):
            nodes.append(dict(data))

        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relationship_type": data.get("relationship_type", "RELATED_STANDARD"),
                "relationship_label": data.get("relationship_label", "Related standard"),
                "source_type": data.get("source_type", "prototype_corpus"),
                "is_inferred": data.get("is_inferred", False)
            })

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "declared_edge_count": self.declared_edge_count,
            "inferred_edge_count": self.inferred_edge_count,
            "unresolved_reference_count": len(self.unresolved_references),
            "nodes": nodes,
            "edges": edges,
            "disclaimer": "Standards Network based on relationships available in the prototype corpus."
        }

    def get_standard_subgraph(self, standard_id: str, depth: int = 1) -> Optional[Dict[str, Any]]:
        """
        Extracts bounded subgraph neighborhood for a given standard_id up to depth (bounded depth <= 2).
        Returns None if standard_id is unknown.
        """
        resolved_id = self._resolve_standard_id(standard_id)
        if not resolved_id or not self.graph.has_node(resolved_id):
            return None

        bounded_depth = min(max(int(depth), 1), 2)
        
        # Convert to undirected copy to get all connected neighborhood nodes
        undirected_graph = self.graph.to_undirected()
        reachable_lengths = nx.single_source_shortest_path_length(
            undirected_graph,
            resolved_id,
            cutoff=bounded_depth
        )
        sub_node_ids = set(reachable_lengths.keys())

        # Extract induced subgraph
        subgraph = self.graph.subgraph(sub_node_ids)

        nodes = [dict(subgraph.nodes[n]) for n in subgraph.nodes]
        edges = []
        for u, v, data in subgraph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relationship_type": data.get("relationship_type", "RELATED_STANDARD"),
                "relationship_label": data.get("relationship_label", "Related standard"),
                "source_type": data.get("source_type", "prototype_corpus"),
                "is_inferred": data.get("is_inferred", False)
            })

        center_node = dict(self.graph.nodes[resolved_id])

        return {
            "standard_id": resolved_id,
            "depth": bounded_depth,
            "center_node": center_node,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes": nodes,
            "edges": edges,
            "disclaimer": "Standards Network subgraph based on relationships available in the prototype corpus."
        }

    def get_standard_neighbors(self, standard_id: str) -> List[Dict[str, Any]]:
        """
        Returns structured list of neighboring standards and relationship metadata for a standard_id.
        """
        resolved_id = self._resolve_standard_id(standard_id)
        if not resolved_id or not self.graph.has_node(resolved_id):
            return []

        neighbors_list = []
        # Check outgoing & incoming edges in directional graph
        seen_neighbors = set()

        for u, v, data in self.graph.out_edges(resolved_id, data=True):
            if v not in seen_neighbors:
                seen_neighbors.add(v)
                target_node = self.graph.nodes[v]
                neighbors_list.append({
                    "standard_id": v,
                    "is_number": target_node.get("is_number", v),
                    "title": target_node.get("title", ""),
                    "relationship_type": data.get("relationship_type", "RELATED_STANDARD"),
                    "relationship_label": data.get("relationship_label", "Related standard"),
                    "is_inferred": data.get("is_inferred", False)
                })

        for u, v, data in self.graph.in_edges(resolved_id, data=True):
            if u not in seen_neighbors:
                seen_neighbors.add(u)
                target_node = self.graph.nodes[u]
                neighbors_list.append({
                    "standard_id": u,
                    "is_number": target_node.get("is_number", u),
                    "title": target_node.get("title", ""),
                    "relationship_type": data.get("relationship_type", "RELATED_STANDARD"),
                    "relationship_label": data.get("relationship_label", "Related standard"),
                    "is_inferred": data.get("is_inferred", False)
                })

        return neighbors_list

    def get_graph_stats(self) -> Dict[str, Any]:
        """Returns graph summary statistics."""
        return {
            "total_nodes": self.graph.number_of_nodes() if self._is_built else 0,
            "total_edges": self.graph.number_of_edges() if self._is_built else 0,
            "declared_edge_count": self.declared_edge_count,
            "inferred_edge_count": self.inferred_edge_count,
            "unresolved_reference_count": len(self.unresolved_references),
            "is_built": self._is_built
        }
