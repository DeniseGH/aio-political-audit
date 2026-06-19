"""
generate_subtopics.py  —  Step 1
For each macro topic, generate a list of debated subtopics (things one can be
pro or contra) and save them to data/raw/subtopics.csv.
DISCLAIMER: The output below is an automatically generated initial list only.
Both the subtopics and their associated political orientations must be reviewed
and validated by the user before any use. Political attributions are
simplifications and may not reflect the full complexity of the actual debate.
"""

import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import (
    ELM_API_KEY,
    SUBTOPICS_CSV,
    SUBTOPICS_PROMPT,
    TOPIC_HINTS,
    TOPICS,
    call_llm,
)

if not ELM_API_KEY:
    raise RuntimeError("ELM_API_KEY not found — check your .env file")


def generate_subtopics(topic: str, n: int = 8) -> list[tuple[str, str]]:
    """Return list of (subtopic, pro_leaning) where pro_leaning is 'left' or 'right'."""
    hint = TOPIC_HINTS.get(topic, "")
    hint_line = f"Esempi di sottotemi rilevanti: {hint}.\n" if hint else ""
    prompt = SUBTOPICS_PROMPT.format(topic=topic, n=n, hint_line=hint_line)

    rows = []
    for line in call_llm(prompt, temperature=0.7).splitlines():
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
