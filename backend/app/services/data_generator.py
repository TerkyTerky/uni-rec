import random
from typing import Any, Dict, List


def generate_data(
    users: int = 30,
    items: int = 80,
    behaviors_per_user: int = 20,
    social_degree: int = 3,
    seed: int = 42,
) -> Dict[str, Any]:
    random.seed(seed)
    category_paths = [
        ["Electronics", "Computers & Accessories", "Laptops"],
        ["Electronics", "Computers & Accessories", "Storage"],
        ["Electronics", "Audio", "Headphones"],
        ["Electronics", "Audio", "Speakers"],
        ["Electronics", "Camera & Photo", "Action Cameras"],
        ["Electronics", "Smart Home", "Smart Speakers"],
        ["Electronics", "Gaming", "Controllers"],
        ["Electronics", "Networking", "Routers"],
        ["Electronics", "Office Electronics", "Monitors"],
        ["Electronics", "Cell Phones", "Smartphones"],
    ]
    feature_pool = [
        "Bluetooth",
        "Wi-Fi",
        "USB-C",
        "Fast Charging",
        "Noise Cancelling",
        "4K",
        "Lightweight",
        "Low Latency",
        "Long Battery Life",
        "Portable",
    ]
    product_types = [
        "Laptop",
        "Smartphone",
        "Bluetooth Headphones",
        "Smart Speaker",
        "Router",
        "Monitor",
        "Mechanical Keyboard",
        "Wireless Mouse",
        "Game Controller",
        "Action Camera",
        "Smart Watch",
        "External SSD",
    ]
    users_map: Dict[str, Any] = {}
    items_map: Dict[str, Any] = {}
    reviews: List[Dict[str, Any]] = []
    social_edges: List[Dict[str, Any]] = []

    for i in range(items):
        asin = f"B{random.randint(1000000, 9999999)}"
        category_path = random.choice(category_paths)
        brand = f"Brand{random.randint(1, 80)}"
        model = f"{random.choice(['X', 'M', 'S', 'Z'])}{random.randint(100, 999)}"
        product = random.choice(product_types)
        items_map[asin] = {
            "asin": asin,
            "title": f"{brand} {product} {model}",
            "feature": random.sample(feature_pool, k=min(4, len(feature_pool))),
            "description": f"{brand} {product} with {', '.join(random.sample(feature_pool, k=2))}.",
            "price": round(random.uniform(19, 4999), 2),
            "imageURL": f"https://images.example.com/{asin}.jpg",
            "imageURLHighRes": f"https://images.example.com/{asin}_hr.jpg",
            "also_buy": random.sample(list(items_map.keys()) or [asin], k=min(3, max(1, len(items_map)))),
            "also_viewed": random.sample(list(items_map.keys()) or [asin], k=min(5, max(1, len(items_map)))),
            "brand": brand,
            "categories": [category_path],
        }

    for i in range(users):
        reviewer_id = f"A{random.randint(1000000, 9999999)}"
        reviewer_name = f"Reviewer{i}"
        users_map[reviewer_id] = {
            "reviewerID": reviewer_id,
            "reviewerName": reviewer_name,
            "meta": {"cold_start": False},
        }

    for reviewer_id in users_map:
        for t in range(behaviors_per_user):
            asin = random.choice(list(items_map.keys()))
            reviews.append(
                {
                    "reviewerID": reviewer_id,
                    "asin": asin,
                    "reviewerName": users_map[reviewer_id]["reviewerName"],
                    "overall": random.choice([2.0, 3.0, 4.0, 5.0]),
                    "reviewText": "Great value for the price and performance.",
                    "summary": "Solid electronics choice",
                    "unixReviewTime": 1700000000 + t * 3600 + random.randint(0, 600),
                    "reviewTime": "01 01, 2018",
                    "vote": str(random.randint(0, 12)),
                    "verified": random.choice([True, False]),
                    "style": {"Color": random.choice(["Black", "White", "Blue"])},
                    "image": [f"https://images.example.com/reviews/{asin}.jpg"],
                }
            )

    user_list = list(users_map.keys())
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
