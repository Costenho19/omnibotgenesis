import re
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable, KeepTogether, Preformatted
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import Flowable

# ── OMNIX Brand Colors ──────────────────────────────────────────────
NAVY      = colors.HexColor('#0A1628')
GOLD      = colors.HexColor('#C9A227')
LIGHT_GOLD= colors.HexColor('#E8D08A')
SLATE     = colors.HexColor('#2C3E50')
LIGHT_BG  = colors.HexColor('#F7F5F0')
MID_GRAY  = colors.HexColor('#8A8A8A')
DARK_GRAY = colors.HexColor('#444444')
WHITE     = colors.white
BOX_BG    = colors.HexColor('#0D1E35')
BOX_BORDER= colors.HexColor('#C9A227')

PAGE_W, PAGE_H = A4
MARGIN_L = 3.2 * cm
MARGIN_R = 2.8 * cm
MARGIN_T = 2.5 * cm
MARGIN_B = 2.5 * cm
TEXT_W   = PAGE_W - MARGIN_L - MARGIN_R

# ── Page template with header/footer ───────────────────────────────
class PageDecor:
    def __init__(self):
        self.page_num = 0

_decor = PageDecor()

def on_page(canvas, doc):
    _decor.page_num += 1
    canvas.saveState()
    # Header line
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.8)
    canvas.line(MARGIN_L, PAGE_H - MARGIN_T + 4*mm, PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 4*mm)
    # Header text
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(MID_GRAY)
    canvas.drawString(MARGIN_L, PAGE_H - MARGIN_T + 6*mm, 'GHOST COMPLIANCE')
    canvas.drawRightString(PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 6*mm, 'Harold Nunes / OMNIX Quantum')
    # Footer line
    canvas.line(MARGIN_L, MARGIN_B - 6*mm, PAGE_W - MARGIN_R, MARGIN_B - 6*mm)
    # Page number
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(MID_GRAY)
    canvas.drawCentredString(PAGE_W / 2, MARGIN_B - 11*mm, str(doc.page))
    canvas.restoreState()

def on_first_page(canvas, doc):
    canvas.saveState()
    canvas.restoreState()

