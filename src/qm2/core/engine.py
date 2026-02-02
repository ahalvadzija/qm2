from __future__ import annotations

import platform
import select
import random
import string
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import questionary
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.prompt import Prompt

from qm2.utils.files import load_json, save_json

console = Console()

QuizResult = Literal["correct", "wrong", "timeout", "quit"]


def _is_valid_question(q: dict[str, Any]) -> bool:
    """Validate question structure before use. Prevents KeyError/TypeError."""
    if not isinstance(q, dict):
        return False
    if "type" not in q or "question" not in q:
        return False
    if q["type"] == "match":
        pairs = q.get("pairs", {})
        return bool(
            pairs.get("left") and pairs.get("right") and pairs.get("answers")
        )
    return "correct" in q


def input_with_timeout(prompt: str, timeout: int = 60) -> str | None:
    if platform.system() == "Windows":
        result = {"value": None}

        def _get_input():
            try:
                result["value"] = input(f"{prompt} ").strip()
            except (EOFError, KeyboardInterrupt):
                result["value"] = None

        t = threading.Thread(target=_get_input, daemon=True)
        t.start()
        t.join(timeout)
        if t.is_alive():
            return None
        return result["value"]

    try:
        sys.stdout.write(f"{prompt} ")
        sys.stdout.flush()
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            line = sys.stdin.readline()
            return line.rstrip("\n")
        return None
    except Exception:
        return None


def _check_quit_confirmation(message: str = "Do you want to stop the quiz?") -> bool:
    """Return True if user confirms quit."""
    return bool(questionary.confirm(message).ask())


def _handle_choice_question(q: dict[str, Any]) -> QuizResult:
    """Handle multiple choice or true/false question. Returns result type."""
    # Ensure wrong_answers is always a list
    wrong_answers = q["wrong_answers"]
    if isinstance(wrong_answers, str):
        wrong_answers = [wrong_answers]
    
    options = [q["correct"]] + wrong_answers
    random.shuffle(options)
    option_labels = list(string.ascii_lowercase)[: len(options)]

    table = Table(box=box.SIMPLE)
    table.add_column("Option", style="cyan")
    table.add_column("Answer")
    for label, option in zip(option_labels, options, strict=False):
        table.add_row(label, option)
    console.print(table)

    remaining_time = 60
    start_time_q = time.time()

    while True:
        elapsed = time.time() - start_time_q
        remaining = int(remaining_time - elapsed)

        if remaining <= 0:
            console.print(f"[red]❌ Time is up. Correct answer: [bold]{q['correct']}[/]")
            return "timeout"

        answer = input_with_timeout(
            f"⏳ {remaining}s - Your choice (letter, x to quit):", remaining
        )

        if answer is None:
            console.print(f"[red]❌ Time is up. Correct answer: [bold]{q['correct']}[/]")
            return "timeout"

        answer = answer.strip().lower()

        if answer == "x":
            if _check_quit_confirmation():
                console.print("[yellow]⏹️ Quiz stopped by the user.")
                return "quit"
            continue

        if answer in option_labels:
            selected = options[option_labels.index(answer)]
            if selected.lower().strip() == q["correct"].lower().strip():
                console.print("[green]✅ Correct!")
                return "correct"
            console.print(f"[red]❌ Wrong. The correct answer is: [bold]{q['correct']}[/]")
            return "wrong"

        console.print("[yellow]⚠️ Invalid input.")


def _handle_fillin_question(q: dict[str, Any]) -> QuizResult:
    """Handle fill-in question. Returns result type."""
    remaining_time = 60
    start_time_q = time.time()

    while True:
        elapsed = time.time() - start_time_q
        remaining = int(remaining_time - elapsed)

        if remaining <= 0:
            console.print(f"[red]❌ Time is up. Correct answer: [bold]{q['correct']}[/]")
            return "timeout"

        answer = input_with_timeout(
            f"⏳ {remaining}s - Enter the correct answer (or x to quit):", remaining
        )

        if answer is None:
            console.print(f"[red]❌ Time is up. Correct answer: [bold]{q['correct']}[/]")
            return "timeout"

        answer = answer.strip()

        if answer.lower() == "x":
            if _check_quit_confirmation():
                console.print("[yellow]⏹️ Quiz stopped by the user.")
                return "quit"
            continue

        if answer.lower() == q["correct"].lower():
            console.print("[green]✅ Correct!")
            return "correct"
        console.print(f"[red]❌ Wrong. The correct answer is: [bold]{q['correct']}[/]")
        return "wrong"


