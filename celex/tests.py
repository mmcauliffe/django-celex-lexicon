"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase

from .utils import lookupCat,lookupFreq

class CatLookupTest(TestCase):
    def test_lookup(self):
        """
        Tests that category lookups equal expected values.
        """
        self.assertEqual(lookupCat('test'),'N')

class FreqLookupTest(TestCase):
    def test_lookup(self):
        """
        Tests that frequency lookups equal expected values.
        """
        self.assertEqual(lookupFreq('test'), 2690)
