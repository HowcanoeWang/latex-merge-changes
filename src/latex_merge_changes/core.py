# src/latex_merge_changes/core.py
import re
from typing import List, Tuple, Optional
from .commands import COMMAND_MAP, Command
from .handlers import InteractionHandler

def _find_balanced_braces(text: str, start_pos: int) -> Tuple[Optional[str], int]:
    """Finds content within the first balanced curly braces starting from start_pos."""
    if start_pos >= len(text) or text[start_pos] != '{':
        return None, -1
    
    balance = 0
    match_start = start_pos + 1
    for i in range(start_pos, len(text)):
        if text[i] == '{':
            balance += 1
        elif text[i] == '}':
            balance -= 1
        
        if balance == 0:
            return text[match_start:i], i + 1
    return None, -1

class ChangeProcessor:
    """
    Processes a LaTeX string to merge changes defined by the 'changes' package.
    This class is UI-agnostic and operates solely on strings.
    """
    def __init__(self, handler: InteractionHandler):
        self.handler = handler
        # Regex to find any of the supported commands, ignoring optional args for now
        command_names = '|'.join(COMMAND_MAP.keys())
        self.command_regex = re.compile(r'\\(' + command_names + r')(\s*\[.*?\])*')

    def process(self, text: str) -> str:
        """
        Iteratively finds and processes all changes in the text.
        
        Returns:
            The fully processed text as a string.
        """
        processed_text = text
        while True:
            match = self.command_regex.search(processed_text)
            if not match:
                break
            
            command_name = match.group(1)
            command = COMMAND_MAP[command_name]
            
            # Find arguments
            args_start_pos = match.end()
            args: List[str] = []
            current_pos = args_start_pos
            
            for _ in range(command.num_args):
                content, next_pos = _find_balanced_braces(processed_text, current_pos)
                if content is None:
                    # Malformed command, skip it
                    current_pos = -1
                    break
                args.append(content)
                current_pos = next_pos
            
            if current_pos == -1: # Parsing failed
                # To avoid an infinite loop, we advance past the broken command
                processed_text = processed_text[:match.start()] + processed_text[match.end():]
                print(f"Warning: Malformed command '\\{command_name}' at position {match.start()}. Skipping.")
                continue

            command_end_pos = current_pos
            
            # Get decision from the handler
            action = self.handler.get_decision_for_change(command, args)
            
            # Apply transformation
            replacement = ""
            if action == 'a':
                replacement = command.accept(args)
            elif action == 'r':
                replacement = command.reject(args)
            elif action == 'k':
                # Keep the original text of the command
                replacement = processed_text[match.start():command_end_pos]

            processed_text = processed_text[:match.start()] + replacement + processed_text[command_end_pos:]
        
        return processed_text
