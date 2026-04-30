"""GeoChef MCP Server."""

from pathlib import Path
from mcp.server.fastmcp import FastMCP
from geochef_mcp.core import GeoChef, load_paper_links, get_paper_link as _get_link, TASK_LIST
from geochef_mcp.data import get_data_path
from geochef_mcp.favorites import (
    list_favorites, add_favorite, remove_favorite,
    list_compare, add_compare, remove_compare, clear_compare,
)
from geochef_mcp.nasa import get_nasa_image_of_the_day as _get_nasa_image

mcp = FastMCP(
    "GeoChef",
    instructions=(
        "GeoChef 是遥感视觉语言（RS-VLM）数据集智能检索与分析工具。"
        "可搜索数据集、查询详情、获取论文链接、检测数据泄露风险、对比数据集指标。"
        "搜索结果中会提示可用的后续操作，请根据用户意图主动调用对应工具。"
    ),
)

_chef: GeoChef | None = None
_paper_links: dict[str, str] | None = None


def get_chef() -> GeoChef:
    global _chef
    if _chef is None:
        _chef = GeoChef()
        _chef.load(str(get_data_path()))
    return _chef


def get_paper_links() -> dict[str, str]:
    global _paper_links
    if _paper_links is None:
        candidates = [
            Path(__file__).parent.parent / "dataset_links.md",
            Path("dataset_links.md"),
        ]
        for p in candidates:
            if p.exists():
                _paper_links = load_paper_links(str(p))
                break
        if _paper_links is None:
            _paper_links = {}
    return _paper_links


def _paper_link_for(name: str) -> str | None:
    return _get_link(get_paper_links(), name)


def _hint(actions: list[str]) -> str:
    return "\n\n\U0001f4a1 " + " | ".join(actions)


@mcp.tool()
def search_datasets(
    keywords: str = "",
    modality: str = "",
    task: str = "",
    year: str = "",
    publisher: str = "",
) -> str:
    """
    搜索遥感视觉语言数据集，支持多维度组合筛选。

    Args:
        keywords: 关键词，多个词空格分隔，如 "SAR detection 2023"
        modality: 数据模态，可选：SAR / Optical (RGB) / Multispectral / Hyperspectral / LiDAR
        task: 任务类型，可选：VQA / Caption / VG / Classification / Detection / Segmentation
        year: 发布年份，如 "2023"
        publisher: 发布单位名称
    """
    chef = get_chef()
    results = chef.filter(
        modals=[modality] if modality else [],
        tasks=[task] if task else [],
        years=[year] if year else [],
        publishers=[publisher] if publisher else [],
        methods=[],
        kws=[w.strip() for w in keywords.split() if w.strip()],
    )
    if not results:
        return "未找到符合条件的数据集。"
    lines = [f"共找到 {len(results)} 个数据集：\n"]
    for item in results[:20]:
        name = item.get("Name", item.get("name", "Unknown"))
        parts = [f"**{name}**", f"[{item.get('_sheet', '')}]"]
        for field in ("Year", "Modality", "#Samples"):
            v = str(item.get(field, "")).strip()
            if v and v.lower() not in ("nan", "none"):
                parts.append(v)
        link = _paper_link_for(name)
        if link:
            parts.append(f"[📄 论文]({link})")
        lines.append("- " + " | ".join(parts))
    if len(results) > 20:
        lines.append(f"\n（仅显示前 20 条，共 {len(results)} 条）")
    lines.append(_hint([
        '说"讲解 <数据集名>" 获取论文讲解',
        '说"对比 A 和 B" 对比数据集',
        '说"收藏 <数据集名>" 加入收藏夹',
        '说"将 <数据集名> 加入对比" 加入对比列表',
        '说"<数据集名> 的详细信息" 查看完整字段',
    ]))
    return "\n".join(lines)


@mcp.tool()
def get_dataset_info(name: str) -> str:
    """
    查询指定数据集的详细信息，支持模糊匹配。

    Args:
        name: 数据集名称，如 "OSVQA" 或 "GeoChat"
    """
    chef = get_chef()
    item = chef.get_item_by_name(name)
    if item is None:
        return f"未找到数据集：{name}"
    skip = {"_sheet", "_text", "_years", "_leak_originals"}
    actual_name = item.get("Name", item.get("name", name))
    lines = [f"## {actual_name}", f"**类别**: {item.get('_sheet', '')}\n"]
    for k, v in item.items():
        if k not in skip and str(v).strip().lower() not in ("nan", "none", ""):
            lines.append(f"- **{k}**: {v}")
    link = _paper_link_for(actual_name)
    if link:
        lines.append(f"\n[📄 查看论文原文]({link})")
        lines.append(_hint([
            f'说"讲解 {actual_name}" 获取论文讲解',
            f'说"收藏 {actual_name}" 加入收藏夹',
        ]))
    else:
        lines.append(_hint([
            f'说"搜索 {actual_name} 相关数据集" 查找类似数据集',
            f'说"收藏 {actual_name}" 加入收藏夹',
        ]))
    return "\n".join(lines)


