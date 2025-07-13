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
from modules.browser_handler import (
    launch_browser_async, 
    create_context_with_cookies_async, 
    get_parallel_query_count
)

logger = setup_logging()

async def process_query(scraper, query, context, semaphore):
    """Process a single query with the given context and semaphore for rate limiting."""
    async with semaphore:
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                retry_count += 1
                logger.info(f"Processing query: {query} - Attempt {retry_count}/{max_retries}")
                
                # Check internet connection before processing each query
                wait_for_internet(raise_on_restore=True)
                
                await scraper.scrape(query, context)
                
                # Successfully processed the query - break the retry loop
                break
                
            except InternetRestoredException:
                logger.warning(f"Internet connection restored during processing query '{query}'. Retrying (Attempt {retry_count}/{max_retries})...")
                if retry_count >= max_retries:
                    logger.error(f"Failed to process query '{query}' after {max_retries} attempts due to repeated internet interruptions.")
                    return
                continue
                
            except Exception as e:
                logger.error(f"Error processing query '{query}' on attempt {retry_count}: {e}")
                if retry_count >= max_retries:
                    logger.error(f"Failed to process query '{query}' after {max_retries} attempts.")
                    return
                # Wait a bit before retrying
                await asyncio.sleep(2)
                continue

async def main():
    # Check internet connection before starting
    wait_for_internet()
    
    config_manager = ConfigManager()
    scraper = GoogleMapsScraper()

    # Get parallel query count from config
    parallel_query_count = get_parallel_query_count()
    headless = config_manager.getboolean("Playwright", "headless", fallback=True)
    
    # Validate parallel_query_count
    if parallel_query_count < 1:
        logger.warning(f"Invalid parallel_query_count: {parallel_query_count}. Setting to 1.")
        parallel_query_count = 1
    elif parallel_query_count > 10:
        logger.warning(f"parallel_query_count is quite high: {parallel_query_count}. This may cause performance issues.")
    
    logger.info(f"Using {parallel_query_count} parallel tab(s) for processing")

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

    # Initialize browser and contexts
    browser = None
    contexts = []
    
    try:
        # Launch browser
        browser = await launch_browser_async(headless=headless)
        
        # Create contexts based on parallel_query_count
        for i in range(parallel_query_count):
            context = await create_context_with_cookies_async(browser)
            contexts.append(context)
            logger.info(f"Created browser context {i + 1}/{parallel_query_count}")
        
        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(parallel_query_count)
        
        # Process queries
        if parallel_query_count == 1:
            # Sequential processing
            context = contexts[0]
            for query in queries:
                await process_query(scraper, query, context, semaphore)
        else:
            # Parallel processing
            tasks = []
            for i, query in enumerate(queries):
                context = contexts[i % parallel_query_count]  # Round-robin context assignment
                task = asyncio.create_task(process_query(scraper, query, context, semaphore))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
    
    except Exception as e:
        logger.error(f"Error in main process: {e}")
    
    finally:
        # Clean up contexts first
        logger.info("Starting cleanup process...")
        for i, context in enumerate(contexts):
            try:
                if context:
                    await context.close()
                    logger.info(f"Closed browser context {i + 1}")
            except Exception as e:
                logger.error(f"Error closing context {i + 1}: {e}")
        
        # Wait a moment before closing browser to ensure all contexts are properly closed
        await asyncio.sleep(1)
        
        # Close browser manually - this avoids the singleton pattern issues
        try:
            if browser:
                await browser.close()
                logger.info("Closed browser")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
        
        # Stop playwright
        try:
            from modules.browser_handler import _playwright_instance
            if _playwright_instance:
                await _playwright_instance.stop()
                logger.info("Stopped Playwright")
        except Exception as e:
            logger.error(f"Error stopping Playwright: {e}")
    
    logger.info("Main scraping process completed.")

if __name__ == "__main__":
    asyncio.run(main())


