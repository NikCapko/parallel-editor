import re
import tkinter as tk
from tkinter import ttk

from dialog_manager import DialogManager
from markdown_text import MarkdownText


class SearchDialog:
    def __init__(self, root, text_frame: MarkdownText):
        self.text_frame = text_frame
        self.search_matches = []
        self.search_index = -1

        search_win = tk.Toplevel(root)
        search_win.title("Поиск")
        search_win.transient(root)
        search_win.resizable(False, False)
        search_win.attributes("-topmost", True)

        # Список вариантов
        options = [".+\\n.+", "\\n\\n\\n", "(?<!\n\n)\n\*{3,}\n(?!\n\n)"]

        tk.Label(search_win, text="Найти:").pack(side=tk.LEFT, padx=5, pady=5)
        search_entry = ttk.Combobox(
            search_win, values=options, width=30, state="normal"
        )
        search_entry.focus_set()
        search_entry.pack(side=tk.LEFT, padx=5, pady=5)

        regex_var = tk.BooleanVar()
        regex_check = tk.Checkbutton(search_win, text="RegEx", variable=regex_var)
        regex_check.pack(side=tk.LEFT, padx=5, pady=5)

        select_all_var = tk.BooleanVar()
        select_all_check = tk.Checkbutton(
            search_win, text="Select All", variable=select_all_var
        )
        select_all_check.pack(side=tk.LEFT, padx=5, pady=5)

        self.search_started = False

        def start_search():
            self.search_started = True
            term = search_entry.get()
            if not term or not self.text_frame:
                return
            self.find_all_matches(
                self.text_frame, term, regex_var.get(), select_all_var.get()
            )
            self.goto_next_match()

        def next_match():
            if self.search_started:
                self.goto_next_match()
            else:
                start_search()

        def prev_match():
            self.goto_prev_match()

        tk.Button(
            search_win, text="🔎", command=start_search, font=("Noto Color Emoji", 10)
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            search_win, text="⬆️", command=prev_match, font=("Noto Color Emoji", 10)
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            search_win, text="⬇️", command=next_match, font=("Noto Color Emoji", 10)
        ).pack(side=tk.LEFT, padx=2)
        tk.Button(
            search_win,
            text="❌",
            command=lambda: self.close_search(search_win),
            font=("Noto Color Emoji", 10),
        ).pack(side=tk.LEFT, padx=2)

        search_entry.bind("<Return>", lambda e: start_search())
        search_win.bind("<Escape>", lambda e: self.close_search(search_win))

    def close_search(self, search_win):
        self.text_frame.tag_remove("search_highlight", "1.0", tk.END)
        self.text_frame.tag_remove("search_highlight_all", "1.0", tk.END)
        search_win.destroy()

    def goto_prev_match(self):
        if not self.search_matches:
            return
        self.search_index = (self.search_index - 1) % len(self.search_matches)
        start_pos = self.search_matches[self.search_index][0]
        end_pos = self.search_matches[self.search_index][1]
        self.text_frame.see(start_pos)
        self.text_frame.mark_set("insert", start_pos)
        self.text_frame.tag_remove("search_highlight", "1.0", tk.END)
        self.text_frame.tag_add("search_highlight", start_pos, end_pos)

    def index_to_text_pos(self, text, index):
        """Преобразует позицию символа (int) в формат 'строка.символ' для Text"""
        line = text.count("\n", 0, index) + 1
        col = index - text.rfind("\n", 0, index) - 1
        return f"{line}.{col}"

    def find_all_matches(self, widget, term, use_regex=False, select_all=False):
        widget.tag_remove("current_line", "1.0", tk.END)
        self.search_matches.clear()
        self.search_index = -1

        text_content = widget.get("1.0", tk.END)

        if use_regex:
            try:
                for match in re.finditer(term, text_content, flags=re.IGNORECASE):
                    start_index = self.index_to_text_pos(text_content, match.start())
                    end_index = self.index_to_text_pos(text_content, match.end())
                    if select_all:
                        widget.tag_add("search_highlight_all", start_index, end_index)
                    else:
                        widget.tag_remove("search_highlight_all", "1.0", tk.END)
                    self.search_matches.append([start_index, end_index])
            except re.error as e:
                DialogManager.show_dialog("Ошибка RegEx", str(e))
                return
        else:
            start_pos = "1.0"
            while True:
                start_pos = widget.search(
                    term, start_pos, nocase=True, stopindex=tk.END
                )
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(term)}c"
                if select_all:
                    widget.tag_add("search_highlight_all", start_pos, end_pos)
                else:
                    widget.tag_remove("search_highlight_all", "1.0", tk.END)
                self.search_matches.append([start_pos, end_pos])
                start_pos = end_pos

        widget.tag_config(
            "search_highlight_all", background="#7CFC00", foreground="black"
        )
        widget.tag_config("search_highlight", background="green", foreground="black")

    def goto_next_match(self):
        if not self.search_matches:
            return
        self.search_index = (self.search_index + 1) % len(self.search_matches)
        start_pos = self.search_matches[self.search_index][0]
        end_pos = self.search_matches[self.search_index][1]
        self.text_frame.see(start_pos)
        self.text_frame.mark_set("insert", start_pos)
        self.text_frame.tag_remove("search_highlight", "1.0", tk.END)
        self.text_frame.tag_add("search_highlight", start_pos, end_pos)
