"""Output management for writing regulation data to directory structure."""

import json
from pathlib import Path
from typing import Optional
from ..processors.validator import Regulation, RegionsConfig, Region, RegulationSource
from .versioning import VersionManager


class OutputWriter:
    """Writes regulation data to the MCP server directory structure."""
    
    def __init__(self, data_dir: Path):
        """
        Initialize output writer.
        
        Args:
            data_dir: Root data directory
        """
        self.data_dir = data_dir
        self.version_manager = VersionManager(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def write_regulation(self, regulation: Regulation, region_id: str) -> tuple[Path, Path]:
        """
        Write regulation to both versioned and active files.
        
        Args:
            regulation: Regulation data to write
            region_id: Region identifier
            
        Returns:
            Tuple of (versioned_path, active_path)
        """
        # Save versioned file
        versioned_path = self.version_manager.save_versioned(regulation, region_id)
        
        # Update active file
        active_path = self.version_manager.update_active(regulation, region_id)
        
        return versioned_path, active_path
    
    def write_regions_json(self, config: RegionsConfig) -> Path:
        """
        Write or update regions.json file.
        
        Args:
            config: Regions configuration
            
        Returns:
            Path to regions.json
        """
        regions_path = self.data_dir / "regions.json"
        
        # Convert to dict for JSON serialization
        data = config.model_dump()
        
        # Write with proper formatting
        with open(regions_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return regions_path
    
    def ensure_directory_structure(self, region_id: str):
        """
        Ensure directory structure exists for a region.
        
        Args:
            region_id: Region identifier
        """
        region_dir = self.data_dir / region_id
        region_dir.mkdir(parents=True, exist_ok=True)


