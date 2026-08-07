import re
import tkinter as tk
from tkinter import ttk

from dialog_manager import DialogManager
from markdown_text import MarkdownText


class ReplaceDialog:
    def __init__(self, root, text_frame: MarkdownText):
        self.text_frame = text_frame
        self.search_matches = []
        self.search_index = -1

        replace_win = tk.Toplevel(root)
        replace_win.title("Замена")
        replace_win.transient(root)
        replace_win.resizable(False, False)
        replace_win.attributes("-topmost", True)

        options = [
            r".+\n.+",
            r"\n\n\n",
            r"(?<!\n\n)\n\*{3,}\n(?!\n\n)",
        ]

        # --- Найти ---
        tk.Label(replace_win, text="Найти:").grid(row=0, column=0, padx=5, pady=5)
        search_entry = ttk.Combobox(
            replace_win, values=options, width=30, state="normal"
        )
        search_entry.grid(row=0, column=1, padx=5, pady=5)
        search_entry.focus_set()

        # --- Заменить ---
        tk.Label(replace_win, text="Заменить:").grid(row=1, column=0, padx=5, pady=5)
        replace_entry = ttk.Combobox(replace_win, width=30, state="normal")
        replace_entry.grid(row=1, column=1, padx=5, pady=5)

        regex_var = tk.BooleanVar()
        tk.Checkbutton(replace_win, text="RegEx", variable=regex_var).grid(
            row=2, column=0, padx=5
        )

        case_sensitive_var = tk.BooleanVar()
        tk.Checkbutton(
            replace_win, text="Case sensitive", variable=case_sensitive_var
        ).grid(row=2, column=1, padx=5)

        select_all_var = tk.BooleanVar()
        tk.Checkbutton(replace_win, text="Select All", variable=select_all_var).grid(
            row=2, column=2, padx=5
        )

        # Чекбокс «С начала»
        from_start_var = tk.BooleanVar(value=False)
        tk.Checkbutton(replace_win, text="С начала", variable=from_start_var).grid(
            row=2, column=3, padx=5
        )

        self.search_started = False

        # --- Функции ---
        def start_search():
            self.search_started = True
            term = search_entry.get()
            if not term:
                return
            self.find_all_matches(
                self.text_frame,
                term,
                regex_var.get(),
                select_all_var.get(),
                case_sensitive_var.get(),
                from_start_var.get(),
            )
            self.goto_next_match()

        def replace_current():
            if not self.search_matches:
                return

            replace_text = replace_entry.get()
            start, end = self.search_matches[self.search_index]

            if regex_var.get():
                # Get the actual matched text so we can expand backreferences
                matched = self.text_frame.get(start, end)
                try:
                    flags = 0 if case_sensitive_var.get() else re.IGNORECASE
                    # re.sub with count=1 expands \1, \2, \n, \g<name> etc. correctly
                    expanded = re.sub(
                        search_entry.get(),
                        replace_text,
                        matched,
                        count=1,
                        flags=flags
                    )
                except re.error as e:
                    DialogManager.show_dialog("Ошибка RegEx", str(e))
                    return
                self.text_frame.delete(start, end)
                self.text_frame.insert(start, expanded)
            else:
                # Ordinary (non-regex) replacement
                self.text_frame.delete(start, end)
                self.text_frame.insert(start, replace_text)

            # After a successful replacement we must rebuild the match list
            # (positions have shifted)
            start_search()


        def replace_all():
            term = search_entry.get()
            replace_text = replace_entry.get()
            if not term:
                return

            content = self.text_frame.get("1.0", tk.END)

            try:
                if regex_var.get():
                    flags = 0 if case_sensitive_var.get() else re.IGNORECASE
                    new_content = re.sub(term, replace_text, content, flags=flags)
                else:
                    if case_sensitive_var.get():
                        new_content = content.replace(term, replace_text)
                    else:
                        pattern = re.compile(re.escape(term), re.IGNORECASE)
                        new_content = pattern.sub(replace_text, content)
            except re.error as e:
                DialogManager.show_dialog("Ошибка RegEx", str(e))
                return

            self.text_frame.delete("1.0", tk.END)
            self.text_frame.insert("1.0", new_content)

            # Rebuild highlights after the bulk replace
            self.find_all_matches(
                self.text_frame,
                term,
                regex_var.get(),
                select_all_var.get(),
                case_sensitive_var.get(),
                from_start_var.get(),
            )

        def next_match():
            if self.search_started:
                self.goto_next_match()
            else:
                start_search()

        def prev_match():
            self.goto_prev_match()

        # --- Кнопки ---
        tk.Button(replace_win, text="Replace", command=replace_current).grid(
            row=3, column=0
        )
        tk.Button(replace_win, text="Replace All", command=replace_all).grid(
            row=3, column=1
        )
        tk.Button(replace_win, text="🔎", command=start_search).grid(row=3, column=2)
        tk.Button(replace_win, text="⬆️", command=prev_match).grid(row=3, column=3)
        tk.Button(replace_win, text="⬇️", command=next_match).grid(row=3, column=4)
        tk.Button(replace_win, text="❌", command=lambda: self.close(replace_win)).grid(
            row=3, column=5
        )

        replace_win.bind("<Escape>", lambda e: self.close(replace_win))
        search_entry.bind("<Return>", lambda e: start_search())

    # --- Логика поиска ---
    def close(self, win):
        self.text_frame.tag_remove("search_highlight", "1.0", tk.END)
        self.text_frame.tag_remove("search_highlight_all", "1.0", tk.END)
        win.destroy()

    def goto_next_match(self):
        if not self.search_matches:
            return
        self.search_index = (self.search_index + 1) % len(self.search_matches)
        start, end = self.search_matches[self.search_index]
        self.text_frame.see(start)
        self.text_frame.mark_set("insert", start)
        self.text_frame.tag_remove("search_highlight", "1.0", tk.END)
        self.text_frame.tag_add("search_highlight", start, end)

    def goto_prev_match(self):
        if not self.search_matches:
            return
        self.search_index = (self.search_index - 1) % len(self.search_matches)
        start, end = self.search_matches[self.search_index]
        self.text_frame.see(start)
        self.text_frame.mark_set("insert", start)
        self.text_frame.tag_remove("search_highlight", "1.0", tk.END)
        self.text_frame.tag_add("search_highlight", start, end)

    def index_to_text_pos(self, text, index):
        line = text.count("\n", 0, index) + 1
        col = index - text.rfind("\n", 0, index) - 1
        return f"{line}.{col}"

    def find_all_matches(
        self,
        widget,
        term,
        use_regex=False,
        select_all=False,
        case_sensitive=False,
        from_start=False,
    ):
        widget.tag_remove("current_line", "1.0", tk.END)
        self.search_matches.clear()
        self.search_index = -1

        text_content = widget.get("1.0", tk.END)

        if use_regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                for match in re.finditer(term, text_content, flags=flags):
                    start = self.index_to_text_pos(text_content, match.start())
                    end = self.index_to_text_pos(text_content, match.end())
                    if select_all:
                        widget.tag_add("search_highlight_all", start, end)
                    self.search_matches.append([start, end])
            except re.error as e:
                DialogManager.show_dialog("Ошибка RegEx", str(e))
                return
        else:
            start_pos = "1.0"
            while True:
                start_pos = widget.search(
                    term, start_pos, nocase=not case_sensitive, stopindex=tk.END
                )
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(term)}c"
                if select_all:
                    widget.tag_add("search_highlight_all", start_pos, end_pos)
                self.search_matches.append([start_pos, end_pos])
                start_pos = end_pos

        # Начинаем с текущего места курсора (если не «С начала»)
        if self.search_matches and not from_start:
            current_pos = widget.index("insert")
            for i, (start, end) in enumerate(self.search_matches):
                if widget.compare(start, ">=", current_pos):
                    self.search_index = i - 1  # следующий goto_next_match попадёт на i
                    break
            # если все совпадения до курсора → остаётся -1 → wrap на первое

        widget.tag_config("search_highlight_all", background="#7CFC00")
        widget.tag_config("search_highlight", background="green")
