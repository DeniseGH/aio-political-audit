import csv
import json
import time
import random
import logging
from pathlib import Path
from datetime import datetime, timezone
import requests
import pandas as pd
import sys
import dateparser
from typing import Optional
from urllib.parse import urlparse

sys.path.append(str(Path(__file__).parent.parent))
from config import SERPAPI_KEY, QUERIES_REVIEWED_CSV, DATA_RAW, DATA_PROCESSED
from schema import SerpRecord

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/serpapi_collection.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ── Core functions ────────────────────────────────────────────────────────────
def fetch_aio_content(page_token: str) -> dict:
    """Second-stage fetch to retrieve AIO content via page_token."""
    params = {
        "engine": "google_ai_overview",
        "page_token": page_token,
        "api_key": SERPAPI_KEY,
    }
    response = requests.get("https://serpapi.com/search", params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_serp(
    query: str, lang: str = "it", country: str = "it", retries: int = 2
) -> tuple[dict, int]:
    """Returns (raw_response, number_of_attempts)."""
    params = {
        "engine": "google",
        "q": query,
        "hl": lang,
        "gl": country,
        "num": 10,
        "no_cache": "true",
        "api_key": SERPAPI_KEY,
    }

    last_raw = None

    for attempt in range(retries):
        response = requests.get("https://serpapi.com/search", params=params, timeout=30)
        response.raise_for_status()
        raw = response.json()
        last_raw = raw

        ai_overview = raw.get("ai_overview", {})

        # ── Case 1: content already inline ────────────────────────
        text_blocks = ai_overview.get("text_blocks", [])
        references = ai_overview.get("references", [])
        has_text = any(b.get("snippet") for b in text_blocks)
        has_refs = len(references) > 0

        if has_text or has_refs:
            if attempt > 0:
                log.info(f"   AIO inline content captured on attempt {attempt + 1}")
            return raw, attempt + 1

        # ── Case 2: page_token — requires a second request ────────
        page_token = ai_overview.get("page_token")
        if page_token:
            log.info("   AIO requires second request (page_token found) — fetching...")
            try:
                aio_raw = fetch_aio_content(page_token)
                if aio_raw.get("ai_overview"):
                    raw["ai_overview"] = aio_raw["ai_overview"]
                    log.info("   AIO second-stage content captured")
                else:
                    log.warning("   AIO second-stage returned no content")
            except Exception as e:
                log.error(f"   AIO second-stage fetch failed: {e}")
            return raw, attempt + 1  # don't retry on page_token path

        # ── Case 3: AIO shell with empty blocks — retry ───────────
        if ai_overview:
            block_types = [b.get("type") for b in text_blocks]
            is_last = attempt == retries - 1
            log.warning(
                f"   AIO shell empty (block types: {block_types}) — attempt {attempt + 1}/{retries}"
                + (
                    ""
                    if is_last
                    else f" — waiting {30 * (attempt + 1)}s before retry..."
                )
            )
            if not is_last:
                time.sleep(30 * (attempt + 1))
            continue

        # ── Case 4: no ai_overview key at all — retry with short wait
        is_last = attempt == retries - 1
        log.warning(
            f"   No AIO in response (attempt {attempt + 1}/{retries})"
            + ("" if is_last else f" — waiting {15 * (attempt + 1)}s before retry...")
        )
        if not is_last:
            time.sleep(15 * (attempt + 1))

    log.warning(f"   AIO absent after {retries} attempts — recording as no AIO")
    return last_raw, retries


def load_queries() -> list[dict]:
    if not QUERIES_REVIEWED_CSV.exists():
        raise FileNotFoundError(
            f"queries_human_reviewed.csv not found at {QUERIES_REVIEWED_CSV}.\n"
            "It is necessary to review the LLM output before running the collector. "
            "Please open queries/queries.csv, review the generated queries, "
            "and rename the file to queries_human_reviewed.csv once done."
        )
    with open(QUERIES_REVIEWED_CSV, newline="", encoding="utf-8") as f:
        sample = f.read(2048)
        f.seek(0)
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        return list(csv.DictReader(f, delimiter=delimiter))


def extract_fields(
    raw: dict,
    query: str,
    topic: str,
    subtopic: str = None,
    pro_leaning: str = None,
    stance: str = None,
    aio_fetch_attempts: int = 1,
) -> SerpRecord:
    now = datetime.now(timezone.utc)
    ai_overview = raw.get("ai_overview", None)
    organic = raw.get("organic_results", [])

    aio_text = None
    aio_sources = None
    aio_source_count = 0
    aio_domains = None
    aio_block_types = None

    if ai_overview:
        text_blocks = ai_overview.get("text_blocks", [])

        snippets = [
            block.get("snippet", "")
            for block in text_blocks
            if block.get("snippet") and block.get("type") not in ("code", "image")
        ]
        aio_text = " ".join(snippets) if snippets else None

        if text_blocks:
            types = [b.get("type", "unknown") for b in text_blocks]
            aio_block_types = json.dumps(types, ensure_ascii=False)
            type_counts = {}
            for t in types:
                type_counts[t] = type_counts.get(t, 0) + 1
            log.info(f"   AIO block types: {type_counts}")

        references = ai_overview.get("references", [])
        aio_source_count = len(references)
        aio_sources = json.dumps(
            [
                {
                    "title": r.get("title"),
                    "link": r.get("link"),
                    "snippet": r.get(
                        "snippet"
                    ),  # excerpt cited by AIO (when available)
                }
                for r in references
            ],
            ensure_ascii=False,
        )
        aio_domains = json.dumps(
            [extract_domain(r.get("link", "")) for r in references if r.get("link")],
            ensure_ascii=False,
        )

    # ── Featured snippet ─────────────────────────────────────────
    answer_box = raw.get("answer_box", {})
    has_featured_snippet = bool(answer_box)
    featured_snippet_text = (
        answer_box.get("snippet") or answer_box.get("answer") or None
    )

    # ── People Also Ask ──────────────────────────────────────────
    paa_questions = None
    raw_paa = raw.get("related_questions", [])
    if raw_paa:
        paa_questions = json.dumps(
            [q.get("question") for q in raw_paa if q.get("question")],
            ensure_ascii=False,
        )

    # ── Related searches ─────────────────────────────────────────
    related_searches = None
    raw_rs = raw.get("related_searches", [])
    if raw_rs:
        related_searches = json.dumps(
            [s.get("query") for s in raw_rs if s.get("query")],
            ensure_ascii=False,
        )

    # ── Organic fields ────────────────────────────────────────────
    organic_count = len(organic)
    organic_domains = json.dumps(
        [extract_domain(r.get("link", "")) for r in organic[:10] if r.get("link")],
        ensure_ascii=False,
    )

    # ── Overlap score ─────────────────────────────────────────────
    aio_organic_overlap = None
    if ai_overview and aio_domains:
        aio_dom_set = set(json.loads(aio_domains))
        org_dom_set = set(json.loads(organic_domains))

        if not org_dom_set:
            aio_organic_overlap = None  # no organic domains to compare against — distinct from a real 0% overlap
        else:
            aio_organic_overlap = (
                len(aio_dom_set & org_dom_set) / len(aio_dom_set)
                if aio_dom_set
                else None
            )

    # ── Top 3 organic flat ────────────────────────────────────────
    def _get(i, key):
        return organic[i].get(key) if i < len(organic) else None

    return SerpRecord(
        query=query,
        topic=topic,
        subtopic=subtopic,
        pro_leaning=pro_leaning,
        stance=stance,
        has_ai_overview=ai_overview is not None,
        aio_fetch_attempts=aio_fetch_attempts,
        aio_text=aio_text,
        aio_sources=aio_sources,
        aio_source_count=aio_source_count,
        aio_domains=aio_domains,
        organic_count=organic_count,
        organic_json=json.dumps(
            [
                {
                    "position": r.get("position"),
                    "title": r.get("title"),
                    "link": r.get("link"),
                    "snippet": r.get("snippet"),
                    "date": parse_date(r.get("date"), now),
                }
                for r in organic[:10]
            ],
            ensure_ascii=False,
        ),
        organic_domains=organic_domains,
        aio_organic_overlap=aio_organic_overlap,
        aio_block_types=aio_block_types,
        has_featured_snippet=has_featured_snippet,
        featured_snippet_text=featured_snippet_text,
        paa_questions=paa_questions,
        related_searches=related_searches,
        org1_title=_get(0, "title"),
        org1_link=_get(0, "link"),
        org1_date=parse_date(_get(0, "date"), now),
        org2_title=_get(1, "title"),
        org2_link=_get(1, "link"),
        org2_date=parse_date(_get(1, "date"), now),
        org3_title=_get(2, "title"),
        org3_link=_get(2, "link"),
        org3_date=parse_date(_get(2, "date"), now),
    )


def extract_domain(url: str) -> str:
    """Estrae il dominio base da un URL."""
    return urlparse(url).netloc.replace("www.", "")


def parse_date(date_str: Optional[str], reference: datetime) -> Optional[str]:
    """Normalizza date assolute e relative → ISO 8601 string."""
    if not date_str:
        return None
    parsed = dateparser.parse(
        date_str,
        languages=["it"],  # ← parametro separato, non dentro settings
        settings={
            "RELATIVE_BASE": reference,
            "PREFER_DAY_OF_MONTH": "first",
            "RETURN_AS_TIMEZONE_AWARE": True,
        },
    )
    return parsed.isoformat() if parsed else date_str


MASTER_PARQUET = DATA_PROCESSED / "serp_master.parquet"


def save_results(records: list[SerpRecord], run_id: str):
    # ── Raw JSON backup per run (audit trail, always written) ─────
    raw_path = DATA_RAW / f"serp_raw_{run_id}.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in records], f, ensure_ascii=False, indent=2)
    log.info(f"📦 Raw JSON  → {raw_path}")

    if not records:
        log.warning("⚠️  No records to save — skipping Parquet.")
        return pd.DataFrame()

    new_df = pd.DataFrame([r.to_dict() for r in records])
    new_df["timestamp_utc"] = pd.to_datetime(new_df["timestamp_utc"])

    # ── Master Parquet: merge with existing data ───────────────────
    if MASTER_PARQUET.exists():
        existing = pd.read_parquet(MASTER_PARQUET, engine="fastparquet")
        # align columns in case schema gained new fields since last run
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df

    combined.to_parquet(MASTER_PARQUET, index=False, engine="fastparquet")
    log.info(f"🗂  Master    → {MASTER_PARQUET}  ({len(combined)} total rows)")
    return new_df


# ── Resume helpers ────────────────────────────────────────────────────────────
def _load_collected_queries() -> set[str]:
    """Return set of queries already saved in any existing raw JSON in DATA_RAW."""
    seen: set[str] = set()
    for path in sorted(DATA_RAW.glob("serp_raw_*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                for r in json.load(f):
                    if r.get("query"):
                        seen.add(r["query"])
        except Exception:
            pass
    return seen


def _checkpoint(records: list, raw_path: Path) -> None:
    """Overwrite the JSON checkpoint with all records collected so far."""
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in records], f, ensure_ascii=False, indent=2)


# ── Main loop ─────────────────────────────────────────────────────────────────
def run_collection():
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    raw_path = DATA_RAW / f"serp_raw_{run_id}.json"
    records = []

    already_done = _load_collected_queries()
    if already_done:
        log.info(
            f"⏭  Resume mode — {len(already_done)} queries already collected, will skip them"
        )

    rows = load_queries()
    log.info(f"Loaded {len(rows)} queries from {QUERIES_REVIEWED_CSV}")

    current_topic = None
    for row in rows:
        topic = row["topic"]
        subtopic = row["subtopic"]
        pro_leaning = row.get("pro_leaning", "")
        stance = row["stance"]
        query = row["query"]

        if query in already_done:
            log.info(f"   [skip] {query}")
            continue

        if topic != current_topic:
            log.info(f"── Topic: {topic}")
            current_topic = topic

        log.info(f"   [{stance}] {query}")
        try:
            raw, attempts = fetch_serp(query)
            record = extract_fields(
                raw,
                query,
                topic,
                subtopic,
                pro_leaning,
                stance,
                aio_fetch_attempts=attempts,
            )
            if record is None:
                log.error(f"   extract_fields returned None for '{query}'")
                continue
            records.append(record)
            status = "✅ AIO" if record.has_ai_overview else "· no AIO"
            log.info(f"   {status}")
            _checkpoint(records, raw_path)
        except requests.HTTPError as e:
            log.error(f"   HTTP error for '{query}': {e}")
            if e.response is not None and e.response.status_code == 429:
                log.error(
                    "   ⛔ SerpAPI quota exhausted — stopping. Re-run when quota resets."
                )
                break
        except Exception as e:
            log.error(f"   Unexpected error for '{query}': {e}", exc_info=True)

        time.sleep(random.uniform(3, 7))

    df = save_results(records, run_id)
    log.info(f"\n✅ Done — {len(records)} queries collected.")
    return df


if __name__ == "__main__":
    run_collection()
