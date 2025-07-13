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
Email Database Manager

Handles all database operations for the new emails table and company tracking.
"""

import sqlite3
import json
import sys
import os
from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from base_addon import EmailResult, CompanyInfo

class EmailDatabaseManager:
    """Manages database operations for the new email architecture."""
    
    def __init__(self, db_path: str):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def ensure_emails_table(self) -> bool:
        """
        Ensure the emails table exists with proper schema.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS emails (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_id INTEGER NOT NULL,
                        email TEXT NOT NULL,
                        source TEXT NOT NULL,
                        source_details TEXT,
                        confidence REAL DEFAULT 1.0,
                        metadata TEXT,  -- JSON
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Email validation fields
                        is_reachable TEXT,
                        mx_accepts_mail BOOLEAN,
                        records TEXT,
                        is_disposable BOOLEAN,
                        is_role_account BOOLEAN,
                        is_valid_syntax BOOLEAN,
                        can_connect_smtp BOOLEAN,
                        is_deliverable BOOLEAN,
                        is_catch_all BOOLEAN,
                        has_full_inbox BOOLEAN,
                        is_disabled BOOLEAN,
                        checked_at TIMESTAMP,
                        
                        FOREIGN KEY (company_id) REFERENCES companies (id),
                        UNIQUE(company_id, email)
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_company_id ON emails (company_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_source ON emails (source)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_email ON emails (email)")
                
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error creating emails table: {e}")
            return False
    
    def add_email(self, company_id: int, email_result: EmailResult) -> bool:
        """
        Add a single email to the database.
        
        Args:
            company_id: ID of the company
            email_result: EmailResult object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO emails 
                    (company_id, email, source, source_details, confidence, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    company_id,
                    email_result.email.lower().strip(),
                    email_result.source,
                    email_result.source_details,
                    email_result.confidence,
                    json.dumps(email_result.metadata) if email_result.metadata else None,
                    email_result.found_at
                ))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Error adding email {email_result.email}: {e}")
            return False
    
    def add_emails_batch(self, emails_data: Dict[int, List[EmailResult]]) -> int:
        """
        Add multiple emails to the database in batch.
        
        Args:
            emails_data: Dictionary mapping company_id to list of EmailResult objects
            
        Returns:
            Number of emails successfully added
        """
        added_count = 0
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for company_id, email_results in emails_data.items():
                    for email_result in email_results:
                        try:
                            cursor.execute("""
                                INSERT OR IGNORE INTO emails 
                                (company_id, email, source, source_details, confidence, metadata, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                company_id,
                                email_result.email.lower().strip(),
                                email_result.source,
                                email_result.source_details,
                                email_result.confidence,
                                json.dumps(email_result.metadata) if email_result.metadata else None,
                                email_result.found_at
                            ))
                            if cursor.rowcount > 0:
                                added_count += 1
                        except sqlite3.Error as e:
                            print(f"Error adding email {email_result.email} for company {company_id}: {e}")
                
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error in batch email insert: {e}")
        
        return added_count
    
    def get_company_emails(self, company_id: int, source: str = None) -> List[Dict[str, Any]]:
        """
        Get all emails for a company.
        
        Args:
            company_id: ID of the company
            source: Optional filter by source
            
        Returns:
            List of email dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if source:
                    cursor.execute("""
                        SELECT * FROM emails 
                        WHERE company_id = ? AND source = ?
                        ORDER BY created_at DESC
                    """, (company_id, source))
                else:
                    cursor.execute("""
                        SELECT * FROM emails 
                        WHERE company_id = ?
                        ORDER BY created_at DESC
                    """, (company_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting emails for company {company_id}: {e}")
            return []
    
    def get_unchecked_emails(self, limit: int = None, source: str = None) -> List[Dict[str, Any]]:
        """
        Get emails that haven't been checked yet.
        
        Args:
            limit: Maximum number of emails to return
            source: Optional filter by source
            
        Returns:
            List of email dictionaries
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT * FROM emails 
                    WHERE checked_at IS NULL
                """
                params = []
                
                if source:
                    query += " AND source = ?"
                    params.append(source)
                
                query += " ORDER BY created_at ASC"
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting unchecked emails: {e}")
            return []
    
    def update_email_check_results(self, email_id: int, check_results: Dict[str, Any]) -> bool:
        """
        Update email with validation results.
        
        Args:
            email_id: ID of the email record
            check_results: Dictionary with validation results
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Map check results to database columns
                update_fields = []
                params = []
                
                field_mapping = {
                    'is_reachable': 'is_reachable',
                    'mx_accepts_mail': 'mx_accepts_mail',
                    'records': 'records',
                    'is_disposable': 'is_disposable',
                    'is_role_account': 'is_role_account',
                    'is_valid_syntax': 'is_valid_syntax',
                    'can_connect_smtp': 'can_connect_smtp',
                    'is_deliverable': 'is_deliverable',
                    'is_catch_all': 'is_catch_all',
                    'has_full_inbox': 'has_full_inbox',
                    'is_disabled': 'is_disabled'
                }
                
                for result_key, db_column in field_mapping.items():
                    if result_key in check_results:
                        update_fields.append(f"{db_column} = ?")
                        value = check_results[result_key]
                        # Convert records to JSON string if it's a list
                        if result_key == 'records' and isinstance(value, list):
                            value = json.dumps(value)
                        params.append(value)
                
                # Always update checked_at
                update_fields.append("checked_at = ?")
                params.append(datetime.now())
                
                # Add email_id for WHERE clause
                params.append(email_id)
                
                if update_fields:
                    query = f"""
                        UPDATE emails 
                        SET {', '.join(update_fields)}
                        WHERE id = ?
                    """
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            print(f"Error updating email check results for ID {email_id}: {e}")
            return False
        
        return False
    
    def update_company_methods(self, company_id: int, method: str, completed: bool = True) -> bool:
        """
        Update tracking of which email finding methods were used for a company.
        
        Args:
            company_id: ID of the company
            method: Method name ('static', 'harvester', 'scraper')
            completed: Whether the method completed successfully
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current methods
                cursor.execute("""
                    SELECT email_methods_used, email_methods_completed 
                    FROM companies WHERE id = ?
                """, (company_id,))
                
                row = cursor.fetchone()
                if not row:
                    return False
                
                # Parse current methods
                used_methods = json.loads(row[0]) if row[0] else []
                completed_methods = json.loads(row[1]) if row[1] else []
                
                # Add method to used list if not already there
                if method not in used_methods:
                    used_methods.append(method)
                
                # Add to completed list if completed and not already there
                if completed and method not in completed_methods:
                    completed_methods.append(method)
                
                # Update database
                cursor.execute("""
                    UPDATE companies 
                    SET email_methods_used = ?, 
                        email_methods_completed = ?,
                        last_email_scan = ?
                    WHERE id = ?
                """, (
                    json.dumps(used_methods),
                    json.dumps(completed_methods),
                    datetime.now(),
                    company_id
                ))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            print(f"Error updating company methods for ID {company_id}: {e}")
            return False
    
    def get_companies_needing_method(self, method: str, limit: int = None) -> List[CompanyInfo]:
        """
        Get companies that haven't had a specific email finding method applied.
        
        Args:
            method: Method name to check for
            limit: Maximum number of companies to return
            
        Returns:
            List of CompanyInfo objects
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, name, website 
                    FROM companies 
                    WHERE website IS NOT NULL 
                    AND website != ''
                    AND (
                        email_methods_completed IS NULL 
                        OR email_methods_completed = '[]'
                        OR json_extract(email_methods_completed, '$') NOT LIKE ?
                    )
                    ORDER BY id ASC
                """
                
                params = [f'%"{method}"%']
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor.execute(query, params)
                
                companies = []
                for row in cursor.fetchall():
                    companies.append(CompanyInfo(
                        id=row[0],
                        name=row[1],
                        website=row[2]
                    ))
                
                return companies
                
        except sqlite3.Error as e:
            print(f"Error getting companies needing method {method}: {e}")
            return []
    
    def get_email_stats(self) -> Dict[str, Any]:
        """
        Get statistics about emails in the database.
        
        Returns:
            Dictionary with email statistics
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total emails
                cursor.execute("SELECT COUNT(*) FROM emails")
                stats['total_emails'] = cursor.fetchone()[0]
                
                # Emails by source
                cursor.execute("""
                    SELECT source, COUNT(*) 
                    FROM emails 
                    GROUP BY source
                """)
                stats['by_source'] = dict(cursor.fetchall())
                
                # Checked vs unchecked
                cursor.execute("SELECT COUNT(*) FROM emails WHERE checked_at IS NOT NULL")
                stats['checked_emails'] = cursor.fetchone()[0]
                stats['unchecked_emails'] = stats['total_emails'] - stats['checked_emails']
                
                # Companies with emails
                cursor.execute("SELECT COUNT(DISTINCT company_id) FROM emails")
                stats['companies_with_emails'] = cursor.fetchone()[0]
                
                return stats
                
        except sqlite3.Error as e:
            print(f"Error getting email stats: {e}")
            return {}
