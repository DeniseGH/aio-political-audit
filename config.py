import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Paths
ROOT_DIR = Path(__file__).parent
DATA_RAW = ROOT_DIR / "data" / "raw"
DATA_PROCESSED = ROOT_DIR / "data" / "processed"
RESULTS_DIR = ROOT_DIR / "results"
QUERIES_DIR = ROOT_DIR / "queries"

# API
SERPAPI_KEY = os.getenv("SERPAPI_KEY")


TOPICS = [
    "droghe_leggere",
    "sicurezza_pubblica",
    "gpa_utero_in_affitto",
    "aborto",
    "immigrazione",
    "diritti_lgbtq",
    "cittadinanza",
    "fine_vita",
    "separazione delle carriere",
    "premierato",
    "energia_nucleare",
]

# Output paths
SUBTOPICS_CSV = QUERIES_DIR / "subtopics.csv"
QUERIES_CSV = QUERIES_DIR / "queries.csv"
