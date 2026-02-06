import re
import tkinter as tk
from tkinter import font


class MarkdownText(tk.Text):
    """Кастомный Text виджет с подсветкой Markdown"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_font = font.Font(family="Monospace", size=10)
        self.config(font=self.base_font)

        self.configure(undo=True, maxundo=20)
        self.configure_tags()
        self.configure_bindings()
        self._update_job = None

    def configure_bindings(self):
        self.bind("<Control-b>", lambda e: self.format_line("bold"))
        self.bind("<Control-i>", lambda e: self.format_line("italic"))
        self.bind("<Control-Key-1>", lambda e: self.format_line("h1"))
        self.bind("<Control-Key-2>", lambda e: self.format_line("h2"))
        self.bind("<Control-Key-3>", lambda e: self.format_line("h3"))
        self.bind("<Control-Key-4>", lambda e: self.format_line("h4"))
        self.bind("<Control-Key-5>", lambda e: self.format_line("h5"))

        self.bind("<Control-plus>", lambda e: self.zoom(1))
        self.bind("<Control-minus>", lambda e: self.zoom(-1))
        self.bind("<Control-0>", lambda e: self.base_font.configure(size=12))

        self.bind("<Control-BackSpace>", self.delete_word_left)
        self.bind("<Control-Delete>", self.delete_word_right)

    def delete_word_left(self, event):
        index = self.index("insert")
        prev_index = self.search(r"\W", index, backwards=True, regexp=True)
        if not prev_index:
            prev_index = "1.0"
        self.delete(prev_index, index)
        return "break"

    def delete_word_right(self, event):
        index = self.index("insert")
        next_index = self.search(r"\W", index, regexp=True)
        if not next_index:
            next_index = tk.END
        self.delete(index, next_index)
        return "break"

    def zoom(self, delta):
        size = self.base_font.actual("size") + delta
        if size >= 8:
            self.base_font.configure(size=size)

    def schedule_highlight_markdown(self):
        if self._update_job:
            self.after_cancel(self._update_job)
        self._update_job = self.after(300, self.highlight_markdown)

    def configure_tags(self):
        """Настройка стилей для Markdown-элементов"""
        # Информация о файле
        self.tag_config(
            "info",
            font=font.Font(
                family=self.base_font.actual("family"),
                size=self.base_font.actual("size"),
                weight="bold",
                slant="italic",
            ),
            foreground="#4B0082",
        )
        self.tag_config(
            "tag",
            font=font.Font(
                family=self.base_font.actual("family"),
                size=self.base_font.actual("size") + 1,
                weight="bold",
                slant="italic",
            ),
            foreground="#3dba0b",
        )
        # Заголовки
        self.tag_config(
            "h1",
            font=font.Font(
                family=self.base_font.actual("family"),
                size=self.base_font.actual("size") + 6,
                weight="bold",
            ),
            foreground="#2b6cb0",
        )
        self.tag_config(
            "h2",
            font=font.Font(
                family=self.base_font.actual("family"),
                size=self.base_font.actual("size") + 4,
                weight="bold",
            ),
            foreground="#2c5282",
        )
        self.tag_config(
            "h3",
            font=font.Font(
                family=self.base_font.actual("family"),
                size=self.base_font.actual("size") + 2,
                weight="bold",
            ),
            foreground="#3182ce",
        )
        self.tag_config(
            "h4",
            font=font.Font(
                family=self.base_font.actual("family"),
                size=self.base_font.actual("size"),
                weight="bold",
            ),
            foreground="#3182ce",
        )
        self.tag_config(
            "h5",
            font=font.Font(
                family=self.base_font.actual("family"),
                size=self.base_font.actual("size") - 1,
                weight="bold",
            ),
            foreground="#3182ce",
        )
        # Форматирование текста
        self.tag_config(
            "bold",
            font=font.Font(
                family=self.base_font.actual("family"),
                size=self.base_font.actual("size"),
                weight="bold",
            ),
        )
        self.tag_config(
            "italic",
            font=font.Font(
                family=self.base_font.actual("family"),
                size=self.base_font.actual("size"),
                slant="italic",
            ),
        )
        self.tag_config(
            "bold_italic",
            font=font.Font(
                family=self.base_font.actual("family"),
                size=self.base_font.actual("size"),
                weight="bold",
                slant="italic",
            ),
        )
        # Код и ссылки
        self.tag_config(
            "code",
            font=("Courier", self.base_font.actual("size")),
            background="#f0f0f0",
        )
        self.tag_config(
            "link",
            font=font.Font(
                family=self.base_font.actual("family"),
                size=self.base_font.actual("size"),
                weight="normal",
            ),
            foreground="#4299e1",
            underline=True,
        )
        # Списки
        self.tag_config(
            "list",
            font=font.Font(
                family=self.base_font.actual("family"),
                size=self.base_font.actual("size"),
                weight="normal",
            ),
            lmargin2=20,
            spacing1=5,
        )

    def highlight_markdown(self, event=None):
        """Подсветка Markdown-синтаксиса"""
        # Очистка всех тегов перед повторной обработкой
        for tag in self.tag_names():
            if tag in (
                "info",
                "tag",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "bold",
                "italic",
                "bold_italic",
                "code",
                "link",
                "list",
            ):
                self.tag_remove(tag, "1.0", tk.END)

        text = self.get("1.0", tk.END)
        lines = text.split("\n")

        # Обрабатываем построчно для многострочных паттернов
        for i, line in enumerate(lines, 1):
            line_start = f"{i}.0"
            line_end = f"{i}.end"

            # Заголовки
            if re.match(r"^%\s", line):
                self.tag_add("info", line_start, line_end)
            elif re.match(r"^#\s", line):
                self.tag_add("h1", line_start, line_end)
            elif re.match(r"^##\s", line):
                self.tag_add("h2", line_start, line_end)
            elif re.match(r"^###\s", line):
                self.tag_add("h3", line_start, line_end)
            elif re.match(r"^####\s", line):
                self.tag_add("h4", line_start, line_end)
            elif re.match(r"^#####\s", line):
                self.tag_add("h5", line_start, line_end)

            # Списки
            if re.match(r"^[\*\-\+]\s", line):
                self.tag_add("list", line_start, line_end)

        # Обрабатываем встроенные элементы (не зависящие от строк)
        self.highlight_pattern(r"\*\*\*(.+?)\*\*\*", "bold_italic")
        self.highlight_pattern(r"#([a-zA-Zа-яА-ЯёЁ_-]+?\s)", "tag")
        self.highlight_pattern(r"\*\*(.+?)\*\*", "bold", exclude_tags=["bold_italic"])
        self.highlight_pattern(
            r"\*(.+?)\*", "italic", exclude_tags=["bold", "bold_italic"]
        )
        self.highlight_pattern(r"`(.+?)`", "code")
        self.highlight_pattern(r"\[(.+?)\]\((.+?)\)", "link")

    def on_text_modified(self, event=None):
        if not self.edit_modified():
            return

        self.edit_modified(False)

        line = int(self.index("insert").split(".")[0])
        last = int(self.index("end-1c").split(".")[0])

        for ln in (line - 2, line, line + 2):
            if 1 <= ln <= last:
                self.highlight_line(ln)

    def highlight_line(self, line_number):
        # Обрабатываем построчно для многострочных паттернов
        line_start = f"{line_number}.0"
        line_end = f"{line_number}.end"
        text = self.get(line_start, line_end)

        # Очистка всех тегов перед повторной обработкой
        for tag in self.tag_names():
            if tag in (
                "info",
                "tag",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "bold",
                "italic",
                "bold_italic",
                "code",
                "link",
                "list",
            ):
                self.tag_remove(tag, line_start, line_end)

        # Заголовки
        if re.match(r"^%\s", text):
            self.tag_add("info", line_start, line_end)
        elif re.match(r"^#\s", text):
            self.tag_add("h1", line_start, line_end)
        elif re.match(r"^##\s", text):
            self.tag_add("h2", line_start, line_end)
        elif re.match(r"^###\s", text):
            self.tag_add("h3", line_start, line_end)
        elif re.match(r"^####\s", text):
            self.tag_add("h4", line_start, line_end)
        elif re.match(r"^#####\s", text):
            self.tag_add("h5", line_start, line_end)

        # Списки
        if re.match(r"^[\*\-\+]\s", text):
            self.tag_add("list", line_start, line_end)

        # Обрабатываем встроенные элементы (не зависящие от строк)
        self.highlight_pattern(
            r"\*\*\*(.+?)\*\*\*", "bold_italic", line_start, line_end
        )
        self.highlight_pattern(
            r"\*\*(.+?)\*\*",
            "bold",
            line_start,
            line_end,
            exclude_tags=["bold_italic"],
        )
        self.highlight_pattern(
            r"\*(.+?)\*",
            "italic",
            line_start,
            line_end,
            exclude_tags=["bold", "bold_italic"],
        )
        self.highlight_pattern(r"#([a-zA-Zа-яА-ЯёЁ_-]+?\s)", "tag")
        self.highlight_pattern(r"`(.+?)`", "code", line_start, line_end)
        self.highlight_pattern(r"\[(.+?)\]\((.+?)\)", "link", line_start, line_end)

    def highlight_pattern(
        self, pattern, tag, start="1.0", end="end", exclude_tags=None
    ):
        """Подсветка без перекрытия с другими тегами"""
        if exclude_tags is None:
            exclude_tags = []

        start = self.index(start)
        end = self.index(end)
        self.mark_set("matchStart", start)
        self.mark_set("matchEnd", start)
        self.mark_set("searchLimit", end)

        count = tk.IntVar()
        while True:
            index = self.search(
                pattern,
                index="matchEnd",
                stopindex="searchLimit",
                count=count,
                regexp=True,
            )
            if index == "":
                break
            if count.get() == 0:
                break

            match_start = index
            match_end = f"{index}+{count.get()}c"

            # Проверяем, есть ли запрещённые теги
            overlap = False
            for t in exclude_tags:
                if self.tag_ranges(t):  # Есть ли теги вообще
                    ranges = self.tag_ranges(t)
                    for i in range(0, len(ranges), 2):
                        if self.compare(match_start, ">=", ranges[i]) and self.compare(
                            match_start, "<", ranges[i + 1]
                        ):
                            overlap = True
                            break
                if overlap:
                    break

            if not overlap:
                self.tag_add(tag, match_start, match_end)

            self.mark_set("matchEnd", match_end)

    def format_line(self, style):
        """Применяет форматирование к строке с курсором"""
        index = self.index("insert")
        line_num = index.split(".")[0]
        line_start = f"{line_num}.0"
        line_end = f"{line_num}.end"

        text = self.get(line_start, line_end)

        if style == "bold":
            # Если уже есть **, убираем
            if text.startswith("**") and text.endswith("**"):
                text = text[2:-2]
            else:
                text = f"**{text.strip().strip('*')}**"

        elif style == "italic":
            if text.startswith("*") and text.endswith("*"):
                text = text[1:-1]
            else:
                text = f"*{text.strip()}*"

        elif style == "h1":
            if text.startswith("# "):
                text = text.strip("#").strip()
            else:
                text = f"# {text.strip('#').strip()}"

        elif style == "h2":
            if text.startswith("## "):
                text = text.strip("#").strip()
            else:
                text = f"## {text.strip('#').strip()}"

        elif style == "h3":
            if text.startswith("### "):
                text = text.strip("#").strip()
            else:
                text = f"### {text.strip('#').strip()}"

        elif style == "h4":
            if text.startswith("#### "):
                text = text.strip("#").strip()
            else:
                text = f"#### {text.strip('#').strip()}"

        elif style == "h5":
            if text.startswith("##### "):
                text = text.strip("#").strip()
            else:
                text = f"##### {text.strip('#').strip()}"

        self.delete(line_start, line_end)
        self.insert(line_start, text)
