import json
import configparser
from playwright.async_api import async_playwright
from modules.logger_config import setup_logging
import os
from datetime import datetime

logger = setup_logging()

_playwright_instance = None
_browser_instance = None

def get_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.ini")
    config.read(config_path)
    return config

def get_cookie_path():
    config = get_config()
    try:
        cookie_dir = config["Playwright"]["cookie_dir"]
        if not os.path.isabs(cookie_dir):
            cookie_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), cookie_dir)
        os.makedirs(cookie_dir, exist_ok=True)
        return os.path.join(cookie_dir, "cookies.json")
    except KeyError:
        default_cookie_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cookies")
        os.makedirs(default_cookie_dir, exist_ok=True)
        return os.path.join(default_cookie_dir, "cookies.json")

def get_screenshot_dir():
    config = get_config()
    try:
        screenshot_dir = config["Playwright"]["screenshot_dir"]
        if not os.path.isabs(screenshot_dir):
            screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), screenshot_dir)
        os.makedirs(screenshot_dir, exist_ok=True)
        return screenshot_dir
    except KeyError:
        default_screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots")
        os.makedirs(default_screenshot_dir, exist_ok=True)
        return default_screenshot_dir

def get_user_agent():
    config = get_config()
    return config.get("Playwright", "user_agent", fallback=None)

async def get_playwright_async():
    """Starts Playwright if not already started."""
    global _playwright_instance
    if _playwright_instance is None:
        logger.info("Starting Playwright...")
        _playwright_instance = await async_playwright().start()
        logger.info("Playwright started.")
    return _playwright_instance

async def launch_browser_async(headless=True):
    """Launches a browser instance using Playwright."""
    global _browser_instance
    if _browser_instance is not None:
        logger.warning("Browser already launched. Returning existing instance.")
        return _browser_instance

    p = await get_playwright_async()
    user_agent = get_user_agent()
    browser_options = {
        "headless": headless,
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-infobars",
            "--window-position=0,0",
            "--ignore-certifcate-errors",
            "--ignore-certifcate-errors-spki-list",
            "--disable-blink-features=AutomationControlled" # Attempt to hide automation
        ]
    }
    if user_agent:
        browser_options["user_agent"] = user_agent
        logger.info(f"Using custom user agent: {user_agent}")
    else:
        logger.info("Using default Playwright user agent.")

    try:
        logger.info(f"Launching browser (headless={headless})...")
        # Using chromium, could be firefox or webkit if needed
        _browser_instance = await p.chromium.launch(**browser_options)
        logger.info("Browser launched successfully.")
        return _browser_instance
    except Exception as e:
        logger.error(f"Failed to launch browser: {e}")
        raise

async def create_context_with_cookies_async(browser):
    """Creates a new browser context and loads cookies."""
    cookie_path = get_cookie_path()
    user_agent = get_user_agent()
    
    # Ensure cookie file exists, create if not
    if not os.path.exists(cookie_path):
        logger.info(f"Cookie file not found at {cookie_path}. Creating an empty one.")
        with open(cookie_path, 'w') as f:
            json.dump([], f) # Write an empty JSON array

    try:
        with open(cookie_path, 'r') as f:
            cookies = json.load(f)
        logger.info(f"Loaded {len(cookies)} cookies from {cookie_path}")
        
        # Fix sameSite values for Playwright compatibility
        for cookie in cookies:
            if 'sameSite' in cookie:
                samesite_value = cookie['sameSite'].lower()
                if samesite_value == 'lax':
                    cookie['sameSite'] = 'Lax'
                elif samesite_value == 'strict':
                    cookie['sameSite'] = 'Strict'
                elif samesite_value in ['none', 'no_restriction']:
                    cookie['sameSite'] = 'None'
                else:
                    # For unspecified or other values, default to Lax
                    cookie['sameSite'] = 'Lax'
        
        logger.info("Fixed sameSite values in cookies for Playwright compatibility")
        
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from cookie file {cookie_path}: {e}")
        # If the file is corrupted, create a new empty one
        with open(cookie_path, 'w') as f:
            json.dump([], f)
        cookies = []
        logger.warning(f"Corrupted cookie file {cookie_path} reset to empty. Proceeding without cookies.")
    except Exception as e:
        logger.error(f"Error reading cookie file {cookie_path}: {e}")
        cookies = [] # Proceed without cookies if there's an error

    try:
        context = await browser.new_context(
            storage_state={"cookies": cookies},
            user_agent=user_agent if user_agent else None,
            # Set viewport for consistency, mimicking a common desktop size
            viewport={"width": 1920, "height": 1080},
            # Emulate some device characteristics
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            locale='en-US', # Set locale
            timezone_id='America/New_York' # Set timezone
        )
        logger.info("Browser context created and cookies loaded.")
        return context
    except Exception as e:
        logger.error(f"Failed to create browser context or load cookies: {e}")
        raise

async def close_browser_async():
    """Closes the browser instance and stops Playwright."""
    global _browser_instance, _playwright_instance
    if _browser_instance:
        try:
            await _browser_instance.close()
            logger.info("Browser closed.")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
        _browser_instance = None

    if _playwright_instance:
        try:
            await _playwright_instance.stop()
            logger.info("Playwright stopped.")
        except Exception as e:
            logger.error(f"Error stopping Playwright: {e}")
        _playwright_instance = None

# Example usage (optional - for testing)
if __name__ == '__main__':
    import asyncio
    async def test_run():
        browser = None
        context = None
        page = None
        try:
            browser = await launch_browser_async(headless=True) # Launch headless for testing in sandbox
            context = await create_context_with_cookies_async(browser)
            page = await context.new_page()
            logger.info("Navigating to Google to test browser handler...")
            await page.goto("https://www.google.com/", wait_until="domcontentloaded", timeout=60000)
            logger.info(f"Current URL: {page.url}")
            logger.info(f"Page title: {page.title()}")
            screenshot_dir = get_screenshot_dir()
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, "browser_handler_test_screenshot.png")
            await page.screenshot(path=screenshot_path)
            logger.info(f"Screenshot saved to {screenshot_path}")

        except Exception as e:
            logger.error(f"Error during browser handler test: {e}")
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
            await close_browser_async()
            logger.info("Browser handler test finished.")
    asyncio.run(test_run())


