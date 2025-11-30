from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

class Evidence(BaseModel):
    """Evidence source supporting the claim analysis"""
    title: str
    url: str
    snippet: str = ""
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Climate Study 2024",
                "url": "https://example.com/study",
                "snippet": "New research shows..."
            }
        }

class ClaimAnalysis(BaseModel):
    """Complete analysis of a single claim"""
    claim: str = Field(..., description="The claim being analyzed")
    verdict: Literal["MISINFORMATION", "VERIFIED", "UNCERTAIN"] = Field(
        ..., 
        description="Verdict on the claim"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence score 0.0-1.0"
    )
    explanation: str = Field(..., description="Detailed explanation of the verdict")
    evidence: List[Evidence] = Field(
        default_factory=list,
        description="Supporting evidence sources"
    )
    analyzed_at: datetime = Field(
        default_factory=datetime.now,
        description="When this analysis was performed"
    )
    cached: bool = Field(
        default=False,
        description="Whether this result came from cache"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "claim": "Climate change is a hoax",
                "verdict": "MISINFORMATION",
                "confidence": 0.95,
                "explanation": "This claim contradicts overwhelming scientific consensus...",
                "evidence": [],
                "analyzed_at": "2025-11-30T20:00:00",
                "cached": False
            }
        }

class AnalysisRequest(BaseModel):
    """Request to analyze a topic"""
    topic: str = Field(..., min_length=1, max_length=200)

class AnalysisResponse(BaseModel):
    """Response containing claim analyses"""
    claims: List[ClaimAnalysis]
    topic: str
    analyzed_at: datetime
    processing_time: float
    cached: bool = False
