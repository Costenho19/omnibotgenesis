"""
Ghost Compliance — Generador PDF Premium v3
Target: ~220 páginas · Cajas sin Unicode · Gráficos reales · TOC
"""
import re, os
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'omnix_web', 'public', 'book_logo.png')
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable, KeepTogether, Image
)

# ── Brand ─────────────────────────────────────────────────────────────
NAVY       = colors.HexColor('#0A1628')
NAVY_MID   = colors.HexColor('#0D1E35')
GOLD       = colors.HexColor('#C9A227')
GOLD_LIGHT = colors.HexColor('#E8D08A')
SLATE      = colors.HexColor('#2C3E50')
LIGHT_BG   = colors.HexColor('#F4F1EB')
MID_GRAY   = colors.HexColor('#888888')
DARK_GRAY  = colors.HexColor('#2A2A2A')
WHITE      = colors.white

PAGE_W, PAGE_H = A4
ML = 4.0*cm; MR = 3.8*cm; MT = 3.2*cm; MB = 3.2*cm
TW = PAGE_W - ML - MR

IMG_DIR = '/tmp/book_imgs'
GRAPHIC_MAP = {
    '01':'01_ghost_compliance.png', '02':'02_avm_signals.png',
    '03':'03_architecture.png',     '04':'04_nine_domains.png',
    '05':'05_forensic_trail.png',   '06':'06_pqc_timeline.png',
    '07':'07_mica_framework.png',   '08':'08_vara_framework.png',
    '09':'09_eu_ai_act.png',        '10':'10_case_study_failures.png',
    '11':'11_vision_2035.png',
}

# ── Page callbacks ────────────────────────────────────────────────────
def on_later_pages(canvas, doc):
    canvas.saveState()
    y_top = PAGE_H - MT + 6*mm
    canvas.setStrokeColor(GOLD); canvas.setLineWidth(0.7)
    canvas.line(ML, y_top, PAGE_W - MR, y_top)
    canvas.setFont('Helvetica', 7); canvas.setFillColor(MID_GRAY)
    canvas.drawString(ML, y_top + 3*mm, 'GHOST COMPLIANCE')
    canvas.drawRightString(PAGE_W - MR, y_top + 3*mm, 'Harold Nunes / OMNIX Quantum')
    y_bot = MB - 8*mm
    canvas.line(ML, y_bot, PAGE_W - MR, y_bot)
    canvas.drawCentredString(PAGE_W/2, y_bot - 4.5*mm, str(doc.page))
    canvas.restoreState()

def on_first_page(canvas, doc):
    """Full-bleed premium cover image on page 1."""
    canvas.saveState()
    cover = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cover_en.png')
    if os.path.exists(cover):
        canvas.drawImage(cover, 0, 0, PAGE_W, PAGE_H, preserveAspectRatio=False)
    else:
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.restoreState()

