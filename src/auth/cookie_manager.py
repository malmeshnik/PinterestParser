import json
import logging
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By

from src.config.settings import PINTEREST_BASE_URL


class CookieManager:
    """
    Manages authentication cookies for Pinterest sessions.
    """
    
    def __init__(self, cookie_path: str):
        """
        Initialize the cookie manager.
        
        Args:
            cookie_path: Path to the cookie file
        """
        self.logger = logging.getLogger(__name__)
        self.cookie_path = Path(cookie_path)
    
    def load_cookies(self, driver: webdriver.Chrome) -> bool:
        """
        Load cookies from file to authenticate the browser session.
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        self.logger.info("Loading authentication cookies...")
        
        try:
            if not self.cookie_path.exists():
                self.logger.error(f"Cookie file not found: {self.cookie_path}")
                return False
                
            with open(self.cookie_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            self.logger.info(f"Loaded {len(cookies)} cookies from file")
            
            # Initialize browser with base URL before adding cookies
            driver.get(PINTEREST_BASE_URL)
            time.sleep(2)
            
            driver.delete_all_cookies()
            time.sleep(0.5)
            
            loaded_cookies = 0
            for cookie in cookies:
                try:
                    # Validate required cookie fields
                    if not {'name', 'value'}.issubset(cookie.keys()):
                        self.logger.warning(f"Skipping invalid cookie: {cookie.get('name', 'unnamed')}")
                        continue
                    
                    # Normalize cookie domain
                    if 'domain' in cookie:
                        cookie['domain'] = cookie['domain'].lstrip('.')
                    else:
                        cookie['domain'] = 'pinterest.com'
                    
                    driver.add_cookie(cookie)
                    loaded_cookies += 1
                    
                except Exception as e:
                    self.logger.warning(f"Failed to add cookie {cookie.get('name', 'unnamed')}: {e}")
            
            self.logger.info(f"Successfully loaded {loaded_cookies} cookies")
            
            # Reload page with cookies applied
            driver.get(PINTEREST_BASE_URL)
            time.sleep(3)
            
            # Verify we're not on mobile version
            if "m.pinterest.com" in driver.current_url:
                self.logger.warning("Mobile version detected! Switching to desktop.")
                driver.get(PINTEREST_BASE_URL)
                time.sleep(2)
            
            return self._verify_authentication(driver)
            
        except Exception as e:
            self.logger.error(f"Failed to load cookies: {e}")
            return False
    
    @staticmethod
    def _verify_authentication(driver: webdriver.Chrome) -> bool:
        """
        Verify that the user is authenticated by checking for profile elements.
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            bool: True if authenticated, False otherwise
        """
        logger = logging.getLogger(__name__)
        
        auth_selectors = [
            'div[data-test-id="header-profile"]',
            'div[data-test-id="header-profile-dropdown"]',
            'button[data-test-id="header-create-menu-button"]'
        ]
        auth_elements = driver.find_elements(By.CSS_SELECTOR, ', '.join(auth_selectors))
        
        is_authenticated = bool(auth_elements)
        log_level = logging.INFO if is_authenticated else logging.ERROR
        logger.log(log_level, f"Authentication status: {'Success' if is_authenticated else 'Failed'}")
        
        return is_authenticated