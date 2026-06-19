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
ELM_API_KEY = os.getenv("ELM_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


TOPIC_HINTS = {
    "droghe_leggere": "legalizzazione cannabis, cannabis per uso ricreativo, depenalizzazione possesso, cannabis light",
    "sicurezza_pubblica": "daspo urbano, videosorveglianza, porto d'armi, sgombero accampamenti",
    "gpa_utero_in_affitto": "GPA altruistica, reato universale GPA, maternità surrogata commerciale, diritti del nascituro",
    "aborto": "obiettori di coscienza, pillola RU486, aborto farmacologico, limiti gestazionali",
    "immigrazione": "chiusura dei porti, mancanza di lavoro, rimpatri forzati, decreto sicurezza",
    "diritti_lgbtq": "adozione arcobaleno, unioni civili, stepchild adoption, identità di genere a scuola",
    "cittadinanza": "ius soli, ius scholae, doppia cittadinanza, naturalizzazione per residenza",
    "fine_vita": "eutanasia legale, suicidio assistito, cure palliative, testamento biologico",
    "separazione delle carriere": "riforma CSM, giudici e PM separati, indipendenza della magistratura, correntismo giudiziario",
    "premierato": "elezione diretta del premier, poteri del presidente della Repubblica, riforma costituzionale, stabilità di governo",
    "energia_nucleare": "nucleare di nuova generazione, small modular reactor, uscita dal gas, transizione energetica",
    "armi_ucraina": "invio armi all'Ucraina, supporto militare, neutralità italiana, escalation conflitto",
    "memoria_storica_antifascismo": "commemorazioni 25 aprile, revisionismo storico, fascismo e antifascismo, memoria pubblica",
    "liberta_di_stampa_rai": "riforma RAI, editoria pubblica, par condicio, libertà di informazione",
    "costo_della_vita_tasse": "flat tax, cuneo fiscale, inflazione, potere d'acquisto",
    "fuga_dei_cervelli": "brain drain, incentivi al rientro, università pubblica, investimenti in ricerca",
    "israele_palestina": "riconoscimento Palestina, embargo armi Israele, soluzione due stati, cooperazione internazionale",
}

TOPICS = list(TOPIC_HINTS.keys())

# Output paths
SUBTOPICS_CSV = QUERIES_DIR / "subtopics.csv"
QUERIES_CSV = QUERIES_DIR / "queries.csv"
