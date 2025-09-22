"""
Lightweight OpenAlex client focused on Topics and Works.
Adjust filter keys if OpenAlex filter names change (e.g. 'topics.id' vs 'topic.id').
"""
from dataclasses import dataclass
from typing import List, Optional, Iterator, Dict, Any
import requests
import json
import time
from typing import Any, Dict, Optional
# import the concrete client implementation
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
    referenced_works: Optional[List[str]] = None
    publication_year: Optional[int] = None
    doi: Optional[str] = None


class OpenAlexClient:
    def __init__(self, *args, **kwargs):
        # delegate to the topic client implementation
        self._client = _UnderlyingClient(*args, **kwargs)

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None):
        # avoid recursion by delegating to the underlying client's _get
        return self._client._get(path, params=params)

    def get_topic(self, topic_id: str):
        # Accept 'T12345' or full path/URL
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
                w = Work(
                    id=i.get("id"),
                    title=i.get("title"),
                    referenced_works=i.get("referenced_works"),
                    publication_year=i.get("publication_year"),
                    doi=i.get("doi"),
                )
                results_list.append(w)
                collected += 1
                if max_items and collected >= max_items:
                    return results_list
            meta = data.get("meta", {})
            # stop if no next page or fewer results than page size
            if not meta.get("next_page") and len(items) < per_page:
                break
            page += 1
        return results_list

    def get_work(self, work_id: str):
        # Accept 'W12345' or full path/URL
        path = f"/works/{work_id}" if not str(work_id).startswith("/") and not str(work_id).startswith("http") else work_id
        data = self._get(path)
        return Work(
            id=data.get("id"),
            title=data.get("title"),
            referenced_works=data.get("referenced_works"),
            publication_year=data.get("publication_year"),
            doi=data.get("doi"),
        )
