import json
import os
import re
import tkinter as tk
from tkinter import ttk
from dialog_manager import DialogManager


class BnfEditor:
    def __init__(self, orig_path):
        self.orig_path = orig_path
        self.history_path = os.path.join(os.path.expanduser("~"), ".bnf_tag_history.json")
        self.tag_history = self._load_tag_history()

        dialog = tk.Toplevel()
        dialog.title("Метаданные книги")
        dialog.geometry("820x520")
        dialog.resizable(False, False)

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Переменные
        title_var = tk.StringVar()
        orig_name_var = tk.StringVar()
        author_var = tk.StringVar()
        lang_var = tk.StringVar(value="en-ru")
        tag_entry_var = tk.StringVar()

        all_tags = sorted(self.tag_history[:])
        current_tags = []

        # Путь к файлу метаданных
        base_dir = os.path.dirname(self.orig_path)
        base_name = os.path.splitext(
            os.path.splitext(os.path.basename(self.orig_path))[0]
        )[0]
        metadata_path = os.path.join(base_dir, f"{base_name}.bnf")
        description_text = ""

        # Загрузка существующих данных
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    title_var.set(data.get("title", ""))
                    orig_name_var.set(data.get("orig_name", ""))
                    author_var.set(data.get("author", ""))
                    lang_var.set(data.get("lang", "en-ru"))
                    current_tags = [t.strip().lower() for t in data.get("tags", []) if t.strip()]
                    description_text = data.get("description", "")

                    for t in current_tags:
                        if t not in all_tags:
                            all_tags.insert(0, t)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        else:
            filename = os.path.basename(base_name)
            match = re.match(r"^(.*?)(?:\[(.*?)\])?$", filename)
            if match:
                title_var.set(match.group(1).strip())
                if match.group(2):
                    author_var.set(match.group(2).strip())

        # ---- UI ----
        row = 0

        ttk.Label(main_frame, text="Название:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=5
        )
        ttk.Entry(main_frame, textvariable=title_var, width=52).grid(
            row=row, column=1, sticky="ew", padx=5, pady=5
        )
        row += 1

        ttk.Label(main_frame, text="Оригинальное название:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=5
        )
        ttk.Entry(main_frame, textvariable=orig_name_var, width=52).grid(
            row=row, column=1, sticky="ew", padx=5, pady=5
        )
        row += 1

        ttk.Label(main_frame, text="Автор:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=5
        )
        ttk.Entry(main_frame, textvariable=author_var, width=52).grid(
            row=row, column=1, sticky="ew", padx=5, pady=5
        )
        row += 1

        ttk.Label(main_frame, text="Язык:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=5
        )
        ttk.Combobox(
            main_frame,
            textvariable=lang_var,
            values=("en-ru",),
            state="readonly",
            width=50,
        ).grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1

        # ===== Теги =====
        ttk.Label(main_frame, text="Теги:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="nw", pady=(8, 4)
        )

        tags_container = ttk.Frame(main_frame)
        tags_container.grid(row=row, column=1, sticky="ew", padx=5, pady=(8, 4))

        # Поле ввода нового тега
        tag_entry = ttk.Entry(tags_container, textvariable=tag_entry_var, width=52)
        tag_entry.pack(fill=tk.X, pady=(0, 8))

        # Контейнер для чипсов с переносом строк
        chips_wrapper = ttk.Frame(tags_container)
        chips_wrapper.pack(fill=tk.BOTH, expand=True)

        # Text-виджет позволяет чипсам переноситься на новую строку
        tags_display = tk.Text(
            chips_wrapper,
            height=8, # примерно 8 строк чипсов
            wrap="word",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=2,
            cursor="arrow",
            state="normal",
        )
        tags_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Вертикальный скролл, если чипсов очень много
        chips_scroll = ttk.Scrollbar(
            chips_wrapper, orient="vertical", command=tags_display.yview
        )
        chips_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tags_display.configure(yscrollcommand=chips_scroll.set)

        def refresh_tags_display():
            tags_display.configure(state="normal")
            tags_display.delete("1.0", tk.END)

            for tag in all_tags:
                is_active = tag in current_tags

                if is_active:
                    bg = "#2980b9"
                    fg = "white"
                else:
                    bg = "#ecf0f1"
                    fg = "#2c3e50"

                chip = tk.Frame(
                    tags_display,
                    bg=bg,
                    cursor="hand2",
                    highlightbackground="#bdc3c7",
                    highlightthickness=1,
                )

                lbl = tk.Label(
                    chip,
                    text=tag,
                    bg=bg,
                    fg=fg,
                    padx=9,
                    pady=3,
                    font=("Arial", 9),
                    cursor="hand2",
                )
                lbl.pack()

                def make_toggle(t):
                    def toggle(event=None):
                        if t in current_tags:
                            current_tags.remove(t)
                        else:
                            current_tags.append(t)
                        refresh_tags_display()
                    return toggle

                toggle_fn = make_toggle(tag)
                chip.bind("<Button-1>", toggle_fn)
                lbl.bind("<Button-1>", toggle_fn)

                # Подсветка при наведении
                def on_enter(e, c=chip, active=is_active):
                    new_bg = "#3498db" if active else "#d5dbdb"
                    c.configure(bg=new_bg)
                    for child in c.winfo_children():
                        child.configure(bg=new_bg)

                def on_leave(e, c=chip, b=bg):
                    c.configure(bg=b)
                    for child in c.winfo_children():
                        child.configure(bg=b)

                chip.bind("<Enter>", on_enter)
                chip.bind("<Leave>", on_leave)
                lbl.bind("<Enter>", on_enter)
                lbl.bind("<Leave>", on_leave)

                # Вставляем чип + маленький пробел
                tags_display.window_create(tk.END, window=chip)
                tags_display.insert(tk.END, " ")

            tags_display.configure(state="disabled")

        def on_return(event):
            tag = tag_entry_var.get().strip().lower()
            if not tag:
                return "break"

            if tag not in all_tags:
                all_tags.insert(0, tag)

            if tag not in current_tags:
                current_tags.append(tag)

            tag_entry_var.set("")
            refresh_tags_display()
            return "break"

        tag_entry.bind("<Return>", on_return)

        # Первоначальная отрисовка
        refresh_tags_display()
        row += 1

        # Описание
        ttk.Label(main_frame, text="Описание:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="nw", pady=5
        )
        desc_frame = ttk.Frame(main_frame)
        desc_frame.grid(row=row, column=1, sticky="nsew", padx=5, pady=5)

        desc_text = tk.Text(desc_frame, height=5, wrap=tk.WORD, undo=True)
        desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        desc_scroll = ttk.Scrollbar(desc_frame, command=desc_text.yview)
        desc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        desc_text.configure(yscrollcommand=desc_scroll.set)
        desc_text.insert("1.0", description_text)

        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(row, weight=1)

        # Кнопки
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(side=tk.BOTTOM, pady=10)

        def do_save():
            self.save_metadata(
                dialog,
                metadata_path,
                title_var,
                orig_name_var,
                author_var,
                lang_var,
                current_tags,
                all_tags,
                desc_text,
            )

        save_button = ttk.Button(buttons_frame, text="Сохранить", command=do_save)
        save_button.pack(side=tk.LEFT, padx=5)

        cancel_button = ttk.Button(buttons_frame, text="Отмена", command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

        dialog.bind("<Control-s>", lambda e: do_save())

        tag_entry.focus_set()

    def _load_tag_history(self):
        if not os.path.exists(self.history_path):
            return []
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [str(t).strip().lower() for t in data if str(t).strip()]
        except (json.JSONDecodeError, OSError):
            pass
        return []

    def _save_tag_history(self, all_tags):
        history = sorted(all_tags[:])
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            self.tag_history = history
        except OSError:
            pass

    def save_metadata(
            self,
            dialog,
            metadata_path,
            title_var,
            orig_name_var,
            author_var,
            lang_var,
            current_tags,
            all_tags,
            desc_text,
    ):
        data = {
            "title": title_var.get(),
            "orig_name": orig_name_var.get(),
            "author": author_var.get(),
            "lang": lang_var.get(),
            "tags": current_tags,
            "description": desc_text.get("1.0", "end-1c"),
        }

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self._save_tag_history(all_tags)

        dialog.destroy()
        DialogManager.show_dialog("Сохранено", "Метаданные успешно сохранены.")
