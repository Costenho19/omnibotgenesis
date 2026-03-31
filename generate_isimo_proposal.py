from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
import os

OUTPUT = "/home/runner/workspace/OMNIX_Propuesta_Isimo_2026.pdf"
LOGO = "/home/runner/workspace/omnix_web/public/omnix_logo.png"

# Colors
OMNIX_DARK = colors.HexColor("#0a0a0f")
OMNIX_BLUE = colors.HexColor("#3b82f6")
OMNIX_CYAN = colors.HexColor("#06b6d4")
OMNIX_WHITE = colors.white
OMNIX_GRAY = colors.HexColor("#94a3b8")
OMNIX_LIGHT = colors.HexColor("#f8fafc")
OMNIX_BORDER = colors.HexColor("#1e293b")
OMNIX_GREEN = colors.HexColor("#10b981")
OMNIX_RED = colors.HexColor("#ef4444")

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=letter,
    rightMargin=0.65*inch,
    leftMargin=0.65*inch,
    topMargin=0.5*inch,
    bottomMargin=0.65*inch
)

styles = getSampleStyleSheet()

# Custom styles
def S(name, **kw):
    return ParagraphStyle(name, **kw)

title_style = S("Title", fontSize=22, fontName="Helvetica-Bold", textColor=OMNIX_DARK, spaceAfter=4, alignment=TA_LEFT)
subtitle_style = S("Subtitle", fontSize=13, fontName="Helvetica", textColor=OMNIX_BLUE, spaceAfter=12, alignment=TA_LEFT)
section_style = S("Section", fontSize=13, fontName="Helvetica-Bold", textColor=OMNIX_BLUE, spaceBefore=18, spaceAfter=6)
body_style = S("Body", fontSize=10, fontName="Helvetica", textColor=OMNIX_DARK, spaceAfter=6, leading=15, alignment=TA_JUSTIFY)
body_bold = S("BodyBold", fontSize=10, fontName="Helvetica-Bold", textColor=OMNIX_DARK, spaceAfter=6, leading=15)
small_gray = S("SmallGray", fontSize=8.5, fontName="Helvetica", textColor=OMNIX_GRAY, spaceAfter=4, alignment=TA_CENTER)
quote_style = S("Quote", fontSize=11, fontName="Helvetica-BoldOblique", textColor=OMNIX_BLUE, spaceAfter=8, spaceBefore=8, alignment=TA_CENTER, leading=16)
label_style = S("Label", fontSize=8, fontName="Helvetica-Bold", textColor=OMNIX_GRAY, spaceAfter=2)
footer_style = S("Footer", fontSize=8, fontName="Helvetica", textColor=OMNIX_GRAY, alignment=TA_CENTER)
right_style = S("Right", fontSize=9, fontName="Helvetica", textColor=OMNIX_GRAY, alignment=TA_RIGHT)

story = []

# ─── HEADER ───────────────────────────────────────────────────────────────────
header_data = [[
    Image(LOGO, width=1.1*inch, height=0.9*inch) if os.path.exists(LOGO) else Paragraph("OMNIX", title_style),
    Paragraph(
        "<font color='#0a0a0f'><b>PROPUESTA DE GOBERNANZA DE DECISIONES</b></font><br/>"
        "<font color='#3b82f6' size='10'>Para Tiendas Ísimo — Grupo Olímpica</font><br/>"
        "<font color='#94a3b8' size='8'>Confidencial | Marzo 2026 | Abu Dhabi, UAE</font>",
        S("h", fontSize=14, fontName="Helvetica-Bold", textColor=OMNIX_DARK, alignment=TA_LEFT, leading=20)
    ),
    Paragraph(
        "<font color='#94a3b8' size='8'>contacto@omnixquantum.net<br/>www.omnixquantum.net<br/>Eureka GCC Dubai 2026 — Semifinalista</font>",
        right_style
    )
]]
header_table = Table(header_data, colWidths=[1.2*inch, 4.2*inch, 1.9*inch])
header_table.setStyle(TableStyle([
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("BACKGROUND", (0,0), (-1,-1), OMNIX_LIGHT),
    ("ROUNDEDCORNERS", [6]),
    ("TOPPADDING", (0,0), (-1,-1), 10),
    ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ("LEFTPADDING", (0,0), (-1,-1), 10),
    ("RIGHTPADDING", (0,0), (-1,-1), 10),
    ("LINEBELOW", (0,0), (-1,0), 2, OMNIX_BLUE),
]))
story.append(header_table)
story.append(Spacer(1, 14))

