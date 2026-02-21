from collections import defaultdict
from typing import Any, Dict

from app.services.data_store import store


def compute_metrics() -> Dict[str, Any]:
    total_items = len(store["items"])
    rec_items = {item["asin"] for item in store.get("last_recommendations", [])}
    feedback = store.get("feedback", [])
    likes = sum(1 for f in feedback if f["action"] == "like")
    ctr = likes / len(feedback) if feedback else 0.0
    coverage = len(rec_items) / total_items if total_items else 0.0
    category_count = defaultdict(int)
    for item in store.get("last_recommendations", []):
        categories = item.get("meta", {}).get("categories") or []
        leaf = categories[0][-1] if categories and categories[0] else "Unknown"
        category_count[leaf] += 1
    diversity = len(category_count) / len(rec_items) if rec_items else 0.0
    return {
        "ctr": round(ctr, 4),
        "coverage": round(coverage, 4),
        "diversity": round(diversity, 4),
        "feedback_count": len(feedback),
        "last_recommendations": len(rec_items),
    }
