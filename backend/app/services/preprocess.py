from collections import defaultdict
from typing import Any, Dict, List, Tuple


def build_user_review_map(reviews: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    result: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for event in reviews:
        result[event["reviewerID"]].append(event)
    for reviewer_id in result:
        result[reviewer_id] = sorted(result[reviewer_id], key=lambda x: x["unixReviewTime"])
    return result


def build_item_popularity(reviews: List[Dict[str, Any]]) -> Dict[str, int]:
    popularity: Dict[str, int] = defaultdict(int)
    for event in reviews:
        popularity[event["asin"]] += 1
    return popularity


def build_user_recent_sequence(
    user_events: List[Dict[str, Any]], limit: int = 10
) -> List[Dict[str, Any]]:
    return list(sorted(user_events, key=lambda x: x["unixReviewTime"], reverse=True)[:limit])


def compute_category_preferences(
    user_events: List[Dict[str, Any]], items: Dict[str, Any]
) -> Dict[str, float]:
    scores: Dict[str, float] = defaultdict(float)
    for idx, event in enumerate(reversed(user_events[-10:])):
        item = items.get(event["asin"])
        if not item:
            continue
        weight = 1.0 + idx * 0.1
        categories = item.get("categories") or []
        leaf = categories[0][-1] if categories and categories[0] else "Unknown"
        scores[leaf] += weight
    return scores


def build_social_neighbors(edges: List[Dict[str, Any]]) -> Dict[str, List[Tuple[str, float]]]:
    neighbors: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    for edge in edges:
        neighbors[edge["source"]].append((edge["target"], edge["weight"]))
    return neighbors
