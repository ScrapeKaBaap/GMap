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
Mail Checker Addon

Validates and checks email deliverability using external API.
Adapted from the original mail-checker/check.py to work with the new emails table.
"""

import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os
import time
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_addon import EmailCheckerAddon
from addon_logger import setup_addon_logging

# Set up logging for this addon
logger = setup_addon_logging("mail-checker")

class MailCheckerAddon(EmailCheckerAddon):
    """
    Mail checker addon for email validation and deliverability checking.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the mail checker addon.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.api_endpoint = self.config.get('api_endpoint', 'http://localhost:8080/v0/check_email')
        self.batch_size = self.config.get('batch_size', 200)
        self.max_workers = self.config.get('max_workers', 10)
        self.max_requests_total = self.config.get('max_requests_total', None)
        self.api_timeout = self.config.get('api_timeout', 3600)  # seconds
    
    def get_source_name(self) -> str:
        """Return the source name for this addon."""
        return 'checker'
    
    def check_email(self, email: str, company_id: int = None) -> Dict[str, Any]:
        """
        Check/validate an email address.
        
        Args:
            email: Email address to check
            company_id: Optional company ID for context
            
        Returns:
            Dictionary with validation results
        """
        headers = {"Content-Type": "application/json"}
        data = {"to_email": email}
        
        try:
            logger.debug(f"Checking email: {email}")
            response = requests.post(self.api_endpoint, headers=headers, json=data, timeout=self.api_timeout)
            response.raise_for_status()
            json_response = response.json()
            
            # Add email to response for tracking
            json_response['email'] = email
            json_response['company_id'] = company_id
            
            logger.debug(f"Email check completed for: {email}")
            return json_response
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout occurred for email: {email}")
            return {'email': email, 'error': 'timeout', 'company_id': company_id}
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error {e.response.status_code} for email {email}: {e.response.text}")
            return {'email': email, 'error': f'http_error_{e.response.status_code}', 'company_id': company_id}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection Error for email {email}: {e}")
            return {'email': email, 'error': 'connection_error', 'company_id': company_id}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Exception for email {email}: {e}")
            return {'email': email, 'error': 'request_exception', 'company_id': company_id}
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error for email {email}: {e}")
            return {'email': email, 'error': 'json_decode_error', 'company_id': company_id}
    
    def process_email_data(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process API response and extract relevant data for database update.
        Always returns data to ensure email gets marked as checked.

        Args:
            api_response: Response from email checking API

        Returns:
            Dictionary of processed data (always returns data, even for errors)
        """
        processed_data = {}

        # Handle error responses - still mark as checked but store error info
        if not api_response or 'error' in api_response:
            error_type = api_response.get('error', 'unknown_error') if api_response else 'no_response'
            processed_data['check_error'] = error_type
            logger.warning(f"API error for email check: {error_type}")
            return processed_data

        # Process successful response
        processed_data = {
            'is_reachable': api_response.get('is_reachable'),
            'mx_accepts_mail': api_response.get('mx', {}).get('accepts_mail'),
            'records': json.dumps(api_response.get('mx', {}).get('records', []))
        }

        # Add misc data
        misc = api_response.get('misc', {})
        processed_data['is_disposable'] = misc.get('is_disposable')
        processed_data['is_role_account'] = misc.get('is_role_account')

        # Add syntax data
        syntax = api_response.get('syntax', {})
        processed_data['is_valid_syntax'] = syntax.get('is_valid_syntax')

        # Add SMTP data
        smtp = api_response.get('smtp', {})
        processed_data['can_connect_smtp'] = smtp.get('can_connect_smtp')
        processed_data['is_deliverable'] = smtp.get('is_deliverable')
        processed_data['is_catch_all'] = smtp.get('is_catch_all')
        processed_data['has_full_inbox'] = smtp.get('has_full_inbox')
        processed_data['is_disabled'] = smtp.get('is_disabled')

        return processed_data

    def _update_email_with_retry(self, db_manager, email_id: int, processed_data: Dict[str, Any], email: str, max_retries: int = 3) -> bool:
        """
        Update email with retry logic for database operations.

        Args:
            db_manager: Database manager instance
            email_id: Email ID to update
            processed_data: Data to update
            email: Email address for logging
            max_retries: Maximum number of retry attempts

        Returns:
            True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                success = db_manager.update_email_check_results(email_id, processed_data)
                if success:
                    return True
                else:
                    logger.warning(f"Database update failed for {email} (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(0.1 * (attempt + 1))  # Exponential backoff
            except Exception as e:
                logger.error(f"Database error for {email} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff

        # Final attempt to mark as checked with error
        try:
            error_data = {'check_error': 'persistent_database_error'}
            return db_manager.update_email_check_results(email_id, error_data)
        except Exception as e:
            logger.error(f"Failed to mark email {email} as checked after all retries: {e}")
            return False

    def check_emails_from_database(self, db_path: str, limit: int = None, source_filter: str = None) -> int:
        """
        Check unchecked emails from the database.
        
        Args:
            db_path: Path to the database
            limit: Maximum number of emails to check
            source_filter: Optional filter by email source
            
        Returns:
            Number of emails successfully checked
        """
        # Import here to avoid circular imports
        # Get the correct path to addons directory
        current_file = os.path.abspath(__file__)
        checker_dir = os.path.dirname(current_file)         # addons/mail-checker
        addons_dir = os.path.dirname(checker_dir)           # addons

        # Import directly from the addons directory
        import importlib.util
        db_manager_path = os.path.join(addons_dir, 'database_manager.py')
        spec = importlib.util.spec_from_file_location("database_manager", db_manager_path)
        database_manager_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(database_manager_module)
        EmailDatabaseManager = database_manager_module.EmailDatabaseManager
        db_manager = EmailDatabaseManager(db_path)

        # Ensure database tables have required schema
        db_manager.ensure_emails_table()
        db_manager.ensure_companies_table_columns()

        # Get unchecked emails
        unchecked_emails = db_manager.get_unchecked_emails(limit=limit, source=source_filter)
        
        if not unchecked_emails:
            logger.info("No unchecked emails found")
            return 0

        logger.info(f"Found {len(unchecked_emails)} unchecked emails to process")
        
        total_checked = 0
        total_requests_made = 0
        
        # Process in batches
        for i in range(0, len(unchecked_emails), self.batch_size):
            if self.max_requests_total and total_requests_made >= self.max_requests_total:
                logger.info(f"Reached maximum requests limit ({self.max_requests_total}). Stopping.")
                break

            batch = unchecked_emails[i:i + self.batch_size]
            logger.info(f"Processing batch {i//self.batch_size + 1}: {len(batch)} emails")

            # Calculate how many requests we can still make in this batch
            remaining_requests = None
            if self.max_requests_total:
                remaining_requests = self.max_requests_total - total_requests_made
                if remaining_requests <= 0:
                    break
                # Limit batch to remaining requests
                batch = batch[:remaining_requests]

            # Use ThreadPoolExecutor for concurrent API requests
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit email checking tasks
                future_to_email = {
                    executor.submit(self.check_email, email_data['email'], email_data['company_id']): email_data
                    for email_data in batch
                }

                # Process all submitted futures to completion
                for future in as_completed(future_to_email):
                    email_data = future_to_email[future]

                    try:
                        # Get the API response
                        api_response = future.result()
                        total_requests_made += 1

                        # Process the response (always returns data now)
                        processed_data = self.process_email_data(api_response)

                        # Always try to update database (even for errors) with retry logic
                        success = self._update_email_with_retry(
                            db_manager,
                            email_data['id'],
                            processed_data,
                            email_data['email']
                        )

                        if success:
                            total_checked += 1
                            logger.debug(f"Updated email check results for: {email_data['email']}")
                        else:
                            logger.error(f"Failed to update database for: {email_data['email']} after all retries")

                    except Exception as exc:
                        logger.error(f"Error checking email {email_data['email']}: {exc}")
                        # Mark as checked with error to prevent infinite retries
                        error_data = {'check_error': f'exception_{type(exc).__name__}'}
                        self._update_email_with_retry(
                            db_manager,
                            email_data['id'],
                            error_data,
                            email_data['email']
                        )

            # Small delay between batches
            time.sleep(0.1)
        
        logger.info(f"Email checking completed! Checked {total_checked} emails successfully")
        logger.info(f"Total API requests made: {total_requests_made}")
        return total_checked

    def get_email_check_stats(self, db_path: str) -> Dict[str, int]:
        """
        Get statistics about email checking status.

        Args:
            db_path: Path to the database

        Returns:
            Dictionary with email checking statistics
        """
        # Import database manager
        current_file = os.path.abspath(__file__)
        checker_dir = os.path.dirname(current_file)
        addons_dir = os.path.dirname(checker_dir)

        import importlib.util
        db_manager_path = os.path.join(addons_dir, 'database_manager.py')
        spec = importlib.util.spec_from_file_location("database_manager", db_manager_path)
        database_manager_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(database_manager_module)
        EmailDatabaseManager = database_manager_module.EmailDatabaseManager
        db_manager = EmailDatabaseManager(db_path)

        try:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Get total emails
                cursor.execute("SELECT COUNT(*) FROM emails")
                total_emails = cursor.fetchone()[0]

                # Get checked emails
                cursor.execute("SELECT COUNT(*) FROM emails WHERE checked_at IS NOT NULL")
                checked_emails = cursor.fetchone()[0]

                # Get emails with errors
                cursor.execute("SELECT COUNT(*) FROM emails WHERE check_error IS NOT NULL")
                error_emails = cursor.fetchone()[0]

                # Get emails by source
                cursor.execute("SELECT source, COUNT(*) FROM emails GROUP BY source")
                source_counts = dict(cursor.fetchall())

                return {
                    'total_emails': total_emails,
                    'checked_emails': checked_emails,
                    'unchecked_emails': total_emails - checked_emails,
                    'error_emails': error_emails,
                    'source_counts': source_counts
                }
        except Exception as e:
            logger.error(f"Error getting email check stats: {e}")
            return {}

def load_geo_mail_config():
    """Load configuration from geo_mail config/config.ini."""
    import configparser
    # Go up two levels from addons/mail-checker to geo_mail root
    geo_mail_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(geo_mail_root, 'config', 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def main():
    """Main function for standalone usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Check email deliverability")
    parser.add_argument("--email", help="Single email to check")
    parser.add_argument("--all-emails", action="store_true", help="Check all unchecked emails from database")
    parser.add_argument("--stats", action="store_true", help="Show email checking statistics")
    parser.add_argument("--batch-size", type=int, default=200, help="Batch size for processing")
    parser.add_argument("--max-workers", type=int, default=10, help="Maximum worker threads")
    parser.add_argument("--max-requests", type=int, help="Maximum total requests")
    parser.add_argument("--limit", type=int, help="Limit number of emails to process (if not set, processes all unchecked emails)")
    parser.add_argument("--source", help="Filter by email source (static, harvester, scraper)")
    parser.add_argument("--api-endpoint", default="http://localhost:8080/v0/check_email", help="API endpoint")

    args = parser.parse_args()

    # Load configuration from geo_mail config
    try:
        geo_config = load_geo_mail_config()
        config_batch_size = geo_config.getint("EmailChecker", "batch_size", fallback=200)
        config_max_workers = geo_config.getint("EmailChecker", "max_workers", fallback=10)
        config_api_endpoint = geo_config.get("EmailChecker", "api_endpoint", fallback="http://localhost:8080/v0/check_email")
    except:
        config_batch_size = 200
        config_max_workers = 10
        config_api_endpoint = "http://localhost:8080/v0/check_email"

    # Configure addon - use config.ini values if available, otherwise use command line args
    config = {
        'api_endpoint': args.api_endpoint if args.api_endpoint != "http://localhost:8080/v0/check_email" else config_api_endpoint,
        'batch_size': args.batch_size if args.batch_size != 200 else config_batch_size,
        'max_workers': args.max_workers if args.max_workers != 10 else config_max_workers,
        'max_requests_total': args.max_requests
    }

    checker = MailCheckerAddon(config)

    if args.email:
        # Check single email
        result = checker.check_email(args.email)
        print(f"Result for {args.email}:")
        print(json.dumps(result, indent=2))

    elif args.all_emails:
        # Check all unchecked emails from geo_mail database
        geo_config = load_geo_mail_config()
        db_name = geo_config.get("Database", "db_name", fallback="google_maps_companies.db")

        # Construct full database path (go up two levels from addons/mail-checker to geo_mail root)
        geo_mail_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(geo_mail_root, db_name)

        logger.info(f"Using database: {db_path}")
        logger.info(f"API endpoint: {config['api_endpoint']}")
        logger.info(f"Batch size: {config['batch_size']}")
        logger.info(f"Max workers (threads): {config['max_workers']}")
        if args.source:
            logger.info(f"Source filter: {args.source}")
        if args.limit:
            logger.info(f"Limit: {args.limit}")

        # Check emails from database
        checked_count = checker.check_emails_from_database(
            db_path,
            limit=args.limit,
            source_filter=args.source
        )
        logger.info(f"Successfully checked {checked_count} emails")

    elif args.stats:
        # Show email checking statistics
        geo_config = load_geo_mail_config()
        db_name = geo_config.get("Database", "db_name", fallback="google_maps_companies.db")

        # Construct full database path
        geo_mail_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(geo_mail_root, db_name)

        checker = MailCheckerAddon(config)
        stats = checker.get_email_check_stats(db_path)

        if stats:
            print("\n" + "=" * 50)
            print("EMAIL CHECKING STATISTICS")
            print("=" * 50)
            print(f"Total emails in database: {stats['total_emails']}")
            print(f"Checked emails: {stats['checked_emails']}")
            print(f"Unchecked emails: {stats['unchecked_emails']}")
            print(f"Emails with errors: {stats['error_emails']}")
            print("\nEmails by source:")
            for source, count in stats['source_counts'].items():
                print(f"  {source}: {count}")
            print("=" * 50)
        else:
            print("Failed to retrieve statistics")

    else:
        print("Usage:")
        print("  --email EMAIL                      Check single email")
        print("  --all-emails                       Check all unchecked emails from geo_mail database")
        print("  --stats                            Show email checking statistics")
        print("  --source SOURCE                    Filter by email source (static, harvester, scraper)")
        print("  --limit N                          Limit number of emails to check (optional - processes all if not set)")
        print("  --batch-size N                     Batch size for processing")
        print("  --max-workers N                    Maximum worker threads")
        print("  --max-requests N                   Maximum total requests")
        print("  --api-endpoint URL                 Email checking API endpoint")
        sys.exit(1)

if __name__ == "__main__":
    main()
