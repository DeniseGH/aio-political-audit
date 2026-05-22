from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class SerpRecord:
    # ── Identifiers ───────────────────────────────────────────────
    query:                  str
    topic:                  str
    timestamp_utc:          str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # ── AI Overview ───────────────────────────────────────────────
    has_ai_overview:        bool = False
    aio_text:               Optional[str] = None   # testo completo AIO
    aio_sources:            Optional[str] = None   # JSON list: [{title, link}]
    aio_source_count:       int = 0                # n. fonti citate nell'AIO
    aio_domains:            Optional[str] = None   # JSON list of domains citati nell'AIO

    # ── Organic results ───────────────────────────────────────────
    organic_count:          int = 0                # n. risultati organici ritornati
    organic_json:           Optional[str] = None   # lista completa come JSON string
    organic_domains:        Optional[str] = None   # JSON list of domains top-10

    # ── AIO vs Organic overlap ────────────────────────────────────
    aio_organic_overlap:    Optional[float] = None # % domini AIO presenti in organic top-10

    # ── Top 3 organic flat ────────────────────────────────────────
    org1_title:             Optional[str] = None
    org1_link:              Optional[str] = None
    org1_date:              Optional[str] = None   # ISO 8601 normalizzata
    org2_title:             Optional[str] = None
    org2_link:              Optional[str] = None
    org2_date:              Optional[str] = None
    org3_title:             Optional[str] = None
    org3_link:              Optional[str] = None
    org3_date:              Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)