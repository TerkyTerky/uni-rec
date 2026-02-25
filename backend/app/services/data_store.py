import json
from pathlib import Path
from typing import Any, Dict

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


def init_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = DATA_DIR / "snapshot.json"
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
