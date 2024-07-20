import unittest
from backend import main


class MainTest(unittest.TestCase):
    def test_main(self):
        self.assertTrue(main.app is not None)