# ─── PARA QUIÉN ES ────────────────────────────────────────────────────────────
story.append(Paragraph("PARA: Tiendas Ísimo — Grupo Olímpica", S("t", fontSize=11, fontName="Helvetica-Bold", textColor=OMNIX_DARK, spaceAfter=2)))
story.append(Paragraph("DE: Harold Nunes — Founder &amp; CEO, OMNIX Decision Governance Infrastructure", S("t", fontSize=10, fontName="Helvetica", textColor=OMNIX_GRAY, spaceAfter=2)))
story.append(Paragraph("FECHA: Marzo 2026 | CLASIFICACIÓN: Propuesta Comercial — Confidencial", S("t", fontSize=9, fontName="Helvetica", textColor=OMNIX_GRAY, spaceAfter=8)))
story.append(HRFlowable(width="100%", thickness=1, color=OMNIX_BORDER))
story.append(Spacer(1, 10))

# ─── EL PROBLEMA ──────────────────────────────────────────────────────────────
story.append(Paragraph("EL PROBLEMA QUE ENFRENTA ÍSIMO HOY", section_style))

problem_intro = (
    "Tiendas Ísimo opera más de 400 puntos de venta en Colombia y planea abrir 100 adicionales en 2025, "
    "con una inversión de $160.000 millones de pesos. A esta escala, <b>cientos de decisiones automatizadas "
    "ocurren cada hora</b> — reabastecimiento de inventario, órdenes a proveedores, ajustes de precios, "
    "decisiones logísticas. El volumen hace imposible la supervisión humana en tiempo real."
)
story.append(Paragraph(problem_intro, body_style))
story.append(Spacer(1, 6))

problem_data = [
    ["RIESGO", "LO QUE OCURRE HOY", "IMPACTO"],
    ["Órdenes de compra incorrectas", "Sistema automatiza sin validar condiciones de mercado", "Sobrestock o quiebre de inventario"],
    ["Decisiones de precio en tiempo real", "Ajustes automáticos sin verificar coherencia interna", "Pérdida de margen o clientes"],
    ["Proveedores en condiciones anómalas", "Sin detección de señales de riesgo antes de comprometer capital", "Pérdidas irrecuperables"],
    ["Decisiones logísticas en cascada", "Un error se propaga a toda la cadena sin freno automático", "Disrupciones operacionales costosas"],
    ["Sin audit trail automatizado", "No existe registro auditable de por qué el sistema decidió algo", "Riesgo regulatorio y de litigios"],
]
pt = Table(problem_data, colWidths=[1.5*inch, 2.8*inch, 2.9*inch])
pt.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), OMNIX_DARK),
    ("TEXTCOLOR", (0,0), (-1,0), OMNIX_WHITE),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
    ("TEXTCOLOR", (0,1), (-1,-1), OMNIX_DARK),
    ("BACKGROUND", (0,1), (-1,1), colors.HexColor("#fef2f2")),
    ("BACKGROUND", (0,2), (-1,2), OMNIX_LIGHT),
    ("BACKGROUND", (0,3), (-1,3), colors.HexColor("#fef2f2")),
    ("BACKGROUND", (0,4), (-1,4), OMNIX_LIGHT),
    ("BACKGROUND", (0,5), (-1,5), colors.HexColor("#fef2f2")),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
    ("TOPPADDING", (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [OMNIX_LIGHT, colors.HexColor("#fef2f2")]),
]))
story.append(pt)
story.append(Spacer(1, 10))

story.append(Paragraph(
    '"A esta escala, un error en una decisión automatizada no es un incidente. Es una cascada."',
    quote_style
))

# ─── LA SOLUCIÓN ──────────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=1, color=OMNIX_BORDER))
story.append(Paragraph("LA SOLUCIÓN: OMNIX PARA ÍSIMO", section_style))

sol_intro = (
    "OMNIX es infraestructura de gobernanza de decisiones. No reemplaza los sistemas de Ísimo — "
    "se instala <b>entre la decisión y la ejecución</b>, validando cada acción antes de que ocurra. "
    "Si la decisión no pasa los checkpoints, se bloquea automáticamente. Sin intervención humana. "
    "Con un recibo firmado criptográficamente como prueba."
)
story.append(Paragraph(sol_intro, body_style))
story.append(Spacer(1, 6))

