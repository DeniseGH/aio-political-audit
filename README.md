# aio-political-audit

> ⚠️ **Work in Progress** — this repository reflects the current state of an ongoing MSc dissertation project. Everything — scope, structure, scripts, and methodology — is actively evolving.

An empirical audit of **Google AI Overviews (AIO)** on politically sensitive Italian-language queries. The project investigates whether AIO appears or not, if systematically privileges certain sources, framings, or perspectives across politically polarising topics in Italy— and whether the sources overlap with organic page rankings.

This research is conducted as part of an MSc in Data and Artificial Intelligence Ethics at the **University of Edinburgh (Edinburgh Futures Institute)**, in partnership with **Democracy Reporting International**. I am funded by a **Banca d'Italia Giorgio Mortara scholarship**

---

## Research Questions

- RQ1: Do AI Overviews appear consistently across politically sensitive query types, or is presence itself uneven across topics and/or political leaning?
- RQ2: How much overlap exists between AIO-cited sources and organic search results?
- RQ3: Do AIO responses differ systematically depending on the political stance embedded in the query?

---

## Query Generation Pipeline

Queries are generated in three steps using the **University of Edinburgh ELM API** (OpenAI-compatible).

### Step 1 — Subtopic generation (`scripts/generate_subtopics.py`)

For each macro topic, an LLM generates ~8 politically polarising subtopics — concrete debates where right and left typically take opposing sides. Each subtopic is labelled with the political leaning that is typically **pro**:
- `destra` (right-wing)
- `sinistra` (left-wing)

Output: `queries/subtopics.csv`

```
topic,subtopic,pro_leaning
immigrazione (immigration),chiusura dei porti (port closure),destra (right-wing)
aborto (abortion),obiettori di coscienza (conscientious objectors),destra (right-wing)
...
```

### Step 1b — Human review

> ⚠️ **Human review required** — subtopic labels and political orientations are LLM-generated simplifications and must be validated before proceeding to Step 2.

After generation, review and edit `queries/subtopics.csv` and save it as `queries/subtopics_human_reviewed.csv`. The human reviewer can add extra columns: `topic_english`, `parties_pro`, and `cross-partisan`. In this case `queries/subtopics_human_reviewed.csv` contains ~6/7 subtopics per topic (111 subtopics in total).

### Step 2 — Query generation (`scripts/generate_queries.py`)

Reads `subtopics_human_reviewed.csv` and generates **18 search queries per subtopic**:

| Stance | Count | Description |
|---|---|---|
| `pro` (supportive) | 6 | Supportive of the subtopic — e.g. *"perché lo ius scholae è giusto"* ("why ius scholae is right") |
| `neutrale` (neutral) | 6 | Informational, no stance — e.g. *"cos'è lo ius scholae"* ("what is ius scholae") |
| `contro` (critical) | 6 | Critical of the subtopic — e.g. *"perché lo ius scholae non funziona"* ("why ius scholae doesn't work") |

Output: `queries/queries.csv`

```
topic_english,topic,subtopic,pro_leaning,parties_pro,cross-partisan,stance,query
immigration,immigrazione,chiusura dei porti,destra,,,pro,perché chiudere i porti è necessario
immigration,immigrazione,chiusura dei porti,destra,,,neutrale,cosa significa chiusura dei porti
immigration,immigrazione,chiusura dei porti,destra,,,contro,perché la chiusura dei porti è illegale
...
```

This step creates ~2000 queries.

### Step 3 — Data collection (`scripts/serpapi_collector.py`)

Fetches Google SERP results for every query via the SerpAPI, extracting AI Overview content and organic results. Supports resume mode (skips already-collected queries) and a two-stage AIO fetch (inline content + `page_token` fallback).

Output: `data/raw/serp_raw_<timestamp>.json` + `data/processed/serp_<timestamp>.parquet`

---

## Topics

17 macro topics highly polarizing in the Italian political debate:

| Topic (Italian) | Topic (English) | Example subtopics |
|---|---|---|
| `droghe_leggere` | Soft drugs | cannabis legalisation, decriminalisation of possession |
| `sicurezza_pubblica` | Public safety | urban banning orders (*daspo urbano*), CCTV, right to carry arms |
| `gpa_utero_in_affitto` | Surrogacy | altruistic surrogacy (*GPA altruistica*), universal crime of surrogacy |
| `aborto` | Abortion | conscientious objectors, RU486 pill |
| `immigrazione` | Immigration | port closures, forced repatriation, security decrees |
| `diritti_lgbtq` | LGBTQ+ rights | rainbow adoption, stepchild adoption, gender identity at school |
| `cittadinanza` | Citizenship | *ius soli* (birthright), *ius scholae* (school-based citizenship), dual nationality |
| `fine_vita` | End of life | legal euthanasia, assisted suicide, living wills |
| `separazione delle carriere` | Separation of judicial careers | CSM (*Consiglio Superiore della Magistratura*) reform, separation of judges and prosecutors |
| `premierato` | Prime-ministerialism | direct election of the Prime Minister, constitutional reform |
| `energia_nucleare` | Nuclear energy | next-generation nuclear, small modular reactors, energy transition |
| `armi_ucraina` | Arms to Ukraine | military support to Ukraine, Italian neutrality, conflict escalation |
| `memoria_storica_antifascismo` | Historical memory / anti-fascism | April 25th commemorations, historical revisionism, fascism and anti-fascism |
| `liberta_di_stampa_rai` | Press freedom / public broadcasting | RAI reform, public media, *par condicio* (equal media access), freedom of information |
| `costo_della_vita_tasse` | Cost of living / taxation | flat tax, payroll tax wedge (*cuneo fiscale*), inflation, purchasing power |
| `fuga_dei_cervelli` | Brain drain | incentives for return educated Italian migrants |
| `israele_palestina` | Israel-Palestine | recognition of Palestine, arms embargo on Israel, two-state solution |

