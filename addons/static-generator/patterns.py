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
Email Pattern Definitions

Contains predefined email patterns and their confidence scores.
"""

from typing import Dict, List

# Common email patterns with confidence scores
EMAIL_PATTERNS = {
    # High confidence - very common
    'info': {
        'confidence': 0.95,
        'description': 'General information email',
        'category': 'general'
    },
    'contact': {
        'confidence': 0.90,
        'description': 'Contact/inquiry email',
        'category': 'general'
    },
    'hello': {
        'confidence': 0.85,
        'description': 'Friendly contact email',
        'category': 'general'
    },
    
    # Medium-high confidence - business common
    'sales': {
        'confidence': 0.80,
        'description': 'Sales inquiries',
        'category': 'business'
    },
    'support': {
        'confidence': 0.80,
        'description': 'Customer support',
        'category': 'support'
    },
    'help': {
        'confidence': 0.75,
        'description': 'Help and support',
        'category': 'support'
    },
    'service': {
        'confidence': 0.75,
        'description': 'Customer service',
        'category': 'support'
    },
    
    # HR and recruitment
    'hr': {
        'confidence': 0.70,
        'description': 'Human resources',
        'category': 'hr'
    },
    'careers': {
        'confidence': 0.70,
        'description': 'Career opportunities',
        'category': 'hr'
    },
    'jobs': {
        'confidence': 0.65,
        'description': 'Job applications',
        'category': 'hr'
    },
    'recruitment': {
        'confidence': 0.65,
        'description': 'Recruitment team',
        'category': 'hr'
    },
    
    # Business development
    'business': {
        'confidence': 0.70,
        'description': 'Business inquiries',
        'category': 'business'
    },
    'partnerships': {
        'confidence': 0.60,
        'description': 'Partnership opportunities',
        'category': 'business'
    },
    'bd': {
        'confidence': 0.60,
        'description': 'Business development',
        'category': 'business'
    },
    
    # Marketing and media
    'marketing': {
        'confidence': 0.65,
        'description': 'Marketing team',
        'category': 'marketing'
    },
    'media': {
        'confidence': 0.60,
        'description': 'Media inquiries',
        'category': 'marketing'
    },
    'press': {
        'confidence': 0.60,
        'description': 'Press inquiries',
        'category': 'marketing'
    },
    
    # Technical
    'admin': {
        'confidence': 0.65,
        'description': 'Administrative contact',
        'category': 'technical'
    },
    'webmaster': {
        'confidence': 0.55,
        'description': 'Website administrator',
        'category': 'technical'
    },
    'it': {
        'confidence': 0.60,
        'description': 'IT department',
        'category': 'technical'
    },
    
    # Finance and legal
    'finance': {
        'confidence': 0.60,
        'description': 'Finance department',
        'category': 'finance'
    },
    'accounting': {
        'confidence': 0.60,
        'description': 'Accounting department',
        'category': 'finance'
    },
    'legal': {
        'confidence': 0.55,
        'description': 'Legal department',
        'category': 'legal'
    },
    
    # Lower confidence - less common but possible
    'office': {
        'confidence': 0.50,
        'description': 'General office',
        'category': 'general'
    },
    'team': {
        'confidence': 0.50,
        'description': 'General team email',
        'category': 'general'
    },
    'mail': {
        'confidence': 0.45,
        'description': 'General mail',
        'category': 'general'
    }
}

# Pattern categories for filtering
PATTERN_CATEGORIES = {
    'general': ['info', 'contact', 'hello', 'office', 'team', 'mail'],
    'business': ['sales', 'business', 'partnerships', 'bd'],
    'support': ['support', 'help', 'service'],
    'hr': ['hr', 'careers', 'jobs', 'recruitment'],
    'marketing': ['marketing', 'media', 'press'],
    'technical': ['admin', 'webmaster', 'it'],
    'finance': ['finance', 'accounting'],
    'legal': ['legal']
}

def get_patterns_by_category(categories: List[str] = None) -> Dict[str, Dict]:
    """
    Get email patterns filtered by category.
    
    Args:
        categories: List of categories to include. If None, returns all patterns.
        
    Returns:
        Dictionary of filtered patterns
    """
    if categories is None:
        return EMAIL_PATTERNS
    
    filtered_patterns = {}
    for category in categories:
        if category in PATTERN_CATEGORIES:
            for pattern in PATTERN_CATEGORIES[category]:
                if pattern in EMAIL_PATTERNS:
                    filtered_patterns[pattern] = EMAIL_PATTERNS[pattern]
    
    return filtered_patterns

def get_high_confidence_patterns(min_confidence: float = 0.8) -> Dict[str, Dict]:
    """
    Get patterns with confidence above threshold.
    
    Args:
        min_confidence: Minimum confidence score (0.0 to 1.0)
        
    Returns:
        Dictionary of high-confidence patterns
    """
    return {
        pattern: data 
        for pattern, data in EMAIL_PATTERNS.items() 
        if data['confidence'] >= min_confidence
    }

def get_patterns_for_company_type(company_name: str, website: str = None) -> Dict[str, Dict]:
    """
    Get recommended patterns based on company information.
    
    Args:
        company_name: Name of the company
        website: Company website (optional)
        
    Returns:
        Dictionary of recommended patterns
    """
    # Start with high-confidence general patterns
    recommended = get_patterns_by_category(['general'])
    
    # Add business patterns for all companies
    recommended.update(get_patterns_by_category(['business']))
    
    # Analyze company name/website for specific patterns
    text_to_analyze = (company_name + ' ' + (website or '')).lower()
    
    # Tech companies - add technical patterns
    tech_keywords = ['tech', 'software', 'digital', 'it', 'computer', 'data', 'ai', 'ml']
    if any(keyword in text_to_analyze for keyword in tech_keywords):
        recommended.update(get_patterns_by_category(['technical']))
    
    # Service companies - add support patterns
    service_keywords = ['service', 'support', 'consulting', 'solutions']
    if any(keyword in text_to_analyze for keyword in service_keywords):
        recommended.update(get_patterns_by_category(['support']))
    
    # Large companies - add HR and marketing
    large_company_keywords = ['corp', 'corporation', 'inc', 'ltd', 'group', 'holdings']
    if any(keyword in text_to_analyze for keyword in large_company_keywords):
        recommended.update(get_patterns_by_category(['hr', 'marketing']))
    
    return recommended
