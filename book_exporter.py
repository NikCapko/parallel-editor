import os
import subprocess

from ebooklib import epub
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from dialog_manager import DialogManager


class BookExporter:
    def __init__(
        self,
        orig_path,
        book_type,
        original_lines,
        translated_lines,
    ):
        # Определяем базовый путь
        base_dir = os.path.dirname(orig_path)
        base_name = os.path.splitext(os.path.splitext(os.path.basename(orig_path))[0])[
            0
        ]

        # ---- EPUB ----
        if book_type.startswith("epub"):
            html_content = ""
            if "table" in book_type:
                html_content += (
                    "<table border='1' style='width:100%; border-collapse:collapse;'>"
                )
                for o, t in zip(original_lines, translated_lines):
                    if not (o.strip() == "" and t.strip() == ""):
                        html_content += f"<tr><td>{o}</td><td>{t}</td></tr>"
                html_content += "</table>"
            else:  # list
                for o, t in zip(original_lines, translated_lines):
                    if not (o.strip() == "" and t.strip() == ""):
                        html_content += f"<p><b>{o}</b><br>{t}</p>"

            book = epub.EpubBook()
            book.set_identifier("id123456")
            book.set_title(base_name)
            book.set_language("en")
            c1 = epub.EpubHtml(title="Content", file_name="content.xhtml", lang="en")
            c1.content = html_content
            book.add_item(c1)
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            book.spine = ["nav", c1]

            save_path = os.path.join(base_dir, f"{base_name}.epub")
            epub.write_epub(save_path, book)
            subprocess.Popen(["xdg-open", save_path])
            DialogManager.show_dialog("Готово", f"EPUB сохранён: {save_path}")

        # ---- PDF ----
        elif book_type.startswith("pdf"):
            # Шрифт с кириллицей
            font_path = "/usr/share/fonts/TTF/DejaVuSans.ttf"
            bold_font_path = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
            if not os.path.exists(font_path):
                DialogManager.show_dialog("Ошибка", f"Не найден шрифт {font_path}")
                return
            if not os.path.exists(bold_font_path):
                DialogManager.show_dialog("Ошибка", f"Не найден шрифт {bold_font_path}")
                return
            pdfmetrics.registerFont(TTFont("DejaVu", font_path))
            pdfmetrics.registerFont(TTFont("DejaVu-Bold", bold_font_path))

            styles = getSampleStyleSheet()
            styles.add(
                ParagraphStyle(
                    name="Cyrillic",
                    fontName="DejaVu",
                    fontSize=10,
                    leading=12,
                    wordWrap="CJK",
                )
            )
            styles.add(
                ParagraphStyle(
                    name="CyrillicBold",
                    fontName="DejaVu-Bold",
                    fontSize=10,
                    leading=12,
                    wordWrap="CJK",
                )
            )

            save_path = os.path.join(base_dir, f"{base_name}.pdf")

            doc = SimpleDocTemplate(
                save_path,
                pagesize=A4,
                leftMargin=0,
                rightMargin=0,
                topMargin=0,
                bottomMargin=0,
            )
            elements = []

            if "table" in book_type:
                data = [["Original", "Translation"]]
                for o, t in zip(original_lines, translated_lines):
                    if not (o.strip() == "" and t.strip() == ""):
                        data.append(
                            [
                                Paragraph(o, styles["Cyrillic"]),
                                Paragraph(t, styles["Cyrillic"]),
                            ]
                        )

                table = Table(data, colWidths=[270, 270])
                table.setStyle(
                    TableStyle(
                        [
                            ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                        ]
                    )
                )
                elements.append(table)
            else:
                for o, t in zip(original_lines, translated_lines):
                    if not (o.strip() == "" and t.strip() == ""):
                        elements.append(
                            Paragraph(o, styles["CyrillicBold"])
                        )  # оригинал жирным
                        elements.append(Paragraph(t, styles["Cyrillic"]))
                        elements.append(Spacer(1, 6))

            doc.build(elements)
            subprocess.Popen(["xdg-open", save_path])
            DialogManager.show_dialog("Готово", f"PDF сохранён: {save_path}")
