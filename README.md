# aio-political-audit

> ⚠️ **Work in Progress** — this repository reflects the current state of an ongoing MSc dissertation project. Everything — scope, structure, scripts, and methodology — is actively evolving.

An empirical audit of **Google AI Overviews (AIO)** on politically sensitive Italian-language queries. The project investigates whether AIO appears or not, if it systematically privileges certain sources, framings, or perspectives across politically polarising topics in Italy — and whether the sources it cites overlap with organic page rankings.

This research is conducted as part of an MSc in Data and Artificial Intelligence Ethics at the **University of Edinburgh (Edinburgh Futures Institute)**, in partnership with **Democracy Reporting International**. I am funded by a **Banca d'Italia Giorgio Mortara scholarship**.

Beyond this specific study, the repository is meant to work as a **reusable audit framework**: end-to-end, from generating politically-framed search queries to analysing what an AI Overview does and doesn't cite. Everything here is built around Italian politics, but every country/language-specific choice lives in a small number of places — see [Reusing this framework](#reusing-this-framework-for-a-different-context) below.

---

## Research Questions

- RQ1 — Opacity of activation: To what extent does the presence of an AI Overview vary systematically across politically contested topics and query framing (e.g. pro/con phrasing), and what are the normative implications of this variation given that Google discloses no criteria for when an AI Overview is triggered?
- RQ2 — Source diversity: To what extent does AIO concentrate citations among a small number of recurring domains compared to the more dispersed source pool of organic results, and what does this concentration imply for the diversity of perspectives users encounter?
- RQ3 — Provenance and accountability of cited content: To what degree do AIO citations rely on user-generated or non-editorially-accountable content (e.g. individual users' YouTube channels) rather than institutionally accountable sources (news outlets, official channels), and what are the implications for accountability and traceability of claims surfaced by AIO on politically sensitive topics?

---

## Reusing this framework for a different context

The pipeline (generate polarised queries → collect SERP/AIO data → analyse presence, sources, and framing sensitivity) doesn't assume anything Italy-specific in its logic — only in its configuration. To adapt it to a different country, language, or topic set, these are the places to touch:

| What you want to change | Where |
|---|---|
| **Country / search locale** | `lang` / `country` params (`hl`, `gl`) in `fetch_serp()`, `scripts/serpapi_collector.py` — currently `"it"` / `"it"` |
| **Language of generated queries & prompts** | `SUBTOPICS_PROMPT`, `QUERIES_PROMPT`, `STANCE_INSTRUCTIONS` in `config.py` — all written in Italian, including the example queries inside the prompts (LLMs follow the language of the examples closely) |
| **Topics & subtopics to audit** | `TOPIC_HINTS` in `config.py` — one entry per macro topic, with a few example subtopics as a steering hint for Step 1 |
| **How many queries per subtopic/stance** | `N_PER_STANCE` in `config.py` (currently 8 → 24 queries per subtopic: pro/neutral/contro) |
| **The pro/con political axis itself** | Hardcoded as binary `destra`/`sinistra` (right/left) in `generate_subtopics.py`'s validation (`leaning in ("destra", "sinistra")`) and throughout the prompts. A multi-party or non-left/right system would need this generalised to an arbitrary label set |
| **LLM backend** | `call_llm()` in `config.py` uses the `openai` Python SDK with `LLM_MODEL = "gpt-4o"` and `ELM_API_KEY` — swap the model name/key, or add a `base_url` for a different OpenAI-compatible endpoint |
| **Language of the analysis output (plots, labels)** | `analysis/common.py`: `STANCE_TRANSLATIONS`, `LEANING_TRANSLATIONS`, `TOPIC_TRANSLATIONS` map the collected Italian codes to the English labels used in every plot. The analysis logic itself (Jaccard overlap, domain extraction, UGC detection, etc.) operates on domains and structured fields, not on query text, so it's language-agnostic downstream of these three dictionaries |
| **Scale** | The only hard constraints are SerpAPI/LLM rate limits and cost — the collector's resume mode (see Step 3 below) makes it safe to run in batches over multiple sessions regardless of how many topics/queries you configure |

Everything downstream of `data/raw/serp_raw_*.json` (the analysis notebooks) reads the same schema regardless of country/language — see [Data Collection Schema](#data-collection-schema).

---

## Query Generation Pipeline

Queries are generated using the **University of Edinburgh ELM API** (OpenAI-compatible), with a human review pass after each LLM step.

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

After generation, review and edit `queries/subtopics.csv` and save it as `queries/subtopics_human_reviewed.csv`. The human reviewer adds `topic_english`, `parties_pro` (parties typically supporting the subtopic), `reason` (why the subtopic is contested / why that side is "pro"), `sources` (link backing the `reason`), and `cross-partisan` (flags a subtopic that doesn't split cleanly along left/right — it is dropped in Step 2, not queried). As of writing, `queries/subtopics_human_reviewed.csv` contains 99 reviewed subtopics across 15 of the 17 topics (see [Topics](#topics)), with 10 flagged `cross-partisan`.

### Step 2 — Query generation (`scripts/generate_queries.py`)

Reads `subtopics_human_reviewed.csv`, skips any subtopic flagged `cross-partisan`, and generates **24 search queries per remaining subtopic** (`N_PER_STANCE = 8` in `config.py`):

| Stance | Count | Description |
|---|---|---|
| `pro` (supportive) | 8 | Supportive of the subtopic — e.g. *"perché lo ius scholae è giusto"* ("why ius scholae is right") |
| `neutrale` (neutral) | 8 | Informational, no stance — e.g. *"cos'è lo ius scholae"* ("what is ius scholae") |
| `contro` (critical) | 8 | Critical of the subtopic — e.g. *"perché lo ius scholae non funziona"* ("why ius scholae doesn't work") |

Output: `queries/queries.csv`

```
topic_english,topic,subtopic,pro_leaning,parties_pro,cross-partisan,stance,query
immigration,immigrazione,chiusura dei porti,destra,,,pro,perché chiudere i porti è necessario
immigration,immigrazione,chiusura dei porti,destra,,,neutrale,cosa significa chiusura dei porti
immigration,immigrazione,chiusura dei porti,destra,,,contro,perché la chiusura dei porti è illegale
...
```

### Step 2b — Human review

> ⚠️ **Human review required**, same pattern as Step 1b. Review `queries/queries.csv` and save it as `queries/queries_human_reviewed.csv` — `serpapi_collector.py` reads from the reviewed file only and refuses to run without it.

As of writing, `queries/queries_human_reviewed.csv` contains 2,017 reviewed queries (672 pro / 673 neutrale / 672 contro) across 84 subtopics and 14 topics — all 2,017 have been collected (see [Status](#status)). Both reviewed CSVs may be `;`- or `,`-delimited — the scripts sniff the delimiter automatically.

### Step 2c — Auxiliary query batches (optional, robustness checks)

Two extra query sets sit alongside the main reviewed CSV, used only by specific analysis cells rather than by the core pipeline:

- **`queries/human_short_queries.csv`** (204 queries) — hand-written short, colloquial phrasings (as opposed to the longer LLM-generated ones), collected into a separate `data/raw_test/` batch and sanity-checked in `analysis/aio_analysis_test.ipynb`, to check whether AIO presence/behaviour is sensitive to query length/style rather than just topic/stance.
- **`queries/symmetric_groups_detail.csv`** (82 groups) — pairs (and sometimes triples with a neutral query) of near-word-for-word-identical queries within the same subtopic that differ only in pro/contro (/neutral) framing, e.g. *"perché l'aborto dovrebbe essere accessibile gratuitamente"* vs. *"perché l'aborto non dovrebbe essere gratuito"*. This is the input to the matched-pair source-overlap analysis in `aio_analysis_1_presence.ipynb` (§5m–5o) — a tighter test of framing sensitivity than pooling all `pro`/`contro` queries in a subtopic, since here the wording is held constant and only the polarity changes. **Note:** the script that mined these matched pairs out of `queries_human_reviewed.csv` isn't currently checked into the repo — treat the CSV as a hand-curated artifact for now if you're reproducing this from scratch.

### Step 3 — Data collection (`scripts/serpapi_collector.py`)

Fetches Google SERP results for every query via the SerpAPI, extracting AI Overview content, organic results, featured snippets, People Also Ask questions, and related searches. Supports resume mode (scans every existing `data/raw/serp_raw_*.json` for queries already collected and skips them) and a two-stage AIO fetch (inline content + `page_token` fallback, up to 2 attempts).

Output:
- `data/raw/serp_raw_<timestamp>.json` — one raw JSON file per collection run (also used as the resume checkpoint)
- `data/processed/serp_master.parquet` — a single cumulative Parquet file, re-merged with all raw JSON on every run

> **Known collection edge case:** SerpAPI occasionally returns an AI Overview "shell" whose second-stage content fetch (`page_token`) comes back empty — no text, no cited sources. These currently still get recorded with `has_ai_overview=True` but empty `aio_domains`/`aio_text`. Downstream, treat `has_ai_overview=True` with empty content as "fetch failed," not as "AIO with zero sources" — see how `_has_real_aio_content()` in `aio_analysis_1_presence.ipynb` §5h handles this.

---

## Topics

17 macro topics configured in `config.py` (`TOPIC_HINTS`), highly polarizing in the Italian political debate. 12 have gone through subtopic generation + human review + query_generation (e.g., `diritti_lgbtq` and `gpa_utero_in_affitto` were merged into one topic during review)

| Topic (Italian) | Topic (English) | Example subtopics |
|---|---|---|
| `droghe_leggere` | Soft drugs | cannabis legalisation, decriminalisation of possession, home cultivation |
| `diritti_lgbtq_gpa_utero_in_affitto` | LGBTQ+ rights & surrogacy | same-sex adoption, civil unions/marriage, gender identity education at school, altruistic surrogacy (*GPA altruistica*), universal crime of surrogacy |
| `aborto` | Abortion | conscientious objection, pharmacological abortion in hospital, stricter gestational limits, family counselling centre funding |
| `immigrazione` | Immigration | port closures & border control, *ius scholae* (school-based citizenship), forced repatriation, security decrees |
| `cittadinanza` | Citizenship | *ius soli* / *ius culturae* (birthright), naturalisation criteria, dual-citizenship taxation, revocation for serious crimes |
| `fine_vita` | End of life | legal euthanasia, assisted suicide, mandatory palliative care, living wills |
| `separazione delle carriere` | Separation of judicial careers | judges/prosecutors career split, CSM independence, judicial "correntismo", magistrates' civil liability |
| `energia_nucleare` | Nuclear energy | nuclear as a climate solution, energy sovereignty, private financing, solar/wind vs. nuclear |
| `armi_ucraina` | Arms to Ukraine | arms shipments to Ukraine, ReArm EU plan, NATO alignment, Italian neutrality, negotiated ceasefire |
| `memoria_storica_antifascismo` | Historical memory / anti-fascism | April 25th commemorations, historical revisionism, *fiamma tricolore* party symbol, foibe massacres |
| `liberta_di_stampa_rai` | Press freedom / public broadcasting | *(planned — subtopics not yet generated)* RAI reform, public media, *par condicio* (equal media access), freedom of information |
| `costo_della_vita_tasse` | Cost of living / taxation | flat tax for the self-employed, payroll tax wedge (*cuneo fiscale*), minimum wage, top-bracket IRPEF cuts |
| `fuga_dei_cervelli` | Brain drain | tax incentives for returning talent, youth job precarity, entry-level wages, public research investment |
| `israele_palestina` | Israel-Palestine | recognition of Palestine, Israel's right to self-defence, arms embargo, "two peoples, two states", EU-Israel association agreement |

Two more raw collection topics get recoded or discarded during analysis (see `analysis/common.py::load_data`, and the [Analysis Notebooks](#analysis-notebooks-wip) note below): `cittadinanza` splits into `costo_della_vita_tasse` (its "dual-citizenship taxation" subtopic) and `immigrazione` (everything else); `sicurezza_pubblica` folds its 3 immigration-adjacent subtopics into `immigrazione` and discards the rest (e.g. detainee rights, policing funding — out of scope for this audit). This leaves **12 topics** in the analysis-ready data.

---

## Repository Structure

```
aio-political-audit/
├── scripts/
│   ├── generate_subtopics.py      # Step 1: LLM subtopics  → queries/subtopics.csv
│   ├── generate_queries.py        # Step 2: LLM queries    → queries/queries.csv
│   ├── serpapi_collector.py       # Step 3: SerpAPI data collection + AIO extraction
│   └── schema.py                  # SerpRecord dataclass (schema for collected records)
├── analysis/
│   ├── common.py                        # Shared preamble: load_data(), palette, topic/stance/leaning translations
│   ├── aio_analysis_1_presence.ipynb    # Part 1: AIO presence, fetch attempts, consistency, AIO–organic overlap, framing-sensitivity (Jaccard)
│   ├── aio_analysis_2_sources.ipynb     # Part 2: UGC sources, YouTube deep-dive, top cited domains, AIO content stats
│   ├── aio_analysis_3_entities.ipynb    # Part 3: entity-aware (canonical-source) AIO–organic overlap
│   ├── aio_analysis_test.ipynb          # Sanity-check for the human_short_queries.csv pilot batch
│   ├── figures/                         # Output figures (PDF), written by the analysis notebooks
│   └── archive/                         # Superseded exploration scripts/notebooks, incl. source_network_analysis.ipynb
│       ├── source_network_analysis.ipynb      # Bipartite/projected source co-citation network analysis (on hold)
│       ├── labelling_sources.py               # Superseded manual YouTube-channel labelling workflow
│       ├── channels_to_label.csv / channels_labeled.csv  # ...its inputs/outputs — Part 2 now resolves channels live via the YouTube API instead
│       └── news_media_bias_and_factuality_dataexploration.ipynb
├── queries/                       # Generated subtopics and queries (gitignored for the moment)
│   ├── subtopics.csv                    # Step 1 output (LLM-only, unreviewed)
│   ├── subtopics_human_reviewed.csv     # Step 1b output — tracked in git despite the folder being gitignored
│   ├── queries.csv                      # Step 2 output (LLM-only, unreviewed)
│   ├── queries_human_reviewed.csv       # Step 2b output — tracked in git despite the folder being gitignored
│   ├── human_short_queries.csv          # Step 2c: hand-written short/colloquial queries for the pilot robustness check
│   └── symmetric_groups_detail.csv      # Step 2c: matched pro/contro(/neutrale) query pairs for the framing-sensitivity analysis
├── data/
│   ├── raw/                       # Raw JSON responses from SerpAPI, one file per run (gitignored)
│   ├── processed/                 # serp_master.parquet, cumulative across all runs (gitignored)
│   ├── raw_test/ / processed_test/  # Same, for the human_short_queries.csv pilot batch (gitignored)
│   └── archive/                   # Older/superseded collection outputs (gitignored)
├── results/                       # Reserved for output figures/tables (currently unused — see analysis/figures/)
├── logs/                          # Collection logs (serpapi_collection.log)
├── config.py                      # Topics, prompts, paths, API key loading, LLM helper — main adaptation surface, see above
├── main.py                        # Entry point (placeholder)
├── pyproject.toml                 # Dependencies (managed with uv)
├── .pre-commit-config.yaml        # Pre-commit hooks (ruff, detect-secrets)
└── .python-version                # Python 3.13
```

> Note: `analysis/`, `data/`, and most of `queries/` are gitignored for now (see `.gitignore`); only the two `*_human_reviewed.csv` files are force-tracked. The notebooks, figures, and collected data therefore only exist locally / are shared outside git until that's revisited before submission.

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

# Step 2b: review queries/queries.csv manually and save as queries/queries_human_reviewed.csv

# Step 3: collect AIO + organic results via SerpAPI
uv run python scripts/serpapi_collector.py
```

Data collection supports **resume mode** — if a run is interrupted, re-running will skip already-collected queries automatically (it scans every `data/raw/serp_raw_*.json` for queries seen so far). This also makes it safe to scale up the topic/query list arbitrarily and collect in batches over multiple sessions.

### Run the analysis

The analysis is split across three notebooks plus a pilot-batch sanity check. Each one loads and cleans the raw data itself, so they can be run independently and in any order (Part 3 also rebuilds the YouTube channel resolution it needs from Part 2, via its own bootstrap cell, if run standalone):

```bash
uv run jupyter notebook analysis/aio_analysis_1_presence.ipynb
uv run jupyter notebook analysis/aio_analysis_2_sources.ipynb
uv run jupyter notebook analysis/aio_analysis_3_entities.ipynb
```

`analysis/aio_analysis_test.ipynb` sanity-checks the separate `human_short_queries.csv` pilot batch (collected into `data/raw_test/`) — auxiliary, not part of the main pipeline.

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
| `aio_fetch_attempts` | Number of SerpAPI calls made before AIO content appeared (or the collector gave up, max 2) |
| `aio_text` | Full AIO text extracted from text blocks |
| `aio_sources` | JSON list of AIO-cited sources `[{title, link, snippet}]` |
| `aio_source_count` | Number of sources cited in AIO |
| `aio_domains` | JSON list of domains cited in AIO |
| `aio_block_types` | JSON list of AIO text-block types (paragraph, list, …) |
| `has_featured_snippet` | Whether Google returned a featured snippet (answer box) |
| `featured_snippet_text` | Featured snippet text, if present |
| `paa_questions` | JSON list of "People Also Ask" question strings |
| `related_searches` | JSON list of related-search query strings |
| `organic_count` | Number of organic results returned |
| `organic_json` | Full organic top-10 as JSON |
| `organic_domains` | JSON list of domains in organic top-10 |
| `aio_organic_overlap` | Share of AIO-cited domains also present in organic top-10 |
| `org1_*` / `org2_*` / `org3_*` | Title, link, and normalised date for top-3 organic results |

---

## Analysis Notebooks (WIP)

All notebooks load the collected `serp_raw_*.json` files themselves via `analysis/common.py::load_data()`, which folds minor topic/subtopic recodes (`cittadinanza` → `immigrazione`/`costo_della_vita_tasse`; `sicurezza_pubblica` → partly `immigrazione`, partly discarded — see [Topics](#topics)), and translates `topic` / `stance` (`pro`/`neutrale`/`contro` → `Pro`/`Neutral`/`Con`) / `pro_leaning` (`sinistra`/`destra` → `Left`/`Right`) to English for all plots.

### Part 1 — `analysis/aio_analysis_1_presence.ipynb`

0. **Query counts** — total records, unique queries, breakdown by stance / leaning / leaning×stance
1. **AIO presence per topic** — how often AIO appears for each macro topic
   - **1b. AIO fetch attempts** — share of queries where AIO appeared on the first SerpAPI request, on a retry, or never (after the collector's max 2 attempts)
2. **AIO presence per stance** — whether `Pro` / `Neutral` / `Con` queries trigger AIO at different rates
   - **2b.** by political leaning × stance (heatmap)
   - **2c.** neutral vs. polarized (`Pro`/`Con` averaged) × leaning
3. **Consistency** — for queries collected more than once, did AIO appear consistently?
4. **AIO presence per subtopic** — granular breakdown within each topic, by leaning and stance
5. **AIO–Organic Overlap** — share of AIO-cited domains also appearing in the organic top-10, sliced by topic, subtopic, stance, leaning, and their combinations (§5a–5g)
   - **§5h–5l. Framing-sensitivity via pooled Jaccard overlap** — for each subtopic, unions the AIO-cited domains across every `Pro` / `Neutral` / `Con` query sharing that subtopic, then computes the Jaccard overlap between each pair of stances. §5j establishes a "noise floor" baseline: the average Jaccard overlap between *different wordings of the same stance* (paraphrase-level variation with no framing change), which the between-stance numbers should be read against.
   - **§5m–5n. Matched query-pair comparison** — a tighter test using `symmetric_groups_detail.csv`'s near-word-for-word pro/contro pairs (framing is the *only* thing that changes), with the distribution of pairwise Jaccard overlap and the most/least framing-sensitive pairs.
   - **§5o. Neutral formulation vs. Pro/Con** — for the subset of matched groups that also have a neutral-phrased query, how much its cited domains overlap with the pro side vs. the contro side.

### Part 2 — `analysis/aio_analysis_2_sources.ipynb`

6. **UGC Sources** — how often user-generated content platforms (YouTube, Reddit, Twitter/X, etc.) appear in AIO vs organic
   - **6e.** YouTube channel deep-dive (channel vs video citations) via the YouTube Data API v3, resolved live (no manual labelling step)
7. **Top Cited Domains** — raw and deduplicated citation counts, rank comparison between AIO and organic (including Sankey/dumbbell-style linked-ranking views), per-topic heatmaps
8. **AIO Content Stats** — source count, text length (chars and words) distributions, broken down by topic, stance, and leaning

### Part 3 — `analysis/aio_analysis_3_entities.ipynb`

9. **Entity-Aware AIO–Organic Overlap** — the domain-string-based overlap metric misses same-source citations across formats (e.g. a YouTube channel cited in AIO vs. the same outlet's website ranking organically) and can produce spurious matches (any two unrelated `youtube.com` links "matching"). This section resolves AIO and organic citations to a canonical media entity (via a hand-curated `ENTITY_MAP`) and recomputes overlap at the entity level, comparing it against the original domain-level metric by topic and stance.


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
| Subtopic generation (LLM) | ✅ Working — 15/17 topics through Step 1b (99 subtopics reviewed, 10 cross-partisan) |
| Query generation — pro / neutrale / contro (LLM) | ✅ Working — 14/17 topics through Step 2b (2,017 queries reviewed) |
| Data collection via SerpAPI (with resume mode) | ✅ Complete — all 2,017 reviewed queries collected across all 14 reviewed topics |
| AIO extraction + two-stage retry logic | ✅ Working (known edge case: empty-content AIO shells, see Step 3 above) |
| Analysis notebooks (presence, framing sensitivity, sources, entity-aware overlap) | 🔄 In progress |

---

## License

MIT
