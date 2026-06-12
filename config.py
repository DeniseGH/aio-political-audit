import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Paths
ROOT_DIR = Path(__file__).parent
DATA_RAW = ROOT_DIR / "data" / "raw"
DATA_PROCESSED = ROOT_DIR / "data" / "processed"
RESULTS_DIR = ROOT_DIR / "results"

# API
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# TODO: better generation of queries


QUERIES = {
    "aborto": [
        # Medio Oriente
        # "perchè l'aborto dovrebbe essere illegale",
        # "cos'è l'aborto",
        "l'immigrazione fa bene all'italia?"
    ],
}


QUERIES_TEST = {
    "immigrazione": [
        "immigrazione in italia",
        "migranti sbarchi italia",
        "decreto flussi 2024",
        "rimpatri immigrati italia",
        "richiedenti asilo italia",
    ],
    "aborto": [
        "legge 194 aborto italia",
        "aborto farmacologico italia",
        "pro vita italia",
        "interruzione volontaria di gravidanza",
        "aborto diritto italia",
    ],
    "politica_estera": [
        # Medio Oriente
        "guerra israele gaza italia",
        "cessate il fuoco gaza",
        "iran guerra",
        "attacco iran israele",
        "iran nucleare",
        "crisi iran usa",
        # Russia-Ucraina
        "guerra ucraina russia",
        "aiuti militari ucraina italia",
        "pace ucraina negoziati",
    ],
    "elezioni": [
        "elezioni comunali",
        "elezioni 2026",
        "elezioni italia",
        "prossime elezioni",
        "elezioni ungheria",
        "elezioni politiche",
        "elezioni amministrative",
        "elezioni comunali 2026",
    ],
    "referendum": [
        "referendum 2026",
        "affluenza referendum",
        "referendum giustizia",
        "referendum risultati",
        "risultati referendum",
        "referendum giustizia 2026",
        "voto referendum",
        "referendum 8 9 giugno",
    ],
}
