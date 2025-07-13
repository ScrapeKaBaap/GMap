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
Utility functions for email harvesting operations.

This module provides helper functions for domain validation, email processing,
and result formatting.
"""

import re
import json
from urllib.parse import urlparse
from typing import Set, List, Dict, Optional, Any
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.logger_config import logger

def normalize_domain(domain: str) -> Optional[str]:
    """
    Normalize domain to standard format.
    Removes protocol, www, paths, and converts to lowercase.
    
    Examples:
        https://www.example.com/path -> example.com
        HTTP://EXAMPLE.COM -> example.com
        www.example.com -> example.com
    """
    if not domain or not isinstance(domain, str):
        return None
    
    domain = domain.strip()
    
    # Remove protocol
    if domain.startswith(('http://', 'https://', 'ftp://', 'ftps://')):
        parsed = urlparse(domain)
        domain = parsed.netloc
    
    # Remove www prefix
    if domain.startswith('www.'):
        domain = domain[4:]
    
    # Remove port if present
    domain = domain.split(':')[0]
    
    # Remove path, query, fragment
    domain = domain.split('/')[0].split('?')[0].split('#')[0]
    
    # Convert to lowercase
    domain = domain.lower()
    
    return domain if domain else None

def is_valid_domain(domain: str) -> bool:
    """
    Validate domain format using regex.
    Returns True if domain appears to be valid, False otherwise.
    """
    if not domain or not isinstance(domain, str):
        return False
    
    # Normalize first
    domain = normalize_domain(domain)
    if not domain:
        return False
    
    # Basic domain validation regex
    # Allows letters, numbers, hyphens, and dots
    # Must have at least one dot
    # Cannot start or end with hyphen
    # Cannot have consecutive dots
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+$'
    
    if not re.match(pattern, domain):
        return False
    
    # Additional checks
    if '..' in domain:  # No consecutive dots
        return False
    
    if domain.startswith('.') or domain.endswith('.'):  # No leading/trailing dots
        return False
    
    # Must have at least one dot
    if '.' not in domain:
        return False
    
    # Check TLD length (at least 2 characters)
    tld = domain.split('.')[-1]
    if len(tld) < 2:
        return False
    
    return True

def validate_email(email: str) -> bool:
    """
    Validate email address format.
    Returns True if email appears to be valid, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False
    
    email = email.strip().lower()
    
    # Basic email validation regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False
    
    # Additional checks
    local, domain = email.split('@', 1)
    
    # Local part checks
    if len(local) > 64:  # Local part too long
        return False
    
    if local.startswith('.') or local.endswith('.'):  # No leading/trailing dots in local
        return False
    
    if '..' in local:  # No consecutive dots in local
        return False
    
    # Domain part checks
    if not is_valid_domain(domain):
        return False
    
    return True

def extract_emails_from_text(text: str) -> Set[str]:
    """
    Extract email addresses from text using regex.
    Returns a set of unique valid email addresses.
    """
    if not text or not isinstance(text, str):
        return set()
    
    # Email regex pattern
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    
    # Find all potential emails
    potential_emails = re.findall(email_pattern, text, re.IGNORECASE)
    
    # Validate and normalize emails
    valid_emails = set()
    for email in potential_emails:
        if validate_email(email):
            valid_emails.add(email.lower().strip())
    
    return valid_emails

def filter_emails_by_domain(emails: Set[str], target_domain: str) -> Set[str]:
    """
    Filter emails to only include those from the target domain.
    Returns a set of emails that belong to the target domain.
    """
    if not emails or not target_domain:
        return set()
    
    target_domain = normalize_domain(target_domain)
    if not target_domain:
        return set()
    
    filtered_emails = set()
    for email in emails:
        if validate_email(email):
            email_domain = email.split('@')[1].lower()
            if email_domain == target_domain:
                filtered_emails.add(email)
    
    return filtered_emails

