# aio-political-audit

> ⚠️ **Work in Progress** — this repository reflects the current state of an ongoing MSc dissertation project. Everything, scope, structure, scripts, and methodology are actively evolving.

An empirical audit of **Google AI Overviews (AIO)** on politically sensitive Italian-language queries. The project investigates whether AIO systematically privileges certain sources, framings, or perspectives across politically polarising topics — and whether the sources overlap with organic page rankings.

This research is conducted as part of an MSc in Data and Artificial Intelligence Ethics at the **University of Edinburgh (Edinburgh Futures Institute)**, funded by a **Banca d'Italia scholarship** and in partnership with **Democracy Reporting International**.

---

## Research Questions

- Do AI Overviews appear consistently across politically sensitive query types, or is presence itself uneven across topics and/or political leaning?
- How much overlap exists between AIO-cited sources and organic search results?
- Do AIO responses differ systematically depending on the political stance embedded in the query?

---

## Query Generation Pipeline

Queries are generated in two steps using the **University of Edinburgh ELM API** (OpenAI-compatible):

### Step 1 — Subtopic generation (`scripts/generate_subtopics.py`)

For each macro topic, an LLM generates ~8 politically polarising subtopics — concrete debates where right and left typically take opposing sides. Each subtopic is labelled with the political leaning that is typically **pro** (`destra` / `sinistra`).

Output: `queries/subtopics.csv`

```
topic,subtopic,pro_leaning
immigrazione,chiusura dei porti,destra
immigrazione,ius scholae,sinistra
aborto,obiettori di coscienza,destra
...
```

### Step 2 — Query generation (`scripts/generate_queries.py`)

For each subtopic, 15 search queries are generated:

| Stance | Count | Description |
|---|---|---|
| `pro` | 5 | Supportive of the subtopic ("perché lo ius scholae è giusto") |
| `neutrale` | 5 | Informational, no stance ("cos'è lo ius scholae") |
| `contro` | 5 | Critical of the subtopic ("perché lo ius scholae non funziona") |

Output: `queries/queries.csv`

```
topic,subtopic,pro_leaning,stance,query
immigrazione,chiusura dei porti,destra,pro,perché chiudere i porti è necessario
immigrazione,chiusura dei porti,destra,neutrale,cosa significa chiusura dei porti
immigrazione,chiusura dei porti,destra,contro,perché la chiusura dei porti è illegale
...
```

---

## Topics

| Topic | Examples of subtopics |
|---|---|
| `droghe_leggere` | legalizzazione cannabis, depenalizzazione possesso |
| `sicurezza_pubblica` | daspo urbano, videosorveglianza, porto d'armi |
| `gpa_utero_in_affitto` | GPA altruistica, reato universale GPA |
| `aborto` | obiettori di coscienza, pillola RU486 |
| `immigrazione` | chiusura dei porti, rimpatri forzati |
| `diritti_lgbtq` | adozione arcobaleno, stepchild adoption |
| `cittadinanza` | ius soli, ius scholae, doppia cittadinanza |
| `fine_vita` | eutanasia legale, testamento biologico |
| `separazione delle carriere` | riforma CSM, giudici e PM separati |
| `premierato` | elezione diretta del premier, riforma costituzionale |
| `energia_nucleare` | nucleare di nuova generazione, small modular reactor |

---

## Repository Structure

```
aio-political-audit/
├── scripts/
│   ├── generate_subtopics.py     # Step 1: LLM-generated subtopics → queries/subtopics.csv
│   ├── generate_queries.py       # Step 2: LLM-generated queries   → queries/queries.csv
│   └── serpapi_collector.py      # SerpAPI data collection pipeline
├── analysis/
│   └── labelling_sources.py      # Source credibility labelling (MBFC + manual)
├── queries/                      # Generated subtopics and queries (gitignored)
│   ├── subtopics.csv
│   └── queries.csv
├── data/
│   ├── raw/                      # Raw JSON responses from SerpAPI (gitignored)
│   └── processed/                # Parquet files after extraction (gitignored)
├── config.py                     # Topics, paths, API key loading
├── main.py                       # Entry point
├── pyproject.toml                # Dependencies (managed with uv)
├── .pre-commit-config.yaml       # Pre-commit hooks (ruff, detect-secrets)
└── .python-version               # Python 3.13
```

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
ELM_API_KEY=your_elm_key_here
```

### Run the pipeline

```bash
# Step 1: generate subtopics
uv run python scripts/generate_subtopics.py

# Step 2: generate queries from subtopics
uv run python scripts/generate_queries.py

# Step 3: collect AIO + organic results via SerpAPI
uv run python scripts/serpapi_collector.py
```

---

## Source Credibility Pipeline (WIP)

Sources are labelled using a two-layer approach:

1. **MBFC dataset** (`sergioburdisso/news_media_bias_and_factuality`) — bias and factual reporting ratings for international outlets, fetched via the HuggingFace Datasets API.
2. **Manual Italian supplement** (`data/italian_sources.csv`) — hand-curated credibility ratings for Italian-language outlets not covered by MBFC, drawing on NewsGuard, Reuters Institute Digital News Report, and AGCOM ROC registration status.

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
| Subtopic generation (LLM) | ✅ Working |
| Query generation — pro / neutral / contra (LLM) | ✅ Working |
| Data collection via SerpAPI | ✅ Working |
| AIO extraction + retry logic | ✅ Working |
| Source credibility labelling (MBFC) | 🔄 In progress |
| Italian sources manual supplement | 🔄 In progress |
| AIO–organic overlap analysis | 📋 Planned |

---

## License

MIT
