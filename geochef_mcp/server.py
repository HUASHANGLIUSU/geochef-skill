"""GeoChef MCP Server."""

from pathlib import Path
from mcp.server.fastmcp import FastMCP
from geochef_mcp.core import GeoChef, load_paper_links, get_paper_link as _get_link
from geochef_mcp.data import get_data_path
from geochef_mcp.favorites import (
    list_favorites, add_favorite, remove_favorite,
    list_compare, add_compare, remove_compare, clear_compare,
)

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
    skip = {"_sheet", "_text", "_years"}
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
    skip = {"_sheet", "_text", "_years"}
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


def main():
    mcp.run()


if __name__ == "__main__":
    main()
