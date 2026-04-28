"""数据文件下载与缓存管理。"""

import os
import sys
import urllib.request
from pathlib import Path

GITHUB_REPO = "VisionXLab/Awesome-RS-VL-Data"
DATA_FILENAME = "rs_vlm_datasets.xlsx"
DOWNLOAD_URL = f"https://github.com/{GITHUB_REPO}/releases/latest/download/{DATA_FILENAME}"

FALLBACK_URL = (
    f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{DATA_FILENAME}"
)


def get_cache_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    cache_dir = base / "geochef"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_data_path() -> Path:
    """返回本地数据文件路径，不存在时自动下载。"""
    # 优先使用同目录下的文件（开发模式）
    local = Path(__file__).parent.parent / DATA_FILENAME
    if local.exists():
        return local

    cache_path = get_cache_dir() / DATA_FILENAME
    if cache_path.exists():
        return cache_path

    print(f"[GeoChef] 首次运行，正在下载数据文件...")
    _download(cache_path)
    return cache_path


def _download(dest: Path):
    for url in [DOWNLOAD_URL, FALLBACK_URL]:
        try:
            print(f"[GeoChef] 下载中: {url}")
            urllib.request.urlretrieve(url, dest)
            print(f"[GeoChef] 下载完成: {dest}")
            return
        except Exception as e:
            print(f"[GeoChef] 下载失败 ({url}): {e}")

    raise RuntimeError(
        f"无法下载数据文件，请手动下载 {DATA_FILENAME} 并放置到：{dest}"
    )