# ── Styles (generous for 220 pages) ──────────────────────────────────
def build_styles():
    B  = 'Helvetica-Bold'
    R  = 'Helvetica'
    BI = 'Helvetica-BoldOblique'
    I  = 'Helvetica-Oblique'
    C  = 'Courier'
    CB = 'Courier-Bold'

    return dict(
        # Cover
        cover_title  = ParagraphStyle('ct',  fontName=B, fontSize=52, textColor=WHITE,    leading=62, alignment=TA_CENTER),
        cover_sub    = ParagraphStyle('cs',  fontName=R, fontSize=18, textColor=GOLD,     leading=26, alignment=TA_CENTER),
        cover_author = ParagraphStyle('ca',  fontName=B, fontSize=14, textColor=GOLD_LIGHT,leading=22, alignment=TA_CENTER),
        cover_brand  = ParagraphStyle('cb',  fontName=R, fontSize=12, textColor=GOLD,     leading=18, alignment=TA_CENTER),
        cover_copy   = ParagraphStyle('cc',  fontName=I, fontSize=9,  textColor=MID_GRAY, leading=14, alignment=TA_CENTER),

        # Parts
        part_label   = ParagraphStyle('pl',  fontName=B, fontSize=10, textColor=GOLD,     leading=15, alignment=TA_CENTER, spaceBefore=30, spaceAfter=8),
        part_title   = ParagraphStyle('pt',  fontName=B, fontSize=30, textColor=NAVY,     leading=38, alignment=TA_CENTER, spaceAfter=20),

        # Chapters
        ch_label     = ParagraphStyle('chl', fontName=B, fontSize=10, textColor=GOLD,     leading=15, alignment=TA_LEFT,   spaceBefore=24, spaceAfter=6),
        ch_title     = ParagraphStyle('cht', fontName=B, fontSize=26, textColor=NAVY,     leading=34, alignment=TA_LEFT,   spaceAfter=6),
        ch_subtitle  = ParagraphStyle('chs', fontName=R, fontSize=15, textColor=SLATE,    leading=23, alignment=TA_LEFT,   spaceAfter=18),

        # Section headings
        h2           = ParagraphStyle('h2',  fontName=B, fontSize=16, textColor=NAVY,     leading=25, spaceBefore=32, spaceAfter=12),
        h3           = ParagraphStyle('h3',  fontName=B, fontSize=14, textColor=NAVY,     leading=23, spaceBefore=28, spaceAfter=10),
        h4           = ParagraphStyle('h4',  fontName=BI,fontSize=12, textColor=SLATE,    leading=20, spaceBefore=22, spaceAfter=8),

        # Body — generous leading for page count
        body         = ParagraphStyle('bd',  fontName=R, fontSize=13, textColor=DARK_GRAY,
                                      leading=25.5, alignment=TA_JUSTIFY, spaceBefore=5, spaceAfter=50),
        blockquote   = ParagraphStyle('bq',  fontName=I, fontSize=13.5, textColor=SLATE,
                                      leading=24, alignment=TA_LEFT),
        bullet       = ParagraphStyle('bl',  fontName=R, fontSize=13, textColor=DARK_GRAY,
                                      leading=23.5, spaceBefore=7, spaceAfter=7,
                                      leftIndent=28, bulletIndent=10),
        numbered     = ParagraphStyle('nm',  fontName=R, fontSize=13, textColor=DARK_GRAY,
                                      leading=23.5, spaceBefore=7, spaceAfter=7,
                                      leftIndent=32, bulletIndent=10),

        # Diagnostic boxes
        box_header   = ParagraphStyle('bxh', fontName=CB, fontSize=9,   textColor=GOLD,       leading=13),
        box_signal   = ParagraphStyle('bxs', fontName=CB, fontSize=8.5, textColor=GOLD,       leading=13),
        box_body     = ParagraphStyle('bxb', fontName=C,  fontSize=8.5, textColor=GOLD_LIGHT, leading=13),
        box_result   = ParagraphStyle('bxr', fontName=CB, fontSize=9.5, textColor=GOLD,       leading=14),

        # Captions & misc
        caption      = ParagraphStyle('cap', fontName=I, fontSize=10,  textColor=MID_GRAY,
                                      leading=15, alignment=TA_CENTER, spaceBefore=6, spaceAfter=18),
        footer_copy  = ParagraphStyle('fc',  fontName=I, fontSize=9,   textColor=MID_GRAY,
                                      leading=14, alignment=TA_CENTER),

        # TOC
        toc_part     = ParagraphStyle('tp',  fontName=B, fontSize=13,  textColor=NAVY,     leading=20, spaceBefore=14, spaceAfter=3),
        toc_ch       = ParagraphStyle('tc',  fontName=R, fontSize=11,  textColor=DARK_GRAY, leading=18, spaceBefore=2, spaceAfter=2, leftIndent=20),
        toc_special  = ParagraphStyle('ts',  fontName=I, fontSize=11,  textColor=SLATE,    leading=18, spaceBefore=2, spaceAfter=2, leftIndent=20),
    )

# ── Inline formatting ─────────────────────────────────────────────────
def fmt(text):
    text = text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'<b><i>\1</i></b>', text)
    text = re.sub(r'\*\*(.*?)\*\*',     r'<b>\1</b>',         text)
    text = re.sub(r'\*(.*?)\*',         r'<i>\1</i>',          text)
    text = re.sub(r'`([^`]+)`',
        lambda m: '<font name="Courier" color="#C9A227">'+m.group(1)+'</font>', text)
    return text

