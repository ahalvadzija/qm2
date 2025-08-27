import os
import re
import requests  # noqa: F401
from pathlib import Path
import questionary
from questionary import Choice
from rich.console import Console
from rich.prompt import Prompt

from qm2 import paths
from qm2.core.categories import create_new_category, delete_category, categories_root_dir, rename_category
from qm2.core.import_export import csv_to_json as core_csv_to_json, json_to_csv as core_json_to_csv, download_remote as core_download_remote
from qm2.core.templates import create_csv_template, create_json_template
from qm2.core.engine import quiz_session, flashcards_mode

from qm2.core.categories import (
    get_categories,
    categories_add,
    delete_json_quiz_file,
    select_category, 
)

from qm2.core.questions import (
    get_questions,
    show_questions_paginated,
    edit_question,
    edit_question_by_index,
    delete_question_by_index,
    delete_question,
    create_question,  
)

from qm2.core.scores import (
    view_scores,
    reset_scores,
)

from qm2.utils import save_json
from qm2.ui.display import show_logo, show_help

console = Console()

# Caching and helpers for performance on large datasets
questions_cache = {}  # path -> {"mtime": float, "data": list}
cache_cleanup_counter = 0  # counter for periodic cache cleanup


SAFE_NAME = re.compile(r"^[a-zA-Z0-9._-]{1,64}$")


def import_remote_file():
    """
    Tanki UI wrapper koji:
    - pita za URL
    - pita kako da se fajl zove (bez ekstenzije)
    - snima u ./categories/<name>.json ili .csv na osnovu URL-a
    - pita za overwrite ako fajl već postoji
    - pozove categories_add(...) i ispiše poruku
    """
    url = Prompt.ask("🌐 Enter CSV/JSON URL").strip()
    base = Prompt.ask("💾 Save as (file name without extension)").strip()

    if not base or not SAFE_NAME.match(base):
        console.print("[red]⚠️ Invalid file name.")
        return

    # heuristika ekstenzije po URL-u
    ext = "json" if url.lower().endswith(".json") else "csv"
    dest_dir = Path(categories_root_dir())
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{base}.{ext}"

    overwrite = True
    if dest_path.exists():
        overwrite = questionary.confirm(f"⚠️ '{dest_path.name}' exists. Overwrite?").ask()

    try:
        saved = core_download_remote(url, dest_path, overwrite=bool(overwrite))
    except FileExistsError:
        console.print("[yellow]↩ Canceled.")
        return
    except Exception as e:
        console.print(f"[red]⚠️ Download failed: {e}")
        return

    categories_add(str(saved))
    console.print(f"[green]✅ File downloaded and saved as:\n{saved}")


def main():
    score_file = str(paths.SCORES_FILE)

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
                            create_new_category(categories_root_dir())
                        elif opt.startswith("✏️"):
                            rename_category(categories_root_dir())
                        elif opt == "🗑️ Delete JSON quiz file":
                            delete_json_quiz_file(categories_root_dir())
                        elif opt == "🗑️ Delete category":
                            delete_category(categories_root_dir())
                        elif opt.startswith("↩"):
                            break

                else:
                    # Manage questions for selected category
                    filename = os.path.join(categories_root_dir(), selection)
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
                    csv_dir = os.path.abspath("csv")  # #local csv
                    os.makedirs(csv_dir, exist_ok=True)
                    csv_files = [f for f in os.listdir(csv_dir) if f.endswith(".csv")]
                    if not csv_files:
                        console.print("[red]⚠️ No CSV files found.")
                        continue

                    csv_choice = questionary.select("📄 Choose a CSV file to convert:", choices=csv_files + ["↩ Back"]).ask()
                    if csv_choice == "↩ Back":
                        continue        

                    # where save JSON – sub ./categories/ (same model as tests)
                    cats_root = categories_root_dir()
                    folder_choice = Prompt.ask("Folder under 'categories' (e.g., history/antiquity)", default="").strip()
                    folder_path = os.path.join(cats_root, folder_choice) if folder_choice else cats_root
                    os.makedirs(folder_path, exist_ok=True)

                    base = os.path.splitext(os.path.basename(csv_choice))[0]
                    src_csv = os.path.join(csv_dir, csv_choice)
                    out_json = os.path.join(folder_path, f"{base}.json")

                    n = core_csv_to_json(Path(src_csv), Path(out_json))
                    if n:
                        # refresh cache and report
                        categories_add(out_json)
                        console.print(f"[green]✅ CSV converted to JSON and saved as: [bold]{out_json}[/]")
                    else:
                        console.print("[yellow]⚠️ No rows converted.")

                elif tools_choice.startswith("📤"):
                    cats = categories_root_dir()
                    # find all JSON files
                    json_files = []
                    for dirpath, _, filenames in os.walk(cats):
                        for f in filenames:
                            if f.endswith(".json"):
                                json_files.append(os.path.relpath(os.path.join(dirpath, f), cats))
                    if not json_files:
                        console.print("[red]⚠️ No JSON files available.")
                        continue
                    
                    rel_choice = questionary.select("📁 Choose a JSON file to export to CSV:", choices=json_files + ["↩ Back"]).ask()
                    if rel_choice == "↩ Back":
                        continue
                    
                    src_json = os.path.join(cats, rel_choice)
                    csv_dir = os.path.abspath("csv")  # drži se lokalnog ./csv
                    os.makedirs(csv_dir, exist_ok=True)
                    csv_name = os.path.splitext(os.path.basename(src_json))[0] + ".csv"
                    out_csv = os.path.join(csv_dir, csv_name)

                    n = core_json_to_csv(Path(src_json), Path(out_csv))
                    if n:
                        console.print(f"[green]✅ JSON successfully exported to CSV: [bold]{out_csv}[/]")
                    else:
                        console.print("[yellow]⚠️ No rows exported.")

                elif tools_choice == "📄 Create CSV template":
                    path = create_csv_template()
                    console.print(f"[green]✅ CSV template created at: [bold]{path}[/]")
                    
                elif tools_choice == "📄 Create JSON template":
                    path = create_json_template()
                    console.print(f"[green]✅ JSON template created: [bold]{path}[/]")

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
