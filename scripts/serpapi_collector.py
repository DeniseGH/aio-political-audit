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
def fetch_serp(query: str, lang: str = "it", country: str = "it") -> dict:
    """Fetch Google SERP results for a single query via SerpAPI."""
    params = {
        "engine":  "google",
        "q":       query,
        "hl":      lang,
        "gl":      country,
        "num":     10,
        "api_key": SERPAPI_KEY,
    }
    response = requests.get("https://serpapi.com/search", params=params, timeout=30)
    response.raise_for_status()
    return response.json()




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

def extract_fields(raw: dict, query: str, topic: str) -> SerpRecord:
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
    """Save raw JSON backup + processed Parquet."""
    # JSON raw backup
    raw_path = DATA_RAW / f"serp_raw_{run_id}.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in records], f, ensure_ascii=False, indent=2)
    log.info(f"📦 Raw JSON  → {raw_path}")

    # Parquet processed
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
                records.append(record)
                status = "✅ AIO" if record.has_ai_overview else "· no AIO"
                log.info(f"   {status}")
            except requests.HTTPError as e:
                log.error(f"   HTTP error for '{query}': {e}")
            except Exception as e:
                log.error(f"   Unexpected error for '{query}': {e}")

            time.sleep(random.uniform(3, 7))
        time.sleep(random.uniform(10, 15))

    df = save_results(records, run_id)
    log.info(f"\n✅ Done — {len(records)} queries collected.")
    return df


if __name__ == "__main__":
    run_collection()