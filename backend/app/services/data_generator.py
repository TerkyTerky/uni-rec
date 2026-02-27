import asyncio
import random
from typing import Any, Dict, List

from app.core.llm import generate_reviews

async def generate_data(
    users: int = 30,
    items: int = 80,
    behaviors_per_user: int = 20,
    social_degree: int = 3,
    seed: int = 42,
) -> Dict[str, Any]:
    random.seed(seed)
    
    # Generate review templates using LLM in background
    review_templates = []
    try:
        # Generate reviews for a few key product categories
        tasks = [
            generate_reviews(5, "笔记本电脑"),
            generate_reviews(5, "智能手机"),
            generate_reviews(5, "蓝牙耳机"),
            generate_reviews(5, "智能音箱"),
            generate_reviews(5, "运动相机"),
            generate_reviews(5, "游戏手柄"),
            generate_reviews(5, "路由器"),
            generate_reviews(5, "4K显示器"),
            generate_reviews(5, "机械键盘"),
            generate_reviews(5, "智能手表"),
            generate_reviews(5, "移动硬盘"),
        ]
        results = await asyncio.gather(*tasks)
        for res in results:
            review_templates.extend(res)
    except Exception as e:
        print(f"[DataGen] LLM review generation failed: {e}")
        
    if not review_templates:
        review_templates = [
            {"reviewText": "性价比很高。", "summary": "不错的选择"},
            {"reviewText": "质量可以更好。", "summary": "一般"},
            {"reviewText": "非常喜欢！", "summary": "优秀"},
            {"reviewText": "不如预期。", "summary": "失望"},
            {"reviewText": "如宣传所言。", "summary": "靠谱的产品"},
        ]

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

    # Generate unique Item IDs
    item_id_set = set()
    while len(item_id_set) < items:
        asin = f"B{random.randint(1000000, 9999999)}"
        item_id_set.add(asin)
    
    for asin in item_id_set:
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
            "also_buy": [],
            "also_viewed": [],
            "brand": brand,
            "categories": [category_path],
        }

    item_ids = list(items_map.keys())
    for item in items_map.values():
        item["also_buy"] = random.sample(item_ids, k=min(3, len(item_ids)))
        item["also_viewed"] = random.sample(item_ids, k=min(5, len(item_ids)))

    # Generate unique User IDs
    user_id_set = set()
    while len(user_id_set) < users:
        reviewer_id = f"A{random.randint(1000000, 9999999)}"
        user_id_set.add(reviewer_id)
        
    for i, reviewer_id in enumerate(user_id_set):
        reviewer_name = f"Reviewer{i}"
        users_map[reviewer_id] = {
            "reviewerID": reviewer_id,
            "reviewerName": reviewer_name,
            "meta": {"cold_start": False},
        }

    # Generate reviews
    # To avoid duplicate (reviewerID, asin) pairs
    user_reviewed_items = {uid: set() for uid in users_map.keys()}
    
    for reviewer_id in users_map:
        target_count = behaviors_per_user
        # Ensure we don't try to review more items than exist
        if target_count > len(item_ids):
            target_count = len(item_ids)
            
        # Select random unique items for this user
        chosen_items = random.sample(item_ids, k=target_count)
        
        for t, asin in enumerate(chosen_items):
            template = random.choice(review_templates)
            reviews.append(
                {
                    "reviewerID": reviewer_id,
                    "asin": asin,
                    "reviewerName": users_map[reviewer_id]["reviewerName"],
                    "overall": random.choice([2.0, 3.0, 4.0, 5.0]),
                    "reviewText": template.get("reviewText", "Nice product"),
                    "summary": template.get("summary", "Review"),
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
        # Avoid self-loops and duplicate edges
        potential_targets = [u for u in user_list if u != reviewer_id]
        if not potential_targets:
            continue
            
        targets = random.sample(potential_targets, k=min(social_degree, len(potential_targets)))
        for target in targets:
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
