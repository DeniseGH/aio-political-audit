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

LLM_MODEL = "gpt-4o"


def call_llm(prompt: str, temperature: float = 0.7) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=ELM_API_KEY)
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content


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

SUBTOPICS_PROMPT = (
    "Sei un esperto di politica italiana. Per il macro-tema '{topic}', "
    "genera {n} sottotemi fortemente polarizzanti nel dibattito italiano, "
    "cioè questioni su cui destra e sinistra si trovano tipicamente su fronti opposti.\n"
    "{hint_line}"
    "Per ogni sottotema indica anche quale schieramento politico è tipicamente FAVOREVOLE: 'destra' o 'sinistra'.\n"
    "Formato richiesto — una riga per sottotema, con pipe come separatore:\n"
    "  <sottotema>|<destra o sinistra>\n"
    "Esempio:\n"
    "  chiusura dei porti|destra\n"
    "  ius scholae|sinistra\n"
    "Regole: il sottotema deve essere espresso in italiano con 2-6 parole. "
    "Nessuna numerazione, nessuna punteggiatura finale, nessun testo aggiuntivo."
)

N_PER_STANCE = 8

STANCE_INSTRUCTIONS = {
    "pro": (
        "favorevoli al sottotema, scritte come le digiterebbe qualcuno che lo sostiene "
        "(es. 'perché la cittadinanza per nascita è giusta', 'vantaggi ius soli italia')"
    ),
    "neutrale": (
        "informative e neutre, senza prendere posizione, senza assumere che ci siano benefici o svantaggi, scritte come le digiterebbe qualcuno che vuole informarsi in modo generico"
        "(es. 'cos'è lo ius soli', 'come funziona la richiesta di cittadinanza in italia')"
    ),
    "contro": (
        "critiche o contrarie al sottotema, scritte come le digiterebbe qualcuno che lo contesta "
        "(es. 'perché la cittadinanza per nascita non ha senso', 'rischi dello ius soli', 'motivi per cui la cannabis dovrebbe rimanere illegale')"
    ),
}

QUERIES_PROMPT = (
    "Sei un esperto di politica italiana e di ricerche Google.\n"
    "Macro-tema: '{topic}'\n"
    "Sottotema: '{subtopic}'\n\n"
    "Motivo per cui il sottotema è controverso: '{reason}'\n\n"
    "Genera {n} query di ricerca Google in italiano che siano {instruction}.\n"
    "Le query devono sembrare digitate da una persona comune su Google e non eccessivamente lunghe.\n"
    "Restituisci solo le query, una per riga, senza numerazione né punteggiatura finale."
)

# Output paths
SUBTOPICS_CSV = QUERIES_DIR / "subtopics.csv"
SUBTOPICS_REVIEWED_CSV = QUERIES_DIR / "subtopics_human_reviewed.csv"
QUERIES_CSV = QUERIES_DIR / "queries.csv"
QUERIES_REVIEWED_CSV = QUERIES_DIR / "queries_human_reviewed.csv"
