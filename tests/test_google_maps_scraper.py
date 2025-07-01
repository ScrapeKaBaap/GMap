import unittest
import asyncio
import os

# Import module functions - ensure they are designed to be called externally
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.google_maps_scraper import GoogleMapsScraper
from modules.database_manager import DatabaseManager
from modules.config_manager import ConfigManager
from base_test import BaseAsyncTest

class TestGoogleMapsScraper(BaseAsyncTest):
    async def asyncSetUp(self):
        # Call parent setup
        await super().asyncSetUp()
        
        # Initialize scraper with config and database managers
        self.scraper = GoogleMapsScraper(config_manager=self.config_manager, db_manager=self.db_manager)

    async def test_scrape(self):
        # This is an integration test that will actually hit Google Maps
        # It's important to keep the max_companies_per_query low for testing purposes
        
        # Check if we should run in headless mode
        headless_mode = self.get_playwright_headless_setting()
        print(f"Running Playwright in headless mode: {headless_mode}")
        
        query = "tech companies in Australia"
        await self.scraper.scrape(query)

        # Verify that some companies were inserted into the database
        # We can't assert an exact number due to dynamic nature of web scraping
        # but we can check if at least one company was added.
        self.db_manager._connect() # Reconnect after scraper closes it
        self.db_manager.cursor.execute("SELECT COUNT(*) FROM companies WHERE search_query = ?", (query,))
        count = self.db_manager.cursor.fetchone()[0]
        self.assertGreater(count, 0, "No companies were scraped or inserted into the database.")

if __name__ == "__main__":
    unittest.main()


