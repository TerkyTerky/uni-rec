from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DataGenerateRequest(BaseModel):
    users: int = 30
    items: int = 80
    behaviors_per_user: int = 20
    social_degree: int = 3
    seed: int = 42


class StartupTypeResponse(BaseModel):
    reviewerID: str
    startup_type: str
    behavior_count: int
    threshold: int


class RecommendRequest(BaseModel):
    reviewerID: str
    top_k: int = 10
    threshold: int = 5
    mode: str = "auto"
    use_llm: bool = True


class RecommendedItem(BaseModel):
    asin: str
    score: float
    reason: str
    source: str
    meta: Dict[str, Any]


class RecommendResponse(BaseModel):
    reviewerID: str
    startup_type: str
    module: str
    items: List[RecommendedItem]
    summary: str


class FeedbackRequest(BaseModel):
    reviewerID: str
    asin: str
    score: int = Field(ge=1, le=5)


class MetricsResponse(BaseModel):
    metrics: Dict[str, Any]


class SocialGraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class SequenceResponse(BaseModel):
    events: List[Dict[str, Any]]


class UserProfileResponse(BaseModel):
    reviewerID: str
    reviewerName: str
    meta: Dict[str, Any]


class DataSnapshotResponse(BaseModel):
    users: int
    items: int
    reviews: int
    social_edges: int
