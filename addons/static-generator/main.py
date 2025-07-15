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
Static Email Generator Addon

Generates common email patterns for companies based on their domain.
This addon creates emails like info@domain.com, contact@domain.com, etc.

Usage:
    python main.py --domain example.com
    python main.py --company-id 123 --db-path ../database.db
"""

import argparse
import sys
import os
from typing import List, Dict, Any
from urllib.parse import urlparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_addon import EmailFinderAddon, EmailResult, CompanyInfo
from patterns import EMAIL_PATTERNS, get_patterns_for_company_type, get_high_confidence_patterns
from addon_logger import setup_addon_logging

# Set up logging for this addon
logger = setup_addon_logging("static-generator")

class StaticEmailGenerator(EmailFinderAddon):
    """
    Static email pattern generator addon.
    
    Generates common email addresses based on predefined patterns.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the static email generator.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.patterns = self._load_patterns()
        self.min_confidence = self.config.get('min_confidence', 0.5)
        self.max_emails = self.config.get('max_emails', 10)
        self.smart_selection = self.config.get('smart_selection', True)
    
    def get_source_name(self) -> str:
        """Return the source name for this addon."""
        return 'static'
    
    def _load_patterns(self) -> Dict[str, Dict]:
        """Load email patterns based on configuration."""
        # Get patterns from config or use defaults
        pattern_names = self.config.get('patterns', None)
        categories = self.config.get('categories', None)
        min_confidence = self.config.get('min_confidence', 0.5)

        # Load patterns
        if pattern_names:
            # Use specific patterns
            patterns = {
                name: EMAIL_PATTERNS[name].copy()
                for name in pattern_names
                if name in EMAIL_PATTERNS
            }
        elif categories:
            # Use patterns from specific categories
            from patterns import get_patterns_by_category
            patterns = get_patterns_by_category(categories)
        else:
            # Use high-confidence patterns by default
            patterns = get_high_confidence_patterns(min_confidence)

        # Override confidence scores from config if available
        self._apply_config_confidence(patterns)
        return patterns

    def _apply_config_confidence(self, patterns: Dict[str, Dict]):
        """Apply confidence scores from configuration."""
        # Try to load geo_mail config for confidence overrides
        try:
            geo_config = load_geo_mail_config()
            for pattern_name in patterns:
                config_key = f"static_confidence_{pattern_name}"
                if geo_config.has_option("EmailFinders", config_key):
                    new_confidence = geo_config.getfloat("EmailFinders", config_key)
                    patterns[pattern_name]['confidence'] = new_confidence
                    logger.debug(f"Updated confidence for {pattern_name}: {new_confidence}")
        except Exception as e:
            logger.debug(f"Could not load geo_mail config for confidence: {e}")
    
    def _clean_domain(self, domain: str) -> str:
        """
        Clean and normalize domain.
        
        Args:
            domain: Raw domain or URL
            
        Returns:
            Cleaned domain
        """
        if not domain:
            return ""
        
        # Remove protocol if present
        if domain.startswith(('http://', 'https://')):
            parsed = urlparse(domain)
            domain = parsed.netloc
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Remove path, query, fragment
        domain = domain.split('/')[0].split('?')[0].split('#')[0]
        
        return domain.lower().strip()
    
    def _is_valid_domain(self, domain: str) -> bool:
        """
        Check if domain is valid for email generation.
        
        Args:
            domain: Domain to validate
            
        Returns:
            True if domain is valid
        """
        if not domain or '.' not in domain:
            return False
        
        # Basic domain validation
        import re
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+$'
        return bool(re.match(pattern, domain))
    
    def find_emails(self, company: CompanyInfo) -> List[EmailResult]:
        """
        Generate static email patterns for a company.
        
        Args:
            company: Company information
            
        Returns:
            List of EmailResult objects
        """
        results = []
        
        # Clean and validate domain
        domain = self._clean_domain(company.website)
        if not self._is_valid_domain(domain):
            print(f"Invalid domain for company {company.id}: {domain}")
            return results
        
        # Get patterns for this company
        if self.smart_selection:
            patterns = get_patterns_for_company_type(company.name, company.website)
        else:
            patterns = self.patterns
        
        # Filter by confidence and limit
        filtered_patterns = {
            name: data for name, data in patterns.items()
            if data['confidence'] >= self.min_confidence
        }
        
        # Sort by confidence (highest first)
        sorted_patterns = sorted(
            filtered_patterns.items(),
            key=lambda x: x[1]['confidence'],
            reverse=True
        )
        
        # Generate emails up to max_emails limit
        for pattern_name, pattern_data in sorted_patterns[:self.max_emails]:
            email = f"{pattern_name}@{domain}"
            
            result = EmailResult(
                email=email,
                source=self.get_source_name(),
                source_details=f"Static pattern: {pattern_data['description']}",
                confidence=pattern_data['confidence'],
                metadata={
                    'pattern': pattern_name,
                    'category': pattern_data['category'],
                    'domain': domain
                }
            )
            
            results.append(result)
        
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
        
        domain = self._clean_domain(company.website)
        return self._is_valid_domain(domain)

