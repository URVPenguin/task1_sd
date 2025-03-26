import unittest
from servers.base.insult_filter_base import InsultFilterBase

class TestInsultFilter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = InsultFilterBase()

    def test_filter_text(self):
        self.assertEqual(self.service.filter_text("idiota"), "CENSORED")
        self.assertEqual(self.service.filter_text("Ets idiota idiota puto tonto"), "Ets CENSORED CENSORED puto CENSORED")

    def test_get_results(self):
        self.assertEqual(self.service.get_results(), ["CENSORED", "Ets CENSORED CENSORED puto CENSORED"])

if __name__ == "__main__":
    unittest.main()