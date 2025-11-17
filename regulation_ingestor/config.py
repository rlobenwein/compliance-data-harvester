"""Configuration management for regulation data ingestor."""

import os
import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class RegulationSource(BaseModel):
    """Source configuration for a regulation."""
    id: str
    sources: list[str] = Field(default_factory=list)


class Region(BaseModel):
    """Region configuration with its regulations."""
    id: str
    name: str
    regulations: list[RegulationSource] = Field(default_factory=list)


class RegionsConfig(BaseModel):
    """Root configuration for all regions."""
    regions: list[Region] = Field(default_factory=list)


class Config:
    """Application configuration."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            data_dir: Override for REGULATION_DATA_DIR environment variable
        """
        # Get data directory from parameter, environment variable, or default
        env_data_dir = os.getenv("REGULATION_DATA_DIR")
        
        if data_dir:
            # Explicit override takes precedence
            self.data_dir = Path(data_dir).resolve()
        elif env_data_dir:
            # Use environment variable from .env or system
            self.data_dir = Path(env_data_dir).resolve()
        else:
            # Default fallback with notification
            print("Warning: REGULATION_DATA_DIR not set. Using default: ./regulation-data")
            print("  Set REGULATION_DATA_DIR in .env file or environment variable to specify data location.")
            self.data_dir = Path("./regulation-data").resolve()
        
        # Load regions.json from data directory
        self.regions_file = self.data_dir / "regions.json"
        self._regions_config: Optional[RegionsConfig] = None
    
    def load_regions(self) -> RegionsConfig:
        """Load and parse regions.json."""
        if self._regions_config is not None:
            return self._regions_config
        
        if not self.regions_file.exists():
            raise FileNotFoundError(
                f"regions.json not found at {self.regions_file}. "
                f"Run 'python main.py init' to initialize."
            )
        
        with open(self.regions_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self._regions_config = RegionsConfig(**data)
        return self._regions_config
    
    def get_region(self, region_id: str) -> Optional[Region]:
        """Get a specific region by ID."""
        config = self.load_regions()
        for region in config.regions:
            if region.id == region_id:
                return region
        return None
    
    def get_regulation(self, region_id: str, regulation_id: str) -> Optional[RegulationSource]:
        """Get a specific regulation by region and regulation ID."""
        region = self.get_region(region_id)
        if not region:
            return None
        
        for regulation in region.regulations:
            if regulation.id == regulation_id:
                return regulation
        return None
    
    def get_regulation_path(self, region_id: str, regulation_id: str) -> Path:
        """Get the path where a regulation JSON file should be stored."""
        return self.data_dir / region_id / f"{regulation_id}.json"
    
    def ensure_data_dir(self):
        """Ensure the data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)


