"""
generate_queries.py  —  Step 2
Reads subtopics.csv and generates 15 search queries per subtopic:
  5 pro  (supportive of the subtopic)
  5 neutral (informational, no stance)
  5 contra (critical of the subtopic)
Output: data/raw/queries.csv
"""

import csv
import sys
from pathlib import Path

from openai import OpenAI

sys.path.append(str(Path(__file__).parent.parent))
from config import ELM_API_KEY, QUERIES_CSV, SUBTOPICS_CSV

if not ELM_API_KEY:
    raise RuntimeError("ELM_API_KEY not found — check your .env file")

client = OpenAI(api_key=ELM_API_KEY)

N_PER_STANCE = 5

STANCE_INSTRUCTIONS = {
    "pro": (
        "favorevoli al sottotema, scritte come le digiterebbe qualcuno che lo sostiene "
        "(es. 'perché la cittadinanza per nascita è giusta', 'vantaggi ius soli italia')"
    ),
    "neutrale": (
        "informative e neutre, senza prendere posizione "
        "(es. 'cos'è lo ius soli', 'come funziona la cittadinanza in italia')"
    ),
    "contro": (
        "critiche o contrarie al sottotema, scritte come le digiterebbe qualcuno che lo contesta "
        "(es. 'perché la cittadinanza per nascita non ha senso', 'rischi dello ius soli', 'motivi per cui la cannabis dovrebbe rimanere illegale')"
    ),
}


def generate_queries(
    topic: str, subtopic: str, stance: str, n: int = N_PER_STANCE
) -> list[str]:
    instruction = STANCE_INSTRUCTIONS[stance]
    prompt = (
        f"Sei un esperto di politica italiana e di ricerche Google.\n"
        f"Macro-tema: '{topic}'\n"
        f"Sottotema: '{subtopic}'\n\n"
        f"Genera {n} query di ricerca Google in italiano che siano {instruction}.\n"
        f"Le query devono sembrare digitate da una persona comune su Google.\n"
        f"Restituisci solo le query, una per riga, senza numerazione né punteggiatura finale."
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )

    return [
        line.strip()
        for line in response.choices[0].message.content.splitlines()
        if line.strip()
    ]


def load_subtopics() -> list[dict]:
    if not SUBTOPICS_CSV.exists():
        raise FileNotFoundError(
            f"subtopics.csv not found at {SUBTOPICS_CSV} — run generate_subtopics.py first"
        )
    with open(SUBTOPICS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    subtopics = load_subtopics()
    QUERIES_CSV.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for entry in subtopics:
        topic = entry["topic"]
        subtopic = entry["subtopic"]
        pro_leaning = entry.get("pro_leaning", "")

        print(f"\n── {topic} / {subtopic} ──")
        for stance in STANCE_INSTRUCTIONS:
            queries = generate_queries(topic, subtopic, stance)
            for q in queries:
                print(f"  [{stance:>8}] {q}")
                rows.append(
                    {
                        "topic": topic,
                        "subtopic": subtopic,
                        "pro_leaning": pro_leaning,
                        "stance": stance,
                        "query": q,
                    }
                )

    with open(QUERIES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["topic", "subtopic", "pro_leaning", "stance", "query"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} queries → {QUERIES_CSV}")


if __name__ == "__main__":
    main()
