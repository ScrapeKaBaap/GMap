import asyncio
import os

# Import module functions - ensure they are designed to be called externally
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.config_manager import ConfigManager
from modules.google_maps_scraper import GoogleMapsScraper
from modules.logger_config import setup_logging

logger = setup_logging()

async def main():
    config_manager = ConfigManager()
    scraper = GoogleMapsScraper()

    search_query_templates = config_manager.get("Search", "search_query_templates").split(", ")
    
    # Generate search queries dynamically
    queries = []
    for template in search_query_templates:
        # Simple substitution for now, can be expanded for more complex logic
        if "${country}" in template:
            countries = config_manager.get("Search", "country").split(", ")
            for country in countries:
                queries.append(template.replace("${country}", country))
        elif "${state}" in template:
            states = config_manager.get("Search", "state").split(", ")
            for state in states:
                queries.append(template.replace("${state}", state))
        else:
            queries.append(template)

    logger.info(f"Generated search queries: {queries}")

    for query in queries:
        logger.info(f"Processing query: {query}")
        await scraper.scrape(query)

if __name__ == "__main__":
    asyncio.run(main())