@mcp.tool()
def get_paper_link(name: str) -> str:
    """
    根据数据集名称查找论文链接，并讲解论文内容。
    调用此工具后，请访问返回的论文链接，为用户详细讲解论文。

    Args:
        name: 数据集名称，如 "OSVQA" 或 "GeoChat"，支持模糊匹配
    """
    chef = get_chef()
    item = chef.get_item_by_name(name)
    link = _paper_link_for(name)
    if link is None and item is None:
        return f"未找到数据集 '{name}'，请检查名称是否正确。可以用 search_datasets 工具搜索。"
    lines = []
    if item:
        actual_name = item.get("Name", item.get("name", name))
        lines.append(f"## {actual_name}")
        lines.append(f"**类别**: {item.get('_sheet', '')}\n")
        skip = {"_sheet", "_text", "_years", "_leak_originals"}
        for k, v in item.items():
            if k not in skip and str(v).strip().lower() not in ("nan", "none", ""):
                lines.append(f"- **{k}**: {v}")
        lines.append("")
    if link:
        lines.append(f"[📄 论文原文]({link})")
        lines.append("")
        lines.append("请访问上方论文链接，为用户详细讲解核心贡献、方法创新、数据特点和实验效果。")
        lines.append(_hint([
            '说"和 <其他数据集> 对比" 对比数据集',
            '说"<数据集名> 有数据泄露风险吗" 检测泄露',
        ]))
    else:
        lines.append("⚠️ 未找到该数据集的论文链接，以上为数据集基本信息。")
    return "\n".join(lines)


@mcp.tool()
def query_source_usage(source_name: str) -> str:
    """
    查询某个原始数据集被哪些数据集使用（数据泄露风险分析）。

    Args:
        source_name: 原始数据集名称，如 "DOTA" 或 "UCM"
    """
    chef = get_chef()
    results = chef.query_by_source(source_name)
    if not results:
        return f"未找到使用原始数据集 '{source_name}' 的数据集。"
    lines = [f"使用 **{source_name}** 的数据集共 {len(results)} 个：\n"]
    for entry in results:
        link = _paper_link_for(entry["name"])
        name_part = f"**{entry['name']}**"
        if link:
            name_part += f" [📄]({link})"
        lines.append(f"- {name_part}")
        lines.append(f"  包含原始数据集：{'、'.join(entry['sources'])}")
        if entry.get("remark"):
            lines.append(f"  备注：{entry['remark']}")
    lines.append(_hint([
        '说"批量检测 A,B,C 的泄露风险" 检测多个原始数据集的交集',
        '说"讲解 <数据集名>" 获取论文讲解',
    ]))
    return "\n".join(lines)


@mcp.tool()
def batch_leakage_detection(source_names: str) -> str:
    """
    批量数据泄露检测：找出被多个原始数据集共同使用的高风险数据集。

    Args:
        source_names: 多个原始数据集名称，逗号分隔，如 "DOTA,DIOR,UCM"
    """
    chef = get_chef()
    names = [n.strip() for n in source_names.split(",") if n.strip()]
    if len(names) < 2:
        return "请提供至少 2 个原始数据集名称，用逗号分隔。"
    result = chef.query_by_multiple_sources(names)
    common = result["common_names"]
    per_source = result["per_source"]
    lines = []
    if common:
        lines.append(f"⚠️ **高风险交集**（{len(common)} 个数据集被所有选中原始数据集共同使用）：")
        for n in common:
            link = _paper_link_for(n)
            entry = f"  - **{n}**"
            if link:
                entry += f" [📄]({link})"
            lines.append(entry)
        lines.append("")
    else:
        lines.append("✅ 所选原始数据集之间无共同使用的数据集。\n")
    lines.append("各原始数据集使用情况：")
    for src, entries in per_source.items():
        lines.append(f"\n**{src}**（{len(entries)} 个）：")
        for e in entries[:5]:
            link = _paper_link_for(e["name"])
            entry = f"  - {e['name']}"
            if link:
                entry += f" [📄]({link})"
            lines.append(entry)
        if len(entries) > 5:
            lines.append(f"  ...（共 {len(entries)} 个）")
    lines.append(_hint(['说"讲解 <数据集名>" 获取任意数据集的论文讲解']))
    return "\n".join(lines)


@mcp.tool()
def compare_datasets(names: str) -> str:
    """
    对比多个数据集的关键指标，以 Markdown 表格输出。

    Args:
        names: 数据集名称，逗号分隔，最多 4 个，如 "OSVQA,GeoChat,SkyEye-968K"
    """
    chef = get_chef()
    name_list = [n.strip() for n in names.split(",") if n.strip()][:4]
    if len(name_list) < 2:
        return "请提供至少 2 个数据集名称，用逗号分隔。"
    found = [(n, chef.get_item_by_name(n)) for n in name_list]
    found = [(n, it) for n, it in found if it is not None]
    if len(found) < 2:
        missing = [n for n in name_list if chef.get_item_by_name(n) is None]
        return f"未找到以下数据集：{', '.join(missing)}"
    fields = ["Year", "Publisher", "#Samples", "Modality", "GSD", "Method", "Type", "数据集备注"]
    skip = {"_sheet", "_text", "_years", "_leak_originals"}
    header = "| 字段 | " + " | ".join(n for n, _ in found) + " |"
    sep = "|---" * (len(found) + 1) + "|"
    rows = [header, sep]
    all_keys = fields.copy()
    for _, item in found:
        for k in item.keys():
            if k not in skip and k not in all_keys:
                all_keys.append(k)
    for key in all_keys:
        vals = [str(it.get(key, "")).strip() for _, it in found]
        vals = ["—" if v.lower() in ("nan", "none", "") else v for v in vals]
        if any(v != "—" for v in vals):
            rows.append(f"| {key} | " + " | ".join(vals) + " |")
    links = [_paper_link_for(n) for n, _ in found]
    if any(links):
        link_vals = [f"[📄 论文]({l})" if l else "—" for l in links]
        rows.append("| 论文链接 | " + " | ".join(link_vals) + " |")
    rows.append(_hint([
        '说"讲解 <数据集名>" 深入了解某个数据集',
        '说"<数据集名> 有数据泄露风险吗" 检测泄露',
    ]))
    return "\n".join(rows)


