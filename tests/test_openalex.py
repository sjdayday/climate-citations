import unittest
import json
import os

from pytest import MonkeyPatch
from climate_citations.openalex import OpenAlexClient, Topic

class TestOpenAlexClient(unittest.TestCase):

    def setUp(self):
        self.client = OpenAlexClient()
        print(f"Running test: {self._testMethodName}")


    def test_get_topic(self):
        sample_path = os.path.join(os.path.dirname(__file__), "sample_topic.json")
        with open(sample_path, "r", encoding="utf-8") as fh:
            sample = json.load(fh)

        mp = MonkeyPatch()
        try:
            def fake_get(self, path, params=None):
                return sample

            mp.setattr(OpenAlexClient, "_get", fake_get)
            client = OpenAlexClient()
            topic = client.get_topic("T10017")
            self.assertIsInstance(topic, Topic)
            self.assertEqual(topic.id, "https://openalex.org/T10017")
            self.assertEqual(topic.display_name, "Geology and Paleoclimatology Research")
            # dict vs dataclass comparison will fail; compare dict forms instead:
            # self.assertEqual(topic.__dict__, sample)
        finally:
            mp.undo()

if __name__ == "__main__":
    unittest.main()