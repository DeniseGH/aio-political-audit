"""
generate_queries.py  —  Step 2
Reads subtopics_human_reviewed.csv and generates 18 search queries per subtopic:
  8 pro  (supportive of the subtopic)
  8 neutral (informational, no stance)
  8 contra (critical of the subtopic)
Output: data/raw/queries.csv
"""

import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import (
    ELM_API_KEY,
    N_PER_STANCE,
    QUERIES_CSV,
    QUERIES_PROMPT,
    STANCE_INSTRUCTIONS,
    SUBTOPICS_REVIEWED_CSV,
    call_llm,
)

if not ELM_API_KEY:
    raise RuntimeError("ELM_API_KEY not found — check your .env file")


def generate_queries(
    topic: str, subtopic: str, stance: str, reason: str, n: int = N_PER_STANCE
) -> list[str]:
    instruction = STANCE_INSTRUCTIONS[stance]
    prompt = QUERIES_PROMPT.format(
        topic=topic, subtopic=subtopic, n=n, instruction=instruction, reason=reason
    )
    return [
        line.strip()
        for line in call_llm(prompt, temperature=0.8).splitlines()
        if line.strip()
    ]


def load_subtopics() -> list[dict]:
    if not SUBTOPICS_REVIEWED_CSV.exists():
        raise FileNotFoundError(
            f"subtopics_human_reviewed.csv not found at {SUBTOPICS_REVIEWED_CSV}.\n"
            "It is necessary to review the LLM output before generating queries. "
            "Please open queries/subtopics.csv, review the generated subtopics, "
            "and rename the file to subtopics_human_reviewed.csv once done."
        )
    with open(SUBTOPICS_REVIEWED_CSV, newline="", encoding="utf-8-sig") as f:
        header = f.readline()
        f.seek(0)
        delimiter = ";" if ";" in header else ","
        return list(csv.DictReader(f, delimiter=delimiter))


def main():
    subtopics = load_subtopics()
    QUERIES_CSV.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for entry in subtopics:
        topic = entry["topic"]
        subtopic = entry["subtopic"]
        topic_english = entry.get("topic_english", "")
        pro_leaning = entry.get("pro_leaning", "")
        parties_pro = entry.get("parties_pro", "")
        cross_partisan = entry.get("cross-partisan", "")
        reason = entry.get("reason", "")

        if cross_partisan not in (None, "", "nan"):
            print(
                f"\n── {topic} / {subtopic} ── SKIPPED (cross-partisan = {cross_partisan!r})"
            )
            continue

        print(f"\n── {topic} / {subtopic} ──")
        for stance in STANCE_INSTRUCTIONS:
            queries = generate_queries(topic, subtopic, stance, reason)
            for q in queries:
                print(f"  [{stance:>8}] {q}")
                rows.append(
                    {
                        "topic_english": topic_english,
                        "topic": topic,
                        "subtopic": subtopic,
                        "pro_leaning": pro_leaning,
                        "parties_pro": parties_pro,
                        "cross-partisan": cross_partisan,
                        "stance": stance,
                        "query": q,
                    }
                )

    with open(QUERIES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "topic_english",
                "topic",
                "subtopic",
                "pro_leaning",
                "parties_pro",
                "cross-partisan",
                "stance",
                "query",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} queries → {QUERIES_CSV}")


if __name__ == "__main__":
    main()
