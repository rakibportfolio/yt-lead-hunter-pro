#!/usr/bin/env python3
"""Tests for Bright Data YouTube Scraper Integration.
Adapted from yaronbeen/bright-data-youtube-outreach
"""

import csv
import os
import sys
import tempfile
import unittest

os.environ.setdefault("BRIGHT_DATA_API_KEY", "test-placeholder-key")

sys.path.insert(0, os.path.dirname(__file__))
import bright_data_cli as scraper


class TestBrightDataUnit(unittest.TestCase):
    """Unit tests for pure utility functions (no external API calls required)."""

    def test_extract_emails_basic(self):
        emails = scraper.extract_emails("contact me at business@creator.org")
        self.assertIn("business@creator.org", emails)

    def test_extract_emails_multiple(self):
        text = "reach out to info@agency.com or support@creatorhub.co.uk for inquiries"
        emails = scraper.extract_emails(text)
        self.assertGreaterEqual(len(emails), 2)

    def test_extract_emails_empty(self):
        self.assertEqual(scraper.extract_emails(""), [])
        self.assertEqual(scraper.extract_emails(None), [])

    def test_extract_emails_deduplicates(self):
        text = "email me at hello@channel.com or hello@channel.com again"
        emails = scraper.extract_emails(text)
        self.assertEqual(len(emails), 1)
        self.assertIn("hello@channel.com", emails)

    def test_read_keywords_csv_with_header(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            f.write("keyword,num_of_posts\n")
            f.write("video editing,60\n")
            f.write("youtube growth,30\n")
            path = f.name
        try:
            keywords = scraper.read_keywords_csv(path)
            self.assertEqual(len(keywords), 2)
            self.assertEqual(keywords[0], ("video editing", 60))
            self.assertEqual(keywords[1], ("youtube growth", 30))
        finally:
            os.unlink(path)

    def test_read_keywords_csv_skips_empty_lines(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            f.write("keyword,num_of_posts\n")
            f.write("test query,60\n")
            f.write("\n")
            f.write("another query,45\n")
            path = f.name
        try:
            keywords = scraper.read_keywords_csv(path)
            self.assertEqual(len(keywords), 2)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()

