"""
OMNIX — Propuesta Comercial para Tiendas Ísimo
PDF profesional con fondo oscuro, estilo OMNIX oficial.
"""

import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether, Image, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas as pdf_canvas

# ── Paleta OMNIX ─────────────────────────────────────────────────────────────
DARK_BG    = HexColor('#0a0f1a')
DARK_MID   = HexColor('#0f172a')
CARD_BG    = HexColor('#1e293b')
CARD2_BG   = HexColor('#162032')
GOLD       = HexColor('#C9A227')
GOLD_LIGHT = HexColor('#F5D97A')
RED_ALERT  = HexColor('#ef4444')
GREEN_OK   = HexColor('#10b981')
YELLOW     = HexColor('#f59e0b')
GRAY       = HexColor('#94a3b8')
GRAY2      = HexColor('#64748b')
WHITE      = HexColor('#ffffff')
BLUE       = HexColor('#3b82f6')
CYAN       = HexColor('#06b6d4')
BORDER     = HexColor('#334155')

W, H = letter
LOGO = '/home/runner/workspace/omnix_web/public/omnix_logo.png'
OUTPUT = '/home/runner/workspace/OMNIX_Propuesta_Isimo_2026.pdf'

# ── Página oscura (callback) ──────────────────────────────────────────────────
def dark_page(c, doc):
    c.saveState()
    c.setFillColor(DARK_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    # Franja dorada lateral izquierda
    c.setFillColor(GOLD)
    c.rect(0, 0, 4, H, fill=1, stroke=0)
    # Footer
    c.setFillColor(GRAY2)
    c.setFont('Helvetica', 7)
    c.drawString(0.75*inch, 0.35*inch, 'OMNIX — Decision Governance Infrastructure | Confidencial')
    c.drawRightString(W - 0.65*inch, 0.35*inch, 'omnixquantum.net')
    c.drawCentredString(W/2, 0.35*inch, 'Marzo 2026  ·  Tiendas Ísimo')
    # Línea footer
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(0.65*inch, 0.52*inch, W - 0.65*inch, 0.52*inch)
    c.restoreState()

# ── Estilos ───────────────────────────────────────────────────────────────────
def make_styles():
    s = getSampleStyleSheet()
    defs = [
        ParagraphStyle('CoverTitle',   fontName='Helvetica-Bold',   fontSize=28, textColor=GOLD,       spaceAfter=6,  spaceBefore=4,  alignment=TA_LEFT),
        ParagraphStyle('CoverSub',     fontName='Helvetica',        fontSize=13, textColor=WHITE,      spaceAfter=4,  spaceBefore=4,  alignment=TA_LEFT),
        ParagraphStyle('CoverMeta',    fontName='Helvetica',        fontSize=9,  textColor=GRAY,       spaceAfter=0,  spaceBefore=4,  alignment=TA_LEFT),
        ParagraphStyle('SectionTitle', fontName='Helvetica-Bold',   fontSize=14, textColor=GOLD,       spaceAfter=6,  spaceBefore=16, alignment=TA_LEFT),
        ParagraphStyle('SectionSub',   fontName='Helvetica-Bold',   fontSize=10, textColor=CYAN,       spaceAfter=4,  spaceBefore=6,  alignment=TA_LEFT),
        ParagraphStyle('Body',         fontName='Helvetica',        fontSize=9.5,textColor=GRAY,       spaceAfter=5,  spaceBefore=2,  alignment=TA_JUSTIFY, leading=14),
        ParagraphStyle('BodyW',        fontName='Helvetica',        fontSize=9.5,textColor=WHITE,      spaceAfter=5,  spaceBefore=2,  alignment=TA_JUSTIFY, leading=14),
        ParagraphStyle('Bold',         fontName='Helvetica-Bold',   fontSize=9.5,textColor=WHITE,      spaceAfter=4,  spaceBefore=2,  alignment=TA_LEFT),
        ParagraphStyle('Quote',        fontName='Helvetica-Oblique',fontSize=10, textColor=GOLD_LIGHT, spaceAfter=6,  spaceBefore=6,  alignment=TA_CENTER,  leading=15, leftIndent=30, rightIndent=30),
        ParagraphStyle('TH',           fontName='Helvetica-Bold',   fontSize=8,  textColor=GOLD,       leading=11),
        ParagraphStyle('TD',           fontName='Helvetica',        fontSize=8.5,textColor=WHITE,      leading=12),
        ParagraphStyle('TDGray',       fontName='Helvetica',        fontSize=8.5,textColor=GRAY,       leading=12),
        ParagraphStyle('TDCyan',       fontName='Helvetica-Bold',   fontSize=8.5,textColor=CYAN,       leading=12),
        ParagraphStyle('TDGold',       fontName='Helvetica-Bold',   fontSize=8.5,textColor=GOLD,       leading=12),
        ParagraphStyle('TDGreen',      fontName='Helvetica-Bold',   fontSize=8.5,textColor=GREEN_OK,   leading=12),
        ParagraphStyle('TDRed',        fontName='Helvetica-Bold',   fontSize=8.5,textColor=RED_ALERT,  leading=12),
        ParagraphStyle('SmallGray',    fontName='Helvetica',        fontSize=8,  textColor=GRAY,       spaceAfter=4,  alignment=TA_CENTER),
        ParagraphStyle('SmallW',       fontName='Helvetica',        fontSize=8,  textColor=WHITE,      spaceAfter=4,  alignment=TA_CENTER),
    ]
    for st in defs:
        try:
            s.add(st)
        except Exception:
            pass
    return s

ST = make_styles()

def th(text): return Paragraph(text, ST['TH'])
def td(text): return Paragraph(text, ST['TD'])
def tdg(text): return Paragraph(text, ST['TDGray'])
def tdc(text): return Paragraph(text, ST['TDCyan'])
def tdgold(text): return Paragraph(text, ST['TDGold'])
def tdgreen(text): return Paragraph(text, ST['TDGreen'])
def tdred(text): return Paragraph(text, ST['TDRed'])

BASE_TABLE = TableStyle([
    ('BACKGROUND',    (0,0), (-1, 0), HexColor('#0d1929')),
    ('BACKGROUND',    (0,1), (-1,-1), CARD_BG),
    ('GRID',          (0,0), (-1,-1), 0.5, BORDER),
    ('VALIGN',        (0,0), (-1,-1), 'TOP'),
    ('TOPPADDING',    (0,0), (-1,-1), 6),
    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ('LEFTPADDING',   (0,0), (-1,-1), 8),
    ('RIGHTPADDING',  (0,0), (-1,-1), 8),
    ('ROWBACKGROUNDS',(0,1), (-1,-1), [CARD_BG, CARD2_BG]),
])

def _make_gold_bar(text):
    t = Table(
        [[Paragraph(f'<b>{text}</b>', ParagraphStyle('gbt', fontName='Helvetica-Bold', fontSize=11, textColor=DARK_BG, spaceAfter=0))]],
        colWidths=[7.1*inch]
    )
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), GOLD),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
    ]))
    return t

