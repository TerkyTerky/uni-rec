from typing import Any, Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.llm import generate_reason
from app.models.sql_models import Review, Item, SocialEdge

# Preprocess helper functions like build_item_popularity are no longer needed
# as we will use SQL aggregations directly.

async def get_startup_type(session: AsyncSession, reviewer_id: str, threshold: int) -> Tuple[str, int]:
    result = await session.execute(
        select(func.count()).select_from(Review).where(Review.reviewerID == reviewer_id)
    )
    count = result.scalar() or 0
    startup_type = "cold" if count < threshold else "hot"
    return startup_type, count

async def sequence_recommend(session: AsyncSession, reviewer_id: str, top_k: int, use_llm: bool) -> List[Dict[str, Any]]:
    # 1. Get user's recent history
    history_result = await session.execute(
        select(Review.asin).where(Review.reviewerID == reviewer_id).order_by(desc(Review.unixReviewTime)).limit(20)
    )
    recent_asins = {row[0] for row in history_result.all()}
    
    # 2. Compute category preferences (simplified: most frequent category in history)
    # Ideally, this should be a complex SQL query, but for simplicity, let's fetch recent items' categories
    # However, to keep it efficient, we might just fallback to a popularity baseline or simple item-based CF.
    
    # Let's implement a simplified logic: 
    # Recommend popular items that are NOT in user's history
    # Sort by overall rating average (popularity proxy)
    
    stmt = (
        select(Item)
        .where(Item.asin.notin_(recent_asins) if recent_asins else True)
        # In a real system, you'd sort by a computed score. 
        # Here we just take some items. To make it "personalized", we could filter by preferred category.
        .limit(top_k * 2) 
    )
    
    result = await session.execute(stmt)
    candidates = result.scalars().all()
    
    # Simple scoring (mock)
    scored_items = []
    for item in candidates:
        score = 0.5 # Default score
        scored_items.append((item, score))
        
    scored_items.sort(key=lambda x: x[1], reverse=True)
    final_items = scored_items[:top_k]
    
    return [
        {
            "asin": item.asin,
            "score": score,
            "reason": "基于近期行为序列与热门内容推荐",
            "source": "sequence",
            "meta": {
                "title": item.title,
                "categories": item.categories,
                "imageURL": item.imageURL,
                "price": item.price
            },
        }
        for item, score in final_items
    ]

async def social_recommend(session: AsyncSession, reviewer_id: str, top_k: int, use_llm: bool) -> List[Dict[str, Any]]:
    # 1. Find neighbors
    stmt = select(SocialEdge).where(SocialEdge.source == reviewer_id)
    result = await session.execute(stmt)
    neighbors = result.scalars().all()
    
    if not neighbors:
        # Fallback to popularity if no neighbors
        return await sequence_recommend(session, reviewer_id, top_k, use_llm)
        
    neighbor_ids = [n.target for n in neighbors]
    neighbor_weights = {n.target: n.weight for n in neighbors}
    
    # 2. Find what neighbors reviewed
    # Select items reviewed by neighbors, ordered by neighbor weight * review rating
    # This is a bit complex in pure ORM, let's fetch recent reviews from neighbors
    reviews_stmt = (
        select(Review, Item)
        .join(Item, Review.asin == Item.asin)
        .where(Review.reviewerID.in_(neighbor_ids))
        .order_by(desc(Review.unixReviewTime))
        .limit(100)
    )
    reviews_result = await session.execute(reviews_stmt)
    
    item_scores = {}
    for review, item in reviews_result:
        weight = neighbor_weights.get(review.reviewerID, 1.0)
        score = weight * (review.overall or 3.0)
        if item.asin not in item_scores:
            item_scores[item.asin] = {
                "score": 0,
                "item": item
            }
        item_scores[item.asin]["score"] += score
        
    # Sort by score
    sorted_items = sorted(item_scores.values(), key=lambda x: x["score"], reverse=True)[:top_k]
    
    return [
        {
            "asin": x["item"].asin,
            "score": float(round(x["score"], 4)),
            "reason": "基于社交邻居行为与影响力推荐",
            "source": "social",
            "meta": {
                "title": x["item"].title,
                "categories": x["item"].categories,
                "imageURL": x["item"].imageURL,
                "price": x["item"].price
            },
        }
        for x in sorted_items
    ]

