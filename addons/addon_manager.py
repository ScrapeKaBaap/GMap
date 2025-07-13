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
Addon Manager

Central manager for all email addons with unified interfaces for single and batch processing.
"""

import os
import sys
from typing import List, Dict, Any, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from base_addon import EmailFinderAddon, EmailCheckerAddon, CompanyInfo, EmailResult
from database_manager import EmailDatabaseManager

class AddonManager:
    """
    Central manager for all email addons.
    
    Provides unified interfaces for single and batch processing across all addons.
    """
    
    def __init__(self, config: Dict[str, Any] = None, db_path: str = None):
        """
        Initialize addon manager.
        
        Args:
            config: Configuration dictionary
            db_path: Path to database file
        """
        self.config = config or {}
        self.db_path = db_path
        self.db_manager = EmailDatabaseManager(db_path) if db_path else None
        self.finder_addons = {}
        self.checker_addons = {}
        self.max_workers = self.config.get('max_workers', 5)
        
        self._load_addons()
    
    def _load_addons(self):
        """Load all available addons."""
        # Load static generator
        try:
            from static_generator import StaticEmailGenerator
            static_config = self.config.get('static', {})
            self.finder_addons['static'] = StaticEmailGenerator(static_config)
        except ImportError as e:
            print(f"Could not load static generator: {e}")
        
        # Load mail harvester
        try:
            from mail_harvester import MailHarvesterAddon
            harvester_config = self.config.get('harvester', {})
            self.finder_addons['harvester'] = MailHarvesterAddon(harvester_config)
        except ImportError as e:
            print(f"Could not load mail harvester: {e}")
        
        # Load mail scraper
        try:
            from mail_scraper import MailScraperAddon
            scraper_config = self.config.get('scraper', {})
            self.finder_addons['scraper'] = MailScraperAddon(scraper_config)
        except ImportError as e:
            print(f"Could not load mail scraper: {e}")
        
        # Load mail checker
        try:
            from mail_checker import MailCheckerAddon
            checker_config = self.config.get('checker', {})
            self.checker_addons['checker'] = MailCheckerAddon(checker_config)
        except ImportError as e:
            print(f"Could not load mail checker: {e}")
    
    def get_available_finders(self) -> List[str]:
        """Get list of available email finder addons."""
        return list(self.finder_addons.keys())
    
    def get_available_checkers(self) -> List[str]:
        """Get list of available email checker addons."""
        return list(self.checker_addons.keys())
    
    def find_emails_single(self, company: CompanyInfo, methods: List[str] = None) -> Dict[str, List[EmailResult]]:
        """
        Find emails for a single company using specified methods.
        
        Args:
            company: Company information
            methods: List of methods to use (defaults to all available)
            
        Returns:
            Dictionary mapping method name to list of EmailResult objects
        """
        if methods is None:
            methods = self.get_available_finders()
        
        results = {}
        
        for method in methods:
            if method in self.finder_addons:
                addon = self.finder_addons[method]
                
                if addon.validate_company(company):
                    try:
                        emails = addon.find_emails(company)
                        results[method] = emails
                        print(f"Found {len(emails)} emails using {method} for company {company.id}")
                    except Exception as e:
                        print(f"Error using {method} for company {company.id}: {e}")
                        results[method] = []
                else:
                    print(f"Company {company.id} not valid for {method} addon")
                    results[method] = []
            else:
                print(f"Method {method} not available")
                results[method] = []
        
        return results
    
    def find_emails_batch(self, companies: List[CompanyInfo], methods: List[str] = None, 
                         use_threading: bool = True) -> Dict[int, Dict[str, List[EmailResult]]]:
        """
        Find emails for multiple companies using specified methods.
        
        Args:
            companies: List of company information
            methods: List of methods to use (defaults to all available)
            use_threading: Whether to use threading for parallel processing
            
        Returns:
            Dictionary mapping company_id to method results
        """
        if methods is None:
            methods = self.get_available_finders()
        
        all_results = {}
        
        if use_threading and len(companies) > 1:
            # Use threading for parallel processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_company = {
                    executor.submit(self.find_emails_single, company, methods): company
                    for company in companies
                }
                
                for future in as_completed(future_to_company):
                    company = future_to_company[future]
                    try:
                        results = future.result()
                        all_results[company.id] = results
                    except Exception as e:
                        print(f"Error processing company {company.id}: {e}")
                        all_results[company.id] = {method: [] for method in methods}
        else:
            # Sequential processing
            for company in companies:
                results = self.find_emails_single(company, methods)
                all_results[company.id] = results
        
        return all_results
    
    def check_email_single(self, email: str, company_id: int = None) -> Dict[str, Any]:
        """
        Check a single email address.
        
        Args:
            email: Email address to check
            company_id: Optional company ID for context
            
        Returns:
            Dictionary with validation results
        """
        if 'checker' in self.checker_addons:
            checker = self.checker_addons['checker']
            return checker.check_email(email, company_id)
        else:
            return {'email': email, 'error': 'no_checker_available'}
    
    def check_emails_batch(self, emails: List[str], company_ids: List[int] = None,
                          use_threading: bool = True) -> List[Dict[str, Any]]:
        """
        Check multiple email addresses.
        
        Args:
            emails: List of email addresses
            company_ids: Optional list of company IDs
            use_threading: Whether to use threading for parallel processing
            
        Returns:
            List of validation result dictionaries
        """
        if 'checker' not in self.checker_addons:
            return [{'email': email, 'error': 'no_checker_available'} for email in emails]
        
        checker = self.checker_addons['checker']
        
        if use_threading:
            return checker.check_emails_batch(emails, company_ids)
        else:
            # Sequential processing
            if company_ids is None:
                company_ids = [None] * len(emails)
            
            results = []
            for email, company_id in zip(emails, company_ids):
                result = checker.check_email(email, company_id)
                results.append(result)
            
            return results
    
    def process_companies_complete_workflow(self, companies: List[CompanyInfo], 
                                          finder_methods: List[str] = None,
                                          check_emails: bool = False,
                                          store_in_db: bool = True) -> Dict[str, Any]:
        """
        Complete workflow: find emails and optionally check them.
        
        Args:
            companies: List of companies to process
            finder_methods: Email finding methods to use
            check_emails: Whether to check found emails
            store_in_db: Whether to store results in database
            
        Returns:
            Dictionary with processing results and statistics
        """
        results = {
            'companies_processed': 0,
            'total_emails_found': 0,
            'total_emails_checked': 0,
            'errors': [],
            'company_results': {}
        }
        
        # Step 1: Find emails
        print(f"Finding emails for {len(companies)} companies...")
        email_results = self.find_emails_batch(companies, finder_methods)
        
        all_emails_to_check = []
        all_company_ids = []
        
        for company_id, method_results in email_results.items():
            company_total = 0
            for method, emails in method_results.items():
                company_total += len(emails)
                
                # Store in database if requested
                if store_in_db and self.db_manager and emails:
                    email_data = {company_id: emails}
                    added_count = self.db_manager.add_emails_batch(email_data)
                    self.db_manager.update_company_methods(company_id, method, completed=True)
                
                # Collect emails for checking
                if check_emails:
                    for email_result in emails:
                        all_emails_to_check.append(email_result.email)
                        all_company_ids.append(company_id)
            
            results['company_results'][company_id] = {
                'emails_found': company_total,
                'methods_used': list(method_results.keys())
            }
            results['total_emails_found'] += company_total
            results['companies_processed'] += 1
        
        # Step 2: Check emails if requested
        if check_emails and all_emails_to_check:
            print(f"Checking {len(all_emails_to_check)} emails...")
            check_results = self.check_emails_batch(all_emails_to_check, all_company_ids)
            
            # Update database with check results if available
            if store_in_db and self.db_manager:
                for i, check_result in enumerate(check_results):
                    if 'error' not in check_result:
                        # Find the email ID in database and update
                        email = all_emails_to_check[i]
                        company_id = all_company_ids[i]
                        
                        # Get email record to update
                        company_emails = self.db_manager.get_company_emails(company_id)
                        for email_record in company_emails:
                            if email_record['email'] == email:
                                self.db_manager.update_email_check_results(
                                    email_record['id'], 
                                    check_result
                                )
                                break
                        
                        results['total_emails_checked'] += 1
        
        return results

def main():
    """Main function for standalone usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Addon Manager - Unified email processing")
    parser.add_argument("--db-path", required=True, help="Path to database file")
    parser.add_argument("--company-id", type=int, help="Single company ID to process")
    parser.add_argument("--domain", help="Single domain to process")
    parser.add_argument("--methods", nargs='+', default=['static'], help="Methods to use")
    parser.add_argument("--check-emails", action="store_true", help="Check found emails")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing")
    
    args = parser.parse_args()
    
    # Initialize addon manager
    config = {
        'max_workers': 5,
        'static': {'patterns': ['info', 'contact', 'sales'], 'max_emails': 5},
        'harvester': {'sources': ['bing'], 'limit_per_source': 50},
        'scraper': {'depth': 1, 'limit_emails': 25}
    }
    
    manager = AddonManager(config, args.db_path)
    
    print(f"Available finders: {manager.get_available_finders()}")
    print(f"Available checkers: {manager.get_available_checkers()}")
    
    if args.domain:
        # Process single domain
        company = CompanyInfo(id=0, name="Test Company", website=args.domain)
        results = manager.find_emails_single(company, args.methods)
        
        print(f"\nResults for {args.domain}:")
        for method, emails in results.items():
            print(f"  {method}: {len(emails)} emails")
            for email_result in emails:
                print(f"    - {email_result.email}")
    
    elif args.company_id:
        # Process single company from database
        if manager.db_manager:
            # Would need to implement getting company from database
            print(f"Processing company ID {args.company_id} from database...")
        else:
            print("Database not available")
    
    else:
        print("Please specify --domain or --company-id")

if __name__ == "__main__":
    main()