principles_data = [
    ["PRINCIPIO", "QUÉ SIGNIFICA PARA ÍSIMO"],
    ["Protección antes de la acción", "Ninguna orden de compra se ejecuta sin pasar por gobernanza"],
    ["Arquitectura fail-closed", "Si el sistema tiene dudas, bloquea. No ejecuta por defecto."],
    ["Auditabilidad total", "Cada decisión — ejecutada o bloqueada — queda registrada con razón completa"],
]
ptable = Table(principles_data, colWidths=[2.3*inch, 4.9*inch])
ptable.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), OMNIX_BLUE),
    ("TEXTCOLOR", (0,0), (-1,0), OMNIX_WHITE),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
    ("TEXTCOLOR", (0,1), (-1,-1), OMNIX_DARK),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
    ("TOPPADDING", (0,0), (-1,-1), 7),
    ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ("LEFTPADDING", (0,0), (-1,-1), 10),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [OMNIX_LIGHT, colors.white]),
]))
story.append(ptable)
story.append(Spacer(1, 10))

# ─── CÓMO FUNCIONA ────────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=1, color=OMNIX_BORDER))
story.append(Paragraph("CÓMO FUNCIONA: 11 CHECKPOINTS ANTES DE CADA DECISIÓN", section_style))

story.append(Paragraph(
    "Piénselo como seguridad de aeropuerto para cada decisión automatizada de su operación. "
    "La señal llega — una orden de reabastecimiento, un ajuste de precio, una aprobación de proveedor — "
    "y debe pasar 11 checkpoints independientes. Si uno falla, la acción se bloquea.",
    body_style
))
story.append(Spacer(1, 6))

cp_data = [
    ["CP", "CHECKPOINT", "QUÉ VALIDA PARA ÍSIMO"],
    ["CP-0", "Integridad de Señal (SIV)", "¿Los datos del sistema son reales y confiables?"],
    ["CP-1", "Validación de Probabilidad", "¿Esta decisión tiene probabilidad positiva de resultado correcto?"],
    ["CP-2", "Límites de Riesgo (RMS)", "¿La decisión supera los límites de exposición de capital?"],
    ["CP-3", "Coherencia de Señal", "¿Los modelos internos están de acuerdo entre sí?"],
    ["CP-4", "Persistencia de Tendencia", "¿La condición que motiva la decisión es sostenida o un spike?"],
    ["CP-5", "Resiliencia al Estrés", "¿La decisión sobrevive escenarios adversos simulados?"],
    ["CP-6", "Consistencia Lógica", "¿Existen contradicciones internas que invaliden la decisión?"],
    ["CP-7", "Coherencia Temporal (TCV)", "¿La señal es consistente con el historial reciente?"],
    ["CP-8", "Confirmación de Edge (ECW)", "¿Existe ventaja sostenida por al menos 2 ciclos consecutivos?"],
    ["CP-9", "Gate Anti-Lavado (AML)", "¿La transacción cumple con controles de prevención de fraude?"],
    ["CP-10", "Gate de Detección de Fraude", "¿Existen señales de manipulación o actividad anómala?"],
]
cptable = Table(cp_data, colWidths=[0.5*inch, 2.0*inch, 4.7*inch])
cptable.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), OMNIX_DARK),
    ("TEXTCOLOR", (0,0), (-1,0), OMNIX_WHITE),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 8),
    ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
    ("FONTNAME", (0,1), (1,-1), "Helvetica-Bold"),
    ("TEXTCOLOR", (0,1), (0,-1), OMNIX_CYAN),
    ("TEXTCOLOR", (1,1), (-1,-1), OMNIX_DARK),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 7),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [OMNIX_LIGHT, colors.white]),
]))
story.append(cptable)
story.append(Spacer(1, 10))

# ─── PROPUESTA PILOTO ─────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=1, color=OMNIX_BORDER))
story.append(Paragraph("PROPUESTA DE PILOTO PARA ÍSIMO", section_style))

story.append(Paragraph(
    "OMNIX propone un proceso de adopción progresivo — sin riesgo operacional desde el día 1:",
    body_style
))
story.append(Spacer(1, 6))

