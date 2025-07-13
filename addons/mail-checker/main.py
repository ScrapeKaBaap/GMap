#!/usr/bin/env python3
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
Mail Checker - Updated Interface

This script validates and checks email deliverability using external API.
It can check individual emails or all unchecked emails from the database.

Usage:
    python main.py --all-emails                      # Check all unchecked emails from database
    python main.py --all-emails --limit 100         # Check 100 emails
    python main.py --email test@example.com         # Check single email
    python main.py --source static                  # Check only static emails
"""

# Import the checker addon functionality
from checker_addon import main as checker_main

def main():
    """Main function - delegates to the checker addon."""
    print("🔄 Using updated mail checker interface...")
    print()
    
    # Call the checker addon main function
    checker_main()

if __name__ == "__main__":
    main()
