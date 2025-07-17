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

import sys
import os
import re
import time
from typing import List, Dict, Any, Optional
from modules.logger_config import setup_logging
from modules.config_manager import ConfigManager
from modules.internet_utils import wait_for_internet, InternetRestoredException

# Add addons directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'addons'))

from addons.base_addon import CompanyInfo, EmailResult
from addons.database_manager import EmailDatabaseManager

logger = setup_logging()

class EmailFinder:
    """
    Modern email finder that uses the addon system for email discovery.

    This class integrates with the new addon architecture to find emails
    using multiple methods: static patterns, harvesting, and scraping.
    """

    def __init__(self, config_manager: ConfigManager = None):
        """
        Initialize the email finder with addon system.

        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager or ConfigManager()
        self.db_manager = None
        self.addons = {}
        self._load_configuration()
        self._initialize_addons()

    def _load_configuration(self):
        """Load configuration from config.ini."""
        # Email finder settings
        self.enabled_methods = [
            method.strip()
            for method in self.config.get("EmailFinders", "enabled_methods", fallback="static").split(",")
        ]
        self.run_inline = self.config.getboolean("EmailFinders", "run_inline", fallback=True)
        self.check_inline = self.config.getboolean("EmailFinders", "check_inline", fallback=False)

        # Database settings
        db_name = self.config.get("Database", "db_name", fallback="google_maps_companies.db")
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_name)

        logger.info(f"Email finder configured with methods: {self.enabled_methods}")
        logger.info(f"Run inline: {self.run_inline}, Check inline: {self.check_inline}")

    def _initialize_addons(self):
        """Initialize enabled email finding addons."""
        # Initialize database manager
        self.db_manager = EmailDatabaseManager(self.db_path)
        self.db_manager.ensure_emails_table()

        # Initialize static generator addon
        if 'static' in self.enabled_methods and self.config.getboolean("EmailFinders", "static_enabled", fallback=True):
            try:
                import sys
                sys.path.append('addons/static-generator')
                from main import StaticEmailGenerator
                static_config = {
                    'patterns': [p.strip() for p in self.config.get("EmailFinders", "static_patterns", fallback="info,contact").split(",")],
                    'min_confidence': self.config.getfloat("EmailFinders", "static_min_confidence", fallback=0.7),
                    'max_emails': self.config.getint("EmailFinders", "static_max_emails", fallback=8),
                    'smart_selection': self.config.getboolean("EmailFinders", "static_smart_selection", fallback=True)
                }
                self.addons['static'] = StaticEmailGenerator(static_config)
                logger.info("Static email generator addon initialized")
            except ImportError as e:
                logger.warning(f"Could not load static email generator: {e}")

        # Initialize harvester addon
        if 'harvester' in self.enabled_methods and self.config.getboolean("EmailFinders", "harvester_enabled", fallback=True):
            try:
                sys.path.append('addons/mail-harvester')
                from harvester_addon import MailHarvesterAddon
                harvester_config = {
                    'sources': [s.strip() for s in self.config.get("EmailFinders", "harvester_sources", fallback="bing,duckduckgo").split(",")],
                    'limit_per_source': self.config.getint("EmailFinders", "harvester_limit_per_source", fallback=100),
                    'timeout': self.config.getint("EmailFinders", "harvester_timeout", fallback=300),
                    'harvester_bin_path': 'addons/mail-harvester/bin/theHarvester',
                    'output_dir': 'addons/mail-harvester/output'
                }
                self.addons['harvester'] = MailHarvesterAddon(harvester_config)
                logger.info("Mail harvester addon initialized")
            except ImportError as e:
                logger.warning(f"Could not load mail harvester: {e}")

        # Initialize scraper addon
        if 'scraper' in self.enabled_methods and self.config.getboolean("EmailFinders", "scraper_enabled", fallback=False):
            try:
                sys.path.append('addons/mail-scraper')
                from scraper_addon import MailScraperAddon
                scraper_config = {
                    'depth': self.config.getint("EmailFinders", "scraper_depth", fallback=1),
                    'limit_emails': self.config.getint("EmailFinders", "scraper_limit_emails", fallback=50),
                    'limit_urls': self.config.getint("EmailFinders", "scraper_limit_urls", fallback=25),
                    'timeout': self.config.getint("EmailFinders", "scraper_timeout", fallback=10000),
                    'sleep': self.config.getint("EmailFinders", "scraper_sleep", fallback=1000),
                    'extractor_bin_path': 'addons/mail-scraper/bin/kevincobain2000.email_extractor'
                }
                self.addons['scraper'] = MailScraperAddon(scraper_config)
                logger.info("Mail scraper addon initialized")
            except ImportError as e:
                logger.warning(f"Could not load mail scraper: {e}")

        # Initialize email checker if inline checking is enabled
        if self.check_inline and self.config.getboolean("EmailChecker", "enabled", fallback=True):
            try:
                sys.path.append('addons/mail-checker')
                from checker_addon import MailCheckerAddon
                checker_config = {
                    'api_endpoint': self.config.get("EmailChecker", "api_endpoint", fallback="http://localhost:8080/v0/check_email"),
                    'batch_size': self.config.getint("EmailChecker", "batch_size", fallback=200),
                    'max_workers': self.config.getint("EmailChecker", "max_workers", fallback=10),
                    'api_timeout': self.config.getint("EmailChecker", "api_timeout", fallback=3600)
                }
                self.addons['checker'] = MailCheckerAddon(checker_config)
                logger.info("Mail checker addon initialized for inline checking")
            except ImportError as e:
                logger.warning(f"Could not load mail checker: {e}")

    def find_email(self, domain: str) -> str:
        """
        Legacy method for backward compatibility.

        Args:
            domain: Domain to find email for

        Returns:
            Single email address (for compatibility)
        """
        logger.info(f"Legacy find_email called for domain: {domain}")

        # For backward compatibility, just return the first static email
        if 'static' in self.addons:
            company = CompanyInfo(id=0, name="Legacy Company", website=domain)
            emails = self.addons['static'].find_emails(company)
            if emails:
                return emails[0].email

        # Fallback to old behavior
        if domain and "." in domain:
            clean_domain = domain.lower()
            if clean_domain.startswith("www."):
                clean_domain = clean_domain[4:]
            return f"info@{clean_domain}"

        return "N/A"

    def find_emails_for_company(self, company_id: int, company_name: str, website: str,
                               methods: List[str] = None) -> Dict[str, List[EmailResult]]:
        """
        Find emails for a company using specified methods.

        Args:
            company_id: ID of the company
            company_name: Name of the company
            website: Company website
            methods: List of methods to use (defaults to enabled methods)

        Returns:
            Dictionary mapping method name to list of EmailResult objects
        """
        if methods is None:
            methods = self.enabled_methods

        company = CompanyInfo(id=company_id, name=company_name, website=website)
        results = {}

        for method in methods:
            if method in self.addons:
                addon = self.addons[method]

                # Check if addon can process this company
                if addon.validate_company(company):
                    try:
                        logger.info(f"Running {method} addon for company {company_id}")
                        emails = addon.find_emails(company)
                        results[method] = emails

                        # Store emails in database
                        if emails:
                            email_data = {company_id: emails}
                            added_count = self.db_manager.add_emails_batch(email_data)
                            logger.info(f"Added {added_count} emails from {method} for company {company_id}")

                        # Update company tracking
                        self.db_manager.update_company_methods(company_id, method, completed=True)

                    except Exception as e:
                        logger.error(f"Error running {method} addon for company {company_id}: {e}")
                        results[method] = []
                        # Mark as attempted but not completed
                        self.db_manager.update_company_methods(company_id, method, completed=False)
                else:
                    logger.warning(f"{method} addon cannot process company {company_id} (invalid website)")
                    results[method] = []
            else:
                logger.warning(f"Addon {method} not available")
                results[method] = []

        return results

    def find_emails_for_companies_batch(self, companies: List[Dict[str, Any]],
                                       methods: List[str] = None) -> Dict[int, Dict[str, List[EmailResult]]]:
        """
        Find emails for multiple companies in batch.

        Args:
            companies: List of company dictionaries with id, name, website
            methods: List of methods to use (defaults to enabled methods)

        Returns:
            Dictionary mapping company_id to method results
        """
        if methods is None:
            methods = self.enabled_methods

        all_results = {}

        for company_data in companies:
            company_id = company_data['id']
            company_name = company_data['name']
            website = company_data['website']

            results = self.find_emails_for_company(company_id, company_name, website, methods)
            all_results[company_id] = results

        return all_results

    def get_companies_needing_email_finding(self, methods: List[str] = None,
                                          limit: int = None) -> List[Dict[str, Any]]:
        """
        Get companies that need email finding for specified methods.

        Args:
            methods: List of methods to check (defaults to enabled methods)
            limit: Maximum number of companies to return

        Returns:
            List of company dictionaries
        """
        if methods is None:
            methods = self.enabled_methods

        companies_needing_work = []

        for method in methods:
            if method in self.addons:
                companies = self.db_manager.get_companies_needing_method(method, limit)
                for company in companies:
                    company_dict = {
                        'id': company.id,
                        'name': company.name,
                        'website': company.website,
                        'needed_method': method
                    }
                    companies_needing_work.append(company_dict)

        return companies_needing_work

    def run_email_checking(self, limit: int = None, source_filter: str = None) -> int:
        """
        Run email checking on unchecked emails.

        Args:
            limit: Maximum number of emails to check
            source_filter: Optional filter by email source

        Returns:
            Number of emails successfully checked
        """
        if 'checker' not in self.addons:
            logger.warning("Email checker addon not available")
            return 0

        checker = self.addons['checker']
        return checker.check_emails_from_database(self.db_path, limit, source_filter)

    def get_email_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about emails in the database.

        Returns:
            Dictionary with email statistics
        """
        return self.db_manager.get_email_stats()

    def verify_email(self, email):
        logger.info(f"Attempting to verify email: {email}")
        
        # Check internet connection before proceeding
        wait_for_internet()
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                retry_count += 1
                logger.info(f"Verifying email {email} - Attempt {retry_count}/{max_retries}")
                
                # Check internet connection with raise on restore
                wait_for_internet(raise_on_restore=True)
                
                # A more robust regex for email validation
                # This regex checks for: 
                # 1. A valid local part (before @)
                # 2. An @ symbol
                # 3. A valid domain part (after @) with at least one dot and characters before and after the dot
                regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" # Added \. to ensure a dot exists in the domain
                if re.match(regex, email):
                    logger.info(f"Email {email} passed basic format check.")
                    return True
                else:
                    logger.warning(f"Email {email} failed basic format check.")
                    return False
                    
            except InternetRestoredException:
                logger.warning(f"Internet connection restored during email verification for {email}. Retrying (Attempt {retry_count}/{max_retries})...")
                if retry_count >= max_retries:
                    logger.error(f"Failed to verify email {email} after {max_retries} attempts due to repeated internet interruptions.")
                    return False
                continue
                
            except Exception as e:
                logger.error(f"Error verifying email {email} on attempt {retry_count}: {e}")
                if retry_count >= max_retries:
                    logger.error(f"Failed to verify email {email} after {max_retries} attempts.")
                    return False
                # Wait a bit before retrying
                time.sleep(1)
                continue


