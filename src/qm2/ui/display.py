from __future__ import annotations

import importlib.resources as pkg_resources
import json
import questionary
import qm2
from rich.console import Console
from rich.panel import Panel
import importlib.metadata

# Import the update check function from your utility module
from qm2.utils import check_for_updates
# Automatically retrieve the version from package metadata
try:
    __version__ = importlib.metadata.version("qm2")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

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
    """Displays the help menu with an option to check for updates."""
    while True:
        # English: Clear and show logo so the Help menu always looks consistent
        console.clear()
        show_logo()
        
        action = questionary.select(
            "Help - Choose an option:",
            choices=[
                "📖 View Instructions",
                "🔄 Check for Updates",
                "↩ Back"
            ]
        ).ask()

        # English: Clear before returning to main so Main Menu can draw its own logo
        if action is None or action == "↩ Back":
            console.clear()
            return 

        if action == "📖 View Instructions":
            console.clear()
            # English: We show the logo even here to keep the branding
            show_logo() 
            try:
                with pkg_resources.files(qm2).joinpath("help.json").open("r", encoding="utf-8") as f:
                    data = json.load(f)
                
                console.rule("[bold cyan]🆘 Help Instructions")
                for line in data.get("instructions", []):
                    console.print(f"[white]- {line}")
                
                questionary.select("", choices=["↩ Back to Help Menu"]).ask()
                # English: After this, the loop restarts, clears, and shows logo + menu
            except Exception:
                console.print("[red]⚠️ Help instructions unavailable.")
                questionary.select("", choices=["↩ Back"]).ask()

        elif action == "🔄 Check for Updates":
            console.clear()
            show_logo()
            
            with console.status("[yellow]Checking GitHub for updates...", spinner="dots"):
                update_available, latest_v = check_for_updates()
            
            console.print() 

            if update_available is True:
                console.print(Panel(
                    f"[bold green]🚀 New version available: v{latest_v}\n"
                    f"[white]Current version: v{__version__}\n\n"
                    f"[bold yellow]To update, run: pip install --upgrade qm2",
                    title="Update Found",
                    border_style="green"
                ))
            elif update_available is False:
                console.print(f"[green]✅ You are up to date! (v{__version__})")
            else:
                console.print("[red]❌ Connection error. Please check your internet or GitHub status.")
            
            console.print()
            questionary.select("", choices=["↩ Back to Help Menu"]).ask()