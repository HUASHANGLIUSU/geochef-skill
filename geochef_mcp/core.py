"""GeoChef 数据核心逻辑（独立版，不依赖 Streamlit）。"""

import json
import random
import re

import pandas as pd

MODAL_KEYWORDS = {
    "SAR": {"sar", "sentinel-1", "sentinel1", "雷达"},
    "Optical (RGB)": {"rgb", "optical", "光学", "可见光"},
    "Multispectral": {"msi", "sentinel-2", "sentinel2", "landsat", "多光谱"},
    "Hyperspectral": {"hsi", "高光谱"},
    "LiDAR": {"lidar", "激光雷达"},
}

TASK_LIST = ["VQA", "Caption", "VG", "Classification", "Detection", "Segmentation"]


class GeoChef:
    def __init__(self):
        self.data = []
        self.years = []
        self.publishers = []
        self.methods = []
        self.modalities = list(MODAL_KEYWORDS.keys())
        self.tasks = TASK_LIST

    def load(self, path: str):
        sheets = [
            "VQA", "Cap", "Caption", "VG",
            "Comprehensive Data", "Comprehensive benchmark",
            "统计期刊数量、国家数量、年份",
        ]
        leakage_sheets = ["VQA", "Cap", "VG", "Comprehensive Data", "Comprehensive benchmark"]
        items, publishers, methods, years = [], set(), set(), set()

        self._name_to_sources: dict[str, list[str]] = {}
        self._source_to_names: dict[str, list[str]] = {}
        _source_display: dict[str, str] = {}

        for sheet in sheets:
            try:
                df = pd.read_excel(path, sheet_name=sheet)
                for _, row in df.iterrows():
                    item = row.dropna().to_dict()
                    item["_sheet"] = sheet
                    item["_text"] = json.dumps(item, ensure_ascii=False).lower()
                    item["_years"] = set(re.findall(r'\b(199\d|20[0-2]\d)\b', item["_text"]))
                    items.append(item)

                    p = str(item.get("Publisher", item.get("publisher", ""))).strip()
                    if p and len(p) > 1:
                        publishers.add(p)
                    m = str(item.get("Method", item.get("method", ""))).strip()
                    if m and len(m) > 1:
                        methods.add(m)
                    years.update(item["_years"])

                    if sheet in leakage_sheets:
                        name = str(item.get("Name", item.get("name", ""))).strip()
                        raw = str(item.get("包含数据集", "")).strip()
                        if name and raw and raw.lower() != "nan":
                            parts = re.split(r'[,，、;；\n]+|\s+and\s+', raw, flags=re.IGNORECASE)
                            sources = [p.strip() for p in parts if p.strip() and len(p.strip()) >= 2]
                            if sources:
                                self._name_to_sources[name] = sources
                                for src in sources:
                                    sl = src.lower()
                                    _source_display.setdefault(sl, src)
                                    self._source_to_names.setdefault(sl, [])
                                    if name not in self._source_to_names[sl]:
                                        self._source_to_names[sl].append(name)
            except Exception as e:
                print(f"[GeoChef] 加载 sheet '{sheet}' 失败: {e}")

        self.data = items
        self.years = sorted(list(years))
        self.publishers = sorted(list(publishers))
        self.methods = sorted(list(methods))
        self._all_sources = sorted(_source_display.values(), key=lambda x: x.lower())
        self._name_to_item: dict[str, dict] = {}
        for item in self.data:
            name = str(item.get("Name", item.get("name", ""))).strip()
            if name and name not in self._name_to_item:
                self._name_to_item[name] = item
        self._stats_cache: dict | None = None

    def get_all_sources(self) -> list[str]:
        return self._all_sources

    def get_item_by_name(self, name: str) -> dict | None:
        item = self._name_to_item.get(name.strip())
        if item:
            return item
        target = name.strip().lower()
        for n, it in self._name_to_item.items():
            if target in n.lower() or n.lower() in target:
                return it
        return None

    def get_all_dataset_names(self) -> list[str]:
        names, seen = [], set()
        for item in self.data:
            name = str(item.get("Name", item.get("name", ""))).strip()
            if name and name not in seen:
                names.append(name)
                seen.add(name)
        return sorted(names)

    def filter(self, modals, tasks, years, publishers, methods, kws) -> list[dict]:
        res = []
        for item in self.data:
            words = set(re.findall(r"\w+", item["_text"]))
            if (self._check_modal(words, modals) and
                    self._check_task(item["_text"], tasks) and
                    self._check_year(item["_years"], years) and
                    self._check_field(item, "Publisher", publishers) and
                    self._check_field(item, "Method", methods) and
                    self._check_kws(item["_text"], kws)):
                res.append(item)
        return res

    def query_by_source(self, source_name: str) -> list[dict]:
        sl = source_name.strip().lower()
        matched = next((k for k in self._source_to_names if sl in k or k in sl), None)
        if not matched:
            return []
        results = []
        for name in self._source_to_names[matched]:
            item = self._name_to_item.get(name)
            if item is None:
                continue
            remark = str(item.get("数据集备注", "")).strip()
            if remark.lower() == "nan":
                remark = ""
            results.append({
                "name": name,
                "sources": self._name_to_sources.get(name, []),
                "remark": remark,
                "item": item,
            })
        return results

    def query_by_multiple_sources(self, source_names: list[str]) -> dict:
        per_source = {src: self.query_by_source(src) for src in source_names}
        if len(source_names) > 1:
            name_sets = [set(e["name"] for e in v) for v in per_source.values()]
            common = name_sets[0].intersection(*name_sets[1:])
        else:
            common = set()
        return {"per_source": per_source, "common_names": common}

    def random_one(self) -> dict | None:
        return random.choice(self.data) if self.data else None

    def get_stats(self) -> dict:
        if self._stats_cache is not None:
            return self._stats_cache
        from collections import Counter
        year_counter: Counter = Counter()
        modal_counter: Counter = Counter()
        task_counter: Counter = Counter()
        sheet_counter: Counter = Counter()
        for item in self.data:
            yrs = item.get("_years", set())
            if yrs:
                year_counter[min(yrs)] += 1
            sheet = item.get("_sheet", "")
            if sheet:
                sheet_counter[sheet] += 1
            text = item.get("_text", "")
            words = set(re.findall(r"\w+", text))
            for modal, kws in MODAL_KEYWORDS.items():
                if kws & words:
                    modal_counter[modal] += 1
            for task in TASK_LIST:
                if task.lower() in text:
                    task_counter[task] += 1
        self._stats_cache = {
            "year": dict(sorted(year_counter.items())),
            "modal": dict(modal_counter),
            "task": dict(task_counter),
            "sheet": dict(sheet_counter),
        }
        return self._stats_cache

    def _check_modal(self, words, modals):
        if not modals: return True
        return any(MODAL_KEYWORDS[m] & words for m in modals)

    def _check_task(self, text, tasks):
        if not tasks: return True
        return any(t.lower() in text for t in tasks)

    def _check_year(self, item_years, years):
        if not years: return True
        return bool(set(years) & item_years)

    def _check_field(self, item, field, selected):
        if not selected: return True
        val = str(item.get(field, item.get(field.lower(), ""))).strip()
        return val in selected

    def _check_kws(self, text, kws):
        if not kws: return True
        return all(kw.lower() in text for kw in kws)

def load_paper_links(readme_path: str) -> dict[str, str]:
    name_to_link: dict[str, str] = {}
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            text = f.read()
        pattern = r'\[(.*?)\]\((https?://.*?)\)'
        for name, link in re.findall(pattern, text, re.DOTALL | re.IGNORECASE):
            clean_name = name.strip().lower()
            clean_link = link.strip()
            if len(clean_name) >= 2 and any(
                k in clean_link for k in ["arxiv", "sciencedirect", "ieee", "mdpi", "github", "cvf"]
            ):
                name_to_link[clean_name] = clean_link
    except Exception:
        pass
    return name_to_link


def get_paper_link(name_to_link: dict[str, str], name: str) -> str | None:
    target = name.strip().lower()
    for key, link in name_to_link.items():
        if target in key or key in target:
            return link
    return None
