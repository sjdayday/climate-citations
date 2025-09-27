"""
Lightweight OpenAlex client focused on Topics and Works.
Adjust filter keys if OpenAlex filter names change (e.g. 'topics.id' vs 'topic.id').
"""
from dataclasses import dataclass
from typing import List, Optional, Iterator, Dict, Any

# prefer the concrete topic client in this package
from .openalex_topic_client import OpenAlexTopicClient as _UnderlyingClient
from .network_file_talker import NetworkFileTalker, ReferenceEdge 

@dataclass
class Topic:
    id: str
    display_name: Optional[str] = None
    level: Optional[int] = None

@dataclass
class Work:
    id: str
    title: Optional[str] = None
    # New field populated from OpenAlex JSON "referenced_works"
    references: Optional[List[str]] = None
    publication_year: Optional[int] = None
    doi: Optional[str] = None
    cited_by_count: Optional[int] = None


class OpenAlexClient:
    talker: NetworkFileTalker 
    reference_edge_file: Optional[str] = "reference_edges.csv"
    work_node_file: Optional[str] = "work_nodes.json" 

    def __init__(self, *args, talker: Optional[NetworkFileTalker] = None, reference_edge_file: Optional[str] = None, work_node_file: Optional[str] = None, **kwargs):
        """
        Create the underlying HTTP client and configure file output.
        Any extra args/kwargs are forwarded to the underlying OpenAlexTopicClient.
        """
        self._client = _UnderlyingClient(*args, **kwargs)
        # use provided talker or a default NetworkFileTalker
        self.talker = talker or NetworkFileTalker()
        # allow overriding the defaults declared on the class
        if reference_edge_file is not None:
            self.reference_edge_file = reference_edge_file
        if work_node_file is not None:
            self.work_node_file = work_node_file

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None):
        return self._client._get(path, params=params)

    def build_work(self, data: Dict[str, Any]) -> Work:
        """
        Build a Work dataclass from raw OpenAlex work JSON, including references
        from the 'referenced_works' field.
        """
        return Work(
            id=data.get("id"),
            title=data.get("title"),
            references=data.get("referenced_works") or [],
            publication_year=data.get("publication_year"),
            doi=data.get("doi"),
            cited_by_count=data.get("cited_by_count"),
        )

    def get_topic(self, topic_id: str) -> Topic:
        path = f"/topics/{topic_id}" if not str(topic_id).startswith("/") and not str(topic_id).startswith("http") else topic_id
        data = self._get(path)
        return Topic(id=data.get("id"), display_name=data.get("display_name"), level=data.get("level"))

    def search_topics(self, query: str, max_pages: int = 1, per_page: int = 25) -> Iterator[Topic]:
        for page in range(1, max_pages + 1):
            params = {"search": query, "per-page": per_page, "page": page}
            data = self._get("/topics", params=params)
            for r in data.get("results", []):
                yield Topic(id=r.get("id"), display_name=r.get("display_name"), level=r.get("level"))
            
    def build_works_and_network_for_page(self, items: List[Dict[str, Any]], build_network: bool, results_list: List[Work], collected: int, max_items: Optional[int]):
        """
        Helper to process a page of work items: build Work objects, append to results_list,
        update collected count, and return (results_list, collected, done_flag).
        If max_items is reached, done_flag is True and the caller should stop.
        """
        page_work_list: List[Work] = []
        max_reached = False
        for i in items:
            w = self.build_work(i)
            results_list.append(w)
            page_work_list.append(w)
            collected += 1
            if max_items and collected >= max_items:
                max_reached = True
                break

        self.talker.write_work_nodes_edges(page_work_list)
        return  collected, max_reached

    def get_works_for_topic(self, topic_id: str, per_page: int = 25, max_items: Optional[int] = None) -> List[Work]:
        results_list: List[Work] = []
        page = 1
        collected = 0
        while True:
            params = {"per-page": per_page, "page": page}
            path = f"/topics/{topic_id}/works"
            data = self._get(path, params=params)
            items = data.get("results", [])
            collected, done = self.build_works_and_network_for_page(items, False, results_list, collected, max_items)
            if done:
                return results_list
            meta = data.get("meta", {})
            if not meta.get("next_page") and len(items) < per_page:
                break
            page += 1
        print( f"Collected {len(results_list)} = {collected} works for topic {topic_id}")
        return results_list

    def get_work(self, work_id: str) -> Work:
        path = f"/works/{work_id}" if not str(work_id).startswith("/") and not str(work_id).startswith("http") else work_id
        data = self._get(path)
        return self.build_work(data)

    def write_work_nodes_edges(self, page_work_list: List[Work]) -> None:
        """
        Write the provided list of Work objects as node records and collect+write
        their reference edges via the NetworkFileTalker.

        - Collects ReferenceEdge objects for each work and writes them as CSV.
        """
        # - Converts Work dataclasses to dicts for JSON output.
        if not page_work_list:
            return

        # convert dataclass Work objects to plain dicts for JSON serialization
        # node_objs = [asdict(w) for w in page_work_list]
        # self.talker.write_list(node_objs, self.work_node_file)
        self.build_works_and_network_for_page(page_work_list, True, [], 0, None)
        self.talker.write_list(page_work_list, self.work_node_file)

        # collect all edges for this page and write them once
        all_edges: List[ReferenceEdge] = []
        for w in page_work_list:
            edges = self.talker.build_reference_edges(w)
            if edges:
                all_edges.extend(edges)

        if all_edges:
            self.talker.write_reference_edges(all_edges, self.reference_edge_file)