@mcp.tool()
def list_all_sources(limit: int = 50) -> str:
    """
    列出所有可用的原始数据集名称（用于数据泄露检测的输入参考）。

    Args:
        limit: 返回数量上限，默认 50
    """
    chef = get_chef()
    sources = chef.get_all_sources()
    shown = sources[:limit]
    lines = [f"共 {len(sources)} 个原始数据集，显示前 {len(shown)} 个：\n"]
    lines.extend(f"- {s}" for s in shown)
    if len(sources) > limit:
        lines.append(f"\n...（共 {len(sources)} 个，可增大 limit 参数查看更多）")
    lines.append(_hint(['说"查询 <原始数据集名> 的使用情况" 分析泄露风险']))
    return "\n".join(lines)


@mcp.tool()
def favorite_add(name: str) -> str:
    """
    将数据集加入收藏夹。

    Args:
        name: 数据集名称，如 "OSVQA"
    """
    chef = get_chef()
    item = chef.get_item_by_name(name)
    actual_name = item.get("Name", item.get("name", name)).strip() if item else name
    if add_favorite(actual_name):
        lines = [f"⭐ **{actual_name}** 已加入收藏夹。"]
        link = _paper_link_for(actual_name)
        if link:
            lines.append(f"[📄 论文原文]({link})")
        lines.append(_hint([
            '说"查看收藏夹" 查看所有收藏',
            f'说"讲解 {actual_name}" 获取论文讲解',
        ]))
        return "\n".join(lines)
    return f"**{actual_name}** 已在收藏夹中。"


@mcp.tool()
def favorite_remove(name: str) -> str:
    """
    从收藏夹移除数据集。

    Args:
        name: 数据集名称，如 "OSVQA"
    """
    if remove_favorite(name):
        return f"🗑️ **{name}** 已从收藏夹移除。\n" + _hint(['说"查看收藏夹" 查看剩余收藏'])
    return f"**{name}** 不在收藏夹中。"


@mcp.tool()
def favorite_list() -> str:
    """
    查看收藏夹中的所有数据集，并显示基本信息和论文链接。
    """
    chef = get_chef()
    names = list_favorites()
    if not names:
        return "收藏夹为空。\n" + _hint(['说"搜索 <关键词>" 找到感兴趣的数据集后说"收藏 <名称>"'])
    lines = [f"⭐ 收藏夹共 {len(names)} 个数据集：\n"]
    for name in names:
        item = chef.get_item_by_name(name)
        link = _paper_link_for(name)
        parts = [f"**{name}**"]
        if item:
            for field in ("Year", "Modality", "#Samples", "_sheet"):
                v = str(item.get(field, "")).strip()
                if v and v.lower() not in ("nan", "none"):
                    parts.append(v)
        if link:
            parts.append(f"[📄 论文]({link})")
        lines.append("- " + " | ".join(parts))
    lines.append(_hint([
        '说"讲解 <数据集名>" 获取论文讲解',
        '说"对比 A 和 B" 对比收藏的数据集',
        '说"取消收藏 <数据集名>" 移除收藏',
    ]))
    return "\n".join(lines)


@mcp.tool()
def compare_add(name: str) -> str:
    """
    将数据集加入对比列表（最多 4 个）。

    Args:
        name: 数据集名称，如 "OSVQA"
    """
    chef = get_chef()
    item = chef.get_item_by_name(name)
    actual_name = item.get("Name", item.get("name", name)).strip() if item else name
    ok, msg = add_compare(actual_name)
    if not ok:
        current = list_compare()
        return msg + f"\n当前对比项：{', '.join(current) if current else '（空）'}"
    current = list_compare()
    lines = [f"✅ 已将 **{actual_name}** 加入对比，目前对比项有：{', '.join(current)}"]
    if len(current) >= 2:
        lines.append(_hint([
            '说"开始对比" 对比当前所有对比项',
            f'说"将 <数据集名> 加入对比" 继续添加（还可加 {4 - len(current)} 个）',
            '说"清除对比项" 清空对比列表',
        ]))
    else:
        lines.append(_hint(['说"将 <数据集名> 加入对比" 继续添加（至少需要 2 个才能对比）']))
    return "\n".join(lines)


@mcp.tool()
def compare_remove(name: str) -> str:
    """
    从对比列表移除指定数据集。

    Args:
        name: 数据集名称，如 "OSVQA"
    """
    if remove_compare(name):
        current = list_compare()
        status = f"，当前对比项：{', '.join(current)}" if current else "，对比列表已清空"
        return f"🗑️ 已将 **{name}** 从对比列表移除{status}。"
    current = list_compare()
    return f"**{name}** 不在对比列表中。当前对比项：{', '.join(current) if current else '（空）'}"


@mcp.tool()
def compare_clear() -> str:
    """
    清空对比列表中的所有数据集。
    """
    clear_compare()
    return "🗑️ 对比列表已清空。\n" + _hint(['说"将 <数据集名> 加入对比" 重新添加'])


@mcp.tool()
def compare_current() -> str:
    """
    查看当前对比列表，并执行对比（如果有 2 个以上数据集）。
    """
    current = list_compare()
    if not current:
        return "对比列表为空。\n" + _hint(['说"将 <数据集名> 加入对比" 添加数据集'])
    if len(current) == 1:
        return f"当前对比项只有 **{current[0]}**，至少需要 2 个才能对比。\n" + _hint([
            '说"将 <数据集名> 加入对比" 继续添加',
        ])
    return compare_datasets(",".join(current))


