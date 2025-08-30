# LaTeX-merge-changes

A modern, command-line tool to interactively or automatically process LaTeX documents that use the `changes` package. This project serves as an updated and more robust Python-based alternative to the original `pyMergeChanges.py` script.

## Key Features

*   **Interactive Mode**: Prompts you for each change (`\added`, `\deleted`, `\replaced`, etc.), allowing you to accept, reject, or keep the markup for each one individually.
*   **Automatic Modes**:
    *   `--accept-all`: Automatically accepts all changes in the document.
    *   `--reject-all`: Automatically rejects all changes.
    *   `--remove-highlights`: Removes all highlights and comments without accepting or rejecting.
*   **Smart Line Handling**: Correctly removes entire lines for `\deleted{...}` commands that occupy a full line, preventing unwanted blank lines in your output.
*   **Standard CLI Interface**: Supports common flags like `--help` and `--version`.
*   **Easy Installation**: Can be installed easily using modern Python packaging tools like `pip` or `uv`.

## Installation

### Using `uv` (Recommended)

[uv](https://github.com/astral-sh/uv) is an extremely fast Python package installer and resolver.

```bash
uv tool install latex-merge-changes
```

### Using `pip`

You can also use the standard Python package installer, `pip`.

```bash
pip install latex-merge-changes
```

### For Developers

If you want to contribute to the project, you can install it in editable mode:

```bash
# 1. Clone the repository
git clone https://github.com/your-username/latex-merge-changes.git
cd latex-merge-changes

# 2. Install in editable mode using uv or pip
uv tool install -e .
```

<details>
    <summary>Project Structures</summary>

    ```plaintext
    latex-merge-changes/
    ├── src/
    │   └── latex_merge_changes/
    │       ├── __init__.py
    │       ├── __main__.py
    │       ├── cli.py              # 命令行界面逻辑 (argparse, 文件 I/O)
    │       ├── core.py             # 核心处理逻辑，完全与 UI 解耦
    │       ├── handlers.py         # 交互处理器 (CLI 交互, 自动处理)
    │       └── commands.py         # 定义所有 LaTeX 命令及其行为
    ├── tests/
    │   └── test_core.py            # 针对 core.py 的单元测试
    ├── pyproject.toml              # 项目元数据和构建配置 (替代 setup.py)
    ├── README.md                   # 项目说明
    └── LICENSE                     # 许可证文件 (GPLv3)
    ```

    **Separation of Concerns**:

    `__init__.py`: 包初始化文件, 用于暴露公共 API
    `__main__.py`: 允许通过 python -m latex_merge_changes 运行
    `core.py`: 这是项目的大脑。它只负责解析字符串和应用转换。它不知道文件系统，也不依赖 print() 或 input()。这是为未来 UI 预留的关键接口。
    `cli.py`: 这是项目的“外壳”。它负责解析命令行参数、读写文件，并将 core 模块与用户连接起来。
    `handlers.py`: 这是 core 和 cli 之间的桥梁。core 模块在需要用户决策时，会调用一个“处理器”(Handler)，这个处理器决定了如何获取决策（是从命令行 input()，还是根据 -a/-r 标志自动决定）。
    `commands.py`: 将每个 LaTeX 命令 (\added, \deleted 等) 的具体逻辑封装起来，使添加新命令变得极其简单。
    
</details>

## Usage

The tool follows a standard command-line structure.

### Basic Syntax

```bash
latex-merge-changes [OPTIONS] INFILE OUTFILE
```

*   **`INFILE`**: The path to your source `.tex` file containing `changes` markup.
*   **`OUTFILE`**: The path where the processed `.tex` file will be saved.

### Options

| Short | Long                | Description                                                                 |
| :---- | :------------------ | :-------------------------------------------------------------------------- |
| `-h`  | `--help`            | Show the help message and exit.                                             |
| `-v`  | `--version`         | Show the program's version number and exit.                                 |
| `-a`  | `--accept-all`      | Accept all changes automatically without prompting.                         |
| `-r`  | `--reject-all`      | Reject all changes automatically without prompting.                         |
| `-rh` | `--remove-highlights`| Remove all highlights and comments automatically without prompting.         |

**Note**: The automatic modes (`-a`, `-r`, `-rh`) are mutually exclusive. If you provide more than one, the tool will prioritize one based on implementation details. You should only use one at a time.

### Examples

Let's say you have a file named `document.tex` with the following content:

**`document.tex`**
```latex
\documentclass{article}
\usepackage[final]{changes} % Using final option to show changes

\begin{document}

This is an \added{excellent} example of the tool.

\deleted{This entire line will be removed.}

We can also \replaced{demonstrate}{show} how replacements work.

\end{document}
```

#### 1. Interactive Mode

Run the tool without any automatic flags to enter interactive mode.

```bash
$ latex-merge-changes document.tex final_document.tex
```

Your terminal will prompt you for each change:
```
Found command: \added
  - Original: {}
  - Changed:  {excellent}
Accept (a), Reject (r), or Keep markup (k)? a

Found command: \deleted
  - Original: {This entire line will be removed.}
  - Changed:  {}
Accept (a), Reject (r), or Keep markup (k)? a

Found command: \replaced
  - Original: {demonstrate}
  - Changed:  {show}
Accept (a), Reject (r), or Keep markup (k)? r
...
Successfully processed file and saved result to 'final_document.tex'
```

#### 2. Automatic Mode (Accept All)

To quickly accept all changes and generate a clean final version:

```bash
latex-merge-changes --accept-all document.tex final_document.tex
```

This will run without any prompts. The resulting `final_document.tex` will look like this:

**`final_document.tex`**
```latex
\documentclass{article}
\usepackage[final]{changes} % Using final option to show changes

\begin{document}

This is an excellent example of the tool.

We can also demonstrate how replacements work.

\end{document}
```
Notice how the deleted line was removed completely without leaving an empty line.

## License
This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.