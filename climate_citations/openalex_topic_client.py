import time
import requests
from typing import Dict, Generator, List, Optional

class OpenAlexTopicClient:
    """
    Minimal OpenAlex client focused on topics and works.
    """
    BASE = "https://api.openalex.org"

    def __init__(self, mailto: Optional[str] = None, sleep_on_rate_limit: float = 10.0, session: Optional[requests.Session] = None):
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
