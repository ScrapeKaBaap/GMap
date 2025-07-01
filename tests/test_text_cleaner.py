#!/usr/bin/env python3
"""
Test script to demonstrate the text cleaner functionality in GoogleMapsScraper.
"""

import sys
import os

# Add the modules directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from google_maps_scraper import GoogleMapsScraper

def test_text_cleaner():
    """Test the text cleaning methods with various input scenarios."""
    scraper = GoogleMapsScraper()
    
    print("=== Testing Text Cleaner ===\n")
    
    # Test clean_text method
    print("1. Testing clean_text method:")
    test_texts = [
        "Normal Company Name",
        "Company 😀 with emoji",
        "Text   with    multiple   spaces",
        "Company™ with trademark",
        "Café & Restaurant",
        "🏢 Office Building 🏢",
        "   Leading and trailing spaces   ",
        "",
        None,
        "Company\nwith\nnewlines",
        "Special•Characters★Here",
    ]
    
    for text in test_texts:
        cleaned = scraper.clean_text(text)
        print(f"  Input:  '{text}' -> Output: '{cleaned}'")
    
    print("\n2. Testing clean_phone method:")
    test_phones = [
        "+61 123 456 789",
        "📞 +61-123-456-789",
        "(02) 1234-5678",
        "Phone: +61 123 456 789 📱",
        "123.456.7890",
        "+61 😊 123 456 789",
        "",
        None,
    ]
    
    for phone in test_phones:
        cleaned = scraper.clean_phone(phone)
        print(f"  Input:  '{phone}' -> Output: '{cleaned}'")
    
    print("\n3. Testing clean_email method:")
    test_emails = [
        "user@example.com",
        "📧 contact@company.com",
        "email: info@test.org 📮",
        "user+tag@domain.co.uk",
        "invalid-email",
        "user@😊domain.com",
        "",
        None,
    ]
    
    for email in test_emails:
        cleaned = scraper.clean_email(email)
        print(f"  Input:  '{email}' -> Output: '{cleaned}'")
    
    print("\n4. Testing clean_website method:")
    test_websites = [
        "https://www.example.com",
        "🌐 https://company.com",
        "www.test.org/path?param=value",
        "http://😊emoji.com",
        "company.com",
        "",
        None,
    ]
    
    for website in test_websites:
        cleaned = scraper.clean_website(website)
        print(f"  Input:  '{website}' -> Output: '{cleaned}'")
    
    print("\n=== Text Cleaner Test Complete ===")

if __name__ == "__main__":
    test_text_cleaner()