# ── AVM / diagnostic box (no Unicode box chars) ───────────────────────
def build_box(raw_lines, styles):
    content = []
    for line in raw_lines:
        # strip all box-drawing Unicode characters
        clean = re.sub(r'[\u2500-\u257F\u2550-\u256C\u2502\u2503]+', '', line)
        clean = clean.strip()
        if clean:
            content.append(clean)
    if not content:
        return None

    rows = []
    for line in content:
        safe = line.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        is_result  = bool(re.search(r'RESULTADO|AVM RESULT|SESIÓN_|SESSION_|RECHAZO INMEDIATO|REJECTION', line))
        is_signal  = bool(re.match(r'(Señal|Signal)\s+\d', line))
        is_header  = bool(re.match(r'^[A-ZÁÉÍÓÚÑ\(\)\s\d,·\.]+$', line) and len(line.strip()) > 4
                          and not re.search(r'[a-záéíóúñ]', line))

        if is_result:
            style = styles['box_result']
        elif is_signal:
            style = styles['box_signal']
        elif is_header:
            style = styles['box_header']
        else:
            style = styles['box_body']
        rows.append([Paragraph(safe, style)])

    if not rows:
        return None

    t = Table(rows, colWidths=[TW - 1.2*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,-1), NAVY_MID),
        ('BOX',          (0,0),(-1,-1), 1.8, GOLD),
        ('LEFTPADDING',  (0,0),(-1,-1), 18),
        ('RIGHTPADDING', (0,0),(-1,-1), 18),
        ('TOPPADDING',   (0,0),(0, 0),  14),
        ('TOPPADDING',   (0,1),(-1,-1),  4),
        ('BOTTOMPADDING',(0,-1),(-1,-1),14),
        ('BOTTOMPADDING',(0,0),(-1,-2),  4),
        ('LINEBELOW',    (0,0),(-1,-2), 0.3, colors.HexColor('#1B3352')),
    ]))
    return t

# ── Image flowable ────────────────────────────────────────────────────
def make_image(gnum, caption_text, styles):
    elems = []
    fname = GRAPHIC_MAP.get(gnum)
    if fname:
        fpath = os.path.join(IMG_DIR, fname)
        if os.path.exists(fpath):
            try:
                img = Image(fpath, width=TW * 0.94, height=TW * 0.56)
                img.hAlign = 'CENTER'
                elems.append(Spacer(1, 10))
                elems.append(img)
            except Exception:
                pass
    if caption_text:
        elems.append(Paragraph(caption_text, styles['caption']))
    return elems

# ── Blockquote builder ────────────────────────────────────────────────
def build_blockquote(text, styles):
    p = Paragraph(fmt(text), styles['blockquote'])
    t = Table([[p]], colWidths=[TW - 0.6*cm])
    t.setStyle(TableStyle([
        ('LINEBEFORE',   (0,0),(0,-1), 4, GOLD),
        ('BACKGROUND',   (0,0),(-1,-1), LIGHT_BG),
        ('LEFTPADDING',  (0,0),(-1,-1), 18),
        ('RIGHTPADDING', (0,0),(-1,-1), 14),
        ('TOPPADDING',   (0,0),(-1,-1), 10),
        ('BOTTOMPADDING',(0,0),(-1,-1), 10),
    ]))
    return [Spacer(1,4), t, Spacer(1,8)]

# ── Cover ─────────────────────────────────────────────────────────────
def _logo_box(width_cm, height_cm):
    """Return a dark-background Table containing the OMNIX logo."""
    img = Image(LOGO_PATH, width=width_cm*cm, height=height_cm*cm)
    t = Table([[img]], colWidths=[width_cm*cm + 1.0*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), colors.HexColor('#0A1628')),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 6),
    ]))
    t.hAlign = 'CENTER'
    return t

def build_cover(styles):
    # on_first_page draws the cover via canvas; story just needs a page break.
    return [PageBreak()]

