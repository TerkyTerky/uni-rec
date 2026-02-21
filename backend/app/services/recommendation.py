from typing import Any, Dict, List, Tuple

from app.core.llm import generate_reason
from app.services.data_store import store
from app.services.preprocess import (
    build_item_popularity,
    build_social_neighbors,
    build_user_recent_sequence,
    build_user_review_map,
    compute_category_preferences,
)


def get_startup_type(reviewer_id: str, threshold: int) -> Tuple[str, int]:
    user_map = build_user_review_map(store["reviews"])
    count = len(user_map.get(reviewer_id, []))
    startup_type = "cold" if count < threshold else "hot"
    return startup_type, count


def sequence_recommend(reviewer_id: str, top_k: int, use_llm: bool) -> List[Dict[str, Any]]:
    user_map = build_user_review_map(store["reviews"])
    user_events = user_map.get(reviewer_id, [])
    items = store["items"]
    category_scores = compute_category_preferences(user_events, items)
    popularity = build_item_popularity(store["reviews"])
    scored: List[Tuple[str, float]] = []
    for asin, item in items.items():
        categories = item.get("categories") or []
        leaf = categories[0][-1] if categories and categories[0] else "Unknown"
        score = category_scores.get(leaf, 0.0) + popularity.get(asin, 0) * 0.05
        scored.append((asin, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    recent_items = {e["asin"] for e in user_events[-20:]}
    results = []
    for asin, score in scored:
        if asin in recent_items:
            continue
        results.append((asin, score))
        if len(results) >= top_k:
            break
    return [
        {
            "asin": asin,
            "score": float(round(score, 4)),
            "reason": "基于近期行为序列与内容偏好推荐",
            "source": "sequence",
            "meta": items[asin],
        }
        for asin, score in results
    ]


def social_recommend(reviewer_id: str, top_k: int, use_llm: bool) -> List[Dict[str, Any]]:
    items = store["items"]
    reviews = store["reviews"]
    neighbors = build_social_neighbors(store["social_edges"])
    user_map = build_user_review_map(reviews)
    scored: Dict[str, float] = {}
    for neighbor_id, weight in neighbors.get(reviewer_id, []):
        neighbor_events = user_map.get(neighbor_id, [])[-10:]
        for event in neighbor_events:
            scored[event["asin"]] = scored.get(event["asin"], 0.0) + weight
    popularity = build_item_popularity(reviews)
    for asin in list(scored.keys()):
        scored[asin] += popularity.get(asin, 0) * 0.02
    ranked = sorted(scored.items(), key=lambda x: x[1], reverse=True)
    results = ranked[:top_k]
    if not results:
        results = sorted(popularity.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [
        {
            "asin": asin,
            "score": float(round(score, 4)),
            "reason": "基于社交邻居行为与影响力推荐",
            "source": "social",
            "meta": items[asin],
        }
        for asin, score in results
    ]


async def apply_llm_reason(
    reviewer_id: str, module: str, items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    titles = [item["meta"]["title"] for item in items[:5]]
    prompt = f"用户:{reviewer_id} 模块:{module} 候选内容:{titles} 请给出推荐理由"
    fallback = items[0]["reason"] if items else ""
    reason = await generate_reason(prompt, fallback)
    updated = []
    for item in items:
        item["reason"] = reason
        updated.append(item)
    return updated


async def recommend(
    reviewer_id: str,
    top_k: int,
    threshold: int,
    mode: str,
    use_llm: bool,
) -> Dict[str, Any]:
    startup_type, count = get_startup_type(reviewer_id, threshold)
    module = "sequence" if startup_type == "hot" else "social"
    if mode in ["sequence", "social"]:
        module = mode
    if module == "sequence":
        items = sequence_recommend(reviewer_id, top_k, use_llm)
        summary = "热启动用户使用序列推荐"
    else:
        items = social_recommend(reviewer_id, top_k, use_llm)
        summary = "冷启动用户使用社交推荐"
    if use_llm and items:
        items = await apply_llm_reason(reviewer_id, module, items)
    store["last_recommendations"] = items
    return {
        "reviewerID": reviewer_id,
        "startup_type": startup_type,
        "module": module,
        "items": items,
        "summary": summary,
        "behavior_count": count,
    }


def get_sequence_events(reviewer_id: str) -> List[Dict[str, Any]]:
    user_map = build_user_review_map(store["reviews"])
    events = build_user_recent_sequence(user_map.get(reviewer_id, []), limit=20)
    items = store["items"]
    for event in events:
        item = items.get(event["asin"], {})
        categories = item.get("categories") or []
        leaf = categories[0][-1] if categories and categories[0] else "Unknown"
        event["title"] = item.get("title", "")
        event["category"] = leaf
        event["ts"] = event.get("unixReviewTime")
    return events


def get_social_graph(reviewer_id: str) -> Dict[str, Any]:
    nodes = []
    edges = []
    neighbors = build_social_neighbors(store["social_edges"])
    nodes.append({"id": reviewer_id, "name": reviewer_id, "category": 0, "symbolSize": 40})
    for idx, (neighbor_id, weight) in enumerate(neighbors.get(reviewer_id, [])):
        nodes.append(
            {
                "id": neighbor_id,
                "name": neighbor_id,
                "category": 1,
                "symbolSize": 30,
                "value": weight,
            }
        )
        edges.append({"source": user_id, "target": neighbor_id, "value": weight})
    return {"nodes": nodes, "edges": edges}
