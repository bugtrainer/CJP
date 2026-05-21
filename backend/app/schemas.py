from pydantic import BaseModel, Field, HttpUrl
from datetime import date, datetime
from typing import List, Optional, Dict, Any

# Movement schemas
class MovementBase(BaseModel):
    name: str
    tagline: Optional[str] = None
    slug: str

class MovementCreate(MovementBase):
    pass

class MovementResponse(MovementBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Metrics Tracker schemas
class MetricsTrackerResponse(BaseModel):
    id: int
    movement_id: int
    platform: str
    follower_count: Optional[int] = None
    mentions_per_minute: Optional[int] = None
    timestamp: datetime

    class Config:
        from_attributes = True

# Sources schemas
class SourceResponse(BaseModel):
    id: int
    movement_id: int
    name: str
    platform: str
    url: Optional[str] = None
    source_reputation_score: int
    verification_status: str
    created_at: datetime

    class Config:
        from_attributes = True

# Posts schemas
class PostResponse(BaseModel):
    id: int
    movement_id: int
    source_id: Optional[int] = None
    source_platform: str
    external_id: str
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    post_url: str
    published_at: Optional[datetime] = None
    ingested_at: datetime
    collector_version: str
    scrape_status: str
    language_code: str
    translated_content: Optional[str] = None
    content_type: Optional[str] = None
    credibility_score: float
    bot_probability: float
    verification_status: Optional[str] = None
    sentiment: Optional[str] = None
    primary_theme: Optional[str] = None
    is_duplicate: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Entity schemas
class EntityBase(BaseModel):
    entity_type: str
    name: str
    aliases: List[str] = []

class EntityResponse(EntityBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Narrative schemas
class NarrativeBase(BaseModel):
    movement_id: int
    title: str
    description: Optional[str] = None
    confidence_score: float = 0.5

class NarrativeResponse(NarrativeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Narrative Evolution schemas
class NarrativeEvolutionResponse(BaseModel):
    id: int
    narrative_id: int
    timestamp: datetime
    volume_score: float
    sentiment_score: float
    platform_distribution: Dict[str, Any]

    class Config:
        from_attributes = True

# Narrative Evidence schemas
class NarrativeEvidenceResponse(BaseModel):
    id: int
    narrative_id: int
    post_id: int
    evidence_strength: float
    created_at: datetime
    post: Optional[PostResponse] = None

    class Config:
        from_attributes = True

# Platform Event schemas
class PlatformEventResponse(BaseModel):
    id: int
    movement_id: int
    platform: str
    event_type: str
    description: str
    external_url: Optional[str] = None
    occurred_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Meme schemas
class MemeResponse(BaseModel):
    id: int
    movement_id: int
    image_url: str
    caption: Optional[str] = None
    slogan: Optional[str] = None
    reposts_count: int
    detected_theme: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Summary schemas
class SummaryResponse(BaseModel):
    id: int
    movement_id: int
    timeframe: str
    summary_text: str
    bullet_points: Optional[List[str]] = None
    narrative_shifts: Optional[List[Dict[str, Any]]] = None
    sentiment_distribution: Optional[Dict[str, Any]] = None
    generated_at: datetime

    class Config:
        from_attributes = True

# Timeline Event schemas
class TimelineEventResponse(BaseModel):
    id: int
    movement_id: int
    event_date: date
    title: str
    description: str
    linked_posts: Optional[List[str]] = None
    event_confidence: str
    importance_score: int
    created_at: datetime

    class Config:
        from_attributes = True
