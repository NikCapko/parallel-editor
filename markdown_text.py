import re
import tkinter as tk

class MarkdownText(tk.Text):
    """Кастомный Text виджет с подсветкой Markdown"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(undo=True, maxundo=20)
        self.configure_tags()
        self.configure_bindings()

    def configure_bindings(self):
        self.bind("<Control-b>", lambda e: self.format_line("bold"))
        self.bind("<Control-i>", lambda e: self.format_line("italic"))
        self.bind("<Control-Key-1>", lambda e: self.format_line("h1"))
        self.bind("<Control-Key-2>", lambda e: self.format_line("h2"))
        self.bind("<Control-Key-3>", lambda e: self.format_line("h3"))

        self.bind_all("<KeyRelease>", lambda e: self.highlight_markdown())
        self.bind("<<Paste>>", lambda e: self.highlight_markdown())
        self.bind("<<Cut>>", lambda e: self.highlight_markdown())

    def configure_tags(self):
        """Настройка стилей для Markdown-элементов"""
        # Заголовки
        self.tag_config("h1", font=("Arial", 18, "bold"), foreground="#2b6cb0")
        self.tag_config("h2", font=("Arial", 16, "bold"), foreground="#2c5282")
        self.tag_config("h3", font=("Arial", 14, "bold"), foreground="#3182ce")
        self.tag_config("h4", font=("Arial", 12, "bold"), foreground="#3182ce")
        self.tag_config("h5", font=("Arial", 11, "bold"), foreground="#3182ce")
        # Форматирование текста
        self.tag_config("bold", font=("Arial", 12, "bold"))
        self.tag_config("italic", font=("Arial", 12, "italic"))
        self.tag_config("bold_italic", font=("Arial", 12, "bold italic"))
        # Код и ссылки
        self.tag_config("code", font=("Courier", 12), background="#f0f0f0")
        self.tag_config("link", foreground="#4299e1", underline=True)
        # Списки
        self.tag_config("list", lmargin2=20, spacing1=5)

    def highlight_markdown(self, event=None):
        """Подсветка Markdown-синтаксиса"""
        # Очистка всех тегов перед повторной обработкой
        for tag in self.tag_names():
            if tag in ("h1", "h2", "h3", "h4", "h5", "bold", "italic", "bold_italic", "code", "link", "list"):
                self.tag_remove(tag, "1.0", tk.END)

        text = self.get("1.0", tk.END)
        lines = text.split('\n')

        # Обрабатываем построчно для многострочных паттернов
        for i, line in enumerate(lines, 1):
            line_start = f"{i}.0"
            line_end = f"{i}.end"

            # Заголовки
            if re.match(r"^#\s", line):
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
        self.highlight_pattern(r"\*\*(.+?)\*\*", "bold", exclude_tags=["bold_italic"])
        self.highlight_pattern(r"\*(.+?)\*", "italic", exclude_tags=["bold", "bold_italic"])
        self.highlight_pattern(r"`(.+?)`", "code")
        self.highlight_pattern(r"\[(.+?)\]\((.+?)\)", "link")

        # if hasattr(self.master.master, "left_toc") and self.master.master.left_toc.text_widget == self:
        #     self.master.master.left_toc.update_toc()
        # if hasattr(self.master.master, "right_toc") and self.master.master.right_toc.text_widget == self:
        #     self.master.master.right_toc.update_toc()

    def highlight_pattern(self, pattern, tag, start="1.0", end="end", exclude_tags=None):
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
                        if self.compare(match_start, ">=", ranges[i]) and self.compare(match_start, "<", ranges[i + 1]):
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
        line_num = index.split('.')[0]
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
                text = text[2:]
            else:
                text = f"# {text}"

        elif style == "h2":
            if text.startswith("## "):
                text = text[3:]
            else:
                text = f"## {text}"

        elif style == "h3":
            if text.startswith("### "):
                text = text[4:]
            else:
                text = f"### {text}"

        elif style == "h4":
            if text.startswith("#### "):
                text = text[5:]
            else:
                text = f"#### {text}"

        elif style == "h5":
            if text.startswith("##### "):
                text = text[6:]
            else:
                text = f"##### {text}"

        self.delete(line_start, line_end)
        self.insert(line_start, text)
        self.highlight_markdown()
