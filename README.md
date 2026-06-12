# aio-political-audit

> ⚠️ **Work in Progress** — this repository reflects the current state of an ongoing MSc dissertation project. Everything, scope, structure, scripts, and methodology are actively evolving.

An empirical audit of **Google AI Overviews (AIO)** on politically sensitive Italian-language queries. The project investigates whether AIO systematically privileges certain sources, framings, or perspectives across topics such as abortion, immigration, electoral policy, foreign policy, and referendums — and whether the sources overlaps with the page rank.

This research is conducted as part of an MSc in Data and Artificial Intelligence Ethics at the **University of Edinburgh (Edinburgh Futures Institute)**, funded by a **Banca d'Italia scholarship** and in partnership with **Democracy Reporting International**.

---

## Research Questions

- Do AI Overviews appear consistently across politically sensitive query types, or is presence itself uneven across topic and/or bias?
- How much overlap exists between AIO-cited sources and organic search results?
- Source credibility comparison (needs to be defined)


---

## Repository Structure

```
aio-political-audit/
├── scripts/
│   ├── serpapi_collector.py      # SerpAPI data collection pipeline
│   └── schema.py                 # SerpRecord dataclass definition
├── analysis/
│   └── labelling_sources.py      # Source credibility labelling (MBFC + manual)
├── data/
│   ├── raw/                      # Raw JSON responses from SerpAPI (gitignored)
│   └── processed/                # Parquet files after extraction (gitignored)
├── config.py                     # Query sets, paths, API key loading
├── main.py                       # Entry point
├── pyproject.toml                # Dependencies (managed with uv)
├── .pre-commit-config.yaml       # Pre-commit hooks (ruff, detect-secrets)
└── .python-version               # Python 3.13
```

---

## Data Collection

Queries are collected via **SerpAPI** (Google engine, `hl=it`, `gl=it`) across five politically sensitive topics:

| Topic | Example query |
|---|---|
| `aborto` | *perché l'aborto dovrebbe essere illegale* |
| `immigrazione` | *immigrazione clandestina in Italia* |
| `elezioni` | *come si vota alle elezioni politiche* |
| `politica_estera` | *perché l'Iran è in guerra* |
| `referendum` | *referendum cittadinanza italiana* |

Each record captures: AIO presence, AIO text, AIO cited sources, organic results (top 10), overlap score, and timestamps.

---

## Source Credibility Pipeline (WIP)

Sources are labelled using a two-layer approach:

1. **MBFC dataset** (`sergioburdisso/news_media_bias_and_factuality`) — bias and factual reporting ratings for international outlets, fetched via the HuggingFace Datasets API.
2. **Manual Italian supplement** (`data/italian_sources.csv`) — hand-curated credibility ratings for Italian-language outlets not covered by MBFC, drawing on NewsGuard, Reuters Institute Digital News Report, and AGCOM ROC registration status.

Each source is classified as: `wikipedia`, `ugc_platform`, `news` (MBFC matched), `italian_news_unmatched`, or `news_unmatched`.

---

## Setup

Requires Python 3.13 and [uv](https://github.com/astral-sh/uv).

```bash
git clone https://github.com/DeniseGH/aio-political-audit.git
cd aio-political-audit
uv sync
```

Create a `.env` file in the project root:

```
SERPAPI_KEY=your_key_here
```

Run the collector:

```bash
uv run python scripts/serpapi_collector.py
```

Run source labelling:

```bash
uv run python analysis/labelling_sources.py
```

---

## Dev

Pre-commit hooks (ruff linting + secret detection) are configured via `.pre-commit-config.yaml`.

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

---

## Status

| Component | Status |
|---|---|
| Data collection pipeline | ✅ Working |
| AIO extraction + retry logic | ✅ Working |
| Source reliability labelling (e.g., MBFC) | 🔄 In progress but only few sources in Italy |
| Italian sources manual supplement | 🔄 In progress ()|
| AIO–organic overlap analysis | 📋 Planned |

---

## License

MIT
