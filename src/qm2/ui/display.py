from __future__ import annotations

import importlib.resources as pkg_resources
import json

import questionary
import qm2
from rich.console import Console
from rich.panel import Panel

console = Console()


def show_logo() -> None:
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


def show_help() -> None:
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
    
