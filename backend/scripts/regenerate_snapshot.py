import asyncio
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

# Load .env
load_dotenv(BASE_DIR / ".env")

from app.services.data_generator import generate_data
from app.core.config import settings

DATA_DIR = Path(settings.data_dir) if settings.data_dir else BASE_DIR / "data"

async def regenerate_snapshot():
    print("[Data] Generating new data (this may take a while)...")
    # Increase counts for better testing
    data = await generate_data(
        users=50,
        items=200,
        behaviors_per_user=30,
        social_degree=5,
        seed=12345  # Change seed for variety
    )
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = DATA_DIR / "snapshot.json"
    
    print(f"[Data] Writing to {snapshot}...")
    snapshot.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print("[Success] Snapshot regenerated!")
    print(f"  - Users: {len(data['users'])}")
    print(f"  - Items: {len(data['items'])}")
    print(f"  - Reviews: {len(data['reviews'])}")
    print(f"  - Social Edges: {len(data['social_edges'])}")
    print("\nNext step: Run 'python3 scripts/sync_sql.py' to update MySQL database.")

if __name__ == "__main__":
    asyncio.run(regenerate_snapshot())
