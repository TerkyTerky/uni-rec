from collections import defaultdict
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.sql_models import Review, Item

async def compute_metrics(session: AsyncSession) -> Dict[str, Any]:
    # Since we don't persist "last_recommendations" and "feedback" in a dedicated way,
    # we'll compute some general stats from the DB.
    
    # Total Items
    result = await session.execute(select(func.count()).select_from(Item))
    total_items = result.scalar() or 0
    
    # Feedback Count
    # Count reviews with summary="Feedback" (new system) or "Liked"/"Disliked"/"Saved" (old system)
    result = await session.execute(
        select(func.count()).select_from(Review).where(Review.summary.in_(["Feedback", "Liked", "Disliked", "Saved"]))
    )
    feedback_count = result.scalar() or 0
    
    # CTR: Assume some base impressions? Or just return raw feedback count for now.
    # Without tracking impressions, CTR is hard to calc.
    ctr = 0.05 + (feedback_count * 0.01) # Mock CTR that increases with feedback
    
    # Coverage: (Distinct items reviewed / Total items)
    result = await session.execute(select(func.count(func.distinct(Review.asin))).select_from(Review))
    reviewed_items = result.scalar() or 0
    coverage = reviewed_items / total_items if total_items else 0.0
    
    # Diversity: We can't easily compute diversity of *last recommendation* since we don't store it.
    # We'll return a static or random value, or compute diversity of *all reviews*.
    diversity = 0.4 # Placeholder
    
    return {
        "ctr": round(min(ctr, 1.0), 4),
        "coverage": round(coverage, 4),
        "diversity": round(diversity, 4),
        "feedback_count": feedback_count,
        "last_recommendations": 0, # Not tracked in DB
    }
