import tkinter as tk

from markdown_text import MarkdownText


class TOCList(tk.Listbox):
    def __init__(
        self, parent, text_widget: MarkdownText | None = None, *args, **kwargs
    ):
        super().__init__(parent, *args, **kwargs)
        self.text_widget = text_widget

        self.configure(width=25, activestyle="none", exportselection=False)
        self.bind("<ButtonRelease-1>", self.on_select)
        self.bind("<<ListboxSelect>>", self.on_select)

        # Словарь для хранения соответствия "заголовок" -> "номер строки"
        self.headers_data = {}
        self._update_job = None

    def check_contains_text(self, text):
        return any(text in str(value) for value in self.headers_data.values())

    def set_text_widget(self, widget):
        self.text_widget = widget

    def schedule_update(self):
        if self._update_job:
            self.after_cancel(self._update_job)
        self._update_job = self.after(300, self.update_toc)

    def update_toc(self):
        # сохраняем индекс выделенного элемента
        selected_index = None
        selection = self.curselection()
        if selection:
            selected_index = selection[0]

        scroll_pos = self.yview()[0]

        self.delete(0, tk.END)
        self.headers_data.clear()

        if not self.text_widget:
            return

        lines = self.text_widget.get("1.0", tk.END).split("\n")

        # Заполняем список и карту номерами строк
        for i, line in enumerate(lines, 1):
            if line.startswith("# "):
                title = line[2:]
                self.insert(tk.END, f"{title}")
                listbox_index = self.size() - 1
                self.headers_data[listbox_index] = (i, title)
            elif line.startswith("#####"):
                title = line[6:]
                self.insert(tk.END, f"        {title}")
                listbox_index = self.size() - 1
                self.headers_data[listbox_index] = (i, title)
            elif line.startswith("####"):
                title = line[5:]
                self.insert(tk.END, f"      {title}")
                listbox_index = self.size() - 1
                self.headers_data[listbox_index] = (i, title)
            elif line.startswith("###"):
                title = line[4:]
                self.insert(tk.END, f"    {title}")
                listbox_index = self.size() - 1
                self.headers_data[listbox_index] = (i, title)
            elif line.startswith("##"):
                title = line[3:]
                self.insert(tk.END, f"  {title}")
                listbox_index = self.size() - 1
                self.headers_data[listbox_index] = (i, title)

        # восстанавливаем выделение по индексу
        if selected_index is not None and selected_index < self.size():
            self.selection_set(selected_index)
            self.activate(selected_index)

        # --- восстановить скролл ---
        self.yview_moveto(scroll_pos)

        if selected_index is not None:
            self.see(selected_index)

    def on_select(self, *args):
        if not self.text_widget:
            return

        selection = self.curselection()
        if not selection:
            return

        # Получаем номер строки из сохранённой карты
        listbox_index = selection[0]
        text_line_number, title = self.headers_data.get(listbox_index, (None, None))

        if text_line_number is not None:
            # Переходим к нужной строке
            self.text_widget.mark_set("insert", f"{text_line_number}.0")
            self.text_widget.see(f"{text_line_number}.0")
            self.text_widget.focus_set()
