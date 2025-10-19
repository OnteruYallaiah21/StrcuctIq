"""
Data Manager Service for handling raw and curated data storage
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class DataManager:
    """Manages raw and curated data storage with timestamps and database IDs."""
    
    def __init__(self):
        """Initialize DataManager with data directory paths."""
        self.base_dir = Path("data")
        self.raw_data_dir = self.base_dir / "raw_data"
        self.curated_data_dir = self.base_dir / "curated_data"
        
        # Ensure directories exist
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.curated_data_dir.mkdir(parents=True, exist_ok=True)
    
    def save_raw_data(self, data: Dict[str, Any], source_type: str = "text") -> str:
        """
        Save raw data (text/image/PDF content) with timestamp.
        
        Args:
            data: Raw data dictionary
            source_type: Type of source (text, image, pdf)
            
        Returns:
            str: Filename of saved raw data
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        filename = f"raw_{source_type}_{timestamp}.json"
        filepath = self.raw_data_dir / filename
        
        # Prepare raw data with metadata
        raw_data = {
            "timestamp": datetime.now().isoformat(),
            "source_type": source_type,
            "raw_content": data,
            "filename": filename
        }
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def save_curated_data(self, structured_data: Dict[str, Any], database_id: int, raw_filename: str) -> str:
        """
        Save curated data (structured JSON) with database ID and timestamp.
        
        Args:
            structured_data: Structured data from LLM processing
            database_id: ID returned from database insertion
            raw_filename: Filename of corresponding raw data
            
        Returns:
            str: Filename of saved curated data
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"curated_db{database_id}_{timestamp}.json"
        filepath = self.curated_data_dir / filename
        
        # Prepare curated data with metadata
        curated_data = {
            "timestamp": datetime.now().isoformat(),
            "database_id": database_id,
            "raw_filename": raw_filename,
            "structured_data": structured_data,
            "filename": filename,
            "status": "success"
        }
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(curated_data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    def get_raw_data(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve raw data by filename.
        
        Args:
            filename: Name of the raw data file
            
        Returns:
            Dict containing raw data or None if not found
        """
        filepath = self.raw_data_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def get_curated_data(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve curated data by filename.
        
        Args:
            filename: Name of the curated data file
            
        Returns:
            Dict containing curated data or None if not found
        """
        filepath = self.curated_data_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def list_raw_data(self) -> list:
        """List all raw data files."""
        return [f.name for f in self.raw_data_dir.glob("*.json")]
    
    def list_curated_data(self) -> list:
        """List all curated data files."""
        return [f.name for f in self.curated_data_dir.glob("*.json")]
    
    def get_data_stats(self) -> Dict[str, Any]:
        """Get statistics about stored data."""
        raw_files = self.list_raw_data()
        curated_files = self.list_curated_data()
        
        return {
            "raw_data_count": len(raw_files),
            "curated_data_count": len(curated_files),
            "raw_files": raw_files,
            "curated_files": curated_files,
            "last_updated": datetime.now().isoformat()
        }


# Global data manager instance
data_manager = DataManager()
