import asyncio
import json
import urllib.parse
import re
from modules.config_manager import ConfigManager
from modules.database_manager import DatabaseManager
from modules.logger_config import setup_logging
from modules.email_finder import EmailFinder
from modules.browser_handler import launch_browser_async, create_context_with_cookies_async, close_browser_async

logger = setup_logging()

class GoogleMapsScraper:
    def __init__(self, config_manager=None, db_manager=None):
        if config_manager is None:
            config_manager = ConfigManager()
        self.config = config_manager
        
        if db_manager is None:
            db_manager = DatabaseManager(config_manager=config_manager)
        self.db_manager = db_manager
        
        self.email_finder = EmailFinder()
        self.headless = self.config.getboolean("Playwright", "headless", fallback=True)
        self.max_companies_per_query = self.config.getint("Search", "max_companies_per_query", fallback=25)

    def clean_text(self, text):
        """
        Clean text by removing emojis, special characters, and normalizing whitespace.
        Keeps only alphanumeric characters, basic punctuation, and common symbols.
        """
        if not text or not isinstance(text, str):
            return "N/A"
        
        # Remove emojis and special Unicode characters
        # Keep only ASCII printable characters, basic Latin, and common symbols
        cleaned = re.sub(r'[^\x20-\x7E\u00A0-\u00FF]', '', text)
        
        # Replace multiple whitespace characters with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()
        
        # Return N/A if the text becomes empty after cleaning
        return cleaned if cleaned else "N/A"

    def clean_phone(self, phone):
        """
        Clean phone number by keeping only digits, spaces, hyphens, parentheses, and plus sign.
        """
        if not phone or not isinstance(phone, str):
            return "N/A"
        
        # Keep only phone-related characters
        cleaned = re.sub(r'[^\d\s\-\(\)\+]', '', phone)
        
        # Replace multiple whitespace with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned if cleaned else "N/A"

    def clean_email(self, email):
        """
        Clean email by keeping only valid email characters.
        """
        if not email or not isinstance(email, str):
            return "N/A"
        
        # Keep only valid email characters
        cleaned = re.sub(r'[^\w\.\-@]', '', email)
        
        return cleaned if cleaned and '@' in cleaned else "N/A"

    def clean_website(self, website):
        """
        Clean website URL by removing invalid characters.
        """
        if not website or not isinstance(website, str):
            return "N/A"
        
        # Keep only valid URL characters
        cleaned = re.sub(r'[^\w\.\-/:?=&%]', '', website)
        
        return cleaned if cleaned else "N/A"

    async def scrape(self, query):
        logger.info(f"Starting scrape for query: {query}")
        browser = None
        context = None
        page = None
        try:
            browser = await launch_browser_async(headless=self.headless)
            context = await create_context_with_cookies_async(browser)
            page = await context.new_page()
            await page.goto("https://www.google.com/maps", wait_until="domcontentloaded")

            # Search for the query
            await page.fill("input#searchboxinput", query)
            await page.press("input#searchboxinput", "Enter")
            
            # Wait for the search results to appear.
            try:
                results_pane_selector = "div[aria-label^=\"Results for\"]"
                await page.wait_for_selector(results_pane_selector, timeout=60000)
            except Exception as e:
                logger.error(f"Timeout waiting for search results container for query \'{query}\': {e}")
                return

            escaped_results_pane_selector = json.dumps(results_pane_selector)

            logger.debug(f"Results pane selector: {escaped_results_pane_selector}")
            processed_companies_count = 0
            max_companies = self.max_companies_per_query
            
            # Continue scrolling and processing until we reach the company limit
            scroll_iteration = 0
            while processed_companies_count < max_companies:
                scroll_iteration += 1
                logger.info(f"Scrolling down results for '{query}' (scroll {scroll_iteration}) - {processed_companies_count}/{max_companies} companies processed")
                await page.evaluate(f"document.querySelector({escaped_results_pane_selector}).scrollTop = document.querySelector({escaped_results_pane_selector}).scrollHeight")
                await page.wait_for_timeout(2000)  # Wait for content to load

                # Get all company links using semantic attributes instead of fragile classes
                # Target anchor tags with business-specific characteristics
                company_elements = await page.query_selector_all("a[aria-label][href*='/maps/place/']")
                logger.info(f"Found {len(company_elements)} potential company elements after scroll {scroll_iteration}.")

                companies_processed_this_scroll = 0
                for j, element in enumerate(company_elements):
                    # Check if we've reached our company limit
                    if processed_companies_count >= max_companies:
                        logger.info(f"Reached maximum companies limit ({max_companies}) for query '{query}'")
                        break
                    # Try multiple methods to extract the business name
                    name = None
                    
                    # Method 1: Try aria-label but validate it
                    aria_label = await element.get_attribute("aria-label")
                    if aria_label and aria_label.lower() != "results" and len(aria_label.strip()) > 1:
                        name = aria_label.strip()
                    
                    # Method 2: Try to get name from href URL
                    if not name or name.lower() == "results":
                        href = await element.get_attribute("href")
                        if href and "/maps/place/" in href:
                            # Extract business name from URL
                            try:
                                # URL format: /maps/place/Business+Name/...
                                place_part = href.split("/maps/place/")[1].split("/")[0]
                                decoded_name = urllib.parse.unquote_plus(place_part)
                                if decoded_name and len(decoded_name.strip()) > 1:
                                    name = decoded_name.strip()
                            except:
                                pass
                    
                    # Method 3: Try to get text content from nested elements
                    if not name or name.lower() == "results":
                        try:
                            # Look for text in child elements
                            text_element = await element.query_selector("div, span")
                            if text_element:
                                text = await text_element.inner_text()
                                if text and text.strip() and text.strip().lower() != "results":
                                    name = text.strip()
                        except:
                            pass
                    
                    # Clean the extracted name before further processing
                    if name:
                        name = self.clean_text(name)
                    
                    # Skip if we still don't have a valid name
                    if not name or name == "N/A" or name.lower() == "results" or len(name.strip()) <= 1:
                        logger.debug(f"Skipping element with invalid name: {name}")
                        continue
                    
                    if name and not self.db_manager.company_exists(name, query):
                        logger.info(f"Processing company: {name}")
                        try:
                            # Click the element directly
                            await element.click()
                            logger.info(f"Waiting for detail page to load for {name}...")
                            
                            # Wait for the detail page to load using a more reliable selector
                            # Look for the main heading (h1) that contains the business name
                            # Use a more flexible approach that doesn't rely on exact aria-label match
                            try:
                                # Try multiple selectors for the business name heading
                                await page.wait_for_selector("h1", timeout=10000)
                                # Additional wait for any dynamic content loading
                                await page.wait_for_timeout(2000)
                            except:
                                # Fallback: wait for any content in the detail pane
                                await page.wait_for_selector("div[role='main']", timeout=10000)
                                await page.wait_for_timeout(2000)
                            
                            logger.info(f"Detail page loaded for {name}. Extracting info...")

                            # Extract information using the new method
                            company_info = await self._extract_company_info(page, name)
                            
                            if company_info and company_info.get('name'):
                                logger.info(f"Successfully extracted info for {company_info['name']}.")
                                
                                # Extract email if website is available
                                email = "N/A"
                                website = company_info.get('website', 'N/A')
                                if website and website != "N/A":
                                    domain = website.replace("http://", "").replace("https://", "").split("/")[0]
                                    email = self.email_finder.find_email(domain)
                                    logger.info(f"Found email for {name}: {email}")

                                # Clean all extracted data before database insertion
                                clean_name = self.clean_text(company_info.get('name', name))
                                clean_address = self.clean_text(company_info.get('address', 'N/A'))
                                clean_phone = self.clean_phone(company_info.get('phone', 'N/A'))
                                clean_website = self.clean_website(website)
                                clean_email = self.clean_email(email)

                                self.db_manager.insert_company(
                                    clean_name,
                                    clean_address,
                                    clean_phone,
                                    clean_website,
                                    clean_email,
                                    query
                                )
                            else:
                                logger.warning(f"Failed to extract complete info for {name}.")
                            logger.info(f"Inserted company: {name}")
                            processed_companies_count += 1
                            companies_processed_this_scroll += 1

                        except Exception as e:
                            logger.warning(f"Could not process company {name}: {e}")
                            # If an error occurs, we need to ensure we are back to the search results list
                            # to continue with the next company. The back button is the most reliable way.
                            try:
                                await page.go_back()
                                await page.wait_for_selector(results_pane_selector, timeout=30000) # Wait for search results to be visible again
                                logger.info(f"Navigated back to search results after error for {name}.")
                            except Exception as back_e:
                                logger.error(f"Failed to navigate back to search results after error for {name}: {back_e}")
                                # If we can't go back, we might be stuck, so break the loop for this query
                                break
                
                # Break the outer loop if we've reached our company limit
                if processed_companies_count >= max_companies:
                    break
                
                # If no new companies were processed in this scroll, we might have reached the end
                if companies_processed_this_scroll == 0:
                    logger.info(f"No new companies found in scroll {scroll_iteration}. Might have reached end of results.")
                    # Try one more scroll to be sure
                    if scroll_iteration > 1:  # Only break if we've scrolled at least twice
                        break

        except Exception as e:
            logger.error(f"An unexpected error occurred during scraping for query \'{query}\': {e}")
        finally:
            if browser:
                await close_browser_async()
            logger.info(f"Finished scrape for query: {query}. Processed {processed_companies_count} companies.")

    async def _extract_company_info(self, page, name):
        """Extract company information from the detail page using multiple fallback strategies."""
        try:
            # Scroll the detail pane to load all content - multiple strategies
            await self._scroll_detail_page(page)
            
            # Extract basic info
            company_info = {"name": name}
            
            # Extract company name - multiple strategies
            raw_name = await self._extract_name(page, name)
            company_info["name"] = self.clean_text(raw_name)
            
            # Extract address - multiple strategies
            raw_address = await self._extract_address(page)
            company_info["address"] = self.clean_text(raw_address)
            
            # Extract website - multiple strategies
            raw_website = await self._extract_website(page)
            company_info["website"] = self.clean_website(raw_website)
            
            # Extract phone - multiple strategies
            raw_phone = await self._extract_phone(page)
            company_info["phone"] = self.clean_phone(raw_phone)
            
            # Extract rating and reviews (clean these too for consistency)
            raw_rating = await self._extract_rating(page)
            company_info["rating"] = self.clean_text(raw_rating)
            raw_review_count = await self._extract_review_count(page)
            company_info["review_count"] = self.clean_text(raw_review_count)
            
            # Extract category
            raw_category = await self._extract_category(page)
            company_info["category"] = self.clean_text(raw_category)
            
            logger.info(f"Extracted data for {name}: {company_info}")
            return company_info
            
        except Exception as e:
            logger.error(f"Error extracting company info for {name}: {e}")
            cleaned_name = self.clean_text(name)
            return {"name": cleaned_name}

    async def _scroll_detail_page(self, page):
        """Scroll the detail page using multiple strategies."""
        try:
            # Strategy 1: Scroll main role element
            await page.evaluate("""
                const mainElement = document.querySelector('div[role="main"]');
                if (mainElement) {
                    mainElement.scrollTo(0, mainElement.scrollHeight);
                }
            """)
            await page.wait_for_timeout(1000)
            
            # Strategy 2: Scroll tabindex -1 element
            await page.evaluate("""
                const tabElement = document.querySelector('div[tabindex="-1"]');
                if (tabElement) {
                    tabElement.scrollTo(0, tabElement.scrollHeight);
                }
            """)
            await page.wait_for_timeout(1000)
            
            # Strategy 3: General page scroll
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            
        except Exception as e:
            logger.debug(f"Error scrolling detail page: {e}")

    async def _extract_name(self, page, fallback_name):
        """Extract company name using multiple strategies."""
        strategies = [
            # More specific strategies for Google Maps business detail pages
            "h1[data-attrid='title']",  # Primary business name heading with data attribute
            "div[role='main'] h1",      # H1 within the main content area
            "h1:not(:has-text('Results'))",  # H1 that doesn't contain "Results"
            "[data-value*='name']",     # Elements with name data attributes
            "button[jsaction*='directionsPlaceActionDialog']",  # Business name in directions button
            # Generic fallbacks
            "h1",  # Any h1 element (last resort)
        ]
        
        for strategy in strategies:
            try:
                element = await page.query_selector(strategy)
                if element:
                    text = await element.inner_text()
                    if text and len(text.strip()) > 0 and text.strip().lower() != "results":
                        # Additional validation - business names should be reasonable length
                        if 2 <= len(text.strip()) <= 100 and not text.strip().startswith("Results"):
                            return text.strip()
            except:
                continue
        
        # If all strategies fail, try to extract from the page title or URL
        try:
            title = await page.title()
            if title and " - Google Maps" in title:
                business_name = title.replace(" - Google Maps", "").strip()
                if business_name and business_name.lower() != "results":
                    return business_name
        except:
            pass
        
        return fallback_name if fallback_name and fallback_name.lower() != "results" else "Unknown Business"

    async def _extract_address(self, page):
        """Extract address using multiple strategies."""
        strategies = [
            'button[data-item-id="address"]',  # Primary data attribute
            'button[aria-label*="Address"]',   # Aria label containing Address
            'button:has-text("Australia")',   # Button containing Australia
            '[data-tooltip*="address"]',      # Tooltip containing address
            'button:has([aria-hidden="true"]):has-text("St")',  # Button with street abbreviation
        ]
        
        for strategy in strategies:
            try:
                element = await page.query_selector(strategy)
                if element:
                    text = await element.inner_text()
                    if text and ("St" in text or "Ave" in text or "Rd" in text or "Australia" in text):
                        return text.strip()
            except:
                continue
        
        return "N/A"

    async def _extract_website(self, page):
        """Extract website using multiple strategies."""
        strategies = [
            ('a[data-item-id="authority"]', 'href'),      # Primary: authority link href
            ('a[data-item-id="authority"]', 'text'),      # Primary: authority link text
            ('a[href*="http"]:not([href*="google"])', 'href'),  # Any external link
            ('button[aria-label*="website"]', 'text'),    # Button with website in aria-label
            ('[data-tooltip*="website"]', 'text'),        # Element with website tooltip
            ('a:has-text(".com")', 'text'),               # Link containing .com
            ('a:has-text(".au")', 'text'),                # Link containing .au
        ]
        
        for strategy, attr_type in strategies:
            try:
                element = await page.query_selector(strategy)
                if element:
                    if attr_type == 'href':
                        value = await element.get_attribute('href')
                    else:
                        value = await element.inner_text()
                    
                    if value and ('.' in value) and not value.startswith('javascript:'):
                        # Clean up the value
                        value = value.strip()
                        if not value.startswith('http') and '.' in value:
                            # If it's just domain like "thoughtworks.com", return as is
                            return value
                        elif value.startswith('http'):
                            return value
            except:
                continue
        
        return "N/A"

    async def _extract_phone(self, page):
        """Extract phone using multiple strategies."""
        strategies = [
            'button[data-item-id*="phone"]',   # Primary: phone data attribute
            'button[aria-label*="Phone"]',     # Aria label containing Phone
            'a[href^="tel:"]',                 # Tel protocol link
            'button:has-text("+")',            # Button containing + (phone prefix)
            '[data-tooltip*="phone"]',         # Tooltip containing phone
        ]
        
        for strategy in strategies:
            try:
                element = await page.query_selector(strategy)
                if element:
                    # Try href first for tel: links
                    if 'tel:' in strategy:
                        href = await element.get_attribute('href')
                        if href and href.startswith('tel:'):
                            return href.replace('tel:', '').strip()
                    
                    # Try text content
                    text = await element.inner_text()
                    if text and ('+' in text or any(char.isdigit() for char in text)):
                        return text.strip()
            except:
                continue
        
        return "N/A"

    async def _extract_rating(self, page):
        """Extract rating using multiple strategies."""
        strategies = [
            'span[aria-hidden="true"]:has-text(".")',  # Span with decimal point
            '[role="img"][aria-label*="stars"]',      # Rating role img
            'span:has-text("4.") span:has-text("5.")', # Common rating patterns
        ]
        
        for strategy in strategies:
            try:
                element = await page.query_selector(strategy)
                if element:
                    text = await element.inner_text()
                    if text and '.' in text and len(text) <= 5:  # Rating should be short like "4.6"
                        return text.strip()
            except:
                continue
        
        return "N/A"

    async def _extract_review_count(self, page):
        """Extract review count using multiple strategies."""
        strategies = [
            '[aria-label*="reviews"]',         # Aria label containing reviews
            'span:has-text("reviews")',        # Span containing reviews text
            'button:has-text("reviews")',      # Button containing reviews text
        ]
        
        for strategy in strategies:
            try:
                element = await page.query_selector(strategy)
                if element:
                    aria_label = await element.get_attribute("aria-label")
                    text = await element.inner_text()
                    
                    for content in [aria_label, text]:
                        if content and 'review' in content.lower():
                            import re
                            match = re.search(r'(\d+)\s*review', content)
                            if match:
                                return match.group(1)
            except:
                continue
        
        return "N/A"

    async def _extract_category(self, page):
        """Extract business category using multiple strategies."""
        strategies = [
            'button:has-text("Software")',     # Button containing Software
            'button:has-text("company")',      # Button containing company
            'button:has-text("Technology")',   # Button containing Technology
            'span:has-text("Software")',       # Span containing Software
        ]
        
        for strategy in strategies:
            try:
                element = await page.query_selector(strategy)
                if element:
                    text = await element.inner_text()
                    if text and len(text) > 0 and len(text) < 100:  # Reasonable category length
                        return text.strip()
            except:
                continue
        
        return "N/A"

if __name__ == "__main__":
    scraper = GoogleMapsScraper()
    asyncio.run(scraper.scrape("tech companies in Australia"))