@mcp.tool()
def random_dataset() -> str:
    """
    随机推荐一个遥感视觉语言数据集。
    """
    chef = get_chef()
    item = chef.random_one()
    if item is None:
        return "数据集库为空。"
    name = item.get("Name", item.get("name", "Unknown"))
    skip = {"_sheet", "_text", "_years", "_leak_originals"}
    lines = [f"🎲 随机推荐：**{name}**", f"**类别**: {item.get('_sheet', '')}\n"]
    for k, v in item.items():
        if k not in skip and str(v).strip().lower() not in ("nan", "none", ""):
            lines.append(f"- **{k}**: {v}")
    link = _paper_link_for(name)
    if link:
        lines.append(f"\n[📄 论文原文]({link})")
    lines.append(_hint([
        f'说"讲解 {name}" 获取论文讲解',
        f'说"收藏 {name}" 加入收藏夹',
        '说"再来一个" 换一个随机数据集',
    ]))
    return "\n".join(lines)


@mcp.tool()
def dataset_stats() -> str:
    """
    查看数据集统计概览：年份分布、任务类型分布、数据模态分布、类别分布。
    """
    chef = get_chef()
    stats = chef.get_stats()
    lines = ["## 📊 数据集统计概览\n", f"**总数据集数量**: {len(chef.data)}\n"]
    lines.append("### 按发布年份")
    for year, count in sorted(stats["year"].items()):
        bar = "█" * min(count, 20)
        lines.append(f"- {year}: {bar} {count}")
    lines.append("\n### 按任务类型")
    for task, count in sorted(stats["task"].items(), key=lambda x: -x[1]):
        lines.append(f"- {task}: {count}")
    lines.append("\n### 按数据模态")
    for modal, count in sorted(stats["modal"].items(), key=lambda x: -x[1]):
        lines.append(f"- {modal}: {count}")
    lines.append("\n### 按数据集类别")
    for sheet, count in sorted(stats["sheet"].items(), key=lambda x: -x[1]):
        if sheet != "统计期刊数量、国家数量、年份":
            lines.append(f"- {sheet}: {count}")
    lines.append(_hint([
        '说"找 <任务类型> 数据集" 搜索特定类型',
        '说"随机推荐一个数据集" 随机探索',
    ]))
    return "\n".join(lines)


@mcp.tool()
def dataset_relations(name: str) -> str:
    """
    查询数据集的关联关系：找出与该数据集共享原始数据的所有其他数据集。

    Args:
        name: 数据集名称，如 "OSVQA"
    """
    chef = get_chef()
    item = chef.get_item_by_name(name)
    if item is None:
        return f"未找到数据集：{name}"
    actual_name = item.get("Name", item.get("name", name))
    own_sources = chef._name_to_sources.get(actual_name, [])
    if not own_sources:
        return f"**{actual_name}** 未记录原始数据集信息，无法分析关联关系。"
    lines = [
        f"## {actual_name} 的关联关系",
        f"**包含原始数据集**: {', '.join(own_sources)}\n",
        "**共享原始数据的相关数据集**:\n",
    ]
    related: dict[str, list[str]] = {}
    for src in own_sources:
        src_lower = src.lower()
        matched = next((k for k in chef._source_to_names if src_lower in k or k in src_lower), None)
        if matched:
            for related_name in chef._source_to_names[matched]:
                if related_name != actual_name:
                    related.setdefault(related_name, [])
                    if src not in related[related_name]:
                        related[related_name].append(src)
    if not related:
        lines.append("未找到共享原始数据的其他数据集。")
    else:
        for rel_name, shared_srcs in sorted(related.items(), key=lambda x: -len(x[1])):
            link = _paper_link_for(rel_name)
            name_part = f"**{rel_name}**"
            if link:
                name_part += f" [📄]({link})"
            lines.append(f"- {name_part} — 共享: {', '.join(shared_srcs)}")
    lines.append(_hint([
        f'说"批量检测 {actual_name} 的泄露风险" 深入分析',
        f'说"讲解 {actual_name}" 获取论文讲解',
    ]))
    return "\n".join(lines)


@mcp.tool()
def compare_with_analysis(names: str) -> str:
    """
    对比多个数据集并给出 AI 分析总结，指出主要差异和各自适用场景。

    Args:
        names: 数据集名称，逗号分隔，最多 4 个，如 "OSVQA,GeoChat,SkyEye-968K"
    """
    chef = get_chef()
    name_list = [n.strip() for n in names.split(",") if n.strip()][:4]
    if len(name_list) < 2:
        return "请提供至少 2 个数据集名称，用逗号分隔。"
    found = [(n, chef.get_item_by_name(n)) for n in name_list]
    found = [(n, it) for n, it in found if it is not None]
    if len(found) < 2:
        missing = [n for n in name_list if chef.get_item_by_name(n) is None]
        return f"未找到以下数据集：{', '.join(missing)}"
    fields = ["Year", "Publisher", "#Samples", "Modality", "GSD", "Method", "Type", "数据集备注"]
    skip = {"_sheet", "_text", "_years", "_leak_originals"}
    header = "| 字段 | " + " | ".join(n for n, _ in found) + " |"
    sep = "|---" * (len(found) + 1) + "|"
    rows = [header, sep]
    all_keys = fields.copy()
    for _, item in found:
        for k in item.keys():
            if k not in skip and k not in all_keys:
                all_keys.append(k)
    diff_fields = []
    for key in all_keys:
        vals = [str(it.get(key, "")).strip() for _, it in found]
        vals = ["—" if v.lower() in ("nan", "none", "") else v for v in vals]
        if any(v != "—" for v in vals):
            rows.append(f"| {key} | " + " | ".join(vals) + " |")
            if len(set(v for v in vals if v != "—")) > 1:
                diff_fields.append((key, vals))
    links = [_paper_link_for(n) for n, _ in found]
    if any(links):
        link_vals = [f"[📄]({l})" if l else "—" for l in links]
        rows.append("| 论文 | " + " | ".join(link_vals) + " |")
    rows.append("")
    rows.append("### 🔍 差异分析")
    if diff_fields:
        for key, vals in diff_fields[:5]:
            paired = ", ".join(f"{n}: {v}" for (n, _), v in zip(found, vals) if v != "—")
            rows.append(f"- **{key}**: {paired}")
    else:
        rows.append("- 所选数据集在主要字段上高度相似。")
    rows.append("\n请根据以上对比表格，为用户总结这些数据集的核心差异，并说明各自最适合的使用场景。")
    rows.append(_hint([
        '说"讲解 <数据集名>" 深入了解某个数据集',
        '说"收藏 <数据集名>" 保存感兴趣的数据集',
    ]))
    return "\n".join(rows)


