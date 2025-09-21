import unittest
from climate_citations.openalex import OpenAlexClient, Topic, Work

class TestOpenAlexClientNetwork(unittest.TestCase):

    def setUp(self):
        self.client = OpenAlexClient()
        print(f"Running test: {self._testMethodName}")

    def test_get_topic(self):
        topic = self.client.get_topic("T10017")
        self.assertIsInstance(topic, Topic)
        self.assertEqual(topic.id, "https://openalex.org/T10017")
        self.assertEqual(topic.display_name, "Geology and Paleoclimatology Research")
        self.assertEqual(topic.level, None)  # replace with actual expected level

    def test_search_topics(self):
        topics = list(self.client.search_topics("climate", max_pages=1, per_page=3))
        self.assertGreater(len(topics), 0)
        self.assertIsInstance(topics[0], Topic)
        for t in topics:
            print(f"{t.id} - {t.display_name!r} (level={t.level})")

    def test_get_works_for_topic(self):
        works = self.client.get_works_for_topic("T10017", per_page=5, max_items=5)
        self.assertIsInstance(works, list)
        if works:
            self.assertIsInstance(works[0], Work)
            first_work = works[0]
            print(f"{first_work.id} - {first_work.title!r} ({first_work.publication_year})")

if __name__ == "__main__":
    unittest.main()