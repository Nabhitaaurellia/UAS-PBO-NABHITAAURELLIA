import json
from pathlib import Path
from typing import Any, Dict
from core.konstanta import DATA_DIR, DB_PATH

DEFAULT_DB: Dict[str, Any] = {
    "users": [],
    "competition": None,
    "registrations": [],
    "schedule_slots": [],
    "scores": []
}

class JsonStore:
    def __init__(self, path: Path = DB_PATH):
        self.path = path
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.write(DEFAULT_DB)

    def read(self) -> Dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def write(self, data: Dict[str, Any]) -> None:
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(self.path)