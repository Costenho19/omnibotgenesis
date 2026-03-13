"""
OMNIX Eureka Pitch Deck — PDF Generator
Generates professional PDF from OMNIX_EUREKA_PITCH_FINAL.md
"""

import os
import re
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas as pdf_canvas

DARK_BG      = HexColor('#0a0f1a')
DARK_MID     = HexColor('#0f172a')
CARD_BG      = HexColor('#1e293b')
GOLD         = HexColor('#C9A227')
GOLD_LIGHT   = HexColor('#F5D97A')
RED_ALERT    = HexColor('#ef4444')
GREEN_OK     = HexColor('#10b981')
YELLOW_WARN  = HexColor('#f59e0b')
LIGHT_GRAY   = HexColor('#94a3b8')
WHITE        = HexColor('#ffffff')
BLUE_ACCENT  = HexColor('#3b82f6')


class SlideHeader(Flowable):
    def __init__(self, text, width=None):
        Flowable.__init__(self)
        self.text = text
        self.width = width or 7 * inch
        self.height = 0.5 * inch

    def draw(self):
        self.canv.setFillColor(GOLD)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        self.canv.setFillColor(DARK_BG)
        self.canv.setFont("Helvetica-Bold", 14)
        self.canv.drawString(0.2 * inch, 0.15 * inch, self.text)


