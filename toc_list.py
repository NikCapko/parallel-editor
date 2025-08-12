import tkinter as tk

class TOCList(tk.Listbox):
    def __init__(self, parent, text_widget=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.text_widget = text_widget
        self.configure(width=25, activestyle="none")
        self.bind("<ButtonRelease-1>", self.on_select)

    def set_text_widget(self, widget):
        self.text_widget = widget

    def update_toc(self):
        self.delete(0, tk.END)
        if not self.text_widget:
            return
        lines = self.text_widget.get("1.0", tk.END).split("\n")
        for i, line in enumerate(lines, 1):
            if line.startswith("# "):
                self.insert(tk.END, f"{line[2:]}")
            elif line.startswith("## "):
                self.insert(tk.END, f"  {line[3:]}")
            elif line.startswith("### "):
                self.insert(tk.END, f"    {line[4:]}")

    def on_select(self, event=None):
        if not self.text_widget:
            return
        selection = self.curselection()
        if not selection:
            return
        idx = selection[0]
        lines = self.text_widget.get("1.0", tk.END).split("\n")
        header_count = -1
        for i, line in enumerate(lines, 1):
            if line.startswith("#"):
                header_count += 1
                if header_count == idx:
                    self.text_widget.mark_set("insert", f"{i}.0")
                    self.text_widget.see(f"{i}.0")
                    break
