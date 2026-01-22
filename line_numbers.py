import tkinter as tk


class LineNumbers(tk.Canvas):
    def __init__(self, parent, *args, **kwargs):
        tk.Canvas.__init__(self, parent, *args, **kwargs)
        self.text_widget = None
        self.configure(width=50, highlightthickness=0)

    def attach(self, text_widget):
        self.text_widget = text_widget
        self.text_widget.bind("<Configure>", self.on_configure)
        self.text_widget.bind("<KeyRelease>", self.on_key_release)
        self.text_widget.bind("<ButtonRelease-1>", self.on_key_release)

    def on_configure(self, event=None):
        self.redraw()

    def on_key_release(self, event=None):
        self.redraw()

    def redraw(self):
        if not self.text_widget:
            return

        self.delete("all")
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            line_num = str(i).split(".")[0]
            self.create_text(45, y, anchor="ne", text=line_num, fill="#666666")
            i = self.text_widget.index(f"{i}+1line")
