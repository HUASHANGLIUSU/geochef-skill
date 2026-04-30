"""NASA Earth Observatory 每日一图（Image of the Day）。"""

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html import unescape

import urllib.request

NASA_RSS_URL = "https://earthobservatory.nasa.gov/feeds/image-of-the-day.rss"

_NS = {
    "media": "http://search.yahoo.com/mrss/",
    "dc": "http://purl.org/dc/elements/1.1/",
}
_CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"

# 简单内存缓存，避免同一进程内频繁请求
_cache: dict = {"items": None, "fetched_at": None}
_CACHE_TTL_SECONDS = 3600


def _extract_image_from_html(html: str) -> str | None:
    """从 content:encoded 的 HTML 中提取主图 URL。"""
    html = unescape(html)

    def parse_img_attrs(tag: str) -> dict:
        return dict(re.findall(r'(\w[\w-]*)="([^"]*)"', tag))

    img_tags = re.findall(r"<img\s[^>]+>", html, re.IGNORECASE | re.DOTALL)

    # 优先 fetchpriority="high"
    for tag in img_tags:
        attrs = parse_img_attrs(tag)
        if attrs.get("fetchpriority") == "high" and attrs.get("src", "").startswith("https://"):
            return _normalize_url(attrs["src"])

    # 备用：assets.science.nasa.gov
    for tag in img_tags:
        attrs = parse_img_attrs(tag)
        src = attrs.get("src", "")
        if src.startswith("https://assets.science.nasa.gov"):
            return _normalize_url(src)

    return None


def _normalize_url(url: str) -> str:
    """裁剪图片为 1200px 宽。"""
    url = re.sub(r"([?&]w)=\d+", r"\g<1>=1200", url, count=1)
    url = re.sub(r"&h=\d+", "", url)
    return url


def _parse_rss(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        pub_date_str = (item.findtext("pubDate") or "").strip()

        pub_date = None
        for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT"):
            try:
                pub_date = datetime.strptime(pub_date_str, fmt)
                break
            except ValueError:
                continue

        image_url = None
        content_encoded = item.find(f"{{{_CONTENT_NS}}}encoded")
        if content_encoded is not None and content_encoded.text:
            image_url = _extract_image_from_html(content_encoded.text)

        if not image_url:
            mc = item.find("media:content", _NS)
            if mc is not None:
                image_url = mc.get("url")
        if not image_url:
            mt = item.find("media:thumbnail", _NS)
            if mt is not None:
                image_url = mt.get("url")
        if not image_url and desc:
            m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc, re.IGNORECASE)
            if m:
                image_url = m.group(1).replace("&amp;", "&")

        clean_desc = re.sub(r"<[^>]+>", "", desc).strip()
        clean_desc = re.sub(
            r"\s*The post .+appeared first on .+\.$", "", clean_desc
        ).strip()

        items.append(
            {
                "title": title,
                "link": link,
                "description": clean_desc,
                "date": pub_date,
                "image_url": image_url,
            }
        )

    return items


def _fetch_items() -> tuple[list[dict], str | None]:
    """拉取 RSS，带简单内存缓存（TTL 1 小时）。"""
    now = datetime.now(timezone.utc).timestamp()
    if (
        _cache["items"] is not None
        and _cache["fetched_at"] is not None
        and now - _cache["fetched_at"] < _CACHE_TTL_SECONDS
    ):
        return _cache["items"], None

    try:
        req = urllib.request.Request(
            NASA_RSS_URL,
            headers={"User-Agent": "Mozilla/5.0 (compatible; GeoChef-MCP/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_text = resp.read().decode("utf-8", errors="replace")

        items = _parse_rss(xml_text)
        items.sort(
            key=lambda x: x["date"] or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        _cache["items"] = items
        _cache["fetched_at"] = now
        return items, None

    except TimeoutError:
        return [], "请求超时，请稍后重试。"
    except Exception as e:
        return [], f"获取失败：{e}"


def _pick_best(items: list[dict]) -> dict | None:
    """优先返回当天条目，否则返回最新一条。"""
    if not items:
        return None
    today = datetime.now(timezone.utc).date()
    for item in items:
        if item["date"] and item["date"].date() == today:
            return item
    return items[0]


def get_nasa_image_of_the_day(recent_count: int = 5) -> str:
    """
    获取 NASA Earth Observatory 每日一图，返回 Markdown 格式文本。

    Args:
        recent_count: 额外返回的近期图片数量（0~9），默认 5
    """
    items, error = _fetch_items()
    if error:
        return f"⚠️ {error}"
    if not items:
        return "⚠️ 暂无数据，请稍后重试。"

    best = _pick_best(items)
    if not best:
        return "⚠️ 暂无数据。"

    today = datetime.now(timezone.utc).date()
    item_date = best["date"].date() if best["date"] else None
    date_str = best["date"].strftime("%Y-%m-%d") if best["date"] else "—"
    is_today = item_date == today

    freshness = "📅 今日更新" if is_today else f"📅 最新（{date_str}）"

    lines = [
        f"## 🛰️ NASA 每日一图",
        f"**{best['title']}**  {freshness}",
        "",
    ]

    if best["image_url"]:
        lines.append(f"![{best['title']}]({best['image_url']})")
        lines.append("")

    if best["description"]:
        lines.append(best["description"])
        lines.append("")

    lines.append(
        f'📡 来源：[NASA Earth Observatory — Image of the Day]({best["link"]})'
    )

    # 近期图片列表
    n = max(0, min(recent_count, 9))
    recent = [it for it in items if it is not best][:n]
    if recent:
        lines.append("")
        lines.append("---")
        lines.append("### 🗂️ 近期图片")
        for it in recent:
            d = it["date"].strftime("%Y-%m-%d") if it["date"] else ""
            img_part = f"![{it['title']}]({it['image_url']})\n\n" if it["image_url"] else ""
            lines.append(
                f"\n**{it['title']}** （{d}）\n\n"
                f"{img_part}"
                f"[查看原文]({it['link']})"
            )

    return "\n".join(lines)
