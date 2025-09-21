"""
Lightweight OpenAlex client focused on Topics and Works.
Adjust filter keys if OpenAlex filter names change (e.g. 'topics.id' vs 'topic.id').
"""
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Generator
import requests
import time


@dataclass
class Topic:
    id: str
    display_name: str
    level: Optional[int] = None
    description: Optional[str] = None


@dataclass
class Work:
    id: str  # OpenAlex ID (e.g. https://openalex.org/W1234567890)
    title: Optional[str] = None
    year: Optional[int] = None
    referenced_works: Optional[List[str]] = None
    # additional fields as needed


class OpenAlexClient:
    def __init__(self, base_url: str = "https://api.openalex.org", sleep_between_requests: float = 0.5):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.sleep = float(sleep_between_requests)

    def _get(self, path: str, params: Optional[Dict] = None) -> dict:
        url = f"{self.base_url}/{path.lstrip('/')}"
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        if self.sleep:
            time.sleep(self.sleep)
        return resp.json()

    def get_topic(self, topic_id: str) -> Topic:
        """Retrieve a single topic by OpenAlex topic id (e.g. T12345 or full URL)."""
        tid = topic_id.split("/")[-1]
        data = self._get(f"topics/{tid}")
        return Topic(
            id=data.get("id") or tid,
            display_name=data.get("display_name"),
            level=data.get("level"),
            description=data.get("description"),
        )

    def search_topics(self, query: str, per_page: int = 25, max_pages: int = 2) -> Generator[Topic, None, None]:
        """
        Simple search for topics by name. Yields Topic objects.
        """
        params = {"search": query, "per-page": per_page}
        path = "topics"
        page = 0
        while page < max_pages:
            page += 1
            data = self._get(path, params=params)
            results = data.get("results", [])
            for t in results:
                yield Topic(id=t.get("id"), display_name=t.get("display_name"), level=t.get("level"))
            # pagination: OpenAlex uses "meta" with "next_cursor" or "next" URL.
            meta = data.get("meta", {})
            next_cursor = meta.get("next_cursor") or meta.get("next")
            if not next_cursor:
                break
            params["cursor"] = next_cursor

    def get_works_for_topic(self, topic_id: str, per_page: int = 200, max_items: int = 1000) -> List[Work]:
        """
        Retrieve works associated with a topic.
        NOTE: The filter key may vary; common pattern is filter=topics.id:T12345
        """
        tid = topic_id.split("/")[-1]
        works: List[Work] = []
        params = {"per-page": per_page, "filter": f"topics.id:{tid}"}
        path = "works"
        items = 0
        cursor = "*"
        while items < max_items:
            params["cursor"] = cursor
            data = self._get(path, params=params)
            results = data.get("results", [])
            for w in results:
                works.append(
                    Work(
                        id=w.get("id"),
                        title=w.get("title"),
                        year=w.get("publication_year"),
                        referenced_works=w.get("referenced_works") or []
                    )
                )
                items += 1
                if items >= max_items:
                    break
            cursor = data.get("meta", {}).get("next_cursor", "*")
            if cursor == "*":
                break
        return works