def _handle_match_question(q: dict[str, Any]) -> QuizResult:
    """Handle matching question. Returns result type."""
    pairs = q.get("pairs", {})
    left = pairs.get("left", [])
    right = pairs.get("right", [])
    correct_mapping = pairs.get("answers", {})

    if not left or not right or not correct_mapping:
        console.print("[red]⚠️ Matching question is not properly defined.")
        return "wrong"

    console.print("[cyan]Match the items (input: a-1, b-2, ...):")
    table = Table.grid(padding=(0, 3))
    for i, (left_val, right_val) in enumerate(zip(left, right, strict=False), start=1):
        table.add_row(
            f"[bold]{chr(96 + i)})[/bold] {left_val}", f"[bold]{i}.[/bold] {right_val}"
        )
    console.print(table)

    user_mapping: dict[str, str] = {}
    remaining_time = 60
    start_time_q = time.time()

    for i in range(len(left)):
        elapsed = time.time() - start_time_q
        remaining = int(remaining_time - elapsed)

        if remaining <= 0:
            console.print("[red]❌ Time is up. You didn't complete the question.")
            return "timeout"

        l_item = left[i]
        input_val = input_with_timeout(
            f"⏳ {remaining}s - Enter the number for pair {chr(97 + i)}) {l_item} (or x to quit):",
            remaining,
        )

        if input_val is None:
            console.print(f"[red]❌ Time is up. You didn't answer {chr(97 + i)})")
            return "timeout"

        if input_val.lower() == "x":
            if _check_quit_confirmation():
                console.print("[yellow]⏹️ Quiz stopped by the user.")
                return "quit"
            continue

        user_mapping[chr(97 + i)] = input_val

    if len(user_mapping) != len(correct_mapping):
        return "timeout"

    for k, v in correct_mapping.items():
        if user_mapping.get(k) != str(v):
            console.print("[red]❌ Incorrect. Correct mapping:")
            console.print(f"[bold yellow]{correct_mapping}[/]")
            return "wrong"

    console.print("[green]✅ You matched all pairs correctly!")
    return "correct"


def _show_quiz_statistics(
    correct_count: int,
    wrong_count: int,
    timeout_count: int,
    total: int,
    duration: int,
) -> None:
    """Display quiz statistics."""
    console.rule("[bold magenta]📊 Quiz statistics")
    console.print(f"[green]✅ Correct answers: {correct_count}")
    console.print(f"[red]❌ Wrong answers: {wrong_count}")
    console.print(f"[yellow]⏱️ Unanswered: {timeout_count}")
    console.print(f"[blue]🕓 Total time: {duration} seconds")
    console.print(f"[bold]🎯 Score: {correct_count}/{total} correct")


def _save_quiz_result(
    score_file: str | Path,
    correct_count: int,
    wrong_count: int,
    timeout_count: int,
    total: int,
    duration: int,
) -> None:
    """Save quiz result to file."""
    scores = load_json(str(score_file))
    scores.append(
        {
            "correct": correct_count,
            "wrong": wrong_count,
            "unanswered": timeout_count,
            "total": total,
            "duration_s": duration,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    if not save_json(str(score_file), scores):
        console.print("[red]⚠️ Failed to save quiz results.")


def quiz_session(questions: list[dict[str, Any]], score_file: str | Path) -> None:
    if not questions:
        console.print("[red]⚠️ No available questions.")
        return

    valid_questions = [q for q in questions if _is_valid_question(q)]
    skipped = len(questions) - len(valid_questions)
    if skipped > 0:
        console.print(f"[yellow]⚠️ Skipped {skipped} invalid question(s).[/yellow]")
    if not valid_questions:
        console.print("[red]⚠️ No valid questions available.")
        return

    questions = valid_questions
    random.shuffle(questions)
    correct_count = wrong_count = timeout_count = 0
    start_time = time.time()

    for q in questions:
        console.rule("[bold blue]Question", characters="━")
        console.print(f"\n[bold]{q['question']}[/bold]")

        if q["type"] in ("multiple", "truefalse"):
            result = _handle_choice_question(q)
        elif q["type"] == "fillin":
            result = _handle_fillin_question(q)
        elif q["type"] == "match":
            result = _handle_match_question(q)
        else:
            continue

        if result == "quit":
            return
        if result == "correct":
            correct_count += 1
        elif result == "wrong":
            wrong_count += 1
        elif result == "timeout":
            timeout_count += 1

    duration = int(time.time() - start_time)
    _show_quiz_statistics(correct_count, wrong_count, timeout_count, len(questions), duration)
    _save_quiz_result(score_file, correct_count, wrong_count, timeout_count, len(questions), duration)


def flashcards_mode(questions: list[dict[str, Any]]) -> None:
    if not questions:
        console.print("[red]⚠️ No questions for flashcards.")
        return

    valid_questions = [q for q in questions if _is_valid_question(q)]
    skipped = len(questions) - len(valid_questions)
    if skipped > 0:
        console.print(f"[yellow]⚠️ Skipped {skipped} invalid question(s).[/yellow]")
    if not valid_questions:
        console.print("[red]⚠️ No valid questions available.")
        return

    questions = valid_questions
    random.shuffle(questions)
    for q in questions:
        console.rule("[bold cyan]Flashcard")
        console.print(Panel(f"[bold]{q['question']}[/bold]"))

        ans = Prompt.ask("Press Enter to reveal answer or 'x' to exit", default="")
        if ans.strip().lower() == "x":
            if _check_quit_confirmation("Do you want to exit flashcards mode?"):
                console.print("[yellow]⏹️ Exited flashcards mode.")
                break

        if q["type"] == "match":
            pairs = q.get("pairs", {})
            left = pairs.get("left", [])
            right = pairs.get("right", [])
            correct = pairs.get("answers", {})

            table = Table(box=box.SIMPLE)
            table.add_column("Left", style="cyan")
            table.add_column("Right", style="magenta")
            for key, val in correct.items():
                l_item = left[ord(key) - 97]
                r_item = right[int(val) - 1]
                table.add_row(f"{key}) {l_item}", f"{val}. {r_item}")
            console.print("[green]✅ Correct matching:")
            console.print(table)
        else:
            console.print(f"[green]✅ Correct answer: {q['correct']}[/]")

        cont = Prompt.ask("Press Enter to continue or 'x' to exit", default="")
        if cont.strip().lower() == "x":
            if _check_quit_confirmation("Do you want to exit flashcards mode?"):
                console.print("[yellow]⏹️ Exited flashcards mode.")
                break
