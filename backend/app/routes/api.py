from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

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
from app.models.sql_models import User, Item, Review, SocialEdge
from app.services.data_store import get_db
from app.services.feedback import add_feedback
from app.services.metrics import compute_metrics
from app.services.recommendation import get_sequence_events, get_social_graph, get_startup_type, recommend_stream


router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/data/generate")
async def generate_snapshot(payload: DataGenerateRequest):
    # This endpoint was for in-memory generation.
    # With SQL, we should probably deprecate it or re-implement it to insert into SQL.
    # For now, let's return a message saying please use the init_sql script.
    return {"message": "Please use scripts/sync_sql.py to reset/generate data."}


@router.get("/users")
async def get_users_list(session: AsyncSession = Depends(get_db)) -> list[dict]:
    """Return a list of all users with basic info."""
    result = await session.execute(select(User))
    users = result.scalars().all()
    return [
        {
            "reviewerID": u.reviewerID,
            "reviewerName": u.reviewerName or "",
            "meta": u.meta or {},
        }
        for u in users
    ]


@router.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: str, session: AsyncSession = Depends(get_db)) -> UserProfileResponse:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return UserProfileResponse(
        reviewerID=user_id,
        reviewerName=user.reviewerName or "",
        meta=user.meta or {},
    )


@router.get("/users/{user_id}/startup-type", response_model=StartupTypeResponse)
async def startup_type(user_id: str, threshold: int = 5, session: AsyncSession = Depends(get_db)) -> StartupTypeResponse:
    startup, count = await get_startup_type(session, user_id, threshold)
    return StartupTypeResponse(
        reviewerID=user_id, startup_type=startup, behavior_count=count, threshold=threshold
    )


@router.get("/users/{user_id}/sequence", response_model=SequenceResponse)
async def sequence_events(user_id: str, session: AsyncSession = Depends(get_db)) -> SequenceResponse:
    events = await get_sequence_events(session, user_id)
    return SequenceResponse(events=events)


@router.get("/users/{user_id}/social-graph", response_model=SocialGraphResponse)
async def social_graph(user_id: str, session: AsyncSession = Depends(get_db)) -> SocialGraphResponse:
    data = await get_social_graph(session, user_id)
    return SocialGraphResponse(nodes=data["nodes"], edges=data["edges"])


@router.post("/recommend")
async def recommend_items(payload: RecommendRequest, session: AsyncSession = Depends(get_db)):
    # Verify user exists
    user = await session.get(User, payload.reviewerID)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
        
    return StreamingResponse(
        recommend_stream(
            session=session,
            reviewer_id=payload.reviewerID,
            top_k=payload.top_k,
            threshold=payload.threshold,
            mode=payload.mode,
            use_llm=payload.use_llm,
        ),
        media_type="text/event-stream"
    )


@router.post("/feedback")
async def feedback(payload: FeedbackRequest, session: AsyncSession = Depends(get_db)) -> dict:
    record = await add_feedback(session, payload.reviewerID, payload.asin, payload.action)
    return {"ok": True, "record": record}


@router.get("/metrics", response_model=MetricsResponse)
async def metrics(session: AsyncSession = Depends(get_db)) -> MetricsResponse:
    return MetricsResponse(metrics=await compute_metrics(session))
