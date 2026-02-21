import gzip
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, Iterable

from pymongo import MongoClient

from app.core.config import settings
from app.services.data_generator import generate_data


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(settings.data_dir) if settings.data_dir else BASE_DIR / "data"


store: Dict[str, Any] = {
    "users": {},
    "items": {},
    "reviews": [],
    "social_edges": [],
    "feedback": [],
    "last_recommendations": [],
}


def _parse_json_lines(path: Path) -> Iterable[Dict[str, Any]]:
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as f:
            for line in f:
                raw = line.decode("utf-8").strip()
                if raw:
                    yield json.loads(raw)
    else:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                raw = line.strip()
                if raw:
                    yield json.loads(raw)


def _normalize_item(record: Dict[str, Any]) -> Dict[str, Any]:
    asin = record.get("asin", "")
    related = record.get("related") or {}
    categories = record.get("categories")
    if not isinstance(categories, list):
        categories = []
    return {
        "asin": asin,
        "title": record.get("title") or f"Item {asin}",
        "feature": record.get("feature") or [],
        "description": record.get("description") or "",
        "price": record.get("price") or 0,
        "imageURL": record.get("imageURL") or record.get("imUrl") or "",
        "imageURLHighRes": record.get("imageURLHighRes") or record.get("imageURL") or record.get("imUrl") or "",
        "also_buy": record.get("also_buy") or related.get("also_bought") or related.get("bought_together") or [],
        "also_viewed": record.get("also_viewed") or related.get("also_viewed") or [],
        "brand": record.get("brand") or "",
        "categories": categories,
    }


def _load_real_data() -> Dict[str, Any] | None:
    reviews_path = Path(os.getenv("REVIEWS_FILE", str(DATA_DIR / "reviews_Electronics.json.gz")))
    meta_path = Path(os.getenv("METADATA_FILE", str(DATA_DIR / "meta_Electronics.json.gz")))
    if not reviews_path.exists() or not meta_path.exists():
        return None

    max_reviews = int(os.getenv("MAX_REVIEWS", "5000"))
    max_items = int(os.getenv("MAX_ITEMS", "2000"))
    max_users = int(os.getenv("MAX_USERS", "2000"))
    social_degree = int(os.getenv("SOCIAL_DEGREE", "3"))

    users_map: Dict[str, Any] = {}
    reviews: list[Dict[str, Any]] = []
    asin_set: set[str] = set()

    for review in _parse_json_lines(reviews_path):
        reviewer_id = review.get("reviewerID")
        asin = review.get("asin")
        if not reviewer_id or not asin:
            continue
        if max_users and reviewer_id not in users_map and len(users_map) >= max_users:
            continue
        if max_items and asin not in asin_set and len(asin_set) >= max_items:
            continue
        reviewer_name = review.get("reviewerName") or ""
        users_map.setdefault(
            reviewer_id,
            {"reviewerID": reviewer_id, "reviewerName": reviewer_name, "meta": {"cold_start": False}},
        )
        if reviewer_name and not users_map[reviewer_id].get("reviewerName"):
            users_map[reviewer_id]["reviewerName"] = reviewer_name
        asin_set.add(asin)
        reviews.append(
            {
                "reviewerID": reviewer_id,
                "asin": asin,
                "reviewerName": reviewer_name,
                "overall": float(review.get("overall", 0.0)),
                "reviewText": review.get("reviewText") or "",
                "summary": review.get("summary") or "",
                "unixReviewTime": int(review.get("unixReviewTime", 0)),
                "reviewTime": review.get("reviewTime") or "",
                "vote": str(review.get("vote") or "0"),
                "verified": bool(review.get("verified", False)),
                "style": review.get("style") or {},
                "image": review.get("image") or [],
            }
        )
        if max_reviews and len(reviews) >= max_reviews:
            break

    items_map: Dict[str, Any] = {}
    for meta in _parse_json_lines(meta_path):
        asin = meta.get("asin")
        if not asin:
            continue
        if asin_set and asin not in asin_set:
            continue
        items_map[asin] = _normalize_item(meta)
        if max_items and len(items_map) >= max_items:
            break

    if not items_map:
        for asin in asin_set:
            items_map[asin] = {
                "asin": asin,
                "title": f"Item {asin}",
                "feature": [],
                "description": "",
                "price": 0,
                "imageURL": "",
                "imageURLHighRes": "",
                "also_buy": [],
                "also_viewed": [],
                "brand": "",
                "categories": [["Electronics"]],
            }

    user_list = list(users_map.keys())
    social_edges: list[Dict[str, Any]] = []
    for reviewer_id in user_list:
        targets = random.sample(user_list, k=min(social_degree, len(user_list)))
        for target in targets:
            if target == reviewer_id:
                continue
            social_edges.append(
                {
                    "source": reviewer_id,
                    "target": target,
                    "weight": round(random.uniform(0.3, 1.0), 2),
                    "type": random.choice(["follow", "friend"]),
                }
            )

    return {
        "users": users_map,
        "items": items_map,
        "reviews": reviews,
        "social_edges": social_edges,
        "feedback": [],
        "last_recommendations": [],
    }


