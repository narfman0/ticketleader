import unittest
from backend import models


class ModelsTest(unittest.TestCase):
    def test_models(self):
        self.assertTrue(models is not None)
