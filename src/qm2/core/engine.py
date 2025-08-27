import platform
import threading
import sys
import select
import random
import time
import string
from datetime import datetime

import questionary
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.prompt import Prompt

from qm2.utils.files import load_json, save_json

console = Console()

def input_with_timeout(prompt, timeout=60):
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
