import csv
import json
import os
import platform
import random
import re
import select
import string
import sys
import threading
import time
from datetime import datetime
import importlib.resources as pkg_resources
import qm2

import questionary
import requests
from questionary import Choice
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from qm2.paths import CATEGORIES_DIR, CSV_DIR, SCORES_FILE


console = Console()

# Caching and helpers for performance on large datasets
categories_root = str(CATEGORIES_DIR)
categories_cache = None  # list of relative JSON paths within categories_root
questions_cache = {}  # path -> {"mtime": float, "data": list}
cache_cleanup_counter = 0  # counter for periodic cache cleanup


SAFE_NAME = re.compile(r"^[a-zA-Z0-9._-]{1,64}$")


def refresh_categories_cache(root_dir=categories_root):
    global categories_cache
    categories = []
    if os.path.exists(root_dir):
        for dirpath, _, filenames in os.walk(root_dir):
            for f in filenames:
                if f.endswith(".json"):
                    categories.append(os.path.relpath(os.path.join(dirpath, f), root_dir))
    categories_cache = sorted(set(categories))
    return categories_cache


def get_categories(use_cache=True, root_dir=categories_root):
    global categories_cache
    if not use_cache or categories_cache is None:
        refresh_categories_cache(root_dir)
    # Return a sanitized copy to avoid external mutations and accidental UI items in cache
    base = categories_cache or []
    cats = [c for c in base if isinstance(c, str) and c.endswith(".json")]
    return list(cats)


def _rel_from_root(path, root_dir=categories_root):
    abs_root = os.path.abspath(root_dir)
    abs_path = os.path.abspath(path)
    try:
        common = os.path.commonpath([abs_root, abs_path])
    except Exception:
        common = abs_root
    if common == abs_root:
        return os.path.relpath(abs_path, abs_root)
    # path is already relative or outside root; return as-is
    if path.startswith(root_dir + os.sep):
        return os.path.relpath(path, root_dir)
    return path


def categories_add(path, root_dir=categories_root):
    global categories_cache
    if categories_cache is None:
        return
    rel = _rel_from_root(path, root_dir)
    if rel not in categories_cache:
        categories_cache.append(rel)
        categories_cache.sort()


def categories_remove(path, root_dir=categories_root):
    global categories_cache
    if categories_cache is None:
        return
    rel = _rel_from_root(path, root_dir)
    if rel in categories_cache:
        categories_cache.remove(rel)


def categories_rename(old_path, new_path, root_dir=categories_root):
    global categories_cache
    if categories_cache is None:
        return
    old_rel = _rel_from_root(old_path, root_dir)
    new_rel = _rel_from_root(new_path, root_dir)
    if old_rel in categories_cache:
        categories_cache.remove(old_rel)
    if new_rel not in categories_cache:
        categories_cache.append(new_rel)
        categories_cache.sort()


def get_questions(filename):
    global cache_cleanup_counter
    abs_path = os.path.abspath(filename)
    try:
        mtime = os.path.getmtime(abs_path)
    except FileNotFoundError:
        return []

    # Periodic cache cleanup to prevent memory leaks
    cache_cleanup_counter += 1
    if cache_cleanup_counter > 100:  # cleanup every 100 calls
        cleanup_questions_cache()
        cache_cleanup_counter = 0

    entry = questions_cache.get(abs_path)
    if entry and entry.get("mtime") == mtime:
        return entry.get("data", [])
    data = load_json(abs_path)
    questions_cache[abs_path] = {"mtime": mtime, "data": data}
    return data


def cleanup_questions_cache():
    """Remove entries from cache for files that no longer exist"""
    global questions_cache
    to_remove = []
    for path in questions_cache:
        if not os.path.exists(path):
            to_remove.append(path)
    for path in to_remove:
        del questions_cache[path]


def type_label(t):
    if t == "multiple":
        return "🟢 Multiple choice"
    if t == "truefalse":
        return "🟠 True/False"
    if t == "fillin":
        return "🟡 Fill-in"
    if t == "match":
        return "🟣 Matching"
    return "❔ Unknown"


def show_questions_paginated(questions, title="📚 Questions", page_size=25):
    if not questions:
        console.print("[yellow]⚠️ No questions to display.")
        return
    total = len(questions)
    page = 0
    total_pages = (total + page_size - 1) // page_size
    while True:
        start = page * page_size
        end = min(start + page_size, total)
        table_title = f"{title} [{start + 1}-{end} of {total}]" if total_pages > 1 else title
        table = Table(title=table_title, box=box.SIMPLE)
        table.add_column("#", justify="right")
        table.add_column("Question")
        table.add_column("Type")
        for i, q in enumerate(questions[start:end], start=start):
            table.add_row(str(i + 1), q.get("question", ""), type_label(q.get("type")))
        console.print(table)
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


def show_scores_paginated(scores, page_size=25):
    # Normalize entries to English keys while supporting legacy data
    normalized = []
    for s in scores:
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
                "correct": correct,
                "wrong": wrong,
                "unanswered": unanswered,
                "total": total,
                "duration_s": duration_s,
                "timestamp": timestamp,
            }
        )

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
        table.add_column("Correct", style="green")
        table.add_column("Wrong", style="red")
        table.add_column("Unanswered", style="yellow")
        table.add_column("Total", style="white")
        table.add_column("Duration (s)", style="magenta")
        table.add_column("Date", style="blue")
        for i, s in enumerate(normalized[start:end], start=start):
            dur = s.get("duration_s", 0)
            if isinstance(dur, int) and dur >= 60:
                minutes = dur // 60
                seconds = dur % 60
                dur_str = f"{minutes} min {seconds} s"
            else:
                dur_str = f"{dur} s"
            table.add_row(
                str(i + 1),
                str(s.get("correct", "")),
                str(s.get("wrong", "")),
                str(s.get("unanswered", "")),
                str(s.get("total", "")),
                dur_str,
                s.get("timestamp", "-"),
            )
        console.print(table)
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


