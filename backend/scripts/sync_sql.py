import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add project root to path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

# Load .env
load_dotenv(BASE_DIR / ".env")

from app.models.sql_models import Base, User, Item, Review, SocialEdge

async def sync_to_mysql():
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "")
    mysql_host = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port = os.getenv("MYSQL_PORT", "3306")
    mysql_db = os.getenv("MYSQL_DB", "uni_rec")
    
    if not mysql_password:
        print("[Error] Please set MYSQL_PASSWORD in .env")
        return

    # Construct async connection string
    db_url = f"mysql+aiomysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"
    print(f"[MySQL] Connecting to {db_url.replace(mysql_password, '******')}...")
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        # Load snapshot data
        snapshot_path = BASE_DIR / "data" / "snapshot.json"
        if not snapshot_path.exists():
            print(f"[Error] Snapshot file not found at {snapshot_path}")
            return
            
        print(f"[Data] Loading snapshot from {snapshot_path}...")
        with open(snapshot_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Normalize data
        if "behaviors" in data and "reviews" not in data:
            data["reviews"] = data.pop("behaviors")

        async with async_session() as session:
            # 1. Clear existing data
            print("[Sync] Clearing existing tables...")
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            await session.execute(text("TRUNCATE TABLE social_edges"))
            await session.execute(text("TRUNCATE TABLE reviews"))
            await session.execute(text("TRUNCATE TABLE items"))
            await session.execute(text("TRUNCATE TABLE users"))
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            await session.commit()
            
            # 2. Sync Users
            users_data = data.get("users", {})
            if users_data:
                print(f"[Sync] Inserting {len(users_data)} users...")
                users = [
                    User(
                        reviewerID=u["reviewerID"],
                        reviewerName=u.get("reviewerName"),
                        meta=u.get("meta")
                    )
                    for u in users_data.values()
                ]
                session.add_all(users)
                await session.commit()
            
            # 3. Sync Items
            items_data = data.get("items", {})
            if items_data:
                print(f"[Sync] Inserting {len(items_data)} items...")
                # Process in batches to avoid packet too large errors
                batch_size = 500
                items_list = list(items_data.values())
                for i in range(0, len(items_list), batch_size):
                    batch = items_list[i : i + batch_size]
                    items = [
                        Item(
                            asin=item["asin"],
                            title=item.get("title", ""),
                            price=item.get("price", 0.0),
                            brand=item.get("brand"),
                            description=item.get("description"),
                            feature=item.get("feature"),
                            categories=item.get("categories"),
                            also_buy=item.get("also_buy"),
                            also_viewed=item.get("also_viewed"),
                            imageURL=item.get("imageURL"),
                            imageURLHighRes=item.get("imageURLHighRes")
                        )
                        for item in batch
                    ]
                    session.add_all(items)
                    await session.commit()
                    print(f"  - Inserted items batch {i // batch_size + 1}")

            # 4. Sync Reviews
            reviews_data = data.get("reviews", [])
            if reviews_data:
                print(f"[Sync] Inserting {len(reviews_data)} reviews...")
                batch_size = 1000
                for i in range(0, len(reviews_data), batch_size):
                    batch = reviews_data[i : i + batch_size]
                    reviews = [
                        Review(
                            reviewerID=r["reviewerID"],
                            asin=r["asin"],
                            overall=r.get("overall", 0.0),
                            reviewText=r.get("reviewText"),
                            summary=r.get("summary"),
                            unixReviewTime=r.get("unixReviewTime", 0),
                            reviewTime=r.get("reviewTime"),
                            vote=r.get("vote"),
                            verified=r.get("verified", False),
                            style=r.get("style"),
                            image=r.get("image")
                        )
                        for r in batch
                    ]
                    session.add_all(reviews)
                    await session.commit()
                    print(f"  - Inserted reviews batch {i // batch_size + 1}")
            
            # 5. Sync Social Edges
            edges_data = data.get("social_edges", [])
            if edges_data:
                print(f"[Sync] Inserting {len(edges_data)} social edges...")
                batch_size = 1000
                for i in range(0, len(edges_data), batch_size):
                    batch = edges_data[i : i + batch_size]
                    edges = [
                        SocialEdge(
                            source=e["source"],
                            target=e["target"],
                            weight=e.get("weight", 0.0),
                            type=e.get("type")
                        )
                        for e in batch
                    ]
                    session.add_all(edges)
                    await session.commit()
                    print(f"  - Inserted edges batch {i // batch_size + 1}")

        print("[Success] MySQL synchronization completed!")
        await engine.dispose()
        
    except Exception as e:
        print(f"[Error] Sync failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(sync_to_mysql())
