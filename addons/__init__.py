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

"""
Email Addons System

This package contains modular email finding and checking addons for the GMap system.

Available Addons:
- static-generator: Generates common email patterns (info@, hr@, contact@, etc.)
- mail-harvester: Uses theHarvester for OSINT email discovery
- mail-scraper: Crawls websites to extract emails
- mail-checker: Validates and checks email deliverability

Each addon follows a standard interface for integration with the main geo_mail system.
"""

from .base_addon import BaseEmailAddon

__version__ = "1.0.0"
__all__ = ["BaseEmailAddon"]
