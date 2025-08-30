from typing import NamedTuple, List

class Command(NamedTuple):
    """Represents a LaTeX command and its processing logic."""
    name: str
    num_args: int
    prompt: str
    
    def accept(self, args: List[str]) -> str:
        """Logic for accepting the change."""
        if self.name == 'added':
            return args[0]
        if self.name == 'deleted':
            return ''
        if self.name == 'replaced':
            return args[1]
        if self.name in ['highlight', 'comment']:
            return args[0]
        return f"\\{self.name}{{{']['.join(args)}}}" # Default keep

    def reject(self, args: List[str]) -> str:
        """Logic for rejecting the change."""
        if self.name == 'added':
            return ''
        if self.name == 'deleted':
            return args[0]
        if self.name == 'replaced':
            return args[0]
        if self.name in ['highlight', 'comment']:
            return ''
        return f"\\{self.name}{{{']['.join(args)}}}" # Default keep

# Central registry of all supported commands
COMMAND_MAP = {
    'added': Command(
        name='added', num_args=1, prompt="Accept addition? [a/r/k] "
    ),
    'deleted': Command(
        name='deleted', num_args=1, prompt="Accept deletion? [a/r/k] "
    ),
    'replaced': Command(
        name='replaced', num_args=2, prompt="Accept replacement? [a/r/k] "
    ),
    'highlight': Command(
        name='highlight', num_args=1, prompt="Remove highlight? [r/k] "
    ),
    'comment': Command(
        name='comment', num_args=1, prompt="Remove comment? [r/k] "
    ),
}
