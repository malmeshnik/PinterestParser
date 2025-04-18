# Pinterest Scraper Configuration

# Base URL for Pinterest
PINTEREST_BASE_URL = "https://www.pinterest.com"

# Default paths
DEFAULT_COOKIE_PATH = "data/cookies/pin.json"
DEFAULT_OUTPUT_DIR = "data/output"

# Scraping settings
MAX_PARALLEL_REQUESTS = 5
REQUEST_TIMEOUT = 5  # seconds
SCROLL_PAUSE_TIME = 1.5  # seconds
MAX_SCROLL_ATTEMPTS = 5  # maximum number of scroll attempts without new pins

# User agent string for requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"