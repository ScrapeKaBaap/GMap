import asyncio
import os

# Import module functions - ensure they are designed to be called externally
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.config_manager import ConfigManager
from modules.google_maps_scraper import GoogleMapsScraper
from modules.logger_config import setup_logging
from modules.internet_utils import wait_for_internet, InternetRestoredException

logger = setup_logging()

async def main():
    # Check internet connection before starting
    wait_for_internet()
    
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
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                retry_count += 1
                logger.info(f"Processing query: {query} - Attempt {retry_count}/{max_retries}")
                
                # Check internet connection before processing each query
                wait_for_internet(raise_on_restore=True)
                
                await scraper.scrape(query)
                
                # Successfully processed the query - break the retry loop
                break
                
            except InternetRestoredException:
                logger.warning(f"Internet connection restored during processing query '{query}'. Retrying (Attempt {retry_count}/{max_retries})...")
                if retry_count >= max_retries:
                    logger.error(f"Failed to process query '{query}' after {max_retries} attempts due to repeated internet interruptions.")
                    continue  # Continue with next query
                continue
                
            except Exception as e:
                logger.error(f"Error processing query '{query}' on attempt {retry_count}: {e}")
                if retry_count >= max_retries:
                    logger.error(f"Failed to process query '{query}' after {max_retries} attempts. Moving to next query.")
                    break  # Move to next query
                # Wait a bit before retrying
                import time
                time.sleep(2)
                continue
    
    logger.info("Main scraping process completed.")

if __name__ == "__main__":
    asyncio.run(main())


