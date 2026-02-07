import json
import os
import re
import tkinter as tk
from tkinter import ttk

from dialog_manager import DialogManager


class BnfEditor:
    def __init__(self, orig_path):
        self.orig_path = orig_path
        dialog = tk.Toplevel()
        dialog.title("Метаданные книги")
        dialog.geometry("800x400")  # Увеличиваем высоту для многострочных полей
        dialog.resizable(False, False)

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Переменные для полей ввода
        title_var = tk.StringVar()
        author_var = tk.StringVar()
        lang_var = tk.StringVar(value="ru")
        tags_var = tk.StringVar()

        # Путь к файлу метаданных
        base_dir = os.path.dirname(self.orig_path)
        base_name = os.path.splitext(
            os.path.splitext(os.path.basename(self.orig_path))[0]
        )[0]
        metadata_path = os.path.join(base_dir, f"{base_name}.bnf")

        description_text = ""

        # Загрузка существующих данных, если файл существует
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    title_var.set(data.get("title", ""))
                    author_var.set(data.get("author", ""))
                    lang_var.set(data.get("lang", "ru"))
                    tags_var.set(", ".join(data.get("tags", [])))
                    description_text = data.get("description", "")
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        else:
            # Парсинг из имени файла, если файл метаданных не найден
            filename = os.path.basename(base_name)
            match = re.match(r"^(.*?)(?:\[(.*?)\])?$", filename)
            if match:
                title_var.set(match.group(1).strip())
                if match.group(2):
                    author_var.set(match.group(2).strip())

        # Заголовки и поля ввода
        row = 0
        ttk.Label(main_frame, text="Название:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=5
        )
        title_entry = ttk.Entry(main_frame, textvariable=title_var, width=50)
        title_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
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
            values=("ru", "en-ru"),
            state="readonly",
            width=50,
        )
        lang_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1

        ttk.Label(
            main_frame, text="Теги (через запятую):", font=("Arial", 10, "bold")
        ).grid(row=row, column=0, sticky="w", pady=5)
        tags_entry = ttk.Entry(main_frame, textvariable=tags_var, width=50)
        tags_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        row += 1

        # Поле для описания с переносом строк
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
        row += 1

        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)  # Делаем строку с описанием растягиваемой

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
                author_var,
                lang_var,
                tags_var,
                desc_text,
            ),
        )
        save_button.pack(side=tk.LEFT, padx=5)

        cancel_button = ttk.Button(buttons_frame, text="Отмена", command=dialog.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

    def save_metadata(
        self,
        dialog,
        metadata_path,
        title_var,
        author_var,
        lang_var,
        tags_var,
        desc_text,
    ):
        data = {
            "title": title_var.get(),
            "author": author_var.get(),
            "lang": lang_var.get(),
            "tags": [tag.strip() for tag in tags_var.get().split(",") if tag.strip()],
            "description": desc_text.get("1.0", "end-1c"),
        }

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        dialog.destroy()
        DialogManager.show_dialog("Сохранено", "Метаданные успешно сохранены.")