@mcp.tool()
def recommend_datasets(requirement: str) -> str:
    """
    根据用户描述的研究需求，推荐最合适的数据集并说明理由。

    Args:
        requirement: 用户的需求描述，如 "我在做 SAR 图像描述任务，需要大规模数据集"
    """
    chef = get_chef()
    kws = [w for w in requirement.lower().split() if len(w) >= 2]
    candidates = chef.filter([], [], [], [], [], kws) if kws else chef.data[:50]
    if not candidates:
        candidates = chef.data[:20]
    top = candidates[:10]
    lines = [
        "## 根据需求推荐",
        f"**需求**: {requirement}\n",
        "以下数据集可能符合你的需求：\n",
    ]
    for item in top:
        name = item.get("Name", item.get("name", "Unknown"))
        parts = [f"**{name}**"]
        for field in ("Year", "Modality", "#Samples", "_sheet"):
            v = str(item.get(field, "")).strip()
            if v and v.lower() not in ("nan", "none"):
                parts.append(v)
        link = _paper_link_for(name)
        if link:
            parts.append(f"[📄]({link})")
        lines.append("- " + " | ".join(parts))
        remark = str(item.get("数据集备注", "")).strip()
        if remark and remark.lower() not in ("nan", "none"):
            lines.append(f"  > {remark}")
    lines.append("\n请根据以上候选数据集和用户需求，分析每个数据集的适用性，给出有针对性的推荐理由。")
    lines.append(_hint([
        '说"讲解 <数据集名>" 深入了解某个数据集',
        '说"对比 A 和 B" 对比候选数据集',
        '说"收藏 <数据集名>" 保存感兴趣的',
    ]))
    return "\n".join(lines)


@mcp.tool()
def dataset_geo_stats() -> str:
    """
    查看数据集论文的国家/地区来源分布（地理统计）。
    当用户问"哪些国家发表了最多遥感数据集论文"、"地理分布"、"国家分布"等时调用。
    """
    chef = get_chef()
    nation_dict = chef.get_geo_stats()
    if not nation_dict:
        return "⚠️ 暂无地理分布数据。"

    total = sum(nation_dict.values())
    lines = [
        "## 🗺️ 论文来源国家 / 地区分布\n",
        f"**覆盖国家/地区数**: {len(nation_dict)}　**论文总计**: {total}\n",
        "| 排名 | 国家 / 地区 | 论文数 | 占比 |",
        "|---:|---|---:|---:|",
    ]
    medals = ["🥇", "🥈", "🥉"]
    for i, (nation, count) in enumerate(nation_dict.items()):
        rank = medals[i] if i < 3 else f"{i + 1}"
        pct = f"{count / total * 100:.1f}%"
        bar = "█" * min(count, 20)
        lines.append(f"| {rank} | {nation} | {count} {bar} | {pct} |")

    lines.append(_hint([
        '说"数据集统计" 查看年份/任务/模态分布',
        '说"增长趋势" 查看各年度数据集增长情况',
    ]))
    return "\n".join(lines)


@mcp.tool()
def dataset_trend_stats() -> str:
    """
    查看数据集发布的年度增长趋势，包括各任务类型的逐年数量和同比增速。
    当用户问"增长趋势"、"每年发布多少数据集"、"哪年增长最快"等时调用。
    """
    chef = get_chef()
    trend = chef.get_trend_stats()
    by_task: dict = trend.get("by_task", {})
    total: dict = trend.get("total", {})

    if not total:
        return "⚠️ 暂无趋势数据。"

    lines = ["## 📈 数据集年度增长趋势\n"]

    # ── 总量逐年 ──
    lines.append("### 总量（按年份）\n")
    lines.append("| 年份 | 数量 | 趋势 |")
    lines.append("|---:|---:|---|")
    sorted_years = sorted(total.keys())
    for i, yr in enumerate(sorted_years):
        cnt = total[yr]
        bar = "█" * min(cnt, 30)
        if i > 0:
            prev = total[sorted_years[i - 1]]
            delta = cnt - prev
            arrow = f"▲ +{delta}" if delta > 0 else (f"▼ {delta}" if delta < 0 else "─ 0")
        else:
            arrow = "—"
        lines.append(f"| {yr} | {cnt} | {bar} {arrow} |")

    # ── 同比增速 ──
    lines.append("\n### 同比增速\n")
    lines.append("| 年份 | 增速 |")
    lines.append("|---:|---|")
    for i in range(1, len(sorted_years)):
        prev = total[sorted_years[i - 1]]
        curr = total[sorted_years[i]]
        if prev > 0:
            rate = (curr - prev) / prev * 100
            sign = "▲" if rate >= 0 else "▼"
            lines.append(f"| {sorted_years[i]} | {sign} {rate:+.1f}% |")

    # ── 各任务类型逐年 ──
    if by_task:
        lines.append("\n### 各任务类型逐年数量\n")
        all_years = sorted({yr for yd in by_task.values() for yr in yd})
        header = "| 任务 | " + " | ".join(all_years) + " |"
        sep = "|---" + "|---" * len(all_years) + "|"
        lines.append(header)
        lines.append(sep)
        for task in TASK_LIST:
            if task not in by_task:
                continue
            year_counts = by_task[task]
            vals = [str(year_counts.get(yr, 0)) for yr in all_years]
            lines.append(f"| {task} | " + " | ".join(vals) + " |")

    lines.append(_hint([
        '说"数据集统计" 查看模态/类别分布',
        '说"地理分布" 查看国家来源分布',
    ]))
    return "\n".join(lines)


