"""Tests for the allama package."""
import unittest
import sys
import os

# Dodaj katalog główny projektu do ścieżki Pythona
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from allama import __version__

class TestAllama(unittest.TestCase):
    """Test cases for the allama package."""

    def test_version(self):
        """Test that version is set correctly."""
        self.assertIsNotNone(__version__)
        self.assertIsInstance(__version__, str)

if __name__ == '__main__':
    unittest.main()