# ── Styles ──────────────────────────────────────────────────────────
def build_styles():
    s = {}

    s['cover_title'] = ParagraphStyle('cover_title',
        fontName='Helvetica-Bold', fontSize=42, textColor=WHITE,
        leading=50, alignment=TA_CENTER, spaceAfter=8)

    s['cover_sub'] = ParagraphStyle('cover_sub',
        fontName='Helvetica', fontSize=16, textColor=GOLD,
        leading=22, alignment=TA_CENTER, spaceAfter=6)

    s['cover_author'] = ParagraphStyle('cover_author',
        fontName='Helvetica', fontSize=13, textColor=LIGHT_GOLD,
        leading=18, alignment=TA_CENTER, spaceAfter=4)

    s['part_label'] = ParagraphStyle('part_label',
        fontName='Helvetica-Bold', fontSize=10, textColor=GOLD,
        leading=14, alignment=TA_CENTER, spaceBefore=30, spaceAfter=6,
        letterSpacing=3)

    s['part_title'] = ParagraphStyle('part_title',
        fontName='Helvetica-Bold', fontSize=26, textColor=NAVY,
        leading=32, alignment=TA_CENTER, spaceBefore=4, spaceAfter=20)

    s['chapter_label'] = ParagraphStyle('chapter_label',
        fontName='Helvetica-Bold', fontSize=9, textColor=GOLD,
        leading=12, alignment=TA_LEFT, spaceBefore=24, spaceAfter=4,
        letterSpacing=2)

    s['chapter_title'] = ParagraphStyle('chapter_title',
        fontName='Helvetica-Bold', fontSize=22, textColor=NAVY,
        leading=28, alignment=TA_LEFT, spaceBefore=4, spaceAfter=6)

    s['chapter_subtitle'] = ParagraphStyle('chapter_subtitle',
        fontName='Helvetica', fontSize=14, textColor=SLATE,
        leading=20, alignment=TA_LEFT, spaceBefore=2, spaceAfter=14)

    s['section_h3'] = ParagraphStyle('section_h3',
        fontName='Helvetica-Bold', fontSize=13, textColor=NAVY,
        leading=18, spaceBefore=18, spaceAfter=6)

    s['section_h4'] = ParagraphStyle('section_h4',
        fontName='Helvetica-BoldOblique', fontSize=11, textColor=SLATE,
        leading=16, spaceBefore=12, spaceAfter=4)

    s['body'] = ParagraphStyle('body',
        fontName='Helvetica', fontSize=10.5, textColor=DARK_GRAY,
        leading=16.5, alignment=TA_JUSTIFY, spaceBefore=4, spaceAfter=6,
        firstLineIndent=0)

    s['body_italic'] = ParagraphStyle('body_italic',
        fontName='Helvetica-Oblique', fontSize=10.5, textColor=DARK_GRAY,
        leading=16.5, alignment=TA_JUSTIFY, spaceBefore=4, spaceAfter=6)

    s['blockquote'] = ParagraphStyle('blockquote',
        fontName='Helvetica-Oblique', fontSize=11, textColor=SLATE,
        leading=17, alignment=TA_LEFT, spaceBefore=10, spaceAfter=10,
        leftIndent=24, rightIndent=16, borderPadding=(6, 0, 6, 0))

    s['bullet'] = ParagraphStyle('bullet',
        fontName='Helvetica', fontSize=10.5, textColor=DARK_GRAY,
        leading=16.5, spaceBefore=2, spaceAfter=2,
        leftIndent=20, bulletIndent=8)

    s['code_block'] = ParagraphStyle('code_block',
        fontName='Courier', fontSize=8, textColor=LIGHT_GOLD,
        leading=11, spaceBefore=8, spaceAfter=8,
        leftIndent=10, rightIndent=10,
        backColor=BOX_BG)

    s['caption'] = ParagraphStyle('caption',
        fontName='Helvetica-Oblique', fontSize=9, textColor=MID_GRAY,
        leading=13, alignment=TA_CENTER, spaceBefore=4, spaceAfter=12)

    s['hr_label'] = ParagraphStyle('hr_label',
        fontName='Helvetica-Bold', fontSize=8, textColor=GOLD,
        leading=12, alignment=TA_CENTER, spaceBefore=12, spaceAfter=12,
        letterSpacing=2)

    s['footer_copy'] = ParagraphStyle('footer_copy',
        fontName='Helvetica-Oblique', fontSize=9, textColor=MID_GRAY,
        leading=14, alignment=TA_CENTER, spaceBefore=6, spaceAfter=4)

    s['toc_part'] = ParagraphStyle('toc_part',
        fontName='Helvetica-Bold', fontSize=11, textColor=NAVY,
        leading=16, spaceBefore=8, spaceAfter=2)

    s['toc_ch'] = ParagraphStyle('toc_ch',
        fontName='Helvetica', fontSize=10, textColor=DARK_GRAY,
        leading=15, spaceBefore=1, spaceAfter=1, leftIndent=16)

    return s

# ── Cover page ──────────────────────────────────────────────────────
def build_cover(styles):
    elems = []
    elems.append(Spacer(1, 3.5*cm))

    # Gold top rule
    elems.append(HRFlowable(width='100%', thickness=3, color=GOLD, spaceAfter=20))

    elems.append(Paragraph('GHOST', styles['cover_title']))
    elems.append(Paragraph('COMPLIANCE', styles['cover_title']))
    elems.append(Spacer(1, 0.4*cm))
    elems.append(HRFlowable(width='60%', thickness=1, color=GOLD, spaceAfter=16))
    elems.append(Paragraph('La Infraestructura de Gobernanza Que los Mercados Aún No Han Construido', styles['cover_sub']))
    elems.append(Spacer(1, 2*cm))
    elems.append(Paragraph('Harold Nunes', styles['cover_author']))
    elems.append(Spacer(1, 0.3*cm))
    elems.append(Paragraph('OMNIX Quantum', ParagraphStyle('omx', fontName='Helvetica-Bold',
        fontSize=11, textColor=GOLD, alignment=TA_CENTER)))
    elems.append(Spacer(1, 4*cm))
    elems.append(HRFlowable(width='100%', thickness=1.5, color=GOLD, spaceAfter=12))
    elems.append(Paragraph('© 2026 Harold Nunes / OMNIX Quantum · omnixquantum.net', styles['footer_copy']))
    elems.append(PageBreak())
    return elems