async def recommend_stream(
    session: AsyncSession,
    reviewer_id: str,
    top_k: int,
    threshold: int,
    mode: str,
    use_llm: bool,
):
    """
    Generator that yields SSE events for recommendation process.
    """
    import json
    
    # 1. Get base recommendations (fast)
    startup_type, count = await get_startup_type(session, reviewer_id, threshold)
    module = "sequence" if startup_type == "hot" else "social"
    if mode in ["sequence", "social"]:
        module = mode
        
    items = []
    if module == "sequence":
        items = await sequence_recommend(session, reviewer_id, top_k, use_llm)
        summary = "热启动用户使用序列推荐"
    else:
        items = await social_recommend(session, reviewer_id, top_k, use_llm)
        summary = "冷启动用户使用社交推荐"

    # Send initial data
    initial_payload = {
        "reviewerID": reviewer_id,
        "startup_type": startup_type,
        "module": module,
        "items": items,
        "summary": summary,
        "behavior_count": count,
        "status": "calculating" if use_llm else "completed"
    }
    yield f"data: {json.dumps(initial_payload)}\n\n"

    if not use_llm or not items:
        yield "event: done\ndata: {}\n\n"
        return

    # 2. Stream LLM reasoning
    # store["last_recommendations"] = items # Store not available anymore, maybe save to DB or cache?
    
    from app.core.llm import stream_reason
    titles = [item["meta"]["title"] for item in items[:5]]
    prompt = f"用户:{reviewer_id} 模块:{module} 候选内容:{titles} 请给出推荐理由"
    fallback = items[0]["reason"] if items else ""
    
    full_reason = ""
    async for chunk in stream_reason(prompt, fallback):
        # Format: "TYPE:CONTENT"
        if chunk.startswith("THINK:"):
            content = chunk[6:]
            yield f"event: thinking\ndata: {json.dumps({'content': content})}\n\n"
        elif chunk.startswith("TEXT:"):
            content = chunk[5:]
            full_reason += content
            yield f"event: reasoning\ndata: {json.dumps({'content': content})}\n\n"

    # 3. Send final update with reason
    updated_items = []
    for item in items:
        item["reason"] = full_reason.strip()
        updated_items.append(item)
    
    final_payload = {
        "items": updated_items,
        "status": "completed"
    }
    yield f"event: update\ndata: {json.dumps(final_payload)}\n\n"
    yield "event: done\ndata: {}\n\n"


async def get_sequence_events(session: AsyncSession, reviewer_id: str) -> List[Dict[str, Any]]:
    stmt = (
        select(Review, Item)
        .join(Item, Review.asin == Item.asin)
        .where(Review.reviewerID == reviewer_id)
        .order_by(desc(Review.unixReviewTime))
        .limit(20)
    )
    result = await session.execute(stmt)
    
    events = []
    for review, item in result:
        categories = item.categories or []
        leaf = categories[0][-1] if categories and categories[0] else "Unknown"
        events.append({
            "asin": review.asin,
            "overall": review.overall,
            "unixReviewTime": review.unixReviewTime,
            "title": item.title,
            "category": leaf,
            "ts": review.unixReviewTime
        })
    return events


async def get_social_graph(session: AsyncSession, reviewer_id: str) -> Dict[str, Any]:
    nodes = []
    edges = []
    
    stmt = select(SocialEdge).where(SocialEdge.source == reviewer_id)
    result = await session.execute(stmt)
    neighbors = result.scalars().all()
    
    nodes.append({"id": reviewer_id, "name": reviewer_id, "category": 0, "symbolSize": 40})
    
    for edge in neighbors:
        nodes.append(
            {
                "id": edge.target,
                "name": edge.target,
                "category": 1,
                "symbolSize": 30,
                "value": edge.weight,
            }
        )
        edges.append({"source": reviewer_id, "target": edge.target, "value": edge.weight})
        
    return {"nodes": nodes, "edges": edges}
