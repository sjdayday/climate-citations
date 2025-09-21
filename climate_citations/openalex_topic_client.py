import time
import requests
from typing import Dict, Generator, List, Optional

class OpenAlexTopicClient:
    """
    Minimal OpenAlex client focused on topics and works.
    """
    BASE = "https://api.openalex.org"

    def __init__(self, mailto: Optional[str] = None, sleep_on_rate_limit: float = 1.0, session: Optional[requests.Session] = None):
        self.mailto = mailto
        self.session = session or requests.Session()
        self.sleep_on_rate_limit = sleep_on_rate_limit

    def _get(self, path: str, params: Optional[Dict] = None) -> Dict:
        params = params or {}
        if self.mailto:
            params.setdefault("mailto", self.mailto)
        url = path if path.startswith("http") else f"{self.BASE}{path}"
        resp = self.session.get(url, params=params, timeout=30)
        if resp.status_code == 429:
            time.sleep(self.sleep_on_rate_limit)
            resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def search_topics(self, query: str, per_page: int = 25) -> List[Dict]:
        data = self._get("/topics", {"search": query, "per-page": per_page})
        return data.get("results", [])

    def get_topic_by_id(self, topic_id: str) -> Dict:
        tid = topic_id
        if topic_id.startswith("T"):
            tid = f"/topics/{topic_id}"
        elif topic_id.startswith("http"):
            tid = "/" + "/".join(topic_id.split("://", 1)[1].split("/")[1:])
        return self._get(tid)

    def iter_topic_works(self, topic_id: str, per_page: int = 200, max_results: Optional[int] = None, filter_q: Optional[str] = None) -> Generator[Dict, None, None]:
        if topic_id.startswith("http"):
            endpoint_tid = topic_id.rstrip("/").split("/")[-1]
        else:
            endpoint_tid = topic_id

        params = {"per-page": per_page}
        if filter_q:
            params["filter"] = filter_q

        page = 1
        fetched = 0
        while True:
            params["page"] = page
            path = f"/topics/{endpoint_tid}/works"
            data = self._get(path, params=params)
            results = data.get("results", [])
            if not results:
                break
            for w in results:
                yield w
                fetched += 1
                if max_results and fetched >= max_results:
                    return
            meta = data.get("meta", {})
            if meta.get("next_page") is None and (len(results) < per_page):
                break
            page += 1