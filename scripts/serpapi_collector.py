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
from datetime import datetime, timezone
from urllib.parse import urlparse

sys.path.append(str(Path(__file__).parent.parent))
from config import SERPAPI_KEY, QUERIES, DATA_RAW, DATA_PROCESSED
from schema import SerpRecord

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/serpapi_collection.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


# ── Core functions ────────────────────────────────────────────────────────────
def fetch_aio_content(page_token: str) -> dict:
    """Second-stage fetch to retrieve AIO content via page_token."""
    params = {
        "engine":     "google_ai_overview",
        "page_token": page_token,
        "api_key":    SERPAPI_KEY,
    }
    response = requests.get("https://serpapi.com/search", params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_serp(query: str, lang: str = "it", country: str = "it", retries: int = 2) -> dict:
    params = {
        "engine":   "google",
        "q":        query,
        "hl":       lang,
        "gl":       country,
        "num":      10,
        "no_cache": "true",
        "api_key":  SERPAPI_KEY,
    }

    for attempt in range(retries):
        response = requests.get("https://serpapi.com/search", params=params, timeout=30)
        response.raise_for_status()
        raw = response.json()

        ai_overview = raw.get("ai_overview", {})

        # ── Case 1: content already inline ────────────────────────
        text_blocks = ai_overview.get("text_blocks", [])
        references  = ai_overview.get("references", [])
        has_text = any(b.get("snippet") for b in text_blocks)
        has_refs = len(references) > 0

        if has_text or has_refs:
            log.info(f"   AIO inline content captured on attempt {attempt + 1}")
            return raw

        # ── Case 2: page_token — requires a second request ────────
        page_token = ai_overview.get("page_token")
        if page_token:
            log.info(f"   AIO requires second request (page_token found) — fetching...")
            try:
                aio_raw = fetch_aio_content(page_token)
                # Merge the AIO content back into the main raw response
                if aio_raw.get("ai_overview"):
                    raw["ai_overview"] = aio_raw["ai_overview"]
                    log.info(f"   AIO second-stage content captured")
                else:
                    log.warning(f"   AIO second-stage returned no content")
            except Exception as e:
                log.error(f"   AIO second-stage fetch failed: {e}")
            return raw  # return regardless — don't retry on page_token path

        # ── Case 3: no AIO at all ──────────────────────────────────
        if not ai_overview:
            return raw

        # ── Case 4: shell with empty text_blocks — retry ──────────
        block_types = [b.get("type") for b in text_blocks]
        wait = 30 * (attempt + 1)
        log.warning(
            f"   AIO shell empty (block types: {block_types}) — "
            f"waiting {wait}s before retry ({attempt + 1}/{retries})..."
        )
        time.sleep(wait)

    log.warning(f"   AIO content never populated after {retries} retries — storing shell")
    return raw


def extract_fields(raw: dict, query: str, topic: str) -> SerpRecord:
    now         = datetime.now(timezone.utc)
    ai_overview = raw.get("ai_overview", None)
    organic     = raw.get("organic_results", [])

    aio_text         = None
    aio_sources      = None
    aio_source_count = 0
    aio_domains      = None

    if ai_overview:
        text_blocks = ai_overview.get("text_blocks", [])

        snippets = [
            block.get("snippet", "")
            for block in text_blocks
            if block.get("snippet")
            and block.get("type") not in ("code", "image")
        ]
        aio_text = " ".join(snippets) if snippets else None

        if text_blocks:
            type_counts = {}
            for b in text_blocks:
                t = b.get("type", "unknown")
                type_counts[t] = type_counts.get(t, 0) + 1
            log.info(f"   AIO block types: {type_counts}")

        references       = ai_overview.get("references", [])
        aio_source_count = len(references)
        aio_sources      = json.dumps(
            [{"title": r.get("title"), "link": r.get("link")} for r in references],
            ensure_ascii=False
        )
        aio_domains = json.dumps(
            [extract_domain(r.get("link", "")) for r in references if r.get("link")],
            ensure_ascii=False
        )

    # ── Organic fields ────────────────────────────────────────────
    organic_count   = len(organic)
    organic_domains = json.dumps(
        [extract_domain(r.get("link", "")) for r in organic[:10] if r.get("link")],
        ensure_ascii=False
    )

    # ── Overlap score ─────────────────────────────────────────────
    aio_organic_overlap = None
    if ai_overview and aio_domains:
        aio_dom_set = set(json.loads(aio_domains))
        org_dom_set = set(json.loads(organic_domains))
        aio_organic_overlap = (
            len(aio_dom_set & org_dom_set) / len(aio_dom_set)
            if aio_dom_set else None
        )

    # ── Top 3 organic flat ────────────────────────────────────────
    def _get(i, key):
        return organic[i].get(key) if i < len(organic) else None

    return SerpRecord(
        query               = query,
        topic               = topic,
        has_ai_overview     = ai_overview is not None,
        aio_text            = aio_text,
        aio_sources         = aio_sources,
        aio_source_count    = aio_source_count,
        aio_domains         = aio_domains,
        organic_count       = organic_count,
        organic_json        = json.dumps(
            [{"position": r.get("position"), "title": r.get("title"),
              "link": r.get("link"), "snippet": r.get("snippet")}
             for r in organic[:10]],
            ensure_ascii=False
        ),
        organic_domains     = organic_domains,
        aio_organic_overlap = aio_organic_overlap,
        org1_title          = _get(0, "title"),
        org1_link           = _get(0, "link"),
        org1_date           = parse_date(_get(0, "date"), now),
        org2_title          = _get(1, "title"),
        org2_link           = _get(1, "link"),
        org2_date           = parse_date(_get(1, "date"), now),
        org3_title          = _get(2, "title"),
        org3_link           = _get(2, "link"),
        org3_date           = parse_date(_get(2, "date"), now),
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
        languages=["it"],           # ← parametro separato, non dentro settings
        settings={
            "RELATIVE_BASE":            reference,
            "PREFER_DAY_OF_MONTH":      "first",
            "RETURN_AS_TIMEZONE_AWARE": True,
        }
    )
    return parsed.isoformat() if parsed else date_str

# def extract_fields(raw: dict, query: str, topic: str) -> SerpRecord:
    """Map raw SerpAPI response → typed SerpRecord dataclass."""
    now         = datetime.now(timezone.utc)
    ai_overview = raw.get("ai_overview", None)
    organic     = raw.get("organic_results", [])

    # ── AIO fields ────────────────────────────────────────────────
    aio_text         = None
    aio_sources      = None
    aio_source_count = 0
    aio_domains      = None

    if ai_overview:
        # Concatena tutti i paragrafi dei text_blocks
        text_blocks = ai_overview.get("text_blocks", [])
        aio_text = " ".join(
            block.get("snippet", "")
            for block in text_blocks
            if block.get("type") == "paragraph" and block.get("snippet")
        )

        # Le fonti sono in "references", non "sources"
        references = ai_overview.get("references", [])
        aio_source_count = len(references)
        aio_sources = json.dumps(
            [{"title": r.get("title"), "link": r.get("link")} for r in references],
            ensure_ascii=False
        )
        aio_domains = json.dumps(
            [extract_domain(r.get("link", "")) for r in references if r.get("link")],
            ensure_ascii=False
        )



    # ── Organic fields ────────────────────────────────────────────
    organic_count   = len(organic)
    organic_domains = json.dumps(
        [extract_domain(r.get("link", "")) for r in organic[:10] if r.get("link")],
        ensure_ascii=False
    )

    # ── Overlap score ─────────────────────────────────────────────
    aio_organic_overlap = None
    if ai_overview and aio_domains:
        aio_dom_set = set(json.loads(aio_domains))
        org_dom_set = set(json.loads(organic_domains))
        aio_organic_overlap = (
            len(aio_dom_set & org_dom_set) / len(aio_dom_set)
            if aio_dom_set else None
        )

    # ── Top 3 organic flat ────────────────────────────────────────
    def _get(i, key):
        return organic[i].get(key) if i < len(organic) else None

    return SerpRecord(
        query               = query,
        topic               = topic,
        has_ai_overview     = ai_overview is not None,
        aio_text            = aio_text,
        aio_sources         = aio_sources,
        aio_source_count    = aio_source_count,
        aio_domains         = aio_domains,
        organic_count       = organic_count,
        organic_json        = json.dumps(
            [{"position": r.get("position"), "title": r.get("title"),
              "link": r.get("link"), "snippet": r.get("snippet")}
             for r in organic[:10]],
            ensure_ascii=False
        ),
        organic_domains     = organic_domains,
        aio_organic_overlap = aio_organic_overlap,
        org1_title          = _get(0, "title"),
        org1_link           = _get(0, "link"),
        org1_date           = parse_date(_get(0, "date"), now),
        org2_title          = _get(1, "title"),
        org2_link           = _get(1, "link"),
        org2_date           = parse_date(_get(1, "date"), now),
        org3_title          = _get(2, "title"),
        org3_link           = _get(2, "link"),
        org3_date           = parse_date(_get(2, "date"), now),
    )




def save_results(records: list[SerpRecord], run_id: str):
    # ── Raw JSON backup (always write, even if empty) ──────────────
    raw_path = DATA_RAW / f"serp_raw_{run_id}.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in records], f, ensure_ascii=False, indent=2)
    log.info(f"📦 Raw JSON  → {raw_path}")

    if not records:                                          # ← guard
        log.warning("⚠️  No records to save — skipping Parquet.")
        return pd.DataFrame()

    df = pd.DataFrame([r.to_dict() for r in records])
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
    parquet_path = DATA_PROCESSED / f"serp_{run_id}.parquet"
    df.to_parquet(parquet_path, index=False, engine="fastparquet")
    log.info(f"🗂  Parquet   → {parquet_path}")
    return df


# ── Main loop ─────────────────────────────────────────────────────────────────
def run_collection():
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    records = []

    for topic, queries in QUERIES.items():
        log.info(f"── Topic: {topic} ({len(queries)} queries)")

        for query in queries:
            log.info(f"   Fetching: '{query}'")
            try:
                raw    = fetch_serp(query)
                record = extract_fields(raw, query, topic)
                if record is None:                          # ← guard
                    log.error(f"   extract_fields returned None for '{query}'")
                    continue
                records.append(record)
                status = "✅ AIO" if record.has_ai_overview else "· no AIO"
                log.info(f"   {status}")
            except requests.HTTPError as e:
                log.error(f"   HTTP error for '{query}': {e}")
            except Exception as e:
                log.error(f"   Unexpected error for '{query}': {e}", exc_info=True)  # ← add exc_info

            time.sleep(random.uniform(3, 7))
        time.sleep(random.uniform(10, 15))

    df = save_results(records, run_id)
    log.info(f"\n✅ Done — {len(records)} queries collected.")
    return df


if __name__ == "__main__":
    run_collection()