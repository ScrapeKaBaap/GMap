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
import os
import sys

# Import module functions - ensure they are designed to be called externally
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.config_manager import ConfigManager

# Import base test from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from base_test import BaseTest

class TestConfigManager(BaseTest):
    pass

    def test_get(self):
        self.assertEqual(self.config_manager.get("TestSection", "key1"), "value1")
        self.assertIsNone(self.config_manager.get("TestSection", "non_existent_key"))
        self.assertEqual(self.config_manager.get("TestSection", "non_existent_key", fallback="default"), "default")

    def test_getint(self):
        self.assertEqual(self.config_manager.getint("TestSection", "key2"), 123)

    def test_getboolean(self):
        self.assertTrue(self.config_manager.getboolean("TestSection", "key3"))

if __name__ == "__main__":
    unittest.main()


