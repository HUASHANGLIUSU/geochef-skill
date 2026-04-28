# GeoChef MCP Skill

**EN** | 遥感视觉语言数据集智能检索与分析工具  
**中文** | Intelligent retrieval and analysis tool for Remote Sensing Vision-Language (RS-VLM) datasets

---

## 安装 / Installation

在 MCP 配置文件中添加以下内容 / Add to your MCP config:

```json
{
  "mcpServers": {
    "geochef": {
      "command": "uvx",
      "args": ["geochef-mcp"]
    }
  }
}
```

**配置文件路径 / Config file location:**

| 客户端 / Client | 路径 / Path |
|---|---|
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cursor | Settings → MCP |
| Kiro | `.kiro/settings/mcp.json` |
| Windsurf / Zed / Cline / Continue | 参考各客户端 MCP 文档 / See client docs |

> 需要安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) / Requires [uv](https://docs.astral.sh/uv/getting-started/installation/)  
> 首次运行自动下载数据，无需 API Key / Dataset auto-downloaded on first run, no API key required

---

## 功能示例 / Usage Examples

```
# 中文
找 2023 年发布的 SAR 目标检测数据集
帮我讲讲 GeoChat 这个数据集
对比 OSVQA 和 SkyEye-968K
把 OSVQA 加入对比，再把 GeoChat 也加进去，开始对比
查一下哪些数据集用到了 DOTA，有数据泄露风险吗
收藏 OSVQA / 查看收藏夹

# English
Find SAR object detection datasets published after 2022
Tell me about the GeoChat dataset
Compare OSVQA and SkyEye-968K
Add OSVQA to compare list, then add GeoChat, now compare them
Which datasets use DOTA as a source? Any leakage risk?
Save OSVQA to favorites / Show my favorites
```

---

## 工具列表 / Tools

| 工具 / Tool | 说明 / Description |
|---|---|
| `search_datasets` | 多维度搜索数据集 / Search by keywords, modality, task, year, publisher |
| `get_dataset_info` | 查询数据集完整信息 / Get full details of a dataset |
| `get_paper_link` | 获取论文链接并讲解 / Find paper link and explain |
| `compare_datasets` | 直接对比指定数据集 / Compare datasets directly |
| `compare_add` | 加入对比列表 / Add to compare list |
| `compare_remove` | 从对比列表移除 / Remove from compare list |
| `compare_clear` | 清空对比列表 / Clear compare list |
| `compare_current` | 查看并执行当前对比 / View and run current compare list |
| `query_source_usage` | 查询原始数据集使用情况 / Find datasets using a source |
| `batch_leakage_detection` | 批量泄露检测 / Batch leakage detection |
| `list_all_sources` | 列出所有原始数据集 / List all source datasets |
| `favorite_add` | 收藏数据集 / Add to favorites |
| `favorite_remove` | 取消收藏 / Remove from favorites |
| `favorite_list` | 查看收藏夹 / View favorites |
| `random_dataset` | 随机推荐数据集 / Random recommendation |
| `dataset_stats` | 统计概览（年份/任务/模态分布）/ Statistics overview |
| `dataset_relations` | 数据集关联关系图谱 / Dataset relationship graph |
| `compare_with_analysis` | 对比数据集并给出 AI 分析 / Compare with AI analysis |
| `recommend_datasets` | 根据需求推荐数据集 / Recommend by requirements |

---

## 数据来源 / Data Source

[Awesome-RS-VL-Data](https://github.com/VisionXLab/Awesome-RS-VL-Data) — 持续更新中 / Continuously updated
