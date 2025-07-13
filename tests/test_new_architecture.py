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
Test Script for New Email Architecture

This script demonstrates the complete new professional email architecture
with the addon system, new database schema, and modular design.

Usage:
    python test_new_architecture.py --migrate-db
    python test_new_architecture.py --test-addons
    python test_new_architecture.py --test-integration
"""

import argparse
import sys
import os
from typing import Dict, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_migration():
    """Test the database migration to new schema."""
    print("=" * 60)
    print("TESTING DATABASE MIGRATION")
    print("=" * 60)
    
    from database_migration import main as migrate_main
    
    # Run migration in dry-run mode first
    print("Running migration in dry-run mode...")
    sys.argv = ['database_migration.py', '--db-path', 'google_maps_companies.first.db', '--dry-run']
    try:
        migrate_main()
        print("✓ Dry-run migration completed successfully")
    except SystemExit:
        pass
    
    # Ask user if they want to run actual migration
    response = input("\nRun actual migration? (y/N): ")
    if response.lower() == 'y':
        print("Running actual migration...")
        sys.argv = ['database_migration.py', '--db-path', 'google_maps_companies.first.db']
        try:
            migrate_main()
            print("✓ Actual migration completed successfully")
        except SystemExit:
            pass
    else:
        print("Skipping actual migration")

def test_static_generator():
    """Test the static email generator addon."""
    print("\n" + "=" * 60)
    print("TESTING STATIC EMAIL GENERATOR ADDON")
    print("=" * 60)
    
    sys.path.append('addons')
    from addons.static_generator import StaticEmailGenerator
    from addons.base_addon import CompanyInfo
    
    # Test configuration
    config = {
        'patterns': ['info', 'contact', 'sales', 'hr'],
        'min_confidence': 0.7,
        'max_emails': 5,
        'smart_selection': True
    }
    
    generator = StaticEmailGenerator(config)
    
    # Test companies
    test_companies = [
        CompanyInfo(id=1, name="Thoughtworks", website="thoughtworks.com"),
        CompanyInfo(id=2, name="Tech Solutions Inc", website="https://www.techsolutions.com"),
        CompanyInfo(id=3, name="HR Consulting Group", website="hr-consulting.co.uk")
    ]
    
    for company in test_companies:
        print(f"\nTesting company: {company.name} ({company.website})")
        emails = generator.find_emails(company)
        
        print(f"Generated {len(emails)} emails:")
        for email_result in emails:
            print(f"  - {email_result.email} (confidence: {email_result.confidence:.2f})")

def test_mail_harvester():
    """Test the mail harvester addon."""
    print("\n" + "=" * 60)
    print("TESTING MAIL HARVESTER ADDON")
    print("=" * 60)
    
    sys.path.append('addons')
    from addons.mail_harvester import MailHarvesterAddon
    from addons.base_addon import CompanyInfo
    
    # Test configuration
    config = {
        'sources': ['bing'],  # Use only bing for quick test
        'limit_per_source': 50,
        'timeout': 120,
        'harvester_bin_path': 'addons/mail-harvester/bin/theHarvester',
        'output_dir': 'addons/mail-harvester/output'
    }
    
    harvester = MailHarvesterAddon(config)
    
    if not harvester.setup():
        print("❌ Harvester setup failed - binary not found or not executable")
        return
    
    # Test company
    company = CompanyInfo(id=1, name="Example Corp", website="example.com")
    
    print(f"Testing harvester for: {company.website}")
    emails = harvester.find_emails(company)
    
    print(f"Harvested {len(emails)} emails:")
    for email_result in emails:
        print(f"  - {email_result.email}")

def test_database_integration():
    """Test the database integration with new emails table."""
    print("\n" + "=" * 60)
    print("TESTING DATABASE INTEGRATION")
    print("=" * 60)
    
    sys.path.append('addons')
    from addons.database_manager import EmailDatabaseManager
    from addons.base_addon import EmailResult, CompanyInfo
    from datetime import datetime
    
    db_manager = EmailDatabaseManager('google_maps_companies.first.db')
    
    # Ensure emails table exists
    if db_manager.ensure_emails_table():
        print("✓ Emails table created/verified")
    else:
        print("❌ Failed to create emails table")
        return
    
    # Test adding emails
    test_emails = [
        EmailResult(
            email="test1@example.com",
            source="static",
            source_details="Test email 1",
            confidence=0.9
        ),
        EmailResult(
            email="test2@example.com", 
            source="harvester",
            source_details="Test email 2",
            confidence=0.8
        )
    ]
    
    # Add test emails
    email_data = {999: test_emails}  # Use company ID 999 for testing
    added_count = db_manager.add_emails_batch(email_data)
    print(f"✓ Added {added_count} test emails to database")
    
    # Get emails for company
    company_emails = db_manager.get_company_emails(999)
    print(f"✓ Retrieved {len(company_emails)} emails for test company")
    
    # Get statistics
    stats = db_manager.get_email_stats()
    print(f"✓ Database stats: {stats}")

def test_email_finder_integration():
    """Test the updated EmailFinder with addon integration."""
    print("\n" + "=" * 60)
    print("TESTING EMAIL FINDER INTEGRATION")
    print("=" * 60)
    
    from modules.email_finder import EmailFinder
    from modules.config_manager import ConfigManager
    
    # Initialize email finder
    config = ConfigManager()
    email_finder = EmailFinder(config)
    
    print(f"✓ Email finder initialized with methods: {email_finder.enabled_methods}")
    print(f"✓ Available addons: {list(email_finder.addons.keys())}")
    
    # Test legacy method for backward compatibility
    legacy_email = email_finder.find_email("example.com")
    print(f"✓ Legacy find_email result: {legacy_email}")
    
    # Test new method
    if email_finder.addons:
        results = email_finder.find_emails_for_company(
            company_id=1000,
            company_name="Test Integration Company",
            website="example.com",
            methods=['static']  # Only test static for quick results
        )
        
        print(f"✓ New find_emails_for_company results:")
        for method, emails in results.items():
            print(f"  {method}: {len(emails)} emails found")
    
    # Get statistics
    stats = email_finder.get_email_statistics()
    print(f"✓ Email statistics: {stats}")

def test_complete_workflow():
    """Test the complete workflow from finding to checking emails."""
    print("\n" + "=" * 60)
    print("TESTING COMPLETE WORKFLOW")
    print("=" * 60)
    
    from modules.email_finder import EmailFinder
    from modules.config_manager import ConfigManager
    
    # Initialize email finder
    config = ConfigManager()
    email_finder = EmailFinder(config)
    
    # Test companies
    test_companies = [
        {'id': 2001, 'name': 'Workflow Test Company A', 'website': 'example.com'},
        {'id': 2002, 'name': 'Workflow Test Company B', 'website': 'test.com'}
    ]
    
    print("Step 1: Finding emails for test companies...")
    all_results = email_finder.find_emails_for_companies_batch(
        test_companies, 
        methods=['static']  # Only use static for quick testing
    )
    
    total_emails_found = 0
    for company_id, method_results in all_results.items():
        for method, emails in method_results.items():
            total_emails_found += len(emails)
            print(f"  Company {company_id} - {method}: {len(emails)} emails")
    
    print(f"✓ Total emails found: {total_emails_found}")
    
    # Note: Email checking would require the API to be running
    print("\nStep 2: Email checking (requires API server)...")
    if email_finder.check_inline and 'checker' in email_finder.addons:
        print("  Email checking is configured but requires API server to be running")
        print("  To test: Start the email checking API and run with --check-emails")
    else:
        print("  Email checking not configured for inline operation")

def main():
    """Main function to run tests."""
    parser = argparse.ArgumentParser(description="Test new email architecture")
    parser.add_argument("--migrate-db", action="store_true", help="Test database migration")
    parser.add_argument("--test-addons", action="store_true", help="Test individual addons")
    parser.add_argument("--test-integration", action="store_true", help="Test integration")
    parser.add_argument("--test-workflow", action="store_true", help="Test complete workflow")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    if not any([args.migrate_db, args.test_addons, args.test_integration, args.test_workflow, args.all]):
        print("Please specify which tests to run. Use --help for options.")
        return
    
    try:
        if args.migrate_db or args.all:
            test_database_migration()
        
        if args.test_addons or args.all:
            test_static_generator()
            test_mail_harvester()
        
        if args.test_integration or args.all:
            test_database_integration()
            test_email_finder_integration()
        
        if args.test_workflow or args.all:
            test_complete_workflow()
        
        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
