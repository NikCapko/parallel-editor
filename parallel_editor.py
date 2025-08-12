import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog

from line_numbers import LineNumbers
from markdown_text import MarkdownText
from toc_list import TOCList
from tooltip import ToolTip


class TextFieldType:
    LEFT = 1
    RIGHT = 2

class SideBySideEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Параллельный редактор перевода (.md)")

        self.orig_path = ""
        self.trans_path = ""
        self.syncing = False

        # Верхний фрейм с заголовком и кнопками
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)

        # Заголовок с названием файла
        self.file_title = tk.Label(self.top_frame, text="Файл не загружен", font=("Arial", 12, "bold"))
        self.file_title.pack(side=tk.TOP, fill=tk.X)

        # Фрейм для кнопок (в левом верхнем углу)
        self.buttons_frame = tk.Frame(self.top_frame)
        self.buttons_frame.pack(side=tk.LEFT, anchor="nw", pady=(5, 0))

        # Кнопки с иконками
        self.load_button = tk.Button(self.buttons_frame, text="📁",
                                     command=self.load_md_pair_dialog,
                                     font=("Noto Color Emoji", 12, "bold"))
        self.load_button.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(self.load_button, "Open File")

        self.save_button = tk.Button(self.buttons_frame, text="💾", command=self.save_md_files,
                                     font=("Noto Color Emoji", 12, "bold"))
        self.save_button.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(self.save_button, "Save Files")

        self.edit_original_button = tk.Button(self.buttons_frame, text="📝󾓦",
                                              command=lambda: self.open_original_with_program("mousepad"),
                                              font=("Noto Color Emoji", 12, "bold"))
        self.edit_original_button.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(self.edit_original_button, "Edit En File")

        self.translate_original_button = tk.Button(self.buttons_frame, text="🌐󾓦",
                                                   command=lambda: self.open_original_with_program(
                                                       "yandex-browser-stable"), font=("Noto Color Emoji", 12, "bold"))
        self.translate_original_button.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(self.translate_original_button, "Translate En File")

        self.edit_translate_button = tk.Button(self.buttons_frame, text="📝󾓬",
                                               command=lambda: self.open_translate_with_program("mousepad"),
                                               font=("Noto Color Emoji", 12, "bold"))
        self.edit_translate_button.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(self.edit_translate_button, "Open Ru File")

        self.reload_button = tk.Button(self.buttons_frame, text="🔄", command=self.reload_md_files,
                                       font=("Noto Color Emoji", 12, "bold"))
        self.reload_button.pack(side=tk.LEFT, padx=(0, 5))
        ToolTip(self.reload_button, "Reload Files")

        self.exit_button = tk.Button(self.buttons_frame, text="❌", command=root.quit,
                                     font=("Noto Color Emoji", 12, "bold"))
        self.exit_button.pack(side=tk.LEFT)
        ToolTip(self.exit_button, "Exit")

        # Панель форматирования справа
        self.format_frame = tk.Frame(self.top_frame)
        self.format_frame.pack(side=tk.RIGHT, anchor="ne", pady=(5, 0))

        self.bold_button = tk.Button(self.format_frame, text="**B**", command=lambda: self.apply_format("bold"),
                                     font=("Arial", 8, "bold"))
        self.bold_button.pack(side=tk.LEFT, padx=2)
        ToolTip(self.bold_button, "bold format")

        self.italic_button = tk.Button(self.format_frame, text="*I*", command=lambda: self.apply_format("italic"),
                                       font=("Arial", 8, "italic"))
        self.italic_button.pack(side=tk.LEFT, padx=2)
        ToolTip(self.italic_button, "italic format")

        self.h1_button = tk.Button(self.format_frame, text="H1", command=lambda: self.apply_format("h1"),
                                   font=("Arial", 8))
        self.h1_button.pack(side=tk.LEFT, padx=2)
        ToolTip(self.h1_button, "h1 title format")

        self.h2_button = tk.Button(self.format_frame, text="H2", command=lambda: self.apply_format("h2"),
                                   font=("Arial", 8))
        self.h2_button.pack(side=tk.LEFT, padx=2)
        ToolTip(self.h2_button, "h2 title format")

        self.h3_button = tk.Button(self.format_frame, text="H3", command=lambda: self.apply_format("h3"),
                                   font=("Arial", 8))
        self.h3_button.pack(side=tk.LEFT, padx=2)
        ToolTip(self.h3_button, "h3 title format")

        # Основной контейнер
        container = tk.Frame(root)
        container.pack(fill=tk.BOTH, expand=True)

        # Создаем фреймы для каждого редактора с номерами строк
        left_frame = tk.Frame(container)
        right_frame = tk.Frame(container)

        # Левый редактор с оглавлением и номерами строк
        self.left_toc = TOCList(left_frame, None)
        self.left_toc.pack(side=tk.LEFT, fill=tk.Y)

        # Левый редактор с номерами строк
        self.left_line_numbers = LineNumbers(left_frame, width=40)
        self.left_line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        self.left_text = MarkdownText(left_frame, wrap="word")
        self.left_toc.text_widget = self.left_text  # привязка
        self.left_line_numbers.attach(self.left_text)

        self.left_scroll = tk.Scrollbar(left_frame, command=self.on_scroll_left)
        self.left_text.configure(yscrollcommand=self.on_text_scroll_left)

        self.left_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.left_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        left_frame.grid(row=0, column=0, sticky="nsew")

        # Правый редактор с номерами строк
        self.right_line_numbers = LineNumbers(right_frame, width=40)
        self.right_line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        self.right_text = MarkdownText(right_frame, wrap="word")
        self.right_line_numbers.attach(self.right_text)
        self.right_scroll = tk.Scrollbar(right_frame, command=self.on_scroll_right)
        self.right_text.configure(yscrollcommand=self.on_text_scroll_right)

        self.right_toc = TOCList(right_frame, None)
        self.right_toc.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_toc.text_widget = self.right_text

        self.right_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.right_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.grid(row=0, column=2, sticky="nsew")

        # Разделитель между редакторами
        separator = tk.Frame(container, width=2, bd=1, relief=tk.SUNKEN)
        separator.grid(row=0, column=1, sticky="ns")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(2, weight=1)

        # Подсветка строки с курсором
        self.left_text.tag_configure("current_line", background="#e7ff00", selectbackground="#77b8ff")
        self.right_text.tag_configure("current_line", background="#e7ff00", selectbackground="#77b8ff")

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

        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            self.load_md_pair(file_path)

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

    def on_text_scroll_left(self, *args):
        self.left_line_numbers.redraw()
        self.left_scroll.set(args[0], args[1])  # обновляем положение ползунка

    def on_text_scroll_right(self, *args):
        self.right_line_numbers.redraw()
        self.right_scroll.set(args[0], args[1])

    def update_file_title(self):
        """Обновляет заголовок с названием файла"""
        if self.orig_path and self.trans_path:
            base_name = os.path.basename(self.orig_path).split(".")[0]
            self.file_title.config(text=f"{base_name}")
        else:
            self.file_title.config(text="Файл не загружен")

    def open_original_with_program(self, program_cmd):
        """Открывает оригинальный .en.md файл выбранной программой"""
        if not self.orig_path:
            show_dialog("Ошибка", "Оригинальный файл не загружен")
            return

        try:
            # Определяем путь к английскому файлу
            en_path = ""
            if self.orig_path.endswith(".en.md"):
                en_path = self.orig_path
            elif self.trans_path.endswith(".en.md"):
                en_path = self.trans_path
            else:
                show_dialog("Ошибка", "Английский файл не найден")
                return

            subprocess.Popen([program_cmd, en_path])

        except Exception as e:
            show_dialog("Ошибка открытия", f"Не удалось открыть файл: {str(e)}")

    def open_translate_with_program(self, program_cmd):
        """Открывает файл перевода .ru.md выбранной программой"""
        if not self.orig_path:
            show_dialog("Ошибка", "Файл перевода не загружен")
            return

        try:
            # Определяем путь к файлу перевода
            en_path = ""
            if self.orig_path.endswith(".ru.md"):
                en_path = self.orig_path
            elif self.trans_path.endswith(".ru.md"):
                en_path = self.trans_path
            else:
                show_dialog("Ошибка", "Файл перевода не найден")
                return

            subprocess.Popen([program_cmd, en_path])

        except Exception as e:
            show_dialog("Ошибка открытия", f"Не удалось открыть файл: {str(e)}")

    def reload_md_files(self):
        """Перезагружает содержимое оригинального и переведённого файла с диска"""
        if not self.orig_path or not self.trans_path:
            show_dialog("Ошибка", "Файлы не загружены")
            return

        try:
            with open(self.orig_path, 'r', encoding='utf-8') as f:
                original_lines = f.read()
            with open(self.trans_path, 'r', encoding='utf-8') as f:
                translation_lines = f.read()

            self.left_text.delete("1.0", tk.END)
            self.right_text.delete("1.0", tk.END)

            self.left_text.insert(tk.END, original_lines)
            self.right_text.insert(tk.END, translation_lines)

            self.left_text.highlight_markdown()
            self.right_text.highlight_markdown()

            self.left_toc.update_toc()
            self.right_toc.update_toc()

            show_dialog("Готово", "Файлы перезагружены с диска.")

        except Exception as e:
            show_dialog("Ошибка загрузки", str(e))

    def load_md_pair_dialog(self):
        file_path = filedialog.askopenfilename(title="Выбери .en.md или .ru.md", filetypes=[("Markdown", "*.md")])
        if not file_path:
            return
        self.load_md_pair(file_path)

    def load_md_pair(self, file_path):
        base_name, lang_ext = os.path.splitext(file_path)
        base_name, lang = os.path.splitext(base_name)

        if lang not in (".en", ".ru"):
            show_dialog("Ошибка", "Файл должен заканчиваться на .en.md или .ru.md")
            return

        other_lang = ".ru" if lang == ".en" else ".en"
        orig_lang = lang
        trans_lang = other_lang

        orig_path = base_name + orig_lang + ".md"
        trans_path = base_name + trans_lang + ".md"

        if not os.path.exists(trans_path):
            show_dialog("Ошибка", f"Файл перевода не найден: {trans_path}")
            return

        if lang == ".en":
            self.orig_path = orig_path
            self.trans_path = trans_path
        else:
            self.orig_path = trans_path
            self.trans_path = orig_path

        try:
            with open(self.orig_path, 'r', encoding='utf-8') as f:
                original_lines = f.read()
            with open(self.trans_path, 'r', encoding='utf-8') as f:
                translation_lines = f.read()

            self.left_text.delete("1.0", tk.END)
            self.right_text.delete("1.0", tk.END)

            self.left_text.insert(tk.END, original_lines)
            self.right_text.insert(tk.END, translation_lines)

            self.left_text.highlight_markdown()
            self.right_text.highlight_markdown()

            self.left_toc.update_toc()
            self.right_toc.update_toc()

            # Обновляем заголовок после загрузки файлов
            self.update_file_title()

        except Exception as e:
            show_dialog("Ошибка", str(e))

    def edit_translate(self):
        """Открывает файл перевода .ru.md в mousepad"""
        if not self.orig_path:
            show_dialog("Ошибка", "Файлы не загружены")
            return

        try:
            # Определяем путь к файлу перевода
            ru_path = ""
            if self.orig_path.endswith(".ru.md"):
                ru_path = self.orig_path
            elif self.trans_path.endswith(".ru.md"):
                ru_path = self.trans_path
            else:
                show_dialog("Ошибка", "Русский файл не найден")
                return

            # Запускаем Ghostwriter с этим файлом
            subprocess.Popen(["mousepad", ru_path])

        except Exception as e:
            show_dialog("Ошибка предпросмотра", f"Не удалось открыть файл: {str(e)}")

    def sync_cursor_left(self, event=None):
        if self.syncing:
            return
        self.syncing = True
        try:
            # Получаем номер текущей строки в левом поле
            index = self.left_text.index("insert")
            line_num = index.split('.')[0]

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
            line_num = index.split('.')[0]

            # Устанавливаем курсор в левом поле на ту же строку
            self.left_text.mark_set("insert", f"{line_num}.0")

            # Выравниваем строки параллельно
            self.align_lines_parallel(line_num, TextFieldType.RIGHT)
        finally:
            self.syncing = False

    def align_lines_parallel(self, line_num, text_field_type):
        """Выравнивает строки параллельно в обоих полях на одной высоте"""
        try:
            # Показываем строку в центре каждого виджета
            self.left_text.see(f"{line_num}.0")
            self.right_text.see(f"{line_num}.0")

            # Обновляем интерфейс
            self.root.update_idletasks()

            # Получаем позицию строки в левом поле
            left_bbox = self.left_text.bbox(f"{line_num}.0")
            right_bbox = self.right_text.bbox(f"{line_num}.0")

            if left_bbox is None or right_bbox is None:
                return

            if text_field_type == TextFieldType.LEFT:
                # Получаем текущую позицию курсора (в виде строки "line.column")
                cursor_pos = self.left_text.index(tk.INSERT)

                # Получаем координаты курсора в пикселях относительно виджета
                bbox = self.left_text.bbox(cursor_pos)

                y_pixel = bbox[1]  # Y-координата верхнего края курсора

                self.adjust_scroll_to_position(self.right_text, line_num, y_pixel)
            elif text_field_type == TextFieldType.RIGHT:
                # Получаем текущую позицию курсора (в виде строки "line.column")
                cursor_pos = self.right_text.index(tk.INSERT)

                # Получаем координаты курсора в пикселях относительно виджета
                bbox = self.right_text.bbox(cursor_pos)

                y_pixel = bbox[1]  # Y-координата верхнего края курсора
                self.adjust_scroll_to_position(self.left_text, line_num, y_pixel)
            else:
                pass
        except:
            # В случае ошибки просто показываем строки
            self.left_text.see(f"{line_num}.0")
            self.right_text.see(f"{line_num}.0")

    def save_md_files(self):
        if not self.orig_path or not self.trans_path:
            show_dialog("Ошибка", "Файлы не загружены")
            return

        try:
            original_text = self.left_text.get("1.0", tk.END).strip().splitlines()
            translated_text = self.right_text.get("1.0", tk.END).strip().splitlines()

            # Выравнивание по строкам
            max_len = max(len(original_text), len(translated_text))
            original_text += [""] * (max_len - len(original_text))
            translated_text += [""] * (max_len - len(translated_text))

            with open(self.orig_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(original_text) + '\n')

            with open(self.trans_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(translated_text) + '\n')

            show_dialog("Успех", "Файлы сохранены.")

        except Exception as e:
            show_dialog("Ошибка сохранения", str(e))

    def adjust_scroll_to_position(self, text_widget, line_num, target_y):
        """Корректирует прокрутку чтобы строка была на заданной высоте"""
        try:
            # Получаем текущую позицию строки
            bbox = text_widget.bbox(f"{line_num}.0")
            if bbox is None:
                return

            current_y = bbox[1]
            diff = target_y - current_y

            # Если разность значительная, корректируем
            if abs(diff) > 5:
                # Получаем высоту строки
                line_height = bbox[3] if bbox[3] > 0 else 16

                # Вычисляем количество строк для прокрутки
                scroll_lines = diff / line_height

                # Применяем прокрутку
                text_widget.yview_scroll(int(-scroll_lines), "units")
        except:
            pass

    def highlight_current_line_left(self, event=None):
        # даём курсору переместиться, затем подсвечиваем
        self.root.after(1, lambda: self._highlight_line_with_sync(self.left_text, self.right_text, TextFieldType.LEFT))

    def highlight_current_line_right(self, event=None):
        self.root.after(1, lambda: self._highlight_line_with_sync(self.right_text, self.left_text, TextFieldType.RIGHT))

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

def show_dialog(title, message, timeout=500):
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


if __name__ == "__main__":
    root = tk.Tk()
    app = SideBySideEditor(root)
    root.mainloop()
