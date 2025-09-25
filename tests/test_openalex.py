import os
import csv
import json
import unittest
from typing import List 
from pytest import MonkeyPatch

from climate_citations.openalex import OpenAlexClient, Topic, Work
# updated imports to use the moved functions
from climate_citations.network_file_talker import NetworkFileTalker, ReferenceEdge 

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
     

    def test_get_work(self):
        # monkeypatch OpenAlexClient._get to return the sample work JSON
        self._get_returns_file_contents("sample_work.json")
        work = self.client.get_work("W4249751050")
        self.assertIsInstance(work, Work)
        self.assertEqual(work.id, "https://openalex.org/W4249751050")
        self.assertEqual(work.title, "IntCal13 and Marine13 Radiocarbon Age Calibration Curves 0–50,000 Years cal BP")
        self.assertEqual(work.publication_year, 2013)
        self.assertEqual(work.cited_by_count, 12706)
        # New assertions about references field
        self.assertIsNotNone(work.references)
        self.assertEqual(len(work.references), 65)
        self.assertEqual(work.references[0], "https://openalex.org/W1529443799")
        self.assertEqual(work.references[-1], "https://openalex.org/W4256135186")
        self.mp.undo()

    def test_build_reference_edges(self):
        self._get_returns_file_contents("sample_work.json")
        work = self.client.get_work("W4249751050")
        self.assertIsInstance(work, Work)
        talker = NetworkFileTalker()    
        edges: List[ReferenceEdge] = talker.build_reference_edges(work)
        self.assertIsInstance(edges, list)
        self.assertEqual(len(edges), 65)
        self.assertEqual(edges[0].from_work, work.id)
        self.assertEqual(edges[0].referenced_work, "https://openalex.org/W1529443799")
        self.assertEqual(edges[-1].referenced_work, "https://openalex.org/W4256135186")
        self.mp.undo()

    def test_write_reference_edges(self):
        self._get_returns_file_contents("sample_work.json")
        work = self.client.get_work("W4249751050")
        tests_dir = os.path.dirname(__file__)
        csv_path = os.path.join(tests_dir, "test_reference_edges.csv")

        talker = NetworkFileTalker(reference_edge_file=csv_path)
        edges = talker.build_reference_edges(work)

        if os.path.exists(csv_path):
            os.remove(csv_path)
        try:
            talker.write_reference_edges(edges, csv_path)
            with open(csv_path, "r", encoding="utf-8") as fh:
                rows = list(csv.reader(fh))
            self.assertEqual(len(rows), len(edges))
            self.assertEqual(rows[0][0], edges[0].from_work)
            self.assertEqual(rows[0][1], edges[0].referenced_work)
            self.assertEqual(rows[-1][0], edges[-1].from_work)
            self.assertEqual(rows[-1][1], edges[-1].referenced_work)
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)
            self.mp.undo()

    def _get_returns_file_contents(self, filename: str) -> dict:
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, "r", encoding="utf-8") as fh:
            sample = json.load(fh)
        def fake_get(self, path, params=None):
                return sample
        self.mp.setattr(OpenAlexClient, "_get", fake_get)
 

if __name__ == "__main__":
    unittest.main()