def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            console.print(f"[red]⚠️ Invalid JSON format in file: {filename}. Returning empty list.")
            return []
        except UnicodeDecodeError:
            console.print(f"[red]⚠️ Encoding error in file: {filename}. Returning empty list.")
            return []
        except Exception as e:
            console.print(f"[red]⚠️ Error reading file {filename}: {e}. Returning empty list.")
            return []
    return []


def save_json(filename, data):
    try:
        # Ensure directory exists (only if filename contains directory)
        dirname = os.path.dirname(filename)
        if dirname:  # Only create directory if dirname is not empty
            os.makedirs(dirname, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except OSError as e:
        console.print(f"[red]⚠️ Error saving file {filename}: {e}")
        return False
    except (TypeError, ValueError) as e:
        console.print(f"[red]⚠️ Error serializing data to JSON: {e}")
        return False

    # update caches
    try:
        abs_path = os.path.abspath(filename)
        mtime = os.path.getmtime(abs_path)
        questions_cache[abs_path] = {"mtime": mtime, "data": data}
    except Exception:
        pass
    # if saved under categories_root and is json, update categories cache
    try:
        abs_root = os.path.abspath(categories_root)
        abs_file = os.path.abspath(filename)
        if abs_file.endswith(".json") and abs_file.startswith(abs_root + os.sep):
            categories_add(abs_file)
    except Exception:
        pass

    return True


def create_new_category(root_dir=categories_root):
    folder = Prompt.ask("📁 Enter a folder inside 'categories' (e.g., programming/python)").strip()
    # Validate folder name
    if not folder or any(c in folder for c in ["<", ">", ":", '"', "|", "?", "*"]):
        console.print("[red]⚠️ Invalid folder name. Please avoid special characters.")
        return

    name = Prompt.ask("📄 Enter file name (e.g., loops.json)").strip()
    # Validate file name
    if not name or any(c in name for c in ["<", ">", ":", '"', "|", "?", "*"]):
        console.print("[red]⚠️ Invalid file name. Please avoid special characters.")
        return
    path = os.path.join(root_dir, folder, name if name.endswith(".json") else f"{name}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    save_json(path, [])
    categories_add(path)
    console.print(f"[green]✅ New category created: {path}")


def rename_category(root_dir=categories_root):
    rel_files = get_categories()
    if not rel_files:
        console.print("[yellow]⚠️ No categories to rename.")
        return

    choice = questionary.select(
        "✏️ Choose a category to rename:", choices=rel_files + ["↩ Back"]
    ).ask()
    if choice == "↩ Back":
        return

    old_path = os.path.join(root_dir, choice)
    new_name_input = Prompt.ask("📝 New file name (without .json)").strip()
    from pathlib import Path

    # normalizuj ime
    new_name = Path(new_name_input).stem + ".json"

    # Validate new file name
    if not new_name_input or any(c in new_name_input for c in ["<", ">", ":", '"', "|", "?", "*"]):
        console.print("[red]⚠️ Invalid file name. Please avoid special characters.")
        return

    new_path = os.path.join(os.path.dirname(old_path), new_name)

    if os.path.exists(new_path):
        confirm = questionary.confirm(f"⚠️ File '{new_name}' already exists. Overwrite?").ask()
        if not confirm:
            console.print("[yellow]↩ Rename canceled.")
            return

    try:
        os.rename(old_path, new_path)
        categories_rename(choice, os.path.relpath(new_path, root_dir))
        console.print(f"[green]✅ Category renamed: {new_path}")
    except OSError as e:
        console.print(f"[red]⚠️ Error renaming file: {e}")
        return


def delete_category(root_dir=categories_root):
    rel_files = get_categories()
    if not rel_files:
        console.print("[yellow]⚠️ No categories to delete.")
        return

    choice = questionary.select(
        "🗑️ Choose a category to delete:", choices=rel_files + ["↩ Back"]
    ).ask()
    if choice == "↩ Back":
        return

    path = os.path.join(root_dir, choice)
    confirm = questionary.confirm(f"⚠️ Are you sure you want to delete category: {choice}?").ask()
    if confirm:
        try:
            os.remove(path)
            categories_remove(choice)
            console.print(f"[red]❌ Category deleted: {choice}")
        except OSError as e:
            console.print(f"[red]⚠️ Error deleting file: {e}")
            return


def create_question():
    console.rule("[bold green]Add question")
    qtype = questionary.select(
        "Choose question type",
        choices=[
            "1. Multiple choice (1 correct + 3 incorrect)",
            "2. True/False",
            "3. Fill-in-the-blank",
            "4. Matching pairs",
            "↩ Back",
        ],
    ).ask()

    if qtype.startswith("1"):
        question = Prompt.ask("Enter the question")
        correct = Prompt.ask("Enter the correct answer")
        wrong_answers = [Prompt.ask(f"Enter incorrect answer #{i + 1}") for i in range(3)]
        return {
            "type": "multiple",
            "question": question,
            "correct": correct,
            "wrong_answers": wrong_answers,
        }
    elif qtype.startswith("2"):
        question = Prompt.ask("Enter a statement (e.g., 'The Sun is a planet.')")
        correct = Prompt.ask("Enter the correct answer", choices=["True", "False"])
        wrong = "False" if correct == "True" else "True"
        return {
            "type": "truefalse",
            "question": question,
            "correct": correct,
            "wrong_answers": [wrong],
        }
    elif qtype.startswith("3"):
        question = Prompt.ask("Enter a fill-in question (e.g., 'The capital of France is _____.')")
        correct = Prompt.ask("Enter the correct answer")
        return {
            "type": "fillin",
            "question": question,
            "correct": correct.strip(),
            "wrong_answers": [],
        }
    elif qtype.startswith("4"):
        question = Prompt.ask("Enter a question (e.g., 'Match the terms')")
        left = []
        right = []

        console.print("[bold blue]Enter items for the left column (e.g., Python, HTML, Linux):")
        for i in range(3):
            left.append(Prompt.ask(f"  Left {chr(97 + i)})"))

        console.print(
            "[bold blue]Enter items for the right column (e.g., Programming language, Markup language, OS):"
        )
        for i in range(3):
            right.append(Prompt.ask(f"  Right {i + 1})"))

        correct_pairs = {}
        console.print("[bold green]Enter correct pairs like (a-1, b-2, c-3). Answers use 1,2,3 ")
        for i in range(3):
            while True:
                par = Prompt.ask(f"  Pair #{i + 1}")
                if "-" in par:
                    left_letter, right_number = par.split("-", 1)
                    ll = left_letter.strip().lower()
                    rn = right_number.strip()
                    if (
                        ll in [chr(97 + j) for j in range(len(left))]
                        and rn.isdigit()
                        and 1 <= int(rn) <= len(right)
                    ):
                        correct_pairs[ll] = rn
                        break
                console.print("[yellow]⚠️ Invalid input. Use format like 'a-1'.")

        return {
            "type": "match",
            "question": question,
            "pairs": {"left": left, "right": right, "answers": correct_pairs},
        }

    return None


def input_with_timeout(prompt, timeout=60):
    """Read a line from stdin with a timeout (cross-platform compatible).
    Returns the input string (without trailing newline) or None on timeout/error.
    """

    if platform.system() == "Windows":
        # Windows fallback - use thread to enforce timeout
        result = {"value": None}

        def _get_input():
            try:
                result["value"] = input(f"{prompt} ").strip()
            except (EOFError, KeyboardInterrupt):
                result["value"] = None

        t = threading.Thread(target=_get_input, daemon=True)
        t.start()
        t.join(timeout)
        if t.is_alive():  # Timeout expired
            return None
        return result["value"]

    else:
        # Unix-like systems with timeout support
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


def delete_json_quiz_file(root_dir=categories_root):
    json_rel = get_categories()

    if not json_rel:
        console.print("[yellow]⚠️ No .json files available to delete.")
        return

    choices = json_rel + ["↩ Back"]

    choice = questionary.select("🗑️ Choose a .json file to delete:", choices=choices).ask()

    if choice == "↩ Back":
        return

    file_to_delete = os.path.join(root_dir, choice)
    confirm = questionary.confirm(f"⚠️ Do you really want to delete: [bold]{choice}[/]?").ask()
    if confirm:
        try:
            os.remove(file_to_delete)
            categories_remove(choice)
            console.print(f"[red]🗑️ File '{choice}' deleted.")
        except OSError as e:
            console.print(f"[red]⚠️ Error deleting file: {e}")
            return
    else:
        console.print("[yellow]↩ Deletion canceled.")


def quiz_session(questions, score_file):
    if not questions:
        console.print("[red]⚠️ No available questions.")
        return

    random.shuffle(questions)
    correct_count = wrong_count = timeout_count = 0
    start_time = time.time()

    for q in questions:
        console.rule("[bold blue]Question", characters="━")
        console.print(f"\n[bold]{q['question']}[/bold]")

        if q["type"] in ("multiple", "truefalse"):
            options = [q["correct"]] + q["wrong_answers"]
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
                    if q["type"] == "match":
                        console.print("[red]❌ Time is up.")
                    else:
                        console.print(
                            f"[red]❌ Time is up. Correct answer: [bold]{q['correct']}[/]"
                        )
                    timeout_count += 1
                    break

                answer = input_with_timeout(
                    f"⏳ {remaining}s - Your choice (letter, x to quit):", remaining
                )

                if answer is None:
                    if q["type"] == "match":
                        console.print("[red]❌ Time is up.")
                    else:
                        console.print(
                            f"[red]❌ Time is up. Correct answer: [bold]{q['correct']}[/]"
                        )
                    timeout_count += 1
                    break

                answer = answer.strip().lower()

                if answer == "x":
                    confirm = questionary.confirm("Do you want to stop the quiz?").ask()
                    if confirm:
                        console.print("[yellow]⏹️ Quiz stopped by the user.")
                        return
                    else:
                        continue  # timer continues

                if answer in option_labels:
                    selected = options[option_labels.index(answer)]
                    if selected.lower().strip() == q["correct"].lower().strip():
                        console.print("[green]✅ Correct!")
                        correct_count += 1
                    else:
                        console.print(
                            f"[red]❌ Wrong. The correct answer is: [bold]{q['correct']}[/]"
                        )
                        wrong_count += 1
                    break
                else:
                    console.print("[yellow]⚠️ Invalid input.")

        elif q["type"] == "fillin":
            remaining_time = 60
            start_time_q = time.time()

            while True:
                elapsed = time.time() - start_time_q
                remaining = int(remaining_time - elapsed)

                if remaining <= 0:
                    console.print(f"[red]❌ Time is up. Correct answer: [bold]{q['correct']}[/]")
                    timeout_count += 1
                    break

                answer = input_with_timeout(
                    f"⏳ {remaining}s - Enter the correct answer (or x to quit):", remaining
                )

                if answer is None:
                    console.print(f"[red]❌ Time is up. Correct answer: [bold]{q['correct']}[/]")
                    timeout_count += 1
                    break

                answer = answer.strip()

                if answer.lower() == "x":
                    confirm = questionary.confirm("Do you want to stop the quiz?").ask()
                    if confirm:
                        console.print("[yellow]⏹️ Quiz stopped by the user.")
                        return
                    else:
                        continue

                if answer.lower() == q["correct"].lower():
                    console.print("[green]✅ Correct!")
                    correct_count += 1
                else:
                    console.print(f"[red]❌ Wrong. The correct answer is: [bold]{q['correct']}[/]")
                    wrong_count += 1
                break
        elif q["type"] == "match":
            pairs = q.get("pairs", {})
            left = pairs.get("left", [])
            right = pairs.get("right", [])
            correct_mapping = pairs.get("answers", {})

            if not left or not right or not correct_mapping:
                console.print("[red]⚠️ Matching question is not properly defined.")
                wrong_count += 1
                continue

            console.print("[cyan]Match the items (input: a-1, b-2, ...):")

            table = Table.grid(padding=(0, 3))
            for i, (left_val, right_val) in enumerate(zip(left, right, strict=False), start=1):
                table.add_row(
                    f"[bold]{chr(96 + i)})[/bold] {left_val}", f"[bold]{i}.[/bold] {right_val}"
                )
            console.print(table)

            user_mapping = {}
            i = 0

            remaining_time = 60  # total time for the whole match question
            start_time_q = time.time()

            while i < len(left):
                elapsed = time.time() - start_time_q
                remaining = int(remaining_time - elapsed)

                if remaining <= 0:
                    console.print("[red]❌ Time is up. You didn't complete the question.")
                    timeout_count += 1
                    break

                l_item = left[i]
                input_val = input_with_timeout(
                    f"⏳ {remaining}s - Enter the number for pair {chr(97 + i)}) {l_item} (or x to quit):",
                    remaining,
                )

                if input_val is None:
                    console.print(f"[red]❌ Time is up. You didn't answer {chr(97 + i)})")
                    timeout_count += 1
                    break

                if input_val.lower() == "x":
                    confirm = questionary.confirm("Do you want to stop the quiz?").ask()
                    if confirm:
                        console.print("[yellow]⏹️ Quiz stopped by the user.")
                        return  # exit entire quiz_session
                    else:
                        continue  # continue same input without losing time

                user_mapping[chr(97 + i)] = input_val
                i += 1

            # If interrupted mid-question
            if len(user_mapping) != len(correct_mapping):
                timeout_count += 1
                continue

            is_correct = True
            for k, v in correct_mapping.items():
                if user_mapping.get(k) != str(v):
                    is_correct = False
                    break

            if is_correct:
                console.print("[green]✅ You matched all pairs correctly!")
                correct_count += 1
            else:
                console.print("[red]❌ Incorrect. Correct mapping:")
                console.print(f"[bold yellow]{correct_mapping}[/]")
                wrong_count += 1

    # Show statistics
    end_time = time.time()
    duration = int(end_time - start_time)

    console.rule("[bold magenta]📊 Quiz statistics")
    console.print(f"[green]✅ Correct answers: {correct_count}")
    console.print(f"[red]❌ Wrong answers: {wrong_count}")
    console.print(f"[yellow]⏱️ Unanswered: {timeout_count}")
    console.print(f"[blue]🕓 Total time: {duration} seconds")
    console.print(f"[bold]🎯 Score: {correct_count}/{len(questions)} correct")

    # Save result
    scores = load_json(score_file)
    scores.append(
        {
            "correct": correct_count,
            "wrong": wrong_count,
            "unanswered": timeout_count,
            "total": len(questions),
            "duration_s": duration,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    if not save_json(score_file, scores):
        console.print("[red]⚠️ Failed to save quiz results.")


def flashcards_mode(questions):
    if not questions:
        console.print("[red]⚠️ No questions for flashcards.")
        return
    random.shuffle(questions)
    for q in questions:
        console.rule("[bold cyan]Flashcard")
        console.print(Panel(f"[bold]{q['question']}[/bold]"))

        ans = Prompt.ask("Press Enter to reveal answer or 'x' to exit", default="")
        if ans.strip().lower() == "x":
            confirm = questionary.confirm("Do you want to exit flashcards mode?").ask()
            if confirm:
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
                l_item = left[ord(key) - 97]  # 'a' => 0
                r_item = right[int(val) - 1]  # '1' => 0
                table.add_row(f"{key}) {l_item}", f"{val}. {r_item}")

            console.print("[green]✅ Correct matching:")
            console.print(table)

        if q["type"] != "match":
            console.print(f"[green]✅ Correct answer: {q['correct']}[/]")

        cont = Prompt.ask("Press Enter to continue or 'x' to exit", default="")
        if cont.strip().lower() == "x":
            confirm = questionary.confirm("Do you want to exit flashcards mode?").ask()
            if confirm:
                console.print("[yellow]⏹️ Exited flashcards mode.")
                break


def view_scores(score_file):
    scores = load_json(score_file)
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


def reset_scores(score_file):
    confirm = questionary.confirm("⚠️ Are you sure you want to delete ALL results?").ask()
    if confirm:
        save_json(score_file, [])
        console.print("[red]❌ All results cleared.")
    else:
        console.print("[yellow]↩ Reset canceled.")


def show_help():
    try:
        # čitanje help.json kao resursa unutar paketa
        with pkg_resources.files(qm2).joinpath("help.json").open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        console.print("[red]⚠️ Help instructions unavailable or invalid.")
        return

    if not data or "instructions" not in data:
        console.print("[red]⚠️ Help instructions unavailable or invalid.")
        return

    console.rule("[bold cyan]🆘 Help")
    for line in data["instructions"]:
        console.print(f"[white]- {line}")

    questionary.select("↩ Back", choices=["↩ Back"]).ask()



def select_category(allow_create: bool = True) -> str | None:
    categories = get_categories()
    choices = categories + (["➕ Create new"] if allow_create else []) + ["↩ Back"]

    choice = questionary.select("📂 Select a category:", choices=choices).ask()

    if choice is None or choice == "↩ Back":
        return None

    if choice == "➕ Create new":
        name = Prompt.ask("Enter file name (e.g., geography.json)").strip()
        base = os.path.splitext(name)[0]
        filename = base + ".json"
        path = os.path.join(categories_root, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        save_json(path, [])
        return path

    return os.path.join(categories_root, choice)


def edit_question(questions):
    if not questions:
        console.print("[yellow]⚠️ No questions available to edit.")
        return

    choices = [f"{i + 1}. {q['question'][:50]}..." for i, q in enumerate(questions)]
    selection = questionary.select(
        "✏️ Choose a question to edit:", choices=choices + ["↩ Back"]
    ).ask()

    if selection == "↩ Back":
        return

    index = int(selection.split(".")[0]) - 1
    qdata = questions[index]

    qtype = qdata["type"]
    new_question_text = Prompt.ask("New question", default=qdata["question"])

    if qtype == "multiple":
        new_correct = Prompt.ask("New correct answer", default=qdata["correct"])
        current_wrongs = qdata.get("wrong_answers", [])
        default_count = max(3, len(current_wrongs)) if current_wrongs else 3
        try:
            count = int(Prompt.ask("Number of incorrect answers", default=str(default_count)))
            count = max(1, min(10, count))
        except Exception:
            count = default_count
        new_wrongs = []
        for i in range(count):
            default_val = current_wrongs[i] if i < len(current_wrongs) else ""
            new_wrongs.append(Prompt.ask(f"New incorrect answer #{i + 1}", default=default_val))
        questions[index] = {
            "type": "multiple",
            "question": new_question_text,
            "correct": new_correct,
            "wrong_answers": new_wrongs,
        }

    elif qtype == "truefalse":
        new_correct = Prompt.ask(
            "New correct answer", default=qdata["correct"], choices=["True", "False"]
        )
        new_wrong = "False" if new_correct == "True" else "True"
        questions[index] = {
            "type": "truefalse",
            "question": new_question_text,
            "correct": new_correct,
            "wrong_answers": [new_wrong],
        }

    elif qtype == "fillin":
        new_correct = Prompt.ask("New correct answer", default=qdata["correct"])
        questions[index] = {
            "type": "fillin",
            "question": new_question_text,
            "correct": new_correct,
            "wrong_answers": [],
        }

    elif qtype == "match":
        pairs = qdata.get("pairs", {})
        left = pairs.get("left", [])
        right = pairs.get("right", [])
        answers = pairs.get("answers", {})

        console.print("\n[cyan]Current left column (items separated by |):")
        console.print(" | ".join(left))
        new_left = Prompt.ask("New left column", default="|".join(left)).split("|")

        console.print("\n[magenta]Current right column (items separated by |):")
        console.print(" | ".join(right))
        new_right = Prompt.ask("New right column", default="|".join(right)).split("|")

        console.print("\n[yellow]Current mapping (e.g., a:1, b:2)")
        current_pairs = ", ".join([f"{k}:{v}" for k, v in answers.items()])
        raw_new = Prompt.ask("New mapping", default=current_pairs)
        new_answers = {}
        for pair in raw_new.split(","):
            if ":" in pair:
                k, v = pair.strip().split(":")
                new_answers[k.strip()] = v.strip()

        questions[index] = {
            "type": "match",
            "question": new_question_text,
            "pairs": {
                "left": [x.strip() for x in new_left if x.strip()],
                "right": [x.strip() for x in new_right if x.strip()],
                "answers": new_answers,
            },
        }

    console.print("[green]✅ Question updated successfully.")


def edit_question_by_index(questions, index_number):
    """Edit a question directly by its ordinal number (1-based)."""
    if not questions:
        console.print("[yellow]⚠️ No questions available to edit.")
        return
    try:
        index = int(index_number) - 1
    except Exception:
        console.print("[yellow]⚠️ Invalid number.")
        return
    if index < 0 or index >= len(questions):
        console.print(f"[yellow]⚠️ Number out of range. Allowed 1-{len(questions)}.")
        return

    qdata = questions[index]
    qtype = qdata.get("type")
    new_question_text = Prompt.ask("New question", default=qdata.get("question", ""))

    if qtype == "multiple":
        new_correct = Prompt.ask("New correct answer", default=qdata.get("correct", ""))
        current_wrongs = qdata.get("wrong_answers", [])
        default_count = max(3, len(current_wrongs)) if current_wrongs else 3
        try:
            count = int(Prompt.ask("Number of incorrect answers", default=str(default_count)))
            count = max(1, min(10, count))
        except Exception:
            count = default_count
        new_wrongs = []
        for i in range(count):
            default_val = current_wrongs[i] if i < len(current_wrongs) else ""
            new_wrongs.append(Prompt.ask(f"New incorrect answer #{i + 1}", default=default_val))
        questions[index] = {
            "type": "multiple",
            "question": new_question_text,
            "correct": new_correct,
            "wrong_answers": new_wrongs,
        }

    elif qtype == "truefalse":
        new_correct = Prompt.ask(
            "New correct answer", default=qdata.get("correct", ""), choices=["True", "False"]
        )
        new_wrong = "False" if new_correct == "True" else "True"
        questions[index] = {
            "type": "truefalse",
            "question": new_question_text,
            "correct": new_correct,
            "wrong_answers": [new_wrong],
        }

    elif qtype == "fillin":
        new_correct = Prompt.ask("New correct answer", default=qdata.get("correct", ""))
        questions[index] = {
            "type": "fillin",
            "question": new_question_text,
            "correct": new_correct,
            "wrong_answers": [],
        }

    elif qtype == "match":
        pairs = qdata.get("pairs", {})
        left = pairs.get("left", [])
        right = pairs.get("right", [])
        answers = pairs.get("answers", {})

        console.print("\n[cyan]Current left column (items separated by |):")
        console.print(" | ".join(left))
        new_left = Prompt.ask("New left column", default="|".join(left)).split("|")

        console.print("\n[magenta]Current right column (items separated by |):")
        console.print(" | ".join(right))
        new_right = Prompt.ask("New right column", default="|".join(right)).split("|")

        console.print("\n[yellow]Current mapping (e.g., a:1, b:2)")
        current_pairs = ", ".join([f"{k}:{v}" for k, v in answers.items()])
        raw_new = Prompt.ask("New mapping", default=current_pairs)
        new_answers = {}
        for pair in raw_new.split(","):
            if ":" in pair:
                k, v = pair.strip().split(":")
                new_answers[k.strip()] = v.strip()

        questions[index] = {
            "type": "match",
            "question": new_question_text,
            "pairs": {
                "left": [x.strip() for x in new_left if x.strip()],
                "right": [x.strip() for x in new_right if x.strip()],
                "answers": new_answers,
            },
        }

    console.print("[green]✅ Question updated successfully.")


def _delete_question_core(category_file: str, index: int) -> bool:
    questions = load_json(category_file)
    if not isinstance(questions, list) or not (0 <= index < len(questions)):
        console.print("[red]Invalid question index.[/red]")
        return False
    removed = questions.pop(index)
    if save_json(category_file, questions):
        console.print(f"[green]Deleted:[/green] {removed.get('question', '<no text>')}")
        return True
    console.print("[red]Failed to save updated questions.[/red]")
    return False


def delete_question_by_index(category_file: str, index: int) -> None:
    _delete_question_core(category_file, index)


def delete_question(category_file: str) -> None:
    questions = load_json(category_file)
    if not questions:
        console.print("[red]No questions to delete.[/red]")
        return

    choices = [q.get("question", "<no text>") for q in questions]
    choice = questionary.select("Select a question to delete:", choices=choices).ask()
    if not choice:
        return

    index = choices.index(choice)
    _delete_question_core(category_file, index)


def import_remote_file():
    url = Prompt.ask("Enter URL to a CSV or JSON file")
    try:
        response = requests.get(url, timeout=15, stream=True)
        response.raise_for_status()
    except requests.RequestException as e:
        console.print(f"[red]❌ Error downloading file: {e}")
        return

    # Detect extension and destination
    is_csv = url.lower().endswith(".csv")
    is_json = url.lower().endswith(".json")
    if is_csv:
        ext = ".csv"
        max_attempts = 3
        attempts = 0
        while True:
            base = Prompt.ask("Enter file name (without extension)").strip()
            base = os.path.splitext(base)[0].strip().strip(".")
            if SAFE_NAME.match(base):
                filename = f"{base}{ext}"
                break
            console.print(
                "[yellow]⚠️ Invalid name. Use only letters, digits, dot, underscore, dash (max 64 chars).")
            attempts += 1
            if attempts >= max_attempts:
                console.print("[red]❌ Too many invalid attempts. Cancelled.")
                return
        dest_dir = str(CSV_DIR)

    elif is_json:
        ext = ".json"
        dest_dir = str(CATEGORIES_DIR)
        os.makedirs(dest_dir, exist_ok=True)

        max_attempts = 3
        attempts = 0
        while True:
            base = Prompt.ask("Enter category name (without extension)").strip()
            base = os.path.splitext(base)[0].strip().strip(".")
            if SAFE_NAME.match(base):
                filename = f"{base}{ext}"
                break
            console.print("[yellow]⚠️ Invalid name. Use only letters, digits, dot, underscore, dash (max 64 chars).")
            attempts += 1
            if attempts >= max_attempts:
                console.print("[red]❌ Too many invalid attempts. Cancelled.")
                return
    else:
        console.print("[red]⚠️ File must be CSV or JSON!")
        return

    filepath = os.path.join(dest_dir, filename)

    # Prepare directory and handle name conflicts
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # If file exists, ask to overwrite or pick a new name
    while os.path.exists(filepath):
        overwrite = questionary.confirm(
            f"⚠️ File '{filename}' already exists in '{dest_dir}'. Overwrite?"
        ).ask()
        if overwrite:
            break
        ext = ".csv" if is_csv else ".json"
        while True:
            new_base = Prompt.ask("Enter a different file name (without extension)").strip()
            new_base = os.path.splitext(new_base)[0].strip().strip(".")
            if SAFE_NAME.fullmatch(new_base):
                filename = f"{new_base}{ext}"
                filepath = os.path.join(dest_dir, filename)
                break
            console.print(
                "[yellow]⚠️ Invalid name. Use only letters, digits, dot, underscore, dash (max 64 chars)."
            )

    # Save (stream + chunks)
    chunk_size = 1024 * 64
    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)

    # Refresh categories cache if JSON under 'categories'
    if is_json:
        categories_add(filepath)

    console.print(f"[green]✅ File downloaded and saved as: {filepath}")


def show_logo():
    console.print(
        Panel(
            """[bold green]🎓 Welcome to
                    •     ┳┳┓      ┓           
            ┏┓  ┓┏  ┓  ┓  ┃┃┃  ┏┓  ┃┏  ┏┓  ┏┓  
            ┗┫  ┗┻  ┗  ┗  ┛ ┗  ┗┻  ┛┗  ┗   ┛   
             ┗                                 
                             ┏┓                            
                        ┏┓┏┳┓┏┛                            
                        ┗┫┛┗┗┗━                            
                         ┗""",
            expand=False,
        )
    )


def main():
    score_file = str(SCORES_FILE)

    while True:
        console.clear()
        show_logo()

        choice = questionary.select(
            "Main Menu",
            choices=[
                "1.) 🚀 Start Quiz",
                "2.) 👾 Flashcards Learning",
                "3.) 🗂️ Questions",
                "4.) 📈 Statistics",
                "5.) 🧰 Tools",
                "6.) 💞 Help",
                "7.) ⏻  Exit",
            ],
        ).ask()

        if choice.startswith("1"):
            print("   ═══════════════════════ Categories ════════════════════════")
            filename = select_category(allow_create=False)
            if filename:
                questions = get_questions(filename)
                quiz_session(questions, score_file)
                input("\nPress Enter to return to the main menu...")

        elif choice.startswith("2"):
            filename = select_category(allow_create=False)
            if filename:
                questions = get_questions(filename)
                flashcards_mode(questions)

        elif choice.startswith("3"):
            while True:
                # List categories (from cache)
                categories_choices = get_categories()
                categories_choices += [
                    Choice("──────────── MANAGE ────────────", disabled="✖"),
                    "🛠️ Manage categories",
                    "↩ Back",
                ]

                selection = questionary.select(
                    "════════════════════════════════════════════════════════════\n 📂 Questions - choose a category or option:",
                    choices=categories_choices,
                ).ask()

                if selection == "↩ Back":
                    break

                elif selection == "🛠️ Manage categories":
                    while True:
                        opt = questionary.select(
                            "🛠️ Manage categories:",
                            choices=[
                                "➕ Create new category",
                                "✏️ Rename category",
                                "🗑️ Delete category",
                                "🗑️ Delete JSON quiz file",
                                "↩ Back",
                            ],
                        ).ask()

                        if opt.startswith("➕"):
                            create_new_category(categories_root)
                        elif opt.startswith("✏️"):
                            rename_category(categories_root)
                        elif opt == "🗑️ Delete JSON quiz file":
                            delete_json_quiz_file(categories_root)
                        elif opt == "🗑️ Delete category":
                            delete_category(categories_root)
                        elif opt.startswith("↩"):
                            break

                else:
                    # Manage questions for selected category
                    filename = os.path.join(categories_root, selection)
                    questions = get_questions(filename)
                    while True:
                        sub_choice = questionary.select(
                            f"════════════════════════════════════════════════════════════\n 📂 Manage questions ({filename})",
                            choices=[
                                "📚 Show all questions",
                                "🔢 Edit by number",
                                "🔢 Delete by number",
                                "➕ Add question",
                                "📝 Edit question",
                                "🗑️ Delete question",
                                "💾 Save questions",
                                "↩ Back",
                            ],
                        ).ask()

                        if sub_choice == "↩ Back":
                            break

                        if sub_choice == "📚 Show all questions":
                            if questions:
                                show_questions_paginated(
                                    questions, title="📚 Questions", page_size=25
                                )
                            else:
                                console.print("[yellow]⚠️ No questions in this category.")
                        elif sub_choice == "🔢 Edit by number":
                            if not questions:
                                console.print("[yellow]⚠️ No questions to edit.")
                            else:
                                entry = Prompt.ask(
                                    f"Enter question number (1-{len(questions)})"
                                ).strip()
                                if not entry.isdigit():
                                    console.print("[yellow]⚠️ Invalid input.")
                                else:
                                    edit_question_by_index(questions, int(entry))
                        elif sub_choice == "🔢 Delete by number":
                            if not questions:
                                console.print("[yellow]⚠️ No questions to delete.")
                            else:
                                entry = Prompt.ask(
                                    f"Enter question number (1-{len(questions)})"
                                ).strip()
                                if not entry.isdigit():
                                    console.print("[yellow]⚠️ Invalid input.")
                                else:
                                    delete_question_by_index(questions, int(entry))
                        elif sub_choice.startswith("➕"):
                            q = create_question()
                            if q:
                                questions.append(q)
                        elif sub_choice.startswith("📝"):
                            edit_question(questions)
                        elif sub_choice.startswith("🗑"):
                            delete_question(questions)
                        elif sub_choice.startswith("💾"):
                            save_json(filename, questions)
                            console.print("[green]✅ Questions saved.")

        elif choice.startswith("4"):
            while True:
                stats_choice = questionary.select(
                    "📊 Statistics",
                    choices=[
                        Choice("──────────── OPTIONS ────────────", disabled="✖"),
                        "📈 View results",
                        "♻️ Reset results",
                        "↩ Back",
                    ],
                ).ask()

                if stats_choice.startswith("📈"):
                    view_scores(score_file)
                elif stats_choice.startswith("♻️"):
                    reset_scores(score_file)
                elif stats_choice.startswith("↩"):
                    break

        elif choice.startswith("5"):
            while True:
                tools_choice = questionary.select(
                    "🧰 Tools - Choose an option:",
                    choices=[
                        "🧾 Convert CSV to JSON",
                        "📤 Export JSON to CSV",
                        "📄 Create CSV template",
                        "📄 Create JSON template",
                        "🌐 Import remote CSV/JSON",
                        "↩ Back",
                    ],
                ).ask()

                if tools_choice == "↩ Back":
                    break

                elif tools_choice.startswith("🧾"):
                    csv_dir = str(CSV_DIR)
                    if not os.path.exists(csv_dir):
                        os.makedirs(csv_dir)

                    csv_files = [f for f in os.listdir(csv_dir) if f.endswith(".csv")]

                    if not csv_files:
                        console.print("[red]⚠️ No CSV files available in 'csv' folder.")
                        continue

                    csv_choice = questionary.select(
                        "📄 Choose a CSV file to convert:", choices=csv_files + ["↩ Back"]
                    ).ask()

                    if csv_choice == "↩ Back":
                        continue

                    csv_path = os.path.join(csv_dir, csv_choice)
                    console.print(f"[green]✅ Selected file: {csv_path}")

                    # 🔽 1. Ask for a folder inside "categories/" for export
                    categories_root_dir = categories_root
                    folders = []

                    for dirpath, dirnames, _ in os.walk(categories_root_dir):
                        for d in dirnames:
                            folders.append(
                                os.path.relpath(os.path.join(dirpath, d), categories_root_dir)
                            )

                    folders = sorted(set(folders))

                    folder_choice = questionary.select(
                        "📁 Choose a folder under 'categories' to save the JSON:",
                        choices=folders + ["➕ Create new folder", "↩ Back"],
                    ).ask()

                    if folder_choice == "↩ Back":
                        continue

                    # 🔽 2. If user wants a new folder
                    if folder_choice == "➕ Create new folder":
                        new_folder = Prompt.ask("Enter new folder name (e.g., history/antiquity)")
                        folder_path = os.path.join(categories_root_dir, new_folder)
                        os.makedirs(folder_path, exist_ok=True)
                    else:
                        folder_path = os.path.join(categories_root_dir, folder_choice)

                    # 🔽 3. Convert CSV to JSON
                    csv_base = os.path.splitext(os.path.basename(csv_path))[0]
                    json_path = os.path.join(folder_path, f"{csv_base}.json")

                    with open(csv_path, newline="", encoding="utf-8") as csvfile:
                        reader = csv.DictReader(csvfile)
                        data_list = []

                        for row in reader:
                            qtype_ = row["type"].strip().lower()
                            question_text = row["question"].strip()
                            correct_ans = row["correct"].strip()
                            wrongs = row.get("wrong_answers", "").split(",")
                            left = [x.strip() for x in row.get("left", "").split("|") if x.strip()]
                            right = [
                                x.strip() for x in row.get("right", "").split("|") if x.strip()
                            ]
                            raw_answers = row.get("answers", "").strip()

                            if qtype_ == "multiple":
                                data_list.append(
                                    {
                                        "type": "multiple",
                                        "question": question_text,
                                        "correct": correct_ans,
                                        "wrong_answers": [a.strip() for a in wrongs if a.strip()],
                                    }
                                )
                            elif qtype_ == "truefalse":
                                data_list.append(
                                    {
                                        "type": "truefalse",
                                        "question": question_text,
                                        "correct": correct_ans,
                                        "wrong_answers": [wrongs[0].strip()] if wrongs else [],
                                    }
                                )
                            elif qtype_ == "fillin":
                                data_list.append(
                                    {
                                        "type": "fillin",
                                        "question": question_text,
                                        "correct": correct_ans,
                                        "wrong_answers": [],
                                    }
                                )
                            elif qtype_ == "match":
                                answers = {}
                                if raw_answers:
                                    for pair in raw_answers.split(","):
                                        if ":" in pair:
                                            parts = pair.strip().split(":")
                                            if len(parts) == 2:
                                                left_key, right_val = parts
                                                answers[left_key.strip()] = right_val.strip()

                                # ✅ Validate pairs
                                if not answers or len(answers) != len(left):
                                    console.print(
                                        f"[red]⚠️ Invalid pairs for question: {question_text}"
                                    )
                                    continue
                                data_list.append(
                                    {
                                        "type": "match",
                                        "question": question_text,
                                        "pairs": {"left": left, "right": right, "answers": answers},
                                    }
                                )

                    save_json(json_path, data_list)
                    console.print(
                        f"[green]✅ CSV converted to JSON and saved as: [bold]{json_path}[/]"
                    )

                elif tools_choice.startswith("📤"):
                    categories_dir = categories_root
                    csv_output_dir = str(CSV_DIR)
                    if not os.path.exists(csv_output_dir):
                        os.makedirs(csv_output_dir)
                    # Find all available .json files
                    json_files = []
                    for dirpath, _, filenames in os.walk(categories_dir):
                        for f in filenames:
                            if f.endswith(".json"):
                                rel_path = os.path.relpath(os.path.join(dirpath, f), categories_dir)
                                json_files.append(rel_path)

                    if not json_files:
                        console.print("[red]⚠️ No JSON files available.")
                        continue

                    json_choice = questionary.select(
                        "📁 Choose a JSON file to export to CSV:", choices=json_files + ["↩ Back"]
                    ).ask()

                    if json_choice == "↩ Back":
                        continue

                    json_path = os.path.join(categories_dir, json_choice)
                    csv_output_name = os.path.splitext(os.path.basename(json_path))[0] + ".csv"
                    csv_output_path = os.path.join(csv_output_dir, csv_output_name)

                    questions_list = get_questions(json_path)
                    if not questions_list:
                        console.print("[red]⚠️ File is empty or invalid.")
                        continue

                    with open(csv_output_path, mode="w", newline="", encoding="utf-8") as csvfile:
                        fieldnames = [
                            "type",
                            "question",
                            "correct",
                            "wrong_answers",
                            "left",
                            "right",
                            "answers",
                        ]
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()

                        for p in questions_list:
                            row = {
                                "type": p.get("type", ""),
                                "question": p.get("question", ""),
                                "correct": p.get("correct", ""),
                                "wrong_answers": ",".join(p.get("wrong_answers", []))
                                if "wrong_answers" in p
                                else "",
                                "left": "|".join(p.get("pairs", {}).get("left", []))
                                if p.get("type") == "match"
                                else "",
                                "right": "|".join(p.get("pairs", {}).get("right", []))
                                if p.get("type") == "match"
                                else "",
                                "answers": ",".join(
                                    [
                                        f"{k}:{v}"
                                        for k, v in p.get("pairs", {}).get("answers", {}).items()
                                    ]
                                )
                                if p.get("type") == "match"
                                else "",
                            }
                            writer.writerow(row)

                        console.print(
                            f"[green]✅ JSON successfully exported to CSV: [bold]{csv_output_path}[/]"
                        )

                elif tools_choice == "📄 Create CSV template":
                    folder_path = CSV_DIR
                    folder_path.mkdir(parents=True, exist_ok=True)
                    csv_path = folder_path / "example_template.csv"
                    template_path = csv_path

                    with open(template_path, mode="w", newline="", encoding="utf-8") as f:
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
                        writer.writerow(
                            ["truefalse", "The Sun is a star.", "True", "False", "", "", ""]
                        )
                        writer.writerow(
                            ["fillin", "The capital of Japan is ______.", "Tokyo", "", "", "", ""]
                        )
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
                    console.print(f"[green]✅ CSV template created at: [bold]{csv_path}[/]")
                elif tools_choice == "📄 Create JSON template":
                    folder_path = CATEGORIES_DIR / "templates"
                    folder_path.mkdir(parents=True, exist_ok=True)
                    json_path = folder_path / "example_template.json"

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

                    save_json(json_path, template)
                    console.print(f"[green]✅ JSON template created: [bold]{json_path}[/]")

                elif tools_choice == "🌐 Import remote CSV/JSON":
                    import_remote_file()

        elif choice.startswith("6"):
            show_help()

        elif choice.startswith("7"):
            confirm = questionary.confirm("Are you sure you want to exit?").ask()
            if confirm:
                console.print("[bold green]👋 Exit. Good luck with your studies!")
                break


if __name__ == "__main__":
    main()