---

## Repository Structure

```
aio-political-audit/
├── scripts/
│   ├── generate_subtopics.py      # Step 1: LLM subtopics → queries/subtopics.csv
subtopics_human_reviewed.csv
│   ├── generate_queries.py        # Step 2: LLM queries   → queries/queries.csv
│   ├── serpapi_collector.py       # Step 3: SerpAPI data collection + AIO extraction
│   └── schema.py                  # SerpRecord dataclass (schema for collected records)
├── analysis/
│   ├── aio_analysis.ipynb         # Main analysis notebook (AIO presence, overlap, UGC, domains)
├── queries/                       # Generated subtopics and queries (gitignored for the moment)
│   ├── subtopics.csv
│   ├── subtopics_human_reviewed.csv
│   └── queries.csv
├── data/
│   ├── raw/                       # Raw JSON responses from SerpAPI (gitignored)
│   └── processed/                 # Parquet files after extraction (gitignored)
├── results/                       # Output figures and tables
├── logs/                          # Collection logs (serpapi_collection.log)
├── config.py                      # Topics, prompts, paths, API key loading, LLM helper
├── main.py                        # Entry point (placeholder)
├── pyproject.toml                 # Dependencies (managed with uv)
├── .pre-commit-config.yaml        # Pre-commit hooks (ruff, detect-secrets)
└── .python-version                # Python 3.13
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
YOUTUBE_API_KEY=your_youtube_key_here
```

### Run the pipeline

```bash
# Step 1: generate subtopics
uv run python scripts/generate_subtopics.py

# Step 1b: review queries/subtopics.csv manually and save as queries/subtopics_human_reviewed.csv

# Step 2: generate queries from human-reviewed subtopics
uv run python scripts/generate_queries.py

# Step 3: collect AIO + organic results via SerpAPI
uv run python scripts/serpapi_collector.py
```

Data collection supports **resume mode** — if a run is interrupted, re-running will skip already-collected queries automatically.

### Run the analysis

```bash
uv run jupyter notebook analysis/aio_analysis.ipynb
```

---

## Data Collection Schema

Each collected record (`SerpRecord`) contains:

| Field | Description |
|---|---|
| `query` | The search query |
| `topic` | Macro topic (Italian label) |
| `subtopic` | Specific debate subtopic |
| `pro_leaning` | Political leaning typically pro this subtopic (`destra` / `sinistra` — right-wing / left-wing) |
| `stance` | Query framing (`pro` / `neutrale` / `contro` — supportive / neutral / critical) |
| `timestamp_utc` | Collection time (ISO 8601, UTC) |
| `has_ai_overview` | Whether Google returned an AIO for this query |
| `aio_text` | Full AIO text extracted from text blocks |
| `aio_sources` | JSON list of AIO-cited sources `[{title, link}]` |
| `aio_source_count` | Number of sources cited in AIO |
| `aio_domains` | JSON list of domains cited in AIO |
| `organic_count` | Number of organic results returned |
| `organic_json` | Full organic top-10 as JSON |
| `organic_domains` | JSON list of domains in organic top-10 |
| `aio_organic_overlap` | Share of AIO-cited domains also present in organic top-10 |
| `org1_*` / `org2_*` / `org3_*` | Title, link, and normalised date for top-3 organic results |

---

## Analysis Notebook (`analysis/aio_analysis.ipynb`) (WIP)

The notebook aims to load all collected `serp_raw_*.json` files and runs the following analyses:

1. **AIO presence per topic** — how often AIO appears for each macro topic
2. **AIO presence per stance** — whether `pro` / `neutrale` / `contro` queries trigger AIO at different rates
3. **Consistency** — for queries collected more than once, did AIO appear consistently?
4. **AIO presence per subtopic** — granular breakdown within each topic
5. **AIO–Organic Overlap** — share of AIO-cited domains also appearing in the organic top-10, by topic, subtopic, stance, and their combination
6. **UGC Sources** — how often user-generated content platforms (YouTube, Reddit, Twitter/X, etc.) appear in AIO vs organic, including a YouTube channel deep-dive via the YouTube Data API v3
7. **Top Cited Domains** — raw and deduplicated citation counts, rank comparison between AIO and organic, per-topic heatmaps
8. **AIO Content Stats** — source count, text length (chars and words) distributions, broken down by topic and stance


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
| Query generation — pro / neutrale / contro (LLM) | ✅ Working |
| Data collection via SerpAPI (with resume mode) | ✅ Working |
| AIO extraction + two-stage retry logic | ✅ Working |
| Analysis notebook (AIO presence, overlap, UGC, domains) | 🔄 In progress (3 topics collected so far) |

---

## License

MIT
