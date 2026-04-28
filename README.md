# GeoChef MCP Skill

> An intelligent retrieval and analysis MCP Skill for Remote Sensing Vision-Language (RS-VLM) datasets.
> Talk to your AI assistant in natural language — search datasets, detect data leakage, compare metrics, and get paper explanations.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Paper](https://img.shields.io/badge/TechRxiv-Paper-yellow)](http://dx.doi.org/10.36227/techrxiv.176978652.29736845/v1)
[![MCP](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)

---

## What is GeoChef?

GeoChef is an MCP (Model Context Protocol) Skill that gives AI assistants like Claude, Cursor, and Kiro direct access to a curated index of RS-VLM datasets. Instead of manually searching papers and spreadsheets, you just ask your AI:

```
Find SAR object detection datasets published after 2022
Tell me about the GeoChat dataset
Compare OSVQA and SkyEye-968K
Which datasets use DOTA as a source? Any leakage risk?
```

The AI calls GeoChef's tools behind the scenes and answers in natural language.

---

## Installation

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/). No API key needed.

Add to your MCP config file:

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

| Client | Config file location |
|--------|---------------------|
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cursor | Settings → MCP |
| Kiro | `.kiro/settings/mcp.json` |

Dataset index is automatically downloaded on first run and cached locally — no manual setup needed.

---

## Capabilities

| Feature | Example |
|---------|---------|
| **Dataset Search** | "Find VQA datasets with SAR modality" |
| **Paper Explanation** | "Tell me about the OSVQA dataset" |
| **Dataset Comparison** | "Compare GeoChat and SkyEye-968K" |
| **Compare List** | "Add OSVQA to compare list, then add GeoChat, now compare" |
| **Data Leakage Detection** | "Which datasets share source data with GeoChat-Instruct?" |
| **Batch Leakage Detection** | "Detect leakage risk across DOTA, DIOR, UCM" |
| **Recommendations** | "I'm building a SAR captioning model, what datasets should I use?" |
| **Statistics** | "Show me the dataset distribution by year and task type" |
| **Relationship Graph** | "What datasets are related to OSVQA?" |
| **Favorites** | "Save OSVQA to favorites" / "Show my favorites" |
| **Random Discovery** | "Recommend a random dataset" |

---

## Tools

| Tool | Description |
|------|-------------|
| `search_datasets` | Multi-dimensional search by keywords, modality, task, year, publisher |
| `get_dataset_info` | Full details of a dataset |
| `get_paper_link` | Find paper link and trigger AI explanation |
| `compare_datasets` | Side-by-side comparison table |
| `compare_with_analysis` | Comparison + AI-generated analysis |
| `compare_add / remove / clear / current` | Manage a persistent compare list |
| `query_source_usage` | Find datasets using a given source dataset |
| `batch_leakage_detection` | Detect high-risk intersections across multiple sources |
| `list_all_sources` | List all available source dataset names |
| `recommend_datasets` | Recommend datasets based on research requirements |
| `dataset_stats` | Statistics overview (year / task / modality distribution) |
| `dataset_relations` | Find datasets sharing source data |
| `random_dataset` | Random dataset recommendation |
| `favorite_add / remove / list` | Manage a persistent favorites list |

---

## Data

- Dataset index: [`rs_vlm_datasets.xlsx`](rs_vlm_datasets.xlsx) — structured metadata for 146+ RS-VLM datasets
- Paper links: [`dataset_links.md`](dataset_links.md) — maps dataset names to paper URLs
- Source: [Awesome-RS-VL-Data](https://github.com/VisionXLab/Awesome-RS-VL-Data), continuously updated

---

## Citation

```bibtex
@article{geochef2025,
  title={GeoChef: An Intelligent Retrieval and Analysis Tool for RS-VLM Datasets},
  author={DREAMS@ECNU and VisionXLab@SJTU},
  journal={TechRxiv},
  year={2025},
  doi={10.36227/techrxiv.176978652.29736845}
}
```
