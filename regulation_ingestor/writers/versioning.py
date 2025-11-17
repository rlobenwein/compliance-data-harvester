"""Version management for regulation JSON files."""

import json
from datetime import date
from pathlib import Path
from typing import Optional
from ..processors.validator import Regulation


class VersionManager:
    """Manages versioned regulation files."""
    
    def __init__(self, data_dir: Path):
        """
        Initialize version manager.
        
        Args:
            data_dir: Root data directory
        """
        self.data_dir = data_dir
    
    def save_versioned(self, regulation: Regulation, region_id: str) -> Path:
        """
        Save a versioned regulation file with date stamp.
        
        Args:
            regulation: Regulation data to save
            region_id: Region identifier
            
        Returns:
            Path to the versioned file
        """
        region_dir = self.data_dir / region_id
        region_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate versioned filename
        today = date.today()
        versioned_filename = f"{regulation.id}_{today.isoformat()}.json"
        versioned_path = region_dir / versioned_filename
        
        # Save versioned file
        with open(versioned_path, "w", encoding="utf-8") as f:
            json.dump(regulation.model_dump(), f, indent=2, ensure_ascii=False)
        
        return versioned_path
    
    def update_active(self, regulation: Regulation, region_id: str) -> Path:
        """
        Update the active (latest) regulation file.
        
        This copies the latest version to the active file name.
        Uses file copy (not symlink) for Windows compatibility.
        
        Args:
            regulation: Regulation data to save
            region_id: Region identifier
            
        Returns:
            Path to the active file
        """
        region_dir = self.data_dir / region_id
        region_dir.mkdir(parents=True, exist_ok=True)
        
        # Active file path
        active_path = region_dir / f"{regulation.id}.json"
        
        # Save active file (copy of latest version)
        with open(active_path, "w", encoding="utf-8") as f:
            json.dump(regulation.model_dump(), f, indent=2, ensure_ascii=False)
        
        return active_path
    
    def get_latest_version(self, region_id: str, regulation_id: str) -> Optional[Path]:
        """
        Get the path to the latest versioned file.
        
        Args:
            region_id: Region identifier
            regulation_id: Regulation identifier
            
        Returns:
            Path to latest versioned file, or None if not found
        """
        region_dir = self.data_dir / region_id
        if not region_dir.exists():
            return None
        
        # Find all versioned files for this regulation
        pattern = f"{regulation_id}_*.json"
        versioned_files = list(region_dir.glob(pattern))
        
        if not versioned_files:
            return None
        
        # Sort by filename (which includes date) to get latest
        versioned_files.sort(reverse=True)
        return versioned_files[0]

