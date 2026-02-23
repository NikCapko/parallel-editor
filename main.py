#!/usr/bin/python
import os
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox

from bnf_editor import BnfEditor
from book_exporter import BookExporter
from dialog_manager import DialogManager
from line_numbers import LineNumbers
from markdown_text import MarkdownText
from search_dialog import SearchDialog
from text_corrector import TextCorrector
from toc_list import TOCList
from tooltip import ToolTip

CONFIG_FILE = "replacements.json"

TEMP_DIR = os.path.join(tempfile.gettempdir(), "paraline_editor")
os.makedirs(TEMP_DIR, exist_ok=True)


class TextFieldType:
    LEFT = 1
    RIGHT = 2


class SideBySideEditor:
    def __init__(self, root):
        self.search_started = None

        self.root = root
        self.root.title("Paraline")

        self.orig_path = ""
        self.trans_path = ""
        self.syncing = False

        # Верхний фрейм с заголовком и кнопками
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)

        # Заголовок с названием файла
        self.file_title = tk.Label(
            self.top_frame, text="Файл не загружен", font=("Arial", 12, "bold")
        )
        self.file_title.pack(side=tk.TOP, fill=tk.X)
        # Привязываем клик левой кнопкой мыши к функции копирования
        self.file_title.bind("<Button-1>", self.copy_to_clipboard)

        # Фрейм для кнопок (в левом верхнем углу)
        self.buttons_frame = tk.Frame(self.top_frame)
        self.buttons_frame.pack(side=tk.LEFT, anchor="nw", pady=(5, 0))

        ## Кнопки с иконками

        # load files

        self.load_button = tk.Button(
            self.buttons_frame,
            text="📂",
            command=self.load_md_pair_dialog,
            font=("Noto Color Emoji", 12, "bold"),
        )
        self.load_button.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(self.load_button, "Open File")

        # save files

        self.save_button = tk.Button(
            self.buttons_frame,
            text="💾",
            command=self.save_md_files,
            font=("Noto Color Emoji", 12, "bold"),
        )
        self.save_button.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(self.save_button, "Save Files")

        # export files to book

        self.export_book_menu_button = tk.Menubutton(
            self.buttons_frame,
            text="📖",
            relief=tk.RAISED,
            font=("Noto Color Emoji", 12),
        )
        self.export_book_menu = tk.Menu(
            self.export_book_menu_button, tearoff=0, font=("Arial", 12, "bold")
        )
        ToolTip(self.export_book_menu_button, "Export Parallel Book")

        # Список вариантов для выбора
        self.export_variants = {
            "Epub file (table)": "epub_table",
            "Epub file (line by line)": "epub_list",
            "Pdf file (table)": "pdf_table",
            "Pdf file (line by line)": "pdf_list",
        }

        for label, key in self.export_variants.items():
            self.export_book_menu.add_command(
                label=label, command=lambda cmd=key: self.export_parallel_book(cmd)
            )

        self.export_book_menu_button.config(menu=self.export_book_menu)
        self.export_book_menu_button.pack(side=tk.LEFT, padx=(0, 5))

        # translate en file

        self.translate_original_button = tk.Menubutton(
            self.buttons_frame,
            text="🌐",
            relief=tk.RAISED,
            font=("Noto Color Emoji", 12),
        )
        self.translate_original_menu = tk.Menu(
            self.translate_original_button, tearoff=0, font=("Arial", 12, "bold")
        )
        ToolTip(self.translate_original_button, "Translate En File With Browser")

        # Список вариантов для выбора
        self.translate_variants = {
            "Yandex Browser": "yandex-browser-stable",
            "Google Chrome": "google-chrome-stable",
        }

        for label, key in self.translate_variants.items():
            self.translate_original_menu.add_command(
                label=label,
                command=lambda cmd=key: self.open_original_with_browser(cmd),
            )

        self.translate_original_button.config(menu=self.translate_original_menu)
        self.translate_original_button.pack(side=tk.LEFT, padx=(0, 5))

        # reload files

        self.reload_button = tk.Button(
            self.buttons_frame,
            text="🔄",
            command=self.reload_md_files,
            font=("Noto Color Emoji", 12, "bold"),
        )
        self.reload_button.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(self.reload_button, "Reload Files")

        self.info_button = tk.Button(
            self.buttons_frame,
            text="❕",
            command=self.open_metadata_dialog,
            font=("Noto Color Emoji", 12, "bold"),
        )
        self.info_button.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(self.info_button, "File Info")

        self.correct_button = tk.Button(
            self.buttons_frame,
            text="📝",
            command=self.correct_text,
            font=("Noto Color Emoji", 12, "bold"),
        )
        self.correct_button.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(self.correct_button, "Correct text")

        self.exit_button = tk.Button(
            self.buttons_frame,
            text="❌",
            command=root.quit,
            font=("Noto Color Emoji", 12, "bold"),
        )
        self.exit_button.pack(side=tk.LEFT)
        ToolTip(self.exit_button, "Exit")

        # Панель форматирования справа
        self.format_frame = tk.Frame(self.top_frame)
        self.format_frame.pack(side=tk.RIGHT, anchor="ne", pady=(5, 0))

        self.bold_button = tk.Button(
            self.format_frame,
            text="**B**",
            command=lambda: self.apply_format("bold"),
            font=("Arial", 8, "bold"),
        )
        self.bold_button.pack(side=tk.LEFT, padx=2)
        ToolTip(self.bold_button, "bold format")

        self.italic_button = tk.Button(
            self.format_frame,
            text="*I*",
            command=lambda: self.apply_format("italic"),
            font=("Arial", 8, "italic"),
        )
        self.italic_button.pack(side=tk.LEFT, padx=2)
        ToolTip(self.italic_button, "italic format")

        self.h1_button = tk.Button(
            self.format_frame,
            text="H1",
            command=lambda: self.apply_format("h1"),
            font=("Arial", 8),
        )
        self.h1_button.pack(side=tk.LEFT, padx=2)
        ToolTip(self.h1_button, "h1 title format")

        self.h2_button = tk.Button(
            self.format_frame,
            text="H2",
            command=lambda: self.apply_format("h2"),
            font=("Arial", 8),
        )
        self.h2_button.pack(side=tk.LEFT, padx=2)
        ToolTip(self.h2_button, "h2 title format")

        self.h3_button = tk.Button(
            self.format_frame,
            text="H3",
            command=lambda: self.apply_format("h3"),
            font=("Arial", 8),
        )
        self.h3_button.pack(side=tk.LEFT, padx=2)
        ToolTip(self.h3_button, "h3 title format")

        self.h4_button = tk.Button(
            self.format_frame,
            text="H4",
            command=lambda: self.apply_format("h4"),
            font=("Arial", 8),
        )
        self.h4_button.pack(side=tk.LEFT, padx=2)
        ToolTip(self.h4_button, "h4 title format")

        self.h5_button = tk.Button(
            self.format_frame,
            text="H5",
            command=lambda: self.apply_format("h5"),
            font=("Arial", 8),
        )
        self.h5_button.pack(side=tk.LEFT, padx=2)
        ToolTip(self.h5_button, "h5 title format")

        # Основной контейнер
        container = tk.Frame(root)
        container.pack(fill=tk.BOTH, expand=True)

        # Создаем фреймы для каждого редактора с номерами строк
        # Левый редактор с оглавлением и номерами строк
        left_editor_frame = tk.Frame(container)
        left_editor_frame.grid(row=0, column=0, sticky="nsew")

        # Панель с кнопкой для левого TOC
        left_top_panel = tk.Frame(left_editor_frame)
        left_top_panel.pack(side=tk.TOP, fill=tk.X)
        self.toggle_left_toc_button = tk.Button(
            left_top_panel,
            text="👈",
            command=self.toggle_left_toc,
            font=("Noto Color Emoji", 10),
        )
        self.toggle_left_toc_button.pack(side=tk.LEFT, anchor="w", padx=2, pady=2)

        self.left_jump_entry = tk.Entry(left_top_panel, width=8)
        self.left_jump_entry.pack(side=tk.LEFT, pady=2)
        self.left_jump_entry.bind(
            "<Return>", lambda e: self.jump_to_line(self.left_jump_entry)
        )
        self.left_jump_entry_button = tk.Button(
            left_top_panel,
            text="Go",
            command=lambda: self.jump_to_line(self.left_jump_entry),
            font=("Noto Color Emoji", 10),
        )
        self.left_jump_entry_button.pack(side=tk.LEFT, anchor="w")
        self.left_search_button = tk.Button(
            left_top_panel,
            text="🔎",
            command=self.on_left_search,
            font=("Noto Color Emoji", 10),
        )
        self.left_search_button.pack(side=tk.LEFT, anchor="w")

        # Основная часть левого редактора
        self.left_frame = tk.Frame(left_editor_frame)
        self.left_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.left_text = MarkdownText(self.left_frame, wrap="word")
        self.left_scroll = tk.Scrollbar(self.left_frame, command=self.on_scroll_left)

        # Левый редактор с оглавлением
        self.left_toc = TOCList(self.left_frame, self.left_text)
        self.left_toc_scroll = tk.Scrollbar(
            self.left_frame, orient=tk.VERTICAL, command=self.left_toc.yview
        )
        self.left_toc.configure(yscrollcommand=self.left_toc_scroll.set)
        self.left_toc.pack(side=tk.LEFT, fill=tk.Y)
        self.left_toc_scroll.pack(side=tk.LEFT, fill=tk.Y)

        self.left_text.bind("<<Modified>>", self.on_left_text_modified)
        self.left_text.edit_modified(False)

        # Фрейм для номеров строк + поле перехода
        left_num_frame = tk.Frame(self.left_frame)
        left_num_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.left_line_numbers = LineNumbers(left_num_frame, width=50)
        self.left_line_numbers.pack(side=tk.TOP, fill=tk.Y, expand=True)
        self.left_line_numbers.attach(self.left_text)

        self.left_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.left_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Правый редактор
        right_editor_frame = tk.Frame(container)
        right_editor_frame.grid(row=0, column=2, sticky="nsew")

        # Панель с кнопкой для правого TOC
        right_top_panel = tk.Frame(right_editor_frame)
        right_top_panel.pack(side=tk.TOP, fill=tk.X)
        self.toggle_right_toc_button = tk.Button(
            right_top_panel,
            text="👉",
            command=self.toggle_right_toc,
            font=("Noto Color Emoji", 10),
        )
        self.toggle_right_toc_button.pack(side=tk.RIGHT, anchor="e", padx=2, pady=2)
        self.right_search_button = tk.Button(
            right_top_panel,
            text="🔎",
            command=self.on_right_search,
            font=("Noto Color Emoji", 10),
        )
        self.right_search_button.pack(side=tk.RIGHT)

        # Основная часть правого редактора
        self.right_frame = tk.Frame(right_editor_frame)
        self.right_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        right_num_frame = tk.Frame(self.right_frame)
        right_num_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.right_line_numbers = LineNumbers(right_num_frame, width=40)
        self.right_line_numbers.pack(side=tk.TOP, fill=tk.Y, expand=True)

        self.right_text = MarkdownText(self.right_frame, wrap="word")
        self.right_line_numbers.attach(self.right_text)
        self.right_scroll = tk.Scrollbar(self.right_frame, command=self.on_scroll_right)

        self.right_toc = TOCList(self.right_frame, self.right_text)
        self.right_toc_scroll = tk.Scrollbar(
            self.right_frame, orient=tk.VERTICAL, command=self.right_toc.yview
        )
        self.right_toc.configure(yscrollcommand=self.right_toc_scroll.set)
        self.right_toc_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_toc.pack(side=tk.RIGHT, fill=tk.Y)

        self.right_text.bind("<<Modified>>", self.on_righ_text_modified)
        self.right_text.edit_modified(False)

        self.right_text.bind("<<Paste>>", lambda e: self.update_right_text_async())
        self.right_text.bind("<<Cut>>", lambda e: self.update_right_text_async())

        self.left_text.bind("<<Paste>>", lambda e: self.update_left_text_async())
        self.left_text.bind("<<Cut>>", lambda e: self.update_left_text_async())

        self.right_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.right_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Скрыть TOC по умолчанию
        # self.init_toc_state()

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(2, weight=1)

        # Подсветка строки с курсором
        self.left_text.tag_configure(
            "current_line", background="#e7ff00", selectbackground="#77b8ff"
        )
        self.right_text.tag_configure(
            "current_line", background="#e7ff00", selectbackground="#77b8ff"
        )

        self.left_text.bind("<ButtonRelease-1>", self.highlight_current_line_left)
        self.right_text.bind("<ButtonRelease-1>", self.highlight_current_line_right)

        self.left_text.bind("<Up>", self.highlight_current_line_left)
        self.right_text.bind("<Up>", self.highlight_current_line_right)

        self.left_text.bind("<Down>", self.highlight_current_line_left)
        self.right_text.bind("<Down>", self.highlight_current_line_right)

        self.left_text.bind("<Left>", self.highlight_current_line_left)
        self.right_text.bind("<Left>", self.highlight_current_line_right)

        self.left_text.bind("<Right>", self.highlight_current_line_left)
        self.right_text.bind("<Right>", self.highlight_current_line_right)

        root.bind("<Control-s>", lambda event: self.save_md_files())
        root.bind("<Control-o>", lambda event: self.load_md_pair_dialog())
        root.bind("<Control-r>", lambda event: self.reload_md_files())

        self.left_text.configure(yscrollcommand=self.on_text_scroll_left)
        self.right_text.configure(yscrollcommand=self.on_text_scroll_right)

        root.bind("<Control-f>", self.on_ctrl_f)

        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            self.load_md_pair(file_path)

    def update_right_text_async(self):
        self.right_text.after(300, self.update_right_text)

    def update_right_text(self):
        self.right_text.schedule_highlight_markdown()
        self.right_toc.schedule_update()

    def update_left_text_async(self):
        self.left_text.after(300, self.update_left_text)

    def update_left_text(self):
        self.left_text.schedule_highlight_markdown()
        self.left_toc.schedule_update()

    def on_righ_text_modified(self, *args):
        self.right_text.on_text_modified()
        line = int(self.right_text.index("insert").split(".")[0])
        text = self.right_text.get(f"{line}.0", f"{line}.end").lstrip()
        if text.startswith("#"):
            self.right_toc.schedule_update()
        elif self.right_toc.check_contains_text(text):
            self.right_toc.schedule_update()

    def on_left_text_modified(self, *args):
        self.left_text.on_text_modified()
        line = int(self.left_text.index("insert").split(".")[0])
        text = self.left_text.get(f"{line}.0", f"{line}.end").lstrip()
        if text.startswith("#"):
            self.left_toc.schedule_update()
        elif self.left_toc.check_contains_text(text):
            self.left_toc.schedule_update()

    def open_metadata_dialog(self):
        if not self.orig_path:
            DialogManager.show_dialog("Ошибка", "Сначала откройте файл.")
            return
        BnfEditor(self.orig_path)

    def on_ctrl_f(self, event):
        # определяем, в каком текстовом поле был фокус при нажатии
        text_frame = self.root.focus_get()
        self.open_search_dialog(text_frame)

    def on_left_search(self):
        self.open_search_dialog(self.left_text)

    def on_right_search(self):
        self.open_search_dialog(self.right_text)

    def open_search_dialog(self, text_frame):
        SearchDialog(self.root, text_frame)

    def correct_text(self):
        self.left_text_corrector = TextCorrector(self.left_text)
        self.left_text_corrector.correct_text(self.orig_path)
        self.left_toc.schedule_update()

        self.right_text_corrector = TextCorrector(self.right_text)
        self.right_text_corrector.correct_text(self.trans_path)
        self.right_toc.schedule_update()

    def on_text_scroll_left(self, *args):
        self.left_line_numbers.redraw()
        self.left_scroll.set(args[0], args[1])

    def on_text_scroll_right(self, *args):
        self.right_line_numbers.redraw()
        self.right_scroll.set(args[0], args[1])

    def copy_to_clipboard(self, event=None):
        # Очищаем буфер обмена и копируем текст метки
        root.clipboard_clear()
        root.clipboard_append(self.file_title.cget("text"))

    def jump_to_line(self, entry_widget):
        try:
            line_num = int(entry_widget.get())

            self.left_text.mark_set("insert", f"{line_num}.0")
            self.left_text.see(f"{line_num}.0")

            self.right_text.mark_set("insert", f"{line_num}.0")
            self.right_text.see(f"{line_num}.0")

            self.left_text.focus_set()

        except ValueError:
            pass

    def init_toc_state(self):
        # Скрываем TOC по умолчанию
        self.left_toc.pack_forget()
        self.right_toc.pack_forget()
        # Иконки в начальном состоянии
        self.toggle_left_toc_button.config(text="📑")
        self.toggle_right_toc_button.config(text="📑")

    def toggle_left_toc(self):
        if self.left_toc.winfo_ismapped():
            self.left_toc.pack_forget()
            self.left_toc_scroll.pack_forget()
            self.toggle_left_toc_button.config(text="📑")  # скрыт
        else:
            self.left_toc = TOCList(self.left_frame, None)
            self.left_toc_scroll = tk.Scrollbar(
                self.left_frame, orient=tk.VERTICAL, command=self.left_toc.yview
            )
            self.left_toc.configure(yscrollcommand=self.left_toc_scroll.set)
            self.left_toc_scroll.pack(
                side=tk.LEFT, fill=tk.Y, before=self.left_line_numbers
            )
            self.left_toc.pack(side=tk.LEFT, fill=tk.Y, before=self.left_toc_scroll)

            self.left_toc.text_widget = self.left_text
            self.left_toc.update_toc()
            self.toggle_left_toc_button.config(text="👈")  # показан

    def toggle_right_toc(self):
        if self.right_toc.winfo_ismapped():
            self.right_toc.pack_forget()
            self.right_toc_scroll.pack_forget()
            self.toggle_right_toc_button.config(text="📑")  # скрыт
        else:
            self.right_toc = TOCList(self.right_frame, None)
            self.right_toc_scroll = tk.Scrollbar(
                self.right_frame, orient=tk.VERTICAL, command=self.right_toc.yview
            )
            self.right_toc.configure(yscrollcommand=self.right_toc_scroll.set)
            self.right_toc_scroll.pack(
                side=tk.RIGHT, fill=tk.Y, after=self.right_scroll
            )
            self.right_toc.pack(side=tk.RIGHT, fill=tk.Y, before=self.right_toc_scroll)
            self.right_toc.update_toc()
            self.toggle_right_toc_button.config(text="👉")  # показан

    def apply_format(self, style):
        widget = self.root.focus_get()
        if widget == self.left_text:
            self.left_text.format_line(style)
        elif widget == self.right_text:
            self.right_text.format_line(style)

    def on_scroll_left(self, *args):
        self.left_text.yview(*args)
        self.left_line_numbers.redraw()
        self.left_scroll.set(*args)  # фикс положения ползунка

    def on_scroll_right(self, *args):
        self.right_text.yview(*args)
        self.right_line_numbers.redraw()
        self.right_scroll.set(*args)

    def update_file_title(self):
        """Обновляет заголовок с названием файла"""
        if self.orig_path:
            filename, _ = os.path.splitext(os.path.basename(self.orig_path))
            base_name = filename.replace(".en", "")
            self.file_title.config(text=f"{base_name}")
        elif self.trans_path:
            filename, _ = os.path.splitext(os.path.basename(self.trans_path))
            base_name = filename.replace(".ru", "")
            self.file_title.config(text=f"{base_name}")
        else:
            self.file_title.config(text="Файл не загружен")

    def save_text_to_file(self, text_widget, path):
        content = text_widget.get("1.0", "end-1c")

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def create_temp_md_from_text(self, lang):
        filename = f"temporary.{lang}.md"
        path = os.path.join(TEMP_DIR, filename)

        content = self.left_text.get("1.0", "end-1c")

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return path

    def open_original_with_browser(self, app):
        """Открывает оригинальный .en.md файл выбранной программой"""
        try:
            en_path = None

            if self.orig_path and self.orig_path.endswith(".en.md"):
                en_path = self.orig_path
            elif self.trans_path and self.trans_path.endswith(".en.md"):
                en_path = self.trans_path

            # 🔹 ЕСЛИ НЕТ — СОЗДАЁМ ВРЕМЕННЫЙ
            if not en_path or not os.path.exists(en_path):
                en_path = self.create_temp_md_from_text("en")
            else:
                # 🔹 обновляем существующий файл перед открытием
                self.save_text_to_file(self.left_text, en_path)

            subprocess.Popen([app, en_path])

        except Exception as e:
            DialogManager.show_dialog(
                "Ошибка открытия", f"Не удалось открыть файл: {str(e)}"
            )

    def reload_md_files(self):
        """Перезагружает содержимое оригинального и переведённого файла с диска"""
        if not self.orig_path or not self.trans_path:
            DialogManager.show_dialog("Ошибка", "Файлы не загружены")
            return

        try:
            # Сохраняем текущую прокрутку
            left_scroll_pos = self.left_text.yview()[0]
            right_scroll_pos = self.right_text.yview()[0]

            with open(self.orig_path, "r", encoding="utf-8") as f:
                original_lines = f.read()
            with open(self.trans_path, "r", encoding="utf-8") as f:
                translation_lines = f.read()

            self.left_text.delete("1.0", tk.END)
            self.right_text.delete("1.0", tk.END)

            self.left_text.insert(tk.END, original_lines)
            self.right_text.insert(tk.END, translation_lines)

            self.left_text.highlight_markdown()
            self.right_text.highlight_markdown()

            self.left_toc.schedule_update()
            self.right_toc.schedule_update()

            # Восстанавливаем прокрутку
            self.left_text.update_idletasks()  # опционально, но помогает
            self.root.after_idle(lambda: self.left_text.yview_moveto(left_scroll_pos))
            self.right_text.update_idletasks()  # опционально, но помогает
            self.root.after_idle(lambda: self.right_text.yview_moveto(right_scroll_pos))

            DialogManager.show_dialog("Готово", "Файлы перезагружены с диска.")

        except Exception as e:
            DialogManager.show_dialog("Ошибка загрузки", str(e))

    def load_md_pair_dialog(self):
        file_path = filedialog.askopenfilename(
            title="Выбери .en.md или .ru.md", filetypes=[("Markdown", "*.md")]
        )
        if not file_path:
            return
        self.load_md_pair(file_path)

    def load_md_pair(self, file_path):
        base_name, lang_ext = os.path.splitext(file_path)
        base_name, lang = os.path.splitext(base_name)

        if lang not in (".en", ".ru"):
            DialogManager.show_dialog(
                "Ошибка", "Файл должен заканчиваться на .en.md или .ru.md"
            )
            return

        other_lang = ".ru" if lang == ".en" else ".en"
        orig_lang = lang
        trans_lang = other_lang

        orig_path = base_name + orig_lang + ".md"
        trans_path = base_name + trans_lang + ".md"

        if lang == ".en":
            self.orig_path = orig_path
            self.trans_path = trans_path
        else:
            self.orig_path = trans_path
            self.trans_path = orig_path

        try:
            if os.path.exists(self.orig_path):
                with open(self.orig_path, "r", encoding="utf-8") as f:
                    original_lines = f.read()
            else:
                original_lines = ""
            if os.path.exists(self.trans_path):
                with open(self.trans_path, "r", encoding="utf-8") as f:
                    translation_lines = f.read()
            else:
                translation_lines = ""

            self.left_text.delete("1.0", tk.END)
            self.right_text.delete("1.0", tk.END)

            self.left_text.insert(tk.END, original_lines)
            self.right_text.insert(tk.END, translation_lines)

            self.left_text.highlight_markdown()
            self.right_text.highlight_markdown()

            self.left_text.mark_set("insert", "1.0")  # ставим курсор в начало
            self.left_text.see("insert")
            self.left_text.focus_set()

            self.left_toc.schedule_update()
            self.right_toc.schedule_update()

            # Обновляем заголовок после загрузки файлов
            self.update_file_title()

        except Exception as e:
            DialogManager.show_dialog("Ошибка", str(e))

        # 🔹 ЕСЛИ ФАЙЛА ПЕРЕВОДА НЕТ
        if not os.path.exists(trans_path):
            answer = messagebox.askyesno(
                "Файл не найден",
                f"Файл перевода не найден:\n{trans_path}\n\nСоздать его?",
            )

            if not answer:
                return

            # 🔹 СОЗДАЁМ ФАЙЛ
            try:
                self.trans_path = trans_path
                with open(trans_path, "w", encoding="utf-8") as f:
                    f.write("")  # можно добавить шаблон
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
                return

    def edit_translate(self):
        """Открывает файл перевода .ru.md в mousepad"""
        if not self.orig_path:
            DialogManager.show_dialog("Ошибка", "Файлы не загружены")
            return

        try:
            # Определяем путь к файлу перевода
            ru_path = ""
            if self.orig_path.endswith(".ru.md"):
                ru_path = self.orig_path
            elif self.trans_path.endswith(".ru.md"):
                ru_path = self.trans_path
            else:
                DialogManager.show_dialog("Ошибка", "Русский файл не найден")
                return

            # Запускаем Ghostwriter с этим файлом
            subprocess.Popen(["mousepad", ru_path])

        except Exception as e:
            DialogManager.show_dialog(
                "Ошибка предпросмотра", f"Не удалось открыть файл: {str(e)}"
            )

    def sync_cursor_left(self, event=None):
        if self.syncing:
            return
        self.syncing = True
        try:
            # Получаем номер текущей строки в левом поле
            index = self.left_text.index("insert")
            line_num = index.split(".")[0]

            # Устанавливаем курсор в правом поле на ту же строку
            self.right_text.mark_set("insert", f"{line_num}.0")

            # Выравниваем строки параллельно
            self.align_lines_parallel(line_num, TextFieldType.LEFT)
        finally:
            self.syncing = False

    def sync_cursor_right(self):
        if self.syncing:
            return
        self.syncing = True
        try:
            # Получаем номер текущей строки в правом поле
            index = self.right_text.index("insert")
            line_num = index.split(".")[0]

            # Устанавливаем курсор в левом поле на ту же строку
            self.left_text.mark_set("insert", f"{line_num}.0")

            # Выравниваем строки параллельно
            self.align_lines_parallel(line_num, TextFieldType.RIGHT)
        finally:
            self.syncing = False

    def align_lines_parallel(self, line_num, text_field_type):
        try:
            # Показываем строку в центре каждого виджета
            self.left_text.see(f"{line_num}.0")
            self.right_text.see(f"{line_num}.0")

            self.root.update_idletasks()

            if text_field_type == TextFieldType.LEFT:
                cursor_pos = self.left_text.index(tk.INSERT)
                bbox = self.left_text.bbox(cursor_pos)
                if bbox:
                    y_pixel = bbox[1]
                    # Передаём реальный индекс позиции курсора, а не начало строки
                    self.adjust_scroll_to_position(self.right_text, cursor_pos, y_pixel)
            elif text_field_type == TextFieldType.RIGHT:
                cursor_pos = self.right_text.index(tk.INSERT)
                bbox = self.right_text.bbox(cursor_pos)
                if bbox:
                    y_pixel = bbox[1]
                    self.adjust_scroll_to_position(self.left_text, cursor_pos, y_pixel)
        except:
            self.left_text.see(f"{line_num}.0")
            self.right_text.see(f"{line_num}.0")

    def adjust_scroll_to_position(self, text_widget, target_index, target_y):
        """Корректирует прокрутку, чтобы указанная позиция была на заданной высоте"""
        try:
            bbox = text_widget.bbox(target_index)
            if bbox is None:
                return
            current_y = bbox[1]
            diff = target_y - current_y
            if abs(diff) > 5:
                line_height = bbox[3] if bbox[3] > 0 else 16
                scroll_lines = diff / line_height
                text_widget.yview_scroll(int(-scroll_lines), "units")
        except:
            pass

    def export_parallel_book(self, book_type):
        if not self.orig_path or not self.trans_path:
            DialogManager.show_dialog("Ошибка", "Файлы не загружены")
            return

        original_lines = self.left_text.get("1.0", tk.END).strip().splitlines()
        translated_lines = self.right_text.get("1.0", tk.END).strip().splitlines()

        max_len = max(len(original_lines), len(translated_lines))
        original_lines += [""] * (max_len - len(original_lines))
        translated_lines += [""] * (max_len - len(translated_lines))

        BookExporter(self.orig_path, book_type, original_lines, translated_lines)

    def save_md_files(self):
        try:
            # 🔹 ЕСЛИ ФАЙЛЫ ЕЩЁ НЕ СОХРАНЯЛИСЬ
            if not self.orig_path or not self.trans_path:
                path = filedialog.asksaveasfilename(
                    title="Сохранить Markdown файлы",
                    defaultextension=".md",
                    filetypes=[("Markdown files", "*.md")],
                )

                if not path:
                    return  # пользователь отменил

                base, ext = os.path.splitext(path)

                # определяем язык
                if base.endswith(".en"):
                    base = base[:-3]
                    self.orig_path = base + ".en.md"
                    self.trans_path = base + ".ru.md"
                elif base.endswith(".ru"):
                    base = base[:-3]
                    self.orig_path = base + ".ru.md"
                    self.trans_path = base + ".en.md"
                else:
                    # если пользователь не указал язык — считаем .en основным
                    self.orig_path = base + ".en.md"
                    self.trans_path = base + ".ru.md"

            # 🔹 ПОЛУЧАЕМ ТЕКСТ
            original_text = self.left_text.get("1.0", "end-1c").splitlines()
            translated_text = self.right_text.get("1.0", "end-1c").splitlines()

            # 🔹 ВЫРАВНИВАНИЕ СТРОК
            # max_len = max(len(original_text), len(translated_text))
            # original_text += [""] * (max_len - len(original_text))
            # translated_text += [""] * (max_len - len(translated_text))

            self.update_file_title()

            # 🔹 СОХРАНЕНИЕ
            with open(self.orig_path, "w", encoding="utf-8") as f:
                f.write("\n".join(original_text) + "\n")

            with open(self.trans_path, "w", encoding="utf-8") as f:
                f.write("\n".join(translated_text) + "\n")

            DialogManager.show_dialog("Успех", "Файлы сохранены.")

        except Exception as e:
            DialogManager.show_dialog("Ошибка сохранения", str(e))

    def highlight_current_line_left(self, event=None):
        # даём курсору переместиться, затем подсвечиваем
        self.root.after(
            1,
            lambda: self._highlight_line_with_sync(
                self.left_text, self.right_text, TextFieldType.LEFT
            ),
        )

    def highlight_current_line_right(self, event=None):
        self.root.after(
            1,
            lambda: self._highlight_line_with_sync(
                self.right_text, self.left_text, TextFieldType.RIGHT
            ),
        )

    def _highlight_line_with_sync(self, src_text, dst_text, field_type):
        self._highlight_line(src_text)
        if field_type == TextFieldType.LEFT:
            self.sync_cursor_left()
        else:
            self.sync_cursor_right()
        self._highlight_line(dst_text)

    def _highlight_line(self, text_widget):
        text_widget.tag_remove("current_line", "1.0", "end")
        index = text_widget.index("insert")
        line_start = f"{index.split('.')[0]}.0"
        line_end = f"{index.split('.')[0]}.end"
        text_widget.tag_add("current_line", line_start, line_end)


def clear_temp_dir():
    if os.path.exists(TEMP_DIR):
        for name in os.listdir(TEMP_DIR):
            path = os.path.join(TEMP_DIR, name)
            try:
                if os.path.isfile(path):
                    os.remove(path)
            except Exception:
                pass


if __name__ == "__main__":
    root = tk.Tk()
    app = SideBySideEditor(root)
    root.mainloop()
    clear_temp_dir()