def dark_page(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFillColor(DARK_BG)
    canvas_obj.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
    canvas_obj.setFillColor(GOLD)
    canvas_obj.setFont("Helvetica", 7)
    canvas_obj.drawString(0.75 * inch, 0.4 * inch, "OMNIX Decision Governance Infrastructure")
    canvas_obj.drawRightString(letter[0] - 0.75 * inch, 0.4 * inch, "omnixquantum.net")
    canvas_obj.drawCentredString(letter[0] / 2, 0.4 * inch, f"Generated {datetime.now(timezone.utc).strftime('%B %d, %Y')}")
    canvas_obj.restoreState()


_cached_styles = None

def get_styles():
    global _cached_styles
    if _cached_styles:
        return _cached_styles

    styles = getSampleStyleSheet()

    custom = {
        'SlideTitle': ParagraphStyle(
            'SlideTitle', fontName='Helvetica-Bold', fontSize=20,
            textColor=GOLD, spaceAfter=6, spaceBefore=12, alignment=TA_LEFT
        ),
        'SlideSubtitle': ParagraphStyle(
            'SlideSubtitle', fontName='Helvetica-Bold', fontSize=13,
            textColor=WHITE, spaceAfter=4, spaceBefore=8, alignment=TA_LEFT
        ),
        'BodyText2': ParagraphStyle(
            'BodyText2', fontName='Helvetica', fontSize=9.5,
            textColor=LIGHT_GRAY, spaceAfter=4, spaceBefore=2,
            alignment=TA_JUSTIFY, leading=13
        ),
        'BoldBody': ParagraphStyle(
            'BoldBody', fontName='Helvetica-Bold', fontSize=10,
            textColor=WHITE, spaceAfter=4, spaceBefore=4, alignment=TA_LEFT
        ),
        'Quote2': ParagraphStyle(
            'Quote2', fontName='Helvetica-Oblique', fontSize=9,
            textColor=GOLD_LIGHT, spaceAfter=6, spaceBefore=6,
            leftIndent=20, rightIndent=20, alignment=TA_LEFT, leading=12
        ),
        'CodeBlock': ParagraphStyle(
            'CodeBlock', fontName='Courier', fontSize=7.5,
            textColor=HexColor('#e2e8f0'), spaceAfter=4, spaceBefore=4,
            leftIndent=10, leading=10, backColor=CARD_BG
        ),
        'TitleSlide': ParagraphStyle(
            'TitleSlide', fontName='Helvetica-Bold', fontSize=32,
            textColor=GOLD, spaceAfter=4, spaceBefore=60, alignment=TA_CENTER
        ),
        'TitleSub': ParagraphStyle(
            'TitleSub', fontName='Helvetica', fontSize=14,
            textColor=LIGHT_GRAY, spaceAfter=10, spaceBefore=4, alignment=TA_CENTER
        ),
        'TableCell': ParagraphStyle(
            'TableCell', fontName='Helvetica', fontSize=8,
            textColor=WHITE, leading=10
        ),
        'TableHeader': ParagraphStyle(
            'TableHeader', fontName='Helvetica-Bold', fontSize=8,
            textColor=GOLD, leading=10
        ),
    }

    for name, style in custom.items():
        if name not in styles.byName:
            styles.add(style)
        else:
            styles.byName[name] = style

    _cached_styles = styles
    return styles


def make_table(headers, rows, col_widths=None):
    if not col_widths:
        n = len(headers)
        col_widths = [6.5 * inch / n] * n

    styles_obj = get_styles()

    header_cells = [Paragraph(h, styles_obj['TableHeader']) for h in headers]
    data_rows = []
    for row in rows:
        data_rows.append([Paragraph(str(c), styles_obj['TableCell']) for c in row])

    table = Table([header_cells] + data_rows, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a2332')),
        ('BACKGROUND', (0, 1), (-1, -1), CARD_BG),
        ('TEXTCOLOR', (0, 0), (-1, -1), WHITE),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#334155')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    return table


def parse_md_and_build(md_path, output_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    styles = get_styles()
    elements = []

    elements.append(Spacer(1, 1.5 * inch))
    elements.append(Paragraph("OMNIX", styles['TitleSlide']))
    elements.append(Paragraph("Decision Governance Infrastructure", styles['TitleSub']))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph('"The best decision is often the one you don\'t make."', styles['Quote2']))
    elements.append(Spacer(1, 0.8 * inch))
    elements.append(Paragraph("Harold Nunes — Founder &amp; Product Architect", styles['TitleSub']))
    elements.append(Paragraph("Pre-Seed | March 2026", styles['TitleSub']))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("contacto@omnixquantum.net | www.omnixquantum.net", styles['TitleSub']))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(HRFlowable(width="80%", thickness=1, color=GOLD, spaceAfter=6))
    elements.append(Paragraph("Eureka Dubai 2026 — Semifinalist", styles['TitleSub']))
    elements.append(PageBreak())

    slides = re.split(r'^## SLIDE \d+', content, flags=re.MULTILINE)
    slide_headers = re.findall(r'^## (SLIDE \d+ — .+)$', content, flags=re.MULTILINE)

    for i, (header, slide_content) in enumerate(zip(slide_headers, slides[1:])):
        clean_title = header.replace('SLIDE ', '').strip()

        elements.append(SlideHeader(clean_title))
        elements.append(Spacer(1, 0.15 * inch))

        lines = slide_content.strip().split('\n')
        in_code = False
        code_lines = []
        in_table = False
        table_lines = []

        for line in lines:
            stripped = line.strip()

            if stripped.startswith('```'):
                if in_code:
                    code_text = '<br/>'.join(
                        l.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace(' ', '&nbsp;')
                        for l in code_lines
                    )
                    elements.append(Paragraph(code_text, styles['CodeBlock']))
                    code_lines = []
                    in_code = False
                else:
                    in_code = True
                continue

            if in_code:
                code_lines.append(line)
                continue

            if stripped.startswith('|') and '|' in stripped[1:]:
                if stripped.replace('|', '').replace('-', '').replace(':', '').replace(' ', '') == '':
                    continue
                table_lines.append(stripped)
                in_table = True
                continue
            elif in_table:
                cells = [c.strip() for c in table_lines[0].split('|')[1:-1]]
                headers_list = cells
                rows_list = []
                for tl in table_lines[1:]:
                    row_cells = [c.strip() for c in tl.split('|')[1:-1]]
                    rows_list.append(row_cells)
                if headers_list and rows_list:
                    n_cols = len(headers_list)
                    widths = [6.5 * inch / n_cols] * n_cols
                    elements.append(make_table(headers_list, rows_list, widths))
                    elements.append(Spacer(1, 0.1 * inch))
                table_lines = []
                in_table = False

            if not stripped or stripped.startswith('---'):
                continue

            if stripped.startswith('### '):
                text = stripped[4:].replace('**', '').strip()
                elements.append(Paragraph(text, styles['SlideSubtitle']))
            elif stripped.startswith('> '):
                text = stripped[2:].replace('**', '').replace('*', '').strip()
                elements.append(Paragraph(f'"{text}"', styles['Quote2']))
            elif stripped.startswith('- '):
                text = stripped[2:]
                text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
                elements.append(Paragraph(f"• {text}", styles['BodyText2']))
            elif stripped.startswith('**') and stripped.endswith('**'):
                text = stripped.strip('*')
                elements.append(Paragraph(text, styles['BoldBody']))
            elif stripped.startswith('#'):
                continue
            else:
                text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', stripped)
                text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
                if text.strip():
                    elements.append(Paragraph(text, styles['BodyText2']))

        if in_table and table_lines:
            cells = [c.strip() for c in table_lines[0].split('|')[1:-1]]
            headers_list = cells
            rows_list = []
            for tl in table_lines[1:]:
                row_cells = [c.strip() for c in tl.split('|')[1:-1]]
                rows_list.append(row_cells)
            if headers_list and rows_list:
                n_cols = len(headers_list)
                widths = [6.5 * inch / n_cols] * n_cols
                elements.append(make_table(headers_list, rows_list, widths))

        elements.append(PageBreak())

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch
    )

    doc.build(elements, onFirstPage=dark_page, onLaterPages=dark_page)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"Generated: {output_path} ({size_kb:.0f} KB)")


if __name__ == '__main__':
    os.makedirs('docs/business/pdf', exist_ok=True)

    parse_md_and_build(
        'docs/business/OMNIX_EUREKA_PITCH_FINAL.md',
        'docs/business/pdf/OMNIX_Eureka_Pitch_Final.pdf'
    )

    _cached_styles = None

    parse_md_and_build(
        'docs/business/OMNIX_EUREKA_PITCH_FINAL_ES.md',
        'docs/business/pdf/OMNIX_Eureka_Pitch_Final_ES.pdf'
    )

    print("Done — both EN and ES PDFs generated.")
