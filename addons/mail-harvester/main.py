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
Mail Harvester - Updated Interface

This script uses theHarvester to find emails for companies from a database.
It can process individual companies or all companies that haven't been processed yet.

Usage:
    python main.py --all-companies                    # Process all unprocessed companies
    python main.py --all-companies --limit 10        # Process 10 companies
    python main.py --company-id 123                  # Process specific company
    python main.py --domain example.com              # Process specific domain
"""

# Import the new harvester addon functionality
from harvester_addon import main as harvester_main

def main():
    """Main function - delegates to the new harvester addon."""
    print("🔄 Using updated mail harvester interface...")
    print()
    
    # Call the new harvester addon main function
    harvester_main()

if __name__ == "__main__":
    main()