# ── Markdown parser → ReportLab flowables ──────────────────────────
def inline_fmt(text, base_style_name='body'):
    """Convert inline **bold**, *italic*, `code` markers to ReportLab XML."""
    # Escape XML special chars first
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # Bold+italic ***
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<b><i>\1</i></b>', text)
    # Bold **
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Italic *
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Inline code `
    text = re.sub(r'`([^`]+)`', r'<font name="Courier" color="#C9A227">\1</font>', text)
    # Em-dash, en-dash
    text = text.replace('---', '—').replace('--', '–')
    return text

def parse_md(md_text, styles):
    lines = md_text.split('\n')
    elems = []
    i = 0
    in_code = False
    code_buf = []
    in_list = False

    def flush_list():
        pass  # handled inline

    while i < len(lines):
        line = lines[i]

        # ── Code block ──────────────────────────────────────────
        if line.strip().startswith('```'):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                code_text = '\n'.join(code_buf)
                # Use Preformatted with styling
                pre_style = ParagraphStyle('pre',
                    fontName='Courier', fontSize=7.5, textColor=LIGHT_GOLD,
                    leading=10.5, backColor=BOX_BG,
                    leftIndent=10, rightIndent=10,
                    spaceBefore=10, spaceAfter=10,
                    borderPadding=(8, 8, 8, 8))
                # Split into lines and render each
                elems.append(Spacer(1, 6))
                code_lines = code_text.split('\n')
                tbl_data = []
                for cl in code_lines:
                    cl_safe = cl.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    tbl_data.append([Paragraph(cl_safe, ParagraphStyle('cl',
                        fontName='Courier', fontSize=7.5, textColor=LIGHT_GOLD,
                        leading=10.5, leftIndent=0))])
                if tbl_data:
                    t = Table(tbl_data, colWidths=[TEXT_W - 1*cm])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), BOX_BG),
                        ('LEFTPADDING', (0,0), (-1,-1), 12),
                        ('RIGHTPADDING', (0,0), (-1,-1), 12),
                        ('TOPPADDING', (0,0), (0,0), 10),
                        ('BOTTOMPADDING', (-1,-1), (-1,-1), 10),
                        ('TOPPADDING', (0,1), (-1,-1), 2),
                        ('BOTTOMPADDING', (0,0), (-1,-2), 2),
                        ('BOX', (0,0), (-1,-1), 1.2, GOLD),
                    ]))
                    elems.append(t)
                    elems.append(Spacer(1, 8))
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        stripped = line.strip()

        # ── Horizontal rule ─────────────────────────────────────
        if stripped in ('---', '***', '___') or re.match(r'^-{3,}$', stripped):
            elems.append(Spacer(1, 6))
            elems.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))
            i += 1
            continue

        # ── Empty line ──────────────────────────────────────────
        if not stripped:
            i += 1
            continue

        # ── PARTE / PART heading (## PARTE ...) ────────────────
        if re.match(r'^## (PARTE|PART) ', stripped):
            elems.append(PageBreak())
            label_txt = re.sub(r'^##\s+', '', stripped)
            elems.append(Spacer(1, 1.5*cm))
            elems.append(HRFlowable(width='100%', thickness=2, color=GOLD, spaceAfter=16))
            elems.append(Paragraph(inline_fmt(label_txt), styles['part_title']))
            elems.append(HRFlowable(width='100%', thickness=1, color=GOLD, spaceAfter=20))
            i += 1
            continue

        # ── CAPÍTULO / CHAPTER / INTERMEDIO / INTERLUDE / APÉNDICE / APPENDIX / EPÍLOGO / EPILOGUE ──
        if re.match(r'^# (CAPÍTULO|CHAPTER|INTERMEDIO|INTERLUDE|APÉNDICE|APPENDIX|EPÍLOGO|EPILOGUE)', stripped):
            elems.append(PageBreak())
            label = re.sub(r'^# ', '', stripped)
            elems.append(Spacer(1, 1*cm))
            elems.append(Paragraph(label, styles['chapter_label']))
            # Check if next line is ## subtitle
            if i + 1 < len(lines) and lines[i+1].startswith('## '):
                i += 1
                subtitle = re.sub(r'^## ', '', lines[i].strip())
                elems.append(Paragraph(inline_fmt(subtitle), styles['chapter_title']))
            elems.append(HRFlowable(width='60%', thickness=1.5, color=GOLD, spaceAfter=14))
            i += 1
            continue

        # ── H2 (##) ─────────────────────────────────────────────
        if stripped.startswith('## '):
            txt = re.sub(r'^## ', '', stripped)
            elems.append(Spacer(1, 6))
            elems.append(Paragraph(inline_fmt(txt), styles['chapter_subtitle']))
            i += 1
            continue

        # ── H3 (###) ────────────────────────────────────────────
        if stripped.startswith('### '):
            txt = re.sub(r'^### ', '', stripped)
            elems.append(Paragraph(inline_fmt(txt), styles['section_h3']))
            i += 1
            continue

        # ── H4 (####) ───────────────────────────────────────────
        if stripped.startswith('#### '):
            txt = re.sub(r'^#### ', '', stripped)
            elems.append(Paragraph(inline_fmt(txt), styles['section_h4']))
            i += 1
            continue

        # ── Blockquote (>) ──────────────────────────────────────
        if stripped.startswith('>'):
            # Collect consecutive blockquote lines
            bq_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                bq_lines.append(lines[i].strip().lstrip('>').strip())
                i += 1
            bq_text = ' '.join(bl for bl in bq_lines if bl)
            if bq_text:
                # Gold left bar via table
                bq_p = Paragraph(inline_fmt(bq_text), styles['blockquote'])
                t = Table([[bq_p]], colWidths=[TEXT_W - 0.8*cm])
                t.setStyle(TableStyle([
                    ('LEFTPADDING', (0,0), (-1,-1), 14),
                    ('RIGHTPADDING', (0,0), (-1,-1), 8),
                    ('TOPPADDING', (0,0), (-1,-1), 6),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('LINEBEFORE', (0,0), (0,-1), 3, GOLD),
                    ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
                ]))
                elems.append(t)
                elems.append(Spacer(1, 4))
            continue

        # ── Bullet list (- or *) ────────────────────────────────
        if re.match(r'^[-*]\s', stripped):
            bullet_text = re.sub(r'^[-*]\s+', '', stripped)
            p = Paragraph('• ' + inline_fmt(bullet_text), styles['bullet'])
            elems.append(p)
            i += 1
            continue

        # ── Numbered list ───────────────────────────────────────
        if re.match(r'^\d+\.\s', stripped):
            num_text = re.sub(r'^\d+\.\s+', '', stripped)
            match = re.match(r'^(\d+)\.', stripped)
            num = match.group(1) if match else '•'
            p = Paragraph(f'{num}. ' + inline_fmt(num_text), styles['bullet'])
            elems.append(p)
            i += 1
            continue

        # ── [GRÁFICO] / [GRAPHIC] captions ──────────────────────
        if stripped.startswith('**[') and stripped.endswith(']**'):
            txt = stripped.strip('*').strip('[').strip(']')
            elems.append(Spacer(1, 8))
            elems.append(Paragraph(f'[ {txt} ]', styles['caption']))
            elems.append(Spacer(1, 8))
            i += 1
            continue

        # ── Regular paragraph ────────────────────────────────────
        if stripped:
            elems.append(Paragraph(inline_fmt(stripped), styles['body']))

        i += 1

    return elems

# ── Main ─────────────────────────────────────────────────────────────
def main():
    input_file  = 'ghost_compliance_ES.md'
    output_file = 'Ghost_Compliance_ES.pdf'

    print(f'Leyendo {input_file}...')
    with open(input_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    styles = build_styles()

    print('Construyendo PDF...')
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B,
        title='Ghost Compliance',
        author='Harold Nunes',
        subject='Gobernanza de IA y Cumplimiento',
        creator='OMNIX Quantum',
    )

    story = []

    # Cover
    story.extend(build_cover(styles))

    # Body
    story.extend(parse_md(md_text, styles))

    # Build
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_page)
    print(f'✓ PDF generado: {output_file}')

if __name__ == '__main__':
    main()
