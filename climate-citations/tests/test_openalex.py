import unittest
from climate_citations.openalex import OpenAlexClient, Topic, Work

class TestOpenAlexClient(unittest.TestCase):

    def setUp(self):
        self.client = OpenAlexClient()

    def test_get_topic(self):
        topic = self.client.get_topic("T12345")
        self.assertIsInstance(topic, Topic)
        self.assertEqual(topic.id, "T12345")

    def test_search_topics(self):
        topics = list(self.client.search_topics("climate"))
        self.assertGreater(len(topics), 0)
        self.assertIsInstance(topics[0], Topic)

    def test_get_works_for_topic(self):
        works = self.client.get_works_for_topic("T12345")
        self.assertIsInstance(works, list)
        if works:
            self.assertIsInstance(works[0], Work)

if __name__ == "__main__":
    unittest.main()