import json
import os
import re
import tkinter as tk
from tkinter import ttk

from dialog_manager import DialogManager


class BnfEditor:
    def __init__(self, orig_path):
        self.orig_path = orig_path
        self.history_path = os.path.join(
            os.path.expanduser("~"), ".bnf_tag_history.json"
        )
        self.tag_history = sorted(self._load_tag_history())

        dialog = tk.Toplevel()
        dialog.title("Метаданные книги")
        dialog.geometry("800x420")
        dialog.resizable(False, False)

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Переменные
        title_var = tk.StringVar()
        orig_name_var = tk.StringVar()
        author_var = tk.StringVar()
        lang_var = tk.StringVar(value="en-ru")
        tags_var = tk.StringVar()
        add_tag_var = tk.StringVar()

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
                    tags_var.set(", ".join(data.get("tags", [])))
                    description_text = data.get("description", "")
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
        title_entry = ttk.Entry(main_frame, textvariable=title_var, width=50)
        title_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1

        ttk.Label(
            main_frame, text="Оригинальное название:", font=("Arial", 10, "bold")
        ).grid(row=row, column=0, sticky="w", pady=5)
        orig_name_entry = ttk.Entry(main_frame, textvariable=orig_name_var, width=50)
        orig_name_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1

        ttk.Label(main_frame, text="Автор:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=5
        )
        author_entry = ttk.Entry(main_frame, textvariable=author_var, width=50)
        author_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1

        ttk.Label(main_frame, text="Язык:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=5
        )
        lang_entry = ttk.Combobox(
            main_frame,
            textvariable=lang_var,
            values=("en-ru",),
            state="readonly",
            width=50,
        )
        lang_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1

        # Теги
        ttk.Label(
            main_frame, text="Теги (через запятую):", font=("Arial", 10, "bold")
        ).grid(row=row, column=0, sticky="w", pady=5)
        tags_entry = ttk.Entry(main_frame, textvariable=tags_var, width=50)
        tags_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1

        # Быстрый выбор из истории
        ttk.Label(
            main_frame, text="Добавить из истории:", font=("Arial", 10, "bold")
        ).grid(row=row, column=0, sticky="w", pady=5)
        add_tag_combo = ttk.Combobox(
            main_frame,
            textvariable=add_tag_var,
            values=self.tag_history,
            width=50,
            state="normal",
        )
        add_tag_combo.grid(row=row, column=1, sticky="ew", padx=5, pady=5)

        def on_tag_selected(event=None):
            selected = add_tag_var.get().strip().lower()
            if not selected:
                return

            current = [
                t.strip().lower() for t in tags_var.get().split(",") if t.strip()
            ]
            if selected not in current:
                current.append(selected)
                tags_var.set(", ".join(current))

            add_tag_var.set("")  # очищаем поле быстрого выбора
            add_tag_combo.set("")

        add_tag_combo.bind("<<ComboboxSelected>>", on_tag_selected)
        add_tag_combo.bind("<Return>", on_tag_selected)
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

        save_button = ttk.Button(
            buttons_frame,
            text="Сохранить",
            command=lambda: self.save_metadata(
                dialog,
                metadata_path,
                title_var,
                orig_name_var,
                author_var,
                lang_var,
                tags_var,
                desc_text,
            ),
        )
        save_button.pack(side=tk.LEFT, padx=5)

        cancel_button = ttk.Button(buttons_frame, text="Отмена", command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

        dialog.bind(
            "<Control-s>",
            lambda event: self.save_metadata(
                dialog,
                metadata_path,
                title_var,
                orig_name_var,
                author_var,
                lang_var,
                tags_var,
                desc_text,
            ),
        )

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

    def _save_tag_history(self, used_tags):
        # used_tags уже в нижнем регистре
        history = self.tag_history[:]

        history = sorted(history)

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
        tags_var,
        desc_text,
    ):
        tags = [tag.strip().lower() for tag in tags_var.get().split(",") if tag.strip()]

        data = {
            "title": title_var.get(),
            "orig_name": orig_name_var.get(),
            "author": author_var.get(),
            "lang": lang_var.get(),
            "tags": tags,
            "description": desc_text.get("1.0", "end-1c"),
        }

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Обновляем историю тегов
        self._save_tag_history(tags)

        dialog.destroy()
        DialogManager.show_dialog("Сохранено", "Метаданные успешно сохранены.")
