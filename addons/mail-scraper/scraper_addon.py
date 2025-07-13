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
Mail Scraper Addon

Uses email_extractor to crawl websites and extract email addresses.
"""

import subprocess
import os
import re
import tempfile
from urllib.parse import urlparse
from typing import List, Dict, Set, Optional, Any

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_addon import EmailFinderAddon, EmailResult, CompanyInfo
from addon_logger import setup_addon_logging

# Set up logging for this addon
logger = setup_addon_logging("mail-scraper")

class MailScraperAddon(EmailFinderAddon):
    """
    Mail scraper addon using email_extractor for website crawling.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the mail scraper addon.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # Get addon directory for relative paths
        addon_dir = os.path.dirname(os.path.abspath(__file__))

        # Set paths relative to addon directory
        self.extractor_bin = self.config.get('extractor_bin_path', os.path.join(addon_dir, 'bin/kevincobain2000.email_extractor'))

        self.depth = self.config.get('depth', 1)  # Crawl depth
        self.limit_emails = self.config.get('limit_emails', 100)
        self.limit_urls = self.config.get('limit_urls', 50)
        self.timeout = self.config.get('timeout', 10000)  # milliseconds
        self.sleep = self.config.get('sleep', 1000)  # milliseconds between requests
        self.parallel = self.config.get('parallel', True)
        self.ignore_queries = self.config.get('ignore_queries', True)
        self.clean_domains = self.config.get('clean_domains', True)
        self.skip_invalid_domains = self.config.get('skip_invalid_domains', True)
        self.confidence = self.config.get('confidence', 0.9)
    
    def get_source_name(self) -> str:
        """Return the source name for this addon."""
        return 'scraper'
    
    def setup(self) -> bool:
        """
        Perform setup - check if email_extractor binary exists.
        
        Returns:
            True if setup successful, False otherwise
        """
        extractor_path = os.path.abspath(self.extractor_bin)
        if not os.path.exists(extractor_path):
            print(f"Error: email_extractor binary not found at {extractor_path}")
            return False
        
        if not os.access(extractor_path, os.X_OK):
            print(f"Error: email_extractor binary is not executable: {extractor_path}")
            return False
        
        return True
    
    def _clean_domain(self, domain: str) -> Optional[str]:
        """Clean and validate domain format."""
        if not domain or not isinstance(domain, str):
            return None
        
        domain = domain.strip()
        
        # Remove protocol if present
        if domain.startswith(('http://', 'https://')):
            parsed = urlparse(domain)
            domain = parsed.netloc
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Remove path, query, fragment
        domain = domain.split('/')[0].split('?')[0].split('#')[0]
        
        # Basic domain validation
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', domain):
            return None
        
        # Must have at least one dot
        if '.' not in domain:
            return None
        
        return domain.lower()
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation."""
        if not email or not isinstance(email, str):
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))
    
    def _extract_emails_from_file(self, file_path: str) -> Set[str]:
        """Extract emails from email_extractor output file."""
        emails = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    email = line.strip()
                    if email and self._is_valid_email(email):
                        emails.add(email.lower())
            
            return emails
            
        except (FileNotFoundError, IOError) as e:
            print(f"Error reading email file {file_path}: {e}")
            return set()
    
    def _run_email_extractor(self, domain: str, output_file: str) -> bool:
        """Run email_extractor for a specific domain."""
        try:
            # Construct the command with absolute path
            extractor_path = os.path.abspath(self.extractor_bin)
            
            cmd = [
                extractor_path,
                f'-url={domain}',
                f'-out={output_file}',
                f'-depth={self.depth}',
                f'-limit-emails={self.limit_emails}',
                f'-limit-urls={self.limit_urls}',
                f'-timeout={self.timeout}',
                f'-sleep={self.sleep}'
            ]
            
            if not self.parallel:
                cmd.append('-parallel=false')
            
            if self.ignore_queries:
                cmd.append('-ignore-queries=true')
            
            logger.info(f"Running email extractor for {domain} with depth {self.depth}")
            
            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout // 1000 + 60,  # Convert to seconds and add buffer
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                return True
            else:
                print(f"Email extractor failed for domain {domain}. Return code: {result.returncode}")
                if result.stderr:
                    print(f"Stderr: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"Email extractor timeout for domain: {domain}")
            return False
        except Exception as e:
            logger.error(f"Error running email extractor for domain {domain}: {e}")
            return False
    
    def find_emails(self, company: CompanyInfo) -> List[EmailResult]:
        """
        Find emails for a company using email_extractor.
        
        Args:
            company: Company information
            
        Returns:
            List of EmailResult objects
        """
        results = []
        
        # Clean the domain
        domain = company.domain
        if self.clean_domains:
            cleaned_domain = self._clean_domain(company.website)
            if not cleaned_domain:
                if self.skip_invalid_domains:
                    print(f"Invalid domain format: {company.website}. Skipping.")
                    return results
                else:
                    cleaned_domain = company.website
            domain = cleaned_domain
        
        if not domain:
            print(f"No valid domain for company {company.id}")
            return results
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_output = temp_file.name
        
        try:
            # Run email extractor
            success = self._run_email_extractor(domain, temp_output)
            
            if success and os.path.exists(temp_output):
                # Extract emails from the output file
                emails = self._extract_emails_from_file(temp_output)
                
                for email in emails:
                    result = EmailResult(
                        email=email,
                        source=self.get_source_name(),
                        source_details=f"Website crawling with depth {self.depth}",
                        confidence=self.confidence,  # Configurable confidence for emails found on actual website
                        metadata={
                            'domain': domain,
                            'crawl_depth': self.depth,
                            'extractor_version': 'kevincobain2000.email_extractor'
                        }
                    )
                    results.append(result)
                
                print(f"Scraped {len(emails)} emails from website: {domain}")
            else:
                print(f"Email extractor failed or no output for domain: {domain}")
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except OSError as e:
                    print(f"Could not remove temporary file {temp_output}: {e}")
        
        return results
    
    def validate_company(self, company: CompanyInfo) -> bool:
        """
        Check if this addon can process the given company.
        
        Args:
            company: Company information
            
        Returns:
            True if company has a valid website/domain
        """
        if not company.website:
            return False
        
        if self.clean_domains:
            domain = self._clean_domain(company.website)
            return domain is not None
        
        return True

def load_geo_mail_config():
    """Load configuration from geo_mail config/config.ini."""
    import configparser
    # Go up two levels from addons/mail-scraper to geo_mail root
    geo_mail_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(geo_mail_root, 'config', 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def process_all_companies_from_db(scraper, db_path, table_name, limit=None, offset=0):
    """Process all companies from database."""
    import sqlite3
    import time

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get companies that need scraper email generation
    query = f"""
        SELECT id, name, website
        FROM {table_name}
        WHERE website IS NOT NULL
        AND website != ''
        AND website != 'N/A'
        AND website NOT LIKE '%N/A%'
        AND website NOT LIKE 'n'
        AND website NOT LIKE 'N'
        AND (
            email_methods_completed IS NULL
            OR email_methods_completed = '[]'
            OR json_extract(email_methods_completed, '$') NOT LIKE '%"scraper"%'
        )
        ORDER BY id ASC
    """

    if offset:
        query += f" OFFSET {offset}"
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    companies = cursor.fetchall()
    conn.close()

    if not companies:
        print("No companies found that need scraper email generation")
        return

    print(f"Processing {len(companies)} companies for email scraping...")

    # Initialize database manager for storing results
    # Get the correct path to addons directory
    current_file = os.path.abspath(__file__)
    scraper_dir = os.path.dirname(current_file)          # addons/mail-scraper
    addons_dir = os.path.dirname(scraper_dir)            # addons

    # Import directly from the addons directory
    import importlib.util
    db_manager_path = os.path.join(addons_dir, 'database_manager.py')
    spec = importlib.util.spec_from_file_location("database_manager", db_manager_path)
    database_manager_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(database_manager_module)
    EmailDatabaseManager = database_manager_module.EmailDatabaseManager
    db_manager = EmailDatabaseManager(db_path)
    db_manager.ensure_emails_table()

    total_emails_scraped = 0

    for i, (company_id, company_name, website) in enumerate(companies, 1):
        print(f"Processing {i}/{len(companies)}: {company_name} ({website})")

        company = CompanyInfo(
            id=company_id,
            name=company_name or "Unknown Company",
            website=website
        )

        try:
            emails = scraper.find_emails(company)

            if emails:
                # Store emails in database
                email_data = {company_id: emails}
                added_count = db_manager.add_emails_batch(email_data)

                # Update company tracking
                db_manager.update_company_methods(company_id, 'scraper', completed=True)

                total_emails_scraped += len(emails)
                print(f"  Scraped {len(emails)} emails, stored {added_count} in database")

                # Show all emails found
                for email_result in emails:
                    print(f"    - {email_result.email}")
            else:
                print(f"  No emails scraped for {website}")
                # Still mark as completed even if no emails found
                db_manager.update_company_methods(company_id, 'scraper', completed=True)

        except Exception as e:
            print(f"  Error processing {company_name}: {e}")
            # Mark as attempted but not completed
            db_manager.update_company_methods(company_id, 'scraper', completed=False)

        # Small delay between companies to be respectful
        time.sleep(3)

    print(f"\nCompleted! Scraped {total_emails_scraped} total emails for {len(companies)} companies")

def main():
    """Main function for standalone usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape emails from website")
    parser.add_argument("--domain", help="Domain to scrape emails from")
    parser.add_argument("--company-id", type=int, help="Company ID from database")
    parser.add_argument("--all-companies", action="store_true", help="Process all companies from database that haven't been processed yet")
    parser.add_argument("--limit", type=int, help="Limit number of companies to process (if not set, processes all unprocessed companies)")
    parser.add_argument("--offset", type=int, default=0, help="Offset for database query")
    parser.add_argument("--depth", type=int, default=1, help="Crawl depth")
    parser.add_argument("--limit-emails", type=int, default=50, help="Limit emails to extract")
    parser.add_argument("--limit-urls", type=int, default=25, help="Limit URLs to crawl")
    parser.add_argument("--timeout", type=int, default=10000, help="Timeout in milliseconds")

    args = parser.parse_args()

    # Load confidence from geo_mail config
    try:
        geo_config = load_geo_mail_config()
        confidence = geo_config.getfloat("EmailFinders", "scraper_confidence", fallback=0.9)
    except:
        confidence = 0.9

    # Get addon directory for relative paths
    addon_dir = os.path.dirname(os.path.abspath(__file__))

    # Configure addon
    config = {
        'depth': args.depth,
        'limit_emails': args.limit_emails,
        'limit_urls': args.limit_urls,
        'timeout': args.timeout,
        'extractor_bin_path': os.path.join(addon_dir, 'bin/kevincobain2000.email_extractor'),
        'confidence': confidence
    }

    scraper = MailScraperAddon(config)

    if not scraper.setup():
        print("Setup failed!")
        sys.exit(1)

    if args.domain:
        # Process specific domain
        company = CompanyInfo(
            id=0,
            name="Test Company",
            website=args.domain
        )

        emails = scraper.find_emails(company)

        print(f"\nFound {len(emails)} emails for {args.domain}:")
        for email_result in emails:
            print(f"  {email_result.email}")

    elif args.all_companies:
        # Process all companies from geo_mail database
        geo_config = load_geo_mail_config()
        db_name = geo_config.get("Database", "db_name", fallback="google_maps_companies.db")
        table_name = geo_config.get("Email", "table_name", fallback="companies")

        # Construct full database path (go up two levels from addons/mail-scraper to geo_mail root)
        geo_mail_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(geo_mail_root, db_name)

        print(f"Using database: {db_path}")
        print(f"Using table: {table_name}")
        print(f"Crawl depth: {args.depth}")

        process_all_companies_from_db(scraper, db_path, table_name, args.limit, args.offset)

    elif args.company_id:
        # Process single company from database
        geo_config = load_geo_mail_config()
        db_name = geo_config.get("Database", "db_name", fallback="google_maps_companies.db")
        table_name = geo_config.get("Email", "table_name", fallback="companies")
        geo_mail_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(geo_mail_root, db_name)

        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, name, website FROM {table_name} WHERE id = ?", (args.company_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            company_id, company_name, website = result
            company = CompanyInfo(id=company_id, name=company_name, website=website)
            emails = scraper.find_emails(company)

            print(f"Scraped {len(emails)} emails for company {company_id} ({company_name}):")
            for email_result in emails:
                print(f"  {email_result.email}")
        else:
            print(f"Company with ID {args.company_id} not found")

    else:
        print("Usage:")
        print("  --domain DOMAIN                    Scrape for specific domain")
        print("  --all-companies                    Process all unprocessed companies from geo_mail database")
        print("  --company-id ID                    Process specific company from database")
        print("  --limit N                          Limit number of companies (optional - processes all if not set)")
        print("  --offset N                         Offset for database query")
        print("  --depth N                          Website crawl depth")
        sys.exit(1)

if __name__ == "__main__":
    main()
