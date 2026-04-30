# GeoChef MCP Skill

> An intelligent retrieval and analysis MCP Skill for Remote Sensing Vision-Language (RS-VLM) datasets.
> Talk to your AI assistant in natural language — search datasets, detect data leakage, compare metrics, explore trends, and get paper explanations.

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
Find datasets similar to GeoChat-Instruct
Show me the NASA image of the day
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

| Feature | Example prompt |
|---------|----------------|
| **Dataset Search** | "Find VQA datasets with SAR modality" |
| **Scale-based Search** | "Find datasets with more than 100K samples" |
| **Paper Explanation** | "Tell me about the OSVQA dataset" |
| **Dataset Comparison** | "Compare GeoChat and SkyEye-968K" |
| **Compare List** | "Add OSVQA to compare list, then add GeoChat, now compare" |
| **Similar Datasets** | "Find datasets similar to GeoChat-Instruct" |
| **Data Leakage Detection** | "Which datasets share source data with GeoChat-Instruct?" |
| **Batch Leakage Detection** | "Detect leakage risk across DOTA, DIOR, UCM" |
| **Recommendations** | "I'm building a SAR captioning model, what datasets should I use?" |
| **Statistics Overview** | "Show me the dataset distribution by year and task type" |
| **Geographic Distribution** | "Which countries publish the most RS-VLM papers?" |
| **Growth Trends** | "How has the number of VQA datasets grown over the years?" |
| **Venue Distribution** | "Which journals and conferences publish the most datasets?" |
| **Publisher Analysis** | "What datasets has TGRS published?" |
| **Timeline** | "Show me the history of SAR captioning datasets" |
| **Relationship Graph** | "What datasets are related to OSVQA?" |
| **Export** | "Export these datasets as BibTeX" / "Generate a Markdown table" |
| **Favorites** | "Save OSVQA to favorites" / "Show my favorites" |
| **Random Discovery** | "Recommend a random dataset" |
| **Dataset Quiz** | "Quiz me on a dataset" |
| **NASA Image of the Day** | "Show me today's NASA satellite image" |

---

## Tools

### Search & Discovery

| Tool | Description |
|------|-------------|
| `search_datasets` | Multi-dimensional search by keywords, modality, task, year, publisher |
| `search_by_scale` | Filter datasets by sample count range, with optional task/modality |
| `get_dataset_info` | Full details of a dataset by name (fuzzy match supported) |
| `get_paper_link` | Find paper URL and trigger AI explanation |
| `recommend_datasets` | Recommend datasets based on a natural language research requirement |
| `find_similar_datasets` | Score-based similarity search across modality, task type, and year |
| `random_dataset` | Random dataset recommendation |

### Comparison

| Tool | Description |
|------|-------------|
| `compare_datasets` | Side-by-side Markdown comparison table (up to 4 datasets) |
| `compare_with_analysis` | Comparison table + AI-generated difference analysis |
| `compare_add / remove / clear / current` | Manage a persistent compare list across turns |

### Data Leakage Detection

| Tool | Description |
|------|-------------|
| `query_source_usage` | Find all datasets that use a given source dataset |
| `batch_leakage_detection` | Detect high-risk intersections across multiple source datasets |
| `list_all_sources` | List all available source dataset names |
| `dataset_relations` | Find datasets sharing source data with a given dataset |

### Statistics & Analytics

| Tool | Description |
|------|-------------|
| `dataset_stats` | Overview: year / task / modality / category distribution |
| `dataset_geo_stats` | Country and region distribution of paper origins |
| `dataset_trend_stats` | Year-over-year growth trend by task type, with growth rate |
| `dataset_venue_stats` | Journal and conference publication distribution |
| `publisher_analysis` | All datasets from a given publisher, with task/modality breakdown |
| `dataset_timeline` | Chronological view of datasets, filterable by task or modality |

### Favorites & Export

| Tool | Description |
|------|-------------|
| `favorite_add / remove / list` | Manage a persistent favorites list |
| `export_dataset_summary` | Export datasets as a Markdown table or BibTeX citations |

### Extras

| Tool | Description |
|------|-------------|
| `dataset_quiz` | Random guessing game — identify a dataset from partial clues |
| `nasa_image_of_the_day` | Fetch the latest NASA Earth Observatory satellite image |

---

## Data

- Dataset index: [`rs_vlm_datasets.xlsx`](rs_vlm_datasets.xlsx) — structured metadata for 146+ RS-VLM datasets across VQA, Caption, VG, and Comprehensive categories
- Paper links: [`dataset_links.md`](dataset_links.md) — maps dataset names to paper URLs (arXiv, IEEE, ISPRS, etc.)
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
