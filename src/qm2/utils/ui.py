from __future__ import annotations
import questionary
from questionary import Choice

def select_with_pagination(prompt_text: str, choices: list[str], page_size: int = 10) -> str | None:
    """Universal helper for pagination - matches Name's call signature."""
    if not choices:
        return None
        
    page = 0
    actual_items = [c for c in choices if c != "↩ Back"]
    total_pages = (len(actual_items) + page_size - 1) // page_size
    
    while True:
        start = page * page_size
        end = min(start + page_size, len(actual_items))
        
        current_batch = actual_items[start:end]
        ui_choices = []
        
        if page > 0:
            ui_choices.append(Choice("⟨ Previous Page", value="prev"))
            
        ui_choices.extend(current_batch)
        
        if page < total_pages - 1:
            ui_choices.append(Choice("Next Page ⟩", value="next"))
            
        ui_choices.append(Choice("↩ Back", value="back"))
        
        selection = questionary.select(
            f"{prompt_text} (Page {page + 1}/{total_pages})",
            choices=ui_choices
        ).ask()
        
        if selection == "next":
            page += 1
        elif selection == "prev":
            page -= 1
        elif selection == "back" or selection is None:
            return "↩ Back"
        else:
            return selection