# ── Table of Contents ─────────────────────────────────────────────────
def build_toc(styles):
    e = []
    e.append(Spacer(1, 1*cm))
    e.append(Paragraph('TABLE OF CONTENTS', styles['part_label']))
    e.append(HRFlowable(width='100%', thickness=1, color=GOLD, spaceAfter=18))

    sections = [
        ('part', 'PART I: THE GHOST COMPLIANCE PROBLEM'),
        ('ch',   'Chapter 1 — Ghost Compliance: The Name for What You Already Know'),
        ('ch',   'Chapter 2 — Post-Admission Drift: When the Photograph Becomes a Lie'),
        ('ch',   'Chapter 3 — Three Failures, One Pattern: Terra, SVB and FTX'),
        ('sp',   'Interlude — What the AVM Would Have Said'),
        ('part', 'PART II: THE OMNIX ARCHITECTURE'),
        ('ch',   'Chapter 4 — The Context Admission Gate'),
        ('ch',   'Chapter 5 — The Six Signals: How the AVM Reads Reality'),
        ('ch',   'Chapter 6 — The Systemic Risk Router'),
        ('ch',   'Chapter 7 — The Forensic Audit Trail'),
        ('ch',   'Chapter 8 — Human Override: Authority With Accountability'),
        ('ch',   'Chapter 9 — Post-Quantum Cryptography'),
        ('part', 'PART III: NINE GOVERNANCE VERTICALS'),
        ('ch',   'Chapter 10 — The Architecture of Nine Domains'),
        ('ch',   'Chapters 11–19 — Stablecoins · Trading · Medical AI · Robotics · Real Estate · Insurance · Energy · Islamic Credit · Autonomous Agents'),
        ('part', 'PART IV: THE REGULATORY CONTEXT'),
        ('ch',   'Chapter 20 — MiCA: Europe\'s Answer'),
        ('ch',   'Chapter 21 — VARA: How Dubai Built the World\'s Most Complete Framework'),
        ('ch',   'Chapter 22 — The EU AI Act: When Risk Becomes Law'),
        ('part', 'PART V: THE FOUNDER AND THE VISION'),
        ('ch',   'Chapter 23 — Built From a Diagnosis: The OMNIX Story'),
        ('ch',   'Chapter 24 — 2026–2035: The Decade That Decides Everything'),
        ('sp',   'Epilogue — Ghost Compliance Will Not Survive the Light'),
        ('part', 'APPENDICES'),
        ('sp',   'Appendix A — Technical Glossary'),
        ('sp',   'Appendix B — Comparative Regulatory Framework'),
        ('sp',   'Appendix C — AVM Signal Descriptions'),
        ('sp',   'Appendix D — Analytical Index'),
        ('sp',   'Appendix E — The Cost of Ghost Compliance'),
        ('sp',   'Appendix F — Board of Directors Manual'),
        ('sp',   'Appendix G — The OMNIX Governance Manifesto'),
        ('sp',   'Appendix H — The Verifiable Receipt'),
    ]

    for kind, title in sections:
        if kind == 'part':
            e.append(Spacer(1, 4))
            e.append(Paragraph(title, styles['toc_part']))
            e.append(HRFlowable(width='100%', thickness=0.4, color=GOLD, spaceAfter=4))
        elif kind == 'ch':
            e.append(Paragraph(title, styles['toc_ch']))
        else:
            e.append(Paragraph(title, styles['toc_special']))

    e.append(PageBreak())
    return e

# ── Part splash page ──────────────────────────────────────────────────
def build_part_page(label, styles):
    e = []
    e.append(PageBreak())
    e.append(Spacer(1, 3.8*cm))
    e.append(HRFlowable(width='100%', thickness=3, color=GOLD, spaceAfter=22))
    e.append(Paragraph(label, styles['part_title']))
    e.append(HRFlowable(width='100%', thickness=1, color=GOLD, spaceAfter=18))
    if os.path.exists(LOGO_PATH):
        e.append(Spacer(1, 5*mm))
        e.append(_logo_box(4.5, 3.1))
    e.append(PageBreak())
    return e

