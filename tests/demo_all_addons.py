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
Demo Script for All Email Addons

This script demonstrates how each addon can process all companies from the database
using the database name and table name from geo_mail config.ini.

Usage:
    python demo_all_addons.py --addon static --limit 5
    python demo_all_addons.py --addon harvester --limit 3
    python demo_all_addons.py --addon scraper --limit 2
    python demo_all_addons.py --addon checker --limit 10
    python demo_all_addons.py --all-addons --limit 2
"""

import argparse
import subprocess
import sys
import os
import time

def run_static_generator(limit=None, offset=0):
    """Run static email generator on all companies."""
    print("=" * 60)
    print("RUNNING STATIC EMAIL GENERATOR")
    print("=" * 60)
    
    cmd = ["python3", "addons/static-generator/main.py", "--all-companies"]
    if limit:
        cmd.extend(["--limit", str(limit)])
    if offset:
        cmd.extend(["--offset", str(offset)])
    
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    print(f"Return code: {result.returncode}")
    return result.returncode == 0

def run_mail_harvester(limit=None, offset=0):
    """Run mail harvester on all companies."""
    print("=" * 60)
    print("RUNNING MAIL HARVESTER")
    print("=" * 60)
    
    cmd = ["python3", "addons/mail-harvester/harvester_addon.py", "--all-companies"]
    if limit:
        cmd.extend(["--limit", str(limit)])
    if offset:
        cmd.extend(["--offset", str(offset)])
    
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    print(f"Return code: {result.returncode}")
    return result.returncode == 0

def run_mail_scraper(limit=None, offset=0):
    """Run mail scraper on all companies."""
    print("=" * 60)
    print("RUNNING MAIL SCRAPER")
    print("=" * 60)
    
    cmd = ["python3", "addons/mail-scraper/scraper_addon.py", "--all-companies"]
    if limit:
        cmd.extend(["--limit", str(limit)])
    if offset:
        cmd.extend(["--offset", str(offset)])
    
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    print(f"Return code: {result.returncode}")
    return result.returncode == 0

def run_mail_checker(limit=None):
    """Run mail checker on all unchecked emails."""
    print("=" * 60)
    print("RUNNING MAIL CHECKER")
    print("=" * 60)
    
    cmd = ["python3", "addons/mail-checker/checker_addon.py", "--all-emails"]
    if limit:
        cmd.extend(["--limit", str(limit)])
    
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    print(f"Return code: {result.returncode}")
    return result.returncode == 0

def show_database_stats():
    """Show current database statistics."""
    print("=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)
    
    # Get database stats
    cmd = ["sqlite3", "google_maps_companies.first.db", """
        SELECT 
            'Total Companies' as metric, 
            COUNT(*) as count 
        FROM companies
        UNION ALL
        SELECT 
            'Companies with Websites' as metric, 
            COUNT(*) as count 
        FROM companies 
        WHERE website IS NOT NULL 
        AND website != '' 
        AND website != 'N/A'
        UNION ALL
        SELECT 
            'Total Emails' as metric, 
            COUNT(*) as count 
        FROM emails
        UNION ALL
        SELECT 
            'Static Emails' as metric, 
            COUNT(*) as count 
        FROM emails 
        WHERE source = 'static'
        UNION ALL
        SELECT 
            'Harvester Emails' as metric, 
            COUNT(*) as count 
        FROM emails 
        WHERE source = 'harvester'
        UNION ALL
        SELECT 
            'Scraper Emails' as metric, 
            COUNT(*) as count 
        FROM emails 
        WHERE source = 'scraper'
        UNION ALL
        SELECT 
            'Checked Emails' as metric, 
            COUNT(*) as count 
        FROM emails 
        WHERE is_reachable IS NOT NULL;
    """]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if '|' in line:
                metric, count = line.split('|')
                print(f"{metric:<25}: {count}")
    else:
        print("Error getting database stats")
    print()

def demonstrate_single_company():
    """Demonstrate processing a single company with each addon."""
    print("=" * 60)
    print("SINGLE COMPANY DEMONSTRATION")
    print("=" * 60)
    
    # Test with company ID 1 (Thoughtworks)
    company_id = 1
    
    print(f"Testing all addons with company ID {company_id}:")
    print()
    
    # Static generator
    print("1. Static Email Generator:")
    cmd = ["python3", "addons/static-generator/main.py", "--company-id", str(company_id)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    
    # Note: Harvester and scraper would require actual tools to be installed
    print("2. Mail Harvester (requires theHarvester):")
    print("   Command: python3 addons/mail-harvester/harvester_addon.py --company-id 1")
    print("   (Skipped - requires theHarvester installation)")
    print()
    
    print("3. Mail Scraper (requires email_extractor):")
    print("   Command: python3 addons/mail-scraper/scraper_addon.py --company-id 1")
    print("   (Skipped - requires email_extractor installation)")
    print()
    
    print("4. Mail Checker (requires API server):")
    print("   Command: python3 addons/mail-checker/checker_addon.py --email info@thoughtworks.com")
    print("   (Skipped - requires email checking API server)")
    print()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Demo all email addons")
    parser.add_argument("--addon", choices=["static", "harvester", "scraper", "checker"], 
                       help="Run specific addon")
    parser.add_argument("--all-addons", action="store_true", help="Run all addons")
    parser.add_argument("--limit", type=int, default=5, help="Limit number of companies/emails")
    parser.add_argument("--offset", type=int, default=0, help="Offset for database query")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--demo", action="store_true", help="Show single company demo")
    
    args = parser.parse_args()
    
    # Change to geo_mail directory
    if not os.path.exists("config.ini"):
        print("Error: Must run from geo_mail directory (config.ini not found)")
        sys.exit(1)
    
    if args.stats:
        show_database_stats()
        return
    
    if args.demo:
        demonstrate_single_company()
        return
    
    print("🚀 EMAIL ADDON DEMONSTRATION")
    print("Using database and table from geo_mail config.ini")
    print()
    
    show_database_stats()
    
    success_count = 0
    total_count = 0
    
    if args.addon == "static" or args.all_addons:
        total_count += 1
        if run_static_generator(args.limit, args.offset):
            success_count += 1
        time.sleep(2)
    
    if args.addon == "harvester" or args.all_addons:
        total_count += 1
        print("\nNote: Mail harvester requires theHarvester to be installed")
        print("Attempting to run anyway...")
        if run_mail_harvester(args.limit, args.offset):
            success_count += 1
        time.sleep(2)
    
    if args.addon == "scraper" or args.all_addons:
        total_count += 1
        print("\nNote: Mail scraper requires email_extractor to be installed")
        print("Attempting to run anyway...")
        if run_mail_scraper(args.limit, args.offset):
            success_count += 1
        time.sleep(2)
    
    if args.addon == "checker" or args.all_addons:
        total_count += 1
        print("\nNote: Mail checker requires email checking API server to be running")
        print("Attempting to run anyway...")
        if run_mail_checker(args.limit):
            success_count += 1
    
    if total_count == 0:
        print("Usage:")
        print("  --addon static                     Run static email generator")
        print("  --addon harvester                  Run mail harvester")
        print("  --addon scraper                    Run mail scraper")
        print("  --addon checker                    Run mail checker")
        print("  --all-addons                       Run all addons")
        print("  --stats                            Show database statistics")
        print("  --demo                             Show single company demo")
        print("  --limit N                          Limit number of items to process")
        return
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Successfully ran {success_count}/{total_count} addons")
    
    show_database_stats()
    
    print("\n✅ All addons are configured to work with:")
    print("   - Database name from config.ini [Database] db_name")
    print("   - Table name from config.ini [Email] table_name")
    print("   - Process all companies with --all-companies option")
    print("   - Process single company with --company-id option")
    print("   - Limit and offset support for batch processing")

if __name__ == "__main__":
    main()