@mcp.tool()
def dataset_venue_stats() -> str:
    """
    查看遥感数据集论文的期刊/会议发表分布。
    当用户问"哪些期刊/会议发表了最多遥感数据集"、"顶会分布"、"发表渠道"等时调用。
    """
    chef = get_chef()
    venue_dict = chef.get_venue_stats()
    if not venue_dict:
        return "⚠️ 暂无期刊/会议数据。"

    total = sum(venue_dict.values())
    lines = [
        "## 📰 期刊 / 会议发表分布\n",
        f"**覆盖期刊/会议数**: {len(venue_dict)}　**论文总计**: {total}\n",
        "| 排名 | 期刊 / 会议 | 论文数 | 占比 |",
        "|---:|---|---:|---:|",
    ]
    medals = ["🥇", "🥈", "🥉"]
    for i, (venue, count) in enumerate(venue_dict.items()):
        rank = medals[i] if i < 3 else f"{i + 1}"
        pct = f"{count / total * 100:.1f}%"
        bar = "█" * min(count, 20)
        lines.append(f"| {rank} | {venue} | {count} {bar} | {pct} |")

    lines.append(_hint([
        '说"地理分布" 查看国家来源分布',
        '说"增长趋势" 查看年度增长情况',
        '说"数据集统计" 查看任务/模态分布',
    ]))
    return "\n".join(lines)


@mcp.tool()
def search_by_scale(
    min_samples: int = 0,
    max_samples: int = 0,
    task: str = "",
    modality: str = "",
) -> str:
    """
    按样本量范围筛选数据集，可组合任务类型和模态过滤。
    当用户说"找超过10万样本的大规模数据集"、"找小规模VQA数据集"等时调用。

    Args:
        min_samples: 最小样本数（0 表示不限下限）
        max_samples: 最大样本数（0 表示不限上限）
        task: 任务类型，可选：VQA / Caption / VG / Classification / Detection / Segmentation
        modality: 数据模态，可选：SAR / Optical (RGB) / Multispectral / Hyperspectral / LiDAR
    """
    chef = get_chef()
    min_s = min_samples if min_samples > 0 else None
    max_s = max_samples if max_samples > 0 else None

    if min_s is None and max_s is None:
        return "请至少提供 min_samples 或 max_samples 中的一个。"

    results = chef.search_by_scale(min_s, max_s)

    # 可选的任务/模态二次过滤：用名称集合做交集，避免对象 identity 问题
    if task or modality:
        filtered = chef.filter(
            modals=[modality] if modality else [],
            tasks=[task] if task else [],
            years=[], publishers=[], methods=[], kws=[],
        )
        filtered_names = {
            str(it.get("Name", it.get("name", ""))).strip() for it in filtered
        }
        results = [
            r for r in results
            if str(r.get("Name", r.get("name", ""))).strip() in filtered_names
        ]

    if not results:
        range_desc = _scale_range_desc(min_s, max_s)
        return f"未找到样本量 {range_desc} 的数据集。"

    range_desc = _scale_range_desc(min_s, max_s)
    lines = [f"样本量 {range_desc} 的数据集共 **{len(results)}** 个：\n"]
    for item in results[:20]:
        name = item.get("Name", item.get("name", "Unknown"))
        samples = str(item.get("#Samples", "")).strip()
        parts = [f"**{name}**", f"[{item.get('_sheet', '')}]"]
        for field in ("Year", "Modality"):
            v = str(item.get(field, "")).strip()
            if v and v.lower() not in ("nan", "none"):
                parts.append(v)
        if samples and samples.lower() not in ("nan", "none"):
            parts.append(f"样本数: {samples}")
        link = _paper_link_for(name)
        if link:
            parts.append(f"[📄 论文]({link})")
        lines.append("- " + " | ".join(parts))
    if len(results) > 20:
        lines.append(f"\n（仅显示前 20 条，共 {len(results)} 条）")
    lines.append(_hint([
        '说"<数据集名> 的详细信息" 查看完整字段',
        '说"对比 A 和 B" 对比数据集',
        '说"收藏 <数据集名>" 加入收藏夹',
    ]))
    return "\n".join(lines)


def _scale_range_desc(min_s: int | None, max_s: int | None) -> str:
    def fmt(n: int) -> str:
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.0f}K"
        return str(n)
    if min_s and max_s:
        return f"{fmt(min_s)} ~ {fmt(max_s)}"
    if min_s:
        return f"≥ {fmt(min_s)}"
    if max_s:
        return f"≤ {fmt(max_s)}"
    return "不限"


