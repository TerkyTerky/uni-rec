from typing import Any, Dict

from app.services.data_store import store


def add_feedback(reviewer_id: str, asin: str, action: str) -> Dict[str, Any]:
    payload = {"reviewerID": reviewer_id, "asin": asin, "action": action}
    store["feedback"].append(payload)
    return payload
