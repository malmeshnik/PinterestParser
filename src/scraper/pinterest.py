import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Dict, List, Optional, Set, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from src.auth.cookie_manager import CookieManager
from src.scraper.parser import PinterestParser
from src.models.pin import Pin
from src.config.settings import PINTEREST_BASE_URL


class PinterestScraper:
    """
    A class for scraping Pinterest data using Selenium and requests.
    
    Handles authentication via cookies and extracts pin information.
    """
    
    def __init__(self, cookie_path: str = 'data/cookies/pin.json'):
        """
        Initialize the Pinterest scraper with browser configuration.
        
        Args:
            cookie_path: Path to the cookie file for authentication
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info('Initializing Pinterest scraper')
        
        self.cookie_manager = CookieManager(cookie_path)
        self.parser = PinterestParser()
        self.driver = self._setup_browser()
        
        if not self.cookie_manager.load_cookies(self.driver):
            self.logger.warning("Authentication failed - check your cookie file")
    
    def _setup_browser(self) -> webdriver.Chrome:
        """Configure and initialize a Selenium Chrome browser with anti-detection measures."""
        self.logger.info("Setting up Chrome browser...")
        
        options = Options()
        
        # User identity configuration
        desktop_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        options.add_argument(f"user-agent={desktop_user_agent}")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        
        # Performance optimization
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument('--no-sandbox')
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Anti-detection measures
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-web-security")
        
        # Error handling and logging
        options.add_argument("--disable-crash-reporter")
        options.add_argument('--log-level=3')
        options.add_argument('--disable-logging')
        options.add_argument('--output=/dev/null')
        
        # Security configurations
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        
        # Uncomment for visible browser, comment for headless
        options.add_argument("--headless=new")
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        # Mask Selenium's presence to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_window_size(1920, 1080)
        
        return driver
    
    def search_pins(self, keyword: str, max_pins: int = 100) -> List[Pin]:
        """
        Search for pins by keyword and process the results.
        
        Args:
            keyword: Search query
            max_pins: Maximum number of pins to process
            
        Returns:
            List of Pin objects containing the scraped data
        """
        self.logger.info(f'Searching pins for query: "{keyword}"')
        
        search_url = f"{PINTEREST_BASE_URL}/search/pins/?q={keyword}"
        self.driver.get(search_url)
        time.sleep(1)
        
        # Get pin URLs
        pin_urls = self._collect_pin_urls(max_pins)
        self.logger.info(f"Collected {len(pin_urls)} pin URLs")
        
        # Process pins in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            process_pin = partial(self.parser.process_pin_url, keyword=keyword)
            results = list(executor.map(process_pin, pin_urls[:max_pins]))
        
        # Filter out None results and convert to Pin objects
        pins = [Pin.from_dict(r) for r in results if r is not None]
        self.logger.info(f"Successfully processed {len(pins)} pins")
        
        return pins
    
    def _collect_pin_urls(self, max_pins: int = 100, scroll_pause: float = 1.5) -> List[str]:
        """
        Collect pin URLs by scrolling the page.
        
        Args:
            max_pins: Maximum number of pins to collect
            scroll_pause: Time to pause between scrolls in seconds
            
        Returns:
            List of unique pin URLs
        """
        pin_urls: Set[str] = set()
        scroll_attempts = 0
        max_attempts_without_new = 5
        
        self.logger.info("Collecting pin URLs by scrolling...")
        
        while len(pin_urls) < max_pins:
            previous_count = len(pin_urls)
            
            # Scroll to bottom of page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)
            
            try:
                # Wait for pin elements to load
                elements = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href^="/pin/"]'))
                )
                
                # Extract and normalize pin URLs
                for element in elements:
                    try:
                        href = element.get_attribute('href')
                        if not href:
                            continue
                            
                        # Normalize URL to standard format: https://pinterest.com/pin/{id}/
                        pin_id = href.split('/pin/')[1].split('/')[0].split('?')[0]
                        clean_url = f"{PINTEREST_BASE_URL}/pin/{pin_id}/"
                        pin_urls.add(clean_url)
                        
                        # Break early if we've reached max_pins
                        if len(pin_urls) >= max_pins:
                            break
                            
                    except Exception as e:
                        self.logger.debug(f"Error extracting pin URL: {e}")
                        
            except Exception as e:
                self.logger.error(f"Error finding pin elements: {e}")
                break
            
            # Track progress
            current_count = len(pin_urls)
            print(f"\rFound pins: {current_count}/{max_pins}", end="")
            
            # Check if we're still finding new pins
            if current_count == previous_count:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
                
            # Stop if we've made several attempts without finding new pins
            if scroll_attempts >= max_attempts_without_new:
                self.logger.info("No new pins found after multiple scroll attempts")
                break
        
        print()  # New line after progress counter
        return list(pin_urls)[:max_pins]
    
    def close(self) -> None:
        """Clean up resources by closing browser and session."""
        if hasattr(self, 'driver'):
            self.driver.quit()
        if hasattr(self, 'parser'):
            self.parser.close()
        self.logger.info("Pinterest scraper resources released")