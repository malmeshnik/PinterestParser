from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Pin:
    """
    Data class representing a Pinterest pin with its metadata.
    """
    pin_id: str
    pin_url: str
    pin_title: str = ""
    pin_description: str = ""
    hashtags: str = ""
    image_url: str = ""
    query: str = ""
    created_date: str = ""
    dominant_color: str = ""
    
    # Creator information
    creator_username: str = ""
    creator_full_name: str = ""
    creator_followers_count: int = 0
    
    # Board information
    board_name: str = ""
    board_url: str = ""
    
    # Engagement metrics
    is_repin: bool = False
    repin_count: int = 0
    share_count: int = 0
    comment_count: int = 0
    saves: int = 0
    reaction_count: int = 0
    
    # Pinner information
    pinner_username: str = ""
    pinner_full_name: str = ""
    pinner_follower_count: int = 0
    
    # SEO and metadata
    external_link: str = ""
    domain: str = ""
    title_metadata: str = ""
    seo_title: str = ""
    seo_description: str = ""
    annotations: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pin':
        """
        Create a Pin object from a dictionary.
        
        Args:
            data: Dictionary containing pin data
            
        Returns:
            Pin object populated with the data
        """
        # Use only keys that are defined in the dataclass
        valid_keys = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        
        return cls(**filtered_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Pin object to a dictionary.
        
        Returns:
            Dictionary representation of the Pin
        """
        return {f.name: getattr(self, f.name) for f in fields(self)}


# Helper function to get dataclass fields
def fields(cls):
    return cls.__dataclass_fields__.values()