def deduplicate_emails(email_sets: List[Set[str]]) -> Set[str]:
    """
    Combine multiple sets of emails and remove duplicates.
    Returns a single set of unique emails.
    """
    all_emails = set()
    for email_set in email_sets:
        if isinstance(email_set, set):
            all_emails.update(email_set)
        elif isinstance(email_set, (list, tuple)):
            all_emails.update(email_set)
    
    return all_emails

def format_emails_for_display(emails: Set[str], max_display: int = 10) -> str:
    """
    Format emails for display in logs.
    Returns a formatted string with limited number of emails.
    """
    if not emails:
        return "No emails"
    
    sorted_emails = sorted(emails)
    
    if len(sorted_emails) <= max_display:
        return ", ".join(sorted_emails)
    else:
        displayed = sorted_emails[:max_display]
        remaining = len(sorted_emails) - max_display
        return f"{', '.join(displayed)} ... and {remaining} more"

def emails_to_json(emails: Set[str]) -> str:
    """
    Convert set of emails to JSON string for database storage.
    Returns JSON string representation of the email list.
    """
    if not emails:
        return "[]"
    
    try:
        return json.dumps(sorted(list(emails)))
    except (TypeError, ValueError) as e:
        logger.error(f"Error converting emails to JSON: {e}")
        return "[]"

def emails_from_json(json_str: str) -> Set[str]:
    """
    Convert JSON string to set of emails.
    Returns set of emails from JSON string.
    """
    if not json_str or json_str.strip() == "":
        return set()
    
    try:
        email_list = json.loads(json_str)
        if isinstance(email_list, list):
            return set(email for email in email_list if validate_email(email))
        else:
            return set()
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Error parsing emails from JSON: {e}")
        return set()

def get_domain_from_email(email: str) -> Optional[str]:
    """
    Extract domain from email address.
    Returns the domain part of the email or None if invalid.
    """
    if not validate_email(email):
        return None
    
    return email.split('@')[1].lower()

def group_emails_by_domain(emails: Set[str]) -> Dict[str, Set[str]]:
    """
    Group emails by their domain.
    Returns a dictionary mapping domain -> set of emails.
    """
    domain_groups = {}
    
    for email in emails:
        if validate_email(email):
            domain = get_domain_from_email(email)
            if domain:
                if domain not in domain_groups:
                    domain_groups[domain] = set()
                domain_groups[domain].add(email)
    
    return domain_groups

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations.
    Removes or replaces unsafe characters.
    """
    if not filename:
        return "unnamed"
    
    # Replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure it's not empty
    if not filename:
        filename = "unnamed"
    
    return filename

def create_summary_report(results: Dict[str, Any]) -> str:
    """
    Create a summary report of harvesting results.
    Returns a formatted string with statistics and highlights.
    """
    if not results:
        return "No results to report"
    
    total_domains = len(results)
    total_emails = sum(len(emails) for emails in results.values() if isinstance(emails, (set, list)))
    domains_with_emails = sum(1 for emails in results.values() if emails and len(emails) > 0)
    
    report_lines = [
        "=== Email Harvesting Summary ===",
        f"Total domains processed: {total_domains}",
        f"Domains with emails found: {domains_with_emails}",
        f"Total unique emails found: {total_emails}",
        f"Success rate: {(domains_with_emails/total_domains*100):.1f}%" if total_domains > 0 else "Success rate: 0%",
        "",
        "Top domains by email count:"
    ]
    
    # Sort domains by email count
    sorted_domains = sorted(
        [(domain, emails) for domain, emails in results.items() if emails],
        key=lambda x: len(x[1]) if isinstance(x[1], (set, list)) else 0,
        reverse=True
    )
    
    for i, (domain, emails) in enumerate(sorted_domains[:10], 1):
        email_count = len(emails) if isinstance(emails, (set, list)) else 0
        report_lines.append(f"  {i}. {domain}: {email_count} emails")
    
    return "\n".join(report_lines)