def _load_mongo_data() -> Dict[str, Any] | None:
    mongo_uri = os.getenv("MONGO_URI", "")
    if not mongo_uri:
        return None
    db_name = os.getenv("MONGO_DB", "uni_rec")
    reviews_collection = os.getenv("MONGO_REVIEWS_COLLECTION", "electronics_reviews")
    items_collection = os.getenv("MONGO_ITEMS_COLLECTION", "electronics_items")
    users_collection = os.getenv("MONGO_USERS_COLLECTION", "electronics_users")
    max_reviews = int(os.getenv("MAX_REVIEWS", "5000"))
    max_items = int(os.getenv("MAX_ITEMS", "2000"))
    max_users = int(os.getenv("MAX_USERS", "2000"))
    social_degree = int(os.getenv("SOCIAL_DEGREE", "3"))

    try:
        client = MongoClient(mongo_uri)
        db = client[db_name]
        if db[reviews_collection].estimated_document_count() == 0 and db[
            items_collection
        ].estimated_document_count() == 0:
            client.close()
            return None
        users_map: Dict[str, Any] = {}
        reviews: list[Dict[str, Any]] = []
        asin_set: set[str] = set()

        if db[users_collection].estimated_document_count() > 0:
            cursor = db[users_collection].find({}, {"_id": 0})
            if max_users:
                cursor = cursor.limit(max_users)
            for user in cursor:
                reviewer_id = user.get("reviewerID")
                if not reviewer_id:
                    continue
                users_map[reviewer_id] = {
                    "reviewerID": reviewer_id,
                    "reviewerName": user.get("reviewerName") or "",
                    "meta": user.get("meta") or {"cold_start": False},
                }

        review_cursor = db[reviews_collection].find({}, {"_id": 0})
        if max_reviews:
            review_cursor = review_cursor.limit(max_reviews)
        for review in review_cursor:
            reviewer_id = review.get("reviewerID")
            asin = review.get("asin")
            if not reviewer_id or not asin:
                continue
            if max_users and reviewer_id not in users_map and len(users_map) >= max_users:
                continue
            reviewer_name = review.get("reviewerName") or ""
            users_map.setdefault(
                reviewer_id,
                {"reviewerID": reviewer_id, "reviewerName": reviewer_name, "meta": {"cold_start": False}},
            )
            if reviewer_name and not users_map[reviewer_id].get("reviewerName"):
                users_map[reviewer_id]["reviewerName"] = reviewer_name
            if max_items and asin not in asin_set and len(asin_set) >= max_items:
                continue
            asin_set.add(asin)
            reviews.append(
                {
                    "reviewerID": reviewer_id,
                    "asin": asin,
                    "reviewerName": reviewer_name,
                    "overall": float(review.get("overall", 0.0)),
                    "reviewText": review.get("reviewText") or "",
                    "summary": review.get("summary") or "",
                    "unixReviewTime": int(review.get("unixReviewTime", 0)),
                    "reviewTime": review.get("reviewTime") or "",
                    "vote": str(review.get("vote") or "0"),
                    "verified": bool(review.get("verified", False)),
                    "style": review.get("style") or {},
                    "image": review.get("image") or [],
                }
            )

        items_map: Dict[str, Any] = {}
        item_query: Dict[str, Any] = {}
        if asin_set:
            item_query = {"asin": {"$in": list(asin_set)}}
        item_cursor = db[items_collection].find(item_query, {"_id": 0})
        if max_items:
            item_cursor = item_cursor.limit(max_items)
        for meta in item_cursor:
            asin = meta.get("asin")
            if not asin:
                continue
            items_map[asin] = _normalize_item(meta)

        client.close()

        if not items_map:
            for asin in asin_set:
                items_map[asin] = {
                    "asin": asin,
                    "title": f"Item {asin}",
                    "feature": [],
                    "description": "",
                    "price": 0,
                    "imageURL": "",
                    "imageURLHighRes": "",
                    "also_buy": [],
                    "also_viewed": [],
                    "brand": "",
                    "categories": [["Electronics"]],
                }

        user_list = list(users_map.keys())
        social_edges: list[Dict[str, Any]] = []
        for reviewer_id in user_list:
            targets = random.sample(user_list, k=min(social_degree, len(user_list)))
            for target in targets:
                if target == reviewer_id:
                    continue
                social_edges.append(
                    {
                        "source": reviewer_id,
                        "target": target,
                        "weight": round(random.uniform(0.3, 1.0), 2),
                        "type": random.choice(["follow", "friend"]),
                    }
                )

        return {
            "users": users_map,
            "items": items_map,
            "reviews": reviews,
            "social_edges": social_edges,
            "feedback": [],
            "last_recommendations": [],
        }
    except Exception:
        return None


def init_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = DATA_DIR / "snapshot.json"
    data = _load_mongo_data()
    if not data:
        data = _load_real_data()
    if data:
        store.update(data)
        persist_snapshot()
        return
    if snapshot.exists():
        data = json.loads(snapshot.read_text(encoding="utf-8"))
        if "behaviors" in data and "reviews" not in data:
            data["reviews"] = data.pop("behaviors")
        store.update(data)
        return
    data = generate_data()
    store.update(data)
    persist_snapshot()


def persist_snapshot() -> None:
    snapshot = DATA_DIR / "snapshot.json"
    snapshot.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def update_store(data: Dict[str, Any]) -> None:
    if "behaviors" in data and "reviews" not in data:
        data["reviews"] = data.pop("behaviors")
    store.update(data)
    store["feedback"] = []
    store["last_recommendations"] = []
    persist_snapshot()
