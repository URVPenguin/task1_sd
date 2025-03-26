import unittest
from servers.xmlrpc.insult_filter import InsultFilterXMLRPC


class TestInsultFilterXMLRPC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = InsultFilterXMLRPC()

    def setUp(self):
        self.service.work_queue = []
        self.service.results = []

    def test_add_task(self):
        result = self.service.add_task("Eres tonto")
        self.assertTrue(result)
        self.assertEqual(self.service.work_queue, ["Eres tonto"])

    def test_process_next_task(self):
        self.service.add_task("Eres idiota")
        filtered_text = self.service.process_next_task()
        self.assertEqual(filtered_text, "Eres CENSORED")
        self.assertEqual(self.service.get_results(), ["Eres CENSORED"])

    def test_process_empty_queue(self):
        result = self.service.process_next_task()
        self.assertEqual(result, "No tasks")

if __name__ == "__main__":
    unittest.main()