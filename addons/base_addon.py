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
Base Email Addon Interface

This module defines the standard interface that all email addons must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class EmailResult:
    """Standard result format for email operations."""
    email: str
    source: str  # 'static', 'harvester', 'scraper', 'checker'
    source_details: str
    confidence: float = 1.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = None
    found_at: datetime = None
    
    def __post_init__(self):
        if self.found_at is None:
            self.found_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CompanyInfo:
    """Company information for email finding."""
    id: int
    name: str
    website: str
    domain: str = None
    
    def __post_init__(self):
        if self.domain is None and self.website:
            # Extract domain from website
            from urllib.parse import urlparse
            parsed = urlparse(self.website if self.website.startswith('http') else f'http://{self.website}')
            self.domain = parsed.netloc.lower()
            if self.domain.startswith('www.'):
                self.domain = self.domain[4:]

class BaseEmailAddon(ABC):
    """
    Base class for all email addons.
    
    All email addons must inherit from this class and implement the required methods.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the addon with configuration.
        
        Args:
            config: Dictionary containing addon-specific configuration
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        self.version = "1.0.0"
    
    @abstractmethod
    def get_addon_type(self) -> str:
        """
        Return the type of this addon.
        
        Returns:
            One of: 'finder', 'checker', 'validator'
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """
        Return the source name for emails found by this addon.
        
        Returns:
            Source identifier (e.g., 'static', 'harvester', 'scraper')
        """
        pass
    
    def is_enabled(self) -> bool:
        """
        Check if this addon is enabled in configuration.
        
        Returns:
            True if addon should be used, False otherwise
        """
        return self.config.get('enabled', True)
    
    def get_priority(self) -> int:
        """
        Get the execution priority of this addon.
        Lower numbers = higher priority.
        
        Returns:
            Priority number (default: 100)
        """
        return self.config.get('priority', 100)
    
    def validate_company(self, company: CompanyInfo) -> bool:
        """
        Check if this addon can process the given company.
        
        Args:
            company: Company information
            
        Returns:
            True if addon can process this company
        """
        return True
    
    def setup(self) -> bool:
        """
        Perform any setup required before processing.
        
        Returns:
            True if setup successful, False otherwise
        """
        return True
    
    def cleanup(self):
        """Perform any cleanup after processing."""
        pass

class EmailFinderAddon(BaseEmailAddon):
    """Base class for email finding addons."""
    
    def get_addon_type(self) -> str:
        return 'finder'
    
    @abstractmethod
    def find_emails(self, company: CompanyInfo) -> List[EmailResult]:
        """
        Find emails for a company.
        
        Args:
            company: Company information
            
        Returns:
            List of EmailResult objects
        """
        pass
    
    def find_emails_batch(self, companies: List[CompanyInfo]) -> Dict[int, List[EmailResult]]:
        """
        Find emails for multiple companies.
        
        Args:
            companies: List of company information
            
        Returns:
            Dictionary mapping company_id to list of EmailResult objects
        """
        results = {}
        for company in companies:
            try:
                results[company.id] = self.find_emails(company)
            except Exception as e:
                print(f"Error finding emails for company {company.id}: {e}")
                results[company.id] = []
        return results

class EmailCheckerAddon(BaseEmailAddon):
    """Base class for email checking/validation addons."""
    
    def get_addon_type(self) -> str:
        return 'checker'
    
    @abstractmethod
    def check_email(self, email: str, company_id: int = None) -> Dict[str, Any]:
        """
        Check/validate an email address.
        
        Args:
            email: Email address to check
            company_id: Optional company ID for context
            
        Returns:
            Dictionary with validation results
        """
        pass
    
    def check_emails_batch(self, emails: List[str], company_ids: List[int] = None) -> List[Dict[str, Any]]:
        """
        Check multiple email addresses.
        
        Args:
            emails: List of email addresses
            company_ids: Optional list of company IDs
            
        Returns:
            List of validation result dictionaries
        """
        if company_ids is None:
            company_ids = [None] * len(emails)
        
        results = []
        for email, company_id in zip(emails, company_ids):
            try:
                results.append(self.check_email(email, company_id))
            except Exception as e:
                print(f"Error checking email {email}: {e}")
                results.append({'email': email, 'error': str(e)})
        return results
