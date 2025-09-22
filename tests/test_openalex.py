import unittest
import json
import os

from pytest import MonkeyPatch
from climate_citations.openalex import OpenAlexClient, Topic, Work

class TestOpenAlexClient(unittest.TestCase):

    def setUp(self):
        self.client = OpenAlexClient()
        self.mp = MonkeyPatch()
        print(f"Running test: {self._testMethodName}")


    def test_get_topic(self):
        self._get_returns_file_contents("sample_topic.json")
        topic = self.client.get_topic("T10017")
        self.assertIsInstance(topic, Topic)
        self.assertEqual(topic.id, "https://openalex.org/T10017")
        self.assertEqual(topic.display_name, "Geology and Paleoclimatology Research")
        self.mp.undo()

    def test_search_topics(self):
        self._get_returns_file_contents("sample_topics_list.json")
        topics = list(self.client.search_topics("climate", max_pages=1, per_page=3))
        self.assertEqual(len(topics), 3)
        topic = topics[0]
        self.assertIsInstance(topic, Topic)
        self.assertEqual(topic.id, "https://openalex.org/T10029")
        self.assertEqual(topic.display_name, "Climate variability and models")
        # for t in topics:
        #     print(f"{t.id} - {t.display_name!r} (level={t.level})")

    def test_get_works_for_topic(self):
        self._get_returns_file_contents("sample_works_list.json")
        works = self.client.get_works_for_topic("T10017", per_page=5, max_items=5)
        self.assertIsInstance(works, list)
        self.assertEqual(len(works), 5)
        first_work = works[0]
        self.assertIsInstance(first_work, Work)
        self.assertEqual(first_work.id, "https://openalex.org/W4249751050")
        self.assertEqual(first_work.title, "IntCal13 and Marine13 Radiocarbon Age Calibration Curves 0–50,000 Years cal BP")
        self.assertEqual(first_work.publication_year, 2013)
     


    def _get_returns_file_contents(self, filename: str) -> dict:
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, "r", encoding="utf-8") as fh:
            sample = json.load(fh)
        def fake_get(self, path, params=None):
                return sample
        self.mp.setattr(OpenAlexClient, "_get", fake_get)
 

if __name__ == "__main__":
    unittest.main()