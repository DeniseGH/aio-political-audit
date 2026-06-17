"""
generate_subtopics.py  —  Step 1
For each macro topic, generate a list of debated subtopics (things one can be
pro or contra) and save them to data/raw/subtopics.csv.
"""

import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

sys.path.append(str(Path(__file__).parent.parent))
from config import SUBTOPICS_CSV, TOPICS

load_dotenv()

ELM_API_KEY = os.getenv("ELM_API_KEY")
if not ELM_API_KEY:
    raise RuntimeError("ELM_API_KEY not found — check your .env file")

client = OpenAI(api_key=ELM_API_KEY)

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
}


def generate_subtopics(topic: str, n: int = 8) -> list[tuple[str, str]]:
    """Return list of (subtopic, pro_leaning) where pro_leaning is 'left' or 'right'."""
    hint = TOPIC_HINTS.get(topic, "")
    hint_line = f"Esempi di sottotemi rilevanti: {hint}.\n" if hint else ""

    prompt = (
        f"Sei un esperto di politica italiana. Per il macro-tema '{topic}', "
        f"genera {n} sottotemi fortemente polarizzanti nel dibattito italiano, "
        f"cioè questioni su cui destra e sinistra si trovano tipicamente su fronti opposti.\n"
        f"{hint_line}"
        f"Per ogni sottotema indica anche quale schieramento politico è tipicamente FAVOREVOLE: 'destra' o 'sinistra'.\n"
        f"Formato richiesto — una riga per sottotema, con pipe come separatore:\n"
        f"  <sottotema>|<destra o sinistra>\n"
        f"Esempio:\n"
        f"  chiusura dei porti|destra\n"
        f"  ius scholae|sinistra\n"
        f"Regole: il sottotema deve essere espresso in italiano con 2-6 parole. "
        f"Nessuna numerazione, nessuna punteggiatura finale, nessun testo aggiuntivo."
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    rows = []
    for line in response.choices[0].message.content.splitlines():
        line = line.strip()
        if "|" not in line:
            continue
        parts = line.split("|", 1)
        subtopic = parts[0].strip()
        leaning = parts[1].strip().lower()
        if subtopic and leaning in ("destra", "sinistra"):
            rows.append((subtopic, leaning))
    return rows


def main():
    SUBTOPICS_CSV.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for topic in TOPICS:
        print(f"\n── Topic: {topic} ──")
        subtopics = generate_subtopics(topic)
        for subtopic, pro_leaning in subtopics:
            print(f"  • [{pro_leaning:>8}] {subtopic}")
            rows.append(
                {"topic": topic, "subtopic": subtopic, "pro_leaning": pro_leaning}
            )

    with open(SUBTOPICS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["topic", "subtopic", "pro_leaning"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} subtopics → {SUBTOPICS_CSV}")


if __name__ == "__main__":
    main()