# ─────────────────────────────────────────────────────────────────────────────
# CONTENIDO
# ─────────────────────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=letter,
        leftMargin=0.7*inch, rightMargin=0.65*inch,
        topMargin=0.65*inch, bottomMargin=0.75*inch
    )
    E = []

    # ── PORTADA ───────────────────────────────────────────────────────────────
    E.append(Spacer(1, 0.3*inch))

    if os.path.exists(LOGO):
        logo_row = Table(
            [[Image(LOGO, width=1.0*inch, height=0.82*inch),
              Paragraph(
                  '<font color="#C9A227"><b>OMNIX</b></font> '
                  '<font color="#94a3b8">Decision Governance Infrastructure</font>',
                  ParagraphStyle('lh', fontName='Helvetica-Bold', fontSize=14, textColor=WHITE, spaceBefore=12)
              )]],
            colWidths=[1.15*inch, 5.95*inch]
        )
        logo_row.setStyle(TableStyle([
            ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
        ]))
        E.append(logo_row)

    E.append(Spacer(1, 0.35*inch))
    E.append(HRFlowable(width='100%', thickness=1, color=GOLD))
    E.append(Spacer(1, 0.25*inch))

    E.append(Paragraph('PROPUESTA DE GOBERNANZA', ST['CoverTitle']))
    E.append(Paragraph(
        'DE DECISIONES AUTOMATIZADAS',
        ParagraphStyle('ct2', fontName='Helvetica-Bold', fontSize=22, textColor=WHITE, spaceAfter=10)
    ))
    E.append(Spacer(1, 0.1*inch))
    E.append(Paragraph(
        'Preparada exclusivamente para <b>Tiendas Ísimo — Grupo Olímpica</b>',
        ST['CoverSub']
    ))
    E.append(Spacer(1, 0.05*inch))
    E.append(Paragraph('Marzo 2026  ·  Confidencial  ·  Abu Dhabi, UAE', ST['CoverMeta']))
    E.append(Paragraph('De: Harold Nunes, Founder &amp; CEO — OMNIX', ST['CoverMeta']))
    E.append(Paragraph(
        'contacto@omnixquantum.net  ·  +1 (650) 507-8293  ·  omnixquantum.net',
        ST['CoverMeta']
    ))
    E.append(Spacer(1, 0.2*inch))

    # Badges
    badge_data = [[
        Paragraph(
            'Eureka GCC Dubai 2026\nSemifinalista',
            ParagraphStyle('b1', fontName='Helvetica-Bold', fontSize=8, textColor=GOLD, alignment=TA_CENTER, leading=12)
        ),
        Paragraph(
            'Sistema en producción\n24/7 — Railway',
            ParagraphStyle('b2', fontName='Helvetica-Bold', fontSize=8, textColor=CYAN, alignment=TA_CENTER, leading=12)
        ),
        Paragraph(
            'Criptografía post-cuántica\nNIST-standardized',
            ParagraphStyle('b3', fontName='Helvetica-Bold', fontSize=8, textColor=GREEN_OK, alignment=TA_CENTER, leading=12)
        ),
        Paragraph(
            '728,000+ decisiones\ngobernadas en vivo',
            ParagraphStyle('b4', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE, alignment=TA_CENTER, leading=12)
        ),
    ]]
    badges = Table(badge_data, colWidths=[1.775*inch]*4)
    badges.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (0,0), HexColor('#1a1500')),
        ('BACKGROUND',    (1,0), (1,0), HexColor('#001a1a')),
        ('BACKGROUND',    (2,0), (2,0), HexColor('#001a0d')),
        ('BACKGROUND',    (3,0), (3,0), CARD_BG),
        ('BOX',           (0,0), (0,0), 1, GOLD),
        ('BOX',           (1,0), (1,0), 1, CYAN),
        ('BOX',           (2,0), (2,0), 1, GREEN_OK),
        ('BOX',           (3,0), (3,0), 1, BORDER),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 6),
    ]))
    E.append(badges)
    E.append(Spacer(1, 0.3*inch))
    E.append(HRFlowable(width='100%', thickness=1, color=BORDER))
    E.append(Spacer(1, 0.15*inch))

    # Resumen ejecutivo portada
    exec_text = (
        'Tiendas Ísimo opera más de 400 puntos de venta con una inversión de $160.000 millones de pesos en expansión. '
        'A esta escala, cientos de decisiones automatizadas ocurren cada hora — reabastecimiento, precios, proveedores, logística. '
        '<b><font color="#C9A227">OMNIX se instala entre la decisión y la ejecución</font></b>, validando cada acción '
        'a través de 11 checkpoints independientes antes de permitir que ocurra. '
        'Si la decisión no supera los checkpoints, se bloquea automáticamente. '
        'Sin intervención humana. Con recibo firmado criptográficamente como prueba.'
    )
    E.append(Paragraph(exec_text, ST['Body']))
    E.append(Spacer(1, 0.2*inch))
    E.append(Paragraph(
        '"A la escala de Ísimo, un error en una decisión automatizada no es un incidente — es una cascada."',
        ST['Quote']
    ))

    E.append(PageBreak())

    # ── SECCIÓN 1: EL PROBLEMA ────────────────────────────────────────────────
    E.append(_make_gold_bar('01  |  EL PROBLEMA QUE ENFRENTA ÍSIMO'))
    E.append(Spacer(1, 10))
    E.append(Paragraph(
        'Con 400+ tiendas y 100 adicionales planificadas, el volumen de decisiones automatizadas '
        'es imposible de supervisar manualmente. Los sistemas de supply chain toman cientos de decisiones '
        'por hora — y ninguna pasa por una capa de validación independiente antes de ejecutarse.',
        ST['Body']
    ))
    E.append(Spacer(1, 8))

    prob_data = [
        [th('ÁREA'), th('RIESGO HOY'), th('CONSECUENCIA')],
        [td('Inventario y\nreabastecimiento'),
         td('Órdenes automatizadas sin validar condiciones de mercado o estado de proveedores'),
         tdred('Sobrestock o quiebre de inventario — costos directos irrecuperables')],
        [td('Gestión de\nprecios'),
         td('Ajustes automáticos sin verificar coherencia interna del modelo de precios'),
         tdred('Pérdida de margen o erosión de precio frente a D1 y Ara')],
        [td('Aprobación de\nproveedores'),
         td('Sin detección de señales de riesgo antes de comprometer capital de compra'),
         tdred('Exposición a proveedores en condición de impago o fraude')],
        [td('Decisiones\nlogísticas'),
         td('Un error se propaga en cascada a toda la red de distribución sin freno automático'),
         tdred('Disrupciones que impactan múltiples puntos de venta simultáneamente')],
        [td('Cumplimiento\nregulatorio'),
         td('Sin audit trail de por qué el sistema tomó cada decisión automatizada'),
         tdred('Riesgo regulatorio y de litigios ante contraloría o proveedores')],
    ]
    prob_table = Table(prob_data, colWidths=[1.4*inch, 3.1*inch, 2.65*inch])
    prob_table.setStyle(BASE_TABLE)
    E.append(prob_table)
    E.append(Spacer(1, 12))

    # ── SECCIÓN 2: LA SOLUCIÓN ────────────────────────────────────────────────
    E.append(_make_gold_bar('02  |  LA SOLUCIÓN: OMNIX PARA ÍSIMO'))
    E.append(Spacer(1, 10))
    E.append(Paragraph(
        'OMNIX no reemplaza los sistemas existentes de Ísimo. '
        '<b><font color="#C9A227">Se instala como capa de gobernanza entre la decisión y la ejecución.</font></b> '
        'Cada señal de decisión entra al motor de OMNIX, pasa por 11 checkpoints independientes, '
        'y solo si los supera todos se permite la ejecución. Si cualquier checkpoint falla: bloqueo '
        'automático, razón documentada, recibo firmado. Arquitectura fail-closed.',
        ST['Body']
    ))
    E.append(Spacer(1, 8))

    princ_data = [
        [th('PRINCIPIO'), th('QUÉ SIGNIFICA PARA ÍSIMO')],
        [tdgold('Protección antes de la acción'),
         td('Ninguna orden de compra, ajuste de precio o aprobación de proveedor se ejecuta sin pasar por gobernanza OMNIX')],
        [tdgold('Arquitectura fail-closed'),
         td('Si el sistema tiene incertidumbre, bloquea. Nunca ejecuta por defecto ante señales ambiguas o contradictorias')],
        [tdgold('Auditabilidad total'),
         td('Cada decisión — ejecutada o bloqueada — queda registrada con razón completa y recibo firmado criptográficamente')],
        [tdgold('Sin reemplazo de sistemas'),
         td('OMNIX se integra vía API sobre los sistemas actuales de Ísimo. No requiere migración ni downtime operacional')],
        [tdgold('Tiempo real (<120ms)'),
         td('Validación completa de 11 checkpoints en tiempo real — gobernanza antes de la acción, no análisis post-hoc')],
    ]
    princ_table = Table(princ_data, colWidths=[2.0*inch, 5.15*inch])
    princ_table.setStyle(BASE_TABLE)
    E.append(princ_table)

    E.append(PageBreak())

    # ── SECCIÓN 3: 11 CHECKPOINTS ─────────────────────────────────────────────
    E.append(_make_gold_bar('03  |  11 CHECKPOINTS ANTES DE CADA DECISIÓN'))
    E.append(Spacer(1, 10))
    E.append(Paragraph(
        'Piénselo como seguridad de aeropuerto para cada decisión automatizada de su operación. '
        'La señal entra al motor de OMNIX y debe superar 11 checkpoints independientes. '
        'Si uno falla, la acción se bloquea. Los 11 checkpoints operan en paralelo en menos de 120ms.',
        ST['Body']
    ))
    E.append(Spacer(1, 8))

    cp_data = [
        [th('CP'), th('CHECKPOINT'), th('QUÉ VALIDA PARA ÍSIMO')],
        [tdc('CP-0'),  tdgold('Integridad de Señal (SIV)'),       td('¿Los datos del sistema de Ísimo son íntegros, completos y confiables antes de decidir?')],
        [tdc('CP-1'),  tdgold('Validación de Probabilidad'),       td('¿Esta decisión tiene probabilidad positiva de resultado correcto según histórico de la operación?')],
        [tdc('CP-2'),  tdgold('Límites de Riesgo (RMS)'),          td('¿La decisión supera los límites de exposición de capital pre-definidos por Ísimo?')],
        [tdc('CP-3'),  tdgold('Coherencia de Señal'),              td('¿Los modelos internos de decisión están de acuerdo entre sí? ¿Existe contradicción de señales?')],
        [tdc('CP-4'),  tdgold('Persistencia de Tendencia'),        td('¿La condición que motiva la decisión es sostenida en el tiempo o un spike puntual?')],
        [tdc('CP-5'),  tdgold('Resiliencia al Estrés'),            td('¿La decisión sobrevive escenarios adversos simulados como quiebre de proveedor o caída de demanda?')],
        [tdc('CP-6'),  tdgold('Consistencia Lógica'),              td('¿Existen contradicciones internas en la lógica de la decisión que la invaliden?')],
        [tdc('CP-7'),  tdgold('Coherencia Temporal (TCV)'),        td('¿La señal es consistente con el historial de decisiones de los últimos N ciclos?')],
        [tdc('CP-8'),  tdgold('Confirmación de Edge (ECW)'),       td('¿Existe ventaja sostenida por al menos 2 ciclos consecutivos que justifique ejecutar la acción?')],
        [tdc('CP-9'),  tdgold('Gate Anti-Lavado (AML)'),           td('¿La transacción cumple controles de prevención contra lavado de activos y cumplimiento normativo?')],
        [tdc('CP-10'), tdgold('Gate Detección de Fraude'),         td('¿Existen señales de manipulación, actividad anómala o patrones de fraude en la operación?')],
    ]
    cp_table = Table(cp_data, colWidths=[0.6*inch, 1.95*inch, 4.6*inch])
    cp_table.setStyle(BASE_TABLE)
    E.append(cp_table)
    E.append(Spacer(1, 12))

    # ── SECCIÓN 4: PILOTO ─────────────────────────────────────────────────────
    E.append(_make_gold_bar('04  |  PROPUESTA DE PILOTO — SIN RIESGO OPERACIONAL'))
    E.append(Spacer(1, 10))
    E.append(Paragraph(
        'OMNIX propone un proceso de adopción en 3 fases, diseñado para eliminar el riesgo operacional '
        'desde el primer día. Ísimo puede validar el valor real del sistema antes de comprometer cualquier inversión.',
        ST['Body']
    ))
    E.append(Spacer(1, 8))

    pilot_data = [
        [th('FASE'), th('DURACIÓN'), th('QUÉ HACE OMNIX'), th('INVERSIÓN')],
        [tdgold('FASE 1\nShadow Mode'),
         td('2 – 4 semanas'),
         td('OMNIX corre en paralelo a los sistemas de Ísimo sin intervenir ni bloquear nada. '
            'Analiza decisiones reales en tiempo real y genera reportes completos: qué habría bloqueado, '
            'por qué, y cuánto capital habría preservado. Cero riesgo operacional.'),
         tdgreen('Sin costo\npara Ísimo')],
        [tdgold('FASE 2\nAdvisory Mode'),
         td('4 – 8 semanas'),
         td('OMNIX emite recomendaciones previas a cada decisión crítica. El equipo de Ísimo decide '
            'si acata la recomendación. Cada recomendación llega con razón documentada '
            'y recibo firmado criptográficamente para audit trail.'),
         tdc('$5K – $10K\nUSD / mes')],
        [tdgold('FASE 3\nGobernanza Completa'),
         td('Mínimo\n12 meses'),
         td('El motor OMNIX tiene autoridad de veto real sobre decisiones críticas. Ninguna orden de '
            'compra, ajuste de precio o aprobación se ejecuta sin superar los 11 checkpoints. '
            'Audit trail completo disponible para reguladores e inversores de Ísimo.'),
         tdc('$15K – $35K\nUSD / mes')],
    ]
    pilot_table = Table(pilot_data, colWidths=[1.25*inch, 1.05*inch, 3.4*inch, 1.45*inch])
    pilot_table.setStyle(BASE_TABLE)
    E.append(pilot_table)

    E.append(PageBreak())

    # ── SECCIÓN 5: POR QUÉ AHORA ─────────────────────────────────────────────
    E.append(_make_gold_bar('05  |  POR QUÉ ÍSIMO NECESITA ESTO AHORA'))
    E.append(Spacer(1, 10))

    why_data = [
        [th('RAZÓN'), th('ARGUMENTO')],
        [tdgold('Escala que supera supervisión manual'),
         td('Con 400+ tiendas en expansión, el volumen de decisiones automatizadas crece más rápido '
            'que cualquier equipo humano puede supervisar. Un error de escala en compras o precios '
            'cuesta cientos de millones de pesos.')],
        [tdgold('Competencia sin margen de error'),
         td('D1 y Ara operan con márgenes ultra-ajustados. En hard discount, una decisión de inventario '
            'incorrecta no es recuperable. La gobernanza de decisiones es ventaja competitiva directa '
            'y diferenciador operacional.')],
        [tdgold('Regulación de IA en camino'),
         td('Colombia avanza en marcos de regulación de IA para el sector retail y financiero. '
            'Las empresas que implementen audit trails hoy estarán preparadas antes de que sea '
            'obligatorio — con ventaja de primer movimiento.')],
        [tdgold('IA sin gobernanza acumula riesgo silencioso'),
         td('Si Ísimo usa sistemas automatizados de decisión — a esta escala es inevitable — '
            'sin una capa de gobernanza, el riesgo operacional acumula silenciosamente '
            'hasta que explota en un evento de alto costo.')],
        [tdgold('Ventana de adopción temprana'),
         td('OMNIX está en fase de primeros clientes enterprise. Los que entran ahora obtienen '
            'condiciones preferenciales, co-diseño del producto para retail colombiano '
            'y soporte dedicado de implementación.')],
    ]
    why_table = Table(why_data, colWidths=[2.1*inch, 5.05*inch])
    why_table.setStyle(BASE_TABLE)
    E.append(why_table)
    E.append(Spacer(1, 12))

    # ── SECCIÓN 6: PRUEBA REAL ────────────────────────────────────────────────
    E.append(_make_gold_bar('06  |  ESTO NO ES TEORÍA — SISTEMA EN PRODUCCIÓN'))
    E.append(Spacer(1, 10))
    E.append(Paragraph(
        'OMNIX lleva operando 24/7 desde noviembre de 2025. Los números siguientes son reales y '
        'verificables de forma independiente en omnixquantum.net/verify.',
        ST['Body']
    ))
    E.append(Spacer(1, 8))

    metrics_data = [
        [th('MÉTRICA'), th('VALOR'), th('QUÉ SIGNIFICA')],
        [td('Decisiones gobernadas en total'),
         tdgreen('728,000+'),
         td('Motor corriendo 24/7 desde noviembre 2025 en entorno de producción real en Railway')],
        [td('Recibos PQC firmados'),
         tdgreen('50,688'),
         td('Cada decisión firmada con algoritmo de firma post-cuántica NIST-standardized')],
        [td('Capital preservado bajo stress'),
         tdgreen('98.5%'),
         td('Durante período de caída de mercado de -7.37% — pérdidas bloqueadas proactivamente')],
        [td('Latencia de gobernanza'),
         tdgreen('<120ms'),
         td('Validación completa de 11 checkpoints en tiempo real, no análisis post-hoc')],
        [td('Precisión de bloqueos'),
         tdgreen('91%'),
         td('El 91% de decisiones bloqueadas habrían resultado en pérdida confirmada')],
        [td('Disponibilidad'),
         tdgreen('24/7'),
         td('Railway — entorno de producción real, no prototipo ni sandbox de demostración')],
        [td('Publicaciones académicas'),
         tdc('SSRN + Zenodo'),
         td('SSRN abstract ID 6321298  ·  Zenodo DOI 10.5281/zenodo.19056919')],
        [td('Reconocimiento externo'),
         tdc('Eureka GCC 2026'),
         td('Semifinalista en Eureka GCC Dubai 2026 — aceleradora de referencia en Medio Oriente')],
    ]
    metrics_table = Table(metrics_data, colWidths=[2.2*inch, 1.45*inch, 3.5*inch])
    metrics_table.setStyle(BASE_TABLE)
    E.append(metrics_table)
    E.append(Spacer(1, 8))
    E.append(Paragraph(
        'Verificación independiente en: <font color="#3b82f6"><b>www.omnixquantum.net/verify</b></font>'
        ' — cualquier recibo es auditable sin autenticación.',
        ST['SmallW']
    ))
    E.append(Spacer(1, 12))

    # ── SECCIÓN 7: PRÓXIMOS PASOS ─────────────────────────────────────────────
    E.append(_make_gold_bar('07  |  PRÓXIMOS PASOS'))
    E.append(Spacer(1, 10))

    steps_data = [
        [th('PASO'), th('ACCIÓN'), th('A CARGO DE')],
        [tdc('1'),
         td('Reunión de diagnóstico — 30 minutos para mapear los sistemas de decisión automatizada '
            'de Ísimo y los flujos de mayor riesgo operacional'),
         tdgold('Harold Nunes\n/ Equipo Ísimo')],
        [tdc('2'),
         td('Propuesta técnica personalizada — OMNIX entrega mapeo de checkpoints '
            'sobre los flujos específicos identificados en la reunión'),
         tdgold('OMNIX\n(1 semana)')],
        [tdc('3'),
         td('Inicio Shadow Mode — 2 a 4 semanas sin costo, corriendo en paralelo '
            'sin intervención ni riesgo operacional para Ísimo'),
         tdgold('OMNIX\n(sin costo)')],
        [tdc('4'),
         td('Reporte de hallazgos — análisis de qué decisiones habría bloqueado OMNIX '
            'y cuánto capital habría preservado durante el período'),
         tdgold('OMNIX')],
        [tdc('5'),
         td('Decisión de avanzar a Fase 2 (Advisory Mode) con contrato piloto pagado'),
         tdgold('Ísimo')],
    ]
    steps_table = Table(steps_data, colWidths=[0.5*inch, 4.75*inch, 1.9*inch])
    steps_table.setStyle(BASE_TABLE)
    E.append(steps_table)
    E.append(Spacer(1, 16))

    # CTA final
    cta_data = [[
        Paragraph(
            '<b><font color="#C9A227" size="12">¿Conversamos esta semana?</font></b><br/><br/>'
            '<font color="#94a3b8">contacto@omnixquantum.net  ·  wa.me/16505078293  ·  +1 (650) 507-8293</font>',
            ParagraphStyle(
                'cta', fontName='Helvetica', fontSize=10,
                textColor=WHITE, alignment=TA_CENTER, leading=18
            )
        )
    ]]
    cta = Table(cta_data, colWidths=[7.1*inch])
    cta.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), CARD_BG),
        ('BOX',           (0,0), (-1,-1), 1.5, GOLD),
        ('TOPPADDING',    (0,0), (-1,-1), 16),
        ('BOTTOMPADDING', (0,0), (-1,-1), 16),
        ('LEFTPADDING',   (0,0), (-1,-1), 20),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    E.append(cta)
    E.append(Spacer(1, 10))
    E.append(Paragraph(
        'OMNIX — Decision Governance Infrastructure  ·  omnixquantum.net  ·  Eureka GCC Dubai 2026 — Semifinalista',
        ParagraphStyle('fin', fontName='Helvetica', fontSize=7.5, textColor=GRAY2, alignment=TA_CENTER)
    ))

    doc.build(E, onFirstPage=dark_page, onLaterPages=dark_page)
    print(f'PDF generado: {OUTPUT}')

build()
