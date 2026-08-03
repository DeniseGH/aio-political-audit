"""Shared data loading & cleaning for the aio-political-audit analysis notebooks.


Import from a notebook living in this same directory with e.g.:

    from common import load_data, PALETTE, ROOT, RAW_DIR
    df = load_data()
"""

import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"

PALETTE = {"Pro": "#2ecc71", "Neutral": "#3498db", "Con": "#e74c3c"}


def set_plot_style() -> None:
    """Switch matplotlib text/math rendering to Computer Modern (LaTeX's default font).

    Uses matplotlib's bundled cmr10 font rather than text.usetex, since the latter
    requires escaping characters like "&" that already appear in plot labels.
    DejaVu Serif is kept as a fallback for glyphs cmr10 lacks (e.g. em dashes, ×).
    """
    plt.rcParams.update(
        {
            "font.family": ["cmr10", "DejaVu Serif"],
            "mathtext.fontset": "cm",
            "axes.formatter.use_mathtext": True,
            "axes.unicode_minus": False,
        }
    )


STANCE_TRANSLATIONS = {"pro": "Pro", "neutrale": "Neutral", "contro": "Con"}
LEANING_TRANSLATIONS = {"sinistra": "Left", "destra": "Right"}

TOPIC_TRANSLATIONS = {
    "aborto": "Abortion",
    "armi_ucraina": "Arms to Ukraine",
    "costo_della_vita_tasse": "Cost of Living & Taxes",
    "diritti_lgbtq_gpa_utero_in_affitto": "LGBTQ+ Rights & Surrogacy",
    "droghe_leggere": "Soft Drugs",
    "energia_nucleare": "Nuclear Energy",
    "fine_vita": "End of Life",
    "fuga_dei_cervelli": "Brain Drain",
    "immigrazione": "Immigration",
    "israele_palestina": "Israel-Palestine",
    "memoria_storica_antifascismo": "Historical Memory & Anti-Fascism",
    "separazione delle carriere": "Judicial Reform Referendum",
}

