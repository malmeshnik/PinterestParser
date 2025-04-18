import json
import logging
import re
import datetime
from typing import Dict, Optional, Any

import requests
from bs4 import BeautifulSoup

from src.config.settings import PINTEREST_BASE_URL


class PinterestParser:
    """
    Parser for extracting information from Pinterest pins.
    """
    
    def __init__(self):
        """Initialize the Pinterest parser with a requests session."""
        self.logger = logging.getLogger(__name__)
        self.session = self._create_requests_session()
    
    def _create_requests_session(self) -> requests.Session:
        """Create and configure a requests session with appropriate headers."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        })
        return session
    
    def process_pin_url(self, pin_url: str, keyword: str) -> Optional[Dict[str, Any]]:
        """
        Process a Pinterest pin URL to extract information.
        
        Args:
            pin_url: URL of the pin to process
            keyword: Search keyword used to find this pin
            
        Returns:
            Dictionary containing pin information, or None if extraction failed
        """
        try:
            pin_info = self._extract_pin_data(pin_url)
            if pin_info:
                pin_info['query'] = keyword
                return pin_info
            return None
        except Exception as e:
            self.logger.error(f"Failed to process pin {pin_url}: {e}")
            return None
    
    def _extract_pin_data(self, pin_url: str) -> Optional[Dict[str, Any]]:
        """
        Extract detailed information from a Pinterest pin.
        
        Args:
            pin_url: URL of the pin
            
        Returns:
            Dictionary with pin data or None if extraction failed
        """
        try:
            response = self.session.get(pin_url, timeout=5)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find script tags with Pinterest data
            script_tags = soup.find_all("script", {"data-relay-response": "true"})
            if len(script_tags) < 2:
                self.logger.warning(f"Insufficient data in pin page: {pin_url}")
                return {}
            
            # Extract JSON data
            pin_data_json = json.loads(script_tags[1].string)
            pin_data = pin_data_json['response']['data']['v3GetPinQuery']['data']
            
            # Extract rich data objects
            pin_join = pin_data.get('pinJoin') or {}
            rich_metadata = pin_data.get('richMetadata') or {}
            closeup_attribution = pin_data.get('closeupAttribution') or {}
            origin_pinner = pin_data.get('originPinner') or {}
            aggregated_pin_data = pin_data.get('aggregatedPinData') or {}
            board = pin_data.get('board') or {}
            
            # Extract SEO data
            seo_title = pin_data.get('seoTitle', '')
            
            # Extract visual annotation
            annotation = pin_join.get('visualAnnotation', '')
            
            # Extract description
            description_div = soup.find("div", {"data-test-id": "safeTextDirection"})
            description = description_div.find("div").text.strip() if description_div else ''
            
            # Extract hashtags
            hashtags = self._extract_hashtags(description)
            
            # Process creation date
            created_at = self._format_date(pin_data.get('createdAt', ''))
            
            # Extract leaf snippet data
            leaf_snippet_tag = soup.find("script", {"data-test-id": "leaf-snippet"})
            leaf_snippet = json.loads(leaf_snippet_tag.string) if leaf_snippet_tag else {}
            
            # Find image URL
            image_container = soup.find("div", {"data-test-id": "pin-closeup-image"})
            image_url = image_container.find("img")["src"] if image_container else ''
            
            # Extract board URL
            board_meta = soup.find("meta", {"name": "pinterestapp:pinboard"})
            board_url = board_meta["content"] if board_meta else ''
            
            # Compile pin information
            pin_info = {
                # Basic pin information
                "pin_id": pin_data.get('entityId', ''),
                "pin_url": pin_url,
                "pin_title": pin_data.get('gridTitle', ''),
                "pin_description": description,
                "hashtags": hashtags,
                "image_url": image_url,
                "created_date": created_at,
                "dominant_color": pin_data.get('dominantColor', ''),
                
                # Creator information
                "creator_username": origin_pinner.get('username', ''),
                "creator_full_name": origin_pinner.get('fullName', ''),
                "creator_followers_count": closeup_attribution.get('followerCount', 0),
                
                # Board information
                "board_name": board.get('name', ''),
                "board_url": board_url,
                
                # Engagement metrics
                "is_repin": pin_data.get('isRepin', False),
                "repin_count": pin_data.get('repinCount', 0),
                "share_count": pin_data.get('shareCount', 0),
                "comment_count": aggregated_pin_data.get('commentCount', 0),
                "saves": aggregated_pin_data.get('aggregatedStats', {}).get('saves', 0),
                "reaction_count": pin_data.get("totalReactionCount", 0),
                
                # Pinner information (current board owner)
                "pinner_username": leaf_snippet.get('author', {}).get('alternateName', ''),
                "pinner_full_name": leaf_snippet.get('author', {}).get('name', ''),
                "pinner_follower_count": origin_pinner.get('followerCount', 0),
                
                # SEO and metadata
                "external_link": pin_data.get('link', ''),
                "domain": '' if pin_data.get('domain') == 'Uploaded by user' else pin_data.get('domain', ''),
                "title_metadata": pin_data.get('gridTitle', ''),
                "seo_title": seo_title,
                "seo_description": rich_metadata.get('description', ''),
                "annotations": annotation,
            }
            
            return pin_info
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error scraping pin {pin_url}: {e}")
            return None
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Data extraction error for pin {pin_url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error processing pin {pin_url}: {e}")
            return None
    
    @staticmethod
    def _extract_hashtags(text: str) -> str:
        """
        Extract hashtags from text.
        
        Args:
            text: Text to extract hashtags from
            
        Returns:
            Space-separated string of hashtags
        """
        hashtags = re.findall(r"#\w+", text)
        return " ".join(hashtags) if hashtags else ""
    
    @staticmethod
    def _format_date(date_str: str) -> str:
        """
        Format Pinterest date string to standard format.
        
        Args:
            date_str: Date string in Pinterest format
            
        Returns:
            Formatted date string
        """
        if not date_str:
            return ""
            
        try:
            dt = datetime.datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            return dt.strftime("%a, %d %b %Y %H:%M:%S")
        except ValueError:
            return date_str
    
    def close(self) -> None:
        """Close the requests session."""
        if hasattr(self, 'session'):
            self.session.close()