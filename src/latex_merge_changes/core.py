import re
import sys
from copy import deepcopy
from typing import List, Tuple, Optional, Dict, NamedTuple
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

class FoundChange(NamedTuple):
    """Represents a single 'changes' command found in the source text."""
    command: Command
    args: Tuple[str, ...] 
    span: Tuple[int, int]  # (start, end) offset in the original text
    line: int
    col: int

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

    def _get_line_col_from_offset(self, text: str, offset: int) -> Tuple[int, int]:
        """Calculates the 1-based line and column number for a given character offset."""
        if offset > len(text):
            return -1, -1
        line_start = text.rfind('\n', 0, offset) + 1
        col = offset - line_start + 1
        line = text.count('\n', 0, line_start) + 1
        return line, col
    
    def _report_malformed_command(self, text: str, command_name: str, line: int, col: int, message: str,) -> None:
        """Formats and prints a detailed error message for a malformed command."""
        # 1. Extract the line where the error occurred
        lines = text.splitlines()
        # Defensive check in case the line number is out of bounds
        error_line = lines[line - 1] if 0 < line <= len(lines) else ""
        
        # 2. Define the context window around the error column
        context_radius = 50
        col_index = col - 1  # Convert 1-based col to 0-based index
        
        start = max(0, col_index - context_radius)
        end = min(len(error_line), col_index + context_radius)
        
        # 3. Add ellipses "..." if the snippet is truncated
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(error_line) else ""
        
        context_snippet = error_line[start:end]
        
        # 4. Calculate the position for the indicator arrow
        indicator_pos = len(prefix) + (col_index - start)
        
        # 5. Print the formatted, multi-line error message
        print(f"Warning: Malformed command '\\{command_name}' at line {line}, column {col}.\n"
              f"  {prefix}{context_snippet}{suffix}\n"
              f"  {' ' * indicator_pos}^\n"
              f"{message}", file=sys.stderr)

    def process(self, text: str) -> str:
        """
        Processes all changes in the text by discovering, deciding, and then building.

        1. FoundChange 数据类:

            我们创建了一个 NamedTuple（行为类似 dataclass）来清晰地组织每个找到的命令的信息。
            最关键的是 span: Tuple[int, int]，它存储了命令在 原始文本 中的开始和结束偏移量。
            我们还在这里存储了解析好的 line 和 col，以备将来使用。

        2. 发现阶段:

            我们不再使用 while True 和 re.search 的组合，而是改用 re.finditer(text)。finditer 是专门为遍历字符串中所有不重叠匹配而设计的，它更简洁、更高效。
            这个循环的唯一目的就是 查找和解析。它在 原始的、不可变的 text 上操作。
            如果发现格式错误的命令，_get_line_col_from_offset 会在 text 上计算位置，保证 100% 准确。
            所有成功解析的命令都被存入 found_changes 列表。
        
        3. 决策阶段:

            我们遍历 found_changes 列表，为每个命令调用 handler 来获取用户决策（a, r, k）。
            这些决策被存储在一个字典 decisions 中，键是 FoundChange 对象，值是决策字符串。
        
        4. 构建阶段:

            这是最精妙的部分。我们使用 reversed(found_changes) 来 从后往前 遍历变更列表。
            为什么从后往前？ 想象一下你有两个变更，一个在第 10 个字符，一个在第 50 个字符。如果你先处理第 10 个字符处的变更，比如删除了 5 个字符，那么原来在第 50 个字符的变更现在就移动到了第 45 个字符。你之前存储的 span 就失效了。
            但是，如果你先处理第 50 个字符处的变更，无论你是删除还是增加内容，它都 不会影响 第 10 个字符的位置。
            通过从后往前应用变更，我们确保了每个 change.span 在轮到它被处理时，始终是相对于当前 processed_text 的正确位置。
            注意，当 action == 'k' (keep) 时，我们直接 continue，因为我们初始的 processed_text 就是原始文本，它已经包含了标记，所以无需任何操作。
        """

        ###################################
        # Find all changes and store them #
        ###################################
        found_changes: List[FoundChange] = []
        # 使用 finditer 在不可变的原始文本上查找所有匹配项
        for match in self.command_regex.finditer(text):
            command_name = match.group(1)
            command = COMMAND_MAP[command_name]
            
            # 解析参数
            args: List[str] = []
            current_pos = match.end()
            for _ in range(command.num_args):
                content, next_pos = _find_balanced_braces(text, current_pos)
                if content is None:
                    current_pos = -1
                    break
                args.append(content)
                current_pos = next_pos

            # 如果命令格式错误，打印基于原始文本的准确位置并跳过
            if current_pos == -1:
                line, col = self._get_line_col_from_offset(text, match.start())
                self._report_malformed_command(
                    text=text,
                    command_name=command_name,
                    line=line,
                    col=col,
                    message="Could not find matching braces. Skipping."
                )
                continue

            # 存储找到的变更及其在原始文本中的位置信息
            line, col = self._get_line_col_from_offset(text, match.start())
            change = FoundChange(
                command=command,
                args=tuple(args),
                span=(match.start(), current_pos),
                line=line,
                col=col
            )
            found_changes.append(change)

        #########################################
        # Ask user's decisions for each changes #
        #########################################
        decisions: Dict[FoundChange, str] = {}
        for change in found_changes:
            # 注意：这里我们不再传递 change.line 和 change.col 给 get_decision_for_change
            # 因为 handler 的设计是独立的。如果需要，可以修改 handler 的接口。
            action = self.handler.get_decision_for_change(change.command, change.args)
            decisions[change] = action

        ###################################################
        # Replace the final manuscript from back to front #
        ###################################################
        # 从后往前处理可以避免替换操作影响前面命令的索引
        processed_text = text
        for change in reversed(found_changes):
            action = decisions[change]
            slice_start, slice_end = change.span

            replacement = ""
            if action == 'a': # Accept
                replacement = change.command.accept(change.args)
                # 检查是否需要删除整行（逻辑与之前相同，但作用于原始文本）
                if change.command.name == 'deleted':
                    line_start = text.rfind('\n', 0, slice_start) + 1
                    line_end_search_pos = text.find('\n', slice_end)
                    line_end = line_end_search_pos if line_end_search_pos != -1 else len(text)
                    
                    pre_command_content = text[line_start:slice_start]
                    post_command_content = text[slice_end:line_end]

                    if not pre_command_content.strip() and not post_command_content.strip():
                        slice_start = line_start
                        if line_end_search_pos != -1:
                            slice_end = line_end + 1
                        else:
                            slice_end = line_end
            
            elif action == 'r': # Reject
                replacement = change.command.reject(change.args)
            
            elif action == 'k': # Keep
                # 如果是 'keep'，我们什么都不做，因为原始文本已经包含了标记
                continue
            
            # 执行替换
            processed_text = processed_text[:slice_start] + replacement + processed_text[slice_end:]
        return processed_text