#!/usr/bin/env python3
"""
Retrieval diagnostic script.

WHAT: Runs the required manual test questions (plus any you add) through
      the real retrieval pipeline and prints the best (smallest) cosine
      distance for each, so you can see actual numbers before trusting
      RETRIEVAL_SCORE_THRESHOLD in .env.
WHY:  The assessment requires a confidence/no-answer mechanism, and this
      project's design explicitly refuses to hard-code per-question
      behavior (e.g. `if "pet insurance" in query`). That means the
      threshold in settings.retrieval_score_threshold MUST be calibrated
      against the real embedding model and your real documents — this
      script is that calibration tool.
HOW TO USE:
    1. Run `python scripts/ingest_documents.py` first (needs an index to query).
    2. Run `python scripts/inspect_retrieval.py`.
    3. Look at the printed distances: known-answer questions should show a
       noticeably SMALLER best distance than the no-answer question. Pick a
       RETRIEVAL_SCORE_THRESHOLD in .env that sits between those two groups.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.config import settings  # noqa: E402
from app.rag.retriever import search_company_documents  # noqa: E402

# The five required manual test questions from the assessment, split into
# the ones expected to have document support and the one expected not to.
KNOWN_ANSWER_QUESTIONS = [
    "What is the work from home policy?",
    "How many annual leaves are allowed?",
    "What is the travel policy?",
    "What security rules should employees follow?",
]
NO_ANSWER_QUESTIONS = [
    "Does the company provide pet insurance?",
]


def _run(question: str) -> None:
    chunks = search_company_documents(question, top_k=settings.top_k)
    if not chunks:
        print(f"  [no chunks returned] {question!r}")
        return
    best = min(chunks, key=lambda c: c.distance)
    within_threshold = best.distance <= settings.retrieval_score_threshold
    verdict = "WOULD ANSWER" if within_threshold else "WOULD SAY NO-ANSWER"
    print(f"  best_distance={best.distance:.4f}  top_source={best.source!r}  -> {verdict}")
    print(f"    Q: {question}")


def main() -> int:
    print(f"RETRIEVAL_SCORE_THRESHOLD = {settings.retrieval_score_threshold}")
    print("(cosine distance — smaller means more similar/relevant)\n")

    print("Questions expected to be answerable from the documents:")
    for question in KNOWN_ANSWER_QUESTIONS:
        _run(question)

    print("\nQuestions expected to trigger the no-answer response:")
    for question in NO_ANSWER_QUESTIONS:
        _run(question)

    print(
        "\nIf any 'expected to be answerable' question shows WOULD SAY "
        "NO-ANSWER, or the no-answer question shows WOULD ANSWER, adjust "
        "RETRIEVAL_SCORE_THRESHOLD in .env so it sits between the two groups."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
