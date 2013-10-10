import unittest
from ift_forks_featuregather import num_to_categories


class TestNumToCategories(unittest.TestCase):
    def test_none(self):
        result = num_to_categories(0)
        self.assertTrue("None", result)

    def test_few(self):
        result = num_to_categories(1)
        self.assertTrue("Few", result)
        result = num_to_categories(2)
        self.assertTrue("Few", result)
        result = num_to_categories(3)
        self.assertTrue("Few", result)

    def test_some(self):
        result = num_to_categories(4)
        self.assertTrue("Some", result)
        result = num_to_categories(5)
        self.assertTrue("Some", result)
        result = num_to_categories(6)
        self.assertTrue("Some", result)

    def test_many(self):
        result = num_to_categories(7)
        self.assertTrue("Many", result)
        result = num_to_categories(8)
        self.assertTrue("Many", result)
        result = num_to_categories(9)
        self.assertTrue("Many", result)

    def test_lots(self):
        result = num_to_categories(10)
        self.assertTrue("Lots", result)
        result = num_to_categories(11)
        self.assertTrue("Lots", result)
        result = num_to_categories(12)
        self.assertTrue("Lots", result)

if __name__ == '__main__':
    unittest.main()
