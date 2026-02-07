import re
import tkinter as tk

from markdown_text import MarkdownText

CONFIG_FILE = "replacements.json"

replacements = {
    "simple": {
        " »": "»",
        "« ": "«",
        "–": "—",
        " - ": " — ",
        " -": " — ",
        "- ": " — ",
        ". .": "..",
        "..": "...",
        " .": ".",
        " ,": ",",
        " !": "!",
        " ?": "?",
        " …": "…",
        "* ": "*",
        "_ ": "_",
        ' ".\n': '".\n',
        '. "\n': '."\n',
        ' "!\n': '"!\n',
        '! "\n': '!"\n',
        ' "?\n': '"?\n',
        '? "\n': '?"\n',
        " *": "*",
        ", #": " #",
        ".…": "…",
    },
    "regex": {
        "\\.{2,}": "…",
        "…{2,}": "…",
        " {2,}": " ",
        "…(?!\\s)": "… ",
        "^\\. ": "",
        "(?<!\n)\n(?!\n|#|\\*)": "\n\n",
    },
}


class TextCorrector:
    def __init__(self, text_frame: MarkdownText):
        self.text_frame = text_frame

    def correct_text(self):
        text = self.text_frame.get("1.0", tk.END).strip()
        text = self.normalize_text(text)
        self.text_frame.delete("1.0", tk.END)
        self.text_frame.insert(tk.END, text)
        self.text_frame.highlight_markdown()

    def normalize_text(self, content: str) -> str:
        # Простые замены
        for old, new in replacements["simple"].items():
            content = content.replace(old, new)

        # Замены через регулярки
        for pattern, repl in replacements["regex"].items():
            content = re.sub(pattern, repl, content, flags=re.MULTILINE)

        # Убираем пробелы перед \n
        content = re.sub(r" \n", "\n", content)
        content = re.sub(r"\n #", "\n#", content)
        content = re.sub(r"\n %", "\n%", content)
        content = re.sub(r"\n\n%", "\n%", content)

        # Гарантируем ровно один пробел в начале строки
        content = self.fix_line_start_spaces(content)

        return content.strip() + "\n"

    def fix_line_start_spaces(self, content: str) -> str:
        new_lines = []
        for line in content.splitlines():
            stripped = line.lstrip()
            if line.startswith(("#", "%")) or stripped.startswith("*"):
                # служебные строки и списки остаются как есть
                new_lines.append(line)
            else:
                # убираем лишние пробелы и добавляем ровно один
                if stripped:
                    line = " " + stripped
                else:
                    line = stripped
                new_lines.append(line)
        return "\n".join(new_lines)