pilot_data = [
    ["FASE", "DURACIÓN", "QUÉ HACE OMNIX", "INVERSIÓN"],
    ["Fase 1\nShadow Mode", "2–4 semanas\n(Gratuito)", "OMNIX corre en paralelo al sistema de Ísimo sin intervenir. Analiza decisiones reales y genera reportes de qué habría bloqueado y por qué. Cero riesgo operacional.", "Sin costo"],
    ["Fase 2\nAdvisory Mode", "4–8 semanas\n($5K–$10K/mes)", "OMNIX emite recomendaciones previas a cada decisión crítica. El equipo de Ísimo decide si las acata. Cada recomendación llega con recibo firmado y razón documentada.", "Piloto"],
    ["Fase 3\nGobernanza Completa", "Contrato mínimo 12 meses\n($15K–$35K/mes)", "El motor de OMNIX tiene autoridad de veto real. Ninguna decisión crítica se ejecuta sin pasar los 11 checkpoints. Audit trail completo disponible para reguladores.", "Enterprise"],
]
pilot_table = Table(pilot_data, colWidths=[1.2*inch, 1.3*inch, 3.2*inch, 1.5*inch])
pilot_table.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), OMNIX_DARK),
    ("TEXTCOLOR", (0,0), (-1,0), OMNIX_WHITE),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
    ("FONTNAME", (1,1), (-1,-1), "Helvetica"),
    ("TEXTCOLOR", (0,1), (0,-1), OMNIX_BLUE),
    ("TEXTCOLOR", (1,1), (-1,-1), OMNIX_DARK),
    ("TEXTCOLOR", (-1,1), (-1,1), OMNIX_GREEN),
    ("TEXTCOLOR", (-1,2), (-1,2), OMNIX_BLUE),
    ("TEXTCOLOR", (-1,3), (-1,3), OMNIX_DARK),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
    ("TOPPADDING", (0,0), (-1,-1), 8),
    ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [OMNIX_LIGHT, colors.white, colors.HexColor("#f0fdf4")]),
]))
story.append(pilot_table)
story.append(Spacer(1, 10))

# ─── POR QUÉ AHORA ────────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=1, color=OMNIX_BORDER))
story.append(Paragraph("POR QUÉ ÍSIMO NECESITA ESTO AHORA", section_style))

reasons_data = [
    ["RAZÓN", "DETALLE"],
    ["Escala de operación", "Con 400+ tiendas y 100 más en camino, el volumen de decisiones automatizadas crece exponencialmente. Un error de escala en compras o precios cuesta cientos de millones de pesos."],
    ["Competencia sin margen de error", "D1 y Ara operan con márgenes ultra-ajustados. En hard discount, una decisión de inventario incorrecta no es recuperable. La gobernanza es ventaja competitiva."],
    ["Regulación en camino", "Colombia avanza en marcos de gobernanza de IA para el sector retail y financiero. Las empresas que implementen audit trails hoy estarán listas antes de que sea obligatorio."],
    ["La IA sin gobernanza es riesgo", "Si Ísimo usa sistemas automatizados de decisión — y a esta escala inevitablemente los usa — sin una capa de gobernanza, el riesgo operacional es silencioso hasta que explota."],
]
rt = Table(reasons_data, colWidths=[1.8*inch, 5.4*inch])
rt.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), OMNIX_BLUE),
    ("TEXTCOLOR", (0,0), (-1,0), OMNIX_WHITE),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
    ("FONTNAME", (1,1), (-1,-1), "Helvetica"),
    ("TEXTCOLOR", (0,1), (0,-1), OMNIX_DARK),
    ("TEXTCOLOR", (1,1), (-1,-1), OMNIX_DARK),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
    ("TOPPADDING", (0,0), (-1,-1), 7),
    ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ("LEFTPADDING", (0,0), (-1,-1), 10),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [OMNIX_LIGHT, colors.white]),
]))
story.append(rt)
story.append(Spacer(1, 10))

# ─── PRUEBA REAL ──────────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=1, color=OMNIX_BORDER))
story.append(Paragraph("ESTO NO ES TEORÍA — ES UN SISTEMA EN PRODUCCIÓN", section_style))