# Canonical entity map for §9 entity-aware overlap (aio_analysis_3_entities.ipynb).
# Keys are lowercase domain names OR lowercase YouTube channel names.
# Values are the canonical entity name used in the overlap calculation.
# Extend this dict whenever you add new data; rewrite entirely for a different
# country's media landscape.
ENTITY_MAP = {
    # ── La7 ──────────────────────────────────────────────────────────────
    "la7.it": "La7",
    "la7 attualità": "La7",
    "la7attualità": "La7",
    "tg la7": "La7",
    "tg la7 attualità": "La7",
    "la7": "La7",
    # ── Il Fatto Quotidiano ───────────────────────────────────────────────
    "ilfattoquotidiano.it": "Il Fatto Quotidiano",
    "il fatto quotidiano": "Il Fatto Quotidiano",
    "fatto quotidiano": "Il Fatto Quotidiano",
    # ── RAI ──────────────────────────────────────────────────────────────
    "rai.it": "RAI",
    "rainews.it": "RAI",
    "rainews": "RAI",
    "rai news": "RAI",
    "rai news 24": "RAI",
    "rai": "RAI",
    # ── Il Sole 24 ORE ────────────────────────────────────────────────────
    "ilsole24ore.com": "Il Sole 24 ORE",
    "il sole 24 ore": "Il Sole 24 ORE",
    "sole 24 ore": "Il Sole 24 ORE",
    # ── Altalex ──────────────────────────────────────────────────────────
    "altalex.com": "Altalex",
    "altalex news": "Altalex",
    "altalex": "Altalex",
    # ── Sky TG24 ─────────────────────────────────────────────────────────
    "tg24.sky.it": "Sky TG24",
    "sky tg24": "Sky TG24",
    "skytg24": "Sky TG24",
    # ── L'Espresso ───────────────────────────────────────────────────────
    "lespresso.it": "L'Espresso",
    "l'espresso": "L'Espresso",
    "espresso": "L'Espresso",
    # ── Vatican News ─────────────────────────────────────────────────────
    "vaticannews.va": "Vatican News",
    "vatican news - italiano": "Vatican News",
    "vatican news": "Vatican News",
    # ── Euronews ─────────────────────────────────────────────────────────
    "it.euronews.com": "Euronews",
    "euronews.com": "Euronews",
    "euronews (in italiano)": "Euronews",
    "euronews italiano": "Euronews",
    # ── Avvenire ─────────────────────────────────────────────────────────
    "avvenire.it": "Avvenire",
    "avvenire": "Avvenire",
    # ── ANSA ─────────────────────────────────────────────────────────────
    "ansa.it": "ANSA",
    "ansa": "ANSA",
    "agensir": "ANSA",  # both are wire agencies
    # ── Wikipedia ────────────────────────────────────────────────────────
    "wikipedia.org": "Wikipedia",
    # ── la Repubblica ────────────────────────────────────────────────────
    "repubblica.it": "la Repubblica",
    "la repubblica": "la Repubblica",
    # ── Corriere della Sera ───────────────────────────────────────────────
    "corriere.it": "Corriere della Sera",
    "corriere della sera": "Corriere della Sera",
    # ── Fanpage.it ───────────────────────────────────────────────────────
    "fanpage.it": "Fanpage.it",
    # ── TV2000 ───────────────────────────────────────────────────────────
    "tv2000.it": "TV2000",
    "tv2000it": "TV2000",
    "tg2000": "TV2000",
    # ── Fondazione Umberto Veronesi ──────────────────────────────────────
    "fondazioneveronesi.it": "Fondazione Umberto Veronesi",
    "fondazione veronesi": "Fondazione Umberto Veronesi",
    # ── Avvocato Cittadinanza ────────────────────────────────────────────
    "avvocatocittadinanza.it": "Avvocato Cittadinanza",
    "avvocato cittadinanza": "Avvocato Cittadinanza",
    # ── ISPI ─────────────────────────────────────────────────────────────
    "ispionline.it": "ISPI",
    "ispi - la geopolitica spiegata in modo chiaro": "ISPI",
    # ── Confindustria ────────────────────────────────────────────────────
    "confindustria.it": "Confindustria",
    "confindustria": "Confindustria",
    # ── Corte Costituzionale ─────────────────────────────────────────────
    "cortecostituzionale.it": "Corte Costituzionale",
    "corte costituzionale": "Corte Costituzionale",
    # ── Garante nazionale privati libertà ────────────────────────────────
    "garantenazionaleprivatiliberta.it": "Garante nazionale privati libertà",
    "garante nazionale privati libertà": "Garante nazionale privati libertà",
    # ── LifeGate ─────────────────────────────────────────────────────────
    "lifegate.it": "LifeGate",
    "lifegate": "LifeGate",
    # ── ANCI ─────────────────────────────────────────────────────────────
    "anci.it": "ANCI",
    "anci lombardia": "ANCI",
    # ── Ministero del Lavoro e delle Politiche Sociali ───────────────────
    "lavoro.gov.it": "Ministero del Lavoro e delle Politiche Sociali",
    "ministero del lavoro e delle politiche sociali": "Ministero del Lavoro e delle Politiche Sociali",
    # ── Consulta di Bioetica ─────────────────────────────────────────────
    "consultadibioetica.org": "Consulta di Bioetica",
    "consulta di bioetica": "Consulta di Bioetica",
    # ── Federazione Cure Palliative ──────────────────────────────────────
    "curepalliative.info": "Federazione Cure Palliative",
    "federazione cure palliative": "Federazione Cure Palliative",
    # ── Mondadori Education ──────────────────────────────────────────────
    "mondadorieducation.it": "Mondadori Education",
    "mondadori education": "Mondadori Education",
    # ── La Stampa ────────────────────────────────────────────────────────
    "lastampa.it": "La Stampa",
    "la stampa": "La Stampa",
    # ── Focus ────────────────────────────────────────────────────────────
    "focus.it": "Focus",
}


def resolve_entity(name: str) -> str:
    """
    Map a domain or YouTube channel name to a canonical entity.
    Strategy:
      1. Exact lowercase match
      2. Substring match (handles 'La7 Attualità – Notizie del giorno' etc.)
      3. Fall back to the original name
    """
    if not name:
        return name
    key = name.lower().strip()
    if key in ENTITY_MAP:
        return ENTITY_MAP[key]
    for k, entity in ENTITY_MAP.items():
        if len(k) > 4 and (key.startswith(k) or k in key):
            return entity
    return name


