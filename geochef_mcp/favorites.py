"""收藏夹持久化存储（本地 JSON）。"""

import json
import os
import sys
from pathlib import Path


def get_favorites_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    path = base / "geochef"
    path.mkdir(parents=True, exist_ok=True)
    return path / "favorites.json"


_cache: dict | None = None


def _load() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    p = get_favorites_path()
    if not p.exists():
        _cache = {"datasets": []}
        return _cache
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("datasets", [])
        _cache = data
        return _cache
    except Exception:
        _cache = {"datasets": []}
        return _cache


def _save(data: dict):
    global _cache
    _cache = data
    with open(get_favorites_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_favorites() -> list[str]:
    return _load()["datasets"]


def add_favorite(name: str) -> bool:
    data = _load()
    if name in data["datasets"]:
        return False
    data["datasets"].append(name)
    _save(data)
    return True


def remove_favorite(name: str) -> bool:
    data = _load()
    if name not in data["datasets"]:
        return False
    data["datasets"].remove(name)
    _save(data)
    return True


def is_favorite(name: str) -> bool:
    return name in _load()["datasets"]


# ── 对比列表（最多 4 个）────────────────────────────────────────

COMPARE_MAX = 4


def list_compare() -> list[str]:
    return _load().get("compare", [])


def add_compare(name: str) -> tuple[bool, str]:
    """返回 (成功, 消息)"""
    data = _load()
    compare = data.setdefault("compare", [])
    if name in compare:
        return False, f"**{name}** 已在对比列表中。"
    if len(compare) >= COMPARE_MAX:
        return False, f"对比列表已满（最多 {COMPARE_MAX} 个），请先移除一个再添加。"
    compare.append(name)
    _save(data)
    return True, ""


def remove_compare(name: str) -> bool:
    data = _load()
    compare = data.get("compare", [])
    if name not in compare:
        return False
    compare.remove(name)
    data["compare"] = compare
    _save(data)
    return True


def clear_compare():
    data = _load()
    data["compare"] = []
    _save(data)
