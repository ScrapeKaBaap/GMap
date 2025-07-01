import asyncio
from playwright.async_api import async_playwright

async def test_playwright():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://www.google.com")
        await page.screenshot(path="google.png")
        await browser.close()
        print("Playwright test successful: google.png created.")

if __name__ == "__main__":
    asyncio.run(test_playwright())