# subtopics of the legacy "sicurezza_pubblica" topic that get folded into immigrazione;
# every other "sicurezza_pubblica" row is discarded.
SICUREZZA_TO_IMMIGRAZIONE = [
    "controllo dell'immigrazione ai confini",
    "integrazione dei migranti per favorire sicurezza sociale",
    "politiche di accoglienza",
]


def load_data(verbose: bool = True, raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Load every serp_raw_*.json file, fold/discard legacy topics, translate labels to English."""
    records = []
    for path in sorted(raw_dir.glob("serp_raw_*.json")):
        with open(path) as f:
            batch = json.load(f)
        for r in batch:
            r["_file"] = path.name
        records.extend(batch)

    df = pd.DataFrame(records)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    df["has_ai_overview"] = df["has_ai_overview"].astype(bool)
    df["aio_organic_overlap"] = pd.to_numeric(
        df["aio_organic_overlap"], errors="coerce"
    )

    if verbose:
        print(f"Total records : {len(df)}")
        print(f"Topics        : {sorted(df['topic'].dropna().unique())}")
        print(
            f"Date range    : {df['timestamp_utc'].min().date()} → {df['timestamp_utc'].max().date()}"
        )

    # ── fold "cittadinanza" into immigrazione / costo_della_vita_tasse ──────────
    mask_citt = df["topic"] == "cittadinanza"
    mask_doppia = mask_citt & (df["subtopic"] == "tassazione doppia cittadinanza")
    mask_rest = mask_citt & ~mask_doppia

    if mask_citt.any():
        df.loc[mask_doppia, "topic"] = "costo_della_vita_tasse"
        df.loc[mask_rest, "topic"] = "immigrazione"
        if verbose:
            print(
                f"Recoded {mask_citt.sum()} 'cittadinanza' rows "
                f"({mask_doppia.sum()} -> costo_della_vita_tasse, {mask_rest.sum()} -> immigrazione)."
            )
    elif verbose:
        print(
            "Warning: no rows with topic == 'cittadinanza' found in df — nothing to clean."
        )

    # ── sicurezza_pubblica: fold immigration-related subtopics into immigrazione, discard the rest ──
    mask_sic = df["topic"] == "sicurezza_pubblica"
    mask_sic_move = mask_sic & df["subtopic"].isin(SICUREZZA_TO_IMMIGRAZIONE)
    mask_sic_discard = mask_sic & ~df["subtopic"].isin(SICUREZZA_TO_IMMIGRAZIONE)

    if mask_sic.any():
        df.loc[mask_sic_move, "topic"] = "immigrazione"
        df = df[~mask_sic_discard].reset_index(drop=True)
        if verbose:
            print(
                f"Recoded {mask_sic_move.sum()} 'sicurezza_pubblica' rows -> immigrazione, "
                f"discarded {mask_sic_discard.sum()} remaining 'sicurezza_pubblica' rows."
            )
    elif verbose:
        print(
            "Warning: no rows with topic == 'sicurezza_pubblica' found in df — nothing to clean."
        )

    if verbose:
        print(f"Topics        : {sorted(df['topic'].dropna().unique())}")

    # ── translate topic/stance/leaning codes to English for use in all downstream plots ──
    df["topic"] = df["topic"].map(TOPIC_TRANSLATIONS).fillna(df["topic"])
    df["stance"] = df["stance"].map(STANCE_TRANSLATIONS).fillna(df["stance"])
    df["pro_leaning"] = (
        df["pro_leaning"].map(LEANING_TRANSLATIONS).fillna(df["pro_leaning"])
    )

    if verbose:
        print(f"Topics (EN)   : {sorted(df['topic'].dropna().unique())}")
        print(f"Stance (EN)   : {sorted(df['stance'].dropna().unique())}")
        print(f"Leaning (EN)  : {sorted(df['pro_leaning'].dropna().unique())}")

    return df