@mcp.tool()
def find_similar_datasets(name: str, top_n: int = 8) -> str:
    """
    找出与指定数据集最相似的其他数据集（基于任务类型、模态、年份等结构化字段打分）。
    当用户说"找和 GeoChat 类似的数据集"、"有没有和 OSVQA 相似的"等时调用。

    Args:
        name: 参考数据集名称，如 "GeoChat"
        top_n: 返回数量，默认 8
    """
    chef = get_chef()
    target = chef.get_item_by_name(name)
    if target is None:
        return f"未找到数据集：{name}，请检查名称是否正确。"

    actual_name = str(target.get("Name", target.get("name", name))).strip()
    similar = chef.find_similar(actual_name, top_n=top_n)

    if not similar:
        return f"未找到与 **{actual_name}** 相似的数据集。"

    lines = [
        f"## 与 {actual_name} 相似的数据集\n",
        f"**参考数据集**: {actual_name} | {target.get('_sheet', '')} | "
        f"{target.get('Modality', '')} | {target.get('#Samples', '')} 样本\n",
        "| 数据集 | 类别 | 模态 | 样本数 | 相似度 | 论文 |",
        "|---|---|---|---|---:|---|",
    ]
    max_score = similar[0][1] if similar else 1
    for item, score in similar:
        n = str(item.get("Name", item.get("name", ""))).strip()
        sheet = item.get("_sheet", "")
        modal = str(item.get("Modality", "")).strip() or "—"
        samples = str(item.get("#Samples", "")).strip() or "—"
        if samples.lower() in ("nan", "none"):
            samples = "—"
        stars = "★" * score + "☆" * (max_score - score)
        link = _paper_link_for(n)
        link_cell = f"[📄]({link})" if link else "—"
        lines.append(f"| {n} | {sheet} | {modal} | {samples} | {stars} | {link_cell} |")

    lines.append(_hint([
        f'说"对比 {actual_name} 和 <相似数据集名>" 深入对比',
        f'说"收藏 <数据集名>" 保存感兴趣的',
        f'说"讲解 <数据集名>" 获取论文讲解',
    ]))
    return "\n".join(lines)


@mcp.tool()
def publisher_analysis(publisher: str) -> str:
    """
    分析指定发布单位（期刊/会议/机构）发表的所有数据集，统计其任务类型和模态分布。
    当用户问"TGRS 发表了哪些数据集"、"arXiv 上有哪些遥感数据集"等时调用。

    Args:
        publisher: 发布单位名称，如 "TGRS"、"arXiv"、"ISPRS"
    """
    chef = get_chef()
    results = chef.get_publisher_datasets(publisher)
    if not results:
        return f"未找到发布单位 '{publisher}' 的数据集，请检查名称是否正确。"

    actual_pub = str(results[0].get("Publisher", publisher)).strip()

    # 统计任务和模态分布
    from collections import Counter
    task_counter: Counter = Counter()
    modal_counter: Counter = Counter()
    for item in results:
        text = item.get("_text", "")
        for task in TASK_LIST:
            if task.lower() in text:
                task_counter[task] += 1
        modal = str(item.get("Modality", "")).strip()
        if modal and modal.lower() not in ("nan", "none"):
            modal_counter[modal] += 1

    lines = [
        f"## 📚 {actual_pub} 发表的数据集\n",
        f"**共 {len(results)} 个数据集**\n",
    ]

    if task_counter:
        lines.append("**任务类型分布**: " + "、".join(
            f"{t}({c})" for t, c in task_counter.most_common()
        ))
    if modal_counter:
        lines.append("**模态分布**: " + "、".join(
            f"{m}({c})" for m, c in modal_counter.most_common(5)
        ))
    lines.append("")

    for item in results:
        name = str(item.get("Name", item.get("name", ""))).strip()
        parts = [f"**{name}**", f"[{item.get('_sheet', '')}]"]
        for field in ("Year", "Modality", "#Samples"):
            v = str(item.get(field, "")).strip()
            if v and v.lower() not in ("nan", "none"):
                parts.append(v)
        link = _paper_link_for(name)
        if link:
            parts.append(f"[📄]({link})")
        lines.append("- " + " | ".join(parts))

    lines.append(_hint([
        '说"对比 A 和 B" 对比该发布单位的数据集',
        '说"讲解 <数据集名>" 获取论文讲解',
    ]))
    return "\n".join(lines)


@mcp.tool()
def dataset_timeline(task: str = "", modality: str = "") -> str:
    """
    展示数据集的发展时间线，按年份排列，可按任务类型或模态过滤。
    当用户问"VQA 数据集是怎么发展的"、"SAR 数据集的历史"等时调用。

    Args:
        task: 任务类型过滤，可选：VQA / Caption / VG / Classification / Detection / Segmentation
        modality: 模态过滤，可选：SAR / Optical (RGB) / Multispectral / Hyperspectral / LiDAR
    """
    chef = get_chef()
    entries = chef.get_timeline(task=task, modality=modality)
    if not entries:
        return "未找到符合条件的数据集。"

    # 按年份分组
    from collections import defaultdict
    by_year: dict[str, list] = defaultdict(list)
    for e in entries:
        by_year[str(e["year"])].append(e)

    title_parts = []
    if task:
        title_parts.append(task)
    if modality:
        title_parts.append(modality)
    title_suffix = " · ".join(title_parts) if title_parts else "全部"

    lines = [f"## 📅 数据集发展时间线（{title_suffix}）\n", f"共 **{len(entries)}** 个数据集\n"]

    for year in sorted(by_year.keys()):
        year_items = by_year[year]
        lines.append(f"### {year} 年（{len(year_items)} 个）")
        for e in year_items:
            name = e["name"]
            parts = [f"**{name}**", f"[{e['sheet']}]"]
            if e["modality"] and e["modality"].lower() not in ("nan", "none"):
                parts.append(e["modality"])
            if e["samples"] and e["samples"].lower() not in ("nan", "none"):
                parts.append(f"{e['samples']} 样本")
            link = _paper_link_for(name)
            if link:
                parts.append(f"[📄]({link})")
            lines.append("- " + " | ".join(parts))
        lines.append("")

    lines.append(_hint([
        '说"讲解 <数据集名>" 获取论文讲解',
        '说"增长趋势" 查看年度增长统计',
    ]))
    return "\n".join(lines)


