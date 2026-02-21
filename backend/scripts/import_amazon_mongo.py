import gzip
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

from pymongo import MongoClient


def parse_json_lines(path: Path) -> Iterable[Dict[str, Any]]:
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


def normalize_item(record: Dict[str, Any]) -> Dict[str, Any]:
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


def batched(items: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]


def main() -> None:
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB", "uni_rec")
    reviews_collection = os.getenv("MONGO_REVIEWS_COLLECTION", "electronics_reviews")
    items_collection = os.getenv("MONGO_ITEMS_COLLECTION", "electronics_items")
    users_collection = os.getenv("MONGO_USERS_COLLECTION", "electronics_users")
    reviews_path = Path(os.getenv("REVIEWS_FILE", "backend/data/reviews_Electronics.json.gz"))
    meta_path = Path(os.getenv("METADATA_FILE", "backend/data/meta_Electronics.json.gz"))
    max_reviews = int(os.getenv("MAX_REVIEWS", "5000"))
    max_items = int(os.getenv("MAX_ITEMS", "2000"))
    max_users = int(os.getenv("MAX_USERS", "2000"))
    batch_size = int(os.getenv("BATCH_SIZE", "1000"))
    clear_collections = os.getenv("CLEAR_COLLECTIONS", "1") == "1"

    client = MongoClient(mongo_uri)
    db = client[db_name]

    if clear_collections:
        db[reviews_collection].delete_many({})
        db[items_collection].delete_many({})
        db[users_collection].delete_many({})

    users_map: Dict[str, Any] = {}
    reviews: List[Dict[str, Any]] = []
    asin_set: set[str] = set()

    for review in parse_json_lines(reviews_path):
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
    for meta in parse_json_lines(meta_path):
        asin = meta.get("asin")
        if not asin:
            continue
        if asin_set and asin not in asin_set:
            continue
        items_map[asin] = normalize_item(meta)
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

    if users_map:
        db[users_collection].insert_many(list(users_map.values()), ordered=False)
    for chunk in batched(reviews, batch_size):
        db[reviews_collection].insert_many(chunk, ordered=False)
    for chunk in batched(list(items_map.values()), batch_size):
        db[items_collection].insert_many(chunk, ordered=False)

    db[reviews_collection].create_index("reviewerID")
    db[users_collection].create_index("reviewerID")

    client.close()


if __name__ == "__main__":
    main()
