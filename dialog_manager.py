import tkinter as tk


class DialogManager:
    @staticmethod
    def show_dialog(title, message, timeout=1000):
        dialog = tk.Toplevel()
        dialog.geometry("300x100")
        dialog.resizable(False, False)

        label = tk.Label(dialog, text=title + "\n\n" + message)
        label.pack(expand=True, padx=20, pady=20)

        # Центрируем окно на экране
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        # Закрыть окно через timeout миллисекунд
        dialog.after(ms=timeout, func=dialog.destroy)
