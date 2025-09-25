"""
Lightweight OpenAlex client focused on Topics and Works.
Adjust filter keys if OpenAlex filter names change (e.g. 'topics.id' vs 'topic.id').
"""
from dataclasses import dataclass
from typing import List, Optional, Iterator, Dict, Any

# prefer the concrete topic client in this package
from .openalex_topic_client import OpenAlexTopicClient as _UnderlyingClient

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

# New dataclass for an edge (from_work -> referenced_work)
@dataclass
class ReferenceEdge:
    from_work: str
    referenced_work: str

class OpenAlexClient:
    def __init__(self, *args, **kwargs):
        self._client = _UnderlyingClient(*args, **kwargs)

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

    def get_works_for_topic(self, topic_id: str, per_page: int = 25, max_items: Optional[int] = None) -> List[Work]:
        results_list: List[Work] = []
        page = 1
        collected = 0
        while True:
            params = {"per-page": per_page, "page": page}
            path = f"/topics/{topic_id}/works"
            data = self._get(path, params=params)
            items = data.get("results", [])
            for i in items:
                w = self.build_work(i)
                results_list.append(w)
                collected += 1
                if max_items and collected >= max_items:
                    return results_list
            meta = data.get("meta", {})
            if not meta.get("next_page") and len(items) < per_page:
                break
            page += 1
        return results_list

    def get_work(self, work_id: str) -> Work:
        path = f"/works/{work_id}" if not str(work_id).startswith("/") and not str(work_id).startswith("http") else work_id
        data = self._get(path)
        return self.build_work(data)


    def build_reference_edges(self, work: Work) -> List[ReferenceEdge]:
        """
        Given a Work, build a list of ReferenceEdge objects, one per referenced work.
        """
        if not work or not work.references:
            return []
        edges: List[ReferenceEdge] = []
        for ref in work.references:
            edges.append(ReferenceEdge(from_work=work.id, referenced_work=ref))
        return edges
