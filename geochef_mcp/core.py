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
                    item["_years"] = set(re.findall(r'\b(199\d|20\d{2})\b', item["_text"]))
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
        self._geo_stats_cache: dict | None = None
        self._trend_stats_cache: dict | None = None
        self._data_path: str = path

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

    def get_geo_stats(self) -> dict:
        """返回国家/地区论文数量分布，格式：{nation: count, ...}，按数量降序。"""
        if self._geo_stats_cache is not None:
            return self._geo_stats_cache
        try:
            df = pd.read_excel(self._data_path, sheet_name="统计期刊数量、国家数量、年份")
            nation_df = df[["nation", "nation_count"]].dropna()
            nation_df = nation_df.copy()
            nation_df["nation"] = nation_df["nation"].replace({"Australian": "Australia"})
            nation_dict = {
                str(row["nation"]).strip(): int(row["nation_count"])
                for _, row in nation_df.iterrows()
                if str(row["nation"]).strip() not in ("", "nan")
            }
            self._geo_stats_cache = dict(
                sorted(nation_dict.items(), key=lambda x: x[1], reverse=True)
            )
        except Exception as e:
            print(f"[GeoChef] 地理统计加载失败: {e}")
            self._geo_stats_cache = {}
        return self._geo_stats_cache

    def get_trend_stats(self) -> dict:
        """
        按任务类型 × 年份统计数据集数量。
        返回 {task: {year: count}, ...} 及总量 {year: count}。
        """
        if self._trend_stats_cache is not None:
            return self._trend_stats_cache
        from collections import defaultdict
        trend: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        total: dict[str, int] = defaultdict(int)
        for item in self.data:
            yrs = item.get("_years", set())
            if not yrs:
                continue
            year = min(yrs)
            text = item.get("_text", "")
            total[year] += 1
            for task in TASK_LIST:
                if task.lower() in text:
                    trend[task][year] += 1
        self._trend_stats_cache = {
            "by_task": {task: dict(sorted(y.items())) for task, y in trend.items()},
            "total": dict(sorted(total.items())),
        }
        return self._trend_stats_cache

    def get_venue_stats(self) -> dict:
        """返回期刊/会议论文数量分布，格式：{venue: count}，按数量降序。"""
        try:
            df = pd.read_excel(self._data_path, sheet_name="统计期刊数量、国家数量、年份")
            venue_df = df[["article", "article_count"]].dropna()
            venue_dict = {
                str(row["article"]).strip(): int(row["article_count"])
                for _, row in venue_df.iterrows()
                if str(row["article"]).strip() not in ("", "nan")
            }
            return dict(sorted(venue_dict.items(), key=lambda x: x[1], reverse=True))
        except Exception as e:
            print(f"[GeoChef] 期刊统计加载失败: {e}")
            return {}

    def search_by_scale(self, min_samples: int | None, max_samples: int | None) -> list[dict]:
        """按样本量范围筛选数据集。"""
        import re as _re
        results = []
        for item in self.data:
            raw = str(item.get("#Samples", "")).strip()
            if not raw or raw.lower() in ("nan", "none", ""):
                continue
            # 去掉逗号/空格后提取第一个数字，支持 K/M 后缀
            raw_clean = raw.replace(",", "").replace("，", "").replace(" ", "")
            m = _re.search(r"[\d.]+", raw_clean)
            if not m:
                continue
            try:
                val = float(m.group())
                suffix = raw_clean[m.end():m.end() + 1].upper()
                if suffix == "K":
                    val *= 1_000
                elif suffix == "M":
                    val *= 1_000_000
            except ValueError:
                continue
            if min_samples is not None and val < min_samples:
                continue
            if max_samples is not None and val > max_samples:
                continue
            results.append(item)
        return results

    def find_similar(self, name: str, top_n: int = 8) -> list[tuple[dict, int]]:
        """
        基于结构化字段相似度打分，找出与指定数据集最相似的其他数据集。
        返回 [(item, score), ...] 降序。
        """
        target = self.get_item_by_name(name)
        if target is None:
            return []
        actual_name = str(target.get("Name", target.get("name", name))).strip()

        t_sheet = target.get("_sheet", "")
        t_modal = str(target.get("Modality", "")).strip().lower()
        t_text = target.get("_text", "")
        t_years = target.get("_years", set())
        t_year = int(min(t_years)) if t_years else None
        t_tasks = {task for task in TASK_LIST if task.lower() in t_text}

        scored: list[tuple[dict, int]] = []
        for item in self.data:
            cname = str(item.get("Name", item.get("name", ""))).strip()
            if cname == actual_name:
                continue
            score = 0
            # 同 sheet（任务大类）+3
            if item.get("_sheet", "") == t_sheet:
                score += 3
            # 模态匹配 +2
            c_modal = str(item.get("Modality", "")).strip().lower()
            if t_modal and c_modal and (t_modal in c_modal or c_modal in t_modal):
                score += 2
            # 任务类型重叠 +1/个
            c_text = item.get("_text", "")
            c_tasks = {task for task in TASK_LIST if task.lower() in c_text}
            score += len(t_tasks & c_tasks)
            # 年份相近（±2年）+1
            c_years = item.get("_years", set())
            if t_year and c_years:
                c_year = int(min(c_years))
                if abs(c_year - t_year) <= 2:
                    score += 1
            if score > 0:
                scored.append((item, score))

        scored.sort(key=lambda x: -x[1])
        return scored[:top_n]

    def get_publisher_datasets(self, publisher: str) -> list[dict]:
        """返回指定发布单位的所有数据集。"""
        pub_lower = publisher.strip().lower()
        results = []
        for item in self.data:
            p = str(item.get("Publisher", item.get("publisher", ""))).strip().lower()
            if pub_lower in p or p in pub_lower:
                results.append(item)
        return results

    def get_timeline(self, task: str = "", modality: str = "") -> list[dict]:
        """
        返回按年份排序的数据集列表，可按任务/模态过滤。
        每条包含 year, name, sheet, modality, samples, link_hint。
        """
        filtered = self.filter(
            modals=[modality] if modality else [],
            tasks=[task] if task else [],
            years=[], publishers=[], methods=[], kws=[],
        )
        result = []
        for item in filtered:
            yrs = item.get("_years", set())
            year = min(yrs) if yrs else "未知"
            result.append({
                "year": year,
                "name": str(item.get("Name", item.get("name", ""))).strip(),
                "sheet": item.get("_sheet", ""),
                "modality": str(item.get("Modality", "")).strip(),
                "samples": str(item.get("#Samples", "")).strip(),
                "item": item,
            })
        result.sort(key=lambda x: (str(x["year"]), x["name"]))
        return result

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