@mcp.tool()
def export_dataset_summary(names: str, format: str = "markdown") -> str:
    """
    将指定数据集导出为 BibTeX 引用或 Markdown 表格，方便粘贴到论文或笔记。
    当用户说"导出这些数据集的引用"、"生成 BibTeX"、"生成 Markdown 表格"等时调用。

    Args:
        names: 数据集名称，逗号分隔，如 "OSVQA,GeoChat,SkyEye-968K"
        format: 导出格式，"bibtex" 或 "markdown"（默认）
    """
    chef = get_chef()
    name_list = [n.strip() for n in names.split(",") if n.strip()]
    if not name_list:
        return "请提供至少一个数据集名称，用逗号分隔。"

    found = []
    missing = []
    for n in name_list:
        item = chef.get_item_by_name(n)
        if item:
            found.append(item)
        else:
            missing.append(n)

    if not found:
        return f"未找到任何数据集：{', '.join(missing)}"

    fmt = format.strip().lower()

    if fmt == "bibtex":
        lines = []
        if missing:
            lines.append(f"⚠️ 未找到：{', '.join(missing)}\n")
        for item in found:
            name = str(item.get("Name", item.get("name", "Unknown"))).strip()
            year = str(item.get("Year", "")).strip()
            publisher = str(item.get("Publisher", "")).strip()
            link = _paper_link_for(name)
            # 生成 cite key：名称小写去空格
            cite_key = name.lower().replace(" ", "_").replace("-", "_")
            if year and year.lower() not in ("nan", "none"):
                cite_key += f"_{year}"
            entry = [f"@article{{{cite_key},"]
            entry.append(f"  title     = {{{name}}},")
            if year and year.lower() not in ("nan", "none"):
                entry.append(f"  year      = {{{year}}},")
            if publisher and publisher.lower() not in ("nan", "none"):
                entry.append(f"  journal   = {{{publisher}}},")
            if link:
                entry.append(f"  url       = {{{link}}},")
            entry.append("}")
            lines.append("\n".join(entry))
        return "\n\n".join(lines)

    else:  # markdown
        fields = ["Name", "Year", "Publisher", "#Samples", "Modality", "_sheet"]
        display = ["数据集", "年份", "发布单位", "样本数", "模态", "类别"]
        header = "| " + " | ".join(display) + " | 论文 |"
        sep = "|---" * (len(display) + 1) + "|"
        rows = [header, sep]
        for item in found:
            vals = []
            for f in fields:
                v = str(item.get(f, "")).strip()
                vals.append("—" if v.lower() in ("nan", "none", "") else v)
            name = str(item.get("Name", item.get("name", ""))).strip()
            link = _paper_link_for(name)
            link_cell = f"[📄]({link})" if link else "—"
            rows.append("| " + " | ".join(vals) + f" | {link_cell} |")
        result = "\n".join(rows)
        if missing:
            result = f"⚠️ 未找到：{', '.join(missing)}\n\n" + result
        return result


@mcp.tool()
def dataset_quiz() -> str:
    """
    随机出一道数据集猜谜题：给出部分信息，让用户猜数据集名称。
    当用户说"出一道题"、"考考我"、"猜猜看"等时调用。
    """
    import random as _random
    chef = get_chef()
    # 只从有足够字段的数据集里出题
    candidates = [
        item for item in chef.data
        if str(item.get("Modality", "")).strip().lower() not in ("nan", "none", "")
        and str(item.get("#Samples", "")).strip().lower() not in ("nan", "none", "")
        and item.get("_years")
    ]
    if not candidates:
        return "暂无足够数据出题。"

    item = _random.choice(candidates)
    name = str(item.get("Name", item.get("name", ""))).strip()
    year = min(item.get("_years", {"?"}))
    modal = str(item.get("Modality", "")).strip()
    samples = str(item.get("#Samples", "")).strip()
    sheet = item.get("_sheet", "")
    publisher = str(item.get("Publisher", "")).strip()
    remark = str(item.get("数据集备注", "")).strip()

    clues = [
        f"- 📅 发布年份：**{year}**",
        f"- 🛰️ 数据模态：**{modal}**",
        f"- 📦 样本数量：**{samples}**",
        f"- 🗂️ 任务类别：**{sheet}**",
    ]
    if publisher and publisher.lower() not in ("nan", "none"):
        clues.append(f"- 📰 发表于：**{publisher}**")
    if remark and remark.lower() not in ("nan", "none"):
        clues.append(f"- 💬 备注：{remark}")

    lines = [
        "## 🎯 数据集猜谜\n",
        "根据以下线索，猜猜这是哪个遥感视觉语言数据集？\n",
    ] + clues + [
        "",
        f"<details><summary>🔍 点击查看答案</summary>\n\n**答案：{name}**",
    ]
    link = _paper_link_for(name)
    if link:
        lines.append(f"\n[📄 论文原文]({link})")
    lines.append("\n</details>")
    lines.append(_hint([
        '说"再来一题" 换一道题',
        f'说"讲解 {name}" 深入了解这个数据集',
        '说"随机推荐一个数据集" 随机探索',
    ]))
    return "\n".join(lines)


@mcp.tool()
def nasa_image_of_the_day(recent_count: int = 5) -> str:
    """
    获取 NASA Earth Observatory 每日一图（卫星遥感图像）。
    当用户说"每日一图"、"NASA每日一图"、"今天的NASA图片"等时调用此工具。

    Args:
        recent_count: 额外展示的近期图片数量（0~9），默认 5
    """
    return _get_nasa_image(recent_count)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
