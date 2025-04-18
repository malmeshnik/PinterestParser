import logging
from pathlib import Path
from typing import List

import pandas as pd

from src.models.pin import Pin


class ExcelExporter:
    """
    Class for exporting Pinterest pin data to Excel files.
    """
    
    def __init__(self, output_dir: str = 'data/output'):
        """
        Initialize the Excel exporter.
        
        Args:
            output_dir: Directory to save Excel files
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(output_dir)
        self._ensure_output_dir()
    
    def _ensure_output_dir(self) -> None:
        """Ensure the output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(self, pins: List[Pin], filename_base: str) -> str:
        """
        Export pins to an Excel file.
        
        Args:
            pins: List of Pin objects to export
            filename_base: Base name for the output file (without extension)
            
        Returns:
            Path to the created Excel file
        """
        if not pins:
            self.logger.warning("No data to export")
            return ""
        
        # Convert pins to dictionaries for DataFrame
        pin_dicts = [pin.to_dict() for pin in pins]
        
        # Create DataFrame
        df = pd.DataFrame(pin_dicts)
        
        # Prepare filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_base}_{timestamp}.xlsx"
        filepath = self.output_dir / filename
        
        # Export to Excel
        try:
            df.to_excel(filepath, index=False, engine='openpyxl')
            self.logger.info(f"Successfully exported {len(pins)} pins to {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Failed to export data to Excel: {e}")
            return ""