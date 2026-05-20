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

# Query settings
QUERIES = {
    "climate_change": ["climate change policy", "global warming"],
    "immigration": ["immigration uk policy", "asylum seekers uk"],
    "defence": ["uk defence spending", "nato uk"],
    "crime": ["uk crime statistics", "knife crime uk"],
}