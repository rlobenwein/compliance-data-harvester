"""Pydantic models for validating regulation data schema."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Article(BaseModel):
    """Article model."""
    article: str = Field(..., description="Article number or identifier")
    title: str = Field(..., description="Article title")
    summary: str = Field(..., description="Article summary")
    notes: Optional[str] = Field(None, description="Optional notes")


class Regulation(BaseModel):
    """Regulation model matching MCP server schema."""
    id: str = Field(..., description="Regulation identifier (e.g., 'gdpr')")
    name: str = Field(..., description="Full name of the regulation")
    region: str = Field(..., description="Region identifier (e.g., 'EU', 'USA')")
    risk_category: str = Field(default="high", description="Risk category")
    summary: str = Field(..., description="High-level description")
    articles: List[Article] = Field(default_factory=list, description="List of articles")
    developer_guidance: List[str] = Field(default_factory=list, description="Developer guidance points")
    
    @field_validator("risk_category")
    @classmethod
    def validate_risk_category(cls, v: str) -> str:
        """Validate risk category."""
        valid_categories = ["low", "medium", "high", "critical"]
        if v.lower() not in valid_categories:
            return "high"  # Default to high
        return v.lower()
    
    @field_validator("articles")
    @classmethod
    def validate_articles(cls, v: List[Article]) -> List[Article]:
        """Ensure articles list is not None."""
        return v or []
    
    @field_validator("developer_guidance")
    @classmethod
    def validate_developer_guidance(cls, v: List[str]) -> List[str]:
        """Ensure developer_guidance list is not None."""
        return v or []


class RegulationSource(BaseModel):
    """Source configuration for a regulation."""
    id: str
    sources: List[str] = Field(default_factory=list)


class Region(BaseModel):
    """Region configuration."""
    id: str
    name: str
    regulations: List[RegulationSource] = Field(default_factory=list)


class RegionsConfig(BaseModel):
    """Root configuration for all regions."""
    regions: List[Region] = Field(default_factory=list)