# ── Main parser ───────────────────────────────────────────────────────
def parse_md(text, styles):
    lines = text.split('\n')
    elems = []
    i = 0
    in_code = False
    code_buf = []

    while i < len(lines):
        raw  = lines[i]
        line = raw.strip()

        # ── Code fence ─────────────────────────────────────────────
        if line.startswith('```'):
            if not in_code:
                in_code = True; code_buf = []
            else:
                in_code = False
                raw_block = '\n'.join(code_buf)
                if re.search(r'[\u2500-\u257F\u2550-\u256C]|[╔║╚═─]', raw_block):
                    box = build_box(code_buf, styles)
                    if box:
                        elems.append(Spacer(1, 10))
                        elems.append(box)
                        elems.append(Spacer(1, 10))
                else:
                    for cl in code_buf:
                        safe = cl.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
                        elems.append(Paragraph(safe, styles['box_body']))
            i += 1; continue

        if in_code:
            code_buf.append(raw); i += 1; continue

        if not line:
            i += 1; continue

        # ── HR ─────────────────────────────────────────────────────
        if re.match(r'^-{3,}$', line):
            elems.append(Spacer(1, 6))
            elems.append(HRFlowable(width='100%', thickness=0.5, color=GOLD, spaceAfter=6))
            i += 1; continue

        # ── PARTE (## PARTE) ───────────────────────────────────────
        if re.match(r'^## (PARTE|PART)\b', line):
            txt = re.sub(r'^##\s+', '', line)
            elems.extend(build_part_page(fmt(txt), styles))
            i += 1; continue

        # ── Chapter / Interlude / Appendix / Epilogue / Glossary ──
        if re.match(r'^# (CAPÍTULO|CHAPTER|INTERMEDIO|INTERLUDE|APÉNDICE|APPENDIX|EPÍLOGO|EPILOGUE|GLOSARIO|GLOSSARY)', line):
            elems.append(PageBreak())
            label = re.sub(r'^#\s+', '', line)
            elems.append(Spacer(1, 1.4*cm))
            elems.append(Paragraph(label, styles['ch_label']))
            j = i + 1
            while j < len(lines) and not lines[j].strip(): j += 1
            if j < len(lines) and lines[j].strip().startswith('## '):
                sub = re.sub(r'^##\s+', '', lines[j].strip())
                elems.append(Paragraph(fmt(sub), styles['ch_title']))
                i = j
            elems.append(HRFlowable(width='50%', thickness=2.5, color=GOLD, spaceAfter=20))
            i += 1; continue

        # ── H2 ─────────────────────────────────────────────────────
        if line.startswith('## '):
            elems.append(Paragraph(fmt(re.sub(r'^##\s+','',line)), styles['h2']))
            i += 1; continue

        # ── H3 ─────────────────────────────────────────────────────
        if line.startswith('### '):
            elems.append(Paragraph(fmt(re.sub(r'^###\s+','',line)), styles['h3']))
            i += 1; continue

        # ── H4 ─────────────────────────────────────────────────────
        if line.startswith('#### '):
            elems.append(Paragraph(fmt(re.sub(r'^####\s+','',line)), styles['h4']))
            i += 1; continue

        # ── Blockquote ─────────────────────────────────────────────
        if line.startswith('>'):
            bq = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                bq.append(lines[i].strip().lstrip('>').strip()); i += 1
            text_bq = ' '.join(b for b in bq if b)
            if text_bq:
                elems.extend(build_blockquote(text_bq, styles))
            continue

        # ── Bullet ─────────────────────────────────────────────────
        if re.match(r'^[-*\u2022]\s', line):
            txt = re.sub(r'^[-*\u2022]\s+', '', line)
            elems.append(Paragraph('&#8226;&#160;&#160;' + fmt(txt), styles['bullet']))
            i += 1; continue

        # ── Numbered ───────────────────────────────────────────────
        if re.match(r'^\d+\.\s', line):
            m = re.match(r'^(\d+)\.\s+(.*)', line)
            num, txt = (m.group(1), m.group(2)) if m else ('1', line)
            elems.append(Paragraph(f'<b>{num}.</b>&#160;&#160;' + fmt(txt), styles['numbered']))
            i += 1; continue

        # ── Graphic placeholder ─────────────────────────────────────
        m = re.match(r'^\*\*\[GR[AÁ]FICO\s+(\d+):\s*(.*?)\]\*\*$', line, re.I)
        if not m:
            m = re.match(r'^\*\*\[GRAPHIC\s+(\d+):\s*(.*?)\]\*\*$', line, re.I)
        if m:
            gnum = m.group(1).zfill(2)
            cap  = m.group(2).strip()
            elems.extend(make_image(gnum, cap, styles))
            i += 1; continue

        # ── Plain paragraph ─────────────────────────────────────────
        elems.append(Paragraph(fmt(line), styles['body']))
        i += 1

    return elems

# ── Main ──────────────────────────────────────────────────────────────
def main():
    src = 'ghost_compliance_EN.md'
    out = 'Ghost_Compliance_EN.pdf'
    print(f'Reading {src}...')
    with open(src, encoding='utf-8') as f:
        md = f.read()

    styles = build_styles()
    print('Building premium PDF v3...')

    doc = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
        title='Ghost Compliance',
        author='Harold Nunes',
        subject='AI Governance -- Real vs Ghost Compliance',
        creator='OMNIX Quantum',
    )

    story = build_cover(styles) + build_toc(styles) + parse_md(md, styles)
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)

    try:
        import PyPDF2
        with open(out,'rb') as f:
            n = len(PyPDF2.PdfReader(f).pages)
        print(f'✓ {out} — {n} pages')
    except Exception:
        import os; print(f'✓ {out} — {os.path.getsize(out)//1024} KB')

if __name__ == '__main__':
    main()
