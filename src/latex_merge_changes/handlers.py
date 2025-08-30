# src/latex_merge_changes/handlers.py
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from .commands import Command

class InteractionHandler(ABC):
    """Abstract base class for handling user decisions."""
    @abstractmethod
    def get_decision_for_change(self, command: Command, args: List[str]) -> str:
        """Return the user's decision ('a', 'r', or 'k')."""
        pass

class CliInteractionHandler(InteractionHandler):
    """Handles interaction via the command-line interface."""
    def get_decision_for_change(self, command: Command, args: List[str]) -> str:
        print("-" * 20)
        print(f"Found \\{command.name}:")
        if command.name == 'replaced':
            print(f"  Old: {args[0]}")
            print(f"  New: {args[1]}")
        else:
            print(f"  Content: {args[0]}")
        
        valid_actions = "ark" if command.num_args > 0 else "rk"
        prompt = command.prompt
        
        while True:
            action = input(prompt).lower()
            if action in valid_actions:
                return action
            print(f"Invalid input. Please enter one of [{'/'.join(valid_actions)}].")

class AutoInteractionHandler(InteractionHandler):
    """Handles decisions automatically based on predefined rules."""
    def __init__(self, accept_all: bool = False, reject_all: bool = False, remove_highlights: bool = False):
        self.rules: Dict[str, str] = {}
        if accept_all:
            self.rules.update({'added': 'a', 'deleted': 'a', 'replaced': 'a'})
        if reject_all:
            self.rules.update({'added': 'r', 'deleted': 'r', 'replaced': 'r'})
        if remove_highlights:
            self.rules.update({'highlight': 'r', 'comment': 'r'})
            
    def get_decision_for_change(self, command: Command, args: List[str]) -> str:
        # Return the predefined action, or 'keep' if no rule applies
        return self.rules.get(command.name, 'k')
