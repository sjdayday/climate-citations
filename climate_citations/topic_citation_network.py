from dataclasses import dataclass
from typing import Optional, Set
import networkx as nx
from .openalex_topic_client import OpenAlexTopicClient

@dataclass
class TopicCitationNetworkBuilder:
    client: OpenAlexTopicClient
    max_works: Optional[int] = 1000
    per_page: int = 200

    def build_network_for_topic(self, topic_id_or_name: str, topic_search: bool = False, year_from: Optional[int] = None, year_to: Optional[int] = None) -> nx.DiGraph:
        if topic_search:
            results = self.client.search_topics(topic_id_or_name, per_page=10)
            if not results:
                raise ValueError(f"No topics found for '{topic_id_or_name}'")
            topic_id = results[0].get("id")
        else:
            topic_id = topic_id_or_name

        filters = []
        if year_from and year_to:
            filters.append(f"publication_year:{year_from}-{year_to}")
        elif year_from:
            filters.append(f"publication_year:>{year_from-1}")
        elif year_to:
            filters.append(f"publication_year:<{year_to+1}")
        filter_q = ",".join(filters) if filters else None

        G = nx.DiGraph()
        seen_nodes: Set[str] = set()

        for work in self.client.iter_topic_works(topic_id, per_page=self.per_page, max_results=self.max_works, filter_q=filter_q):
            work_id = work.get("id")
            if not work_id:
                continue
            if work_id not in seen_nodes:
                G.add_node(work_id, title=work.get("title"), year=work.get("publication_year"), doi=work.get("doi"))
                seen_nodes.add(work_id)

            referenced = work.get("referenced_works") or []
            for cited_id in referenced:
                if cited_id not in seen_nodes:
                    G.add_node(cited_id)
                    seen_nodes.add(cited_id)
                G.add_edge(work_id, cited_id)

        return G

    def save_graph(self, G: nx.DiGraph, path: str, fmt: str = "gexf") -> None:
        fmt = fmt.lower()
        if fmt == "gexf":
            nx.write_gexf(G, path)
        elif fmt == "gml":
            nx.write_gml(G, path)
        elif fmt == "graphml":
            nx.write_graphml(G, path)
        elif fmt == "json":
            from networkx.readwrite import json_graph
            data = json_graph.node_link_data(G)
            import json as _json
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(_json.dumps(data, indent=2))
        else:
            raise ValueError(f"Unsupported format: {fmt}")