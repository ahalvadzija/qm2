import os

from rich.console import Console
from rich.table import Table
from rich import box
from rich.prompt import Prompt
import questionary

from qm2.utils.files import load_json, save_json

console = Console()
questions_cache = {}

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

