#!/usr/bin/env python3
"""
Generate professional PDFs from OMNIX business markdown documents for José Salvador.
Uses fpdf2 for PDF generation with clean, readable formatting.
"""
import re
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FONT_DIR = os.path.join(
    os.path.expanduser("~"),
    "workspace/.pythonlibs/lib/python3.11/site-packages/kaleido/executable/xdg/fonts/truetype/dejavu"
)
FONT_REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
FONT_MONO = os.path.join(FONT_DIR, "DejaVuSansMono.ttf")
FONT_MONO_BOLD = os.path.join(FONT_DIR, "DejaVuSansMono-Bold.ttf")
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "business", "pdfs")

DOCUMENTS = [
    {
        "input": os.path.join(BASE_DIR, "docs", "business", "EXECUTIVE_FACT_SHEET.md"),
        "output": os.path.join(OUTPUT_DIR, "OMNIX_Executive_Fact_Sheet.pdf"),
        "title": "OMNIX — Executive Fact Sheet",
    },
    {
        "input": os.path.join(BASE_DIR, "docs", "business", "OMNIX_EUREKA_PITCH_FINAL.md"),
        "output": os.path.join(OUTPUT_DIR, "OMNIX_Eureka_Pitch_Final.pdf"),
        "title": "OMNIX — Eureka Dubai Pitch",
    },
    {
        "input": os.path.join(BASE_DIR, "docs", "business", "EUREKA_PRESENTATION_SCRIPT.md"),
        "output": os.path.join(OUTPUT_DIR, "OMNIX_Presentation_Script_Jose.pdf"),
        "title": "OMNIX — Presentation Script (José Salvador)",
    },
    {
        "input": os.path.join(BASE_DIR, "docs", "business", "investor", "OMNIX_5YEAR_FINANCIAL_MODEL.md"),
        "output": os.path.join(OUTPUT_DIR, "OMNIX_5Year_Financial_Model.pdf"),
        "title": "OMNIX — 5-Year Financial Model",
    },
    {
        "input": os.path.join(BASE_DIR, "docs", "business", "OMNIX_EUREKA_PITCH_HAROLD.md"),
        "output": os.path.join(OUTPUT_DIR, "OMNIX_Eureka_Pitch_Harold.pdf"),
        "title": "OMNIX — Eureka GCC 2026 Pitch Script (Harold Nunes)",
    },
]

DATE_LABEL = "March 2026 | Confidential"

DARK = (20, 20, 40)
ACCENT = (0, 80, 160)
LIGHT_GRAY = (245, 245, 248)
MID_GRAY = (180, 180, 190)
WHITE = (255, 255, 255)
TABLE_HEADER = (0, 60, 120)


def safe(text):
    """Replace Unicode characters that may cause issues, normalize for PDF output."""
    replacements = {
        "\u2014": "--", "\u2013": "-", "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "*",
        "\u00b0": "deg", "\u00ae": "(R)", "\u2122": "(TM)",
        "\u00e9": "e", "\u00e1": "a", "\u00f3": "o", "\u00fa": "u",
        "\u00ed": "i", "\u00f1": "n",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


class OmnixPDF(FPDF):
    def __init__(self, doc_title):
        super().__init__()
        self.doc_title = doc_title
        self.set_margins(20, 18, 20)
        self.set_auto_page_break(auto=True, margin=18)
        self.add_font("DejaVu", style="", fname=FONT_REGULAR)
        self.add_font("DejaVu", style="B", fname=FONT_BOLD)
        self.add_font("DejaVuMono", style="", fname=FONT_MONO)
        self.add_font("DejaVuMono", style="B", fname=FONT_MONO_BOLD)

    def header(self):
        self.set_font("DejaVu", "B", 8)
        self.set_text_color(*ACCENT)
        self.cell(0, 6, "OMNIX -- Decision Governance Infrastructure", align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)

    def footer(self):
        self.set_y(-14)
        self.set_font("DejaVu", "", 7)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 5, f"{DATE_LABEL}  |  {safe(self.doc_title)}", align="L", new_x=XPos.RIGHT)
        self.cell(0, 5, f"Page {self.page_no()}", align="R")


def strip_html(text):
    return re.sub(r"<[^>]+>", "", text)


def clean_line(line):
    line = strip_html(line)
    line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
    line = re.sub(r"\*(.+?)\*", r"\1", line)
    line = re.sub(r"`(.+?)`", r"\1", line)
    line = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", line)
    return line.strip()


def is_table_row(line):
    return line.strip().startswith("|") and line.strip().endswith("|")


def is_separator_row(line):
    return bool(re.match(r"^\s*\|[-\s|:]+\|\s*$", line))


def parse_table_row(line):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return [clean_line(c) for c in cells]