metrics_data = [
    ["MÉTRICA", "VALOR", "SIGNIFICADO"],
    ["Decisiones gobernadas", "728,000+", "Motor corriendo 24/7 desde noviembre 2025"],
    ["Recibos PQC firmados", "50,688", "Cada decisión firmada con criptografía post-cuántica"],
    ["Capital preservado", "98.5%", "Durante período de caída de mercado de -7.37%"],
    ["Latencia de decisión", "<120ms", "Gobernanza en tiempo real, no post-hoc"],
    ["Precisión de bloqueos", "91%", "El 91% de decisiones bloqueadas habrían resultado en pérdida"],
    ["Uptime en producción", "24/7", "Railway — entorno de producción real, no ambiente de prueba"],
]
mt = Table(metrics_data, colWidths=[2.0*inch, 1.3*inch, 3.9*inch])
mt.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), OMNIX_DARK),
    ("TEXTCOLOR", (0,0), (-1,0), OMNIX_WHITE),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 9),
    ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
    ("FONTNAME", (1,1), (-1,-1), "Helvetica"),
    ("TEXTCOLOR", (0,1), (0,-1), OMNIX_DARK),
    ("TEXTCOLOR", (1,1), (1,-1), OMNIX_BLUE),
    ("FONTNAME", (1,1), (1,-1), "Helvetica-Bold"),
    ("TEXTCOLOR", (2,1), (-1,-1), OMNIX_DARK),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
    ("TOPPADDING", (0,0), (-1,-1), 7),
    ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ("LEFTPADDING", (0,0), (-1,-1), 10),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [OMNIX_LIGHT, colors.white]),
]))
story.append(mt)
story.append(Spacer(1, 8))

story.append(Paragraph(
    'Verificación independiente disponible en: <font color="#3b82f6">www.omnixquantum.net/verify</font>',
    S("link", fontSize=9, fontName="Helvetica", textColor=OMNIX_DARK, alignment=TA_CENTER, spaceAfter=4)
))

# ─── PRÓXIMOS PASOS ───────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=1, color=OMNIX_BORDER))
story.append(Paragraph("PRÓXIMOS PASOS", section_style))

steps_data = [
    ["PASO", "ACCIÓN", "RESPONSABLE"],
    ["1", "Reunión de diagnóstico — 30 minutos para entender los sistemas de decisión automatizada de Ísimo", "Harold Nunes / Equipo Ísimo"],
    ["2", "Propuesta técnica personalizada — identificar los flujos de decisión prioritarios para gobernanza", "OMNIX"],
    ["3", "Inicio Shadow Mode — 2 a 4 semanas sin costo, corriendo en paralelo al sistema existente", "OMNIX (sin costo para Ísimo)"],
    ["4", "Reporte de hallazgos — qué decisiones habría bloqueado OMNIX y cuánto capital habría preservado", "OMNIX"],
    ["5", "Decisión de avanzar a fase de piloto pagado", "Ísimo"],
]
st = Table(steps_data, colWidths=[0.4*inch, 4.5*inch, 2.3*inch])
st.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), OMNIX_DARK),
    ("TEXTCOLOR", (0,0), (-1,0), OMNIX_WHITE),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (-1,-1), 8.5),
    ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
    ("FONTNAME", (1,1), (-1,-1), "Helvetica"),
    ("TEXTCOLOR", (0,1), (0,-1), OMNIX_CYAN),
    ("TEXTCOLOR", (1,1), (-1,-1), OMNIX_DARK),
    ("TEXTCOLOR", (2,1), (-1,-1), OMNIX_GRAY),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
    ("TOPPADDING", (0,0), (-1,-1), 7),
    ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [OMNIX_LIGHT, colors.white]),
]))
story.append(st)
story.append(Spacer(1, 12))

# ─── FOOTER ───────────────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=1.5, color=OMNIX_BLUE))
story.append(Spacer(1, 8))

footer_data = [[
    Image(LOGO, width=0.7*inch, height=0.55*inch) if os.path.exists(LOGO) else Paragraph("OMNIX", footer_style),
    Paragraph(
        "<b>OMNIX — Decision Governance Infrastructure</b><br/>"
        "contacto@omnixquantum.net | +1 (650) 507-8293 | www.omnixquantum.net<br/>"
        "Eureka GCC Dubai 2026 — Semifinalista | Abu Dhabi, UAE",
        S("fc", fontSize=8, fontName="Helvetica", textColor=OMNIX_GRAY, alignment=TA_CENTER, leading=12)
    ),
    Paragraph(
        "<font color='#94a3b8'>Marzo 2026<br/>Confidencial</font>",
        S("fr", fontSize=8, fontName="Helvetica", textColor=OMNIX_GRAY, alignment=TA_RIGHT)
    )
]]
footer_table = Table(footer_data, colWidths=[0.9*inch, 5.4*inch, 1.0*inch])
footer_table.setStyle(TableStyle([
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
]))
story.append(footer_table)

doc.build(story)
print(f"PDF generado: {OUTPUT}")
