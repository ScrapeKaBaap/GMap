# ================================================================================
# GMap - Professional Google Maps Scraper & Email Discovery Platform
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: GMap - Automated Google Maps Scraping + Email Discovery System
# Repository: https://github.com/ScrapeKaBaap/GMap
#
# Description: Enterprise-grade business intelligence platform that combines
#              automated Google Maps scraping with advanced email discovery
#              techniques to build targeted business contact databases.
#
# Components: - Google Maps Company Scraper
#             - Multi-Method Email Discovery (Static, Harvester, Scraper, Checker)
#             - Professional Database Management
#             - Advanced Configuration & Logging System
#
# License: MIT License
# Created: 2025
#
# ================================================================================
# This file is part of the GMap project.
# For complete documentation, visit: https://github.com/ScrapeKaBaap/GMap
# ================================================================================

import unittest
from modules.email_finder import EmailFinder

class TestEmailFinder(unittest.TestCase):
    def setUp(self):
        self.email_finder = EmailFinder()

    def test_find_email(self):
        self.assertEqual(self.email_finder.find_email("example.com"), "info@example.com")
        self.assertEqual(self.email_finder.find_email("sub.example.com"), "info@sub.example.com")
        self.assertEqual(self.email_finder.find_email(""), "N/A")
        self.assertEqual(self.email_finder.find_email(None), "N/A")

    def test_verify_email(self):
        self.assertTrue(self.email_finder.verify_email("test@example.com"))
        self.assertFalse(self.email_finder.verify_email("invalid-email"))
        self.assertFalse(self.email_finder.verify_email("test@.com"))
        self.assertFalse(self.email_finder.verify_email("test@example"))

if __name__ == "__main__":
    unittest.main()


