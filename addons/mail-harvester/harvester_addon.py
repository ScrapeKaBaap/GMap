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
Mail Harvester Addon

Uses theHarvester for OSINT email discovery from various sources.
"""

import subprocess
import json
import os
import re
import tempfile
import time
from urllib.parse import urlparse
from typing import List, Dict, Set, Optional, Any

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_addon import EmailFinderAddon, EmailResult, CompanyInfo
from addon_logger import setup_addon_logging

# Set up logging for this addon
logger = setup_addon_logging("mail-harvester")

class MailHarvesterAddon(EmailFinderAddon):
    """
    Mail harvester addon using theHarvester for OSINT email discovery.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the mail harvester addon.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # Get addon directory for relative paths
        addon_dir = os.path.dirname(os.path.abspath(__file__))

        # Set paths relative to addon directory
        self.harvester_bin = self.config.get('harvester_bin_path', os.path.join(addon_dir, 'bin/theHarvester'))
        self.output_dir = self.config.get('output_dir', os.path.join(addon_dir, 'output'))

        self.sources = self.config.get('sources', ['bing', 'duckduckgo', 'yahoo', 'crtsh', 'dnsdumpster', 'hackertarget'])
        self.limit_per_source = self.config.get('limit_per_source', 100)
        self.timeout = self.config.get('timeout', 300)
        self.clean_domains = self.config.get('clean_domains', True)
        self.skip_invalid_domains = self.config.get('skip_invalid_domains', True)
        self.confidence = self.config.get('confidence', 0.8)
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_source_name(self) -> str:
        """Return the source name for this addon."""
        return 'harvester'
    
    def setup(self) -> bool:
        """
        Perform setup - check if theHarvester binary exists.
        
        Returns:
            True if setup successful, False otherwise
        """
        harvester_path = os.path.abspath(self.harvester_bin)
        if not os.path.exists(harvester_path):
            print(f"Error: theHarvester binary not found at {harvester_path}")
            return False
        
        if not os.access(harvester_path, os.X_OK):
            print(f"Error: theHarvester binary is not executable: {harvester_path}")
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
    
    def _extract_emails_from_json(self, json_file_path: str) -> Set[str]:
        """Extract emails from theHarvester JSON output."""
        emails = set()
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check common fields where emails might be stored
            email_fields = ['emails', 'email', 'people']
            
            for field in email_fields:
                if field in data:
                    field_data = data[field]
                    if isinstance(field_data, list):
                        for item in field_data:
                            if isinstance(item, str) and self._is_valid_email(item):
                                emails.add(item.lower().strip())
                            elif isinstance(item, dict) and 'email' in item:
                                email = item['email']
                                if self._is_valid_email(email):
                                    emails.add(email.lower().strip())
                    elif isinstance(field_data, str) and self._is_valid_email(field_data):
                        emails.add(field_data.lower().strip())
            
            # Also check if the entire data structure contains email-like strings
            json_str = json.dumps(data)
            email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
            found_emails = re.findall(email_pattern, json_str)
            
            for email in found_emails:
                if self._is_valid_email(email):
                    emails.add(email.lower().strip())
            
            return emails
            
        except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
            logger.error(f"Error reading JSON file {json_file_path}: {e}")
            return set()
    
    def _run_harvester(self, domain: str, sources: List[str], limit: int, output_file: str) -> bool:
        """Run theHarvester for a specific domain and sources."""
        try:
            # Construct the command with absolute path
            harvester_path = os.path.abspath(self.harvester_bin)
            
            sources_str = ','.join(sources)
            cmd = [
                harvester_path,
                '-d', domain,
                '-b', sources_str,
                '-l', str(limit),
                '-f', output_file,
                '-q'  # Quiet mode to suppress API key warnings
            ]
            
            logger.info(f"Running harvester for {domain} with sources: {sources_str}")
            
            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                return True
            else:
                print(f"Harvester failed for domain {domain}. Return code: {result.returncode}")
                if result.stderr:
                    print(f"Stderr: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Harvester timeout for domain: {domain}")
            return False
        except Exception as e:
            logger.error(f"Error running harvester for domain {domain}: {e}")
            return False
    
    def find_emails(self, company: CompanyInfo) -> List[EmailResult]:
        """
        Find emails for a company using theHarvester.
        
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, dir=self.output_dir) as temp_file:
            temp_output = temp_file.name.replace('.json', '')  # theHarvester adds .json automatically
        
        try:
            # Run harvester with all sources
            success = self._run_harvester(domain, self.sources, self.limit_per_source, temp_output)
            
            if success:
                # Extract emails from the JSON output
                json_file = f"{temp_output}.json"
                if os.path.exists(json_file):
                    emails = self._extract_emails_from_json(json_file)
                    
                    for email in emails:
                        result = EmailResult(
                            email=email,
                            source=self.get_source_name(),
                            source_details=f"theHarvester OSINT discovery from sources: {', '.join(self.sources)}",
                            confidence=self.confidence,  # Configurable confidence for OSINT discovered emails
                            metadata={
                                'domain': domain,
                                'sources': self.sources,
                                'harvester_version': 'theHarvester 4.8.0'
                            }
                        )
                        results.append(result)
                    
                    print(f"Harvested {len(emails)} emails for domain: {domain}")
                else:
                    print(f"JSON output file not found: {json_file}")
            else:
                print(f"Harvester failed for domain: {domain}")
        
        finally:
            # Clean up temporary files
            for ext in ['.json', '.xml']:
                temp_file_path = f"{temp_output}{ext}"
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except OSError as e:
                        print(f"Could not remove temporary file {temp_file_path}: {e}")
        
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
    # Go up two levels from addons/mail-harvester to geo_mail root
    geo_mail_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(geo_mail_root, 'config', 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def get_database_column_config(geo_config):
    """Get database column configuration from config."""
    return {
        'table_name': geo_config.get("Database", "table_name", fallback="companies"),
        'id_column': geo_config.get("Database", "id_column", fallback="id"),
        'name_column': geo_config.get("Database", "name_column", fallback="name"),
        'website_column': geo_config.get("Database", "website_column", fallback="website"),
        'existing_emails_column': geo_config.get("Database", "existing_emails_column", fallback="").strip()
    }

def process_single_company_harvester(harvester, company_data, db_path, thread_id=None):
    """Process a single company for email harvesting (thread-safe)."""

    company_id, company_name, website = company_data

    # Load database column configuration
    geo_config = load_geo_mail_config()
    db_config = get_database_column_config(geo_config)

    # Create a thread-local database manager for thread safety
    # Get the correct path to addons directory
    current_file = os.path.abspath(__file__)
    harvester_dir = os.path.dirname(current_file)        # addons/mail-harvester
    addons_dir = os.path.dirname(harvester_dir)          # addons

    # Import directly from the addons directory
    import importlib.util
    db_manager_path = os.path.join(addons_dir, 'database_manager.py')
    spec = importlib.util.spec_from_file_location("database_manager", db_manager_path)
    database_manager_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(database_manager_module)
    EmailDatabaseManager = database_manager_module.EmailDatabaseManager
    db_manager = EmailDatabaseManager(db_path, db_config['id_column'])

    thread_prefix = f"[Thread-{thread_id}] " if thread_id else ""

    print(f"{thread_prefix}Processing: {company_name} ({website})")

    company = CompanyInfo(
        id=company_id,
        name=company_name or "Unknown Company",
        website=website
    )

    try:
        emails = harvester.find_emails(company)

        if emails:
            # Store emails in database (thread-safe)
            email_data = {company_id: emails}
            added_count = db_manager.add_emails_batch(email_data)

            # Update company tracking (thread-safe)
            db_manager.update_company_methods(company_id, 'harvester', completed=True)

            print(f"{thread_prefix}  Harvested {len(emails)} emails, stored {added_count} in database")

            # Show all emails found
            for email_result in emails:
                print(f"{thread_prefix}    - {email_result.email}")

            return len(emails)
        else:
            print(f"{thread_prefix}  No emails harvested for {website}")
            # Still mark as completed even if no emails found
            db_manager.update_company_methods(company_id, 'harvester', completed=True)
            return 0

    except Exception as e:
        print(f"{thread_prefix}  Error processing {company_name}: {e}")
        # Mark as attempted but not completed
        db_manager.update_company_methods(company_id, 'harvester', completed=False)
        return 0

def process_all_companies_from_db(harvester, db_path, table_name, limit=None, offset=0, max_threads=2):
    """Process all companies from database using threading."""
    import sqlite3
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Load database column configuration
    geo_config = load_geo_mail_config()
    db_config = get_database_column_config(geo_config)

    # Initialize database manager for storing results and ensure schema
    # Get the correct path to addons directory
    current_file = os.path.abspath(__file__)
    harvester_dir = os.path.dirname(current_file)        # addons/mail-harvester
    addons_dir = os.path.dirname(harvester_dir)          # addons

    # Import directly from the addons directory
    import importlib.util
    db_manager_path = os.path.join(addons_dir, 'database_manager.py')
    spec = importlib.util.spec_from_file_location("database_manager", db_manager_path)
    database_manager_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(database_manager_module)
    EmailDatabaseManager = database_manager_module.EmailDatabaseManager
    db_manager = EmailDatabaseManager(db_path, db_config['id_column'])

    # Ensure both emails table and companies table have required columns
    db_manager.ensure_emails_table()
    db_manager.ensure_companies_table_columns()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get companies that need harvester email generation
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
            OR json_extract(email_methods_completed, '$') NOT LIKE '%"harvester"%'
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
        logger.info("No companies found that need harvester email generation")
        return

    logger.info(f"Processing {len(companies)} companies for email harvesting using {max_threads} threads...")

    total_emails_harvested = 0
    completed_count = 0

    # Use ThreadPoolExecutor for concurrent processing
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        # Submit all tasks
        future_to_company = {}
        for i, company_data in enumerate(companies):
            thread_id = (i % max_threads) + 1
            future = executor.submit(process_single_company_harvester, harvester, company_data, db_path, thread_id)
            future_to_company[future] = company_data

        # Process completed tasks
        for future in as_completed(future_to_company):
            company_data = future_to_company[future]
            _, company_name, _ = company_data  # Unpack only what we need
            completed_count += 1

            try:
                emails_count = future.result()
                total_emails_harvested += emails_count
                print(f"[{completed_count}/{len(companies)}] Completed: {company_name}")
            except Exception as e:
                print(f"[{completed_count}/{len(companies)}] Failed: {company_name} - {e}")

            # Small delay between processing completions to be respectful
            time.sleep(1)

    print(f"\nCompleted! Harvested {total_emails_harvested} total emails for {len(companies)} companies using {max_threads} threads")

def main():
    """Main function for standalone usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Harvest emails using theHarvester")
    parser.add_argument("--domain", help="Domain to harvest emails from")
    parser.add_argument("--company-id", type=int, help="Company ID from database")
    parser.add_argument("--all-companies", action="store_true", help="Process all companies from database that haven't been processed yet")
    parser.add_argument("--limit", type=int, help="Limit number of companies to process (if not set, processes all unprocessed companies)")
    parser.add_argument("--offset", type=int, default=0, help="Offset for database query")
    parser.add_argument("--sources", nargs='+', default=['bing', 'duckduckgo', 'yahoo'], help="Sources to use")
    parser.add_argument("--limit-per-source", type=int, default=100, help="Limit per source")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--threads", type=int, help="Number of concurrent threads for processing multiple companies")

    args = parser.parse_args()

    # Load configuration from geo_mail config
    try:
        geo_config = load_geo_mail_config()
        confidence = geo_config.getfloat("EmailFinders", "harvester_confidence", fallback=0.8)
        config_threads = geo_config.getint("EmailFinders", "harvester_threads", fallback=2)
    except:
        confidence = 0.8
        config_threads = 2

    # Get addon directory for relative paths
    addon_dir = os.path.dirname(os.path.abspath(__file__))

    # Configure addon
    config = {
        'sources': args.sources,
        'limit_per_source': args.limit_per_source,
        'timeout': args.timeout,
        'harvester_bin_path': os.path.join(addon_dir, 'bin/theHarvester'),
        'output_dir': os.path.join(addon_dir, 'output'),
        'confidence': confidence
    }

    # Use command line threads argument if provided, otherwise use config value
    threads_to_use = args.threads if args.threads is not None else config_threads

    harvester = MailHarvesterAddon(config)

    if not harvester.setup():
        print("Setup failed!")
        sys.exit(1)

    if args.domain:
        # Process specific domain
        company = CompanyInfo(
            id=0,
            name="Test Company",
            website=args.domain
        )

        emails = harvester.find_emails(company)

        print(f"\nFound {len(emails)} emails for {args.domain}:")
        for email_result in emails:
            print(f"  {email_result.email}")

    elif args.all_companies:
        # Process all companies from geo_mail database
        geo_config = load_geo_mail_config()
        db_name = geo_config.get("Database", "db_name", fallback="google_maps_companies.db")
        table_name = geo_config.get("Email", "table_name", fallback="companies")

        # Construct full database path (go up two levels from addons/mail-harvester to geo_mail root)
        geo_mail_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(geo_mail_root, db_name)

        print(f"Using database: {db_path}")
        print(f"Using table: {table_name}")
        print(f"Using sources: {args.sources}")
        print(f"Thread count: {threads_to_use}")

        process_all_companies_from_db(harvester, db_path, table_name, args.limit, args.offset, threads_to_use)

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
            emails = harvester.find_emails(company)

            print(f"Harvested {len(emails)} emails for company {company_id} ({company_name}):")
            for email_result in emails:
                print(f"  {email_result.email}")
        else:
            print(f"Company with ID {args.company_id} not found")

    else:
        print("Usage:")
        print("  --domain DOMAIN                    Harvest for specific domain")
        print("  --all-companies                    Process all unprocessed companies from geo_mail database")
        print("  --company-id ID                    Process specific company from database")
        print("  --limit N                          Limit number of companies (optional - processes all if not set)")
        print("  --offset N                         Offset for database query")
        print("  --sources SOURCE1 SOURCE2         theHarvester sources to use")
        print("  --threads N                        Number of concurrent threads (default: from config.ini)")
        sys.exit(1)

if __name__ == "__main__":
    main()
