from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    DataGenerateRequest,
    DataSnapshotResponse,
    FeedbackRequest,
    MetricsResponse,
    RecommendRequest,
    RecommendResponse,
    SequenceResponse,
    SocialGraphResponse,
    StartupTypeResponse,
    UserProfileResponse,
)
from app.services.data_generator import generate_data
from app.services.data_store import store, update_store
from app.services.feedback import add_feedback
from app.services.metrics import compute_metrics
from app.services.recommendation import get_sequence_events, get_social_graph, get_startup_type, recommend


router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/data/generate", response_model=DataSnapshotResponse)
async def generate_snapshot(payload: DataGenerateRequest) -> DataSnapshotResponse:
    data = await generate_data(
        users=payload.users,
        items=payload.items,
        behaviors_per_user=payload.behaviors_per_user,
        social_degree=payload.social_degree,
        seed=payload.seed,
    )
    update_store(data)
    return DataSnapshotResponse(
        users=len(store["users"]),
        items=len(store["items"]),
        reviews=len(store["reviews"]),
        social_edges=len(store["social_edges"]),
    )


@router.get("/users/{user_id}", response_model=UserProfileResponse)
def get_user_profile(user_id: str) -> UserProfileResponse:
    user = store["users"].get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return UserProfileResponse(
        reviewerID=user_id,
        reviewerName=user.get("reviewerName", ""),
        meta=user.get("meta", {}),
    )


@router.get("/users/{user_id}/startup-type", response_model=StartupTypeResponse)
def startup_type(user_id: str, threshold: int = 5) -> StartupTypeResponse:
    startup, count = get_startup_type(user_id, threshold)
    return StartupTypeResponse(
        reviewerID=user_id, startup_type=startup, behavior_count=count, threshold=threshold
    )


@router.get("/users/{user_id}/sequence", response_model=SequenceResponse)
def sequence_events(user_id: str) -> SequenceResponse:
    return SequenceResponse(events=get_sequence_events(user_id))


@router.get("/users/{user_id}/social-graph", response_model=SocialGraphResponse)
def social_graph(user_id: str) -> SocialGraphResponse:
    data = get_social_graph(user_id)
    return SocialGraphResponse(nodes=data["nodes"], edges=data["edges"])


@router.post("/recommend", response_model=RecommendResponse)
async def recommend_items(payload: RecommendRequest) -> RecommendResponse:
    if payload.reviewerID not in store["users"]:
        raise HTTPException(status_code=404, detail="user not found")
    result = await recommend(
        reviewer_id=payload.reviewerID,
        top_k=payload.top_k,
        threshold=payload.threshold,
        mode=payload.mode,
        use_llm=payload.use_llm,
    )
    return RecommendResponse(
        reviewerID=result["reviewerID"],
        startup_type=result["startup_type"],
        module=result["module"],
        items=result["items"],
        summary=result["summary"],
    )


@router.post("/feedback")
def feedback(payload: FeedbackRequest) -> dict:
    record = add_feedback(payload.reviewerID, payload.asin, payload.action)
    return {"ok": True, "record": record}


@router.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    return MetricsResponse(metrics=compute_metrics())
