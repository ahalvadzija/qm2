# src/qm2/core/templates.py
from __future__ import annotations

from pathlib import Path
import csv
import json

from qm2.paths import CATEGORIES_DIR, CSV_DIR


def create_csv_template(filename: str = "template.csv") -> Path:
    """
    Kreira CSV template u aplikacijskom CSV direktoriju.
    Vraća punu putanju do kreiranog fajla.
    """
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    path = CSV_DIR / filename

    with path.open(mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "type",
                "question",
                "correct",
                "wrong_answers",
                "left",
                "right",
                "answers",
            ]
        )
        writer.writerow(
            [
                "multiple",
                "What is the capital of France?",
                "Paris",
                "Rome,Berlin,Madrid",
                "",
                "",
                "",
            ]
        )
        writer.writerow(["truefalse", "The Sun is a star.", "True", "False", "", "", ""])
        writer.writerow(["fillin", "The capital of Japan is ______.", "Tokyo", "", "", "", ""])
        writer.writerow(
            [
                "match",
                "Match technologies",
                "",
                "",
                "Python|HTML",
                "Programming language|Markup language",
                "a:1,b:2",
            ]
        )

    return path


def create_json_template(filename: str = "example_template.json") -> Path:
    """
    Kreira JSON template u CATEGORIES_DIR/templates.
    Vraća punu putanju do kreiranog fajla.
    """
    folder = CATEGORIES_DIR / "templates"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / filename

    template = [
        {
            "type": "multiple",
            "question": "What is the capital of France?",
            "correct": "Paris",
            "wrong_answers": ["Rome", "Berlin", "Madrid"],
        },
        {
            "type": "truefalse",
            "question": "The Sun is a star.",
            "correct": "True",
            "wrong_answers": ["False"],
        },
        {
            "type": "fillin",
            "question": "The capital of Japan is ______.",
            "correct": "Tokyo",
            "wrong_answers": [],
        },
        {
            "type": "match",
            "question": "Match technologies",
            "pairs": {
                "left": ["Python", "HTML"],
                "right": ["Programming language", "Markup language"],
                "answers": {"a": "1", "b": "2"},
            },
        },
    ]

    path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
    return path