from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt


ROOT = Path(__file__).resolve().parent
SCREENSHOTS = ROOT / "screenshots"
OUT = ROOT / "01_nginx_portainer_report.docx"

BLACK = "000000"
FONT = "Times New Roman"


def set_run_font(run, size=14, bold=False, italic=False):
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = __import__("docx").shared.RGBColor.from_string(BLACK)


def set_cell_text(cell, text: str, bold=False, size=11):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if bold else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_cell_shading(cell, fill="D9D9D9"):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def add_page_field(paragraph):
    run = paragraph.add_run()
    set_run_font(run, size=12)
    fld_char_1 = OxmlElement("w:fldChar")
    fld_char_1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = " PAGE "
    fld_char_2 = OxmlElement("w:fldChar")
    fld_char_2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char_1)
    run._r.append(instr_text)
    run._r.append(fld_char_2)


def configure_document(doc: Document):
    section = doc.sections[0]
    section.page_width = Cm(210)
    section.page_height = Cm(297)
    section.left_margin = Cm(3)
    section.right_margin = Cm(1.5)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.different_first_page_header_footer = True

    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    normal.font.size = Pt(14)
    normal.font.color.rgb = __import__("docx").shared.RGBColor.from_string(BLACK)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.first_line_indent = Cm(1.25)
    normal.paragraph_format.space_after = Pt(0)

    for style_name, size in (("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 14)):
        style = doc.styles[style_name]
        style.font.name = FONT
        style._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = __import__("docx").shared.RGBColor.from_string(BLACK)
        style.paragraph_format.line_spacing = 1.5
        style.paragraph_format.first_line_indent = Cm(0)
        style.paragraph_format.space_before = Pt(6)
        style.paragraph_format.space_after = Pt(6)

    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_field(p)


def add_paragraph(doc, text="", *, bold=False, italic=False, center=False, indent=True, size=14, space_after=0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.first_line_indent = Cm(1.25) if indent and not center else Cm(0)
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, italic=italic)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run(text)
    set_run_font(run, size={1: 16, 2: 14, 3: 14}[level], bold=True)
    return p


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = True
    for i, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], header, bold=True, size=11)
        set_cell_shading(table.rows[0].cells[i])
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], str(value), size=10.5)
    if widths:
        for row in table.rows:
            for i, width in enumerate(widths):
                row.cells[i].width = Cm(width)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def add_figure(doc, filename, caption, width_cm=16.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_after = Pt(3)
    run = p.add_run()
    run.add_picture(str(SCREENSHOTS / filename), width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.first_line_indent = Cm(0)
    cap.paragraph_format.line_spacing = 1.0
    r = cap.add_run(caption)
    set_run_font(r, size=12)


def add_page_break(doc):
    doc.add_page_break()


def build():
    doc = Document()
    configure_document(doc)

    # Title page.
    add_paragraph(doc, "Московский авиационный институт\n(национальный исследовательский университет)", center=True, indent=False, size=14, space_after=0)
    add_paragraph(doc, "Институт № 3, кафедра № 307", center=True, indent=False, size=14)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(100)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("ОТЧЁТ")
    set_run_font(r, size=16, bold=True)
    add_paragraph(doc, "по практическому заданию", center=True, indent=False, size=14)
    add_paragraph(doc, "Установка Docker Desktop, Portainer и nginx", center=True, indent=False, size=14, bold=True)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(150)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Выполнил: студент группы М3О-226СВ-25\nСунгатуллин Саид Рустамович\n\nМосква, 2026")
    set_run_font(r, size=14)
    add_page_break(doc)

    # Abstract and contents.
    add_heading(doc, "РЕФЕРАТ", 1)
    add_paragraph(doc, "Отчёт посвящён выполнению практического задания по контейнеризации приложений средствами Docker Desktop и Portainer. В работе развёрнут контейнер nginx и проверена публикация веб-сервиса на локальном порту.")
    add_paragraph(doc, "Приведены конфигурация образов, сопоставление портов, порядок проверки, снимки экрана работающих сервисов и результаты выполнения задания.")
    add_paragraph(doc, "Ключевые слова: Docker Desktop, Portainer, nginx, Docker, контейнер, порт.", indent=False)
    add_heading(doc, "СОДЕРЖАНИЕ", 1)
    for text in [
        "Введение ........................................................................ 3",
        "1 Цель и исходная конфигурация ................................. 3",
        "2 Выполнение задания ................................................ 4",
        "3 Доказательства выполнения ..................................... 5",
        "Заключение .................................................................. 7",
        "Список использованных источников ............................ 7",
    ]:
        add_paragraph(doc, text, indent=False, size=14)
    add_page_break(doc)

    add_heading(doc, "ВВЕДЕНИЕ", 1)
    add_paragraph(doc, "Цель задания — проверить установку Docker Desktop и Portainer, создать контейнер nginx, опубликовать его HTTP-порт на хостовой системе и подтвердить доступность стандартной страницы веб-сервера в браузере.")
    add_heading(doc, "1 Цель и исходная конфигурация", 2)
    add_paragraph(doc, "Работа выполнена в Docker-контексте desktop-linux. Управление контейнерами выполнялось через Docker Desktop и Portainer Community Edition. Для Portainer использованы HTTPS-порт 9443 и постоянный том portainer_data.")
    add_table(doc, ["Компонент", "Значение"], [
        ["Docker Engine", "29.1.3, контекст desktop-linux"],
        ["Docker Compose", "v5.0.1"],
        ["Portainer", "portainer/portainer-ce:lts, версия по журналу 2.45.1"],
        ["nginx", "nginx:1.30.5-alpine"],
        ["Имя контейнера", "nginx-lab"],
    ], [5, 11])
    add_paragraph(doc, "Контейнер Portainer создан с подключением Docker socket и тома конфигурации. Контейнер nginx запущен с политикой автоматического перезапуска unless-stopped.")
    add_heading(doc, "2 Выполнение задания", 2)
    add_paragraph(doc, "После запуска контейнера nginx выполнена проверка командой docker exec nginx-lab nginx -v. Получен результат: nginx/1.30.5. Из браузера открыта страница http://localhost:8088.")
    add_page_break(doc)

    add_heading(doc, "2 ВЫПОЛНЕНИЕ ЗАДАНИЯ", 1)
    add_heading(doc, "2.1 Конфигурация публикации портов", 3)
    add_table(doc, ["Сервис", "Порт контейнера", "Порт хоста", "Протокол", "Назначение"], [
        ["Portainer", "9443", "9443", "TCP/HTTPS", "Административный интерфейс"],
        ["Portainer Agent tunnel", "8000", "8000", "TCP", "Служебный порт"],
        ["nginx-lab", "80", "8088", "TCP/HTTP", "Проверка страницы nginx"],
    ], [3.2, 2.5, 2.2, 2.5, 5.6])
    add_heading(doc, "2.2 Сведения об образах", 3)
    add_table(doc, ["Образ", "Тег", "Digest"], [
        ["portainer/portainer-ce", "lts", "sha256:4d616db18cfeb5dd41a69c0958bc825c84483ea9cde1106eb82a5d26f3bd8b0e"],
        ["nginx", "1.30.5-alpine", "sha256:0985e772fb9f729e6fa0980da05fca5d9c468e870eed43071545afa9d2e27d94"],
    ], [5, 3, 10.5])
    add_paragraph(doc, "Фиксация тега и digest позволяет связать результат лабораторной работы с конкретными версиями контейнерных образов.")
    add_heading(doc, "2.3 Проверка страницы nginx", 3)
    add_paragraph(doc, "На странице отображается стандартное приветствие nginx. Адресная строка браузера содержит локальный адрес и опубликованный порт 8088.")
    add_paragraph(doc, "Команда запуска: docker run -d --name nginx-lab --restart unless-stopped -p 8088:80 nginx:1.30.5-alpine", indent=False, size=11)
    add_page_break(doc)

    add_heading(doc, "3 ДОКАЗАТЕЛЬСТВА ВЫПОЛНЕНИЯ", 1)
    add_figure(doc, "nginx_browser_full.png", "Рисунок 1 — Проверка стандартной страницы nginx по адресу http://localhost:8088", 16.5)
    add_page_break(doc)

    add_heading(doc, "3 ДОКАЗАТЕЛЬСТВА ВЫПОЛНЕНИЯ", 1)
    add_figure(doc, "portainer_nginx.png", "Рисунок 2 — Контейнер nginx-lab и опубликованный порт в Portainer", 16.5)
    add_paragraph(doc, "Снимок показывает контейнер nginx-lab в интерфейсе Portainer. Состояние контейнера — запущен, опубликованный порт — 8088:80/TCP.")
    add_page_break(doc)

    add_heading(doc, "ЗАКЛЮЧЕНИЕ", 1)
    add_paragraph(doc, "В ходе выполнения задания Docker Desktop и Portainer были установлены и проверены. В Portainer доступен локальный Docker environment. Создан контейнер nginx-lab на основе образа nginx:1.30.5-alpine. Внешний порт 8088 направлен на внутренний порт 80/TCP.")
    add_paragraph(doc, "Стандартная страница nginx успешно открыта в браузере по адресу http://localhost:8088. Имя образа, версия nginx, идентификатор образа и параметры публикации портов зафиксированы в отчёте и файле image-manifest.txt.")
    add_paragraph(doc, "Таким образом, задание выполнено полностью.")
    add_heading(doc, "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", 1)
    for text in [
        "1. Portainer Documentation. Install Portainer CE with Docker on Docker Desktop [Электронный ресурс]. URL: https://docs.portainer.io/start/install-ce/server/docker/wsl (дата обращения: 1 октября 2026 г.).",
        "2. Docker Docs. Docker run reference [Электронный ресурс]. URL: https://docs.docker.com/reference/cli/docker/container/run/ (дата обращения: 1 октября 2026 г.).",
        "3. nginx. Official Docker image [Электронный ресурс]. URL: https://hub.docker.com/_/nginx (дата обращения: 1 октября 2026 г.).",
    ]:
        p = add_paragraph(doc, text, indent=False, size=11)
        p.paragraph_format.left_indent = Cm(1.25)
        p.paragraph_format.first_line_indent = Cm(-1.25)

    doc.core_properties.author = "Сунгатуллин Саид Рустамович"
    doc.core_properties.title = "Установка Docker Desktop, Portainer и nginx"
    doc.core_properties.subject = "Практический отчёт"
    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
