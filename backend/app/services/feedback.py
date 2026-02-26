from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sql_models import Review
import time

async def add_feedback(session: AsyncSession, reviewer_id: str, asin: str, action: str) -> Dict[str, Any]:
    # For now, let's treat "like" as a positive vote and add a review record?
    # Or better, if we had a dedicated feedback table.
    # Since we reused the 'vote' field in reviews table as string, maybe we can't easily map it.
    
    # Option 1: Insert into a new Feedback table (if we created one, but we didn't yet)
    # Option 2: Mock behavior for now (print to log) or update a user preference table.
    
    # Let's assume we just log it for now as we don't have a dedicated Feedback table in SQL models yet,
    # or we can reuse the Review table to insert a "fake" review with action?
    
    # Actually, let's create a new Review entry with special marking? 
    # Or better, just return success for now until we define where to store explicit feedback.
    
    # Update: Let's insert a dummy review with current timestamp to reflect "interaction"
    if action == "like":
        new_review = Review(
            reviewerID=reviewer_id,
            asin=asin,
            overall=5.0, # Like = 5 stars
            summary="Liked",
            reviewText="User liked this item.",
            unixReviewTime=int(time.time()),
            verified=True
        )
        session.add(new_review)
        await session.commit()
        
    return {"reviewerID": reviewer_id, "asin": asin, "action": action}