def load_geo_mail_config():
    """Load configuration from geo_mail config/config.ini."""
    import configparser
    # Go up two levels from addons/static-generator to geo_mail root
    geo_mail_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(geo_mail_root, 'config', 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def process_all_companies_from_db(generator, db_path, table_name, limit=None, offset=0):
    """Process all companies from database."""
    import sqlite3

    # Initialize database manager for storing results and ensure schema
    # Get the geo_mail root directory (parent of addons)
    current_file = os.path.abspath(__file__)
    static_generator_dir = os.path.dirname(current_file)  # addons/static-generator
    addons_dir = os.path.dirname(static_generator_dir)    # addons
    geo_mail_root = os.path.dirname(addons_dir)           # geo_mail

    # Import directly from the addons directory
    import importlib.util
    db_manager_path = os.path.join(addons_dir, 'database_manager.py')
    spec = importlib.util.spec_from_file_location("database_manager", db_manager_path)
    database_manager_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(database_manager_module)
    EmailDatabaseManager = database_manager_module.EmailDatabaseManager
    db_manager = EmailDatabaseManager(db_path)

    # Ensure both emails table and companies table have required columns
    db_manager.ensure_emails_table()
    db_manager.ensure_companies_table_columns()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get companies that need static email generation
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
            OR json_extract(email_methods_completed, '$') NOT LIKE '%"static"%'
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
        logger.info("No companies found that need static email generation")
        return

    logger.info(f"Processing {len(companies)} companies for static email generation...")

    total_emails_generated = 0

    for i, (company_id, company_name, website) in enumerate(companies, 1):
        logger.info(f"Processing {i}/{len(companies)}: {company_name} ({website})")

        company = CompanyInfo(
            id=company_id,
            name=company_name or "Unknown Company",
            website=website
        )

        try:
            emails = generator.find_emails(company)

            if emails:
                # Store emails in database
                email_data = {company_id: emails}
                added_count = db_manager.add_emails_batch(email_data)

                # Update company tracking
                db_manager.update_company_methods(company_id, 'static', completed=True)

                total_emails_generated += len(emails)
                logger.info(f"  Generated {len(emails)} emails, stored {added_count} in database")

                # Show first few emails
                for email_result in emails[:3]:
                    logger.info(f"    - {email_result.email} (confidence: {email_result.confidence:.2f})")
                if len(emails) > 3:
                    logger.info(f"    ... and {len(emails) - 3} more")
            else:
                logger.info(f"  No emails generated for {website}")
                # Still mark as completed even if no emails found
                db_manager.update_company_methods(company_id, 'static', completed=True)

        except Exception as e:
            logger.error(f"  Error processing {company_name}: {e}")
            # Mark as attempted but not completed
            db_manager.update_company_methods(company_id, 'static', completed=False)

    logger.info(f"\nCompleted! Generated {total_emails_generated} total emails for {len(companies)} companies")

def main():
    """Main function for standalone usage."""
    parser = argparse.ArgumentParser(description="Generate static email patterns")
    parser.add_argument("--domain", help="Domain to generate emails for")
    parser.add_argument("--company-name", help="Company name for smart pattern selection")
    parser.add_argument("--company-id", type=int, help="Company ID from database")
    parser.add_argument("--all-companies", action="store_true", help="Process all companies from database that haven't been processed yet")
    parser.add_argument("--limit", type=int, help="Limit number of companies to process (if not set, processes all unprocessed companies)")
    parser.add_argument("--offset", type=int, default=0, help="Offset for database query")
    parser.add_argument("--patterns", nargs='+', help="Specific patterns to use")
    parser.add_argument("--min-confidence", type=float, default=0.7, help="Minimum confidence score")
    parser.add_argument("--max-emails", type=int, default=8, help="Maximum emails to generate")

    args = parser.parse_args()

    # Configure addon
    config = {
        'min_confidence': args.min_confidence,
        'max_emails': args.max_emails,
        'smart_selection': True
    }

    if args.patterns:
        config['patterns'] = args.patterns

    generator = StaticEmailGenerator(config)

    if args.domain:
        # Generate for specific domain
        company = CompanyInfo(
            id=0,
            name=args.company_name or "Unknown Company",
            website=args.domain
        )

        emails = generator.find_emails(company)

        logger.info(f"Generated {len(emails)} emails for {args.domain}:")
        for email_result in emails:
            logger.info(f"  {email_result.email} (confidence: {email_result.confidence:.2f})")

    elif args.all_companies:
        # Process all companies from geo_mail database
        geo_config = load_geo_mail_config()
        db_name = geo_config.get("Database", "db_name", fallback="google_maps_companies.db")
        table_name = geo_config.get("Email", "table_name", fallback="companies")

        # Construct full database path (go up two levels from addons/static-generator to geo_mail root)
        geo_mail_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(geo_mail_root, db_name)

        logger.info(f"Using database: {db_path}")
        logger.info(f"Using table: {table_name}")

        process_all_companies_from_db(generator, db_path, table_name, args.limit, args.offset)

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
            emails = generator.find_emails(company)

            print(f"Generated {len(emails)} emails for company {company_id} ({company_name}):")
            for email_result in emails:
                print(f"  {email_result.email} (confidence: {email_result.confidence:.2f})")
        else:
            print(f"Company with ID {args.company_id} not found")

    else:
        print("Usage:")
        print("  --domain DOMAIN                    Generate for specific domain")
        print("  --all-companies                    Process all unprocessed companies from geo_mail database")
        print("  --company-id ID                    Process specific company from database")
        print("  --limit N                          Limit number of companies (optional - processes all if not set)")
        print("  --offset N                         Offset for database query")
        sys.exit(1)

if __name__ == "__main__":
    main()
