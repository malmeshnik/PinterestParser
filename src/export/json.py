import json
import logging
from pathlib import Path
from typing import List

from src.models.pin import Pin


class JsonExporter:
    """
    Class for exporting Pinterest pin data to JSON files.
    """
    
    def __init__(self, output_dir: str = 'data/output'):
        """
        Initialize the JSON exporter.
        
        Args:
            output_dir: Directory to save JSON files
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(output_dir)
        self._ensure_output_dir()
    
    def _ensure_output_dir(self) -> None:
        """Ensure the output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(self, pins: List[Pin], filename_base: str) -> str:
        """
        Export pins to a JSON file.
        
        Args:
            pins: List of Pin objects to export
            filename_base: Base name for the output file (without extension)
            
        Returns:
            Path to the created JSON file
        """
        if not pins:
            self.logger.warning("No data to export")
            return ""
        
        # Convert pins to dictionaries
        pin_dicts = [pin.to_dict() for pin in pins]
        result_data = {"pins": pin_dicts}
        
        # Prepare filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_base}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        # Export to JSON
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Successfully exported {len(pins)} pins to {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Failed to export data to JSON: {e}")
            return ""