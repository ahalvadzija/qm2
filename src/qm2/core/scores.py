from __future__ import annotations

from pathlib import Path
from typing import Any

import questionary
from rich.console import Console
from rich.table import Table
from rich import box

from qm2.utils.files import load_json, save_json

console = Console()

def show_scores_paginated(
    scores: list[dict[str, Any]], page_size: int = 25
) -> None:
    # Normalize entries to English keys while supporting legacy data
    normalized = []
    for s in scores:
        # Extract quiz_name from the record or default to "N/A"
        quiz_name = s.get("quiz_name", "N/A")
        
        correct = s.get("correct", s.get("tačnih", s.get("tacnih", s.get("correct_count", 0))))
        wrong = s.get("wrong", s.get("pogrešnih", s.get("pogresnih", s.get("wrong_count", 0))))
        unanswered = s.get("unanswered", s.get("neodgovorenih", s.get("unanswered_count", 0)))
        total = s.get(
            "total",
            s.get(
                "ukupno",
                s.get("total_questions", (correct or 0) + (wrong or 0) + (unanswered or 0)),
            ),
        )
        duration_s = s.get("duration_s", s.get("trajanje_s", 0))
        timestamp = s.get("timestamp", s.get("vrijeme", "-"))
        
        normalized.append(
            {
                "quiz_name": quiz_name,
                "correct": correct,
                "wrong": wrong,
                "unanswered": unanswered,
                "total": total,
                "duration_s": duration_s,
                "timestamp": timestamp,
            }
        )
    
    normalized.reverse()
    
    total = len(normalized)
    page = 0
    total_pages = (total + page_size - 1) // page_size
    while True:
        start = page * page_size
        end = min(start + page_size, total)
        table = Table(
            title=f"[bold cyan]📈 Statistics [{start + 1}-{end} of {total}]", box=box.SIMPLE
        )
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Quiz", style="bold yellow")
        table.add_column("Correct", style="green")
        table.add_column("Wrong", style="red")
        table.add_column("Unanswered", style="yellow")
        table.add_column("Total", style="white")
        table.add_column("Duration (s)", style="magenta")
        table.add_column("Date", style="blue")
        
        for i, s in enumerate(normalized[start:end], start=start):
            dur = s.get("duration_s", 0)
            if isinstance(dur, int) and dur >= 60:
                dur_str = f"{dur // 60}m {dur % 60}s"
            else:
                dur_str = f"{dur}s"

            raw_ts = s.get("timestamp", "-")
            if len(raw_ts) > 16:
                short_ts = raw_ts[2:16] 
            else:
                short_ts = raw_ts

            table.add_row(
                str(i + 1),
                str(s.get("quiz_name", "N/A")),
                str(s.get("correct", "")),
                str(s.get("wrong", "")),
                str(s.get("unanswered", "")),
                str(s.get("total", "")),
                dur_str,
                short_ts,
            )
        console.print(table)
        
        # --- Navigation ---
        choices = []
        if page > 0:
            choices.append("⟨ Previous")
        if page < total_pages - 1:
            choices.append("Next ⟩")
        choices.append("↩ Back")
        
        action = questionary.select("Navigation", choices=choices).ask()
        if action == "⟨ Previous":
            page -= 1
            continue
        if action == "Next ⟩":
            page += 1
            continue
        break

def view_scores(score_file: str | Path) -> None:
    scores = load_json(str(score_file))
    if not scores:
        console.print("[yellow]⚠️ No saved results.")
        return
    limit = 50
    if len(scores) > limit:
        console.print(f"[white]Showing last {limit} of {len(scores)} results.")
        show_scores_paginated(scores[-limit:], page_size=25)
        action = questionary.select("Options", choices=["👀 Show all", "↩ Back"]).ask()
        if action and action.startswith("👀"):
            show_scores_paginated(scores, page_size=25)
    else:
        show_scores_paginated(scores, page_size=25)


def reset_scores(score_file: str | Path) -> None:
    confirm = questionary.confirm("⚠️ Are you sure you want to delete ALL results?").ask()
    if confirm:
        save_json(str(score_file), [])
        console.print("[red]❌ All results cleared.")
    else:
        console.print("[yellow]↩ Reset canceled.")