def render_markdown(pdf, text):
    lines = text.split("\n")
    i = 0
    in_code_block = False
    in_blockquote = False
    table_lines = []

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()

        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if not in_code_block:
                pdf.ln(2)
            i += 1
            continue

        if in_code_block:
            pdf.set_font("DejaVuMono", "", 7.5)
            pdf.set_fill_color(*LIGHT_GRAY)
            pdf.set_text_color(*DARK)
            safe_line = safe(line) if line else " "
            pdf.multi_cell(0, 5, safe_line, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            i += 1
            continue

        if is_table_row(line):
            table_lines.append(line)
            i += 1
            continue
        elif table_lines:
            render_table(pdf, table_lines)
            table_lines = []

        stripped = line.strip()

        if not stripped:
            if in_blockquote:
                in_blockquote = False
            pdf.ln(2)
            i += 1
            continue

        if stripped.startswith("> "):
            quote_text = clean_line(stripped[2:])
            pdf.set_fill_color(*LIGHT_GRAY)
            pdf.set_draw_color(*ACCENT)
            pdf.set_line_width(1.0)
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.set_x(pdf.l_margin + 4)
            pdf.set_font("DejaVu", "", 9)
            pdf.set_text_color(60, 60, 80)
            pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 4, 5.5, safe(quote_text), fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.line(pdf.l_margin, y, pdf.l_margin, pdf.get_y())
            pdf.ln(1)
            i += 1
            continue

        if stripped.startswith("---"):
            pdf.set_draw_color(*MID_GRAY)
            pdf.set_line_width(0.3)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(3)
            i += 1
            continue

        h_match = re.match(r"^(#{1,4})\s+(.*)", stripped)
        if h_match:
            level = len(h_match.group(1))
            heading = clean_line(h_match.group(2))
            if level == 1:
                pdf.ln(3)
                pdf.set_fill_color(*ACCENT)
                pdf.set_text_color(*WHITE)
                pdf.set_font("DejaVu", "B", 13)
                pdf.cell(0, 10, f"  {safe(heading)}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(3)
            elif level == 2:
                pdf.ln(4)
                pdf.set_text_color(*ACCENT)
                pdf.set_font("DejaVu", "B", 11)
                pdf.cell(0, 7, safe(heading), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_draw_color(*ACCENT)
                pdf.set_line_width(0.3)
                pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 60, pdf.get_y())
                pdf.ln(2)
            elif level == 3:
                pdf.ln(3)
                pdf.set_text_color(*DARK)
                pdf.set_font("DejaVu", "B", 9.5)
                pdf.cell(0, 6, safe(heading), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.ln(1)
            else:
                pdf.ln(2)
                pdf.set_text_color(*DARK)
                pdf.set_font("DejaVu", "B", 9)
                pdf.cell(0, 5, safe(heading), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(*DARK)
            i += 1
            continue

        bullet_match = re.match(r"^(\s*)[-*]\s+(.*)", stripped)
        if bullet_match:
            indent = len(re.match(r"^(\s*)", raw).group(1))
            content = clean_line(bullet_match.group(2))
            level_indent = min(indent // 2, 3)
            bullet_x = pdf.l_margin + 4 + level_indent * 5
            pdf.set_x(bullet_x)
            pdf.set_font("DejaVu", "", 9)
            pdf.set_text_color(*DARK)
            pdf.multi_cell(pdf.w - bullet_x - pdf.r_margin, 5.5, f"*  {safe(content)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            i += 1
            continue

        num_match = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if num_match:
            num = num_match.group(1)
            content = clean_line(num_match.group(2))
            pdf.set_x(pdf.l_margin + 4)
            pdf.set_font("DejaVu", "", 9)
            pdf.set_text_color(*DARK)
            pdf.multi_cell(pdf.w - pdf.l_margin - pdf.r_margin - 4, 5.5, f"{num}. {safe(content)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            i += 1
            continue

        clean = clean_line(stripped)
        if clean:
            pdf.set_font("DejaVu", "", 9)
            pdf.set_text_color(*DARK)
            pdf.multi_cell(0, 5.5, safe(clean), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        i += 1

    if table_lines:
        render_table(pdf, table_lines)


def render_table(pdf, table_lines):
    rows = []
    is_header_row = True
    for line in table_lines:
        if is_separator_row(line):
            is_header_row = False
            continue
        rows.append((parse_table_row(line), is_header_row))
        if is_header_row:
            is_header_row = False

    if not rows:
        return

    usable_w = pdf.w - pdf.l_margin - pdf.r_margin
    all_cells = [row[0] for row in rows]
    if not all_cells:
        return

    num_cols = max(len(r) for r in all_cells)
    if num_cols == 0:
        return

    col_w = usable_w / num_cols

    pdf.ln(2)
    for cells, is_header in rows:
        while len(cells) < num_cols:
            cells.append("")

        if is_header:
            pdf.set_fill_color(*TABLE_HEADER)
            pdf.set_text_color(*WHITE)
            pdf.set_font("DejaVu", "B", 8)
        else:
            pdf.set_fill_color(*LIGHT_GRAY)
            pdf.set_text_color(*DARK)
            pdf.set_font("DejaVu", "", 8)

        row_y = pdf.get_y()
        max_lines = 1
        for cell in cells:
            estimated = max(1, len(cell) // 30 + 1)
            max_lines = max(max_lines, estimated)

        row_h = max_lines * 5 + 3

        for j, cell in enumerate(cells):
            x = pdf.l_margin + j * col_w
            pdf.set_xy(x, row_y)
            pdf.multi_cell(col_w, row_h / max_lines, safe(cell), fill=True, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)

        pdf.set_y(row_y + row_h)

    pdf.ln(3)


def generate_pdf(input_path, output_path, doc_title):
    print(f"Generating: {os.path.basename(output_path)} ...")

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    pdf = OmnixPDF(doc_title)
    pdf.add_page()

    pdf.set_fill_color(*DARK)
    pdf.rect(pdf.l_margin - 20, pdf.get_y(), pdf.w, 22, "F")
    pdf.set_text_color(*WHITE)
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_x(pdf.l_margin)
    pdf.cell(0, 12, safe(doc_title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(180, 200, 230)
    pdf.cell(0, 6, f"OMNIX Decision Governance Infrastructure  |  {DATE_LABEL}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)
    pdf.set_text_color(*DARK)

    render_markdown(pdf, content)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    size_kb = os.path.getsize(output_path) // 1024
    print(f"  Done: {output_path} ({size_kb} KB)")


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for doc in DOCUMENTS:
        try:
            generate_pdf(doc["input"], doc["output"], doc["title"])
        except Exception as e:
            print(f"  ERROR on {doc['input']}: {e}")
            import traceback
            traceback.print_exc()
    print("\nAll PDFs generated.")
