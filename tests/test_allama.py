"""Tests for the allama package."""
import unittest
from allama import __version__

class TestAllama(unittest.TestCase):
    """Test cases for the allama package."""

    def test_version(self):
        """Test that version is set correctly."""
        self.assertIsNotNone(__version__)
        self.assertIsInstance(__version__, str)

if __name__ == '__main__':
    unittest.main()
