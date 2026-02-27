from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sql_models import Review
import time

async def add_feedback(session: AsyncSession, reviewer_id: str, asin: str, score: int) -> Dict[str, Any]:
    current_time = int(time.time())
    
    # Map score to review properties
    overall = float(score)
    summary = "Feedback"
    text = f"User rated this item {score} stars."

    new_review = Review(
        reviewerID=reviewer_id,
        asin=asin,
        overall=overall,
        summary=summary,
        reviewText=text,
        unixReviewTime=current_time,
        verified=True, # Mark as verified to distinguish or just for weight
        vote="0"
    )
    
    session.add(new_review)
    await session.commit()
        
    return {"reviewerID": reviewer_id, "asin": asin, "score": score, "timestamp": current_time}
